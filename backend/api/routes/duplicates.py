"""API routes for managing duplicates."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.core.deduplicator import Deduplicator
from backend.database.crud import BookCRUD, DuplicateCRUD
from backend.database.models import Duplicate

router = APIRouter(prefix="/api/duplicates", tags=["duplicates"])


class DuplicateResponse(BaseModel):
    """Response model for duplicate."""

    id: int
    book_id_1: int
    book_id_2: int
    duplicate_type: str
    similarity_score: float
    resolved: bool
    action: str
    book1_filename: Optional[str] = None
    book2_filename: Optional[str] = None
    kept_book_id: Optional[int] = None

    class Config:
        from_attributes = True


class ResolveRequest(BaseModel):
    """Request to resolve a duplicate."""

    action: str  # keep_first, keep_second, keep_both
    kept_book_id: Optional[int] = None


class DetectionRequest(BaseModel):
    """Request to detect duplicates."""

    methods: Optional[List[str]] = None  # hash_exact, name_fuzzy, image_perceptual
    similarity_threshold: Optional[float] = None


@router.get("/", response_model=List[DuplicateResponse])
async def list_duplicates(
    resolved: Optional[bool] = None,
    duplicate_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Liste tous les doublons détectés.

    Args:
        resolved: Filtrer par statut résolu (None = tous)
        duplicate_type: Filtrer par type (hash_exact, name_fuzzy, image_perceptual)
        skip: Nombre d'éléments à sauter
        limit: Nombre d'éléments à retourner
        db: Session de base de données
    """
    query = db.query(Duplicate)

    if resolved is not None:
        query = query.filter(Duplicate.resolved == resolved)

    if duplicate_type:
        query = query.filter(Duplicate.duplicate_type == duplicate_type)

    duplicates = query.offset(skip).limit(limit).all()

    # Enrichir avec les noms de fichiers
    result = []
    for dup in duplicates:
        book1 = BookCRUD.get(db, dup.book_id_1)
        book2 = BookCRUD.get(db, dup.book_id_2)

        dup_dict = {
            "id": dup.id,
            "book_id_1": dup.book_id_1,
            "book_id_2": dup.book_id_2,
            "duplicate_type": dup.duplicate_type,
            "similarity_score": dup.similarity_score,
            "resolved": dup.resolved,
            "action": dup.action,
            "kept_book_id": dup.kept_book_id,
            "book1_filename": book1.filename if book1 else None,
            "book2_filename": book2.filename if book2 else None,
        }
        result.append(DuplicateResponse(**dup_dict))

    return result


@router.get("/unresolved", response_model=List[DuplicateResponse])
async def list_unresolved_duplicates(db: Session = Depends(get_db)):
    """Liste tous les doublons non résolus."""
    duplicates = DuplicateCRUD.get_unresolved(db)

    result = []
    for dup in duplicates:
        book1 = BookCRUD.get(db, dup.book_id_1)
        book2 = BookCRUD.get(db, dup.book_id_2)

        dup_dict = {
            "id": dup.id,
            "book_id_1": dup.book_id_1,
            "book_id_2": dup.book_id_2,
            "duplicate_type": dup.duplicate_type,
            "similarity_score": dup.similarity_score,
            "resolved": dup.resolved,
            "action": dup.action,
            "kept_book_id": dup.kept_book_id,
            "book1_filename": book1.filename if book1 else None,
            "book2_filename": book2.filename if book2 else None,
        }
        result.append(DuplicateResponse(**dup_dict))

    return result


@router.get("/{duplicate_id}", response_model=DuplicateResponse)
async def get_duplicate(duplicate_id: int, db: Session = Depends(get_db)):
    """Récupère un doublon spécifique."""
    duplicate = db.query(Duplicate).filter(Duplicate.id == duplicate_id).first()

    if not duplicate:
        raise HTTPException(status_code=404, detail="Duplicate not found")

    book1 = BookCRUD.get(db, duplicate.book_id_1)
    book2 = BookCRUD.get(db, duplicate.book_id_2)

    dup_dict = {
        "id": duplicate.id,
        "book_id_1": duplicate.book_id_1,
        "book_id_2": duplicate.book_id_2,
        "duplicate_type": duplicate.duplicate_type,
        "similarity_score": duplicate.similarity_score,
        "resolved": duplicate.resolved,
        "action": duplicate.action,
        "kept_book_id": duplicate.kept_book_id,
        "book1_filename": book1.filename if book1 else None,
        "book2_filename": book2.filename if book2 else None,
    }

    return DuplicateResponse(**dup_dict)


@router.post("/{duplicate_id}/resolve")
async def resolve_duplicate(
    duplicate_id: int, request: ResolveRequest, db: Session = Depends(get_db)
):
    """
    Résout un doublon.

    Args:
        duplicate_id: ID du doublon
        request: Action à effectuer
        db: Session de base de données
    """
    duplicate = db.query(Duplicate).filter(Duplicate.id == duplicate_id).first()

    if not duplicate:
        raise HTTPException(status_code=404, detail="Duplicate not found")

    if duplicate.resolved:
        raise HTTPException(status_code=400, detail="Duplicate already resolved")

    # Déterminer quel livre garder
    kept_book_id = request.kept_book_id
    if not kept_book_id:
        if request.action == "keep_first":
            kept_book_id = duplicate.book_id_1
        elif request.action == "keep_second":
            kept_book_id = duplicate.book_id_2

    # Marquer comme résolu
    success = DuplicateCRUD.mark_resolved(db, duplicate_id, kept_book_id, request.action)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to resolve duplicate")

    # Si on garde un seul fichier, déplacer l'autre
    if request.action in ["keep_first", "keep_second"]:
        deduplicator = Deduplicator(db)

        # Déterminer quel livre déplacer
        book_to_move_id = (
            duplicate.book_id_2 if request.action == "keep_first" else duplicate.book_id_1
        )
        book_to_move = BookCRUD.get(db, book_to_move_id)

        if book_to_move:
            deduplicator.move_duplicate_to_folder(book_to_move)

    logger.info(f"Duplicate {duplicate_id} resolved with action: {request.action}")

    return {"status": "success", "message": "Duplicate resolved", "action": request.action}


@router.post("/detect")
async def detect_duplicates(
    request: Optional[DetectionRequest] = None, db: Session = Depends(get_db)
):
    """
    Lance la détection de doublons sur tous les livres.

    Args:
        request: Paramètres de détection
        db: Session de base de données
    """
    logger.info("Starting duplicate detection")

    # Récupérer tous les livres
    books = BookCRUD.get_all(db, skip=0, limit=10000)

    if not books:
        return {
            "status": "success",
            "message": "No books to analyze",
            "total_duplicates": 0,
        }

    # Créer le déduplicator
    deduplicator = Deduplicator(
        db,
        similarity_threshold=request.similarity_threshold if request else None,
    )

    # Lancer la détection
    results = deduplicator.run_full_detection(books)

    # Sauvegarder les résultats en DB
    if results["exact_duplicates"]:
        deduplicator.save_duplicates_to_db(results["exact_duplicates"], "hash_exact")

    if results["fuzzy_duplicates"]:
        # Convertir le format (book1, book2, score) en (book1, book2)
        fuzzy_pairs = [(b1, b2) for b1, b2, _ in results["fuzzy_duplicates"]]
        deduplicator.save_duplicates_to_db(fuzzy_pairs, "name_fuzzy")

    if results["perceptual_duplicates"]:
        # Convertir le format (book1, book2, distance) en (book1, book2)
        perceptual_pairs = [(b1, b2) for b1, b2, _ in results["perceptual_duplicates"]]
        deduplicator.save_duplicates_to_db(perceptual_pairs, "hash_perceptual")

    logger.info(f"Duplicate detection completed: {results['total_duplicates']} found")

    return {
        "status": "success",
        "message": "Duplicate detection completed",
        "total_books": results["total_books"],
        "exact_duplicates": len(results["exact_duplicates"]),
        "fuzzy_duplicates": len(results["fuzzy_duplicates"]),
        "perceptual_duplicates": len(results["perceptual_duplicates"]),
        "total_duplicates": results["total_duplicates"],
    }


@router.get("/stats")
async def get_duplicate_stats(db: Session = Depends(get_db)):
    """Obtient les statistiques sur les doublons."""
    total = db.query(Duplicate).count()
    resolved = db.query(Duplicate).filter(Duplicate.resolved == True).count()  # noqa: E712
    unresolved = total - resolved

    by_type = {}
    for dup_type in ["hash_exact", "name_fuzzy", "hash_perceptual"]:
        count = db.query(Duplicate).filter(Duplicate.duplicate_type == dup_type).count()
        by_type[dup_type] = count

    return {
        "total": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "by_type": by_type,
    }
