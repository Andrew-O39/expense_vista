from pydantic import BaseModel, confloat, Field, validator
from datetime import datetime
from typing import Optional

class IncomeBase(BaseModel):
    """
    Shared fields for reading and writing income data.
    """
    amount: float = Field(..., example=1500.00, description="The amount of income received.")
    source: str = Field(..., example="Salary", description="The source of the income.")
    category: Optional[str] = Field(None, example="Active", description="Optional category (Active, Passive, etc.)")
    notes: Optional[str] = Field(None, example="Monthly paycheck", description="Additional notes about the income.")
    received_at: Optional[datetime] = Field(None, description="Timestamp when income was received." )

    @validator("source", "category", pre=True)
    def normalize_text(cls, v):
        # Normalize text fields for consistent querying and grouping
        return v.strip().lower() if isinstance(v, str) else v


class IncomeCreate(IncomeBase):
    """
    Schema for creating a new income.
    """
    pass


class IncomeUpdate(BaseModel):
    """
    Schema for partial updates to an income.
    """
    amount: Optional[confloat(gt=0)] = None
    source: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None

    @validator("source", "category", pre=True)
    def normalize_text(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


class IncomeOut(IncomeBase):
    """
    Schema returned to clients for an income record.
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True