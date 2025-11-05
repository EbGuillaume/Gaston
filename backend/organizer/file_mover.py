"""File mover with ComicInfo.xml injection."""
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Optional
from loguru import logger

from backend.organizer.comicinfo import ComicInfoGenerator


class FileMover:
    """
    Handles secure file moving and ComicInfo.xml injection.

    Supports:
    - CBZ files (ZIP archives) - can inject ComicInfo.xml
    - CBR files (RAR archives) - copy only, can't inject
    - Other formats (PDF, EPUB) - copy only
    """

    def __init__(self, dry_run: bool = False):
        """
        Initialize file mover.

        Args:
            dry_run: If True, don't actually move files (simulation)
        """
        self.dry_run = dry_run
        self.comicinfo_generator = ComicInfoGenerator()

    def move_with_metadata(
        self,
        source_path: Path,
        target_path: Path,
        metadata: Optional[dict] = None,
        copy_instead_of_move: bool = False,
    ) -> bool:
        """
        Move file to target with metadata injection (if CBZ).

        Args:
            source_path: Source file path
            target_path: Target file path
            metadata: Metadata dictionary for ComicInfo.xml
            copy_instead_of_move: Copy instead of moving

        Returns:
            True if successful
        """
        try:
            # Vérifier que le fichier source existe
            if not source_path.exists():
                logger.error(f"Source file not found: {source_path}")
                return False

            # Créer le dossier de destination
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Vérifier si le fichier existe déjà
            if target_path.exists():
                logger.warning(f"Target file already exists: {target_path}")
                # Ajouter un suffixe numérique
                counter = 1
                while True:
                    new_target = target_path.parent / (
                        target_path.stem + f" ({counter})" + target_path.suffix
                    )
                    if not new_target.exists():
                        target_path = new_target
                        break
                    counter += 1

            if self.dry_run:
                logger.info(f"[DRY RUN] Would move: {source_path} -> {target_path}")
                return True

            # Traitement selon l'extension
            extension = source_path.suffix.lower()

            if extension == ".cbz":
                # CBZ: on peut injecter ComicInfo.xml
                return self._move_cbz_with_metadata(
                    source_path, target_path, metadata, copy_instead_of_move
                )
            else:
                # Autres formats: copie/déplacement simple
                if copy_instead_of_move:
                    shutil.copy2(source_path, target_path)
                    logger.info(f"Copied: {source_path} -> {target_path}")
                else:
                    shutil.move(str(source_path), str(target_path))
                    logger.info(f"Moved: {source_path} -> {target_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to move file {source_path}: {e}")
            return False

    def _move_cbz_with_metadata(
        self,
        source_path: Path,
        target_path: Path,
        metadata: Optional[dict],
        copy_instead_of_move: bool,
    ) -> bool:
        """
        Move CBZ file and inject ComicInfo.xml.

        Args:
            source_path: Source CBZ file
            target_path: Target CBZ file
            metadata: Metadata dictionary
            copy_instead_of_move: Copy source instead of moving

        Returns:
            True if successful
        """
        try:
            # Si pas de métadonnées, simple copie/déplacement
            if not metadata:
                if copy_instead_of_move:
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.move(str(source_path), str(target_path))
                logger.info(
                    f"{'Copied' if copy_instead_of_move else 'Moved'} CBZ without metadata: {source_path} -> {target_path}"
                )
                return True

            # Générer le ComicInfo.xml
            comicinfo_xml = self.comicinfo_generator.generate(metadata)

            # Créer un fichier temporaire pour la nouvelle archive
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".cbz"
            ) as temp_file:
                temp_path = Path(temp_file.name)

            # Copier l'archive et ajouter ComicInfo.xml
            with zipfile.ZipFile(source_path, "r") as source_zip:
                with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target_zip:
                    # Copier tous les fichiers sauf ComicInfo.xml existant
                    for item in source_zip.infolist():
                        if item.filename.lower() != "comicinfo.xml":
                            data = source_zip.read(item.filename)
                            target_zip.writestr(item, data)

                    # Ajouter le nouveau ComicInfo.xml
                    target_zip.writestr("ComicInfo.xml", comicinfo_xml)

            # Déplacer le fichier temporaire vers la destination
            shutil.move(str(temp_path), str(target_path))

            # Supprimer l'original si move (pas copy)
            if not copy_instead_of_move:
                source_path.unlink()
                logger.info(f"Moved CBZ with metadata: {source_path} -> {target_path}")
            else:
                logger.info(f"Copied CBZ with metadata: {source_path} -> {target_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to process CBZ file {source_path}: {e}")
            # Nettoyer le fichier temporaire si erreur
            if temp_path and temp_path.exists():
                temp_path.unlink()
            return False

    def inject_comicinfo(
        self, cbz_path: Path, metadata: dict, backup: bool = True
    ) -> bool:
        """
        Inject ComicInfo.xml into existing CBZ file.

        Args:
            cbz_path: Path to CBZ file
            metadata: Metadata dictionary
            backup: Create backup before modifying

        Returns:
            True if successful
        """
        try:
            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would inject ComicInfo.xml into: {cbz_path}"
                )
                return True

            if not cbz_path.exists():
                logger.error(f"CBZ file not found: {cbz_path}")
                return False

            # Créer un backup si demandé
            if backup:
                backup_path = cbz_path.with_suffix(".cbz.bak")
                shutil.copy2(cbz_path, backup_path)
                logger.debug(f"Backup created: {backup_path}")

            # Générer le ComicInfo.xml
            comicinfo_xml = self.comicinfo_generator.generate(metadata)

            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix=".cbz") as temp_file:
                temp_path = Path(temp_file.name)

            # Copier l'archive et ajouter/remplacer ComicInfo.xml
            with zipfile.ZipFile(cbz_path, "r") as source_zip:
                with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target_zip:
                    # Copier tous les fichiers sauf ComicInfo.xml existant
                    for item in source_zip.infolist():
                        if item.filename.lower() != "comicinfo.xml":
                            data = source_zip.read(item.filename)
                            target_zip.writestr(item, data)

                    # Ajouter le nouveau ComicInfo.xml
                    target_zip.writestr("ComicInfo.xml", comicinfo_xml)

            # Remplacer l'original par le nouveau
            shutil.move(str(temp_path), str(cbz_path))
            logger.info(f"Injected ComicInfo.xml into: {cbz_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to inject ComicInfo.xml into {cbz_path}: {e}")
            if temp_path and temp_path.exists():
                temp_path.unlink()
            return False

    def extract_comicinfo(self, cbz_path: Path) -> Optional[str]:
        """
        Extract ComicInfo.xml from CBZ file.

        Args:
            cbz_path: Path to CBZ file

        Returns:
            ComicInfo.xml content or None
        """
        try:
            if not cbz_path.exists():
                logger.error(f"CBZ file not found: {cbz_path}")
                return None

            with zipfile.ZipFile(cbz_path, "r") as zip_file:
                # Chercher ComicInfo.xml (case insensitive)
                for filename in zip_file.namelist():
                    if filename.lower() == "comicinfo.xml":
                        content = zip_file.read(filename).decode("utf-8")
                        return content

            logger.debug(f"No ComicInfo.xml found in: {cbz_path}")
            return None

        except Exception as e:
            logger.error(f"Failed to extract ComicInfo.xml from {cbz_path}: {e}")
            return None

    def verify_move(self, source_path: Path, target_path: Path) -> bool:
        """
        Verify that file was moved correctly (compare sizes).

        Args:
            source_path: Original source path
            target_path: Target path

        Returns:
            True if verification successful
        """
        try:
            if not target_path.exists():
                logger.error(f"Target file not found: {target_path}")
                return False

            source_size = source_path.stat().st_size if source_path.exists() else 0
            target_size = target_path.stat().st_size

            # Pour CBZ avec injection, la taille peut différer légèrement
            size_diff = abs(target_size - source_size)
            max_diff = 100_000  # 100 KB de différence acceptable

            if size_diff > max_diff and source_path.exists():
                logger.warning(
                    f"Size difference detected: {source_path} ({source_size} bytes) vs {target_path} ({target_size} bytes)"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to verify move: {e}")
            return False
