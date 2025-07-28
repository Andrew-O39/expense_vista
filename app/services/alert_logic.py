from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.models.budget import Budget
from app.db.models.expense import Expense
from app.db.models.alert_log import AlertLog
from app.utils.date_utils import get_date_range
from app.utils.email_sender import send_alert_email, render_alert_email
from app.db.models.user import User

import logging
logger = logging.getLogger(__name__)

# Alert thresholds
HALF_LIMIT_THRESHOLD = 0.5   # 50%
NEAR_LIMIT_THRESHOLD = 0.8   # 80%

ALERT_MESSAGES = {
    "limit_exceeded": "🚨 Budget EXCEEDED",
    "near_limit": "⚠️ Nearing budget",
    "half_limit": "📢 50% budget usage"
}


def check_budget_alerts(user_id: int, db: Session):
    """Checks if user's spending crosses 50%, 80%, or 100% thresholds and triggers alerts."""
    today = datetime.utcnow()
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"No user found with ID {user_id}")
        return

    for budget in budgets:
        if budget.period.lower() == "unknown":
            logger.info(f"Skipping 'unknown' period budget (category: {budget.category})")
            continue

        try:
            start_date, end_date = get_date_range(today, budget.period)
        except ValueError as e:
            logger.warning(f"Skipping invalid budget period for category {budget.category}: {e}")
            continue

        total_spent = (
            db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                Expense.category == budget.category,  # Assume already normalized
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
            .scalar() or 0.0
        )

        # Determine alert type
        alert_type = None
        if total_spent > budget.limit_amount:
            alert_type = "limit_exceeded"
        elif total_spent >= NEAR_LIMIT_THRESHOLD * budget.limit_amount:
            alert_type = "near_limit"
        elif total_spent >= HALF_LIMIT_THRESHOLD * budget.limit_amount:
            alert_type = "half_limit"

        if alert_type:
            trigger_alert(user, budget, total_spent, db, alert_type)


def trigger_alert(user: User, budget: Budget, spent: float, db: Session, alert_type: str):
    """Logs and sends a budget alert if it hasn't already been triggered."""
    existing_alert = db.query(AlertLog).filter(
        and_(
            AlertLog.user_id == user.id,
            AlertLog.category == budget.category,
            AlertLog.period == budget.period,
            AlertLog.type == alert_type
        )
    ).first()

    if existing_alert:
        return  # Avoid duplicate alerts

    alert_message = ALERT_MESSAGES.get(alert_type, "ℹ️ Budget Alert")
    logger.info(
        f"[ALERT] {alert_message} for user {user.id}, "
        f"category '{budget.category}' ({budget.period}) → "
        f"Limit: {budget.limit_amount}, Spent: {spent}"
    )

    # Log the alert in DB
    notes = (
        f"Spent {spent:.2f} of {budget.limit_amount:.2f} "
        f"in your {budget.period} budget for '{budget.category}'"
    )
    new_alert = AlertLog(
        user_id=user.id,
        category=budget.category,
        period=budget.period,
        type=alert_type,
        notes=notes
    )
    db.add(new_alert)
    db.commit()

    # Send alert email
    if user.email:
        subject = f"Budget Alert: {alert_message} - {budget.category} ({budget.period})"
        html_content = render_alert_email(
            user_name=user.username,
            category=budget.category,
            period=budget.period,
            total_spent=spent,
            limit=budget.limit_amount,
            alert_type=alert_type
        )
        send_alert_email(to_email=user.email, subject=subject, html_content=html_content)