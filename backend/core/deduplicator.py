"""Duplicate detection for library files."""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from backend.config import gaston_config
from backend.database.crud import BookCRUD, DuplicateCRUD
from backend.database.models import Book, Duplicate
from backend.utils.archive import ArchiveHandler
from backend.utils.fuzzy import FuzzyMatcher
from backend.utils.hash import HashCalculator


class Deduplicator:
    """Détecteur de doublons pour les fichiers de bibliothèque."""

    def __init__(
        self,
        db: Session,
        similarity_threshold: Optional[float] = None,
        format_priority: Optional[List[str]] = None,
    ):
        """
        Initialize deduplicator.

        Args:
            db: Session de base de données
            similarity_threshold: Seuil de similarité pour fuzzy matching
            format_priority: Ordre de priorité des formats
        """
        self.db = db
        self.similarity_threshold = (
            similarity_threshold or gaston_config.deduplication.similarity_threshold
        )
        self.format_priority = format_priority or gaston_config.deduplication.format_priority

    def detect_exact_duplicates(self, books: List[Book]) -> List[Tuple[Book, Book]]:
        """
        Détecte les doublons exacts par hash de fichier.

        Args:
            books: Liste de livres à analyser

        Returns:
            Liste de paires de livres dupliqués
        """
        duplicates = []
        hash_map = {}

        for book in books:
            if not book.file_hash:
                continue

            if book.file_hash in hash_map:
                # Doublon trouvé
                original = hash_map[book.file_hash]
                duplicates.append((original, book))
                logger.info(f"Exact duplicate found: {book.filename} vs {original.filename}")
            else:
                hash_map[book.file_hash] = book

        return duplicates

    def detect_fuzzy_duplicates(self, books: List[Book]) -> List[Tuple[Book, Book, float]]:
        """
        Détecte les doublons par similarité de noms.

        Args:
            books: Liste de livres à analyser

        Returns:
            Liste de tuples (book1, book2, similarity_score)
        """
        duplicates = []
        filenames = [book.filename for book in books]

        # Grouper les fichiers similaires
        groups = FuzzyMatcher.group_similar_files(filenames, self.similarity_threshold)

        for group in groups:
            # Trouver les livres correspondants
            group_books = [b for b in books if b.filename in group]

            # Créer des paires
            for i in range(len(group_books)):
                for j in range(i + 1, len(group_books)):
                    book1 = group_books[i]
                    book2 = group_books[j]

                    # Calculer le score exact
                    score = FuzzyMatcher.calculate_token_similarity(
                        book1.filename, book2.filename
                    )

                    if score >= self.similarity_threshold:
                        duplicates.append((book1, book2, score))
                        logger.info(
                            f"Fuzzy duplicate found: {book1.filename} vs {book2.filename} "
                            f"(score: {score:.2f})"
                        )

        return duplicates

    def detect_perceptual_duplicates(
        self, books: List[Book], threshold: int = 10
    ) -> List[Tuple[Book, Book, int]]:
        """
        Détecte les doublons par hash perceptuel des couvertures.

        Args:
            books: Liste de livres à analyser
            threshold: Seuil de différence (plus bas = plus strict)

        Returns:
            Liste de tuples (book1, book2, distance)
        """
        duplicates = []

        # Extraire les couvertures et calculer les hash
        covers = {}
        for book in books:
            try:
                # Extraire la couverture
                handler = ArchiveHandler(book.original_path)
                cover = handler.extract_cover()

                if cover:
                    # Calculer le hash perceptuel directement depuis PIL Image
                    import imagehash

                    phash = imagehash.phash(cover)
                    covers[book.id] = (book, str(phash))

            except Exception as e:
                logger.warning(f"Could not extract cover from {book.filename}: {e}")
                continue

        # Comparer les hash
        book_ids = list(covers.keys())
        for i in range(len(book_ids)):
            for j in range(i + 1, len(book_ids)):
                book1, hash1 = covers[book_ids[i]]
                book2, hash2 = covers[book_ids[j]]

                distance = HashCalculator.compare_perceptual_hashes(hash1, hash2)

                if 0 <= distance <= threshold:
                    duplicates.append((book1, book2, distance))
                    logger.info(
                        f"Perceptual duplicate found: {book1.filename} vs {book2.filename} "
                        f"(distance: {distance})"
                    )

        return duplicates

    def select_best_file(self, book1: Book, book2: Book) -> Book:
        """
        Sélectionne le meilleur fichier entre deux doublons.

        Critères :
        1. Priorité de format
        2. Taille de fichier (plus grand = meilleur)

        Args:
            book1: Premier livre
            book2: Deuxième livre

        Returns:
            Le meilleur livre
        """
        # Vérifier la priorité de format
        ext1 = book1.extension.lower().replace(".", "")
        ext2 = book2.extension.lower().replace(".", "")

        try:
            priority1 = self.format_priority.index(ext1)
        except ValueError:
            priority1 = 999

        try:
            priority2 = self.format_priority.index(ext2)
        except ValueError:
            priority2 = 999

        if priority1 != priority2:
            return book1 if priority1 < priority2 else book2

        # Même priorité, comparer la taille
        if book1.file_size and book2.file_size:
            return book1 if book1.file_size >= book2.file_size else book2

        # Par défaut, retourner le premier
        return book1

    def run_full_detection(self, books: List[Book]) -> Dict:
        """
        Exécute la détection complète de doublons.

        Args:
            books: Liste de livres à analyser

        Returns:
            Dictionnaire avec les résultats
        """
        logger.info(f"Starting duplicate detection for {len(books)} books")

        results = {
            "total_books": len(books),
            "exact_duplicates": [],
            "fuzzy_duplicates": [],
            "perceptual_duplicates": [],
            "total_duplicates": 0,
        }

        # Détection par hash exact
        if "hash_exact" in gaston_config.deduplication.methods:
            exact = self.detect_exact_duplicates(books)
            results["exact_duplicates"] = exact
            logger.info(f"Found {len(exact)} exact duplicates")

        # Détection par fuzzy matching
        if "name_fuzzy" in gaston_config.deduplication.methods:
            fuzzy = self.detect_fuzzy_duplicates(books)
            results["fuzzy_duplicates"] = fuzzy
            logger.info(f"Found {len(fuzzy)} fuzzy duplicates")

        # Détection par hash perceptuel
        if "image_perceptual" in gaston_config.deduplication.methods:
            perceptual = self.detect_perceptual_duplicates(books)
            results["perceptual_duplicates"] = perceptual
            logger.info(f"Found {len(perceptual)} perceptual duplicates")

        results["total_duplicates"] = (
            len(results["exact_duplicates"])
            + len(results["fuzzy_duplicates"])
            + len(results["perceptual_duplicates"])
        )

        logger.info(f"Duplicate detection completed: {results['total_duplicates']} total")

        return results

    def save_duplicates_to_db(self, duplicates: List[Tuple[Book, Book]], duplicate_type: str):
        """
        Sauvegarde les doublons détectés en base de données.

        Args:
            duplicates: Liste de paires de livres dupliqués
            duplicate_type: Type de doublon (hash_exact, name_fuzzy, hash_perceptual)
        """
        for book1, book2 in duplicates:
            # Vérifier si le doublon existe déjà
            existing = (
                self.db.query(Duplicate)
                .filter(
                    (
                        (Duplicate.book_id_1 == book1.id)
                        & (Duplicate.book_id_2 == book2.id)
                    )
                    | (
                        (Duplicate.book_id_1 == book2.id)
                        & (Duplicate.book_id_2 == book1.id)
                    )
                )
                .first()
            )

            if not existing:
                # Déterminer le meilleur fichier
                best = self.select_best_file(book1, book2)

                DuplicateCRUD.create(
                    self.db,
                    book_id_1=book1.id,
                    book_id_2=book2.id,
                    duplicate_type=duplicate_type,
                    similarity_score=1.0 if duplicate_type == "hash_exact" else 0.85,
                    kept_book_id=best.id,
                    action="pending",
                )

                # Marquer les livres comme doublons
                BookCRUD.update(self.db, book1.id, is_duplicate=True)
                BookCRUD.update(self.db, book2.id, is_duplicate=True)

    def move_duplicate_to_folder(self, book: Book, scan_id: Optional[str] = None) -> bool:
        """
        Déplace un doublon vers le dossier /duplicates.

        Args:
            book: Livre à déplacer
            scan_id: Identifiant du scan (pour organiser par date)

        Returns:
            True si le déplacement a réussi
        """
        try:
            source = Path(book.original_path)

            if not source.exists():
                logger.error(f"Source file does not exist: {source}")
                return False

            # Créer le dossier de destination
            if scan_id is None:
                scan_id = datetime.now().strftime("%Y-%m-%d_scan_%H%M%S")

            duplicates_dir = Path(gaston_config.special_folders.duplicates) / scan_id
            duplicates_dir.mkdir(parents=True, exist_ok=True)

            # Déplacer le fichier
            destination = duplicates_dir / source.name

            # Gérer les conflits de noms
            counter = 1
            while destination.exists():
                stem = source.stem
                ext = source.suffix
                destination = duplicates_dir / f"{stem}_{counter}{ext}"
                counter += 1

            shutil.move(str(source), str(destination))
            logger.info(f"Moved duplicate {source.name} to {destination}")

            # Mettre à jour le chemin dans la DB
            BookCRUD.update(self.db, book.id, new_path=str(destination))

            return True

        except Exception as e:
            logger.error(f"Error moving duplicate {book.filename}: {e}")
            return False
