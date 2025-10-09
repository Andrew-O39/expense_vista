"""
Schemas for AI-powered features such as:
- Category suggestion
- Duplicate detection
- Anomaly (unusual spend) checks
- Subscription detection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# ---------- CATEGORY SUGGESTION ----------

class SuggestReq(BaseModel):
    """Request model for suggesting a category based on expense description."""
    description: str = Field(..., example="Uber ride to airport")
    amount: Optional[float] = Field(None, example=25.5)


class SuggestResp(BaseModel):
    """Response model containing the suggested category and confidence score."""
    suggested_category: Optional[str] = Field(None, example="transport")
    confidence: float = Field(..., ge=0, le=1, example=0.87)
    rationale: Optional[str] = Field(None, example="Matched keyword 'uber'")


# ---------- DUPLICATE DETECTION ----------

class DupCheckReq(BaseModel):
    """Request model to check if a similar expense already exists."""
    description: str
    amount: float
    created_at: Optional[str] = None


class DupMatch(BaseModel):
    """Represents a possible duplicate expense."""
    id: int
    description: str
    amount: float
    created_at: str


class DupCheckResp(BaseModel):
    """Response containing a list of possible duplicates."""
    possible_duplicates: List[DupMatch]


# ---------- ANOMALY DETECTION ----------

class AnomalyReq(BaseModel):
    """Request model to check if an expense amount is unusually high."""
    category: str
    amount: float


class AnomalyResp(BaseModel):
    """Response showing anomaly analysis."""
    is_unusual: bool
    threshold: float
    mean: float
    std: float
    window_months: int = 6


# ---------- SUBSCRIPTION DETECTION ----------

class Subscription(BaseModel):
    """Represents a detected recurring payment or subscription."""
    merchant: str
    avg_amount: float
    cadence: str
    last_seen: str
    evidence: int

class CategoryFeedbackReq(BaseModel):
    """User feedback to teach the model a mapping from description -> category."""
    description: str = Field(..., example="Uber ride to airport")
    category: str = Field(..., example="transport")

class MessageOut(BaseModel):
    msg: str