from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetOut
from app.db.session import get_db
from app.crud import budget as crud_budget
from app.db.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("/", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new budget.

    The budget will be associated with the currently authenticated user.
    """
    return crud_budget.create_budget(db=db, budget_data=budget, user_id=current_user.id)


@router.get("/", response_model=List[BudgetOut])
def get_user_budgets(
    skip: int = Query(0, ge=0, description="Number of budgets to skip (for pagination)"),
    limit: int = Query(10, le=100, description="Maximum number of budgets to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all budgets belonging to the current user.

    Supports pagination via `skip` and `limit` query parameters.
    """
    return crud_budget.get_user_budgets(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get("/{budget_id}", response_model=BudgetOut)
def get_budget_by_id(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a single budget by its ID.

    The budget must belong to the current user.
    """
    budget = crud_budget.get_budget_by_id(db, budget_id=budget_id, user_id=current_user.id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.put("/{budget_id}", response_model=BudgetOut)
def update_budget(
    budget_id: int,
    updates: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing budget by ID.

    The budget must belong to the current user.
    """
    db_budget = crud_budget.get_budget_by_id(db, budget_id=budget_id, user_id=current_user.id)
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return crud_budget.update_budget(db, db_budget=db_budget, updates=updates)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a budget by ID.

    Only budgets belonging to the current user can be deleted.
    """
    db_budget = crud_budget.get_budget_by_id(db, budget_id=budget_id, user_id=current_user.id)
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    crud_budget.delete_budget(db, db_budget=db_budget)