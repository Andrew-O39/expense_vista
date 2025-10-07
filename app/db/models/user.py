"""
SQLAlchemy model definition for the User entity.

Represents registered users in the expense tracking application.
Each user can have multiple expenses, budgets, and alert logs.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class User(Base):
    """
    ORM model representing registered users in the ExpenseVista application.

    Each user has unique login credentials (username and email) and owns
    associated financial records such as expenses, budgets, and incomes.
    """

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        doc="Unique identifier for the user (primary key)."
    )

    username = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
        doc="Unique username chosen by the user for login and display."
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address used for authentication and password resets."
    )

    hashed_password = Column(
        String,
        nullable=False,
        doc="Hashed version of the user's password (never stored in plaintext)."
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp (UTC) indicating when the user account was created."
    )

    # --- Relationships ---

    expenses = relationship(
        "Expense",
        back_populates="owner",
        cascade="all, delete",
        doc="List of all expenses recorded by the user."
    )

    budgets = relationship(
        "Budget",
        back_populates="owner",
        cascade="all, delete",
        doc="Budgets created by the user, defining spending limits per category."
    )

    alert_logs = relationship(
        "AlertLog",
        back_populates="user",
        doc="Records of budget or expense alerts sent to the user."
    )

    incomes = relationship(
        "Income",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="List of income entries associated with this user."
    )

    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="Password reset tokens linked to the user for password recovery."
    )

    def __repr__(self) -> str:
        """Readable string representation for debugging and logs."""
        return f"<User(username={self.username}, email={self.email})>"