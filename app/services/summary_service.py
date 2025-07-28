from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Union
from datetime import datetime

from app.db.models.expense import Expense
from app.utils.date_utils import get_date_range


def get_spending_summary(
    db: Session,
    user_id: int,
    period: str,
    category: Optional[str] = None
) -> Dict[str, Union[str, float, Dict[str, float]]]:
    """
    Get total spending for a user in a given period.

    - With a category: returns {"category", "total_spent", "period"}
    - Without a category: returns {"period", "summary": {category: amount}}

    Args:
        db: Database session
        user_id: ID of the user
        period: 'weekly', 'monthly', or 'yearly'
        category: Optional category filter

    Returns:
        dict: Spending summary
    """
    today = datetime.utcnow()
    start_date, end_date = get_date_range(today, period)

    query = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start_date,
        Expense.created_at <= end_date
    )

    if category:
        normalized_category = category.strip().lower()
        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user_id,
                Expense.category == normalized_category,
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
            .scalar()
        )
        return {
            "category": normalized_category,
            "total_spent": round(total, 2),
            "period": period
        }

    else:
        results = (
            db.query(Expense.category, func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user_id,
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
            .group_by(Expense.category)
            .all()
        )

        summary = {category: round(amount, 2) for category, amount in results}
        return {
            "period": period,
            "summary": summary
        }