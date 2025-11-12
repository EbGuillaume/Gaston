"""API routes for metadata operations."""
import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.database.crud import BookCRUD, MetadataCRUD
from backend.database.models import Book
from backend.matching.name_matcher import NameMatcher
from backend.scrapers.cache import ScraperCache

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


class MetadataResponse(BaseModel):
    """Response model for metadata."""

    source: str
    confidence: float
    series_name: str
    volume_number: Optional[int] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    writers: List[str] = []
    pencillers: List[str] = []
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    cover_url: Optional[str] = None
    url: Optional[str] = None


class SearchRequest(BaseModel):
    """Request to search metadata."""

    query: str
    source: Optional[str] = None  # bedetheque, comicvine
    limit: int = 10


class MatchRequest(BaseModel):
    """Request to match a filename."""

    filename: str
    auto_validate: bool = True
    auto_validate_threshold: float = 0.90


@router.post("/search", response_model=List[MetadataResponse])
async def search_metadata(request: SearchRequest):
    """
    Search for metadata.

    Args:
        request: Search request with query

    Returns:
        List of metadata results
    """
    logger.info(f"Searching metadata for: {request.query}")

    matcher = NameMatcher(use_cache=False)  # Cache désactivé pour debug

    try:
        results = await matcher.match(request.query)

        # Limiter les résultats
        results = results[: request.limit]

        # Convertir en response models
        responses = []
        for result in results:
            resp = MetadataResponse(
                source=result.source,
                confidence=result.confidence,
                series_name=result.series_name,
                volume_number=result.volume_number,
                title=result.title,
                summary=result.summary,
                writers=result.writers,
                pencillers=result.pencillers,
                publisher=result.publisher,
                publication_date=result.publication_date,
                cover_url=result.cover_url,
                url=result.url,
            )
            responses.append(resp)

        return responses

    finally:
        await matcher.close()


@router.post("/match/{book_id}")
async def match_book_metadata(
    book_id: int,
    auto_validate: bool = True,
    auto_validate_threshold: float = 0.90,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
):
    """
    Match metadata for a specific book.

    Args:
        book_id: Book ID
        auto_validate: Automatically save if confidence >= threshold
        auto_validate_threshold: Confidence threshold for auto-validation
        force_refresh: Force re-enrichment even if metadata already exists
        db: Database session

    Returns:
        Match results
    """
    logger.info(f"Matching metadata for book {book_id} (force_refresh={force_refresh})")

    # Récupérer le livre
    book = BookCRUD.get(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Vérifier si des métadonnées existent déjà
    existing_metadata = MetadataCRUD.get_by_book(db, book_id)
    if existing_metadata and not force_refresh:
        logger.info(f"Metadata already exists for book {book_id}")
        return {
            "status": "success",
            "message": "Metadata already exists",
            "metadata_id": existing_metadata.id,
            "confidence": existing_metadata.confidence_score,
        }

    # Si force_refresh et metadata existe, la supprimer d'abord
    if existing_metadata and force_refresh:
        logger.info(f"Force refresh: deleting existing metadata for book {book_id}")
        MetadataCRUD.delete(db, existing_metadata.id)

    # Matcher
    matcher = NameMatcher(use_cache=False)  # Cache désactivé pour debug

    try:
        # Chercher les correspondances (avec le chemin complet pour détecter le dossier parent)
        matches = await matcher.match(book.filename, full_path=book.original_path)

        if not matches:
            return {
                "status": "no_match",
                "message": "No metadata found",
                "matches": [],
            }

        best_match = matches[0]

        # Auto-validation si confiance suffisante
        if auto_validate and best_match.confidence >= auto_validate_threshold:
            # Sauvegarder les métadonnées
            metadata = MetadataCRUD.create(
                db,
                book_id=book_id,
                source=best_match.source,
                confidence_score=best_match.confidence,
                series_name=best_match.series_name,
                volume_number=best_match.volume_number,
                title=best_match.title,
                summary=best_match.summary,
                writers=",".join(best_match.writers) if best_match.writers else None,
                pencillers=",".join(best_match.pencillers) if best_match.pencillers else None,
                publisher=best_match.publisher,
                publication_date=best_match.publication_date,
                cover_url=best_match.cover_url,
            )

            # Marquer le livre comme ayant des métadonnées
            BookCRUD.update(db, book_id, has_metadata=True)

            logger.info(
                f"Auto-validated and saved metadata for book {book_id} "
                f"(confidence: {best_match.confidence:.2f})"
            )

            return {
                "status": "success",
                "message": "Metadata automatically saved",
                "metadata_id": metadata.id,
                "confidence": best_match.confidence,
            }

        # Sinon, retourner les options
        match_responses = []
        for match in matches[:5]:  # Top 5
            match_responses.append(
                {
                    "source": match.source,
                    "confidence": match.confidence,
                    "series_name": match.series_name,
                    "volume_number": match.volume_number,
                    "title": match.title,
                    "cover_url": match.cover_url,
                    "url": match.url,
                }
            )

        return {
            "status": "requires_validation",
            "message": f"Found {len(matches)} matches, user validation required",
            "matches": match_responses,
        }

    finally:
        await matcher.close()


@router.post("/batch-match")
async def batch_match_metadata(
    book_ids: List[int] = Query(...),
    auto_validate_threshold: float = 0.90,
    db: Session = Depends(get_db),
):
    """
    Match metadata for multiple books.

    Args:
        book_ids: List of book IDs
        auto_validate_threshold: Confidence threshold
        db: Database session

    Returns:
        Batch match results
    """
    logger.info(f"Batch matching metadata for {len(book_ids)} books")

    results = {
        "total": len(book_ids),
        "auto_validated": 0,
        "requires_validation": 0,
        "no_match": 0,
        "errors": 0,
    }

    matcher = NameMatcher(use_cache=False)  # Cache désactivé pour debug

    try:
        for book_id in book_ids:
            try:
                book = BookCRUD.get(db, book_id)
                if not book:
                    results["errors"] += 1
                    continue

                matches = await matcher.match(book.filename, full_path=book.original_path)

                if not matches:
                    results["no_match"] += 1
                    continue

                best_match = matches[0]

                if best_match.confidence >= auto_validate_threshold:
                    # Sauvegarder
                    MetadataCRUD.create(
                        db,
                        book_id=book_id,
                        source=best_match.source,
                        confidence_score=best_match.confidence,
                        series_name=best_match.series_name,
                        volume_number=best_match.volume_number,
                        title=best_match.title,
                        summary=best_match.summary,
                        writers=",".join(best_match.writers) if best_match.writers else None,
                        pencillers=",".join(best_match.pencillers)
                        if best_match.pencillers
                        else None,
                        publisher=best_match.publisher,
                        publication_date=best_match.publication_date,
                        cover_url=best_match.cover_url,
                    )

                    BookCRUD.update(db, book_id, has_metadata=True)
                    results["auto_validated"] += 1
                else:
                    results["requires_validation"] += 1

            except Exception as e:
                logger.error(f"Error matching book {book_id}: {e}")
                results["errors"] += 1

        return results

    finally:
        await matcher.close()


@router.get("/enrich-all-stream")
async def enrich_all_stream(
    auto_validate_threshold: float = 0.80,
    batch_size: int = 10,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
):
    """
    Enrich all books with Server-Sent Events for real-time progress.
    Processes books in parallel batches for speed.

    Args:
        auto_validate_threshold: Confidence threshold for auto-validation
        batch_size: Number of books to process in parallel (default: 10)
        force_refresh: Force re-enrichment even if metadata already exists
        db: Database session

    Returns:
        SSE stream with enrichment progress
    """

    async def event_generator():
        """Generate SSE events for enrichment progress."""
        try:
            # Récupérer tous les livres
            books = db.query(Book).all()
            total_books = len(books)

            if total_books == 0:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No books to enrich'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'found', 'total': total_books})}\n\n"
            await asyncio.sleep(0)

            success = 0
            failed = 0
            skipped = 0

            # Créer un matcher réutilisable
            matcher = NameMatcher(use_cache=True)

            try:
                # Traiter par lots
                for batch_start in range(0, total_books, batch_size):
                    batch_end = min(batch_start + batch_size, total_books)
                    batch = books[batch_start:batch_end]

                    # Traiter le lot en parallèle
                    tasks = []
                    for book in batch:
                        tasks.append(_enrich_single_book(book, matcher, auto_validate_threshold, force_refresh, db))

                    # Attendre que tout le lot soit traité
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Traiter les résultats du lot
                    for idx, result in enumerate(batch_results):
                        book = batch[idx]
                        current_idx = batch_start + idx + 1

                        # Envoyer la progression
                        yield f"data: {json.dumps({'type': 'progress', 'current': current_idx, 'total': total_books, 'filename': book.filename})}\n\n"
                        await asyncio.sleep(0)

                        if isinstance(result, Exception):
                            logger.error(f"Error enriching book {book.id}: {result}")
                            failed += 1
                        elif result == "success":
                            success += 1
                        elif result == "skipped":
                            skipped += 1
                        else:
                            failed += 1

                # Résultat final
                result_data = {
                    "type": "complete",
                    "total": total_books,
                    "success": success,
                    "failed": failed,
                    "skipped": skipped,
                }

                yield f"data: {json.dumps(result_data)}\n\n"

                logger.info(
                    f"Enrichment completed: {success} success, {failed} failed, {skipped} skipped"
                )

            finally:
                await matcher.close()

        except Exception as e:
            logger.error(f"Error during enrichment: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _enrich_single_book(book, matcher, threshold, force_refresh, db):
    """
    Helper function to enrich a single book.

    Args:
        book: Book object
        matcher: NameMatcher instance
        threshold: Confidence threshold
        force_refresh: Force re-enrichment even if metadata already exists
        db: Database session

    Returns:
        "success", "skipped", or "failed"
    """
    try:
        # Vérifier si des métadonnées existent déjà
        existing_metadata = MetadataCRUD.get_by_book(db, book.id)
        if existing_metadata and not force_refresh:
            return "skipped"

        # Si force_refresh et metadata existe, la supprimer d'abord
        if existing_metadata and force_refresh:
            MetadataCRUD.delete(db, existing_metadata.id)

        # Chercher les correspondances
        matches = await matcher.match(book.filename, full_path=book.original_path)

        if not matches:
            return "failed"

        best_match = matches[0]

        # Auto-validation si confiance suffisante
        if best_match.confidence >= threshold:
            # Sauvegarder les métadonnées
            MetadataCRUD.create(
                db,
                book_id=book.id,
                source=best_match.source,
                confidence_score=best_match.confidence,
                series_name=best_match.series_name,
                volume_number=best_match.volume_number,
                title=best_match.title,
                summary=best_match.summary,
                writers=",".join(best_match.writers) if best_match.writers else None,
                pencillers=",".join(best_match.pencillers) if best_match.pencillers else None,
                publisher=best_match.publisher,
                publication_date=best_match.publication_date,
                cover_url=best_match.cover_url,
            )

            # Marquer le livre comme ayant des métadonnées
            BookCRUD.update(db, book.id, has_metadata=True)

            return "success"
        else:
            return "failed"

    except Exception as e:
        logger.error(f"Error enriching book {book.id}: {e}")
        return "failed"


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    cache = ScraperCache()
    stats = cache.get_stats()
    return stats


@router.post("/cache/clear")
async def clear_cache(source: Optional[str] = None):
    """
    Clear metadata cache.

    Args:
        source: If specified, only clear cache for this source
    """
    cache = ScraperCache()
    cache.clear(source=source)

    return {
        "status": "success",
        "message": f"Cache cleared{' for ' + source if source else ''}",
    }


@router.post("/cache/cleanup")
async def cleanup_cache():
    """Remove expired cache entries."""
    cache = ScraperCache()
    cache.cleanup_expired()

    return {"status": "success", "message": "Expired cache entries removed"}


class ManualMetadataRequest(BaseModel):
    """Request to manually add/update metadata."""

    book_id: int
    series_name: str
    volume_number: Optional[int] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    writers: List[str] = []
    pencillers: List[str] = []
    inkers: List[str] = []
    colorists: List[str] = []
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    isbn: Optional[str] = None
    page_count: Optional[int] = None
    genres: List[str] = []
    tags: List[str] = []


@router.post("/manual")
async def add_manual_metadata(request: ManualMetadataRequest, db: Session = Depends(get_db)):
    """
    Manually add or update metadata for a book.

    Args:
        request: Manual metadata request
        db: Database session

    Returns:
        Created/updated metadata
    """
    logger.info(f"Adding manual metadata for book {request.book_id}")

    # Vérifier que le livre existe
    book = BookCRUD.get(db, request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Vérifier si des métadonnées existent déjà
    existing_metadata = MetadataCRUD.get_by_book(db, request.book_id)

    metadata_data = {
        "book_id": request.book_id,
        "source": "manual",
        "confidence_score": 1.0,  # Manuel = confiance maximale
        "series_name": request.series_name,
        "volume_number": request.volume_number,
        "title": request.title,
        "summary": request.summary,
        "writers": ",".join(request.writers) if request.writers else None,
        "pencillers": ",".join(request.pencillers) if request.pencillers else None,
        "inkers": ",".join(request.inkers) if request.inkers else None,
        "colorists": ",".join(request.colorists) if request.colorists else None,
        "publisher": request.publisher,
        "publication_date": request.publication_date,
        "isbn": request.isbn,
        "page_count": request.page_count,
        "genres": ",".join(request.genres) if request.genres else None,
        "tags": ",".join(request.tags) if request.tags else None,
    }

    if existing_metadata:
        # Mettre à jour
        metadata = MetadataCRUD.update(db, existing_metadata.id, **metadata_data)
        logger.info(f"Updated metadata {metadata.id} for book {request.book_id}")
        action = "updated"
    else:
        # Créer
        metadata = MetadataCRUD.create(db, **metadata_data)
        logger.info(f"Created metadata {metadata.id} for book {request.book_id}")
        action = "created"

    # Marquer le livre comme ayant des métadonnées
    BookCRUD.update(db, request.book_id, has_metadata=True)

    return {
        "status": "success",
        "action": action,
        "metadata_id": metadata.id,
        "message": f"Metadata {action} successfully",
    }


@router.get("/book/{book_id}")
async def get_book_metadata(book_id: int, db: Session = Depends(get_db)):
    """
    Get metadata for a specific book.

    Args:
        book_id: Book ID
        db: Database session

    Returns:
        Metadata if exists
    """
    # Vérifier que le livre existe
    book = BookCRUD.get(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Récupérer les métadonnées
    metadata = MetadataCRUD.get_by_book(db, book_id)

    if not metadata:
        return {
            "status": "no_metadata",
            "message": "No metadata found for this book",
            "book_id": book_id,
            "filename": book.filename,
        }

    return {
        "status": "success",
        "metadata": {
            "id": metadata.id,
            "source": metadata.source,
            "confidence_score": metadata.confidence_score,
            "series_name": metadata.series_name,
            "volume_number": metadata.volume_number,
            "title": metadata.title,
            "summary": metadata.summary,
            "writers": metadata.writers.split(",") if metadata.writers else [],
            "pencillers": metadata.pencillers.split(",") if metadata.pencillers else [],
            "inkers": metadata.inkers.split(",") if metadata.inkers else [],
            "colorists": metadata.colorists.split(",") if metadata.colorists else [],
            "publisher": metadata.publisher,
            "publication_date": metadata.publication_date,
            "isbn": metadata.isbn,
            "page_count": metadata.page_count,
            "genres": metadata.genres.split(",") if metadata.genres else [],
            "tags": metadata.tags.split(",") if metadata.tags else [],
            "cover_url": metadata.cover_url,
        },
    }
