"""Caching system for scraper results."""
import copy
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional

from loguru import logger

from backend.config import gaston_config
from backend.scrapers.base import MetadataResult


class ScraperCache:
    """Cache for scraper results."""

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl: Optional[int] = None,
    ):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache files
            ttl: Time to live in seconds (None = unlimited)
        """
        self.cache_dir = Path(cache_dir or gaston_config.performance.cache_path) / "scrapers"
        self.ttl = ttl  # None = unlimited (as per config)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, source: str, query: str) -> str:
        """
        Generate cache key.

        Args:
            source: Scraper source name
            query: Search query

        Returns:
            Cache key
        """
        # Normaliser la query (minuscules, sans espaces multiples)
        normalized = " ".join(query.lower().split())
        key_string = f"{source}:{normalized}"

        # Hash MD5 pour avoir un nom de fichier valide
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path."""
        return self.cache_dir / f"{cache_key}.cache"

    def get(self, source: str, query: str) -> Optional[List[MetadataResult]]:
        """
        Get cached results.

        Args:
            source: Scraper source name
            query: Search query

        Returns:
            Cached results or None
        """
        cache_key = self._get_cache_key(source, query)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            logger.debug(f"Cache miss for {source}:{query}")
            return None

        try:
            # Lire le cache
            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)

            # Vérifier le TTL
            if self.ttl is not None:
                cached_at = cache_data.get("timestamp")
                if cached_at:
                    age = (datetime.now() - cached_at).total_seconds()
                    if age > self.ttl:
                        logger.debug(f"Cache expired for {source}:{query} (age: {age}s)")
                        cache_path.unlink()
                        return None

            # Reconstruire les MetadataResult avec copie profonde
            results = []
            for result_dict in cache_data.get("results", []):
                # Copie profonde du dict pour éviter les modifications des objets mutables
                result_dict_copy = copy.deepcopy(result_dict)
                result = MetadataResult(**result_dict_copy)
                results.append(result)

            logger.info(f"Cache hit for {source}:{query} ({len(results)} results)")
            return results

        except Exception as e:
            logger.error(f"Error reading cache for {source}:{query}: {e}")
            # Supprimer le cache corrompu
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, source: str, query: str, results: List[MetadataResult]):
        """
        Cache results.

        Args:
            source: Scraper source name
            query: Search query
            results: Results to cache
        """
        cache_key = self._get_cache_key(source, query)
        cache_path = self._get_cache_path(cache_key)

        try:
            # Convertir les résultats en dictionnaires
            results_dicts = [r.to_dict() for r in results]

            cache_data = {
                "timestamp": datetime.now(),
                "source": source,
                "query": query,
                "results": results_dicts,
            }

            # Écrire le cache
            with open(cache_path, "wb") as f:
                pickle.dump(cache_data, f)

            logger.debug(f"Cached {len(results)} results for {source}:{query}")

        except Exception as e:
            logger.error(f"Error writing cache for {source}:{query}: {e}")

    def clear(self, source: Optional[str] = None):
        """
        Clear cache.

        Args:
            source: If specified, only clear cache for this source
        """
        if source:
            # Supprimer seulement les caches de cette source
            pattern = f"{source}:*"
            count = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, "rb") as f:
                        cache_data = pickle.load(f)
                    if cache_data.get("source") == source:
                        cache_file.unlink()
                        count += 1
                except:
                    pass
            logger.info(f"Cleared {count} cache entries for {source}")
        else:
            # Supprimer tout le cache
            count = len(list(self.cache_dir.glob("*.cache")))
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            logger.info(f"Cleared all cache ({count} entries)")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)

        by_source = {}
        expired = 0

        for cache_file in cache_files:
            try:
                with open(cache_file, "rb") as f:
                    cache_data = pickle.load(f)

                source = cache_data.get("source", "unknown")
                by_source[source] = by_source.get(source, 0) + 1

                # Vérifier si expiré
                if self.ttl is not None:
                    cached_at = cache_data.get("timestamp")
                    if cached_at:
                        age = (datetime.now() - cached_at).total_seconds()
                        if age > self.ttl:
                            expired += 1

            except:
                pass

        return {
            "total_entries": len(cache_files),
            "total_size_bytes": total_size,
            "by_source": by_source,
            "expired": expired,
        }

    def cleanup_expired(self):
        """Remove expired cache entries."""
        if self.ttl is None:
            logger.debug("TTL is unlimited, no cleanup needed")
            return

        removed = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, "rb") as f:
                    cache_data = pickle.load(f)

                cached_at = cache_data.get("timestamp")
                if cached_at:
                    age = (datetime.now() - cached_at).total_seconds()
                    if age > self.ttl:
                        cache_file.unlink()
                        removed += 1

            except:
                # Supprimer les caches corrompus
                cache_file.unlink()
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} expired cache entries")
