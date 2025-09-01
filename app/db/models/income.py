"""
Income model definition.

Represents a financial income record linked to a specific user.
Each income entry tracks the amount, source (e.g., salary, freelance),
optional category (active vs passive), notes, and timestamps.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Income(Base):
    """
    ORM model for incomes.
    """
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Float, nullable=False, doc="The monetary amount of the income.")
    source = Column(String, nullable=False, doc="The source of the income (e.g., salary, freelance).")
    category = Column(String, nullable=True, doc="Optional category (e.g., active, passive).")
    notes = Column(String, nullable=True, doc="Optional notes about the income record.")

    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        doc="When the income was received."
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        doc="When the record was created."
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        doc="When the record was last updated."
    )

    # Relationships
    user = relationship("User", back_populates="incomes")