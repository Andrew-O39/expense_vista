from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertLogSchema(BaseModel):
    """
    Schema used to return alert log entries to the user.
    """
    id: int
    category: Optional[str] = None  # Budget category (if any)
    period: str  # 'weekly', 'monthly', 'yearly'
    type: str  # Alert type (e.g., 'limit_exceeded', etc.)
    created_at: datetime  # When the alert was generated
    notes: Optional[str] = None  # Optional description or extra info

    class Config:
        orm_mode = True