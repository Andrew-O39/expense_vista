from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime
from app.db.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate

ALLOWED_PERIODS = {'weekly', 'monthly', 'yearly', 'quarterly', 'half-yearly'}

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


def get_user_budgets(
    db: Session,
    user_id: int,
    period: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 10
) -> List[Budget]:
    """
    Retrieve budgets for a user with optional filtering and pagination.

    Filtering:
        - period: Must match one of the allowed periods (e.g., "weekly", "monthly", "yearly").
        - category: Case-insensitive match against the budget category.
        - search: Case-insensitive partial match against category or notes.

    Pagination:
        - skip: Number of records to skip.
        - limit: Maximum number of records to return.
    """
    query = db.query(Budget).filter(Budget.user_id == user_id)

    if period:
        normalized_period = period.strip().lower()
        if normalized_period not in ALLOWED_PERIODS:
            raise HTTPException(status_code=400, detail="Invalid period value")
        query = query.filter(Budget.period == normalized_period)

    if category:
        normalized_category = category.strip().lower()
        query = query.filter(Budget.category == normalized_category)

    if search:
        search_term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Budget.category.ilike(search_term),
                Budget.notes.ilike(search_term)
            )
        )

    if start_date and end_date:
        query = query.filter(Budget.created_at.between(start_date, end_date))
    elif start_date:
        query = query.filter(Budget.created_at >= start_date)
    elif end_date:
        query = query.filter(Budget.created_at <= end_date)


    return query.order_by(Budget.created_at.desc()).offset(skip).limit(limit).all()


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