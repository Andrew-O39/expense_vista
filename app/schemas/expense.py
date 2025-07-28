from pydantic import BaseModel, confloat, Field, validator
from typing import Optional
from datetime import datetime


class ExpenseBase(BaseModel):
    """
    Shared fields for creating and returning expense data.
    """
    amount: confloat(gt=0) = Field(..., example=25.50, description="Amount of money spent (must be greater than zero).")
    description: Optional[str] = Field(None, example="Dinner at a restaurant", description="Optional short description of the expense.")
    category: str = Field(..., example="Food", description="Category under which this expense falls.")
    notes: Optional[str] = Field(None, example="Used company card", description="Optional additional notes or details.")

    @validator("category", pre=True)
    def normalize_category(cls, v: str) -> str:
        """
        Normalize the category by lowercasing and stripping whitespace.
        Ensures consistency across budget/expense comparisons.
        """
        return v.strip().lower() if isinstance(v, str) else v


class ExpenseCreate(ExpenseBase):
    """
    Schema for creating a new expense.
    Inherits all required fields from ExpenseBase.
    """
    pass


class ExpenseUpdate(BaseModel):
    """
    Schema for updating an existing expense.
    All fields are optional to allow partial updates.
    """
    amount: Optional[confloat(gt=0)] = Field(None, example=40.0, description="New amount (must be greater than zero).")
    description: Optional[str] = Field(None, example="Changed to lunch")
    category: Optional[str] = Field(None, example="Dining", description="New category name.")
    notes: Optional[str] = Field(None, example="Updated reimbursement note.")

    @validator("category", pre=True)
    def normalize_category(cls, v: Optional[str]) -> Optional[str]:
        """
        Normalize the category if provided.
        """
        return v.strip().lower() if isinstance(v, str) else v


class ExpenseOut(ExpenseBase):
    """
    Schema used for returning an expense to the client.
    Includes metadata such as ID, timestamps, and ownership.
    """
    id: int = Field(..., description="Unique identifier of the expense.")
    created_at: datetime = Field(..., description="Timestamp of when the expense was created.")
    user_id: int = Field(..., description="ID of the user who created this expense.")

    class Config:
        orm_mode = True  # Enables use with ORM models like SQLAlchemy