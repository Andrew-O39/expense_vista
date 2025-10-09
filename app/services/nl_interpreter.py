# app/services/nl_interpreter.py
import re
from typing import Optional, Tuple

# Supported periods
PERIOD_KEYWORDS = {
    "this week": "week",
    "last week": "last_week",
    "this month": "month",
    "last month": "last_month",
    "this quarter": "quarter",
    "last quarter": "last_quarter",
    "this year": "year",
    "last year": "last_year",
}

def parse_period(text: str) -> Optional[str]:
    t = text.lower()
    for k, v in PERIOD_KEYWORDS.items():
        if k in t:
            return v
    # default
    if "month" in t: return "month"
    if "week" in t:  return "week"
    if "quarter" in t: return "quarter"
    if "year" in t: return "year"
    return None

def parse_category(text: str) -> Optional[str]:
    # naive: look for "on/for <category>" or after "category"
    m = re.search(r"\b(?:on|for|category)\s+([a-zA-Z\-\s]+)", text.lower())
    if m:
        return " ".join(m.group(1).strip().split())
    # fallback: common categories (tune as you wish)
    commons = ["groceries", "transport", "utilities", "restaurants", "shopping", "subscriptions", "housing"]
    for c in commons:
        if c in text.lower():
            return c
    return None

def parse_intent(text: str) -> Tuple[str, dict]:
    """
    Returns (intent, params dict)
    intents:
      - spend_in_period
      - spend_in_category_period
      - income_expense_overview_period
      - on_track_quarter (placeholder)
    """
    t = text.lower()
    period = parse_period(t)
    category = parse_category(t)

    if "how much did i spend" in t or "total spent" in t or "spend" in t:
        if category:
            return "spend_in_category_period", {"period": period or "month", "category": category}
        return "spend_in_period", {"period": period or "month"}

    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {"period": "quarter"}

    if "income" in t or "net" in t or "balance" in t or "overview" in t:
        return "income_expense_overview_period", {"period": period or "month"}

    # default
    return "spend_in_period", {"period": period or "month"}