from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AlertLogSchema(BaseModel):
    """
    Schema for returning alert log entries in API responses.
    """
    id: int = Field(..., description="Unique identifier for the alert log entry.")
    category: Optional[str] = Field(None, example="groceries", description="Category associated with the alert (if any).")
    period: str = Field(..., description="Period over which the budget was monitored. Common values: 'weekly', 'monthly', 'yearly'.")
    type: str = Field(..., description="Type of alert that was triggered (e.g., 'limit_exceeded', 'half_limit', etc.).")
    created_at: datetime = Field(..., description="Timestamp when the alert was generated.")
    notes: Optional[str] = Field(None, example="Budget exceeded by $25", description="Optional descriptive note for the alert.")

    class Config:
        orm_mode = True