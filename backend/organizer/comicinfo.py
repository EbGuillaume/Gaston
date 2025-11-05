"""ComicInfo.xml generator for metadata injection."""
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger


class ComicInfoGenerator:
    """
    Generates ComicInfo.xml files for comic archives.

    ComicInfo.xml is a standard format for metadata in CBZ/CBR files.
    It's used by Komga, Komf, and other comic readers.
    """

    def __init__(self):
        """Initialize ComicInfo generator."""
        pass

    def generate(self, metadata: Dict[str, Any]) -> str:
        """
        Generate ComicInfo.xml content from metadata.

        Args:
            metadata: Dictionary with metadata fields

        Returns:
            XML string
        """
        root = ET.Element("ComicInfo")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")

        # Titre et série
        self._add_element_if_exists(root, "Title", metadata.get("title"))
        self._add_element_if_exists(root, "Series", metadata.get("series_name"))
        self._add_element_if_exists(root, "Number", metadata.get("volume_number"))

        # Résumé
        self._add_element_if_exists(root, "Summary", metadata.get("summary"))

        # Auteurs (writers, pencillers, inkers, colorists, letterers)
        self._add_creators(root, metadata)

        # Éditeur
        self._add_element_if_exists(root, "Publisher", metadata.get("publisher"))

        # Date de publication
        pub_date = metadata.get("publication_date")
        if pub_date:
            self._add_publication_date(root, pub_date)

        # ISBN
        self._add_element_if_exists(root, "ISBN", metadata.get("isbn"))

        # Nombre de pages
        self._add_element_if_exists(root, "PageCount", metadata.get("page_count"))

        # Genres et tags
        genres = metadata.get("genres")
        if genres:
            if isinstance(genres, str):
                genres = [g.strip() for g in genres.split(",")]
            self._add_element_if_exists(root, "Genre", ", ".join(genres))

        tags = metadata.get("tags")
        if tags:
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            self._add_element_if_exists(root, "Tags", ", ".join(tags))

        # Age rating
        self._add_element_if_exists(root, "AgeRating", metadata.get("age_rating"))

        # URL de couverture
        self._add_element_if_exists(root, "Web", metadata.get("url"))

        # Notes (source des métadonnées)
        source = metadata.get("source")
        if source:
            confidence = metadata.get("confidence_score")
            notes = f"Metadata from {source}"
            if confidence:
                notes += f" (confidence: {confidence:.2f})"
            self._add_element_if_exists(root, "Notes", notes)

        # Formater le XML avec indentation
        self._indent(root)
        tree = ET.ElementTree(root)

        # Convertir en string avec déclaration XML
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += ET.tostring(root, encoding="unicode")

        return xml_str

    def _add_element_if_exists(
        self, parent: ET.Element, tag: str, value: Any
    ) -> None:
        """
        Add XML element if value exists and is not None/empty.

        Args:
            parent: Parent XML element
            tag: Tag name
            value: Value to add
        """
        if value is not None and value != "" and value != []:
            element = ET.SubElement(parent, tag)
            element.text = str(value)

    def _add_creators(self, root: ET.Element, metadata: Dict[str, Any]) -> None:
        """
        Add creator information (writers, artists, etc.).

        Args:
            root: Root XML element
            metadata: Metadata dictionary
        """
        # Writers (scénaristes)
        writers = metadata.get("writers")
        if writers:
            if isinstance(writers, str):
                writers = [w.strip() for w in writers.split(",")]
            self._add_element_if_exists(root, "Writer", ", ".join(writers))

        # Pencillers (dessinateurs)
        pencillers = metadata.get("pencillers")
        if pencillers:
            if isinstance(pencillers, str):
                pencillers = [p.strip() for p in pencillers.split(",")]
            self._add_element_if_exists(root, "Penciller", ", ".join(pencillers))

        # Inkers (encreurs)
        inkers = metadata.get("inkers")
        if inkers:
            if isinstance(inkers, str):
                inkers = [i.strip() for i in inkers.split(",")]
            self._add_element_if_exists(root, "Inker", ", ".join(inkers))

        # Colorists (coloristes)
        colorists = metadata.get("colorists")
        if colorists:
            if isinstance(colorists, str):
                colorists = [c.strip() for c in colorists.split(",")]
            self._add_element_if_exists(root, "Colorist", ", ".join(colorists))

        # Letterers (lettreurs)
        letterers = metadata.get("letterers")
        if letterers:
            if isinstance(letterers, str):
                letterers = [l.strip() for l in letterers.split(",")]
            self._add_element_if_exists(root, "Letterer", ", ".join(letterers))

    def _add_publication_date(self, root: ET.Element, pub_date: str) -> None:
        """
        Add publication date in correct format.

        Args:
            root: Root XML element
            pub_date: Publication date string
        """
        # Essayer de parser différents formats de date
        date_formats = [
            "%Y-%m-%d",  # ISO format
            "%d/%m/%Y",  # French format
            "%d %B %Y",  # "15 janvier 2020"
            "%B %Y",  # "janvier 2020"
            "%Y",  # Year only
        ]

        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(pub_date, fmt)
                break
            except ValueError:
                continue

        if parsed_date:
            # Format ComicInfo: Year, Month, Day
            self._add_element_if_exists(root, "Year", parsed_date.year)
            self._add_element_if_exists(root, "Month", parsed_date.month)
            if parsed_date.day != 1:  # Si jour != 1, on l'ajoute
                self._add_element_if_exists(root, "Day", parsed_date.day)
        else:
            # Si on ne peut pas parser, essayer d'extraire au moins l'année
            import re

            year_match = re.search(r"\b(19|20)\d{2}\b", pub_date)
            if year_match:
                self._add_element_if_exists(root, "Year", int(year_match.group()))

    @staticmethod
    def _indent(elem: ET.Element, level: int = 0) -> None:
        """
        Add indentation to XML for pretty printing.

        Args:
            elem: Element to indent
            level: Current indentation level
        """
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                ComicInfoGenerator._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def generate_from_db_metadata(self, db_metadata) -> str:
        """
        Generate ComicInfo.xml from database metadata object.

        Args:
            db_metadata: Database metadata object

        Returns:
            XML string
        """
        metadata_dict = {
            "title": db_metadata.title,
            "series_name": db_metadata.series_name,
            "volume_number": db_metadata.volume_number,
            "summary": db_metadata.summary,
            "writers": db_metadata.writers,
            "pencillers": db_metadata.pencillers,
            "inkers": db_metadata.inkers,
            "colorists": db_metadata.colorists,
            "letterers": db_metadata.letterers,
            "publisher": db_metadata.publisher,
            "publication_date": db_metadata.publication_date,
            "isbn": db_metadata.isbn,
            "page_count": db_metadata.page_count,
            "genres": db_metadata.genres,
            "tags": db_metadata.tags,
            "age_rating": db_metadata.age_rating,
            "url": db_metadata.raw_data.get("url") if db_metadata.raw_data else None,
            "source": db_metadata.source,
            "confidence_score": db_metadata.confidence_score,
        }

        return self.generate(metadata_dict)
