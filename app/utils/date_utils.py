from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from typing import Tuple


def get_date_range(today: datetime, period: str) -> Tuple[datetime, datetime]:
    """
    Return the UTC start and end datetime for a given period.

    Supported values for `period`: 'weekly', 'monthly', 'yearly'.
    """
    period = period.strip().lower()
    today = today.astimezone(timezone.utc)

    if period == "weekly":
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = start_date + timedelta(days=6)
    elif period == "monthly":
        start_date = today.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        raise ValueError(f"Invalid period '{period}'. Use: 'weekly', 'monthly', or 'yearly'.")

    # Normalize both to UTC start/end of day
    start_utc = datetime.combine(start_date.date(), datetime.min.time(), tzinfo=timezone.utc)
    end_utc = datetime.combine(end_date.date(), datetime.max.time(), tzinfo=timezone.utc)

    return start_utc, end_utc