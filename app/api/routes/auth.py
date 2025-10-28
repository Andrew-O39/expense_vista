from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Optional

from jinja2 import Template
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.db.session import get_db
from app.crud import user as crud_user
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.api.deps import get_current_user, get_current_user_optional
from app.db.models.user import User
from app.db.models.password_reset import PasswordResetToken

# Schemas
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth_email import ResendVerificationIn, VerifyTokenIn
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
    if not tmpl_path.exists():
        return f"""
        <html><body>
          <p>Hi {username},</p>
          <p>Please verify your email: <a href="{verify_url}">Verify</a></p>
          <p>This link expires in {ttl_hours} hours.</p>
        </body></html>
        """.strip()

    return Template(tmpl_path.read_text(encoding="utf-8")).render(
        username=username,
        verify_url=verify_url,
        expires_hours=ttl_hours,
        current_year=datetime.now().year,
    )


def _send_verification_email(user: User, db: Session, ttl_hours: int = 24) -> None:
    """
    Create a one-time verification token (store HASH+expiry on the user),
    compose the verification URL, and send it via SES.
    """
    # Create a fresh token and store only the hash
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

    user.verification_token_hash = token_hash
    user.verification_token_expires_at = expires_at
    db.add(user)
    db.commit()

    # Link that your frontend will hit to call /verify-email?token=...
    verify_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw_token}"

    html = _render_verify_email(user.username, verify_url, ttl_hours=ttl_hours)

    try:
        send_alert_email(
            to_email=user.email,
            subject="Verify your ExpenseVista email",
            html_content=html,
        )
    except Exception:
        # Don't crash signup flows if email provider hiccups
        pass


@router.post("/verify-email", response_model=MessageOut)
def verify_email_post(
    payload: VerifyTokenIn,
    db: Session = Depends(get_db),
):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    user = (
        db.query(User)
        .filter(User.verification_token_hash == token_hash)
        .first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if not user.verification_token_expires_at or user.verification_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")

    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    db.add(user)
    db.commit()

    return {"msg": "Email verified successfully. You can now sign in."}

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

    # ⛔ Block login until email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox (or request a new verification link).",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# -------------------------
# Register
# -------------------------
# app/api/routes/auth.py  (register route)

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    # Uniqueness checks
    if crud_user.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username is already in use")
    if crud_user.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email is already in use")

    # Create user (is_verified defaults to False)
    created = crud_user.create_user(db, user)

    # Issue verification token (hash only) and send email
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    created.verification_token_hash = token_hash
    created.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(created)
    db.commit()

    verify_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw}"
    html = _render_verify_email(
        username=created.username,
        verify_url=verify_url,
        ttl_hours=24,
    )

    try:
        ok = send_alert_email(
            to_email=created.email,
            subject="Verify your ExpenseVista email",
            html_content=html,
        )
        print(f"[VERIFY EMAIL] sent={ok} to={created.email} url={verify_url}")
    except Exception as e:
        print(f"[VERIFY EMAIL ERROR] {e}")

    return created

# -------------------------
# Resend Verification
# -------------------------
@router.post("/resend-verification", response_model=MessageOut)
def resend_verification(
    payload: Optional[ResendVerificationIn] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    user: Optional[User] = None

    if current_user:
        user = current_user
    else:
        email = (payload.email if payload else None)
        if not email:
            raise HTTPException(status_code=422, detail="Email is required when not authenticated.")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don’t leak whether the email exists
            return {"msg": "If this email is registered, a verification message will be sent shortly."}

    if user.is_verified:
        return {"msg": "This email is already verified."}

    # New token
    raw = secrets.token_urlsafe(32)
    user.verification_token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(user)
    db.commit()

    verify_url = f"{settings.frontend_url.rstrip('/')}/verify-email?token={raw}"
    html = _render_verify_email(user.username, verify_url, 24)

    try:
        ok = send_alert_email(user.email, "Verify your ExpenseVista email", html)
        print(f"[RESEND VERIFY] sent={ok} to={user.email} url={verify_url}")
    except Exception as e:
        print(f"[RESEND VERIFY ERROR] {e}")

    return {"msg": "If this email is registered, a verification message will be sent shortly."}


@router.post("/resend-verification/me", response_model=MessageOut)
def resend_verification_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_verified:
        return {"msg": "Your email is already verified."}

    try:
        _send_verification_email(current_user, db, ttl_hours=24)
    except Exception:
        pass

    return {"msg": "Verification email sent."}


@router.get("/verify-email", response_model=MessageOut)
def verify_email(
    token: str = Query(..., min_length=8),
    db: Session = Depends(get_db),
):
    """
    Verify a user's email given a token from the email link.
    """
    # Hash the incoming token and look up a user
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    user = (
        db.query(User)
        .filter(User.verification_token_hash == token_hash)
        .first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if not user.verification_token_expires_at or user.verification_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")

    # Mark as verified and burn the token
    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    db.add(user)
    db.commit()

    return {"msg": "Email verified successfully. You can now sign in."}

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