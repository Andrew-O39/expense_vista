from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import user as crud_user
from app.db.models.user import User
from app.core.config import settings

# Tell FastAPI where to expect the token (Authorization header)
# Keep the same tokenUrl you already use
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# NEW: optional scheme that won't raise if the header is missing
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Extract and return the current user based on the JWT access token.
    Raises 401 if invalid or not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Are you logged in?",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud_user.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Return the current user if a valid Bearer token is provided.
    If no token (or invalid), return None instead of raising.
    Perfect for routes like /resend-verification that allow either:
      - logged-in user (no email query needed), or
      - anonymous user providing ?email=...
    """
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int | None = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    return crud_user.get_user_by_id(db, user_id=user_id)