"""
CRUD operations for Expense model.
Handles creation, retrieval, updating, and deletion of expense records.
"""

from sqlalchemy.orm import Session
from expense_tracker.app.db.models.expense import Expense
from expense_tracker.app.schemas.expense import ExpenseCreate, ExpenseUpdate

# ----------------------------
# Create a new expense
# ----------------------------
def create_expense(db: Session, expense: ExpenseCreate, user_id: int) -> Expense:
    """
    Create and store a new Expense in the database, associated with a specific user.
    """
    db_expense = Expense(**expense.dict(), user_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


# ----------------------------
# Get a single expense by ID
# ----------------------------
def get_expense(db: Session, expense_id: int) -> Expense | None:
    """
    Retrieve a single Expense by its ID.
    """
    return db.query(Expense).filter(Expense.id == expense_id).first()


# ----------------------------
# Get all expenses for a user
# ----------------------------
def get_expenses_by_user(db: Session, user_id: int) -> list[Expense]:
    """
    Retrieve all expenses that belong to a given user.
    """
    return db.query(Expense).filter(Expense.user_id == user_id).all()


# ----------------------------
# Update an existing expense
# ----------------------------
def update_expense(db: Session, expense_id: int, updates: ExpenseUpdate) -> Expense | None:
    """
    Update an existing Expense with new data.
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return None

    for field, value in updates.dict(exclude_unset=True).items():
        setattr(db_expense, field, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


# ----------------------------
# Delete an expense
# ----------------------------
def delete_expense(db: Session, expense_id: int) -> bool:
    """
    Delete an Expense by ID. Returns True if deleted, False otherwise.
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return False

    db.delete(db_expense)
    db.commit()
    return True