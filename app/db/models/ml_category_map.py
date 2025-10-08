from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class MLCategoryMap(Base):
    """
    Stores AI-assisted category mappings learned from user inputs, so we can
    suggest or auto-fill categories for similar future entries.
    """
    __tablename__ = "ml_category_maps"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # A normalized key the model uses (e.g., cleaned merchant or description)
    pattern = Column(String(256), nullable=False)

    # The category we believe is correct for this pattern
    category = Column(String(128), nullable=False)

    # Optional: model version / source (“rules”, “openai-2025-x”, etc.)
    source = Column(String(64), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    # A user shouldn’t have duplicate pattern entries
    __table_args__ = (
        UniqueConstraint("user_id", "pattern", name="uq_ml_map_user_pattern"),
        Index("ix_ml_map_user_pattern", "user_id", "pattern"),
    )

    user = relationship("User", back_populates="ml_category_maps")