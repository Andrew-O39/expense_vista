import re

# Recognized period keywords (expanded for half-year)
PERIOD_ALIASES = {
    # Week variations
    "this week": "week",
    "current week": "week",
    "last week": "last_week",

    # Month variations
    "this month": "month",
    "current month": "month",
    "last month": "last_month",

    # Quarter variations
    "this quarter": "quarter",
    "current quarter": "quarter",
    "last quarter": "last_quarter",

    # Year variations
    "this year": "year",
    "current year": "year",
    "last year": "last_year",

    # Half-year variations
    "this half year": "half_year",
    "this half-year": "half_year",
    "this halfyear": "half_year",
    "this half yearly": "half_year",
    "this half-yearly": "half_year",

    "current half year": "half_year",
    "current half-year": "half_year",
    "current halfyear": "half_year",

    "last half year": "last_half_year",
    "last half-year": "last_half_year",
    "last halfyear": "last_half_year",
    "last half yearly": "last_half_year",
    "last half-yearly": "last_half_year",
}

# allow 'half-year' variants in the period detector
PERIOD_PAT = re.compile(
    r"\b(this|current|last)\s+(week|month|quarter|year|half[-\s]?year(?:ly)?)\b",
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
    phrase = m.group(0).lower()  # e.g. "this half-year"
    # normalize the phrase for lookup
    phrase_norm = phrase.replace("  ", " ").strip()
    period_key = PERIOD_ALIASES.get(phrase_norm, None)
    # remove the matched phrase from text so it can't pollute category/source
    cleaned = (text[:m.start()] + text[m.end():]).strip()
    return period_key, cleaned

def parse_intent(message: str):
    """
    Very small NL interpreter:
    - detects period (order-insensitive)
    - tries to detect category words (minus the period phrase)
    - recognizes expenses + budgets + income intents
    - returns (intent, params)
    """
    t = _normalize(message)

    # 1) detect period and strip it from text to avoid contaminating category/source
    period, rest = _extract_period(t)

    # --- EXPENSES ---
    if "spend" in t or "spent" in t or "expenses" in t:
        stop = {
            "how","much","did","i","on","in","this","last","current",
            "week","month","quarter","year","half","half-year","halfyear",
            "halfyearly","half-yearly","my","the","me",
            "spend","spent","expenses"
        }
        tokens = [w for w in re.split(r"[^a-z0-9]+", rest) if w and w not in stop]
        cat = " ".join(tokens[:2]).strip() if tokens else ""

        if cat:
            return "spend_in_category_period", {
                "category": cat,
                "period": period or "month",
            }

        return "spend_in_period", {
            "period": period or "month",
        }

    # --- INCOME ---
    # If user mentions income and NOT specifically expenses, treat as income query
    if "income" in t and not ("spend" in t or "spent" in t or "expenses" in t):
        # Try to detect "from X" (simple source heuristic)
        source = None
        m = re.search(r"\bincome\s+from\s+([a-z0-9\s\-]+)", rest)
        if m:
            source = " ".join(m.group(1).strip().split()[:3])  # up to 3 tokens

        # If not "from", try a generic trailing token after 'income'
        if not source:
            m2 = re.search(r"\bincome\s+([a-z0-9][a-z0-9\s\-]{0,30})$", rest)
            if m2:
                cand = " ".join(m2.group(1).strip().split()[:2])
                # avoid common words
                if cand not in ("in", "on", "this", "last", "current", "week", "month", "quarter", "year"):
                    source = cand

        if source:
            return "income_in_period", {
                "period": period or "month",
                "source": source,
            }

        return "income_in_period", {
            "period": period or "month",
        }

    # --- OVERVIEW (income vs expense) ---
    if "income" in t and ("expense" in t or "spend" in t or "spent" in t):
        return "income_expense_overview_period", {
            "period": period or "month",
        }

    # --- BUDGETS ---
    budget_triggers = ("on track", "remaining", "left", "budget status", "over budget", "overspent")
    if any(bt in t for bt in budget_triggers):
        # Try to extract a category-ish token (reuse simple heuristic)
        stop = {
            "how","much","did","i","on","in","this","last","current",
            "week","month","quarter","year","half","half-year","halfyear",
            "halfyearly","half-yearly","my","the","me","budget","budgets","status",
            "remaining","left","over","overspent","track","on","am","i"
        }
        tokens = [w for w in re.split(r"[^a-z0-9]+", rest) if w and w not in stop]
        cat = " ".join(tokens[:2]).strip() if tokens else ""

        if cat:
            return "budget_status_category_period", {
                "category": cat,
                "period": period or "month",
            }
        return "budget_status_period", {
            "period": period or "month",
        }

    # --- On track (quarter) legacy phrase ---
    if "on track" in t and "quarter" in t:
        return "on_track_quarter", {}

    # fallback
    return "unknown", {}