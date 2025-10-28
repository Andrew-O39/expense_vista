from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from jinja2 import Template
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.db.session import get_db
from app.crud import user as crud_user
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.models.password_reset import PasswordResetToken

# Schemas
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserOut
from app.schemas.common import MessageOut  # simple {"msg": "..."} schema
from app.schemas.auth_password import (
    PasswordResetRequest,
    PasswordResetConfirm,
)

# Email
from app.utils.email_sender import send_alert_email  # SES sender

router = APIRouter(tags=["Authentication"])

def _render_verify_email(username: str, verify_url: str, ttl_hours: int = 24) -> str:
    tmpl_path = Path(__file__).resolve().parents[2] / "templates" / "email_verify.html"
    if tmpl_path.exists():
        html = Template(tmpl_path.read_text(encoding="utf-8")).render(
            user_name=username,
            verify_url=verify_url,
            ttl_hours=ttl_hours,
        )
    else:
        # Minimal fallback (no template file)
        html = f"""
        <html><body style="font-family: sans-serif">
          <h2>Verify your email</h2>
          <p>Hi {username},</p>
          <p>Please verify your email to activate your ExpenseVista account.</p>
          <p><a href="{verify_url}">Verify Email</a></p>
          <p>This link expires in {ttl_hours} hours.</p>
        </body></html>
        """
    return html


# -------------------------
# Login
# -------------------------
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Log in a user using username and password.
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


# -------------------------
# Register
# -------------------------
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account and send a verification email.
    """
    if crud_user.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username is already in use")
    if crud_user.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email is already in use")

    # Create the user (your existing logic)
    db_user = crud_user.create_user(db, user)

    # Issue a verification token (hash only is stored)
    raw_token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db_user.verification_token_hash = token_hash
    db_user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Build verification URL
    verify_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw_token}"

    # Send via SES
    try:
        html = _render_verify_email(db_user.username or db_user.email, verify_url, ttl_hours=24)
        send_alert_email(
            to_email=db_user.email,
            subject="Verify your email for ExpenseVista",
            html_content=html,
        )
    except Exception:
        # Don’t fail registration if email sending hiccups; user can /verify/resend
        pass

    return db_user

# -------------------------
# Resend Verification
# -------------------------
@router.post("/verify/resend", response_model=MessageOut)
def resend_verification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resend a verification email to the logged-in user (if not verified).
    Optional: add throttling if needed using the stored expiry.
    """
    if current_user.is_verified:
        return {"msg": "Your email is already verified."}

    # Optional throttling: only allow new token if < 60s since last issue, etc.
    raw_token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    current_user.verification_token_hash = token_hash
    current_user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    verify_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw_token}"

    try:
        html = _render_verify_email(current_user.username or current_user.email, verify_url, ttl_hours=24)
        ok = send_alert_email(
            to_email=current_user.email,
            subject="Verify your email for ExpenseVista",
            html_content=html,
        )
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to send verification email.")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send verification email.")

    return {"msg": "Verification email sent."}

@router.get("/verify", response_model=MessageOut)
def verify_email(
    token: str = Query(..., description="Email verification token from the email link"),
    db: Session = Depends(get_db),
):
    """
    Verify a user's email given a token from the email link.
    """
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    user = (
        db.query(User)
        .filter(User.verification_token_hash == token_hash)
        .first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    # Check expiry and status
    now = datetime.now(timezone.utc)
    if user.is_verified:
        return {"msg": "Email already verified."}
    if not user.verification_token_expires_at or user.verification_token_expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    # Mark verified and clear token fields
    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    db.add(user)
    db.commit()

    return {"msg": "Email verified successfully."}

# -------------------------
# Me
# -------------------------
@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Get the currently authenticated user's information.
    """
    return current_user


# -------------------------
# Password Reset: Request
# -------------------------
@router.post(
    "/forgot-password",
    response_model=MessageOut,
    summary="Request a password reset link",
)


def forgot_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Accepts an email and (if a user exists) creates a one-time reset token
    and emails a reset link. Always returns 200 to avoid email enumeration.
    """
    # Normalize email
    email: EmailStr = payload.email

    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        return {"msg": "If this email is registered, you will receive a reset link shortly."}

    # Generate secure token and store HASH only
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_expire_minutes
    )

    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False,
    )
    db.add(prt)
    db.commit()

    # Build reset URL for frontend
    reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"

    # Load template file
    template_path = Path(__file__).resolve().parents[2] / "templates" / "password_reset.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Render the template with context
    html = Template(template_path.read_text(encoding="utf-8")).render(
        username=user.username,
        reset_url=reset_url,
        year=datetime.now().year,
        expiry_minutes=settings.password_reset_expire_minutes,
    )

    try:
        send_alert_email(
            to_email=user.email,
            subject="Reset your ExpenseVista password",
            html_content=html,
        )
    except Exception:
        pass

    return {"msg": "If this email is registered, you will receive a reset link shortly."}


# -------------------------
# Password Reset: Confirm
# -------------------------
@router.post(
    "/reset-password",
    response_model=MessageOut,
    summary="Reset password using a token",
)
def reset_password(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Confirms a password reset using the provided token and new password.
    """
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()

    prt = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,  # noqa: E712
        )
        .first()
    )
    if not prt:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Check expiry
    if prt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")

    # Find user
    user = db.query(User).get(prt.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    # Update password
    user.hashed_password = get_password_hash(payload.new_password)
    db.add(user)

    # Burn token
    prt.used = True
    db.add(prt)

    db.commit()

    return {"msg": "Password has been reset successfully."}