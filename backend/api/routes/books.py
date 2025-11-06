"""API routes for books."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.database.crud import BookCRUD, MetadataCRUD
from backend.database.models import Book

router = APIRouter(prefix="/api/books", tags=["books"])


class BookResponse(BaseModel):
    """Response model for a book."""

    id: int
    filename: str
    original_path: str
    extension: str
    file_size: int
    has_metadata: bool
    is_duplicate: bool
    is_corrupted: bool

    # Metadata if available
    series_name: Optional[str] = None
    volume_number: Optional[int] = None
    title: Optional[str] = None
    publisher: Optional[str] = None
    confidence_score: Optional[float] = None


class BookListResponse(BaseModel):
    """Response model for book list."""

    total: int
    books: List[BookResponse]


@router.get("/", response_model=BookListResponse)
async def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    has_metadata: Optional[bool] = Query(None),
    is_duplicate: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List books with optional filtering.

    Args:
        skip: Number of books to skip (pagination)
        limit: Maximum number of books to return
        has_metadata: Filter by metadata status
        is_duplicate: Filter by duplicate status
        search: Search in filename
        db: Database session

    Returns:
        List of books with metadata
    """
    logger.info(f"Listing books (skip={skip}, limit={limit})")

    # Build query
    query = db.query(Book)

    # Apply filters
    if has_metadata is not None:
        query = query.filter(Book.has_metadata == has_metadata)

    if is_duplicate is not None:
        query = query.filter(Book.is_duplicate == is_duplicate)

    if search:
        query = query.filter(Book.filename.ilike(f"%{search}%"))

    # Count total
    total = query.count()

    # Get books with pagination
    books = query.order_by(Book.id.desc()).offset(skip).limit(limit).all()

    # Build response with metadata
    book_responses = []
    for book in books:
        metadata = MetadataCRUD.get_by_book(db, book.id)

        book_response = BookResponse(
            id=book.id,
            filename=book.filename,
            original_path=book.original_path,
            extension=book.extension,
            file_size=book.file_size,
            has_metadata=book.has_metadata,
            is_duplicate=book.is_duplicate or False,
            is_corrupted=book.is_corrupted or False,
            series_name=metadata.series_name if metadata else None,
            volume_number=metadata.volume_number if metadata else None,
            title=metadata.title if metadata else None,
            publisher=metadata.publisher if metadata else None,
            confidence_score=metadata.confidence_score if metadata else None,
        )

        book_responses.append(book_response)

    return BookListResponse(total=total, books=book_responses)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    Get a specific book by ID.

    Args:
        book_id: Book ID
        db: Database session

    Returns:
        Book details with metadata
    """
    book = BookCRUD.get(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    metadata = MetadataCRUD.get_by_book(db, book_id)

    return BookResponse(
        id=book.id,
        filename=book.filename,
        original_path=book.original_path,
        extension=book.extension,
        file_size=book.file_size,
        has_metadata=book.has_metadata,
        is_duplicate=book.is_duplicate or False,
        is_corrupted=book.is_corrupted or False,
        series_name=metadata.series_name if metadata else None,
        volume_number=metadata.volume_number if metadata else None,
        title=metadata.title if metadata else None,
        publisher=metadata.publisher if metadata else None,
        confidence_score=metadata.confidence_score if metadata else None,
    )


@router.delete("/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """
    Delete a book.

    Args:
        book_id: Book ID
        db: Database session

    Returns:
        Success message
    """
    book = BookCRUD.get(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Delete metadata if exists
    metadata = MetadataCRUD.get_by_book(db, book_id)
    if metadata:
        MetadataCRUD.delete(db, metadata.id)

    # Delete book
    BookCRUD.delete(db, book_id)

    logger.info(f"Deleted book {book_id}")

    return {"status": "success", "message": f"Book {book_id} deleted"}
