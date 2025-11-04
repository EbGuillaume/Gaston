"""Tests for name matcher."""
import pytest

from backend.matching.name_matcher import NameMatcher
from backend.scrapers.base import BaseScraper, MetadataResult


class MockScraper(BaseScraper):
    """Mock scraper for testing."""

    def __init__(self, name="mock", priority=1):
        super().__init__(name, priority)
        self.search_called = False
        self.get_by_id_called = False
        self.mock_results = []

    async def search(self, query: str, **kwargs):
        """Mock search."""
        self.search_called = True
        self.last_query = query
        return self.mock_results

    async def get_by_id(self, item_id: str):
        """Mock get by ID."""
        self.get_by_id_called = True
        return None

    def set_mock_results(self, results):
        """Set mock results to return."""
        self.mock_results = results


@pytest.mark.asyncio
async def test_name_matcher_initialization():
    """Test NameMatcher initialization."""
    matcher = NameMatcher(scrapers=[], use_cache=False)

    assert matcher is not None
    assert len(matcher.scrapers) > 0  # Should have default Bedetheque scraper


@pytest.mark.asyncio
async def test_name_matcher_with_mock_scraper():
    """Test matching with mock scraper."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([
        MetadataResult(
            source="mock",
            confidence=0.95,
            series_name="Astérix",
            volume_number=1,
            title="Le Gaulois",
        )
    ])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False)

    results = await matcher.match("Asterix 01 - Le Gaulois.cbz")

    assert len(results) > 0
    assert mock_scraper.search_called
    assert results[0].series_name == "Astérix"


@pytest.mark.asyncio
async def test_name_matcher_filters_by_confidence():
    """Test that low confidence results are filtered."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([
        MetadataResult(source="mock", confidence=0.95, series_name="High"),
        MetadataResult(source="mock", confidence=0.50, series_name="Low"),
    ])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False, min_confidence=0.70)

    results = await matcher.match("test.cbz")

    # Should only return high confidence result
    assert len(results) == 1
    assert results[0].series_name == "High"


@pytest.mark.asyncio
async def test_name_matcher_sorts_by_confidence():
    """Test that results are sorted by confidence."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([
        MetadataResult(source="mock", confidence=0.80, series_name="Medium"),
        MetadataResult(source="mock", confidence=0.95, series_name="High"),
        MetadataResult(source="mock", confidence=0.75, series_name="Low"),
    ])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False, min_confidence=0.70)

    results = await matcher.match("test.cbz")

    # Should be sorted by confidence descending
    assert len(results) == 3
    assert results[0].series_name == "High"
    assert results[0].confidence == 0.95
    assert results[2].series_name == "Low"


@pytest.mark.asyncio
async def test_name_matcher_filters_by_volume():
    """Test that results are filtered by volume number."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([
        MetadataResult(
            source="mock", confidence=0.95, series_name="Astérix", volume_number=1
        ),
        MetadataResult(
            source="mock", confidence=0.95, series_name="Astérix", volume_number=2
        ),
    ])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False)

    # Search for volume 1 specifically
    results = await matcher.match("Asterix 01.cbz")

    # Should only return volume 1
    assert len(results) == 1
    assert results[0].volume_number == 1


@pytest.mark.asyncio
async def test_name_matcher_get_best_match():
    """Test getting best match."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([
        MetadataResult(source="mock", confidence=0.95, series_name="Best"),
        MetadataResult(source="mock", confidence=0.80, series_name="Second"),
    ])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False)

    best = await matcher.get_best_match("test.cbz")

    assert best is not None
    assert best.series_name == "Best"
    assert best.confidence == 0.95


@pytest.mark.asyncio
async def test_name_matcher_no_results():
    """Test when no results are found."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False)

    results = await matcher.match("nonexistent.cbz")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_name_matcher_batch():
    """Test batch matching."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([
        MetadataResult(source="mock", confidence=0.95, series_name="Test"),
    ])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False)

    filenames = ["file1.cbz", "file2.cbz"]
    results = await matcher.match_batch(filenames)

    assert len(results) == 2
    assert "file1.cbz" in results
    assert "file2.cbz" in results


@pytest.mark.asyncio
async def test_name_matcher_add_scraper():
    """Test adding a scraper."""
    matcher = NameMatcher(scrapers=[], use_cache=False)
    initial_count = len(matcher.scrapers)

    new_scraper = MockScraper(name="new", priority=2)
    matcher.add_scraper(new_scraper)

    assert len(matcher.scrapers) == initial_count + 1


@pytest.mark.asyncio
async def test_name_matcher_remove_scraper():
    """Test removing a scraper."""
    mock_scraper = MockScraper(name="removeme")
    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False)

    matcher.remove_scraper("removeme")

    assert not any(s.name == "removeme" for s in matcher.scrapers)


@pytest.mark.asyncio
async def test_name_matcher_prefer_series():
    """Test preferring specific series."""
    mock_scraper = MockScraper()
    mock_scraper.set_mock_results([
        MetadataResult(source="mock", confidence=0.80, series_name="Preferred Series"),
        MetadataResult(source="mock", confidence=0.85, series_name="Other Series"),
    ])

    matcher = NameMatcher(scrapers=[mock_scraper], use_cache=False)

    results = await matcher.match("test.cbz", prefer_series="Preferred Series")

    # Preferred series should be boosted and come first
    assert results[0].series_name == "Preferred Series"
    assert results[0].confidence > 0.80  # Should be boosted
