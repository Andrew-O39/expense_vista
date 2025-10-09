from datetime import datetime, timezone
from calendar import monthrange

def period_range(period: str):
    now = datetime.now(timezone.utc)
    y, m, d = now.year, now.month, now.day

    if period == "week":
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        # move to Monday
        dow = start.weekday()  # Mon=0
        start = start.replace(day=(start.day - dow))
        end = start.replace(day=(start.day + 6), hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    if period == "last_week":
        # previous Monday..Sunday
        start, end = period_range("week")
        start = start.replace(day=start.day - 7)
        end   = end.replace(day=end.day - 7)
        return start, end

    if period in ("month", "last_month"):
        if period == "last_month":
            m2 = m - 1 or 12
            y2 = y - 1 if m == 1 else y
            start = datetime(y2, m2, 1, tzinfo=timezone.utc)
            last_day = monthrange(y2, m2)[1]
            end = datetime(y2, m2, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
        else:
            start = datetime(y, m, 1, tzinfo=timezone.utc)
            last_day = monthrange(y, m)[1]
            end = datetime(y, m, last_day, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return start, end

    if period in ("quarter", "last_quarter"):
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

    if period in ("year", "last_year"):
        if period == "last_year":
            y = y - 1
        start = datetime(y, 1, 1, tzinfo=timezone.utc)
        end = datetime(y, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
        return start, end

    # default month
    return period_range("month")