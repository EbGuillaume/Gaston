"""File scanner for detecting books in directories."""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from backend.config import gaston_config


class FileScanner:
    """Scanner pour détecter les fichiers dans les bibliothèques."""

    def __init__(self, max_file_size: Optional[int] = None):
        """
        Initialize the file scanner.

        Args:
            max_file_size: Taille maximale des fichiers en bytes (None = utiliser config)
        """
        self.max_file_size = max_file_size or gaston_config.scanning.max_file_size
        self.supported_extensions = gaston_config.scanning.file_extensions
        self.ignore_hidden = gaston_config.scanning.ignore_hidden

    def scan_directory(self, directory: str) -> List[Dict]:
        """
        Scan un répertoire pour trouver les fichiers supportés.

        Args:
            directory: Chemin du répertoire à scanner

        Returns:
            Liste de dictionnaires contenant les informations des fichiers trouvés
        """
        directory_path = Path(directory)

        if not directory_path.exists():
            logger.error(f"Directory does not exist: {directory}")
            return []

        if not directory_path.is_dir():
            logger.error(f"Path is not a directory: {directory}")
            return []

        logger.info(f"Scanning directory: {directory}")

        files = []
        for root, dirs, filenames in os.walk(directory_path):
            # Ignorer les dossiers cachés si configuré
            if self.ignore_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                filenames = [f for f in filenames if not f.startswith(".")]

            for filename in filenames:
                file_path = Path(root) / filename

                # Vérifier l'extension
                if file_path.suffix.lower() not in self.supported_extensions:
                    continue

                # Vérifier la taille du fichier
                try:
                    file_size = file_path.stat().st_size
                    if file_size > self.max_file_size:
                        logger.warning(
                            f"File too large ({file_size} bytes), skipping: {file_path}"
                        )
                        continue
                except Exception as e:
                    logger.error(f"Error getting file size for {file_path}: {e}")
                    continue

                # Ajouter le fichier à la liste
                file_info = {
                    "path": str(file_path),
                    "filename": filename,
                    "extension": file_path.suffix.lower(),
                    "size": file_size,
                    "directory": str(Path(root)),
                }

                files.append(file_info)

        logger.info(f"Found {len(files)} files in {directory}")
        return files

    def scan_multiple_directories(self, directories: List[str]) -> List[Dict]:
        """
        Scan plusieurs répertoires.

        Args:
            directories: Liste des chemins de répertoires à scanner

        Returns:
            Liste de dictionnaires contenant les informations des fichiers trouvés
        """
        all_files = []

        for directory in directories:
            files = self.scan_directory(directory)
            all_files.extend(files)

        logger.info(f"Total files found across all directories: {len(all_files)}")
        return all_files

    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
        """
        Calcule le hash d'un fichier.

        Args:
            file_path: Chemin du fichier
            algorithm: Algorithme de hash (md5, sha256)

        Returns:
            Hash du fichier en hexadécimal, ou None en cas d'erreur
        """
        hash_func = hashlib.new(algorithm)

        try:
            with open(file_path, "rb") as f:
                # Lire le fichier par blocs pour économiser la mémoire
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)

            return hash_func.hexdigest()

        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None

    @staticmethod
    def is_file_corrupted(file_path: str) -> bool:
        """
        Vérifie si un fichier est corrompu (basique).

        Args:
            file_path: Chemin du fichier

        Returns:
            True si le fichier semble corrompu
        """
        try:
            # Vérification basique : peut-on ouvrir le fichier ?
            with open(file_path, "rb") as f:
                # Essayer de lire le début du fichier
                f.read(1024)
            return False

        except Exception as e:
            logger.warning(f"File appears to be corrupted: {file_path} - {e}")
            return True

    def get_file_type(self, file_path: str) -> Optional[str]:
        """
        Détermine le type de fichier basé sur l'extension.

        Args:
            file_path: Chemin du fichier

        Returns:
            Type de fichier ('BD', 'Comic', 'Manga', 'Book') ou None
        """
        extension = Path(file_path).suffix.lower()

        # Pour l'instant, on ne peut pas distinguer BD/Comic/Manga sans métadonnées
        # On retourne un type générique
        if extension in [".cbz", ".cbr"]:
            return "Comic"  # Type générique pour les comics/BD
        elif extension == ".epub":
            return "Book"
        elif extension == ".pdf":
            return "Book"  # Peut être BD ou Book, à affiner avec métadonnées

        return None

    def scan_and_analyze(self, directory: str) -> Dict:
        """
        Scan un répertoire et analyse les fichiers.

        Args:
            directory: Chemin du répertoire à scanner

        Returns:
            Dictionnaire avec statistiques et liste des fichiers
        """
        files = self.scan_directory(directory)

        stats = {
            "total_files": len(files),
            "by_extension": {},
            "total_size": 0,
            "corrupted": [],
        }

        analyzed_files = []

        for file_info in files:
            # Calculer le hash
            file_hash = self.calculate_file_hash(file_info["path"])
            file_info["hash"] = file_hash

            # Vérifier si corrompu
            is_corrupted = self.is_file_corrupted(file_info["path"])
            file_info["is_corrupted"] = is_corrupted

            if is_corrupted:
                stats["corrupted"].append(file_info["path"])

            # Déterminer le type
            file_type = self.get_file_type(file_info["path"])
            file_info["type"] = file_type

            # Statistiques
            ext = file_info["extension"]
            stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
            stats["total_size"] += file_info["size"]

            analyzed_files.append(file_info)

        stats["files"] = analyzed_files

        logger.info(f"Scan completed: {stats['total_files']} files, "
                   f"{len(stats['corrupted'])} corrupted")

        return stats
