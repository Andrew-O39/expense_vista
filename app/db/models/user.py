"""
SQLAlchemy model definition for the User entity.

This model represents registered users in the expense tracking application.
Each user can own multiple expenses and budgets, managed through defined relationships.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import DateTime
from sqlalchemy.sql import func

class User(Base):
    """
    User model representing application users.

    Attributes:
        id (int): Primary key, unique identifier for each user.
        username (str): Unique username used for login or identification.
        email (str): Unique email address associated with the user.
        hashed_password (str): Securely stored (hashed) password.
        expenses (List[Expense]): One-to-many relationship to Expense records.
        budgets (List[Budget]): One-to-many relationship to Budget records.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    expenses = relationship("Expense", back_populates="owner", cascade="all, delete")
    budgets = relationship("Budget", back_populates="owner", cascade="all, delete")
    alert_logs = relationship("AlertLog", back_populates="user")

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"