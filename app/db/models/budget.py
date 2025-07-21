"""
This model represents a user's budget for a specific category or time period.
Each budget is linked to a user.
"""
from app.db.base import Base # Base = declarative_base()
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.sql import func

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    limit_amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    period = Column(String, nullable=False)  # "weekly", "monthly", or "yearly"
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
        return f"<Budget(limit={self.limit_amount}, category={self.category}, period={self.period})>"