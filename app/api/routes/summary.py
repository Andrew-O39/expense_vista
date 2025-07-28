from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Union
from datetime import datetime, timezone

from app.api.deps import get_current_user
from app.db.session import get_db
from app.utils.date_utils import get_date_range
from app.schemas.summary import SingleCategorySummary, MultiCategorySummary
from app.db.models.user import User
from app.db.models.expense import Expense


router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get("/summary", response_model=Union[SingleCategorySummary, MultiCategorySummary])
def get_spending_summary(
    period: str = Query(..., description="Time period to summarize ('weekly', 'monthly', or 'yearly')"),
    category: Optional[str] = Query(None, description="Optional category to filter by"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a summary of user spending for a given time period.

    - If a `category` is provided, returns the total spent in that category during the specified period.
    - If `category` is not provided, returns total spending grouped by category for that period.

    Examples:
    - `/summary/summary?period=monthly` → multi-category summary
    - `/summary/summary?period=monthly&category=groceries` → single-category summary
    """
    start_date, end_date = get_date_range(datetime.now(timezone.utc), period)

    if category:
        normalized_category = category.strip().lower()

        total_spent = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            func.lower(Expense.category) == normalized_category,
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).scalar() or 0.0

        return SingleCategorySummary(
            period=period,
            category=normalized_category,
            total_spent=total_spent
        )

    else:
        results = db.query(
            Expense.category,
            func.sum(Expense.amount)
        ).filter(
            Expense.user_id == current_user.id,
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).group_by(Expense.category).all()

        summary_data = {cat: float(total or 0.0) for cat, total in results}

        return MultiCategorySummary(
            period=period,
            summary=summary_data
        )