"""API routes for database management."""
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.database.models import Base
from backend.database.session import engine

router = APIRouter(prefix="/api/database", tags=["database"])


class ResetResponse(BaseModel):
    """Response for database reset."""

    status: str
    message: str


@router.post("/reset", response_model=ResetResponse)
async def reset_database(db: Session = Depends(get_db)):
    """
    Reset the entire database (drop all tables and recreate).

    WARNING: This will delete ALL data!
    """
    try:
        logger.warning("Resetting database - dropping all tables!")

        # Fermer la session actuelle
        db.close()

        # Drop toutes les tables
        Base.metadata.drop_all(bind=engine)

        # Recréer les tables
        Base.metadata.create_all(bind=engine)

        logger.info("Database reset completed")

        return ResetResponse(
            status="success",
            message="Database has been reset. All data has been deleted.",
        )

    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {e}")


@router.get("/stats", response_model=dict)
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics."""
    try:
        from backend.database.models import Book, Series, Metadata

        total_books = db.query(Book).count()
        total_series = db.query(Series).count()
        total_metadata = db.query(Metadata).count()

        return {
            "total_books": total_books,
            "total_series": total_series,
            "total_metadata": total_metadata,
        }

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get database stats: {e}"
        )
