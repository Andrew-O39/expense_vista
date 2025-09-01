from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

ALLOWED_PERIODS = {"weekly", "monthly", "yearly", "quarterly", "half-yearly"}

class BudgetBase(BaseModel):
    """
    Shared fields between creation, update, and response.
    """
    limit_amount: float = Field(..., example=500.0, description="Spending limit for this budget.")
    category: str = Field(..., example="Groceries", description="Category name for the budget.")
    period: str = Field(..., example="monthly", description="Period: weekly, monthly, yearly, quarterly, half-yearly.")
    notes: Optional[str] = Field(None, example="This is my grocery budget for the month.", description="Optional notes about the budget.")

    @validator("category", pre=True)
    def norm_category(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @validator("period", pre=True)
    def norm_period(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
            if v not in ALLOWED_PERIODS:
                raise ValueError(f"period must be one of {sorted(ALLOWED_PERIODS)}")
        return v


class BudgetCreate(BudgetBase):
    """
    Fields required to create a new budget.
    Inherits all fields from BudgetBase.
    """
    pass


class BudgetUpdate(BaseModel):
    """
    Fields that can be updated in an existing budget.
    All fields are optional.
    """
    limit_amount: Optional[float] = Field(None, example=600.0, description="Updated spending limit.")
    category: Optional[str] = Field(None, example="Utilities", description="Updated category name.")
    period: Optional[str] = Field(None, example="weekly", description="Updated budgeting period.")
    notes: Optional[str] = Field(None, example="Updated notes about the budget.", description="Optional notes update.")

    @validator("category", "period", pre=True)
    def normalize_optional_fields(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalize optional string fields if provided.
        """
        return v.strip().lower() if isinstance(v, str) else v

    @validator("period")
    def validate_period(cls, v: str) -> str:
        if v is not None and v not in ALLOWED_PERIODS:
            allowed = ", ".join(sorted(ALLOWED_PERIODS))
            raise ValueError(f"Invalid period '{v}'. Allowed: {allowed}")
        return v


class BudgetOut(BudgetBase):
    """
    Response model for returning a budget to the client.
    Includes metadata fields.
    """
    id: int = Field(..., description="Unique ID of the budget.")
    user_id: int = Field(..., description="ID of the user who owns the budget.")
    created_at: datetime = Field(..., description="Timestamp when the budget was created.")
    updated_at: datetime = Field(..., description="Timestamp of the last update.")

    class Config:
        orm_mode = True  # Enables ORM -> Pydantic conversion