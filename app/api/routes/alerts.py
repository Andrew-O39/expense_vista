from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models.alert_log import AlertLog
from app.db.models.user import User
from app.schemas.alert_log import AlertLogSchema
from app.api.deps import get_current_user


router = APIRouter(prefix="", tags=["Alerts"])


@router.get("/alerts/", response_model=List[AlertLogSchema], tags=["Alerts"])
def read_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve a list of alerts for the current authenticated user.

    Alerts are sorted by `date_sent` in descending order (most recent first).

    Returns:
        A list of alerts triggered for the user's budgets.
    """
    alerts = (
        db.query(AlertLog)
        .filter(AlertLog.user_id == current_user.id)
        .order_by(AlertLog.date_sent.desc())
        .all()
    )
    return alerts
