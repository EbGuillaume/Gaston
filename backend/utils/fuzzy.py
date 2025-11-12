"""Fuzzy string matching utilities for duplicate detection."""
import re
from typing import List, Optional, Tuple

from rapidfuzz import fuzz, process
from loguru import logger


class FuzzyMatcher:
    """Fuzzy string matcher for detecting similar filenames."""

    @staticmethod
    def normalize_filename(filename: str) -> str:
        """
        Normalise un nom de fichier pour la comparaison.

        Args:
            filename: Nom de fichier à normaliser

        Returns:
            Nom de fichier normalisé
        """
        # Enlever l'extension
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

        # Convertir en minuscules
        name = name.lower()

        # Enlever les caractères spéciaux courants
        name = re.sub(r"[_\-\.\[\]\(\)]", " ", name)

        # Enlever les numéros de version/qualité
        name = re.sub(r"\b(v\d+|hd|1080p|720p|cbr|cbz|pdf|epub)\b", "", name, flags=re.IGNORECASE)

        # Enlever les espaces multiples
        name = re.sub(r"\s+", " ", name)

        return name.strip()

    @staticmethod
    def calculate_similarity(string1: str, string2: str, normalize: bool = True) -> float:
        """
        Calcule la similarité entre deux chaînes.

        Args:
            string1: Première chaîne
            string2: Deuxième chaîne
            normalize: Si True, normalise les chaînes avant comparaison

        Returns:
            Score de similarité entre 0 et 1
        """
        if normalize:
            string1 = FuzzyMatcher.normalize_filename(string1)
            string2 = FuzzyMatcher.normalize_filename(string2)

        # Utiliser le ratio de Levenshtein
        score = fuzz.ratio(string1, string2)

        return score / 100.0

    @staticmethod
    def calculate_token_similarity(string1: str, string2: str, normalize: bool = True) -> float:
        """
        Calcule la similarité par tokens entre deux chaînes.

        Args:
            string1: Première chaîne
            string2: Deuxième chaîne
            normalize: Si True, normalise les chaînes avant comparaison

        Returns:
            Score de similarité entre 0 et 1
        """
        if normalize:
            string1 = FuzzyMatcher.normalize_filename(string1)
            string2 = FuzzyMatcher.normalize_filename(string2)

        # Utiliser le token sort ratio (ordre des mots n'importe pas)
        score = fuzz.token_sort_ratio(string1, string2)

        return score / 100.0

    @staticmethod
    def are_filenames_similar(
        filename1: str, filename2: str, threshold: float = 0.85
    ) -> bool:
        """
        Détermine si deux noms de fichiers sont similaires.

        Args:
            filename1: Premier nom de fichier
            filename2: Deuxième nom de fichier
            threshold: Seuil de similarité (0-1)

        Returns:
            True si les noms sont similaires
        """
        # Essayer plusieurs méthodes
        ratio = FuzzyMatcher.calculate_similarity(filename1, filename2)
        token_ratio = FuzzyMatcher.calculate_token_similarity(filename1, filename2)

        # Prendre le meilleur score
        best_score = max(ratio, token_ratio)

        logger.debug(
            f"Comparing '{filename1}' vs '{filename2}': "
            f"ratio={ratio:.2f}, token_ratio={token_ratio:.2f}, best={best_score:.2f}"
        )

        return best_score >= threshold

    @staticmethod
    def find_similar_names(
        target: str, candidates: List[str], threshold: float = 0.85, limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Trouve les noms similaires dans une liste de candidats.

        Args:
            target: Nom cible
            candidates: Liste de noms candidats
            threshold: Seuil de similarité minimum
            limit: Nombre maximum de résultats

        Returns:
            Liste de tuples (nom, score) triée par score décroissant
        """
        # Normaliser le target
        normalized_target = FuzzyMatcher.normalize_filename(target)

        # Normaliser les candidats
        normalized_candidates = [
            (orig, FuzzyMatcher.normalize_filename(orig)) for orig in candidates
        ]

        # Utiliser process.extract pour trouver les meilleurs matches
        results = process.extract(
            normalized_target,
            [norm for _, norm in normalized_candidates],
            scorer=fuzz.token_sort_ratio,
            limit=limit,
        )

        # Filtrer par seuil et reconstruire avec les noms originaux
        similar = []
        for normalized, score, idx in results:
            score_normalized = score / 100.0
            if score_normalized >= threshold:
                original_name = normalized_candidates[idx][0]
                similar.append((original_name, score_normalized))

        return similar

    @staticmethod
    def clean_tags(filename: str) -> str:
        """
        Retire les tags entre crochets et parenthèses du nom de fichier.

        Exemples:
            "[Comics.fr] Y le dernier homme - 01 [Vaughan]" → "Y le dernier homme - 01"
            "Asterix T41 [CBZ] Fr" → "Asterix T41 Fr"

        Args:
            filename: Nom de fichier à nettoyer

        Returns:
            Nom de fichier sans tags
        """
        # Retirer les tags entre crochets au début (ex: [Comics.fr], [CBZ])
        cleaned = re.sub(r'^\[.*?\]\s*', '', filename)

        # Retirer les tags entre crochets/parenthèses contenant des auteurs ou infos
        # (généralement en fin de nom après le numéro)
        # Ex: "[Vaughan-Guerra]", "(Uderzo)"
        cleaned = re.sub(r'\s*[\[\(][^\]\)]*?[\]\)]\s*', ' ', cleaned)

        # Retirer les tags de langue/format en fin (ex: "Fr", "EN", "FRENCH")
        cleaned = re.sub(r'\s+(fr|en|us|uk|french|english|vf|vo)\s*$', '', cleaned, flags=re.IGNORECASE)

        # Enlever les espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned.strip()

    @staticmethod
    def extract_series_and_number(filename: str, full_path: Optional[str] = None) -> Tuple[str, int]:
        """
        Extrait le nom de série et le numéro d'un nom de fichier.

        Args:
            filename: Nom de fichier
            full_path: Chemin complet du fichier (optionnel). Si fourni et que le nom
                      de série extrait est générique, utilise le nom du dossier parent.

        Returns:
            Tuple (nom de série, numéro) ou (filename, 0) si non trouvé
        """
        # Nettoyer les tags d'abord
        cleaned = FuzzyMatcher.clean_tags(filename)

        # Patterns courants pour les numéros
        patterns = [
            r"(.+?)\s+[Tt](?:ome)?\.?\s*(\d+)",  # "Asterix Tome 01" ou "Asterix T01"
            r"(.+?)\s+[Vv](?:ol)?\.?\s*(\d+)",  # "Asterix Vol 01"
            r"(.+?)\s+#(\d+)",  # "Asterix #01"
            r"(.+?)\s+-\s+(\d+)",  # "Y le dernier homme - 01"
            r"(.+?)\s+(\d+)",  # "Asterix 01" (doit être en dernier, moins spécifique)
        ]

        normalized = FuzzyMatcher.normalize_filename(cleaned)

        series_name = None
        number = 0

        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                series_name = match.group(1).strip()
                number = int(match.group(2))
                break

        # Si pas de nom de série trouvé, utiliser le filename normalisé
        if not series_name:
            series_name = normalized
            logger.debug(f"No volume number found, using full filename as series: {series_name}")

        # Si le nom de série est trop court ou générique, essayer le dossier parent
        generic_names = {"tome", "vol", "volume", "chapter", "chapitre", "ch", "t", "v"}
        if full_path and (len(series_name) < 3 or series_name.lower() in generic_names):
            import os
            parent_folder = os.path.basename(os.path.dirname(full_path))
            # Vérifier que le dossier parent n'est pas un nom générique de dossier
            generic_folders = {"bd_sample", "comics", "books", "library", "scan", "scans"}
            if parent_folder and parent_folder.lower() not in generic_folders:
                series_name = parent_folder
                logger.debug(f"Using parent folder name as series: {series_name}")

        return (series_name, number)

    @staticmethod
    def group_similar_files(filenames: List[str], threshold: float = 0.85) -> List[List[str]]:
        """
        Groupe les fichiers similaires ensemble.

        Args:
            filenames: Liste de noms de fichiers
            threshold: Seuil de similarité

        Returns:
            Liste de groupes de fichiers similaires
        """
        groups = []
        processed = set()

        for filename in filenames:
            if filename in processed:
                continue

            # Créer un nouveau groupe
            group = [filename]
            processed.add(filename)

            # Trouver les fichiers similaires
            for other in filenames:
                if other in processed:
                    continue

                if FuzzyMatcher.are_filenames_similar(filename, other, threshold):
                    group.append(other)
                    processed.add(other)

            if len(group) > 1:
                groups.append(group)

        return groups
