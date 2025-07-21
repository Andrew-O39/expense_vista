"""
Represents a single expense entry.
Linked to a specific user via a foreign key.
"""
from app.db.base import Base
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.sql import func

class Expense(Base):
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

    # Relationship back to User
    owner = relationship("User", back_populates="expenses")

    def __repr__(self):
        return f"<Expense(amount={self.amount}, category={self.category})>"