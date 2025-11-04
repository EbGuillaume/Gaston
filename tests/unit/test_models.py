"""Tests for database models."""
import pytest

from backend.database.crud import BookCRUD, DuplicateCRUD, MetadataCRUD, SeriesCRUD, TaskCRUD
from backend.database.models import Book, Duplicate, Metadata, Series, Task


def test_create_series(test_db):
    """Test creating a series."""
    series = SeriesCRUD.create(
        test_db, name="Astérix", type="BD", language="fr", total_books=38
    )

    assert series.id is not None
    assert series.name == "Astérix"
    assert series.type == "BD"
    assert series.total_books == 38


def test_get_series(test_db):
    """Test getting a series by ID."""
    # Create a series
    series = SeriesCRUD.create(test_db, name="Spider-Man", type="Comic")

    # Retrieve it
    retrieved = SeriesCRUD.get(test_db, series.id)

    assert retrieved is not None
    assert retrieved.id == series.id
    assert retrieved.name == "Spider-Man"


def test_update_series(test_db):
    """Test updating a series."""
    series = SeriesCRUD.create(test_db, name="Batman", type="Comic")

    # Update
    updated = SeriesCRUD.update(test_db, series.id, total_books=100)

    assert updated.total_books == 100


def test_delete_series(test_db):
    """Test deleting a series."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    # Delete
    success = SeriesCRUD.delete(test_db, series.id)
    assert success is True

    # Verify deletion
    retrieved = SeriesCRUD.get(test_db, series.id)
    assert retrieved is None


def test_create_book(test_db):
    """Test creating a book."""
    # Create a series first
    series = SeriesCRUD.create(test_db, name="Test Series")

    # Create a book
    book = BookCRUD.create(
        test_db,
        original_path="/test/path/book.cbz",
        filename="book.cbz",
        series_id=series.id,
        extension=".cbz",
        status="pending",
    )

    assert book.id is not None
    assert book.filename == "book.cbz"
    assert book.series_id == series.id


def test_get_books_by_series(test_db):
    """Test getting all books for a series."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    # Create multiple books
    for i in range(3):
        BookCRUD.create(
            test_db,
            original_path=f"/test/book_{i}.cbz",
            filename=f"book_{i}.cbz",
            series_id=series.id,
        )

    # Retrieve books
    books = BookCRUD.get_by_series(test_db, series.id)

    assert len(books) == 3


def test_create_metadata(test_db):
    """Test creating metadata for a book."""
    series = SeriesCRUD.create(test_db, name="Test Series")
    book = BookCRUD.create(
        test_db, original_path="/test/book.cbz", filename="book.cbz", series_id=series.id
    )

    metadata = MetadataCRUD.create(
        test_db,
        book_id=book.id,
        source="bedetheque",
        confidence_score=0.95,
        series_name="Test Series",
        volume_number=1,
        title="First Volume",
    )

    assert metadata.id is not None
    assert metadata.book_id == book.id
    assert metadata.confidence_score == 0.95


def test_create_duplicate(test_db):
    """Test creating a duplicate entry."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    book1 = BookCRUD.create(
        test_db, original_path="/test/book1.cbz", filename="book1.cbz", series_id=series.id
    )

    book2 = BookCRUD.create(
        test_db, original_path="/test/book2.cbz", filename="book2.cbz", series_id=series.id
    )

    duplicate = DuplicateCRUD.create(
        test_db,
        book_id_1=book1.id,
        book_id_2=book2.id,
        duplicate_type="hash_exact",
        similarity_score=1.0,
        action="pending",
    )

    assert duplicate.id is not None
    assert duplicate.book_id_1 == book1.id
    assert duplicate.book_id_2 == book2.id


def test_mark_duplicate_resolved(test_db):
    """Test marking a duplicate as resolved."""
    series = SeriesCRUD.create(test_db, name="Test Series")
    book1 = BookCRUD.create(
        test_db, original_path="/test/book1.cbz", filename="book1.cbz", series_id=series.id
    )
    book2 = BookCRUD.create(
        test_db, original_path="/test/book2.cbz", filename="book2.cbz", series_id=series.id
    )

    duplicate = DuplicateCRUD.create(
        test_db,
        book_id_1=book1.id,
        book_id_2=book2.id,
        duplicate_type="hash_exact",
        similarity_score=1.0,
        action="pending",
    )

    # Mark as resolved
    success = DuplicateCRUD.mark_resolved(test_db, duplicate.id, book1.id, "keep_first")

    assert success is True

    # Refresh and check
    test_db.refresh(duplicate)
    assert duplicate.resolved is True
    assert duplicate.kept_book_id == book1.id


def test_create_task(test_db):
    """Test creating a task."""
    task = TaskCRUD.create(test_db, task_type="scan", total=100)

    assert task.id is not None
    assert task.task_type == "scan"
    assert task.status == "pending"
    assert task.total == 100


def test_update_task_progress(test_db):
    """Test updating task progress."""
    task = TaskCRUD.create(test_db, task_type="scan", total=100)

    TaskCRUD.update_progress(test_db, task.id, progress=50, current_item="file_50.cbz")

    test_db.refresh(task)
    assert task.progress == 50
    assert task.current_item == "file_50.cbz"


def test_mark_task_completed(test_db):
    """Test marking a task as completed."""
    task = TaskCRUD.create(test_db, task_type="scan")

    TaskCRUD.mark_completed(test_db, task.id)

    test_db.refresh(task)
    assert task.status == "completed"
    assert task.completed_at is not None


def test_cascade_delete_series(test_db):
    """Test that deleting a series cascades to books."""
    series = SeriesCRUD.create(test_db, name="Test Series")
    book = BookCRUD.create(
        test_db, original_path="/test/book.cbz", filename="book.cbz", series_id=series.id
    )

    # Delete series
    SeriesCRUD.delete(test_db, series.id)

    # Book should also be deleted
    retrieved_book = BookCRUD.get(test_db, book.id)
    assert retrieved_book is None
