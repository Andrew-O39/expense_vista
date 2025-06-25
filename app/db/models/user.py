"""
This model defines the User model representing an account holder.
Each user can have multiple expenses and budgets.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from expense_tracker.app.db.base import Base  # Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Relationships
    expenses = relationship("Expense", back_populates="owner", cascade="all, delete")
    budgets = relationship("Budget", back_populates="owner", cascade="all, delete")

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"