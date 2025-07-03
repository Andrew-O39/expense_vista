"""
CRUD operations for the User model.
Handles creation and retrieval of users, primarily for registration and authentication workflows.
"""

from sqlalchemy.orm import Session
from expense_tracker.app.db.models.user import User
from expense_tracker.app.schemas.user import UserCreate
from expense_tracker.app.core.security import get_password_hash

# ------------------------------
# Create a new user
# ------------------------------
def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user in the database.

    Hashes the user's password before storing it securely in the 'users' table.

    Args:
        db (Session): SQLAlchemy database session.
        user (UserCreate): User creation schema with username, email, and raw password.

    Returns:
        User: The created user instance.
    """
    # Hash the plain password
    hashed_password = get_password_hash(user.password)

    # Create a new User instance
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    # Add the user to the session and commit
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

# ------------------------------
# Get user by username
# ------------------------------
def get_user_by_username(db: Session, username: str) -> User | None:
    """
    Retrieve a user by their username.

    Args:
        db (Session): SQLAlchemy session.
        username (str): Username to look up.

    Returns:
        User or None
    """
    return db.query(User).filter(User.username == username).first()


# ------------------------------
# Get user by email
# ------------------------------
def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Retrieve a user by their email.

    Args:
        db (Session): SQLAlchemy session.
        email (str): Email address to look up.

    Returns:
        User or None
    """
    return db.query(User).filter(User.email == email).first()


# ------------------------------
# Get user by ID (e.g., from token)
# ------------------------------
def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    Retrieve a user by their ID (useful for token decoding).

    Args:
        db (Session): SQLAlchemy session.
        user_id (int): User ID to look up.

    Returns:
        User or None
    """
    return db.query(User).filter(User.id == user_id).first()