"""
SQLAlchemy model for tracking budget alerts triggered for a user.

Each AlertLog entry records a budget threshold notification such as
'half_limit', 'near_limit', or 'limit_exceeded' for a specific period and category.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class AlertLog(Base):
    """
    AlertLog model representing a triggered budget alert.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key linking to the user who owns the alert.
        category (str): Budget category the alert relates to.
        period (str): Budget period ('weekly', 'monthly', 'yearly').
        type (str): Alert type - e.g., 'half_limit', 'near_limit', 'limit_exceeded'.
        notes (str): Optional notes about the alert.
        created_at (datetime): When the alert was recorded.
        user (User): SQLAlchemy relationship to the user.
    """
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=True)
    period = Column(String, nullable=False)
    type = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )

    user = relationship("User", back_populates="alert_logs")

    def __repr__(self):
        return (
            f"<AlertLog(user_id={self.user_id}, category='{self.category}', "
            f"period='{self.period}', type='{self.type}', created_at={self.created_at})>"
        )