"""
Security utilities for password hashing and JWT-based access tokens.

Handles:
- Secure password storage using bcrypt.
- Token generation using JWT.
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

from app.core.config import settings

# Config values loaded from env variables
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


# Password hashing context (uses bcrypt algorithm)
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


# -----------------------------
# Hash plain-text password
# -----------------------------
def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password for safe storage.

    Uses bcrypt algorithm.
    """
    return pwd_context.hash(password)


# -----------------------------
# Verify a password
# -----------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against the hashed version stored in the DB.
    """
    return pwd_context.verify(plain_password, hashed_password)


# -----------------------------
# Create a JWT access token
# -----------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT token with optional expiration.

    Args:
        data (dict): Data to encode in the token (e.g., user ID).
        expires_delta (timedelta, optional): Token lifetime.

    Returns:
        str: JWT access token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    # Sign and encode the JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt