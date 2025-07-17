from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Tuple


def get_date_range(today: datetime, period: str) -> Tuple[datetime, datetime]:
    """
    Returns the start and end date for a given period.
    Supported periods: 'weekly', 'monthly', 'yearly'
    """
    if period == "weekly":
        start = today - timedelta(days=today.weekday())  # Monday
        end = start + timedelta(days=6)  # Sunday
    elif period == "monthly":
        start = today.replace(day=1)
        end = (start + relativedelta(months=1)) - timedelta(days=1)
    elif period == "yearly":
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
    else:
        raise ValueError(f"Unknown period type: '{period}'")

    return start, end