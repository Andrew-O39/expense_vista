"""
SQLAlchemy model definition for user expenses.

Each Expense represents a single transaction recorded by a user,
with fields for amount, category, description, and optional notes.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Expense(Base):
    """
    Expense model representing individual spending records.

    Attributes:
        id (int): Primary key.
        amount (float): Amount spent.
        description (str): Optional description of the expense.
        category (str): Category of the expense (e.g., 'food', 'transport').
        notes (str): Optional notes for this entry.
        created_at (datetime): Timestamp when the expense was created.
        user_id (int): Foreign key to the User table.
        owner (User): Relationship to the owning user.
    """
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="expenses")

    def __repr__(self):
        return (
            f"<Expense(amount={self.amount}, "
            f"category='{self.category}')>"
        )