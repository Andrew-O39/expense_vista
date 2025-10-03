from pydantic import BaseModel, EmailStr, Field

class PasswordChangeReq(BaseModel):
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)