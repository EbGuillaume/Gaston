"""Database models for Gaston."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database.session import Base


class Series(Base):
    """Modèle pour les séries détectées."""

    __tablename__ = "series"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(
        String,
        CheckConstraint("type IN ('BD', 'Comic', 'Manga', 'Book', 'Oneshot', 'Integrale')"),
    )
    language = Column(String, default="fr")
    folder_path = Column(String)
    komga_ready = Column(Boolean, default=False)
    total_books = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    books = relationship("Book", back_populates="series", cascade="all, delete-orphan")


class Book(Base):
    """Modèle pour les fichiers/livres."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(Integer, ForeignKey("series.id", ondelete="CASCADE"))
    original_path = Column(String, nullable=False)
    new_path = Column(String)
    filename = Column(String, nullable=False)
    file_hash = Column(String, index=True)
    file_size = Column(Integer)
    number = Column(Integer)
    title = Column(String)
    extension = Column(String)
    status = Column(
        String,
        CheckConstraint(
            "status IN ('pending', 'processing', 'renamed', 'organized', 'error')"
        ),
    )
    has_metadata = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    is_corrupted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    series = relationship("Series", back_populates="books")
    metadata = relationship(
        "Metadata", back_populates="book", uselist=False, cascade="all, delete-orphan"
    )
    duplicates_as_first = relationship(
        "Duplicate",
        foreign_keys="[Duplicate.book_id_1]",
        back_populates="book_1",
        cascade="all, delete-orphan",
    )
    duplicates_as_second = relationship(
        "Duplicate",
        foreign_keys="[Duplicate.book_id_2]",
        back_populates="book_2",
        cascade="all, delete-orphan",
    )


class Metadata(Base):
    """Modèle pour les métadonnées enrichies."""

    __tablename__ = "metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), unique=True)
    source = Column(
        String,
        CheckConstraint("source IN ('bedetheque', 'comicvine', 'manual', 'embedded')"),
    )
    confidence_score = Column(Float)

    # Données bibliographiques
    series_name = Column(String)
    volume_number = Column(Integer)
    title = Column(String)
    summary = Column(Text)

    # Créateurs (stockés en JSON array)
    writers = Column(Text)  # JSON array
    pencillers = Column(Text)  # JSON array
    inkers = Column(Text)  # JSON array
    colorists = Column(Text)  # JSON array
    letterers = Column(Text)  # JSON array

    # Publication
    publisher = Column(String)
    publication_date = Column(String)
    isbn = Column(String)
    page_count = Column(Integer)

    # Classification
    genres = Column(Text)  # JSON array
    tags = Column(Text)  # JSON array
    age_rating = Column(String)

    # Médias
    cover_url = Column(String)
    cover_local_path = Column(String)

    # Données brutes
    raw_data = Column(Text)  # JSON

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    book = relationship("Book", back_populates="metadata")


class Duplicate(Base):
    """Modèle pour les doublons détectés."""

    __tablename__ = "duplicates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id_1 = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    book_id_2 = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    similarity_score = Column(Float)
    duplicate_type = Column(
        String,
        CheckConstraint("duplicate_type IN ('hash_exact', 'hash_perceptual', 'name_fuzzy')"),
    )
    resolved = Column(Boolean, default=False)
    kept_book_id = Column(Integer, ForeignKey("books.id", ondelete="SET NULL"))
    action = Column(
        String,
        CheckConstraint("action IN ('keep_both', 'keep_first', 'keep_second', 'pending')"),
    )
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    # Relations
    book_1 = relationship("Book", foreign_keys=[book_id_1], back_populates="duplicates_as_first")
    book_2 = relationship(
        "Book", foreign_keys=[book_id_2], back_populates="duplicates_as_second"
    )


class Task(Base):
    """Modèle pour les tâches asynchrones."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(
        String,
        CheckConstraint(
            "task_type IN ('scan', 'rename', 'organize', 'scrape', 'dedupe', 'ocr')"
        ),
    )
    status = Column(
        String,
        CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')"),
    )
    progress = Column(Integer, default=0)
    total = Column(Integer, default=0)
    current_item = Column(String)
    log_messages = Column(Text)  # JSON
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Config(Base):
    """Modèle pour la configuration globale."""

    __tablename__ = "config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    value_type = Column(
        String, CheckConstraint("value_type IN ('string', 'integer', 'boolean', 'json')")
    )
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperationHistory(Base):
    """Modèle pour l'historique des opérations."""

    __tablename__ = "operations_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(
        String,
        CheckConstraint(
            "operation_type IN ('rename', 'move', 'delete', 'metadata_update')"
        ),
    )
    book_id = Column(Integer, ForeignKey("books.id", ondelete="SET NULL"))
    before_state = Column(Text)  # JSON
    after_state = Column(Text)  # JSON
    reversible = Column(Boolean, default=True)
    rolled_back = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
