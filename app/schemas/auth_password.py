from pydantic import BaseModel, EmailStr, Field


class PasswordChangeReq(BaseModel):
    """
    Schema for authenticated users changing their password in-app.
    """
    old_password: str = Field(min_length=8, description="The user's current password.")
    new_password: str = Field(min_length=8, description="The new password to be set.")


class PasswordResetRequest(BaseModel):
    """
    Schema for requesting a password reset via email.
    """
    email: EmailStr = Field(..., description="The registered email address of the user.")


class PasswordResetConfirm(BaseModel):
    """
    Schema for confirming and completing a password reset using a token.
    """
    token: str = Field(..., description="The one-time secure reset token sent via email.")
    new_password: str = Field(min_length=8, description="The new password chosen by the user.")