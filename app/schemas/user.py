"""
Pydantic schemas for the User model.

These schemas define how user data is validated and serialized:
- When received from the client (e.g., during registration or login)
- When returned to the client (excluding sensitive data like passwords)
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# ------------------------------
# Base schema with shared fields
# ------------------------------
class UserBase(BaseModel):
    """
    Shared fields for reading and writing user data.
    """
    username: str = Field(..., description="Unique username for the user", examples=["andrew_owusu"])
    email: EmailStr = Field(..., description="User's email address", examples=["andrew@example.com"])


# ------------------------------
# Schema for user creation
# ------------------------------
class UserCreate(UserBase):
    """
    Schema used when a new user is registering.
    Requires a plain-text password.
    """
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters", examples=["password123"])


# ------------------------------
# Schema used for login
# ------------------------------
class UserLogin(BaseModel):
    """
    Schema used during user login.
    """
    username: str = Field(..., description="Your username", examples=["andrew_owusu"])
    password: str = Field(..., description="Your password", examples=["password123"])


# ------------------------------
# Schema used for returning user info (safe)
# ------------------------------
class UserOut(UserBase):
    """
    Schema returned to the client after user registration or authentication.
    Excludes sensitive fields like hashed_password.
    """
    id: int = Field(..., description="User ID")

    class Config:
        orm_mode = True


# ------------------------------
# Internal schema for DB use (optional)
# ------------------------------
class UserInDB(UserBase):
    """
    Internal schema that includes hashed password.
    Useful for internal DB logic but not exposed to clients.
    """
    id: int
    hashed_password: str

    class Config:
        orm_mode = True