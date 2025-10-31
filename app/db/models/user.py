"""
SQLAlchemy model definition for the User entity.

Represents registered users in the expense tracking application.
Each user can have multiple expenses, budgets, and alert logs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Boolean, Integer, String, DateTime, func, text
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """
    ORM model representing registered users in the ExpenseVista application.

    Each user has unique login credentials (username and email) and owns
    associated financial records such as expenses, budgets, and incomes.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_token_hash = Column(String(128), nullable=True, index=True)
    verification_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    # Server-side onboarding flag (defaults to true for new users)
    first_login = Column(Boolean, nullable=False, default=True, server_default=text("true"),)

    expenses = relationship("Expense", back_populates="owner", cascade="all, delete")
    budgets = relationship("Budget", back_populates="owner", cascade="all, delete")
    alert_logs = relationship("AlertLog", back_populates="user")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")

    # Link password reset tokens
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    ml_category_maps = relationship("MLCategoryMap", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"