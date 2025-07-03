"""
CRUD operations for Expense model.
Handles creation, retrieval, updating, and deletion of expense records.
"""

from sqlalchemy.orm import Session
from app.db.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

# ----------------------------
# Create a new expense
# ----------------------------
def create_expense(db: Session, expense_create: ExpenseCreate, user_id: int) -> Expense:
    """
    Create and store a new Expense in the database, associated with a specific user.

    Args:
        db (Session): SQLAlchemy database session.
        expense_create (ExpenseCreate): Validated Pydantic schema with expense data.
        user_id (int): ID of the user who owns the expense.

    Returns:
        Expense: The newly created Expense ORM object.
    """
    db_expense = Expense(**expense_create.dict(), user_id=user_id)
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

    Args:
        db (Session): SQLAlchemy session.
        expense_id (int): ID of the expense to retrieve.

    Returns:
        Expense | None: The Expense if found, otherwise None.
    """
    return db.query(Expense).filter(Expense.id == expense_id).first()



# ----------------------------
# Get all expenses for a user
# ----------------------------
def get_expenses_by_user(db: Session, user_id: int) -> list[Expense]:
    """
    Retrieve all expenses that belong to a given user.

    Args:
        db (Session): SQLAlchemy session.
        user_id (int): ID of the user whose expenses to fetch.

    Returns:
        list[Expense]: A list of Expense objects.
    """
    return db.query(Expense).filter(Expense.user_id == user_id).all()


# ----------------------------
# Update an existing expense
# ----------------------------
def update_expense(db: Session, expense_id: int, expense_update: ExpenseUpdate) -> Expense | None:
    """
    Update an existing Expense with new data.

    Args:
        db (Session): SQLAlchemy session.
        expense_id (int): ID of the expense to update.
        expense_update (ExpenseUpdate): Data to update the expense with.

    Returns:
        Expense | None: The updated Expense if found, otherwise None.
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return None

    for field, value in expense_update.dict(exclude_unset=True).items():
        setattr(db_expense, field, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


# ----------------------------
# Delete an expense
# ----------------------------
def delete_expense(db: Session, expense_id: int) -> bool:
    """
    Delete an Expense by ID.

    Args:
        db (Session): SQLAlchemy session.
        expense_id (int): ID of the expense to delete.

    Returns:
        bool: True if deleted, False if not found.
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return False

    db.delete(db_expense)
    db.commit()
    return True