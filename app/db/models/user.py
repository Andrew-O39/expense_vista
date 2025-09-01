"""
SQLAlchemy model definition for the User entity.

Represents registered users in the expense tracking application.
Each user can have multiple expenses, budgets, and alert logs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """
    User model representing application users.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        email (str): Unique email address.
        hashed_password (str): Securely hashed password.
        created_at (datetime): Timestamp of account creation.
        expenses: One-to-many relationship to expenses.
        budgets: One-to-many relationship to budgets.
        alert_logs: One-to-many relationship to alert logs.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    expenses = relationship("Expense", back_populates="owner", cascade="all, delete")
    budgets = relationship("Budget", back_populates="owner", cascade="all, delete")
    alert_logs = relationship("AlertLog", back_populates="user")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"