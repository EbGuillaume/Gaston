"""Pytest configuration and fixtures."""
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database."""
    # Create temporary database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_cbz_file(temp_dir):
    """Create a sample CBZ file for testing."""
    import zipfile

    cbz_path = Path(temp_dir) / "test_comic.cbz"

    # Create a simple test image
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")

    # Create ZIP with image
    with zipfile.ZipFile(cbz_path, "w") as zf:
        # Save image to bytes
        import io

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        zf.writestr("page_001.jpg", img_bytes.read())

    yield str(cbz_path)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample test files."""
    files = []

    # Create some test files
    extensions = [".cbz", ".cbr", ".epub", ".pdf"]
    for i, ext in enumerate(extensions):
        file_path = Path(temp_dir) / f"test_file_{i}{ext}"
        file_path.touch()
        files.append(str(file_path))

    yield files
