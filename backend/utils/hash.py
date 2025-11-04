"""File hashing utilities for duplicate detection."""
import hashlib
from pathlib import Path
from typing import Dict, Optional

import imagehash
from loguru import logger
from PIL import Image


class HashCalculator:
    """Calculator for various types of hashes."""

    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
        """
        Calcule le hash complet d'un fichier.

        Args:
            file_path: Chemin du fichier
            algorithm: Algorithme de hash (md5, sha256)

        Returns:
            Hash du fichier en hexadécimal, ou None en cas d'erreur
        """
        try:
            hash_func = hashlib.new(algorithm)

            with open(file_path, "rb") as f:
                # Lire le fichier par blocs pour économiser la mémoire
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)

            return hash_func.hexdigest()

        except Exception as e:
            logger.error(f"Error calculating {algorithm} hash for {file_path}: {e}")
            return None

    @staticmethod
    def calculate_perceptual_hash(image_path: str, hash_size: int = 8) -> Optional[str]:
        """
        Calcule le hash perceptuel d'une image.

        Args:
            image_path: Chemin de l'image
            hash_size: Taille du hash (8 = 64 bits)

        Returns:
            Hash perceptuel en string, ou None en cas d'erreur
        """
        try:
            image = Image.open(image_path)
            phash = imagehash.phash(image, hash_size=hash_size)
            return str(phash)

        except Exception as e:
            logger.error(f"Error calculating perceptual hash for {image_path}: {e}")
            return None

    @staticmethod
    def calculate_average_hash(image_path: str, hash_size: int = 8) -> Optional[str]:
        """
        Calcule le hash moyen d'une image.

        Args:
            image_path: Chemin de l'image
            hash_size: Taille du hash

        Returns:
            Hash moyen en string, ou None en cas d'erreur
        """
        try:
            image = Image.open(image_path)
            ahash = imagehash.average_hash(image, hash_size=hash_size)
            return str(ahash)

        except Exception as e:
            logger.error(f"Error calculating average hash for {image_path}: {e}")
            return None

    @staticmethod
    def calculate_difference_hash(image_path: str, hash_size: int = 8) -> Optional[str]:
        """
        Calcule le hash de différence d'une image.

        Args:
            image_path: Chemin de l'image
            hash_size: Taille du hash

        Returns:
            Hash de différence en string, ou None en cas d'erreur
        """
        try:
            image = Image.open(image_path)
            dhash = imagehash.dhash(image, hash_size=hash_size)
            return str(dhash)

        except Exception as e:
            logger.error(f"Error calculating difference hash for {image_path}: {e}")
            return None

    @staticmethod
    def calculate_all_hashes(file_path: str) -> Dict[str, Optional[str]]:
        """
        Calcule tous les types de hash pour un fichier.

        Args:
            file_path: Chemin du fichier

        Returns:
            Dictionnaire avec tous les hash
        """
        return {
            "md5": HashCalculator.calculate_file_hash(file_path, "md5"),
            "sha256": HashCalculator.calculate_file_hash(file_path, "sha256"),
        }

    @staticmethod
    def compare_perceptual_hashes(hash1: str, hash2: str) -> int:
        """
        Compare deux hash perceptuels.

        Args:
            hash1: Premier hash
            hash2: Deuxième hash

        Returns:
            Distance de Hamming (0 = identiques)
        """
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            return h1 - h2

        except Exception as e:
            logger.error(f"Error comparing perceptual hashes: {e}")
            return -1

    @staticmethod
    def are_images_similar(
        image1_path: str, image2_path: str, threshold: int = 10
    ) -> bool:
        """
        Détermine si deux images sont similaires.

        Args:
            image1_path: Chemin de la première image
            image2_path: Chemin de la deuxième image
            threshold: Seuil de différence (plus bas = plus strict)

        Returns:
            True si les images sont similaires
        """
        hash1 = HashCalculator.calculate_perceptual_hash(image1_path)
        hash2 = HashCalculator.calculate_perceptual_hash(image2_path)

        if hash1 is None or hash2 is None:
            return False

        distance = HashCalculator.compare_perceptual_hashes(hash1, hash2)
        return distance <= threshold
