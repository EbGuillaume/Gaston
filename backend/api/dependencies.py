"""FastAPI dependencies."""
from typing import Generator

from sqlalchemy.orm import Session

from backend.database.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI pour obtenir une session de base de données.

    Yields:
        Session SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
