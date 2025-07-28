"""
SQLAlchemy model definition for user budgets.

Each Budget is associated with a user and defines a spending limit
for a specific category and period (weekly, monthly, or yearly).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Budget(Base):
    """
    Budget model representing spending limits per category.

    Attributes:
        id (int): Primary key.
        limit_amount (float): Maximum allowed spending for the period.
        category (str): Budget category (e.g., 'food', 'transport').
        period (str): Budgeting period - 'weekly', 'monthly', or 'yearly'.
        created_at (datetime): Timestamp when budget was created.
        updated_at (datetime): Timestamp of last update.
        notes (str): Optional notes about the budget.
        user_id (int): Foreign key referencing the User.
        owner (User): Relationship to the owning User.
    """
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    limit_amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    period = Column(String, nullable=False)  # 'weekly', 'monthly', or 'yearly'

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="budgets")

    def __repr__(self):
        return (
            f"<Budget(limit={self.limit_amount}, "
            f"category='{self.category}', period='{self.period}')>"
        )