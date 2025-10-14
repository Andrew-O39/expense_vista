from datetime import datetime, timezone, timedelta
from calendar import monthrange

def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

def _end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)

def period_range(period: str):
    now = datetime.now(timezone.utc)

    # ---- week / last_week ----
    if period == "week":
        today = _start_of_day(now)
        # Monday = 0 ... Sunday = 6
        dow = today.weekday()
        start = today - timedelta(days=dow)
        end = _end_of_day(start + timedelta(days=6))
        return start, end

    if period == "last_week":
        this_week_start, _ = period_range("week")
        start = this_week_start - timedelta(days=7)
        end = _end_of_day(start + timedelta(days=6))
        return start, end

    # ---- month / last_month ----
    if period in ("month", "last_month"):
        y, m = now.year, now.month
        if period == "last_month":
            m = 12 if m == 1 else m - 1
            y = y - 1 if m == 12 else y
        start = datetime(y, m, 1, tzinfo=timezone.utc)
        last_day = monthrange(y, m)[1]
        end = datetime(y, m, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return start, end

    # ---- quarter / last_quarter ----
    if period in ("quarter", "last_quarter"):
        y, m = now.year, now.month
        q = (m - 1) // 3  # 0..3
        if period == "last_quarter":
            q = (q - 1) % 4
            y = y - 1 if q == 3 else y
        start_month = q * 3 + 1
        end_month = start_month + 2
        start = datetime(y, start_month, 1, tzinfo=timezone.utc)
        last_day = monthrange(y, end_month)[1]
        end = datetime(y, end_month, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return start, end

    # ---- half-year / last_half_year ----
    if period in ("half_year", "last_half_year"):
        y, m = now.year, now.month
        first_half = m <= 6
        if period == "last_half_year":
            if first_half:
                y -= 1
                start_m, end_m = 7, 12
            else:
                start_m, end_m = 1, 6
        else:
            start_m, end_m = (1, 6) if first_half else (7, 12)
        start = datetime(y, start_m, 1, tzinfo=timezone.utc)
        last_day = monthrange(y, end_m)[1]
        end = datetime(y, end_m, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return start, end

    # ---- year / last_year ----
    if period in ("year", "last_year"):
        y = now.year - 1 if period == "last_year" else now.year
        start = datetime(y, 1, 1, tzinfo=timezone.utc)
        end = datetime(y, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return start, end

    # default
    return period_range("month")