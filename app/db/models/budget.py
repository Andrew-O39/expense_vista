"""
This model represents a user's budget for a specific category or time period.
Each budget is linked to a user.
"""
from app.db.base import Base # Base = declarative_base()
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    period = Column(String, nullable=True)  # e.g., "monthly", "weekly"
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship back to User
    owner = relationship("User", back_populates="budgets")

    def __repr__(self):
        return f"<Budget(amount={self.amount}, category={self.category}, period={self.period})>"