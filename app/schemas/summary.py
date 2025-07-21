from typing import Dict, Optional
from pydantic import BaseModel

class SingleCategorySummary(BaseModel):
    period: str
    category: str
    total_spent: float

class MultiCategorySummary(BaseModel):
    period: str
    summary: Dict[str, float]