"""Tests for hash utilities."""
from pathlib import Path

import pytest
from PIL import Image

from backend.utils.hash import HashCalculator


def test_calculate_file_hash(temp_dir):
    """Test file hash calculation."""
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    # MD5
    hash_md5 = HashCalculator.calculate_file_hash(str(test_file), "md5")
    assert hash_md5 is not None
    assert len(hash_md5) == 32

    # SHA256
    hash_sha256 = HashCalculator.calculate_file_hash(str(test_file), "sha256")
    assert hash_sha256 is not None
    assert len(hash_sha256) == 64


def test_calculate_file_hash_same_content(temp_dir):
    """Test that same content produces same hash."""
    file1 = Path(temp_dir) / "file1.txt"
    file2 = Path(temp_dir) / "file2.txt"

    file1.write_text("Same content")
    file2.write_text("Same content")

    hash1 = HashCalculator.calculate_file_hash(str(file1))
    hash2 = HashCalculator.calculate_file_hash(str(file2))

    assert hash1 == hash2


def test_calculate_file_hash_different_content(temp_dir):
    """Test that different content produces different hash."""
    file1 = Path(temp_dir) / "file1.txt"
    file2 = Path(temp_dir) / "file2.txt"

    file1.write_text("Content 1")
    file2.write_text("Content 2")

    hash1 = HashCalculator.calculate_file_hash(str(file1))
    hash2 = HashCalculator.calculate_file_hash(str(file2))

    assert hash1 != hash2


def test_calculate_perceptual_hash(temp_dir):
    """Test perceptual hash calculation."""
    # Create a test image
    img_path = Path(temp_dir) / "test.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)

    phash = HashCalculator.calculate_perceptual_hash(str(img_path))
    assert phash is not None
    assert len(phash) == 16  # 8x8 = 64 bits = 16 hex chars


def test_calculate_average_hash(temp_dir):
    """Test average hash calculation."""
    img_path = Path(temp_dir) / "test.jpg"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(img_path)

    ahash = HashCalculator.calculate_average_hash(str(img_path))
    assert ahash is not None
    assert len(ahash) == 16


def test_calculate_difference_hash(temp_dir):
    """Test difference hash calculation."""
    img_path = Path(temp_dir) / "test.jpg"
    img = Image.new("RGB", (100, 100), color="green")
    img.save(img_path)

    dhash = HashCalculator.calculate_difference_hash(str(img_path))
    assert dhash is not None
    assert len(dhash) == 16


def test_compare_perceptual_hashes():
    """Test perceptual hash comparison."""
    # Identical hashes
    hash1 = "a1b2c3d4e5f67890"
    hash2 = "a1b2c3d4e5f67890"

    distance = HashCalculator.compare_perceptual_hashes(hash1, hash2)
    assert distance == 0


def test_are_images_similar(temp_dir):
    """Test image similarity detection."""
    # Create two similar images (same color)
    img1_path = Path(temp_dir) / "img1.jpg"
    img2_path = Path(temp_dir) / "img2.jpg"

    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="red")

    img1.save(img1_path)
    img2.save(img2_path)

    # Should be very similar
    assert HashCalculator.are_images_similar(str(img1_path), str(img2_path), threshold=10)


def test_are_images_different(temp_dir):
    """Test that different images are detected."""
    img1_path = Path(temp_dir) / "img1.jpg"
    img2_path = Path(temp_dir) / "img2.jpg"

    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="blue")

    img1.save(img1_path)
    img2.save(img2_path)

    # Should be different (with low threshold)
    assert not HashCalculator.are_images_similar(str(img1_path), str(img2_path), threshold=5)


def test_calculate_all_hashes(temp_dir):
    """Test calculating all hashes at once."""
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Test content")

    hashes = HashCalculator.calculate_all_hashes(str(test_file))

    assert "md5" in hashes
    assert "sha256" in hashes
    assert hashes["md5"] is not None
    assert hashes["sha256"] is not None
