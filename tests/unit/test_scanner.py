"""Tests for the file scanner module."""
from pathlib import Path

import pytest

from backend.core.scanner import FileScanner


def test_scanner_initialization():
    """Test FileScanner initialization."""
    scanner = FileScanner()
    assert scanner is not None
    assert scanner.max_file_size > 0
    assert len(scanner.supported_extensions) > 0


def test_scan_directory_empty(temp_dir):
    """Test scanning an empty directory."""
    scanner = FileScanner()
    files = scanner.scan_directory(temp_dir)
    assert files == []


def test_scan_directory_with_files(temp_dir):
    """Test scanning a directory with supported files."""
    # Create test files
    test_files = ["test1.cbz", "test2.cbr", "test3.pdf", "test4.txt"]
    for filename in test_files:
        (Path(temp_dir) / filename).touch()

    scanner = FileScanner()
    files = scanner.scan_directory(temp_dir)

    # Should find 3 files (excluding .txt)
    assert len(files) == 3
    assert all("extension" in f for f in files)
    assert all("size" in f for f in files)


def test_scan_directory_ignores_hidden(temp_dir):
    """Test that scanner ignores hidden files."""
    # Create visible and hidden files
    (Path(temp_dir) / "visible.cbz").touch()
    (Path(temp_dir) / ".hidden.cbz").touch()

    scanner = FileScanner()
    files = scanner.scan_directory(temp_dir)

    # Should only find visible file
    assert len(files) == 1
    assert "visible.cbz" in files[0]["filename"]


def test_scan_nonexistent_directory():
    """Test scanning a non-existent directory."""
    scanner = FileScanner()
    files = scanner.scan_directory("/nonexistent/path")
    assert files == []


def test_calculate_file_hash(temp_dir):
    """Test file hash calculation."""
    # Create a test file with known content
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    hash_md5 = FileScanner.calculate_file_hash(str(test_file), "md5")
    assert hash_md5 is not None
    assert len(hash_md5) == 32  # MD5 hash length

    hash_sha256 = FileScanner.calculate_file_hash(str(test_file), "sha256")
    assert hash_sha256 is not None
    assert len(hash_sha256) == 64  # SHA256 hash length


def test_is_file_corrupted(temp_dir):
    """Test corrupted file detection."""
    # Create a valid file
    valid_file = Path(temp_dir) / "valid.txt"
    valid_file.write_text("Valid content")

    assert FileScanner.is_file_corrupted(str(valid_file)) is False

    # Test with non-existent file
    assert FileScanner.is_file_corrupted("/nonexistent/file.txt") is True


def test_get_file_type():
    """Test file type detection."""
    scanner = FileScanner()

    assert scanner.get_file_type("test.cbz") == "Comic"
    assert scanner.get_file_type("test.cbr") == "Comic"
    assert scanner.get_file_type("test.epub") == "Book"
    assert scanner.get_file_type("test.pdf") == "Book"
    assert scanner.get_file_type("test.txt") is None


def test_scan_and_analyze(temp_dir):
    """Test scan and analyze functionality."""
    # Create test files
    (Path(temp_dir) / "comic1.cbz").write_bytes(b"test content 1")
    (Path(temp_dir) / "comic2.cbr").write_bytes(b"test content 2")

    scanner = FileScanner()
    stats = scanner.scan_and_analyze(temp_dir)

    assert "total_files" in stats
    assert stats["total_files"] == 2
    assert "by_extension" in stats
    assert ".cbz" in stats["by_extension"]
    assert "total_size" in stats
    assert stats["total_size"] > 0


def test_scan_multiple_directories(temp_dir):
    """Test scanning multiple directories."""
    # Create two subdirectories with files
    dir1 = Path(temp_dir) / "dir1"
    dir2 = Path(temp_dir) / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    (dir1 / "file1.cbz").touch()
    (dir2 / "file2.cbz").touch()

    scanner = FileScanner()
    files = scanner.scan_multiple_directories([str(dir1), str(dir2)])

    assert len(files) == 2
