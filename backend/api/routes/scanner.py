"""API routes for scanning libraries."""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.core.scanner import FileScanner
from backend.database.crud import BookCRUD, SeriesCRUD

router = APIRouter(prefix="/api/scan", tags=["scanner"])


class ScanRequest(BaseModel):
    """Request to scan a directory."""

    path: str
    calculate_hashes: bool = True
    save_to_db: bool = True


class ScanResponse(BaseModel):
    """Response from scan operation."""

    status: str
    total_files: int
    by_extension: dict
    total_size_bytes: int
    corrupted_count: int
    saved_to_db: int = 0
    skipped_count: int = 0
    message: str


@router.post("/directory", response_model=ScanResponse)
async def scan_directory(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Scan a directory for books.

    Args:
        request: Scan request with directory path
        db: Database session

    Returns:
        Scan results
    """
    logger.info(f"Scanning directory: {request.path}")

    try:
        # Créer le scanner
        scanner = FileScanner()

        # Scanner et analyser
        results = scanner.scan_and_analyze(request.path)

        saved_count = 0
        skipped_count = 0

        # Sauvegarder en DB si demandé
        if request.save_to_db:
            for file_info in results["files"]:
                if file_info.get("is_corrupted"):
                    continue

                # Vérifier si le livre existe déjà (par hash)
                file_hash = file_info.get("hash")
                if file_hash:
                    existing_book = BookCRUD.get_by_hash(db, file_hash)
                    if existing_book:
                        logger.debug(
                            f"Skipping {file_info['filename']}: already exists (hash: {file_hash[:8]}...)"
                        )
                        skipped_count += 1
                        continue

                # Créer ou récupérer la série (on utilisera le type comme nom pour l'instant)
                series_name = file_info.get("type", "Unknown")
                series = SeriesCRUD.get_by_name(db, series_name)
                if not series:
                    series = SeriesCRUD.create(
                        db, name=series_name, type=file_info.get("type")
                    )

                # Créer le livre
                book = BookCRUD.create(
                    db,
                    original_path=file_info["path"],
                    filename=file_info["filename"],
                    series_id=series.id,
                    file_hash=file_info.get("hash"),
                    file_size=file_info["size"],
                    extension=file_info["extension"],
                    status="pending",
                    is_corrupted=file_info.get("is_corrupted", False),
                )
                saved_count += 1

                logger.debug(f"Saved book {book.id}: {file_info['filename']}")

        response = ScanResponse(
            status="success",
            total_files=results["total_files"],
            by_extension=results["by_extension"],
            total_size_bytes=results["total_size"],
            corrupted_count=len(results["corrupted"]),
            saved_to_db=saved_count,
            skipped_count=skipped_count,
            message=f"Scanned {results['total_files']} files, {saved_count} saved to database, {skipped_count} duplicates skipped",
        )

        logger.info(
            f"Scan completed: {results['total_files']} files found, "
            f"{saved_count} saved to DB, {skipped_count} skipped (duplicates)"
        )

        return response

    except Exception as e:
        logger.error(f"Error scanning directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/directory-stream")
async def scan_directory_stream(
    path: str,
    calculate_hashes: bool = True,
    save_to_db: bool = True,
    db: Session = Depends(get_db)
):
    """
    Scan a directory with Server-Sent Events for real-time progress.

    Args:
        path: Directory path to scan
        calculate_hashes: Whether to calculate file hashes
        save_to_db: Whether to save to database
        db: Database session

    Returns:
        SSE stream with scan progress
    """

    async def event_generator():
        """Generate SSE events for scan progress."""
        try:
            scanner = FileScanner()

            # Étape 1: Lister les fichiers
            yield f"data: {json.dumps({'type': 'status', 'message': 'Listing files...'})}\n\n"
            await asyncio.sleep(0)  # Allow event loop to process

            files = scanner.scan_directory(path)
            total_files = len(files)

            yield f"data: {json.dumps({'type': 'found', 'total': total_files})}\n\n"
            await asyncio.sleep(0)

            # Statistiques
            stats = {
                "total_files": total_files,
                "by_extension": {},
                "total_size": 0,
                "corrupted": [],
            }

            saved_count = 0
            skipped_count = 0
            corrupted_count = 0

            # Étape 2: Analyser et sauvegarder chaque fichier
            for idx, file_info in enumerate(files, 1):
                # Envoyer le progrès
                yield f"data: {json.dumps({'type': 'progress', 'current': idx, 'total': total_files, 'filename': file_info['filename']})}\n\n"
                await asyncio.sleep(0)

                # Calculer le hash
                file_hash = scanner.calculate_file_hash(file_info["path"])
                file_info["hash"] = file_hash

                # Vérifier si corrompu
                is_corrupted = scanner.is_file_corrupted(file_info["path"])
                file_info["is_corrupted"] = is_corrupted

                if is_corrupted:
                    stats["corrupted"].append(file_info["path"])
                    corrupted_count += 1

                # Déterminer le type
                file_type = scanner.get_file_type(file_info["path"])
                file_info["type"] = file_type

                # Statistiques
                ext = file_info["extension"]
                stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
                stats["total_size"] += file_info["size"]

                # Sauvegarder en DB si demandé
                if save_to_db and not is_corrupted:
                    # Vérifier si le livre existe déjà (par hash)
                    if file_hash:
                        existing_book = BookCRUD.get_by_hash(db, file_hash)
                        if existing_book:
                            logger.debug(
                                f"Skipping {file_info['filename']}: already exists"
                            )
                            skipped_count += 1
                            continue

                    # Créer ou récupérer la série
                    series_name = file_type or "Unknown"
                    series = SeriesCRUD.get_by_name(db, series_name)
                    if not series:
                        series = SeriesCRUD.create(db, name=series_name, type=file_type)

                    # Créer le livre
                    BookCRUD.create(
                        db,
                        original_path=file_info["path"],
                        filename=file_info["filename"],
                        series_id=series.id,
                        file_hash=file_hash,
                        file_size=file_info["size"],
                        extension=file_info["extension"],
                        status="pending",
                        is_corrupted=False,
                    )
                    saved_count += 1

            # Envoyer le résultat final
            result = {
                "type": "complete",
                "total_files": total_files,
                "saved_to_db": saved_count,
                "skipped_count": skipped_count,
                "corrupted_count": corrupted_count,
                "by_extension": stats["by_extension"],
                "total_size_bytes": stats["total_size"],
            }

            yield f"data: {json.dumps(result)}\n\n"

            logger.info(
                f"Scan completed: {total_files} files, {saved_count} saved, "
                f"{skipped_count} skipped, {corrupted_count} corrupted"
            )

        except Exception as e:
            logger.error(f"Error during scan: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/stats")
async def get_scan_stats(db: Session = Depends(get_db)):
    """Get statistics about scanned books."""
    total_books = db.query(BookCRUD).count()
    total_series = db.query(SeriesCRUD).count()

    books_with_hash = (
        db.query(BookCRUD).filter(BookCRUD.file_hash.isnot(None)).count()
    )

    books_with_metadata = (
        db.query(BookCRUD).filter(BookCRUD.has_metadata == True).count()  # noqa: E712
    )

    corrupted = db.query(BookCRUD).filter(BookCRUD.is_corrupted == True).count()  # noqa: E712

    duplicates = db.query(BookCRUD).filter(BookCRUD.is_duplicate == True).count()  # noqa: E712

    return {
        "total_books": total_books,
        "total_series": total_series,
        "books_with_hash": books_with_hash,
        "books_with_metadata": books_with_metadata,
        "corrupted": corrupted,
        "duplicates": duplicates,
    }
