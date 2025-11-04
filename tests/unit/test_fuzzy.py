"""Tests for fuzzy matching utilities."""
import pytest

from backend.utils.fuzzy import FuzzyMatcher


def test_normalize_filename():
    """Test filename normalization."""
    assert FuzzyMatcher.normalize_filename("Asterix_01.cbz") == "asterix 01"
    assert FuzzyMatcher.normalize_filename("Spider-Man.2023.HD.cbz") == "spider man 2023"
    assert FuzzyMatcher.normalize_filename("Batman [01] (2023).pdf") == "batman 01 2023"


def test_calculate_similarity():
    """Test similarity calculation."""
    # Identical strings
    assert FuzzyMatcher.calculate_similarity("test", "test") == 1.0

    # Similar strings
    score = FuzzyMatcher.calculate_similarity("Asterix 01", "Asterix 1")
    assert score > 0.8

    # Different strings
    score = FuzzyMatcher.calculate_similarity("Asterix", "Batman")
    assert score < 0.5


def test_calculate_token_similarity():
    """Test token-based similarity."""
    # Same words, different order
    score = FuzzyMatcher.calculate_token_similarity("Batman Dark Knight", "Dark Knight Batman")
    assert score > 0.9


def test_are_filenames_similar():
    """Test filename similarity detection."""
    # Similar filenames
    assert FuzzyMatcher.are_filenames_similar(
        "Asterix 01 - Le Gaulois.cbz", "Asterix 1 Le Gaulois.cbr", threshold=0.85
    )

    # Different filenames
    assert not FuzzyMatcher.are_filenames_similar(
        "Asterix 01.cbz", "Batman 01.cbz", threshold=0.85
    )


def test_find_similar_names():
    """Test finding similar names in a list."""
    candidates = [
        "Asterix 01 - Le Gaulois.cbz",
        "Asterix 02 - La Serpe d'Or.cbz",
        "Batman 01.cbz",
        "Asterix 1 Le Gaulois.cbr",
    ]

    similar = FuzzyMatcher.find_similar_names("Asterix 01 Le Gaulois", candidates, threshold=0.80)

    assert len(similar) >= 2
    # Should find both Asterix 01 files
    filenames = [name for name, score in similar]
    assert any("Asterix 01" in name or "Asterix 1" in name for name in filenames)


def test_extract_series_and_number():
    """Test extracting series name and number."""
    # Standard format
    series, num = FuzzyMatcher.extract_series_and_number("Asterix 01 - Le Gaulois.cbz")
    assert "asterix" in series.lower()
    assert num == 1

    # Tome format
    series, num = FuzzyMatcher.extract_series_and_number("Batman Tome 05.cbz")
    assert "batman" in series.lower()
    assert num == 5

    # Hash format
    series, num = FuzzyMatcher.extract_series_and_number("Spider-Man #123.cbz")
    assert "spider" in series.lower()
    assert num == 123

    # No number
    series, num = FuzzyMatcher.extract_series_and_number("Maus.cbz")
    assert num == 0


def test_group_similar_files():
    """Test grouping similar files."""
    files = [
        "Asterix 01 - Le Gaulois.cbz",
        "Asterix 1 Le Gaulois.cbr",
        "Batman 01.cbz",
        "Batman 1.cbr",
        "Tintin 01.cbz",
    ]

    groups = FuzzyMatcher.group_similar_files(files, threshold=0.85)

    # Should find at least 2 groups (Asterix and Batman)
    assert len(groups) >= 2

    # Each group should have at least 2 files
    assert all(len(group) >= 2 for group in groups)


def test_normalize_removes_quality_indicators():
    """Test that normalization removes quality indicators."""
    normalized = FuzzyMatcher.normalize_filename("Movie.2023.1080p.BluRay.x264.cbz")
    assert "1080p" not in normalized
    assert "bluray" not in normalized


def test_similarity_case_insensitive():
    """Test that similarity is case insensitive."""
    score1 = FuzzyMatcher.calculate_similarity("ASTERIX", "asterix")
    assert score1 == 1.0

    score2 = FuzzyMatcher.calculate_similarity("Batman", "BATMAN")
    assert score2 == 1.0


def test_find_similar_names_empty_list():
    """Test finding similar names with empty list."""
    similar = FuzzyMatcher.find_similar_names("test", [], threshold=0.8)
    assert similar == []


def test_extract_series_bracket_format():
    """Test extracting series with bracket format."""
    series, num = FuzzyMatcher.extract_series_and_number("Superman [42] Special.cbz")
    assert "superman" in series.lower()
    assert num == 42


def test_extract_series_parenthesis_format():
    """Test extracting series with parenthesis format."""
    series, num = FuzzyMatcher.extract_series_and_number("Wonder Woman (99).cbz")
    assert "wonder woman" in series.lower()
    assert num == 99
