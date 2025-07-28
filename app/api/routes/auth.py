from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud import user as crud_user
from app.core.security import verify_password, create_access_token
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserOut
from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Log in a user using username and password.

    Returns:
        A JWT access token if credentials are valid.
    """
    user = crud_user.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.

    Ensures the username and email are unique, and stores the user with a hashed password.
    """
    if crud_user.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username is already in use")

    if crud_user.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email is already in use")

    return crud_user.create_user(db, user)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Get the currently authenticated user's information.

    Requires a valid JWT access token.
    """
    return current_user
