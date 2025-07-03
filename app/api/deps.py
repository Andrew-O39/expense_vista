from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from expense_tracker.app.db.session import get_db
from expense_tracker.app.crud import user as crud_user
from expense_tracker.app.db.models.user import User
from expense_tracker.app.core.config import settings

# Tell FastAPI where to expect the token (Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Extract and return the current user based on the JWT access token.

    Raises:
        HTTPException: If the token is invalid or the user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Are you logged in?",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Fetch the user from DB
    user = crud_user.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return user