from sqlalchemy.orm import Session
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


def get_expenses_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> list[Expense]:
    """Retrieve a paginated list of expenses for a user, ordered by newest."""
    return (
        db.query(Expense)
        .filter(Expense.user_id == user_id)
        .order_by(Expense.created_at.desc())
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