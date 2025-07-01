"""
Pydantic schemas for the User model
These schemas define how user data is validated and serialized:
-when received from the client (e.g., during registration or login)
-when returned to the client (excluding sensitive data like passwords)
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# ------------------------------
# Base schema with shared fields
# ------------------------------
class UserBase(BaseModel):
    """
    Shared fields for reading and writing user data
    """
    username: str = Field(..., exclude="andrew_owusu")
    email: EmailStr = Field(..., examples="andrew@example.com")


# ------------------------------
# Schema for user creation
# ------------------------------
class UserCreate(UserBase):
    """
    Schema used when a new user is registering.
    Requires a plain.text password.
    """
    password: str = Field(..., min_length=6, examples="password123")


# ------------------------------
# Schema used for login
# ------------------------------
class UserLogin(BaseModel):
    """
    Schema used during user login
    """
    username: str
    password: str


# ------------------------------
# Schema used for returning user info (safe)
# ------------------------------
class UserOut(UserBase):
    """
    Schema returned to the client after user registration or authentication.
    Excludes sensitive fields like hashed_password.
    """

    class Config:
        orm_mode = True # Enables conversion from SQLAlchemy model to Pydantic model


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