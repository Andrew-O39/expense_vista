"""
This model represents a user's budget for a specific category or time period.
Each budget is linked to a user.
"""
from app.db.base import Base # Base = declarative_base()
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    limit_amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    period = Column(String, nullable=False)  # "weekly", "monthly", or "yearly"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="budgets")

    def __repr__(self):
        return f"<Budget(limit={self.limit_amount}, category={self.category}, period={self.period})>"