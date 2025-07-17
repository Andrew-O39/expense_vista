from pydantic import BaseModel
from datetime import datetime


class AlertLogSchema(BaseModel):
    """
    Schema used to return alert log entries to the user.
    """
    id: int
    category: str | None = None  # Budget category (if any)
    type: str  # Alert type (e.g., 'limit_exceeded', '80_percent', etc.)
    date_sent: datetime  # When the alert was generated
    notes: str | None = None  # Optional description or extra info

    class Config:
        orm_mode = True  # Tells Pydantic to work well with SQLAlchemy models