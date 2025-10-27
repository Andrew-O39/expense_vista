import re

PERIOD_ALIASES = {
    # week
    "this week": "week",
    "current week": "week",
    "this wk": "week",
    "wk": "week",
    "last week": "last_week",
    "prev week": "last_week",

    # month
    "this month": "month",
    "current month": "month",
    "last month": "last_month",
    "previous month": "last_month",

    # quarter
    "this quarter": "quarter",
    "current quarter": "quarter",
    "last quarter": "last_quarter",
    "previous quarter": "last_quarter",

    # half-year (many variants)
    "this half-year": "half_year",
    "this half year": "half_year",
    "current half-year": "half_year",
    "current half year": "half_year",
    "last half-year": "last_half_year",
    "last half year": "last_half_year",
    "previous half-year": "last_half_year",
    "previous half year": "last_half_year",
    "h1": "half_year", "first half": "half_year", "first half-year": "half_year",
    "h2": "half_year", "second half": "half_year", "second half-year": "half_year",

    # year
    "this year": "year",
    "current year": "year",
    "last year": "last_year",
    "previous year": "last_year",
}

SUPPORTED_PERIOD_KEYS = {
    "week","last_week",
    "month","last_month",
    "quarter","last_quarter",
    "half_year","last_half_year",
    "year","last_year",
}

PERIOD_PAT = re.compile(
    r"\b(this|current|last)\s+(week|month|quarter|half[-\s]?year|year)\b",
    re.I,
)

EXPENSE_WORDS = {"spend","spent","expense","expenses","cost","costs"}
INCOME_WORDS  = {"income","incomes","earnings","revenue"}
BUDGET_WORDS  = {"budget","budgets","over","under","remaining","left","status","on track","track"}
TOP_WORDS     = {"top","biggest","largest","most"}
EXTREME_WORDS_HIGH = {"highest","largest","biggest","top","max","maximum","hightest"}
EXTREME_WORDS_LOW  = {"lowest","smallest","min","minimum"}


STOP_WORDS = {
    "how","what","which","when","where","why","is","are","was","were","did","do","does","me","my",
    "the","a","an","of","for","to","vs","versus","compare","comparison","show",
    "this","last","current","week","month","quarter","half-year","half","year",
    "budget","budgets","overbudget","over-budget","underbudget","under-budget","status",
    "remaining","remain","left","leftover","on","track","am","under","over",
    "spend","spent","expense","expenses","cost","costs","income","incomes","and","in","at","with",
}

def _normalize(s: str) -> str:
    s = (s or "").lower().strip()
    # strip possessives ("what's" → "what")
    s = s.replace("'s", " ").replace("’s", " ")
    return " ".join(s.split())


def _extract_period(text: str):
    m = PERIOD_PAT.search(text)
    if not m:
        return None, text
    phrase = m.group(0).lower().replace("half year","half-year")
    period_key = PERIOD_ALIASES.get(phrase, None)
    cleaned = (text[:m.start()] + text[m.end():]).strip()
    return period_key, cleaned

def _clean(s: str) -> str:
    s = re.sub(r"[^a-z0-9\s]+", " ", s.lower())
    s = re.sub(r"\b(" + "|".join(map(re.escape, STOP_WORDS)) + r")\b", " ", s)
    s = " ".join(s.split())
    return s

def _valid_cat(c: str) -> bool:
    if not c: return False
    if len(c) < 2: return False          # reject one-letter “i”
    if c in {"i","am"}: return False
    return True

def _extract_category(text: str) -> str:
    t = text

    # When asking for highest/lowest budgets, do NOT try to interpret that as a category
    if "budget" in t and (any(w in t for w in EXTREME_WORDS_HIGH | EXTREME_WORDS_LOW)):
        return ""

    # 1) “over/under budget on/for X”
    m = re.search(r"\b(?:over|under)\s+budget\s+(?:on|for)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = _clean(m.group(1))
        if _valid_cat(cand): return cand

    # 2) “budget for/on/of X”
    m = re.search(r"\bbudget\s+(?:for|on|of)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = _clean(m.group(1))
        if _valid_cat(cand): return cand

    # 3) “my X budget” / “X budget” (but avoid “i over budget”)
    m = re.search(r"\b(?:my\s+)?([a-z0-9\s]+?)\s+budget\b", t)
    if m:
        raw = m.group(1).strip().lower()
        if not re.search(r"\b(over|under)\b", raw):  # avoid “i over”
            cand = _clean(raw)
            if _valid_cat(cand): return cand

    # 4) “spend on/for X”, “spent on/for X”
    m = re.search(r"\bspen[td]\s+(?:money\s+)?(?:on|for)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = _clean(m.group(1))
        if _valid_cat(cand): return cand

    # 5) generic “on/for X”
    m = re.search(r"\b(?:on|for)\s+([a-z0-9\s]+)\b", t)
    if m:
        cand = _clean(m.group(1))
        if _valid_cat(cand): return cand

    return ""

def parse_intent(message: str):
    t = _normalize(message)
    period, rest = _extract_period(t)

    # income vs expenses (compare)
    if (any(w in t for w in INCOME_WORDS) and
        (" vs " in t or "versus" in t or "compare" in t or any(w in t for w in EXPENSE_WORDS))):
        return "income_expense_overview_period", {"period": period or "month"}

    # income-only totals
    if any(w in t for w in INCOME_WORDS) and not any(w in t for w in EXPENSE_WORDS | BUDGET_WORDS):
        return "income_in_period", {"period": period or "month"}

    # highest/lowest budget (overall) BEFORE generic budgets ----
    if "budget" in t and any(w in t for w in EXTREME_WORDS_HIGH):
        return "highest_budget_period", {"period": period or "month"}  # or "year" if you prefer
    if "budget" in t and any(w in t for w in EXTREME_WORDS_LOW):
        return "lowest_budget_period", {"period": period or "month"}   # or "year"

    # budgets (status, optional category)
    if "budget" in t or any(w in t for w in BUDGET_WORDS):
        cat = _extract_category(rest)
        if cat:
            return "budget_status_category_period", {"category": cat, "period": period or "month"}
        return "budget_status_period", {"period": period or "month"}

    # “top category …”
    if any(w in t for w in TOP_WORDS) and ("category" in t or "categories" in t or any(w in t for w in EXPENSE_WORDS)):
        return "top_category_in_period", {"period": period or "month"}

    # generic spend
    if any(w in t for w in EXPENSE_WORDS):
        cat = _extract_category(rest)
        if cat:
            return "spend_in_category_period", {"category": cat, "period": period or "month"}
        return "spend_in_period", {"period": period or "month"}

    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {}

    return "unknown", {}

    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {}

    return "unknown", {}