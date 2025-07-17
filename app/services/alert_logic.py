from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.budget import Budget
from app.db.models.expense import Expense
from app.db.models.alert_log import AlertLog
from app.utils.date_utils import get_date_range

# Alert thresholds before exceeding budget
HALF_LIMIT_THRESHOLD = 0.5   # 50%
NEAR_LIMIT_THRESHOLD = 0.8   # 80%

def check_budget_alerts(user_id: int, db: Session):
    """
    Checks user's expenses against each of their budgets and triggers alerts:
    - 50% used → 'half_limit'
    - 80% used → 'near_limit'
    - >100% used → 'limit_exceeded'
    For each budget (e.g. weekly, monthly), the total expenses are compared
    against the limit. Alerts are triggered appropriately.

    Args:
        user_id (int): The user's ID.
        db (Session): SQLAlchemy DB session.
    """
    today = datetime.utcnow()
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

    for budget in budgets:
        try:
            start_date, end_date = get_date_range(today, budget.period)
        except ValueError as e:
            print(f"Skipping budget with invalid period: {e}")
            continue

        total_spent = (
            db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                Expense.category == budget.category,
                Expense.timestamp >= start_date,
                Expense.timestamp <= end_date
            )
            .scalar() or 0.0
        )

        # Trigger only the highest severity alert applicable
        if total_spent > budget.limit_amount:
            trigger_alert(user_id, budget, total_spent, db, alert_type="limit_exceeded")
        elif total_spent >= NEAR_LIMIT_THRESHOLD * budget.limit_amount:
            trigger_alert(user_id, budget, total_spent, db, alert_type="near_limit")
        elif total_spent >= HALF_LIMIT_THRESHOLD * budget.limit_amount:
            trigger_alert(user_id, budget, total_spent, db, alert_type="half_limit")


def trigger_alert(user_id: int, budget: Budget, spent: float, db: Session, alert_type: str):
    """
    Logs an alert when budget usage crosses a predefined threshold.

    Args:
        user_id (int): The user's ID.
        budget (Budget): The budget that was evaluated.
        spent (float): The total spent in the time window.
        db (Session): SQLAlchemy DB session.
        alert_type (str): Either "limit_exceeded", "near_limit" or "half_limit".
    """
    messages = {
        "limit_exceeded": "🚨 Budget EXCEEDED",
        "near_limit": "⚠️ Nearing budget",
        "half_limit": "📢 50% budget usage"
    }

    message = messages.get(alert_type, "ℹ️ Unknown alert")
    print(
        f"[ALERT] {message} for user {user_id}, category '{budget.category}' "
        f"({budget.period}) → Limit: {budget.limit_amount}, Spent: {spent}"
    )

    # Save to AlertLog table
    new_alert = AlertLog(
        user_id=user_id,
        category=budget.category,
        type=alert_type,
        date_sent=datetime.utcnow(),
    )
    db.add(new_alert)
    db.commit()