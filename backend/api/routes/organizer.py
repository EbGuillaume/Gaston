"""API routes for library organization."""
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.database.crud import BookCRUD, MetadataCRUD
from backend.database.models import Book
from backend.organizer import KomgaOrganizer, FileMover

router = APIRouter(prefix="/api/organize", tags=["organization"])


class OrganizeRequest(BaseModel):
    """Request to organize books."""

    book_ids: Optional[List[int]] = None  # None = all books with metadata
    output_path: Optional[str] = None  # Override config output_path
    copy_instead_of_move: bool = False  # Copy files instead of moving
    dry_run: bool = False  # Simulate without actual changes
    inject_comicinfo: bool = True  # Inject ComicInfo.xml in CBZ files


class OrganizeResponse(BaseModel):
    """Response from organize operation."""

    status: str
    total_books: int
    organized: int
    failed: int
    skipped: int
    results: List[dict]
    message: str


class PreviewRequest(BaseModel):
    """Request to preview organization."""

    book_ids: Optional[List[int]] = None
    output_path: Optional[str] = None


class PreviewResponse(BaseModel):
    """Response for organization preview."""

    status: str
    total_books: int
    previews: List[dict]


@router.post("/preview", response_model=PreviewResponse)
async def preview_organization(request: PreviewRequest, db: Session = Depends(get_db)):
    """
    Preview how books will be organized without actually moving them.

    Args:
        request: Preview request
        db: Database session

    Returns:
        Preview of organization
    """
    logger.info("Previewing organization")

    try:
        # Créer l'organizer
        organizer = KomgaOrganizer(output_path=request.output_path)

        # Récupérer les livres à organiser
        if request.book_ids:
            books = [BookCRUD.get(db, book_id) for book_id in request.book_ids]
            books = [b for b in books if b is not None]
        else:
            # Tous les livres avec métadonnées
            books = db.query(Book).filter(BookCRUD.has_metadata == True).all()

        if not books:
            return PreviewResponse(
                status="no_books", total_books=0, previews=[]
            )

        previews = []
        for book in books:
            # Récupérer les métadonnées
            metadata = MetadataCRUD.get_by_book(db, book.id)
            if not metadata:
                continue

            # Générer le chemin cible
            metadata_dict = {
                "series_name": metadata.series_name,
                "volume_number": metadata.volume_number,
                "title": metadata.title,
                "extension": book.extension,
                "publisher": metadata.publisher,
            }

            target_path = organizer.get_target_path_from_metadata(metadata_dict)

            previews.append(
                {
                    "book_id": book.id,
                    "filename": book.filename,
                    "current_path": book.original_path,
                    "target_path": str(target_path),
                    "series": metadata.series_name,
                    "volume": metadata.volume_number,
                    "title": metadata.title,
                }
            )

        return PreviewResponse(
            status="success", total_books=len(previews), previews=previews
        )

    except Exception as e:
        logger.error(f"Error previewing organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organize", response_model=OrganizeResponse)
async def organize_library(request: OrganizeRequest, db: Session = Depends(get_db)):
    """
    Organize books according to Komga standards.

    Args:
        request: Organize request
        db: Database session

    Returns:
        Organization results
    """
    logger.info(
        f"Organizing library (dry_run: {request.dry_run}, copy: {request.copy_instead_of_move})"
    )

    try:
        # Créer l'organizer et le mover
        organizer = KomgaOrganizer(output_path=request.output_path)
        mover = FileMover(dry_run=request.dry_run)

        # Récupérer les livres à organiser
        if request.book_ids:
            books = [BookCRUD.get(db, book_id) for book_id in request.book_ids]
            books = [b for b in books if b is not None]
        else:
            # Tous les livres avec métadonnées
            books = db.query(Book).filter(BookCRUD.has_metadata == True).all()

        if not books:
            return OrganizeResponse(
                status="no_books",
                total_books=0,
                organized=0,
                failed=0,
                skipped=0,
                results=[],
                message="No books to organize",
            )

        results = []
        organized_count = 0
        failed_count = 0
        skipped_count = 0

        for book in books:
            try:
                # Récupérer les métadonnées
                metadata = MetadataCRUD.get_by_book(db, book.id)
                if not metadata:
                    skipped_count += 1
                    results.append(
                        {
                            "book_id": book.id,
                            "filename": book.filename,
                            "status": "skipped",
                            "reason": "No metadata",
                        }
                    )
                    continue

                # Préparer les métadonnées pour ComicInfo.xml
                metadata_dict = None
                if request.inject_comicinfo:
                    metadata_dict = {
                        "title": metadata.title,
                        "series_name": metadata.series_name,
                        "volume_number": metadata.volume_number,
                        "summary": metadata.summary,
                        "writers": metadata.writers,
                        "pencillers": metadata.pencillers,
                        "inkers": metadata.inkers,
                        "colorists": metadata.colorists,
                        "letterers": metadata.letterers,
                        "publisher": metadata.publisher,
                        "publication_date": metadata.publication_date,
                        "isbn": metadata.isbn,
                        "page_count": metadata.page_count,
                        "genres": metadata.genres,
                        "tags": metadata.tags,
                        "age_rating": metadata.age_rating,
                        "source": metadata.source,
                        "confidence_score": metadata.confidence_score,
                    }

                # Générer le chemin cible
                target_path_metadata = {
                    "series_name": metadata.series_name,
                    "volume_number": metadata.volume_number,
                    "title": metadata.title,
                    "extension": book.extension,
                    "publisher": metadata.publisher,
                }
                target_path = organizer.get_target_path_from_metadata(
                    target_path_metadata
                )

                # Déplacer le fichier
                source_path = Path(book.original_path)
                success = mover.move_with_metadata(
                    source_path=source_path,
                    target_path=target_path,
                    metadata=metadata_dict,
                    copy_instead_of_move=request.copy_instead_of_move,
                )

                if success:
                    organized_count += 1

                    # Mettre à jour le chemin dans la base de données (si pas dry-run)
                    if not request.dry_run:
                        BookCRUD.update(db, book.id, original_path=str(target_path))

                    results.append(
                        {
                            "book_id": book.id,
                            "filename": book.filename,
                            "status": "success",
                            "source": str(source_path),
                            "target": str(target_path),
                        }
                    )
                else:
                    failed_count += 1
                    results.append(
                        {
                            "book_id": book.id,
                            "filename": book.filename,
                            "status": "failed",
                            "reason": "Move operation failed",
                        }
                    )

            except Exception as e:
                logger.error(f"Error organizing book {book.id}: {e}")
                failed_count += 1
                results.append(
                    {
                        "book_id": book.id,
                        "filename": book.filename,
                        "status": "failed",
                        "reason": str(e),
                    }
                )

        message = f"Organized {organized_count}/{len(books)} books"
        if request.dry_run:
            message = f"[DRY RUN] Would organize {organized_count}/{len(books)} books"

        return OrganizeResponse(
            status="success",
            total_books=len(books),
            organized=organized_count,
            failed=failed_count,
            skipped=skipped_count,
            results=results,
            message=message,
        )

    except Exception as e:
        logger.error(f"Error organizing library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inject-comicinfo/{book_id}")
async def inject_comicinfo_to_book(book_id: int, db: Session = Depends(get_db)):
    """
    Inject ComicInfo.xml into a specific book's CBZ file.

    Args:
        book_id: Book ID
        db: Database session

    Returns:
        Injection result
    """
    logger.info(f"Injecting ComicInfo.xml into book {book_id}")

    try:
        # Récupérer le livre
        book = BookCRUD.get(db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Vérifier que c'est un CBZ
        if book.extension.lower() != ".cbz":
            raise HTTPException(
                status_code=400, detail="Only CBZ files support ComicInfo.xml injection"
            )

        # Récupérer les métadonnées
        metadata = MetadataCRUD.get_by_book(db, book_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="No metadata found for this book")

        # Préparer les métadonnées
        metadata_dict = {
            "title": metadata.title,
            "series_name": metadata.series_name,
            "volume_number": metadata.volume_number,
            "summary": metadata.summary,
            "writers": metadata.writers,
            "pencillers": metadata.pencillers,
            "inkers": metadata.inkers,
            "colorists": metadata.colorists,
            "letterers": metadata.letterers,
            "publisher": metadata.publisher,
            "publication_date": metadata.publication_date,
            "isbn": metadata.isbn,
            "page_count": metadata.page_count,
            "genres": metadata.genres,
            "tags": metadata.tags,
            "age_rating": metadata.age_rating,
            "source": metadata.source,
            "confidence_score": metadata.confidence_score,
        }

        # Injecter ComicInfo.xml
        mover = FileMover()
        cbz_path = Path(book.original_path)
        success = mover.inject_comicinfo(cbz_path, metadata_dict, backup=True)

        if success:
            return {
                "status": "success",
                "message": f"ComicInfo.xml injected into {book.filename}",
                "backup_created": True,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to inject ComicInfo.xml")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error injecting ComicInfo.xml: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_organization_stats(db: Session = Depends(get_db)):
    """Get statistics about library organization."""
    try:
        total_books = db.query(Book).count()
        books_with_metadata = (
            db.query(Book).filter(BookCRUD.has_metadata == True).count()
        )
        books_without_metadata = total_books - books_with_metadata

        # Compter par extension
        cbz_count = (
            db.query(Book).filter(BookCRUD.extension == ".cbz").count()
        )
        cbr_count = (
            db.query(Book).filter(BookCRUD.extension == ".cbr").count()
        )
        pdf_count = (
            db.query(Book).filter(BookCRUD.extension == ".pdf").count()
        )
        other_count = total_books - cbz_count - cbr_count - pdf_count

        return {
            "total_books": total_books,
            "books_with_metadata": books_with_metadata,
            "books_without_metadata": books_without_metadata,
            "books_ready_to_organize": books_with_metadata,
            "by_extension": {
                "cbz": cbz_count,
                "cbr": cbr_count,
                "pdf": pdf_count,
                "other": other_count,
            },
            "comicinfo_injection_supported": cbz_count,
        }

    except Exception as e:
        logger.error(f"Error getting organization stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
