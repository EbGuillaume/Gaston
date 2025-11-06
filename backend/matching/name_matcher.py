"""Name-based metadata matching."""
from typing import List, Optional, Tuple

from loguru import logger

from backend.scrapers.base import BaseScraper, MetadataResult
from backend.scrapers.bedetheque import BedethequeScraper
from backend.scrapers.bdphile import BDPhileScraper
from backend.scrapers.cache import ScraperCache
from backend.utils.fuzzy import FuzzyMatcher


class NameMatcher:
    """Matches files to metadata based on filename."""

    def __init__(
        self,
        scrapers: Optional[List[BaseScraper]] = None,
        use_cache: bool = False,  # TEMPORAIRE: Désactivé pour debug
        min_confidence: float = 0.70,
    ):
        """
        Initialize name matcher.

        Args:
            scrapers: List of scrapers to use
            use_cache: Whether to use caching
            min_confidence: Minimum confidence threshold
        """
        self.scrapers = scrapers or []
        self.cache = ScraperCache() if use_cache else None
        self.min_confidence = min_confidence

        # Si aucun scraper fourni, créer BDPhile par défaut (Bedetheque est désactivé)
        if not self.scrapers:
            self.scrapers.append(BDPhileScraper(enabled=True))
            # self.scrapers.append(BedethequeScraper(enabled=False))  # Désactivé: protection anti-scraping

        # Trier par priorité
        self.scrapers.sort(key=lambda s: s.priority)

    async def match(
        self, filename: str, prefer_series: Optional[str] = None, full_path: Optional[str] = None
    ) -> List[MetadataResult]:
        """
        Match a filename to metadata.

        Args:
            filename: Filename to match
            prefer_series: If provided, boost results matching this series
            full_path: Full path of the file (optional). Used to extract series name
                      from parent folder if filename is generic (e.g., "Tome 01.pdf")

        Returns:
            List of metadata results sorted by confidence
        """
        logger.info(f"Matching filename: {filename}")

        # Extraire série et numéro du nom de fichier (avec dossier parent si fourni)
        series_name, volume_number = FuzzyMatcher.extract_series_and_number(filename, full_path)

        logger.debug(
            f"Extracted: series='{series_name}', volume={volume_number}"
        )

        # Construire la query de recherche
        search_query = series_name

        # Chercher dans tous les scrapers
        all_results = []

        for scraper in self.scrapers:
            if not scraper.is_enabled():
                continue

            # Vérifier le cache d'abord
            cached_results = None
            if self.cache:
                cached_results = self.cache.get(scraper.name, search_query)

            if cached_results:
                results = cached_results
            else:
                # Rechercher
                try:
                    results = await scraper.search(search_query, limit=10)

                    # Mettre en cache
                    if self.cache and results:
                        self.cache.set(scraper.name, search_query, results)

                except Exception as e:
                    logger.error(f"Error searching with {scraper.name}: {e}")
                    continue

            # Enrichir les résultats avec les détails complets des albums si possible
            if volume_number is not None and hasattr(scraper, 'enrich_with_album_details'):
                enriched_results = []
                for result in results:
                    try:
                        enriched = await scraper.enrich_with_album_details(result, volume_number)
                        enriched_results.append(enriched)
                    except Exception as e:
                        logger.warning(f"Error enriching result for {result.series_name}: {e}")
                        # Garder le résultat non enrichi en cas d'erreur
                        enriched_results.append(result)
                results = enriched_results

            # Filtrer par numéro de volume si connu
            if volume_number is not None:
                results = [
                    r for r in results
                    if r.volume_number is None or r.volume_number == volume_number
                ]

            # Boost results matching preferred series
            if prefer_series:
                for result in results:
                    if FuzzyMatcher.are_filenames_similar(
                        result.series_name, prefer_series, threshold=0.80
                    ):
                        result.confidence = min(1.0, result.confidence * 1.1)

            all_results.extend(results)

        # Préserver le volume_number extrait du filename si les résultats n'en ont pas
        if volume_number is not None and volume_number > 0:
            for result in all_results:
                if result.volume_number is None:
                    result.volume_number = volume_number
                    logger.debug(
                        f"Assigned volume_number={volume_number} from filename to {result.series_name}"
                    )

        # Filtrer par confiance minimale
        all_results = [r for r in all_results if r.confidence >= self.min_confidence]

        # Trier par confiance décroissante
        all_results.sort(key=lambda r: r.confidence, reverse=True)

        logger.info(
            f"Found {len(all_results)} matches for '{filename}' "
            f"(min confidence: {self.min_confidence})"
        )

        return all_results

    async def match_batch(
        self, filenames: List[str]
    ) -> dict[str, List[MetadataResult]]:
        """
        Match multiple filenames.

        Args:
            filenames: List of filenames

        Returns:
            Dictionary mapping filename to results
        """
        results = {}

        for filename in filenames:
            matches = await self.match(filename)
            results[filename] = matches

        return results

    async def get_best_match(
        self, filename: str, auto_validate_threshold: float = 0.90
    ) -> Optional[MetadataResult]:
        """
        Get the best match for a filename.

        Args:
            filename: Filename to match
            auto_validate_threshold: Threshold for auto-validation

        Returns:
            Best match or None
        """
        matches = await self.match(filename)

        if not matches:
            return None

        best = matches[0]

        # Log si validation automatique
        if best.confidence >= auto_validate_threshold:
            logger.info(
                f"Auto-validated match for '{filename}': "
                f"{best.series_name} #{best.volume_number} (confidence: {best.confidence:.2f})"
            )
        else:
            logger.info(
                f"Best match for '{filename}': "
                f"{best.series_name} #{best.volume_number} (confidence: {best.confidence:.2f}, "
                f"requires validation)"
            )

        return best

    def add_scraper(self, scraper: BaseScraper):
        """Add a scraper to the matcher."""
        self.scrapers.append(scraper)
        self.scrapers.sort(key=lambda s: s.priority)
        logger.info(f"Added scraper: {scraper.name}")

    def remove_scraper(self, name: str):
        """Remove a scraper by name."""
        self.scrapers = [s for s in self.scrapers if s.name != name]
        logger.info(f"Removed scraper: {name}")

    async def close(self):
        """Close all scrapers."""
        for scraper in self.scrapers:
            if hasattr(scraper, "close"):
                await scraper.close()
