"""API routes for metadata operations."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.database.crud import BookCRUD, MetadataCRUD
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

    matcher = NameMatcher(use_cache=True)

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
    db: Session = Depends(get_db),
):
    """
    Match metadata for a specific book.

    Args:
        book_id: Book ID
        auto_validate: Automatically save if confidence >= threshold
        auto_validate_threshold: Confidence threshold for auto-validation
        db: Database session

    Returns:
        Match results
    """
    logger.info(f"Matching metadata for book {book_id}")

    # Récupérer le livre
    book = BookCRUD.get(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Matcher
    matcher = NameMatcher(use_cache=True)

    try:
        # Chercher les correspondances
        matches = await matcher.match(book.filename)

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
                "status": "auto_validated",
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

    matcher = NameMatcher(use_cache=True)

    try:
        for book_id in book_ids:
            try:
                book = BookCRUD.get(db, book_id)
                if not book:
                    results["errors"] += 1
                    continue

                matches = await matcher.match(book.filename)

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
