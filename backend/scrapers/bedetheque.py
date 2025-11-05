"""Bedetheque scraper for French BD metadata."""
import asyncio
import re
from typing import List, Optional
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from backend.scrapers.base import BaseScraper, MetadataResult
from backend.utils.fuzzy import FuzzyMatcher


class BedethequeScraper(BaseScraper):
    """Scraper for Bedetheque.com."""

    BASE_URL = "https://www.bedetheque.com"
    SEARCH_URL = f"{BASE_URL}/search/albums"

    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize Bedetheque scraper.

        Args:
            rate_limit: Minimum seconds between requests
        """
        super().__init__(name="bedetheque", priority=1)
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = None

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session."""
        if self.session is None:
            self.session = httpx.AsyncClient(
                headers={
                    "User-Agent": "Gaston/0.1.0 (Library Organizer)",
                    "Accept-Language": "fr-FR,fr;q=0.9",
                },
                timeout=30.0,
            )
        return self.session

    async def _rate_limit(self):
        """Apply rate limiting."""
        import time

        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def _fetch(self, url: str) -> Optional[str]:
        """
        Fetch URL with rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None
        """
        await self._rate_limit()

        try:
            session = await self._get_session()
            response = await session.get(url)
            response.raise_for_status()
            return response.text

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def search(self, query: str, limit: int = 10) -> List[MetadataResult]:
        """
        Search for BD on Bedetheque.

        Args:
            query: Search query (series name or full title)
            limit: Maximum results to return

        Returns:
            List of metadata results
        """
        if not self.enabled:
            logger.warning(f"Scraper {self.name} is disabled")
            return []

        logger.info(f"Searching Bedetheque for: {query}")

        # Construire l'URL de recherche
        search_url = f"{self.SEARCH_URL}?RechSerie={quote(query)}"

        # Récupérer la page
        html = await self._fetch(search_url)
        if not html:
            return []

        # Parser les résultats
        results = self._parse_search_results(html, query, limit)

        logger.info(f"Found {len(results)} results on Bedetheque for '{query}'")
        return results

    def _parse_search_results(
        self, html: str, original_query: str, limit: int
    ) -> List[MetadataResult]:
        """
        Parse search results page.

        Args:
            html: HTML content
            original_query: Original search query
            limit: Maximum results

        Returns:
            List of metadata results
        """
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Trouver les résultats (structure peut varier)
        albums = soup.find_all("li", class_="li-album")

        if not albums:
            # Essayer une autre structure
            albums = soup.find_all("div", class_="album-item")

        for album in albums[:limit]:
            try:
                result = self._parse_album_item(album, original_query)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Error parsing album item: {e}")
                continue

        return results

    def _parse_album_item(self, album_element, original_query: str) -> Optional[MetadataResult]:
        """
        Parse a single album item from search results.

        Args:
            album_element: BeautifulSoup element
            original_query: Original search query

        Returns:
            MetadataResult or None
        """
        try:
            # Extraire le lien
            link = album_element.find("a")
            if not link:
                return None

            url = urljoin(self.BASE_URL, link.get("href", ""))

            # Extraire le titre complet
            title_elem = album_element.find("span", class_="titre") or link
            full_title = title_elem.get_text(strip=True) if title_elem else ""

            # Essayer d'extraire série, tome et titre
            series_name, volume_number, title = self._parse_title(full_title)

            # Extraire l'image de couverture
            img = album_element.find("img")
            cover_url = img.get("src") if img else None
            if cover_url and not cover_url.startswith("http"):
                cover_url = urljoin(self.BASE_URL, cover_url)

            # Extraire les auteurs (si présents)
            author_elem = album_element.find("span", class_="auteur")
            writers = []
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                writers = [a.strip() for a in author_text.split(",")]

            # Extraire l'éditeur (si présent)
            publisher_elem = album_element.find("span", class_="editeur")
            publisher = publisher_elem.get_text(strip=True) if publisher_elem else None

            # Calculer la confiance basée sur la similarité du nom
            confidence = FuzzyMatcher.calculate_token_similarity(original_query, series_name)

            return MetadataResult(
                source="bedetheque",
                confidence=confidence,
                series_name=series_name,
                volume_number=volume_number,
                title=title,
                writers=writers,
                publisher=publisher,
                cover_url=cover_url,
                url=url,
                raw_data={"full_title": full_title},
            )

        except Exception as e:
            logger.error(f"Error parsing album item: {e}")
            return None

    def _parse_title(self, full_title: str) -> tuple[str, Optional[int], Optional[str]]:
        """
        Parse full title to extract series, volume and title.

        Args:
            full_title: Full title string

        Returns:
            Tuple (series_name, volume_number, title)
        """
        # Patterns courants sur Bedetheque:
        # "Astérix - Tome 1 - Le Gaulois"
        # "Batman - 1 - The Dark Knight"
        # "Tintin - Les Cigares du Pharaon"

        # Pattern avec tome
        match = re.match(r"^(.+?)\s*-\s*(?:Tome|T\.?|Vol\.?)\s*(\d+)\s*-\s*(.+)$", full_title, re.I)
        if match:
            series = match.group(1).strip()
            volume = int(match.group(2))
            title = match.group(3).strip()
            return (series, volume, title)

        # Pattern avec juste un numéro
        match = re.match(r"^(.+?)\s*-\s*(\d+)\s*-\s*(.+)$", full_title)
        if match:
            series = match.group(1).strip()
            volume = int(match.group(2))
            title = match.group(3).strip()
            return (series, volume, title)

        # Pattern sans numéro
        match = re.match(r"^(.+?)\s*-\s*(.+)$", full_title)
        if match:
            series = match.group(1).strip()
            title = match.group(2).strip()
            return (series, None, title)

        # Pas de pattern reconnu, tout est la série
        return (full_title.strip(), None, None)

    async def get_by_id(self, item_id: str) -> Optional[MetadataResult]:
        """
        Get detailed metadata by Bedetheque ID.

        Args:
            item_id: Bedetheque album ID or URL

        Returns:
            Detailed metadata or None
        """
        if not self.enabled:
            return None

        # Si c'est juste un ID, construire l'URL
        if not item_id.startswith("http"):
            url = f"{self.BASE_URL}/BD/{item_id}"
        else:
            url = item_id

        logger.info(f"Fetching details from Bedetheque: {url}")

        html = await self._fetch(url)
        if not html:
            return None

        return self._parse_album_details(html, url)

    def _parse_album_details(self, html: str, url: str) -> Optional[MetadataResult]:
        """
        Parse detailed album page.

        Args:
            html: HTML content
            url: Album URL

        Returns:
            Detailed metadata result
        """
        soup = BeautifulSoup(html, "html.parser")

        try:
            # Extraire le titre
            title_elem = soup.find("h1")
            full_title = title_elem.get_text(strip=True) if title_elem else ""
            series_name, volume_number, title = self._parse_title(full_title)

            # Extraire la couverture
            cover_img = soup.find("img", class_="couv")
            cover_url = cover_img.get("src") if cover_img else None
            if cover_url and not cover_url.startswith("http"):
                cover_url = urljoin(self.BASE_URL, cover_url)

            # Extraire les informations dans le tableau
            info_dict = {}
            info_table = soup.find("div", class_="infos")
            if info_table:
                for row in info_table.find_all("li"):
                    label_elem = row.find("label")
                    if label_elem:
                        label = label_elem.get_text(strip=True).rstrip(":")
                        value = row.get_text(strip=True).replace(label + ":", "").strip()
                        info_dict[label] = value

            # Extraire les créateurs
            writers = []
            pencillers = []
            colorists = []

            if "Scénario" in info_dict:
                writers = [a.strip() for a in info_dict["Scénario"].split(",")]
            if "Dessin" in info_dict:
                pencillers = [a.strip() for a in info_dict["Dessin"].split(",")]
            if "Couleurs" in info_dict:
                colorists = [a.strip() for a in info_dict["Couleurs"].split(",")]

            # Extraire l'éditeur et la date
            publisher = info_dict.get("Editeur")
            publication_date = info_dict.get("Dépot légal")
            isbn = info_dict.get("ISBN")

            # Extraire le résumé
            summary_elem = soup.find("p", class_="resume")
            summary = summary_elem.get_text(strip=True) if summary_elem else None

            # Extraire le nombre de pages
            page_count = None
            if "Planches" in info_dict:
                try:
                    page_count = int(re.search(r"\d+", info_dict["Planches"]).group())
                except:
                    pass

            return MetadataResult(
                source="bedetheque",
                confidence=1.0,  # Confiance maximale car on a l'URL exacte
                series_name=series_name,
                volume_number=volume_number,
                title=title,
                summary=summary,
                writers=writers,
                pencillers=pencillers,
                colorists=colorists,
                publisher=publisher,
                publication_date=publication_date,
                isbn=isbn,
                page_count=page_count,
                cover_url=cover_url,
                url=url,
                raw_data=info_dict,
            )

        except Exception as e:
            logger.error(f"Error parsing album details: {e}")
            return None

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.aclose()
            self.session = None
