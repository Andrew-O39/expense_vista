# app/services/email_verification.py
from __future__ import annotations
import secrets, hmac, hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.models.user import User

TOKEN_BYTES = 24          # ~32-48 chars urlsafe
TOKEN_TTL_HOURS = 24

def _hash_token(raw: str) -> str:
    # sha256 hex – simple and adequate here
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def issue_verification_token(db: Session, user: User) -> str:
    """
    Creates a new raw token, stores its hash + expiry on the user, and returns the *raw* token
    to embed in the verification link. Any previous token is overwritten.
    """
    raw = secrets.token_urlsafe(TOKEN_BYTES)
    user.verification_token_hash = _hash_token(raw)
    user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)
    db.add(user)
    db.commit()
    return raw

def consume_verification_token(db: Session, raw_token: str) -> bool:
    """
    Verifies token:
      - matches stored hash (constant-time)
      - not expired
    On success: marks user verified and clears token fields. Returns True/False.
    """
    token_hash = _hash_token(raw_token)

    # Look up by hash (index recommended; you already have index=True)
    user = db.query(User).filter(User.verification_token_hash == token_hash).first()
    if not user:
        return False

    # Expired or already verified?
    now = datetime.now(timezone.utc)
    if user.is_verified or not user.verification_token_expires_at or user.verification_token_expires_at < now:
        return False

    # Constant-time check (belt & braces)
    if not hmac.compare_digest(user.verification_token_hash or "", token_hash):
        return False

    # Mark verified + clear token fields
    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    db.add(user)
    db.commit()
    return True