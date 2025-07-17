from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class BudgetBase(BaseModel):
    """
    Shared fields between creation, update, and response.
    """
    limit_amount: float = Field(..., example=500.0, description="Spending limit for this budget.")
    category: str = Field(..., example="Groceries", description="Category for the budget.")
    period: str = Field(..., example="monthly", description="Budgeting period (e.g., monthly, weekly).")
    notes: Optional[str] = Field(None, example="This is my grocery budget for the month.", description="Any extra notes.")

    @validator("category", "period", pre=True)
    def normalize_fields(cls, v: str) -> str:
        """
        Normalize strings by trimming and lowercasing.
        Applies to both category and period fields.
        """
        return v.strip().lower() if isinstance(v, str) else v


class BudgetCreate(BudgetBase):
    """
    Fields required to create a new budget.
    Inherits from BudgetBase.
    """
    pass


class BudgetUpdate(BaseModel):
    """
    Fields that can be updated on an existing budget.
    All fields are optional.
    """
    limit_amount: Optional[float] = Field(None, example=600.0, description="Updated spending limit.")
    category: Optional[str] = Field(None, example="Utilities")
    period: Optional[str] = Field(None, example="weekly")
    notes: Optional[str] = Field(None, example="Updated notes about the budget.")

    @validator("category", "period", pre=True)
    def normalize_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalize optional string fields if they are provided.
        """
        return v.strip().lower() if isinstance(v, str) else v


class BudgetOut(BudgetBase):
    """
    Response model for returning a budget to the client.
    Includes database-specific and relational fields.
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # Allows compatibility with ORM objects