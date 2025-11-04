"""Archive manipulation utilities for CBZ, CBR, EPUB, and PDF files."""
import io
import zipfile
from pathlib import Path
from typing import List, Optional

import rarfile
from loguru import logger
from PIL import Image


class ArchiveHandler:
    """Handler for comic book archives and ebook files."""

    SUPPORTED_FORMATS = [".cbz", ".cbr", ".epub", ".pdf"]
    IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

    def __init__(self, file_path: str):
        """
        Initialize archive handler.

        Args:
            file_path: Path to the archive file
        """
        self.file_path = Path(file_path)
        self.extension = self.file_path.suffix.lower()

        if self.extension not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {self.extension}")

    def is_valid(self) -> bool:
        """
        Check if the archive is valid and can be opened.

        Returns:
            True if archive is valid
        """
        try:
            if self.extension == ".cbz":
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    # Test the archive
                    zf.testzip()
                return True

            elif self.extension == ".cbr":
                with rarfile.RarFile(self.file_path, "r") as rf:
                    # Test the archive
                    rf.testrar()
                return True

            elif self.extension == ".epub":
                # EPUB is actually a ZIP file
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    zf.testzip()
                return True

            elif self.extension == ".pdf":
                # Basic PDF validation - check if file starts with PDF header
                with open(self.file_path, "rb") as f:
                    header = f.read(5)
                    return header == b"%PDF-"

            return False

        except Exception as e:
            logger.error(f"Archive validation failed for {self.file_path}: {e}")
            return False

    def list_files(self) -> List[str]:
        """
        List all files in the archive.

        Returns:
            List of file names in the archive
        """
        try:
            if self.extension == ".cbz":
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    return zf.namelist()

            elif self.extension == ".cbr":
                with rarfile.RarFile(self.file_path, "r") as rf:
                    return rf.namelist()

            elif self.extension == ".epub":
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    return zf.namelist()

            elif self.extension == ".pdf":
                # PDF doesn't have a file list concept
                return []

        except Exception as e:
            logger.error(f"Failed to list files in {self.file_path}: {e}")
            return []

        return []

    def get_image_files(self) -> List[str]:
        """
        Get list of image files in the archive.

        Returns:
            List of image file names
        """
        all_files = self.list_files()

        # Filter for image files
        image_files = [
            f
            for f in all_files
            if Path(f).suffix.lower() in self.IMAGE_EXTENSIONS
        ]

        # Sort files naturally
        return sorted(image_files)

    def extract_cover(self, output_path: Optional[str] = None) -> Optional[Image.Image]:
        """
        Extract the cover image from the archive.

        Args:
            output_path: Optional path to save the cover image

        Returns:
            PIL Image object or None if failed
        """
        try:
            if self.extension in [".cbz", ".cbr", ".epub"]:
                image_files = self.get_image_files()

                if not image_files:
                    logger.warning(f"No images found in {self.file_path}")
                    return None

                # Take the first image as cover
                cover_file = image_files[0]

                # Extract the image
                image_data = self.read_file(cover_file)

                if image_data:
                    image = Image.open(io.BytesIO(image_data))

                    if output_path:
                        image.save(output_path)
                        logger.info(f"Cover saved to {output_path}")

                    return image

            elif self.extension == ".pdf":
                # For PDF, we would need to use a PDF library like PyPDF2 or pdf2image
                # This is a placeholder for now
                logger.warning("PDF cover extraction not yet implemented")
                return None

        except Exception as e:
            logger.error(f"Failed to extract cover from {self.file_path}: {e}")
            return None

        return None

    def read_file(self, filename: str) -> Optional[bytes]:
        """
        Read a specific file from the archive.

        Args:
            filename: Name of the file to read

        Returns:
            File contents as bytes or None if failed
        """
        try:
            if self.extension == ".cbz":
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    return zf.read(filename)

            elif self.extension == ".cbr":
                with rarfile.RarFile(self.file_path, "r") as rf:
                    return rf.read(filename)

            elif self.extension == ".epub":
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    return zf.read(filename)

        except Exception as e:
            logger.error(f"Failed to read {filename} from {self.file_path}: {e}")
            return None

        return None

    def extract_all(self, output_dir: str) -> bool:
        """
        Extract all files from the archive.

        Args:
            output_dir: Directory to extract files to

        Returns:
            True if extraction succeeded
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            if self.extension == ".cbz":
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    zf.extractall(output_path)
                return True

            elif self.extension == ".cbr":
                with rarfile.RarFile(self.file_path, "r") as rf:
                    rf.extractall(output_path)
                return True

            elif self.extension == ".epub":
                with zipfile.ZipFile(self.file_path, "r") as zf:
                    zf.extractall(output_path)
                return True

            elif self.extension == ".pdf":
                logger.warning("PDF extraction not supported")
                return False

        except Exception as e:
            logger.error(f"Failed to extract {self.file_path}: {e}")
            return False

        return False

    def get_page_count(self) -> int:
        """
        Get the number of pages (images) in the archive.

        Returns:
            Number of pages
        """
        if self.extension == ".pdf":
            # Would need PDF library to implement this
            return 0

        image_files = self.get_image_files()
        return len(image_files)
