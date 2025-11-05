"""Tests for scrapers."""
import pytest

from backend.scrapers.base import BaseScraper, MetadataResult
from backend.scrapers.bedetheque import BedethequeScraper
from backend.scrapers.cache import ScraperCache


def test_metadata_result_creation():
    """Test creating a metadata result."""
    result = MetadataResult(
        source="test",
        confidence=0.95,
        series_name="Astérix",
        volume_number=1,
        title="Le Gaulois",
        writers=["Goscinny"],
        pencillers=["Uderzo"],
    )

    assert result.source == "test"
    assert result.confidence == 0.95
    assert result.series_name == "Astérix"
    assert result.volume_number == 1
    assert "Goscinny" in result.writers


def test_metadata_result_to_dict():
    """Test converting metadata result to dict."""
    result = MetadataResult(
        source="test",
        confidence=0.95,
        series_name="Astérix",
        volume_number=1,
    )

    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert result_dict["source"] == "test"
    assert result_dict["confidence"] == 0.95
    assert result_dict["series_name"] == "Astérix"


def test_bedetheque_scraper_initialization():
    """Test Bedetheque scraper initialization."""
    scraper = BedethequeScraper()

    assert scraper.name == "bedetheque"
    assert scraper.priority == 1
    assert scraper.is_enabled()


def test_bedetheque_parse_title_with_tome():
    """Test parsing title with tome."""
    scraper = BedethequeScraper()

    series, volume, title = scraper._parse_title("Astérix - Tome 1 - Le Gaulois")

    assert series == "Astérix"
    assert volume == 1
    assert title == "Le Gaulois"


def test_bedetheque_parse_title_with_number():
    """Test parsing title with just number."""
    scraper = BedethequeScraper()

    series, volume, title = scraper._parse_title("Batman - 42 - The Dark Knight")

    assert series == "Batman"
    assert volume == 42
    assert title == "The Dark Knight"


def test_bedetheque_parse_title_without_number():
    """Test parsing title without number."""
    scraper = BedethequeScraper()

    series, volume, title = scraper._parse_title("Tintin - Les Cigares du Pharaon")

    assert series == "Tintin"
    assert volume is None
    assert title == "Les Cigares du Pharaon"


def test_bedetheque_parse_title_simple():
    """Test parsing simple title."""
    scraper = BedethequeScraper()

    series, volume, title = scraper._parse_title("Maus")

    assert series == "Maus"
    assert volume is None
    assert title is None


def test_scraper_enable_disable():
    """Test enabling and disabling scraper."""
    scraper = BedethequeScraper()

    assert scraper.is_enabled()

    scraper.disable()
    assert not scraper.is_enabled()

    scraper.enable()
    assert scraper.is_enabled()


def test_scraper_cache_initialization(temp_dir):
    """Test scraper cache initialization."""
    cache = ScraperCache(cache_dir=temp_dir)

    assert cache.cache_dir.exists()


def test_scraper_cache_set_and_get(temp_dir):
    """Test caching and retrieving results."""
    cache = ScraperCache(cache_dir=temp_dir, ttl=None)

    # Créer des résultats
    results = [
        MetadataResult(
            source="test",
            confidence=0.95,
            series_name="Astérix",
            volume_number=1,
        ),
        MetadataResult(
            source="test",
            confidence=0.90,
            series_name="Astérix",
            volume_number=2,
        ),
    ]

    # Mettre en cache
    cache.set("bedetheque", "asterix", results)

    # Récupérer du cache
    cached_results = cache.get("bedetheque", "asterix")

    assert cached_results is not None
    assert len(cached_results) == 2
    assert cached_results[0].series_name == "Astérix"


def test_scraper_cache_miss(temp_dir):
    """Test cache miss."""
    cache = ScraperCache(cache_dir=temp_dir)

    result = cache.get("bedetheque", "nonexistent")

    assert result is None


def test_scraper_cache_key_normalization(temp_dir):
    """Test that cache keys are normalized."""
    cache = ScraperCache(cache_dir=temp_dir)

    results = [
        MetadataResult(source="test", confidence=1.0, series_name="Test"),
    ]

    # Mettre en cache avec différentes variantes
    cache.set("bedetheque", "ASTERIX", results)

    # Devrait trouver avec différentes casses
    assert cache.get("bedetheque", "asterix") is not None
    assert cache.get("bedetheque", "Asterix") is not None
    assert cache.get("bedetheque", "ASTERIX") is not None


def test_scraper_cache_clear(temp_dir):
    """Test clearing cache."""
    cache = ScraperCache(cache_dir=temp_dir)

    results = [MetadataResult(source="test", confidence=1.0, series_name="Test")]

    cache.set("bedetheque", "test1", results)
    cache.set("bedetheque", "test2", results)

    # Vérifier que le cache existe
    assert cache.get("bedetheque", "test1") is not None

    # Tout effacer
    cache.clear()

    # Vérifier que le cache est vide
    assert cache.get("bedetheque", "test1") is None
    assert cache.get("bedetheque", "test2") is None


def test_scraper_cache_stats(temp_dir):
    """Test cache statistics."""
    cache = ScraperCache(cache_dir=temp_dir)

    results = [MetadataResult(source="test", confidence=1.0, series_name="Test")]

    cache.set("bedetheque", "test1", results)
    cache.set("bedetheque", "test2", results)
    cache.set("comicvine", "test3", results)

    stats = cache.get_stats()

    assert stats["total_entries"] == 3
    assert "bedetheque" in stats["by_source"]
    assert stats["by_source"]["bedetheque"] == 2


def test_scraper_cache_ttl_expired(temp_dir):
    """Test that expired cache is not returned."""
    import time

    cache = ScraperCache(cache_dir=temp_dir, ttl=1)  # 1 second TTL

    results = [MetadataResult(source="test", confidence=1.0, series_name="Test")]

    cache.set("bedetheque", "test", results)

    # Devrait être en cache
    assert cache.get("bedetheque", "test") is not None

    # Attendre l'expiration
    time.sleep(1.5)

    # Devrait être expiré
    assert cache.get("bedetheque", "test") is None


def test_scraper_cache_cleanup_expired(temp_dir):
    """Test cleanup of expired cache entries."""
    import time

    cache = ScraperCache(cache_dir=temp_dir, ttl=1)

    results = [MetadataResult(source="test", confidence=1.0, series_name="Test")]

    cache.set("bedetheque", "old", results)
    time.sleep(1.5)
    cache.set("bedetheque", "new", results)

    # Nettoyer
    cache.cleanup_expired()

    # L'ancien devrait être supprimé, le nouveau conservé
    assert cache.get("bedetheque", "old") is None
    assert cache.get("bedetheque", "new") is not None
