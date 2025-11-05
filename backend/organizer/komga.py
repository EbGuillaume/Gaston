"""Komga organizer for library structure and naming."""
import re
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from backend.config import gaston_config


class KomgaOrganizer:
    """
    Organizes library according to Komga standards.

    Komga naming convention:
    - Series: /Series Name/Series Name 001 - Volume Title.extension
    - One-shots: /One-Shots/Series Name.extension
    - Integrales: /Series Name/Series Name - Intégrale Tome 1-5.extension
    """

    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize Komga organizer.

        Args:
            output_path: Output directory path (from config if not provided)
        """
        self.output_path = Path(output_path or gaston_config.output_path)
        self.naming_pattern = gaston_config.organization.naming_pattern
        self.create_oneshots = gaston_config.organization.create_oneshots_folder
        self.create_integrales = gaston_config.organization.create_integrales_folder
        self.separate_by_publisher = gaston_config.organization.separate_by_publisher

    def generate_filename(
        self,
        series_name: str,
        volume_number: Optional[int] = None,
        title: Optional[str] = None,
        extension: str = ".cbz",
        is_oneshot: bool = False,
        is_integrale: bool = False,
        integrale_range: Optional[str] = None,
    ) -> str:
        """
        Generate filename according to Komga standards.

        Args:
            series_name: Series name
            volume_number: Volume number (None for one-shots)
            title: Volume title
            extension: File extension
            is_oneshot: Is this a one-shot?
            is_integrale: Is this an integrale?
            integrale_range: Range for integrale (e.g., "1-5")

        Returns:
            Formatted filename
        """
        # Nettoyer le nom de série
        clean_series = self._sanitize_filename(series_name)

        # One-shot
        if is_oneshot or volume_number is None:
            return f"{clean_series}{extension}"

        # Intégrale
        if is_integrale:
            if integrale_range:
                return f"{clean_series} - Intégrale Tome {integrale_range}{extension}"
            return f"{clean_series} - Intégrale{extension}"

        # Série normale
        number_str = f"{volume_number:03d}" if volume_number else "000"

        if title:
            clean_title = self._sanitize_filename(title)
            return f"{clean_series} {number_str} - {clean_title}{extension}"
        else:
            return f"{clean_series} {number_str}{extension}"

    def generate_directory_path(
        self,
        series_name: str,
        publisher: Optional[str] = None,
        is_oneshot: bool = False,
    ) -> Path:
        """
        Generate directory path according to Komga structure.

        Args:
            series_name: Series name
            publisher: Publisher name (if separate_by_publisher is True)
            is_oneshot: Is this a one-shot?

        Returns:
            Full directory path
        """
        base_path = self.output_path

        # Séparation par éditeur si configuré
        if self.separate_by_publisher and publisher:
            clean_publisher = self._sanitize_filename(publisher)
            base_path = base_path / clean_publisher

        # One-shots dans un dossier spécial
        if is_oneshot and self.create_oneshots:
            return base_path / "One-Shots"

        # Série normale
        clean_series = self._sanitize_filename(series_name)
        return base_path / clean_series

    def generate_full_path(
        self,
        series_name: str,
        volume_number: Optional[int] = None,
        title: Optional[str] = None,
        extension: str = ".cbz",
        publisher: Optional[str] = None,
        is_oneshot: bool = False,
        is_integrale: bool = False,
        integrale_range: Optional[str] = None,
    ) -> Path:
        """
        Generate complete file path (directory + filename).

        Args:
            series_name: Series name
            volume_number: Volume number
            title: Volume title
            extension: File extension
            publisher: Publisher name
            is_oneshot: Is this a one-shot?
            is_integrale: Is this an integrale?
            integrale_range: Range for integrale

        Returns:
            Complete file path
        """
        directory = self.generate_directory_path(
            series_name=series_name,
            publisher=publisher,
            is_oneshot=is_oneshot,
        )

        filename = self.generate_filename(
            series_name=series_name,
            volume_number=volume_number,
            title=title,
            extension=extension,
            is_oneshot=is_oneshot,
            is_integrale=is_integrale,
            integrale_range=integrale_range,
        )

        return directory / filename

    def detect_oneshot(
        self, volume_number: Optional[int], title: Optional[str]
    ) -> bool:
        """
        Detect if a book is a one-shot.

        Args:
            volume_number: Volume number
            title: Volume title

        Returns:
            True if one-shot
        """
        # Pas de numéro de volume = one-shot
        if volume_number is None:
            return True

        # Titre contient "one-shot" ou équivalent
        if title:
            oneshot_keywords = [
                "one-shot",
                "one shot",
                "oneshot",
                "hors-série",
                "hors série",
                "hs",
            ]
            title_lower = title.lower()
            if any(keyword in title_lower for keyword in oneshot_keywords):
                return True

        return False

    def detect_integrale(
        self, title: Optional[str], volume_number: Optional[int]
    ) -> tuple[bool, Optional[str]]:
        """
        Detect if a book is an integrale and extract range.

        Args:
            title: Volume title
            volume_number: Volume number

        Returns:
            Tuple (is_integrale, range)
        """
        if not title:
            return False, None

        title_lower = title.lower()

        # Mots-clés d'intégrale
        integrale_keywords = [
            "intégrale",
            "integrale",
            "intégral",
            "integral",
            "omnibus",
            "compilation",
            "recueil",
        ]

        if not any(keyword in title_lower for keyword in integrale_keywords):
            return False, None

        # Extraire la plage si présente (ex: "tome 1-5", "T1-T5", "vol 1 à 5")
        patterns = [
            r"tome\s*(\d+)\s*[-àa]\s*(\d+)",
            r"t\.?\s*(\d+)\s*[-àa]\s*t?\.?\s*(\d+)",
            r"vol\.?\s*(\d+)\s*[-àa]\s*(\d+)",
            r"(\d+)\s*[-àa]\s*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, title_lower)
            if match:
                start, end = match.groups()
                return True, f"{start}-{end}"

        # Intégrale sans plage explicite
        return True, None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitize filename by removing invalid characters.

        Args:
            name: Original name

        Returns:
            Sanitized name
        """
        # Caractères interdits dans les noms de fichiers
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, "", name)

        # Nettoyer les espaces multiples
        sanitized = re.sub(r"\s+", " ", sanitized)

        # Supprimer les espaces en début/fin
        sanitized = sanitized.strip()

        # Supprimer les points en fin (problème Windows)
        sanitized = sanitized.rstrip(".")

        return sanitized

    def create_directory(self, path: Path) -> bool:
        """
        Create directory if it doesn't exist.

        Args:
            path: Directory path

        Returns:
            True if created or already exists
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory created/verified: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False

    def get_target_path_from_metadata(self, metadata: Dict[str, Any]) -> Path:
        """
        Generate target path from metadata dictionary.

        Args:
            metadata: Metadata dictionary with keys: series_name, volume_number, title, etc.

        Returns:
            Target file path
        """
        series_name = metadata.get("series_name", "Unknown")
        volume_number = metadata.get("volume_number")
        title = metadata.get("title")
        extension = metadata.get("extension", ".cbz")
        publisher = metadata.get("publisher")

        # Détecter one-shot et intégrale
        is_oneshot = self.detect_oneshot(volume_number, title)
        is_integrale, integrale_range = self.detect_integrale(title, volume_number)

        return self.generate_full_path(
            series_name=series_name,
            volume_number=volume_number,
            title=title,
            extension=extension,
            publisher=publisher,
            is_oneshot=is_oneshot,
            is_integrale=is_integrale,
            integrale_range=integrale_range,
        )
