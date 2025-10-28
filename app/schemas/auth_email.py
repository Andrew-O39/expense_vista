from typing import Optional
from pydantic import BaseModel, EmailStr

class ResendVerificationIn(BaseModel):
    email: Optional[EmailStr] = None

class VerifyTokenIn(BaseModel):
    token: str