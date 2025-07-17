from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate


def create_budget(db: Session, budget_data: BudgetCreate, user_id: int) -> Budget:
    """
    Create a new budget for a user.
    Normalizes category and period to lowercase to ensure consistency in comparisons.
    Args:
        db (Session): SQLAlchemy DB session.
        budget_data (BudgetCreate): Pydantic schema with new budget data.
        user_id (int): The ID of the user creating the budget.
    Returns:
        Budget: The newly created budget instance.
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
    Retrieve budgets for a specific user, with pagination support.

    Args:
        db (Session): Database session.
        user_id (int): The ID of the user.
        skip (int): Number of records to skip.
        limit (int): Max number of records to return.

    Returns:
        List[Budget]: Paginated list of budget records.
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
    Fetch a specific budget by ID for a user.
    Args:
        db (Session): DB session.
        budget_id (int): Budget ID to retrieve.
        user_id (int): Owner of the budget.
    Returns:
        Optional[Budget]: The budget object if found, else None.
    """
    return db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()


def update_budget(db: Session, db_budget: Budget, updates: BudgetUpdate) -> Budget:
    """
    Update an existing budget's fields. Also normalizes category/period if provided.
    Args:
        db (Session): DB session.
        db_budget (Budget): The existing budget object to update.
        updates (BudgetUpdate): Pydantic model with updated fields.
    Returns:
        Budget: The updated budget object.
    """
    update_data = updates.dict(exclude_unset=True)

    # Normalize if present
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
    Permanently delete a budget from the database.
    Args:
        db (Session): DB session.
        db_budget (Budget): The budget object to delete.
    """
    db.delete(db_budget)
    db.commit()