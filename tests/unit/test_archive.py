"""Tests for the archive handler module."""
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from backend.utils.archive import ArchiveHandler


def test_archive_handler_initialization(sample_cbz_file):
    """Test ArchiveHandler initialization."""
    handler = ArchiveHandler(sample_cbz_file)
    assert handler is not None
    assert handler.extension == ".cbz"


def test_unsupported_format(temp_dir):
    """Test that unsupported formats raise ValueError."""
    unsupported_file = Path(temp_dir) / "test.txt"
    unsupported_file.touch()

    with pytest.raises(ValueError, match="Unsupported file format"):
        ArchiveHandler(str(unsupported_file))


def test_is_valid_cbz(sample_cbz_file):
    """Test validation of CBZ file."""
    handler = ArchiveHandler(sample_cbz_file)
    assert handler.is_valid() is True


def test_is_valid_corrupted_cbz(temp_dir):
    """Test validation of corrupted CBZ file."""
    # Create a corrupted CBZ (not a valid ZIP)
    corrupted_file = Path(temp_dir) / "corrupted.cbz"
    corrupted_file.write_text("This is not a ZIP file")

    handler = ArchiveHandler(str(corrupted_file))
    assert handler.is_valid() is False


def test_list_files(sample_cbz_file):
    """Test listing files in archive."""
    handler = ArchiveHandler(sample_cbz_file)
    files = handler.list_files()

    assert len(files) > 0
    assert "page_001.jpg" in files


def test_get_image_files(sample_cbz_file):
    """Test getting image files from archive."""
    handler = ArchiveHandler(sample_cbz_file)
    images = handler.get_image_files()

    assert len(images) > 0
    assert all(Path(img).suffix.lower() in handler.IMAGE_EXTENSIONS for img in images)


def test_extract_cover(sample_cbz_file, temp_dir):
    """Test cover extraction."""
    handler = ArchiveHandler(sample_cbz_file)
    cover_path = Path(temp_dir) / "cover.jpg"

    cover = handler.extract_cover(str(cover_path))

    assert cover is not None
    assert isinstance(cover, Image.Image)
    assert cover_path.exists()


def test_read_file(sample_cbz_file):
    """Test reading a specific file from archive."""
    handler = ArchiveHandler(sample_cbz_file)
    content = handler.read_file("page_001.jpg")

    assert content is not None
    assert isinstance(content, bytes)
    assert len(content) > 0


def test_extract_all(sample_cbz_file, temp_dir):
    """Test extracting all files."""
    handler = ArchiveHandler(sample_cbz_file)
    output_dir = Path(temp_dir) / "extracted"

    success = handler.extract_all(str(output_dir))

    assert success is True
    assert output_dir.exists()
    assert len(list(output_dir.iterdir())) > 0


def test_get_page_count(sample_cbz_file):
    """Test getting page count."""
    handler = ArchiveHandler(sample_cbz_file)
    page_count = handler.get_page_count()

    assert page_count > 0
    assert page_count == 1  # Our sample has 1 page


def test_pdf_validation(temp_dir):
    """Test PDF file validation."""
    # Create a minimal PDF file
    pdf_file = Path(temp_dir) / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n%Test PDF")

    handler = ArchiveHandler(str(pdf_file))
    assert handler.is_valid() is True


def test_invalid_pdf(temp_dir):
    """Test invalid PDF file."""
    pdf_file = Path(temp_dir) / "invalid.pdf"
    pdf_file.write_text("Not a PDF")

    handler = ArchiveHandler(str(pdf_file))
    assert handler.is_valid() is False


def test_epub_support(temp_dir):
    """Test EPUB file support."""
    # Create a minimal EPUB (which is a ZIP with specific structure)
    epub_file = Path(temp_dir) / "test.epub"

    with zipfile.ZipFile(epub_file, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", "<container/>")

    handler = ArchiveHandler(str(epub_file))
    assert handler.extension == ".epub"
    assert handler.is_valid() is True
