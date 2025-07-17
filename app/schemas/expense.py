"""
Pydantic schemas for the Expense model.

These schemas define how expense data is validated and structured when:
- receiving data from the client (input)
- sending data back to the client (output)
"""

from pydantic import BaseModel, confloat, validator
from typing import Optional
from datetime import datetime


class ExpenseBase(BaseModel):
    """
    Shared fields used for both reading and writing expense data.

    This schema can be inherited by other schemas like ExpenseCreate and ExpenseUpdate.
    """
    amount: confloat(gt=0)
    description: Optional[str] = None
    category: str
    notes: Optional[str] = None

    @validator("category", pre=True)
    def normalize_category(cls, v: str) -> str:
        """
        Normalize the category by making it lowercase and trimming whitespace.
        This helps ensure consistency when matching against budgets.
        """
        return v.strip().lower() if isinstance(v, str) else v


class ExpenseCreate(ExpenseBase):
    """
    Schema for creating a new expense.
    Inherits required fields from ExpenseBase.
    """
    pass


class ExpenseUpdate(BaseModel):
    """
    Schema for updating an existing expense.
    All fields are optional; allows partial updates.
    """
    amount: Optional[confloat(gt=0)] = None
    description: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None

    @validator("category", pre=True)
    def normalize_category(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalize the category if provided.
        """
        return v.strip().lower() if isinstance(v, str) else v


class ExpenseOut(ExpenseBase):
    """
    Schema for returning an expense from the API.
    Includes ID, timestamp, and user_id.
    Enables compatibility with SQLAlchemy ORM objects.
    """
    id: int
    created_at: datetime
    user_id: int

    class Config:
        orm_mode = True  # Enables ORM-to-Pydantic conversion