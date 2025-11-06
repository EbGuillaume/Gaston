"""BDPhile.fr scraper for French BD/Comics metadata."""
import re
from typing import List, Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from backend.scrapers.base import BaseScraper, MetadataResult


class BDPhileScraper(BaseScraper):
    """Scraper for bdphile.fr."""

    BASE_URL = "https://www.bdphile.fr"
    SEARCH_URL = f"{BASE_URL}/search/series/"

    def __init__(self, rate_limit: float = 1.0, enabled: bool = True, priority: int = 1):
        """
        Initialize BDPhile scraper.

        Args:
            rate_limit: Minimum seconds between requests
            enabled: Whether scraper is enabled
            priority: Priority (lower = higher priority)
        """
        super().__init__(name="bdphile", priority=priority)
        self.enabled = enabled
        self.rate_limit = rate_limit
        self._last_request_time = 0
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            timeout=10.0,
            follow_redirects=True,
        )

    def is_enabled(self) -> bool:
        """Check if scraper is enabled."""
        return self.enabled

    async def search(self, query: str, limit: int = 10) -> List[MetadataResult]:
        """
        Search for BD on BDPhile.

        Args:
            query: Search query (series name or full title)
            limit: Maximum results to return

        Returns:
            List of metadata results
        """
        if not self.enabled:
            logger.warning(f"Scraper {self.name} is disabled")
            return []

        logger.info(f"Searching BDPhile for: {query}")

        # Construire l'URL de recherche
        search_url = f"{self.SEARCH_URL}?q={quote(query)}"

        # Récupérer la page
        html = await self._fetch(search_url)
        if not html:
            return []

        # Parser les résultats
        results = self._parse_search_results(html, query, limit)

        logger.info(f"Found {len(results)} results on BDPhile for '{query}'")
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

        # Trouver les liens vers les séries
        # Format BD: <a href="https://www.bdphile.fr/series/view/124/">Astérix</a>
        # Format Comics: <a href="https://www.bdphile.fr/series/comics/4315-y-le-dernier-homme">Y le dernier homme</a>
        links = soup.find_all("a", href=True)
        serie_links = [
            link for link in links
            if "/series/view/" in link.get("href", "") or "/series/comics/" in link.get("href", "")
        ]

        if not serie_links:
            logger.debug(f"No series links found for '{original_query}'")
            return []

        # Dédupliquer par URL
        seen_urls = set()
        unique_links = []
        for link in serie_links:
            url = link.get("href")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_links.append(link)

        # Parser TOUS les résultats (pas de limite ici)
        for link in unique_links:
            try:
                url = link.get("href")
                if not url.startswith("http"):
                    url = self.BASE_URL + url

                series_name = link.get_text(strip=True)

                # Extraire l'ID de la série depuis l'URL
                # Format BD: /series/view/124/
                # Format Comics: /series/comics/4315-y-le-dernier-homme
                series_id = None
                series_type = "bd"

                match_bd = re.search(r"/series/view/(\d+)", url)
                match_comics = re.search(r"/series/comics/(\d+)", url)

                if match_bd:
                    series_id = int(match_bd.group(1))
                    series_type = "bd"
                elif match_comics:
                    series_id = int(match_comics.group(1))
                    series_type = "comics"
                else:
                    continue

                # Calculer un score de confiance basé sur la similarité du nom
                confidence = self._calculate_confidence(original_query, series_name)

                # Créer un résultat basique (détails à récupérer plus tard)
                result = MetadataResult(
                    source=self.name,
                    confidence=confidence,
                    series_name=series_name,
                    url=url,
                    raw_data={"series_id": series_id, "series_type": series_type},
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error parsing search result: {e}")
                continue

        # Trier par confiance décroissante AVANT de limiter
        results.sort(key=lambda x: x.confidence, reverse=True)

        # Limiter APRÈS le tri
        results = results[:limit]

        return results

    async def get_series_details(self, series_id: int) -> Optional[dict]:
        """
        Get detailed information about a series.

        Args:
            series_id: BDPhile series ID

        Returns:
            Dictionary with series details
        """
        url = f"{self.BASE_URL}/series/view/{series_id}/"

        html = await self._fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Titre de la série
        title_elem = soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else None

        # Récupérer les albums
        albums = []

        # Les albums sont dans un tableau
        # Format BD: <td><a href="/album/bd/163670-asterix-2-la-serpe-d-or">La Serpe d'or</a></td>
        # Format Comics: <a href="/album/comics/62942-y-le-dernier-homme-2-un-petit-coin-de-paradis">...</a>
        album_links = soup.find_all("a", href=lambda x: x and ("/album/bd/" in x or "/album/comics/" in x))

        for link in album_links:
            try:
                album_url = link.get("href")
                if not album_url.startswith("http"):
                    album_url = self.BASE_URL + album_url

                album_title = link.get_text(strip=True)

                # Extraire l'ID depuis l'URL
                # Format BD: /album/bd/163670-asterix-2-la-serpe-d-or
                # Format Comics: /album/comics/133975-y-le-dernier-homme-1-no-man-s-land
                match_id = re.search(r"/album/(?:bd|comics)/(\d+)", album_url)
                if not match_id:
                    logger.debug(f"Could not extract album ID from URL: {album_url}")
                    continue

                album_id = int(match_id.group(1))

                # Extraire le numéro de tome depuis l'URL
                # Plusieurs patterns possibles:
                # - asterix-2-la-serpe-d-or (chiffre seul après le nom de série)
                # - y-le-dernier-homme-1-no-man-s-land (chiffre avant le titre)
                # - deadpool-tome-5-deadpool-vs-thanos (avec "tome")
                volume_number = None

                # Essayer de trouver un pattern comme "-NUMERO-" ou "-tome-NUMERO-"
                patterns = [
                    r"-(\d+)-[a-z]",  # -1-no (chiffre suivi d'un tiret et d'une lettre)
                    r"-tome-(\d+)",   # -tome-5
                    r"-t(\d+)-",      # -t5-
                    r"-vol-(\d+)",    # -vol-3
                    r"-volume-(\d+)", # -volume-2
                ]

                for pattern in patterns:
                    match_vol = re.search(pattern, album_url, re.I)
                    if match_vol:
                        volume_number = int(match_vol.group(1))
                        logger.debug(f"Found volume {volume_number} in URL using pattern: {pattern}")
                        break

                # Si toujours pas trouvé, essayer d'extraire depuis le titre du lien
                if volume_number is None:
                    # Chercher "Tome X", "T.X", "#X", "Volume X" dans le titre
                    title_patterns = [
                        r"(?:tome|t\.?)\s*(\d+)",
                        r"#(\d+)",
                        r"volume\s*(\d+)",
                        r"^(\d+)\s*[-:]",  # Commence par un nombre
                    ]

                    for pattern in title_patterns:
                        match_title = re.search(pattern, album_title, re.I)
                        if match_title:
                            volume_number = int(match_title.group(1))
                            logger.debug(f"Found volume {volume_number} in title '{album_title}'")
                            break

                albums.append({
                    "id": album_id,
                    "title": album_title,
                    "volume_number": volume_number,
                    "url": album_url,
                })

                logger.debug(
                    f"Parsed album: id={album_id}, vol={volume_number}, "
                    f"title='{album_title[:50]}...', url={album_url}"
                )

            except Exception as e:
                logger.debug(f"Error parsing album link: {e}")
                continue

        return {
            "id": series_id,
            "title": title,
            "albums": albums,
            "url": url,
        }

    async def enrich_with_album_details(
        self, result: MetadataResult, volume_number: Optional[int] = None
    ) -> MetadataResult:
        """
        Enrich a search result with full album details.

        Args:
            result: Basic search result with series info
            volume_number: Volume number to look for (if not in result)

        Returns:
            Enriched MetadataResult with complete album information
        """
        # Utiliser le volume_number fourni ou celui du résultat
        vol_num = volume_number or result.volume_number

        if not vol_num:
            logger.debug(f"No volume number provided for enrichment of '{result.series_name}'")
            return result

        # Récupérer l'ID de la série depuis raw_data
        series_id = result.raw_data.get("series_id")
        if not series_id:
            logger.warning(f"No series_id in result for '{result.series_name}'")
            return result

        logger.info(f"Enriching '{result.series_name}' tome {vol_num} from series {series_id}")

        # Récupérer les albums de la série
        series_details = await self.get_series_details(series_id)
        if not series_details or not series_details.get("albums"):
            logger.warning(f"No albums found for series {series_id}")
            return result

        # Chercher l'album correspondant au numéro de tome
        matching_album = None
        for album in series_details["albums"]:
            if album.get("volume_number") == vol_num:
                matching_album = album
                break

        if not matching_album:
            # Afficher la liste des albums disponibles pour debug
            available_volumes = [
                a.get("volume_number") for a in series_details["albums"]
                if a.get("volume_number") is not None
            ]
            logger.warning(
                f"Album tome {vol_num} not found in series {series_id} "
                f"({len(series_details['albums'])} albums). "
                f"Available volumes: {sorted(set(available_volumes))}"
            )
            return result

        # Récupérer les détails complets de l'album
        album_id = matching_album["id"]
        album_type = result.raw_data.get("series_type", "bd")
        logger.info(f"Fetching details for album {album_id} (type: {album_type})")

        album_result = await self.get_album_details(album_id, album_type)

        if album_result:
            # Préserver la confidence du résultat original
            album_result.confidence = result.confidence

            # Si l'album n'a pas de volume_number (page sans champ "Titre"),
            # utiliser celui de la série
            if album_result.volume_number is None and matching_album.get("volume_number"):
                album_result.volume_number = matching_album["volume_number"]

            # Si pas de titre spécifique, utiliser le titre de l'album depuis la série
            if album_result.title is None and matching_album.get("title"):
                album_result.title = matching_album["title"]

            return album_result

        return result

    async def get_by_id(self, item_id: str) -> Optional[MetadataResult]:
        """
        Get metadata by ID (implements abstract method).

        Args:
            item_id: BDPhile album ID (as string)

        Returns:
            MetadataResult with complete album information
        """
        try:
            album_id = int(item_id)
            return await self.get_album_details(album_id)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid album ID: {item_id} - {e}")
            return None

    async def get_album_details(self, album_id: int, album_type: str = "bd") -> Optional[MetadataResult]:
        """
        Get detailed information about an album.

        Args:
            album_id: BDPhile album ID
            album_type: Type of album ("bd" or "comics")

        Returns:
            MetadataResult with complete album information
        """
        # Essayer d'abord avec le type spécifié, puis l'autre si ça échoue
        for try_type in [album_type, "comics" if album_type == "bd" else "bd"]:
            url = f"{self.BASE_URL}/album/{try_type}/{album_id}"

            logger.debug(f"Fetching album details from: {url}")
            html = await self._fetch(url)

            if html and "404" not in html and "Page non trouvée" not in html:
                break
        else:
            logger.warning(f"Could not fetch album {album_id} (tried bd and comics)")
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Parser les détails
        details = self._parse_album_details(soup, url)

        if not details:
            return None

        # Créer le résultat
        result = MetadataResult(
            source=self.name,
            confidence=1.0,  # Détails directs = confiance max
            series_name=details.get("series_name", ""),
            volume_number=details.get("volume_number"),
            title=details.get("title"),
            summary=details.get("summary"),
            writers=details.get("writers", []),
            pencillers=details.get("pencillers", []),
            publisher=details.get("publisher"),
            publication_date=details.get("publication_date"),
            isbn=details.get("isbn"),
            page_count=details.get("page_count"),
            cover_url=details.get("cover_url"),
            url=url,
            raw_data=details,
        )

        return result

    def _parse_album_details(self, soup: BeautifulSoup, url: str) -> Optional[dict]:
        """
        Parse album details from BeautifulSoup object.

        Args:
            soup: BeautifulSoup parsed HTML
            url: Album URL

        Returns:
            Dictionary with album details
        """
        details = {}

        # Titre (peut contenir série + tome)
        title_elem = soup.find("h1")
        if title_elem:
            full_title = title_elem.get_text(strip=True)
            # Séparer série et tome si format "SérieNuméro"
            # Ex: "AstérixFR" ou "Astérix"
            details["full_title"] = full_title

        # Informations dans les dt/dd
        dts = soup.find_all("dt")

        for dt in dts:
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next("dd")
            if not dd:
                continue

            value = dd.get_text(strip=True)

            if "scénario" in label or "scenario" in label:
                # Peut avoir plusieurs auteurs séparés par des virgules
                details["writers"] = [w.strip() for w in value.split(",")]

            elif "dessin" in label:
                details["pencillers"] = [p.strip() for p in value.split(",")]

            elif "éditeur" in label or "editeur" in label:
                details["publisher"] = value

            elif "date de publication" in label:
                details["publication_date"] = value

            elif "ean" in label or "isbn" in label:
                # Nettoyer l'ISBN
                isbn = re.sub(r"[^0-9X-]", "", value)
                if isbn and isbn != "Sans ISBN":
                    details["isbn"] = isbn

            elif "titre" in label:
                # Titre complet: "Tome X : Titre"
                title_text = value
                # Extraire tome et titre
                match = re.match(r"Tome\s+(\d+)\s*:\s*(.+)", title_text, re.I)
                if match:
                    details["volume_number"] = int(match.group(1))
                    details["title"] = match.group(2).strip()
                else:
                    details["title"] = title_text

            elif "format" in label:
                # Format peut contenir le nombre de pages
                # Ex: "Cartonné - 48 pages - 10.5€"
                match = re.search(r"(\d+)\s+pages?", value, re.I)
                if match:
                    details["page_count"] = int(match.group(1))

        # Image de couverture
        # Format: <img ... src="https://static.bdphile.fr/data/cover-163670-w350.jpg" />
        cover_img = soup.find("img", src=re.compile(r"cover-\d+"))
        if cover_img:
            details["cover_url"] = cover_img.get("src")

        # Synopsis
        synopsis_div = soup.find("div", class_="synopsis")
        if not synopsis_div:
            synopsis_div = soup.find("div", id="synopsis")
        if synopsis_div:
            details["summary"] = synopsis_div.get_text(strip=True)

        # Déduire le nom de série depuis le titre complet si pas trouvé
        if "series_name" not in details and "full_title" in details:
            # Supprimer les suffixes de langue (FR, US, etc.)
            series_name = re.sub(r"(FR|US|UK|JP)$", "", details["full_title"]).strip()
            details["series_name"] = series_name

        return details if details else None

    def _calculate_confidence(self, query: str, result_name: str) -> float:
        """
        Calculate confidence score for a search result.

        Args:
            query: Original search query
            result_name: Name from search result

        Returns:
            Confidence score between 0 and 1
        """
        import re

        # Normaliser en retirant la ponctuation et en minuscules
        def normalize(text: str) -> str:
            # Retirer la ponctuation et mettre en minuscules
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            # Enlever les espaces multiples
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        query_normalized = normalize(query)
        result_normalized = normalize(result_name)

        # Exact match (après normalisation)
        if query_normalized == result_normalized:
            return 1.0

        # Contains query (après normalisation)
        if query_normalized in result_normalized:
            return 0.95

        # Result contains query words
        query_words = set(query_normalized.split())
        result_words = set(result_normalized.split())

        if query_words & result_words:  # Intersection
            ratio = len(query_words & result_words) / len(query_words)
            return 0.7 + (ratio * 0.25)  # 0.7 to 0.95

        # Fallback: simple similarity
        return 0.5

    async def _wait_rate_limit(self):
        """Wait for rate limit before making a request."""
        import time
        import asyncio

        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit:
            wait_time = self.rate_limit - time_since_last
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()

    async def _fetch(self, url: str) -> Optional[str]:
        """
        Fetch URL with rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None
        """
        await self._wait_rate_limit()

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
