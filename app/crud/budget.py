from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate


def create_budget(db: Session, budget_data: BudgetCreate, user_id: int) -> Budget:
    """
    Create a new budget for a user with normalized category and period.
    """
    normalized_data = budget_data.dict()
    normalized_data["category"] = normalized_data["category"].lower()
    normalized_data["period"] = normalized_data["period"].lower()

    db_budget = Budget(**normalized_data, user_id=user_id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


def get_user_budgets(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[Budget]:
    """
    Retrieve budgets for a user with pagination.
    """
    return (
        db.query(Budget)
        .filter(Budget.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_budget_by_id(db: Session, budget_id: int, user_id: int) -> Optional[Budget]:
    """
    Get a budget by ID for a given user.
    """
    return db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()


def update_budget(db: Session, db_budget: Budget, updates: BudgetUpdate) -> Budget:
    """
    Update budget fields, normalizing category and period if present.
    """
    update_data = updates.dict(exclude_unset=True)

    if "category" in update_data and update_data["category"]:
        update_data["category"] = update_data["category"].lower()
    if "period" in update_data and update_data["period"]:
        update_data["period"] = update_data["period"].lower()

    for field, value in update_data.items():
        setattr(db_budget, field, value)

    db.commit()
    db.refresh(db_budget)
    return db_budget


def delete_budget(db: Session, db_budget: Budget) -> None:
    """
    Delete a budget from the database.
    """
    db.delete(db_budget)
    db.commit()