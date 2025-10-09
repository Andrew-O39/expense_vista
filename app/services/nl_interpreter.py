import re
from typing import Optional, Tuple

# Recognized period keywords
PERIOD_ALIASES = {
    "this week": "week",
    "current week": "week",
    "last week": "last_week",
    "this month": "month",
    "current month": "month",
    "last month": "last_month",
    "this quarter": "quarter",
    "current quarter": "quarter",
    "last quarter": "last_quarter",
    "this year": "year",
    "current year": "year",
    "last year": "last_year",
}

PERIOD_PAT = re.compile(
    r"\b(this|current|last)\s+(week|month|quarter|year)\b",
    flags=re.I,
)

def _normalize(s: str) -> str:
    return " ".join((s or "").lower().strip().split())

def _extract_period(text: str):
    """
    Returns (period_key, text_without_that_period_phrase)
    If none found, returns (None, original_text)
    """
    m = PERIOD_PAT.search(text)
    if not m:
        return None, text
    phrase = m.group(0).lower()  # e.g. "this week"
    period_key = PERIOD_ALIASES.get(phrase, None)
    # remove the matched phrase from text so it can't pollute category
    cleaned = (text[:m.start()] + text[m.end():]).strip()
    return period_key, cleaned

def parse_intent(message: str):
    """
    Very small NL interpreter:
    - detects period (order-insensitive)
    - tries to detect category words (minus the period phrase)
    - returns (intent, params)
    """
    t = _normalize(message)

    # 1) detect period and strip it from text to avoid contaminating category
    period, rest = _extract_period(t)

    # 2) see if user asks spend in category+period (order-insensitive)
    #    trigger words for spending
    if "spend" in t or "spent" in t or "expenses" in t:
        # try to spot a category-ish token. We’ll use a simple heuristic:
        # take the remaining words, drop common function words
        stop = set(["how", "much", "did", "i", "on", "in", "this", "last", "current", "week",
                    "month", "quarter", "year", "my", "the", "me", "spend", "spent", "expenses"])
        # candidate category is the longest remaining token/phrase up to 2 words
        tokens = [w for w in re.split(r"[^a-z0-9]+", rest) if w and w not in stop]
        cat = " ".join(tokens[:2]).strip() if tokens else ""

        if cat:
            return "spend_in_category_period", {
                "category": cat,
                "period": period or "month",
            }

        # no category found → total spend in period
        return "spend_in_period", {
            "period": period or "month",
        }

    # 3) overview
    if "income" in t and ("expense" in t or "spend" in t):
        return "income_expense_overview_period", {
            "period": period or "month",
        }

    # 4) on track
    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {}

    # fallback
    return "unknown", {}