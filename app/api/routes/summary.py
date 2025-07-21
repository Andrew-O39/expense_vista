from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Union
from datetime import datetime, timezone

from app.api.deps import get_current_user
from app.db.session import get_db
from app.services.summary_service import get_spending_summary
from app.utils.date_utils import get_date_range
from app.schemas.summary import SingleCategorySummary, MultiCategorySummary
from app.db.models.user import User
from app.db.models.expense import Expense


router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get("/summary", response_model=Union[SingleCategorySummary, MultiCategorySummary])
def get_spending_summary(
    period: str = Query(..., description="Summary period (e.g., 'monthly', 'weekly', 'yearly')"),
    category: Optional[str] = Query(None, description="Optional category to filter by"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a summary of user's spending over a specified period.
    Optionally filter by category.
    """
    start_date, end_date = get_date_range(datetime.now(timezone.utc), period)

    if category:
        normalized_category = category.strip().lower()

        total = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            func.lower(Expense.category) == normalized_category,  # normalize in query
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).scalar() or 0.0

        return {
            "period": period,
            "category": normalized_category,
            "total_spent": total
        }

    else:
        results = db.query(
            Expense.category,
            func.sum(Expense.amount)
        ).filter(
            Expense.user_id == current_user.id,
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).group_by(Expense.category).all()

        summary = {category: float(total or 0.0) for category, total in results}

        return {
            "period": period,
            "summary": summary
        }