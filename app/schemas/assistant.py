from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AssistantMessage(BaseModel):
    message: str = Field(..., example="How much did I spend on groceries last month?")

class AssistantAction(BaseModel):
    type: str                                    # e.g. 'navigate', 'show_chart'
    label: Optional[str] = None                  # e.g. 'View details'
    params: Optional[Dict[str, Any]] = None      # e.g. {'period':'month','category':'groceries'}

class AssistantReply(BaseModel):
    reply: str
    actions: List[AssistantAction] = []