"""
Pydantic schemas for the Expense model.

These schemas define how expense data is validated and structured when:
- receiving data from the client (input)
- sending data back to the client (output)
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base class with shared fields
class ExpenseBase(BaseModel):
    """
    Shared fields used for both reading and writing expense data.

    This schema can be inherited by other schemas like ExpenseCreate and ExpenseUpdate.
    """
    amount: float
    description: Optional[str] = None
    category: Optional[str] = None

# Schema for creation
class ExpenseCreate(ExpenseBase):
    """
    Schema for creating a new expense.
    In addition to base fields, the user_id is required to link the expense to a user.
    """
    user_id: int # Required when creating an expense

# Schema for update (all fields optional)
class ExpenseUpdate(ExpenseBase):
    """
    Schema for updating an existing expense.
    All fields are optional; allows partial updates.
    """
    pass  # Optional update schema (patch)

# Schema for API response
class ExpenseOut(ExpenseBase):
    """
    Schema for returning an expense from the API.
    Includes ID, timestamp, and user_id.
    Enables compatibility with SQLAlchemy ORM objects.
    """
    id: int
    timestamp: datetime
    user_id: int

    class Config:
        orm_mode = True  # Allows automatic conversion from SQLAlchemy model to Pydantic schema. It tells Pydantic to read data as ORM objects

