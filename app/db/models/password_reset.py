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
        index=True,
        doc="Foreign key referencing the associated user. Cascade deletes when the user is removed."
    )

    token_hash = Column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        doc="SHA-256 hash of the raw reset token (never store the raw token)."
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="UTC timestamp indicating when the token expires."
    )

    used = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Flag indicating whether the token has already been used."
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the token record was created (UTC)."
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
        doc="Timestamp automatically updated whenever the token record is modified (UTC)."
    )

    # Relationship back to the user
    user = relationship(
        "User",
        back_populates="password_reset_tokens",
        doc="Relationship linking this token to its user."
    )

    __table_args__ = (
        Index(
            "ix_prt_token_not_used",
            "token_hash",
            "used",
            doc="Optimized index to quickly locate unused tokens by hash."
        ),
    )