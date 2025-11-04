"""Tests for deduplicator module."""
import pytest

from backend.core.deduplicator import Deduplicator
from backend.database.crud import BookCRUD, SeriesCRUD


def test_deduplicator_initialization(test_db):
    """Test Deduplicator initialization."""
    dedup = Deduplicator(test_db)
    assert dedup is not None
    assert dedup.db == test_db
    assert dedup.similarity_threshold > 0


def test_detect_exact_duplicates(test_db):
    """Test exact duplicate detection by hash."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    # Create two books with same hash
    book1 = BookCRUD.create(
        test_db,
        original_path="/test/book1.cbz",
        filename="book1.cbz",
        series_id=series.id,
        file_hash="abc123",
    )

    book2 = BookCRUD.create(
        test_db,
        original_path="/test/book2.cbz",
        filename="book2.cbz",
        series_id=series.id,
        file_hash="abc123",
    )

    # Create a book with different hash
    book3 = BookCRUD.create(
        test_db,
        original_path="/test/book3.cbz",
        filename="book3.cbz",
        series_id=series.id,
        file_hash="def456",
    )

    dedup = Deduplicator(test_db)
    duplicates = dedup.detect_exact_duplicates([book1, book2, book3])

    assert len(duplicates) == 1
    assert duplicates[0][0].id == book1.id
    assert duplicates[0][1].id == book2.id


def test_detect_fuzzy_duplicates(test_db):
    """Test fuzzy duplicate detection by name."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    # Create books with similar names
    book1 = BookCRUD.create(
        test_db,
        original_path="/test/book1.cbz",
        filename="Asterix 01 - Le Gaulois.cbz",
        series_id=series.id,
    )

    book2 = BookCRUD.create(
        test_db,
        original_path="/test/book2.cbz",
        filename="Asterix 1 Le Gaulois.cbr",
        series_id=series.id,
    )

    # Create a book with different name
    book3 = BookCRUD.create(
        test_db,
        original_path="/test/book3.cbz",
        filename="Batman 01.cbz",
        series_id=series.id,
    )

    dedup = Deduplicator(test_db)
    duplicates = dedup.detect_fuzzy_duplicates([book1, book2, book3])

    # Should find book1 and book2 as duplicates
    assert len(duplicates) >= 1


def test_select_best_file_by_format(test_db):
    """Test selecting best file by format priority."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    book_cbz = BookCRUD.create(
        test_db,
        original_path="/test/book.cbz",
        filename="book.cbz",
        series_id=series.id,
        extension=".cbz",
    )

    book_cbr = BookCRUD.create(
        test_db,
        original_path="/test/book.cbr",
        filename="book.cbr",
        series_id=series.id,
        extension=".cbr",
    )

    dedup = Deduplicator(test_db, format_priority=["cbz", "cbr"])
    best = dedup.select_best_file(book_cbz, book_cbr)

    # CBZ should be preferred
    assert best.id == book_cbz.id


def test_select_best_file_by_size(test_db):
    """Test selecting best file by size when format is same."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    book_small = BookCRUD.create(
        test_db,
        original_path="/test/book1.cbz",
        filename="book1.cbz",
        series_id=series.id,
        extension=".cbz",
        file_size=1000,
    )

    book_large = BookCRUD.create(
        test_db,
        original_path="/test/book2.cbz",
        filename="book2.cbz",
        series_id=series.id,
        extension=".cbz",
        file_size=2000,
    )

    dedup = Deduplicator(test_db)
    best = dedup.select_best_file(book_small, book_large)

    # Larger file should be preferred
    assert best.id == book_large.id


def test_run_full_detection(test_db):
    """Test full duplicate detection."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    # Create some books
    book1 = BookCRUD.create(
        test_db,
        original_path="/test/book1.cbz",
        filename="book1.cbz",
        series_id=series.id,
        file_hash="hash1",
    )

    book2 = BookCRUD.create(
        test_db,
        original_path="/test/book2.cbz",
        filename="book2.cbz",
        series_id=series.id,
        file_hash="hash1",  # Same hash
    )

    dedup = Deduplicator(test_db)
    results = dedup.run_full_detection([book1, book2])

    assert "total_books" in results
    assert results["total_books"] == 2
    assert "exact_duplicates" in results
    assert len(results["exact_duplicates"]) >= 1


def test_detect_exact_duplicates_no_hash(test_db):
    """Test that books without hash are skipped."""
    series = SeriesCRUD.create(test_db, name="Test Series")

    book1 = BookCRUD.create(
        test_db,
        original_path="/test/book1.cbz",
        filename="book1.cbz",
        series_id=series.id,
        file_hash=None,  # No hash
    )

    book2 = BookCRUD.create(
        test_db,
        original_path="/test/book2.cbz",
        filename="book2.cbz",
        series_id=series.id,
        file_hash=None,  # No hash
    )

    dedup = Deduplicator(test_db)
    duplicates = dedup.detect_exact_duplicates([book1, book2])

    # Should find no duplicates
    assert len(duplicates) == 0


def test_format_priority_default(test_db):
    """Test that default format priority is used."""
    dedup = Deduplicator(test_db)
    assert "cbz" in dedup.format_priority
    assert "cbr" in dedup.format_priority


def test_custom_similarity_threshold(test_db):
    """Test using custom similarity threshold."""
    dedup = Deduplicator(test_db, similarity_threshold=0.95)
    assert dedup.similarity_threshold == 0.95
