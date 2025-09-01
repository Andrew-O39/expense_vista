"""
API routes for managing incomes.

These endpoints allow users to:
- create a new income
- retrieve one or all of their incomes
- update or delete an income
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeOut
from app.crud import income as crud_income

router = APIRouter(prefix="/incomes", tags=["Incomes"])

@router.post("/", response_model=IncomeOut, status_code=status.HTTP_201_CREATED)
def create_income(
    payload: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new income entry for the authenticated user.
    """
    return crud_income.create_income(db=db, income_create=payload, user_id=current_user.id)


@router.get("/", response_model=List[IncomeOut])
def list_incomes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    start_date: Optional[datetime] = Query(
        None, description="ISO timestamp start (filters by received_at, e.g., 2025-08-01T00:00:00Z)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="ISO timestamp end (filters by received_at, e.g., 2025-08-31T23:59:59Z)"
    ),
    category: Optional[str] = Query(
        None, description="Filter by category (case-insensitive)"
    ),
    source: Optional[str] = Query(
        None, description="Filter by income source (case-insensitive)"
    ),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum income amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum income amount"),
    search: Optional[str] = Query(
        None,
        description="Free-text search across category, source, notes (case-insensitive)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a paginated list of the current user's incomes (newest first), with optional filters:
    - Date range: `start_date`, `end_date` (filter by `received_at`)
    - Text: `category`, `source` (case-insensitive)
    - Amount range: `min_amount`, `max_amount`
    - Free-text `search` over category, source, notes (case-insensitive)
    """
    return crud_income.get_incomes_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        category=category,
        source=source,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
    )


@router.get("/{income_id}", response_model=IncomeOut)
def get_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single income entry by ID (must belong to the current user).
    """
    inc = crud_income.get_income(db, income_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Income not found")
    if inc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this income")
    return inc


@router.put("/{income_id}", response_model=IncomeOut)
def update_income(
    income_id: int,
    payload: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing income entry (must belong to the current user).
    """
    inc = crud_income.get_income(db, income_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Income not found")
    if inc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this income")

    updated = crud_income.update_income(db, income_id=income_id, updates=payload)
    return updated


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an income entry (must belong to the current user).
    """
    inc = crud_income.get_income(db, income_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Income not found")
    if inc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this income")

    ok = crud_income.delete_income(db, income_id)
    if not ok:
        # Shouldn't happen because we just fetched it, but for completeness:
        raise HTTPException(status_code=404, detail="Income not found")
    return