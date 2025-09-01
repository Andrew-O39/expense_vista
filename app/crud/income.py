"""
CRUD operations for the Income model.
Handles creation, retrieval, updating, and deletion of income records.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.db.models.income import Income
from app.schemas.income import IncomeCreate, IncomeUpdate


def create_income(db: Session, income_create: IncomeCreate, user_id: int) -> Income:
    """
    Create and store a new Income for the given user.

    - Normalizes text fields defensively (schema already normalizes).
    - If `received_at` is not provided, defaults to current UTC time.
    """
    data = income_create.dict()

    # Defensive normalization (schemas already handle this)
    if isinstance(data.get("source"), str):
        data["source"] = data["source"].strip().lower()
    if isinstance(data.get("category"), str) and data["category"] is not None:
        data["category"] = data["category"].strip().lower()


    # Ensure received_at exists and is UTC-aware
    if not data.get("received_at"):
        data["received_at"] = datetime.now(timezone.utc) # Default received_at to now (UTC) if omitted
    else:
        # If client sent a naive datetime, make it UTC
        if data["received_at"].tzinfo is None:
            data["received_at"] = data["received_at"].replace(tzinfo=timezone.utc)

    income = Income(**data, user_id=user_id)
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def get_income(db: Session, income_id: int) -> Optional[Income]:
    """Return a single Income by ID (or None)."""
    return db.query(Income).filter(Income.id == income_id).first()


def get_incomes_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
) -> List[Income]:
    """
    Retrieve a paginated list of incomes for a user, newest first,
    with optional filters (date range by received_at, category, source, amount range),
    and case-insensitive free-text search across category/source/notes.
    """
    q = db.query(Income).filter(Income.user_id == user_id)

    # Date range (received_at)
    if start_date:
        q = q.filter(Income.received_at >= start_date)
    if end_date:
        q = q.filter(Income.received_at <= end_date)

    # Case-insensitive text filters
    if category:
        q = q.filter(func.lower(Income.category) == category.strip().lower())
    if source:
        q = q.filter(func.lower(Income.source) == source.strip().lower())

    # Amount range
    if min_amount is not None:
        q = q.filter(Income.amount >= min_amount)
    if max_amount is not None:
        q = q.filter(Income.amount <= max_amount)

    # Free-text search across category, source, notes (case-insensitive)
    if search:
        term = f"%{search.strip().lower()}%"
        q = q.filter(
            or_(
                func.lower(Income.category).like(term),
                func.lower(Income.source).like(term),
                func.lower(func.coalesce(Income.notes, "")).like(term),
            )
        )

    # Newest first — prefer received_at if available, else created_at
    q = q.order_by(
        (Income.received_at.desc() if hasattr(Income, "received_at") else Income.created_at.desc())
    )

    return q.offset(skip).limit(limit).all()


def update_income(db: Session, income_id: int, updates: IncomeUpdate) -> Optional[Income]:
    """
    Partially update an Income. Returns None if not found.
    """
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        return None

    data = updates.dict(exclude_unset=True)

    # Defensive normalization
    if "source" in data and isinstance(data["source"], str):
        data["source"] = data["source"].strip().lower()
    if "category" in data and isinstance(data["category"], str) and data["category"] is not None:
        data["category"] = data["category"].strip().lower()

    for field, value in data.items():
        setattr(income, field, value)

    db.commit()
    db.refresh(income)
    return income


def delete_income(db: Session, income_id: int) -> bool:
    """
    Delete an Income by ID. Returns True if deleted, False if not found.
    """
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        return False

    db.delete(income)
    db.commit()
    return True