from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.alert_logic import check_budget_alerts


def create_expense(db: Session, expense_create: ExpenseCreate, user_id: int) -> Expense:
    """Create and save a new expense, then check budget alerts."""
    expense_data = expense_create.dict()
    expense_data["category"] = expense_data["category"].strip().lower()

    db_expense = Expense(**expense_data, user_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    check_budget_alerts(user_id, db)

    return db_expense


def get_expense(db: Session, expense_id: int) -> Expense | None:
    """Get an expense by ID."""
    return db.query(Expense).filter(Expense.id == expense_id).first()


def get_expenses_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None
) -> List[Expense]:
    """
    Retrieve a list of expenses for a given user.

    Args:
        db (Session): SQLAlchemy database session.
        user_id (int): The ID of the user whose expenses are being retrieved.
        skip (int, optional): Number of records to skip (for pagination). Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 10.
        search (str, optional): A search term to filter expenses by category,
                                description, or notes. Case-insensitive. Defaults to None.

    Returns:
        List[Expense]: A list of Expense objects matching the criteria,
                       ordered by `created_at` in descending order (newest first).
    """
    query = db.query(Expense).filter(Expense.user_id == user_id)

    if start_date and end_date:
        query = query.filter(Expense.created_at.between(start_date, end_date))
    elif start_date:
        query = query.filter(Expense.created_at >= start_date)
    elif end_date:
        query = query.filter(Expense.created_at <= end_date)

    if search:
        like_term = f"%{search}%"
        query = query.filter(
            (Expense.category.ilike(like_term)) |
            (Expense.description.ilike(like_term)) |
            (Expense.notes.ilike(like_term))
        )

    return (
        query.order_by(Expense.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_expense(db: Session, expense_id: int, expense_update: ExpenseUpdate) -> Expense | None:
    """Update an existing expense, normalizing category if provided."""
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return None

    update_data = expense_update.dict(exclude_unset=True)
    if "category" in update_data and isinstance(update_data["category"], str):
        update_data["category"] = update_data["category"].strip().lower()

    for field, value in update_data.items():
        setattr(db_expense, field, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, expense_id: int) -> bool:
    """Delete an expense by ID. Returns True if deleted, False if not found."""
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        return False

    db.delete(db_expense)
    db.commit()
    return True