"""
API routes for managing expenses.

These endpoints allow authenticated users to:
- Create a new expense
- Retrieve their expenses (individually or in a list)
- Update or delete an expense
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.schemas.expense import ExpenseOut, ExpenseCreate, ExpenseUpdate
from app.db.session import get_db
from app.crud import expense as crud_expense
from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new expense.

    The expense will be associated with the currently authenticated user.
    Requires an amount, category, and optionally a description.
    """
    return crud_expense.create_expense(db=db, expense_create=expense, user_id=current_user.id)


@router.get("/", response_model=List[ExpenseOut])
def read_expenses_by_user(
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(10, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a list of all expenses for the current user.

    Supports pagination using `skip` and `limit` query parameters.
    """
    return crud_expense.get_expenses_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get("/{expense_id}", response_model=ExpenseOut)
def read_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific expense by its ID.

    Only accessible if the expense belongs to the current user.
    Returns 404 if not found and 403 if access is denied.
    """
    db_expense = crud_expense.get_expense(db, expense_id=expense_id)

    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this expense")

    return db_expense


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing expense by ID.

    Only the owner can update the expense. Returns:
    - 404 if the expense is not found
    - 403 if the user does not own the expense
    """
    db_expense = crud_expense.get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this expense")

    return crud_expense.update_expense(db=db, expense_id=expense_id, expense_update=expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an expense by its ID.

    Only the owner of the expense can delete it. Returns:
    - 204 No Content on success
    - 404 if the expense is not found
    - 403 if the user does not own the expense
    """
    db_expense = crud_expense.get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this expense")

    return crud_expense.delete_expense(db=db, expense_id=expense_id)