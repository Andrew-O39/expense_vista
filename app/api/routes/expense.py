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
from expense_tracker.app.api.deps import get_current_user
from expense_tracker.app.db.models.user import User

router = APIRouter(prefix="/expenses", tags=["Expenses"])

# -----------------------------
# Create a new expense
# -----------------------------
@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new expense record for the authenticated user.

    Requires amount, category, and optional description. Returns the created expense.
    """
    return crud_expense.create_expense(db=db, expense_create=expense, user_id=current_user.id)

# -----------------------------
# Get all expenses for user
# -----------------------------
@router.get("/", response_model=List[ExpenseOut])
def read_expenses_by_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a list of all expenses for the currently authenticated user.
    """
    return crud_expense.get_expenses_by_user(db, user_id=current_user.id)

# -----------------------------
# Get a specific expense
# -----------------------------
@router.get("/{expense_id}", response_model=ExpenseOut)
def read_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a single expense by its ID for the current user.

    Returns:
        - 200 OK with expense data if found and owned by the user
        - 404 Not Found if the expense doesn't exist or doesn't belong to the user
    """
    db_expense = crud_expense.get_expense(db, expense_id=expense_id)

    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Only allow access to the owner's data
    if db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this expense")

    return db_expense

# -----------------------------
# Update an expense
# -----------------------------
@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing expense by its ID, if it belongs to the user.

    Returns 404 if not found or not owned by the user.
    """

    # Verify ownership before updating
    db_expense = crud_expense.get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this expense")

    return crud_expense.update_expense(db=db, expense_id=expense_id, expense_update=expense)

# -----------------------------
# Delete an expense
# -----------------------------
@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an expense by its ID, if it belongs to the user.

    Returns:
        - 204 No Content if successful
        - 404 Not Found if the expense doesn't exist or isn't owned by the user
    """
    db_expense = crud_expense.get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if db_expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this expense")

    return crud_expense.delete_expense(db=db, expense_id=expense_id)