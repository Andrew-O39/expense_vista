import re

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

EXPENSE_WORDS = {"spend","spent","expense","expenses","cost","costs"}
INCOME_WORDS  = {"income","incomes","earnings","revenue"}
BUDGET_WORDS  = {"budget","budgets","over","under","remaining","left","status","on track","track"}
TOP_WORDS     = {"top","biggest","largest","most"}

STOP_WORDS = {
    "how","what","which","when","where","why","is","are","was","were","did","do","does","me","my",
    "the","a","an","of","for","to","vs","versus","compare","comparison","show",
    "this","last","current","week","month","quarter","half-year","half","year",
    "budget","budgets","overbudget","over-budget","underbudget","under-budget","status",
    "remaining","remain","left","leftover","on","track","am","under","over",
    "spend","spent","expense","expenses","cost","costs","income","incomes","and","in","at","with",
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

def _extract_category(text: str) -> str:
    t = text
    # “my groceries budget”, “groceries budget”
    m = re.search(r"\b(?:my\s+)?([a-z0-9\s]+?)\s+budget\b", t)
    if m:
        cand = _clean(m.group(1))
        if cand: return cand

    # “budget for groceries”
    m = re.search(r"\bbudget\s+(?:for|on|of)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = _clean(m.group(1))
        if cand: return cand

    # “spend on groceries”, “spent on transport”
    m = re.search(r"\bspen[td]\s+(?:money\s+)?(?:on|for)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = _clean(m.group(1))
        if cand: return cand

    # generic “on/for X” but only if it’s not just stop words
    m = re.search(r"\b(?:on|for)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = _clean(m.group(1))
        if cand: return cand

    # no category unless a pattern matched
    return ""

def _clean(s: str) -> str:
    s = re.sub(r"[^a-z0-9\s]+", " ", s.lower())
    s = re.sub(r"\b(" + "|".join(map(re.escape, STOP_WORDS)) + r")\b", " ", s)
    s = " ".join(s.split())
    return s

def parse_intent(message: str):
    t = _normalize(message)
    period, rest = _extract_period(t)

    # 1) income vs expenses (or compare …)
    if (any(w in t for w in INCOME_WORDS) and
        (" vs " in t or "versus" in t or "compare" in t or any(w in t for w in EXPENSE_WORDS))):
        return "income_expense_overview_period", {"period": period or "month"}

    # 2) budget queries
    if "budget" in t or any(w in t for w in BUDGET_WORDS):
        cat = _extract_category(rest)
        if cat:
            return "budget_status_category_period", {"category": cat, "period": period or "month"}
        return "budget_status_period", {"period": period or "month"}

    # 3) “top category”
    if any(w in t for w in TOP_WORDS) and ("category" in t or "categories" in t or any(w in t for w in EXPENSE_WORDS)):
        return "top_category_in_period", {"period": period or "month"}

    # 4) generic spend
    if any(w in t for w in EXPENSE_WORDS):
        cat = _extract_category(rest)
        if cat:
            return "spend_in_category_period", {"category": cat, "period": period or "month"}
        return "spend_in_period", {"period": period or "month"}

    # heuristic
    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {}

    return "unknown", {}