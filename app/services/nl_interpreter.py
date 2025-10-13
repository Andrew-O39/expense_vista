import re

# Recognized period keywords (added half-year)
PERIOD_ALIASES = {
    "this week": "week", "current week": "week", "last week": "last_week",
    "this month": "month", "current month": "month", "last month": "last_month",
    "this quarter": "quarter", "current quarter": "quarter", "last quarter": "last_quarter",
    "this half-year": "half_year", "this half year": "half_year", "current half-year": "half_year",
    "last half-year": "last_half_year", "last half year": "last_half_year",
    "this year": "year", "current year": "year", "last year": "last_year",
}

# allow 'half-year' variants in the period detector
PERIOD_PAT = re.compile(r"\b(this|current|last)\s+(week|month|quarter|half[-\s]?year|year)\b", re.I)

BUDGET_WORDS = {"budget", "budgets", "overbudget", "over-budget", "underbudget", "under-budget", "left", "remaining", "remain", "leftover"}
EXPENSE_WORDS = {"spend", "spent", "expense", "expenses", "costs"}
INCOME_WORDS = {"income", "incomes", "earnings", "revenue"}

STOP_WORDS = {
    "how","much","did","i","on","in","this","last","current","week","month","quarter","half-year","half","year",
    "my","the","me","spend","spent","expenses","expense","of","for","vs","versus","compare","comparison","show"
}

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
    phrase = m.group(0).lower()  # e.g. "this half-year"
    # normalize the phrase for lookup
    phrase = phrase.replace("half year", "half-year")  # normalize alias
    period_key = PERIOD_ALIASES.get(phrase, None)
    # remove the matched phrase from text so it can't pollute category/source
    cleaned = (text[:m.start()] + text[m.end():]).strip()
    return period_key, cleaned

def _extract_category(text_without_period: str):
    tokens = [w for w in re.split(r"[^a-z0-9]+", text_without_period) if w]
    # drop stop words, keep the longest 1–2 remaining tokens as category guess
    cand = [w for w in tokens if w not in STOP_WORDS and w not in {"on","in"}]
    if not cand:
        return ""
    return " ".join(cand[:2]).strip()

def parse_intent(message: str):
    """
    Detects:
      - spend_in_category_period / spend_in_period
      - income_expense_overview_period
      - budget_status_category_period / budget_status_period
      - on_track_quarter
    Returns (intent, params)
    """
    t = _normalize(message)
    period, rest = _extract_period(t)

    # Budget-related questions
    if any(w in t for w in BUDGET_WORDS) or "budget" in t:
        cat = _extract_category(rest)
        if cat:
            return "budget_status_category_period", {"category": cat, "period": period or "month"}
        return "budget_status_period", {"period": period or "month"}

    # Spend / expenses
    if any(w in t for w in EXPENSE_WORDS):
        cat = _extract_category(rest)
        if cat:
            return "spend_in_category_period", {"category": cat, "period": period or "month"}
        return "spend_in_period", {"period": period or "month"}

    # Income vs expenses overview
    if any(w in t for w in INCOME_WORDS) and (any(w in t for w in EXPENSE_WORDS) or "vs" in t or "versus" in t or "compare" in t):
        return "income_expense_overview_period", {"period": period or "month"}

    # Heuristic for "on track this quarter"
    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {}

    return "unknown", {}