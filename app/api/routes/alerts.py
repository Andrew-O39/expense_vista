from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models.alert_log import AlertLog
from app.db.models.user import User
from app.schemas.alert_log import AlertLogSchema
from app.api.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertLogSchema])
def read_alerts(
    skip: int = Query(0, ge=0, description="Number of alerts to skip (for pagination)"),
    limit: int = Query(20, le=100, description="Max number of alerts to return (max 100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a list of budget alert logs for the authenticated user, sorted by most recent.

    This endpoint supports pagination using `skip` and `limit`.
    """
    alerts = (
        db.query(AlertLog)
        .filter(AlertLog.user_id == current_user.id)
        .order_by(AlertLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return alerts