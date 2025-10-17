"""
AI-powered endpoints for smart assistance features.

Includes:
- Category suggestions based on description, amount, and user history.

This version preserves the original API (schemas + route names) and augments
the logic with an optional LLM fallback behind a feature flag.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.ml_category_map import MLCategoryMap
from app.schemas.ai import SuggestReq, SuggestResp, CategoryFeedbackReq, MessageOut
from app.core.config import settings
from app.core.ai_client import ai_client  # optional provider; disabled unless flagged

router = APIRouter(prefix="/ai", tags=["AI"])


# --- Helper: normalize text (for matching keywords etc.) ---
def norm_key(s: str) -> str:
    return " ".join((s or "").lower().strip().split())

def norm_cat(s: str) -> str:
    return " ".join((s or "").lower().strip().split())


@router.post("/suggest-category", response_model=SuggestResp)
def suggest_category(
    payload: SuggestReq,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Suggest a category for a new expense based on description, amount, and user history.

    Priority:
      1) User memory (MLCategoryMap.key -> category)
      2) LLM suggestion (if enabled)
      3) Keyword rules
      4) Most frequent category fallback

    Returns a SuggestResp with suggested_category, confidence, rationale.
    """
    desc = norm_key(payload.description)
    if not desc:
        return {"suggested_category": None, "confidence": 0.0, "rationale": "Empty description"}

    # 1) Personal memory (your existing table: MLCategoryMap with fields 'key' and 'category')
    memory = (
        db.query(MLCategoryMap)
        .filter(MLCategoryMap.user_id == user.id,
                MLCategoryMap.pattern == desc)
        .first()
    )
    if memory and memory.category:
        return {
            "suggested_category": memory.category,
            "confidence": 0.95,
            "rationale": "Based on your past choice",
        }

    # 2) Optional LLM (feature-flagged; off by default)
    #    We keep the schema/response EXACTLY as already defined.
    if settings.ai_category_suggestion_enabled and ai_client.enabled():
        user_prompt = (
            f"Transaction text: {payload.description}\n"
            + (f"Amount: {payload.amount}\n" if payload.amount is not None else "")
            + "Respond with ONLY the category word/phrase."
        )
        llm_cat = ai_client.complete(
            system_prompt=(
                "You classify personal finance transactions into short, simple categories "
                "(e.g., groceries, rent, utilities, transport, dining, entertainment, salary, refund). "
                "Return only the category text, no explanations."
            ),
            user_prompt=user_prompt,
        )
        if llm_cat:
            cat = norm_key(llm_cat)
            if cat:
                return {
                    "suggested_category": cat,
                    "confidence": 0.85,
                    "rationale": "AI suggestion",
                }

    # 3) Keyword rules (fallback)
    RULES = {
        "uber lyft bolt taxi cab ride": "transport",
        "aldi lidl tesco market grocery supermarket": "groceries",
        "amazon ikea decathlon shop mall store": "shopping",
        "netflix spotify youtube prime disney hulu": "subscriptions",
        "pizza burger cafe restaurant bar pub dine": "restaurants",
        "electricity water gas utility internet phone": "utilities",
        "rent mortgage lease": "housing",
        "fuel petrol diesel shell bp station": "transport",
        "gym fitness membership": "health",
        "pharmacy medicine drug": "health",
    }

    for bag, cat in RULES.items():
        for token in bag.split():
            if token in desc:
                return {
                    "suggested_category": cat,
                    "confidence": 0.7,
                    "rationale": f"Matched keyword '{token}'",
                }

    # 4) Fallback: user's most frequent category (proper SQL count)
    row = (
        db.query(Expense.category, func.count(Expense.id).label("cnt"))
        .filter(Expense.user_id == user.id)
        .group_by(Expense.category)
        .order_by(func.count(Expense.id).desc())
        .first()
    )
    if row and row[0]:
        return {
            "suggested_category": row[0],
            "confidence": 0.4,
            "rationale": "Your most frequent category",
        }

    return {"suggested_category": None, "confidence": 0.0, "rationale": "No match found"}


@router.post("/category-feedback", response_model=MessageOut)
def category_feedback(
    payload: CategoryFeedbackReq,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Store/update a per-user mapping from normalized description to category.
    This helps improve future category suggestions.
    """
    desc = norm_key(payload.description)        # normalized description
    cat = norm_cat(payload.category)            # normalized category

    if not desc or not cat:
        raise HTTPException(status_code=400, detail="description and category are required")

    # Upsert into MLCategoryMap by (user_id, pattern)
    row = (
        db.query(MLCategoryMap)
          .filter(MLCategoryMap.user_id == user.id,
                  MLCategoryMap.pattern == desc)
          .first()
    )

    if row:
        row.category = cat
        # confidence counter, bump it here (optional)
        # if hasattr(row, "confidence_count") and row.confidence_count is not None:
        #     row.confidence_count += 1
        db.add(row)
    else:
        row = MLCategoryMap(user_id=user.id, pattern=desc, category=cat, source="feedback")
        db.add(row)

    db.commit()
    return {"msg": "Thanks! Your preference will improve future suggestions."}