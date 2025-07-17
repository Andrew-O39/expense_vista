from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.models.budget import Budget
from app.db.models.expense import Expense
from app.db.models.alert_log import AlertLog
from app.utils.date_utils import get_date_range

# Alert thresholds
HALF_LIMIT_THRESHOLD = 0.5   # 50%
NEAR_LIMIT_THRESHOLD = 0.8   # 80%

def check_budget_alerts(user_id: int, db: Session):
    """
    Checks user expenses against budgets and triggers alerts if usage crosses:
    - 50%: 'half_limit'
    - 80%: 'near_limit'
    - >100%: 'limit_exceeded'
    """
    today = datetime.utcnow()
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

    for budget in budgets:
        if budget.period.lower() == "unknown":
            print(f"Skipping budget with 'unknown' period (category: {budget.category})")
            continue

        try:
            start_date, end_date = get_date_range(today, budget.period)
        except ValueError as e:
            print(f"Skipping budget with invalid period: {e}")
            continue

        total_spent = (
            db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                Expense.category == budget.category,  # Assumes both are normalized
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
            .scalar() or 0.0
        )

        # Decide which alert to trigger (highest severity only)
        alert_type = None
        if total_spent > budget.limit_amount:
            alert_type = "limit_exceeded"
        elif total_spent >= NEAR_LIMIT_THRESHOLD * budget.limit_amount:
            alert_type = "near_limit"
        elif total_spent >= HALF_LIMIT_THRESHOLD * budget.limit_amount:
            alert_type = "half_limit"

        if alert_type:
            trigger_alert(user_id, budget, total_spent, db, alert_type)


def trigger_alert(user_id: int, budget: Budget, spent: float, db: Session, alert_type: str):
    """
    Logs an alert (if not already triggered) for this budget cycle.
    """
    # Prevent duplicate alert for same budget/period/type
    existing_alert = db.query(AlertLog).filter(
        and_(
            AlertLog.user_id == user_id,
            AlertLog.category == budget.category,
            AlertLog.period == budget.period,
            AlertLog.type == alert_type
        )
    ).first()

    if existing_alert:
        return  # Alert already triggered previously

    messages = {
        "limit_exceeded": "🚨 Budget EXCEEDED",
        "near_limit": "⚠️ Nearing budget",
        "half_limit": "📢 50% budget usage"
    }

    print(
        f"[ALERT] {messages.get(alert_type, 'ℹ️ Alert')} for user {user_id}, "
        f"category '{budget.category}' ({budget.period}) → "
        f"Limit: {budget.limit_amount}, Spent: {spent}"
    )

    new_alert = AlertLog(
        user_id=user_id,
        category=budget.category,
        period=budget.period,
        type=alert_type,
        notes=f"Spent {spent} of {budget.limit_amount} in {budget.period} budget for '{budget.category}'"
    )
    db.add(new_alert)
    db.commit()