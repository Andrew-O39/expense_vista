from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import DateTime
from sqlalchemy.sql import func

class AlertLog(Base):
    """
    Represents an alert that was triggered for a user when a budget was exceeded.
    Used for logging and analytics.
    """
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=True)
    period = Column(String, nullable=False)  # e.g., 'weekly', 'monthly', 'yearly'
    type = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now()
    )
    notes = Column(String, nullable=True)



    user = relationship("User", back_populates="alert_logs")

    def __repr__(self):
        return (
            f"<AlertLog(user_id={self.user_id}, category={self.category}, "
            f"period={self.period}, type={self.type}, created_at={self.created_at})>"
        )