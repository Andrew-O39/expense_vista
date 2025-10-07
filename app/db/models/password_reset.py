from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class PasswordResetToken(Base):
    """
    ORM model representing a one-time password reset token.

    This table stores hashed tokens that allow users to securely reset their passwords.
    Each token is unique, expires after a set period, and is marked as `used` once consumed.
    Tokens are linked to a specific user and automatically removed when that user is deleted.
    """

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_hash = Column(String(128), nullable=False, unique=True, index=True)

    # Expiry is always required
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Mark as used after first successful reset
    used = Column(Boolean, default=False, nullable=False)

    # Track creation + updates
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

    # Relationship back to user
    user = relationship("User", back_populates="password_reset_tokens")

    # Optimized index: lookup by token but only if not used
    __table_args__ = (
        Index("ix_prt_token_not_used", "token_hash", "used"),
    )