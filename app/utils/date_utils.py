from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from typing import Tuple

ALLOWED_PERIODS = {"weekly", "monthly", "yearly", "quarterly", "half-yearly"}

def _quarter_bounds(dt: datetime) -> Tuple[datetime, datetime]:
    """Start/end (inclusive) of the quarter containing dt, UTC-day bounds."""
    dt = dt.astimezone(timezone.utc)
    q = (dt.month - 1) // 3               # 0..3
    start_month = q * 3 + 1               # 1,4,7,10
    start = dt.replace(month=start_month, day=1)
    end = (start + relativedelta(months=3)) - timedelta(days=1)
    return start, end

def _half_year_bounds(dt: datetime) -> Tuple[datetime, datetime]:
    """Start/end (inclusive) of the half-year containing dt, UTC-day bounds."""
    dt = dt.astimezone(timezone.utc)
    if dt.month <= 6:
        start = dt.replace(month=1, day=1)
        end   = dt.replace(month=6, day=30)
    else:
        start = dt.replace(month=7, day=1)
        end   = dt.replace(month=12, day=31)
    # Alternatively (more uniform), you can do:
    # start = dt.replace(month=1 if dt.month <= 6 else 7, day=1)
    # end   = (start + relativedelta(months=6)) - timedelta(days=1)
    return start, end

def get_date_range(today: datetime, period: str) -> Tuple[datetime, datetime]:
    """
    Returns start/end datetimes (UTC) for a given period.
    Supported: 'weekly', 'monthly', 'yearly', 'quarterly', 'half-yearly'
    """
    if not isinstance(period, str):
        raise ValueError("Period must be a string.")
    period = period.strip().lower()
    today = today.astimezone(timezone.utc)

    if period == "weekly":
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date   = start_date + timedelta(days=6)           # Sunday
    elif period == "monthly":
        start_date = today.replace(day=1)
        end_date   = (start_date + relativedelta(months=1)) - timedelta(days=1)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
        end_date   = today.replace(month=12, day=31)
    elif period == "quarterly":
        start_date, end_date = _quarter_bounds(today)
    elif period == "half-yearly":
        start_date, end_date = _half_year_bounds(today)
    else:
        raise ValueError(f"Unknown period type: '{period}'. Allowed: {', '.join(sorted(ALLOWED_PERIODS))}")

    # Normalize to UTC start/end of day
    start_utc = datetime.combine(start_date.date(), datetime.min.time(), tzinfo=timezone.utc)
    end_utc   = datetime.combine(end_date.date(),   datetime.max.time(), tzinfo=timezone.utc)
    return start_utc, end_utc