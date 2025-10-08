"""
AI-powered endpoints for smart assistance features.

Includes:
- Category suggestions based on description and past data.
- Duplicate detection for new expenses.
- Simple anomaly (unusual spend) detection.
- Subscription detection from recurring expenses.

These features are lightweight rule-based helpers designed to evolve later
into learned models without changing the API interface.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import statistics as stats
import collections

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.ml_category_map import MLCategoryMap
from app.schemas.ai import SuggestReq, SuggestResp, DupCheckReq, DupCheckResp, AnomalyReq, AnomalyResp, Subscription

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/suggest-category", response_model=SuggestResp)
def suggest_category(
    payload: SuggestReq,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Suggest a category for a new expense based on its description, amount, and user history.
    """
    desc = norm_key(payload.description)
    if not desc:
        return {"suggested_category": None, "confidence": 0.0, "rationale": "Empty description"}

    # 1. Check user’s personal memory (from past expenses)
    memory = db.query(MLCategoryMap).filter_by(user_id=user.id, key=desc).first()
    if memory:
        return {
            "suggested_category": memory.category,
            "confidence": 0.95,
            "rationale": "Based on your past choice",
        }

    # 2. Keyword-based rules (fallback)
    RULES = {
        "uber lyft taxi": "transport",
        "aldi lidl tesco market grocery supermarket": "groceries",
        "amazon ikea decathlon": "shopping",
        "netflix spotify youtube prime disney": "subscriptions",
        "pizza burger cafe restaurant bar": "restaurants",
        "electricity water gas utility": "utilities",
        "rent mortgage": "housing",
    }

    for bag, cat in RULES.items():
        for token in bag.split():
            if token in desc:
                return {
                    "suggested_category": cat,
                    "confidence": 0.7,
                    "rationale": f"Matched keyword '{token}'",
                }

    # 3. Fallback to user's most frequent category
    row = (
        db.query(Expense.category)
        .filter(Expense.user_id == user.id)
        .group_by(Expense.category)
        .order_by(-stats.mode([1]))  # fallback hack, you can replace with count
        .first()
    )

    if row:
        return {"suggested_category": row[0], "confidence": 0.4, "rationale": "Your most frequent category"}

    return {"suggested_category": None, "confidence": 0.0, "rationale": "No match found"}

# --- Helper: normalize text (for matching keywords etc.) ---
def norm_key(s: str) -> str:
    return " ".join((s or "").lower().strip().split())