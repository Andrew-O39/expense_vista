import re

# ----- Periods (incl. half-year) -----
PERIOD_ALIASES = {
    "this week": "week", "current week": "week", "last week": "last_week",
    "this month": "month", "current month": "month", "last month": "last_month",
    "this quarter": "quarter", "current quarter": "quarter", "last quarter": "last_quarter",
    "this half-year": "half_year", "this half year": "half_year",
    "current half-year": "half_year", "current half year": "half_year",
    "last half-year": "last_half_year", "last half year": "last_half_year",
    "this year": "year", "current year": "year", "last year": "last_year",
}
PERIOD_PAT = re.compile(
    r"\b(this|current|last)\s+(week|month|quarter|half[-\s]?year|year)\b",
    re.I,
)

# ----- Keyword sets -----
BUDGET_WORDS = {
    "budget","budgets","overbudget","over-budget","underbudget","under-budget",
    "left","remaining","remain","leftover","status","on track","track"
}
EXPENSE_WORDS = {"spend","spent","expense","expenses","cost","costs"}
INCOME_WORDS  = {"income","incomes","earnings","revenue"}

# words that must NOT be treated as categories
STOP_WORDS = {
    # wh- & helpers
    "how","what","which","when","where","why","is","are","was","were","did","do","does","me","my",
    "the","a","an","of","for","to","vs","versus","compare","comparison","show",
    # time
    "this","last","current","week","month","quarter","half-year","half","year",
    # budget & calc
    "budget","budgets","overbudget","over-budget","underbudget","under-budget","status",
    "remaining","remain","left","leftover","on","track","am","under","over",
    # expense/income
    "spend","spent","expense","expenses","cost","costs","income","incomes","and",
    # fillers
    "in","on","at","with"
}

def _normalize(s: str) -> str:
    return " ".join((s or "").lower().strip().split())

def _extract_period(text: str):
    m = PERIOD_PAT.search(text)
    if not m:
        return None, text
    phrase = m.group(0).lower().replace("half year","half-year")
    period_key = PERIOD_ALIASES.get(phrase, None)
    cleaned = (text[:m.start()] + text[m.end():]).strip()
    return period_key, cleaned

def _extract_category_from_patterns(text: str) -> str:
    """
    Try explicit patterns first, then fallback heuristic.
    """
    t = text

    # Budget-focused patterns
    # "my groceries budget", "groceries budget", "my transport budget"
    m = re.search(r"\b(?:my\s+)?([a-z0-9\s]+?)\s+budget\b", t)
    if m:
        cand = m.group(1).strip()
        cand = re.sub(r"\b(" + "|".join(map(re.escape, STOP_WORDS)) + r")\b", " ", cand)
        cand = " ".join(cand.split())
        if cand:
            return cand

    # "budget for groceries"
    m = re.search(r"\bbudget\s+(?:for|on|of)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = m.group(1).strip()
        cand = re.sub(r"\b(" + "|".join(map(re.escape, STOP_WORDS)) + r")\b", " ", cand)
        cand = " ".join(cand.split())
        if cand:
            return cand

    # Spend-focused patterns
    # "spend on groceries", "spent on transport"
    m = re.search(r"\bspen[td]\s+(?:money\s+)?(?:on|for)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = m.group(1).strip()
        cand = re.sub(r"\b(" + "|".join(map(re.escape, STOP_WORDS)) + r")\b", " ", cand)
        cand = " ".join(cand.split())
        if cand:
            return cand

    # Generic “on X” / “for X” (but avoid grabbing period words etc.)
    m = re.search(r"\b(?:on|for)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = m.group(1).strip()
        cand = re.sub(r"\b(" + "|".join(map(re.escape, STOP_WORDS)) + r")\b", " ", cand)
        cand = " ".join(cand.split())
        if cand:
            return cand

    # Fallback heuristic: take up to two non-stop tokens
    tokens = [w for w in re.split(r"[^a-z0-9]+", t) if w]
    cand = [w for w in tokens if w not in STOP_WORDS]
    if cand:
        return " ".join(cand[:2]).strip()

    return ""

def parse_intent(message: str):
    """
    - detects period (order-insensitive)
    - category via patterns (“my X budget”, “spent on X”, …) then heuristic
    - intent order: 1) income-vs-expenses, 2) budget, 3) expenses
    """
    t = _normalize(message)
    period, rest = _extract_period(t)

    # 1) income vs expenses / compare
    if (any(w in t for w in INCOME_WORDS) and
        (" vs " in t or "versus" in t or "compare" in t or any(w in t for w in EXPENSE_WORDS))):
        return "income_expense_overview_period", {"period": period or "month"}

    # 2) budget questions
    if "budget" in t or any(w in t for w in BUDGET_WORDS):
        cat = _extract_category_from_patterns(rest)
        if cat:
            return "budget_status_category_period", {"category": cat, "period": period or "month"}
        return "budget_status_period", {"period": period or "month"}

    # 3) spend / expenses
    if any(w in t for w in EXPENSE_WORDS):
        cat = _extract_category_from_patterns(rest)
        if cat:
            return "spend_in_category_period", {"category": cat, "period": period or "month"}
        return "spend_in_period", {"period": period or "month"}

    # Heuristic: on track this quarter
    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {}

    return "unknown", {}