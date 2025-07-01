"""
API routes for managing expenses.

These endpoints allow users to:
- create a new expense
- retrieve one or all of their expenses
- update or delete an expense
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from expense_tracker.app.schemas.expense import ExpenseOut, ExpenseCreate, ExpenseUpdate
from expense_tracker.app.db.session import get_db
from expense_tracker.app.crud import expense as crud_expense

router = APIRouter(prefix="/expenses", tags=["Expenses"])

def get_current_user_id() -> int:
    """
    Temporary stub to simulate an authenticated user.
    Will be replaced with real user extraction logic (e.g., from JWT) when implementing auth.
    """
    return 1


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    """
    Create a new expense record.

    Requires amount, category, and optional description. Returns the created expense.
    """
    user_id = get_current_user_id()
    return crud_expense.create_expense(db=db, expense_create=expense, user_id=user_id)


@router.get("/", response_model=List[ExpenseOut])
def read_expenses_by_user(db: Session = Depends(get_db)):
    """
    Retrieve a list of all expenses for the currently authenticated user.
    """
    user_id = get_current_user_id()
    return crud_expense.get_expenses_by_user(db, user_id=user_id)


@router.get("/{expense_id}", response_model=ExpenseOut)
def read_expense(expense_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single expense by its ID.

    Returns:
        - 200 OK with expense data if found
        - 404 Not Found if the expense doesn't exist
    """
    db_expense = crud_expense.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return db_expense


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, expense: ExpenseUpdate, db: Session = Depends(get_db)):
    """
    Update an existing expense by its ID.

    Accepts partial updates. Returns 404 if the expense does not exist.
    """
    updated = crud_expense.update_expense(db=db, expense_id=expense_id, expense_update=expense)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return updated


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """
    Delete an expense by its ID.

    Returns:
        - 204 No Content if successful
        - 404 Not Found if the expense doesn't exist
    """
    deleted = crud_expense.delete_expense(db=db, expense_id=expense_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return