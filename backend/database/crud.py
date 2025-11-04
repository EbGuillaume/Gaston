"""CRUD operations for database models."""
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.database.models import Book, Duplicate, Metadata, Series, Task


class SeriesCRUD:
    """CRUD operations for Series."""

    @staticmethod
    def create(db: Session, name: str, **kwargs) -> Series:
        """Create a new series."""
        series = Series(name=name, **kwargs)
        db.add(series)
        db.commit()
        db.refresh(series)
        return series

    @staticmethod
    def get(db: Session, series_id: int) -> Optional[Series]:
        """Get a series by ID."""
        return db.query(Series).filter(Series.id == series_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Series]:
        """Get a series by name."""
        return db.query(Series).filter(Series.name == name).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Series]:
        """Get all series with pagination."""
        return db.query(Series).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, series_id: int, **kwargs) -> Optional[Series]:
        """Update a series."""
        series = db.query(Series).filter(Series.id == series_id).first()
        if series:
            for key, value in kwargs.items():
                setattr(series, key, value)
            db.commit()
            db.refresh(series)
        return series

    @staticmethod
    def delete(db: Session, series_id: int) -> bool:
        """Delete a series."""
        series = db.query(Series).filter(Series.id == series_id).first()
        if series:
            db.delete(series)
            db.commit()
            return True
        return False


class BookCRUD:
    """CRUD operations for Book."""

    @staticmethod
    def create(db: Session, original_path: str, filename: str, **kwargs) -> Book:
        """Create a new book."""
        book = Book(original_path=original_path, filename=filename, **kwargs)
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def get(db: Session, book_id: int) -> Optional[Book]:
        """Get a book by ID."""
        return db.query(Book).filter(Book.id == book_id).first()

    @staticmethod
    def get_by_hash(db: Session, file_hash: str) -> Optional[Book]:
        """Get a book by file hash."""
        return db.query(Book).filter(Book.file_hash == file_hash).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Book]:
        """Get all books with pagination."""
        return db.query(Book).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_series(db: Session, series_id: int) -> List[Book]:
        """Get all books for a series."""
        return db.query(Book).filter(Book.series_id == series_id).all()

    @staticmethod
    def update(db: Session, book_id: int, **kwargs) -> Optional[Book]:
        """Update a book."""
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            for key, value in kwargs.items():
                setattr(book, key, value)
            db.commit()
            db.refresh(book)
        return book

    @staticmethod
    def delete(db: Session, book_id: int) -> bool:
        """Delete a book."""
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            db.delete(book)
            db.commit()
            return True
        return False


class MetadataCRUD:
    """CRUD operations for Metadata."""

    @staticmethod
    def create(db: Session, book_id: int, **kwargs) -> Metadata:
        """Create metadata for a book."""
        metadata = Metadata(book_id=book_id, **kwargs)
        db.add(metadata)
        db.commit()
        db.refresh(metadata)
        return metadata

    @staticmethod
    def get_by_book(db: Session, book_id: int) -> Optional[Metadata]:
        """Get metadata for a book."""
        return db.query(Metadata).filter(Metadata.book_id == book_id).first()

    @staticmethod
    def update(db: Session, book_id: int, **kwargs) -> Optional[Metadata]:
        """Update metadata for a book."""
        metadata = db.query(Metadata).filter(Metadata.book_id == book_id).first()
        if metadata:
            for key, value in kwargs.items():
                setattr(metadata, key, value)
            db.commit()
            db.refresh(metadata)
        return metadata

    @staticmethod
    def delete(db: Session, book_id: int) -> bool:
        """Delete metadata for a book."""
        metadata = db.query(Metadata).filter(Metadata.book_id == book_id).first()
        if metadata:
            db.delete(metadata)
            db.commit()
            return True
        return False


class DuplicateCRUD:
    """CRUD operations for Duplicate."""

    @staticmethod
    def create(
        db: Session, book_id_1: int, book_id_2: int, duplicate_type: str, **kwargs
    ) -> Duplicate:
        """Create a duplicate entry."""
        duplicate = Duplicate(
            book_id_1=book_id_1, book_id_2=book_id_2, duplicate_type=duplicate_type, **kwargs
        )
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)
        return duplicate

    @staticmethod
    def get_unresolved(db: Session) -> List[Duplicate]:
        """Get all unresolved duplicates."""
        return db.query(Duplicate).filter(Duplicate.resolved == False).all()  # noqa: E712

    @staticmethod
    def mark_resolved(db: Session, duplicate_id: int, kept_book_id: int, action: str) -> bool:
        """Mark a duplicate as resolved."""
        duplicate = db.query(Duplicate).filter(Duplicate.id == duplicate_id).first()
        if duplicate:
            duplicate.resolved = True
            duplicate.kept_book_id = kept_book_id
            duplicate.action = action
            from datetime import datetime

            duplicate.resolved_at = datetime.utcnow()
            db.commit()
            return True
        return False


class TaskCRUD:
    """CRUD operations for Task."""

    @staticmethod
    def create(db: Session, task_type: str, **kwargs) -> Task:
        """Create a new task."""
        task = Task(task_type=task_type, status="pending", **kwargs)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get(db: Session, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_active(db: Session) -> List[Task]:
        """Get all active tasks."""
        return db.query(Task).filter(Task.status.in_(["pending", "running"])).all()

    @staticmethod
    def update_progress(db: Session, task_id: int, progress: int, current_item: str = None):
        """Update task progress."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.progress = progress
            if current_item:
                task.current_item = current_item
            db.commit()

    @staticmethod
    def mark_completed(db: Session, task_id: int):
        """Mark a task as completed."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "completed"
            from datetime import datetime

            task.completed_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def mark_failed(db: Session, task_id: int, error_message: str):
        """Mark a task as failed."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = error_message
            from datetime import datetime

            task.completed_at = datetime.utcnow()
            db.commit()
