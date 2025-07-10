from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate


# Create a new budget
def create_budget(db: Session, budget_data: BudgetCreate, user_id: int) -> Budget:
    db_budget = Budget(**budget_data.dict(), user_id=user_id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


# Get all budgets for a specific user
def get_user_budgets(db: Session, user_id: int) -> List[Budget]:
    return db.query(Budget).filter(Budget.user_id == user_id).all()


# Get a single budget by its ID (belonging to the user)
def get_budget_by_id(db: Session, budget_id: int, user_id: int) -> Optional[Budget]:
    return db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()


# Update an existing budget
def update_budget(db: Session, db_budget: Budget, updates: BudgetUpdate) -> Budget:
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(db_budget, field, value)
    db.commit()
    db.refresh(db_budget)
    return db_budget


# Delete a budget
def delete_budget(db: Session, db_budget: Budget) -> None:
    db.delete(db_budget)
    db.commit()