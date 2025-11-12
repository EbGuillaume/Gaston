"""Base abstract class for metadata scrapers."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from loguru import logger


class MetadataResult:
    """Result from a metadata search."""

    def __init__(
        self,
        source: str,
        confidence: float,
        series_name: str,
        volume_number: Optional[int] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        writers: Optional[List[str]] = None,
        pencillers: Optional[List[str]] = None,
        inkers: Optional[List[str]] = None,
        colorists: Optional[List[str]] = None,
        publisher: Optional[str] = None,
        publication_date: Optional[str] = None,
        isbn: Optional[str] = None,
        page_count: Optional[int] = None,
        genres: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        cover_url: Optional[str] = None,
        url: Optional[str] = None,
        raw_data: Optional[Dict] = None,
    ):
        """Initialize metadata result."""
        self.source = source
        self.confidence = confidence
        self.series_name = series_name
        self.volume_number = volume_number
        self.title = title
        self.summary = summary
        self.writers = writers or []
        self.pencillers = pencillers or []
        self.inkers = inkers or []
        self.colorists = colorists or []
        self.publisher = publisher
        self.publication_date = publication_date
        self.isbn = isbn
        self.page_count = page_count
        self.genres = genres or []
        self.tags = tags or []
        self.cover_url = cover_url
        self.url = url
        self.raw_data = raw_data or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "confidence": self.confidence,
            "series_name": self.series_name,
            "volume_number": self.volume_number,
            "title": self.title,
            "summary": self.summary,
            "writers": self.writers,
            "pencillers": self.pencillers,
            "inkers": self.inkers,
            "colorists": self.colorists,
            "publisher": self.publisher,
            "publication_date": self.publication_date,
            "isbn": self.isbn,
            "page_count": self.page_count,
            "genres": self.genres,
            "tags": self.tags,
            "cover_url": self.cover_url,
            "url": self.url,
            "raw_data": self.raw_data,
        }

    def __repr__(self):
        """String representation."""
        return (
            f"MetadataResult(source={self.source}, series={self.series_name}, "
            f"volume={self.volume_number}, confidence={self.confidence:.2f})"
        )


class BaseScraper(ABC):
    """Base class for metadata scrapers."""

    def __init__(self, name: str, priority: int = 1):
        """
        Initialize scraper.

        Args:
            name: Name of the scraper
            priority: Priority (lower = higher priority)
        """
        self.name = name
        self.priority = priority
        self.enabled = True

    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[MetadataResult]:
        """
        Search for metadata.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            List of metadata results
        """
        pass

    @abstractmethod
    async def get_by_id(self, item_id: str) -> Optional[MetadataResult]:
        """
        Get metadata by ID.

        Args:
            item_id: Item identifier

        Returns:
            Metadata result or None
        """
        pass

    def enable(self):
        """Enable the scraper."""
        self.enabled = True
        logger.info(f"Scraper {self.name} enabled")

    def disable(self):
        """Disable the scraper."""
        self.enabled = False
        logger.warning(f"Scraper {self.name} disabled")

    def is_enabled(self) -> bool:
        """Check if scraper is enabled."""
        return self.enabled

    def __repr__(self):
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name}, priority={self.priority})"
