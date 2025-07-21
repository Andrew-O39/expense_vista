from sqlalchemy.orm import Session
from typing import Optional, Dict
from datetime import datetime

from app.db.models.expense import Expense
from app.utils.date_utils import get_date_range


def get_spending_summary(
        db: Session,
        user_id: int,
        period: str,
        category: Optional[str] = None
) -> Dict:
    """
    Returns a summary of spending for a user during a given period.

    If a category is provided, returns total spent in that category.
    If no category is provided, returns a breakdown of all categories.

    Args:
        db (Session): SQLAlchemy database session
        user_id (int): ID of the user
        period (str): 'weekly', 'monthly', or 'yearly'
        category (Optional[str]): Optional category to filter by

    Returns:
        dict: A summary dictionary. Example:
              - Single category: {"category": "Food", "total_spent": 120.0, "period": "monthly"}
              - All categories: {"period": "monthly", "summary": {"Food": 120.0, "Transport": 45.0}}
    """
    today = datetime.utcnow()
    start_date, end_date = get_date_range(today, period)

    query = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start_date,
        Expense.created_at <= end_date
    )

    if category:
        query = query.filter(Expense.category == category)
        total = sum(exp.amount for exp in query.all())
        return {
            "category": category,
            "total_spent": round(total, 2),
            "period": period
        }
    else:
        summary = {}
        expenses = query.all()
        for exp in expenses:
            summary.setdefault(exp.category, 0.0)
            summary[exp.category] += exp.amount
        return {
            "period": period,
            "summary": {cat: round(amount, 2) for cat, amount in summary.items()}
        }