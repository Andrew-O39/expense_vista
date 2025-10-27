from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from unicodedata import normalize as u_norm
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.income import Income
from app.db.models.budget import Budget
from app.core.config import settings
from app.schemas.assistant import AssistantMessage, AssistantReply, AssistantAction
from app.services.nl_interpreter import parse_intent, PERIOD_ALIASES, SUPPORTED_PERIOD_KEYS
from app.services.llm_client import llm_complete_json
from app.utils.assistant_dates import period_range
import re
from calendar import monthrange
from collections import OrderedDict

import logging
logger = logging.getLogger("assistant")
logging.basicConfig(level=logging.INFO)


router = APIRouter(prefix="/ai", tags=["AI"])

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

def _month_name_to_num(name: str) -> int | None:
    return MONTHS.get((name or "").strip().lower())

def _end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def _month_range(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = monthrange(year, month)[1]
    end = _end_of_day(datetime(year, month, last_day, tzinfo=timezone.utc))
    return start, end


def _latest_budgets_by_category(
    db: Session,
    user_id: int,
    period_key: str,
    end_dt: datetime,
) -> list[Budget]:
    """Return the most recent budget per category (created_at <= end_dt) for a given period_key."""
    period_map = {
        "week": "weekly", "last_week": "weekly",
        "month": "monthly", "last_month": "monthly",
        "quarter": "quarterly", "last_quarter": "quarterly",
        "half_year": "half-yearly", "last_half_year": "half-yearly",
        "year": "yearly", "last_year": "yearly",
    }
    target = period_map.get(period_key, "monthly")

    rows = (
        db.query(Budget)
          .filter(
              Budget.user_id == user_id,
              Budget.period == target,
              Budget.created_at <= end_dt,
          )
          .order_by(Budget.category.asc(), Budget.created_at.desc())
          .all()
    )

    # keep only the latest per category (case-insensitive)
    latest: "OrderedDict[str, Budget]" = OrderedDict()
    for b in rows:
        cat = (b.category or "").strip().lower()
        if not cat:
            continue
        if cat not in latest:
            latest[cat] = b  # first seen is latest due to DESC ordering

    return list(latest.values())

def _hint_period_from_text(text: str) -> str | None:
    t = " ".join((text or "").lower().split())
    # order matters: check specific before generic
    if "last week" in t: return "last_week"
    if "this week" in t or "current week" in t: return "week"
    if "last month" in t or "previous month" in t: return "last_month"
    if "this month" in t or "current month" in t: return "month"
    if "last quarter" in t or "previous quarter" in t: return "last_quarter"
    if "this quarter" in t or "current quarter" in t: return "quarter"
    if "last half-year" in t or "last half year" in t: return "last_half_year"
    if "this half-year" in t or "this half year" in t: return "half_year"
    if "last year" in t or "previous year" in t: return "last_year"
    if "this year" in t or "current year" in t: return "year"
    return None

def _text_mentions_year(text: str) -> bool:
    return bool(re.search(r"\b\d{4}\b", (text or "")))

MONTH_NAME_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.I
)

RELATIVE_RE = re.compile(
    r"\b(this|current|last|previous)\s+(week|month|quarter|half[-\s]?year|year)\b",
    re.I,
)

def _text_mentions_month(text: str) -> bool:
    return bool(MONTH_NAME_RE.search((text or "")))

def _friendly_period_label(period_key: str) -> str:
    """
    Map internal period keys to human-friendly labels.
    """
    mapping = {
        "week": "this week",
        "last_week": "last week",
        "month": "this month",
        "last_month": "last month",
        "quarter": "this quarter",
        "last_quarter": "last quarter",
        "half_year": "this half-year",
        "last_half_year": "last half-year",
        "year": "this year",
        "last_year": "last year",
    }
    return mapping.get(period_key, period_key.replace("_", " "))

def _humanize_range(start: datetime, end: datetime, original_period: str | None = None) -> str:
    if original_period in {
        "week","last_week","month","last_month",
        "quarter","last_quarter","half_year","last_half_year",
        "year","last_year",
    }:
        return _friendly_period_label(original_period)

    # Otherwise, humanize dates (for “since June”, “September and October”, etc.)
    if start.year == end.year and start.month == end.month:
        return start.strftime("%B %Y")                # e.g. "September 2025"
    if start.year == end.year:
        return f"{start.strftime('%b')}–{end.strftime('%b %Y')}"   # "Sep–Oct 2025"
    return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}" # "Dec 2024 – Jan 2025"

def _find_months_in_text(text: str) -> list[tuple[int, int]]:
    """
    Return list of (year, month) seen in the text, in order.
    Handles 'september', 'september 2024', etc. Scans all tokens, not just the first.
    """
    t = " ".join((text or "").lower().split())
    now = datetime.now(timezone.utc)
    results: list[tuple[int,int]] = []
    for m in re.finditer(r"\b([a-z]+)(?:\s+(\d{4}))?\b", t):
        name, y = m.group(1), m.group(2)
        mn = _month_name_to_num(name)
        if not mn:
            continue
        year = int(y) if y else now.year
        results.append((year, mn))
    return results

def _heuristic_range_from_text(text: str) -> tuple[datetime, datetime] | None:
    """Extended free-form date range parser."""
    t = " ".join((text or "").lower().split())
    now = datetime.now(timezone.utc)

    # last N days
    m = re.search(r"\blast\s+(\d{1,3})\s+days?\b", t)
    if m:
        n = max(1, int(m.group(1)))
        start = (now - timedelta(days=n - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = _end_of_day(now)
        return start, end

    # between X and Y
    m = re.search(r"\bbetween\s+([a-z]+)(?:\s+(\d{4}))?\s+and\s+([a-z]+)(?:\s+(\d{4}))?\b", t)
    if m:
        m1, y1, m2, y2 = m.group(1), m.group(2), m.group(3), m.group(4)
        mn1, mn2 = _month_name_to_num(m1), _month_name_to_num(m2)
        if mn1 and mn2:
            y_1 = int(y1) if y1 else now.year
            y_2 = int(y2) if y2 else (y_1 if y1 else now.year)
            s1, e1 = _month_range(y_1, mn1)
            s2, e2 = _month_range(y_2, mn2)
            return min(s1, s2), max(e1, e2)

    # from X to|until|till Y (Y can be now/today or a month)
    m = re.search(r"\bfrom\s+([a-z]+)(?:\s+(\d{4}))?\s+(?:to|until|till)\s+(now|today|[a-z]+(?:\s+\d{4})?)\b", t)
    if m:
        m_from, y_from, to_part = m.group(1), m.group(2), m.group(3)
        mn_from = _month_name_to_num(m_from)
        if mn_from:
            y_start = int(y_from) if y_from else now.year
            start = datetime(y_start, mn_from, 1, tzinfo=timezone.utc)
            if to_part in {"now", "today"}:
                end = _end_of_day(now); return start, end
            mm = re.match(r"([a-z]+)(?:\s+(\d{4}))?$", to_part)
            if mm:
                m_to, y_to = mm.group(1), mm.group(2)
                mn_to = _month_name_to_num(m_to)
                if mn_to:
                    y_end = int(y_to) if y_to else now.year
                    _, end = _month_range(y_end, mn_to)
                    return start, end

    # "<Month> and <Month>" (same year)
    m = re.search(r"\b([a-z]+)\s+and\s+([a-z]+)\b", t)
    if m:
        m1, m2 = _month_name_to_num(m.group(1)), _month_name_to_num(m.group(2))
        if m1 and m2:
            y = now.year
            s1, e1 = _month_range(y, m1)
            s2, e2 = _month_range(y, m2)
            return min(s1, s2), max(e1, e2)

    # since <month> [year]
    m = re.search(r"\bsince\s+([a-z]+)(?:\s+(\d{4}))?\b", t)
    if m:
        mn = _month_name_to_num(m.group(1))
        if mn:
            y = int(m.group(2)) if m.group(2) else now.year
            start = datetime(y, mn, 1, tzinfo=timezone.utc)
            end = _end_of_day(now)
            return start, end

    # single month anywhere
    months = _find_months_in_text(t)
    if months:
        y, mn = months[0]
        return _month_range(y, mn)

    return None


def _euro(n: float) -> str:
    return f"€{(n or 0):.2f}"

def _clean_category(cat: str) -> str:
    c = u_norm("NFKC", (cat or "").strip().lower())
    c = " ".join(c.split())
    synonyms = {
        "grocery": "groceries",
        "supermarket": "groceries",
        "transportation": "transport",
        "dining": "restaurants",
        "restaurant": "restaurants",
        "subscription": "subscriptions",
    }
    return synonyms.get(c, c)

def _parse_iso(dt: str) -> datetime:
    s = dt.strip().replace("Z", "+00:00")
    d = datetime.fromisoformat(s)
    return d.astimezone(timezone.utc)

def _normalize_period(p: Optional[str]) -> str | None:
    if not p:
        return None
    p = " ".join((p or "").lower().strip().split())
    return PERIOD_ALIASES.get(p, p)

def _resolve_range(params: dict, original_text: str | None = None) -> tuple[datetime, datetime, str, str | None]:
    """
    Priority:
      1) For RELATIVE phrases in the text, trust our period_range — ignore LLM start/end.
      2) If explicit start/end and NOT a relative phrase with no month name → use them.
      3) If no period, try heuristics (“since June”, “Sep & Oct”, “last 20 days”, “between … and …”, “from … until …”).
      4) Otherwise normalize period and use period_range.
    Returns (start, end, period_label, period_key_or_None)
    """
    raw = (original_text or "").lower().strip()

    # 1) Relative phrase (“this week/month/…” or “last N days”) → canonical period
    if RELATIVE_RE.search(raw):
        hint_key = _hint_period_from_text(raw)
        period_key = hint_key or _normalize_period(params.get("period")) or "month"
        s, e = period_range(period_key)
        return s, e, _humanize_range(s, e, original_period=period_key), period_key

    # 2) If the model supplied explicit dates:
    #    - but the user named a month WITHOUT a year → prefer our heuristics to avoid model inventing the year
    if "start" in params and "end" in params:
        if _text_mentions_month(raw) and not _text_mentions_year(raw):
            r = _heuristic_range_from_text(raw)
            if r:
                s, e = r
                return s, e, _humanize_range(s, e), None
        # otherwise trust explicit dates
        start = _parse_iso(params["start"])
        end   = _parse_iso(params["end"])
        return start, end, _humanize_range(start, end), None

    # 3) No explicit dates — try robust heuristics first (handles between/from/since/last N days)
    r = _heuristic_range_from_text(raw)
    if r:
        s, e = r
        return s, e, _humanize_range(s, e), None

    # 4) Fall back to normalized named period (default month)
    period_key = _normalize_period(params.get("period")) or "month"
    if period_key not in SUPPORTED_PERIOD_KEYS:
        period_key = "month"

    s, e = period_range(period_key)
    return s, e, _humanize_range(s, e, original_period=period_key), period_key

def _pick_budget(
    db: Session,
    user_id: int,
    category: Optional[str],
    period_key: str,
    start,
    end,
) -> Optional[Budget]:
    period_map = {
        "week": "weekly", "last_week": "weekly",
        "month": "monthly", "last_month": "monthly",
        "quarter": "quarterly", "last_quarter": "quarterly",
        "half_year": "half-yearly", "last_half_year": "half-yearly",
        "year": "yearly", "last_year": "yearly",
    }
    target = period_map.get(period_key, "monthly")

    q = (
        db.query(Budget)
          .filter(Budget.user_id == user_id,
                  Budget.period == target,
                  Budget.created_at <= end)
    )
    if category:
        q = q.filter(func.lower(Budget.category) == _clean_category(category))

    return q.order_by(desc(Budget.created_at)).first()

# ---------- Debug endpoint ----------

@router.post("/_intent_debug")
def ai_intent_debug(payload: dict):
    if not settings.ai_assistant_enabled or settings.ai_provider != "openai":
        return {"enabled": False, "reason": "AI assistant disabled in settings."}

    msg = (payload.get("message") or "").strip()
    if not msg:
        raise HTTPException(400, "message is required")

    prompt = (
        "You are a finance intent extractor. Respond ONLY with strict JSON.\n"
        "Allowed intents: [\n"
        "  'spend_in_period', 'spend_in_category_period',\n"
        "  'income_expense_overview_period', 'top_category_in_period',\n"
        "  'budget_status_category_period', 'budget_status_period',\n"
        "  'income_in_period'\n"
        "]\n"
        "Params may include:\n"
        "  - period: one of ['this week','last week','this month','last month','this quarter','last quarter','this half-year','last half-year','this year','last year']\n"
        "  - category: short string\n"
        "  - start, end: ISO 8601 UTC if the user named months/ranges or said 'since ...'\n"
        "If start/end are provided, omit 'period'. Return ONLY JSON.\n\n"
        f"User: {msg}"
    )
    parsed = llm_complete_json(prompt)
    return {"enabled": True, "model": settings.ai_model or "gpt-4o-mini", "parsed": parsed}

@router.post("/_range_debug")
def ai_range_debug(payload: dict):
    msg = (payload.get("message") or "").strip()
    if not msg:
        raise HTTPException(400, "message is required")

    # simulate your normal flow just enough to build params
    intent, params = parse_intent(msg)
    # (Pretend the LLM added start/end—skip that here)

    start, end, label, key = _resolve_range(params, original_text=msg)
    return {
        "intent": intent,
        "params_in": params,
        "resolved": {
            "period_key": key,
            "label": label,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    }

# ---------- Assistant endpoint (AI-first, rules fallback) ----------

@router.post("/assistant", response_model=AssistantReply)
def ai_assistant(payload: AssistantMessage, db: Session = Depends(get_db), user=Depends(get_current_user)):
    text = (payload.message or "").strip()

    # 1) AI-first intent extraction
    intent, params = "unknown", {}
    if settings.ai_assistant_enabled and settings.ai_provider == "openai":
        try:
            prompt = (
                "You are a finance intent extractor. Respond ONLY with strict JSON.\n"
                "Allowed intents: ['spend_in_period','spend_in_category_period',"
                "'income_expense_overview_period','top_category_in_period',"
                "'budget_status_category_period','budget_status_period','income_in_period']\n"
                "Params may include: { 'period'?: str, 'category'?: str, 'start'?: iso, 'end'?: iso }.\n"
                "If the user says 'September', 'since July', or 'September and October', compute explicit start/end (UTC).\n"
                "If both start/end are provided, omit 'period'. Return only JSON."
            )
            parsed = llm_complete_json(f"{prompt}\n\nUser: {text}")
            if parsed:
                alias = {"budget_status": "budget_status_period", "top_category_period": "top_category_in_period"}
                i = (parsed.get("intent") or "unknown").lower()
                intent = alias.get(i, i)
                params = parsed.get("params") or {}
        except Exception as e:
            print("LLM fallback failed:", e)

    # 2) Rules fallback if AI failed
    if intent == "unknown":
        intent, rule_params = parse_intent(text)
        # merge, but keep any start/end we might add later:
        params = {**rule_params}

    # 3) Resolve time range + friendly label
    start, end, period_label, period_key = _resolve_range(params, original_text=text)
    logger.info(
        "AI assistant resolved range: intent=%s period_label=%s period_key=%s start=%s end=%s",
        intent, period_label, period_key, start.isoformat(), end.isoformat()
    )

    actions: List[AssistantAction] = []

    # ---- Spend in category over a period ----
    if intent == "spend_in_category_period":
        cat = _clean_category(params.get("category", ""))
        if not cat:
            raise HTTPException(status_code=400, detail="Could not detect a category.")
        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id,
                      func.lower(Expense.category) == cat,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .scalar()
        ) or 0.0
        logger.info("spend_in_period result: total=%s label=%s start=%s end=%s",
                    total, period_label, start.isoformat(), end.isoformat())
        reply = f"You spent {_euro(total)} on {cat} in {period_label}."
        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={"search": cat, "category": cat,
                    "start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Spend total over a period ----
    if intent == "spend_in_period":
        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .scalar()
        ) or 0.0
        logger.info("spend_in_period result: total=%s label=%s start=%s end=%s",
                    total, period_label, start.isoformat(), end.isoformat())
        reply = f"You spent {_euro(total)} in {period_label}."
        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Income total in period ----
    if intent == "income_in_period":
        ts = func.coalesce(Income.received_at, Income.created_at)
        inc = (
            db.query(func.coalesce(func.sum(Income.amount), 0.0))
              .filter(Income.user_id == user.id, ts >= start, ts <= end)
              .scalar()
        ) or 0.0
        reply = f"Your income in {period_label} is {_euro(inc)}."
        actions.append(AssistantAction(
            type="open_incomes",
            label="See incomes",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Income vs expenses ----
    if intent == "income_expense_overview_period":
        income_ts = func.coalesce(Income.received_at, Income.created_at)
        inc = (
            db.query(func.coalesce(func.sum(Income.amount), 0.0))
              .filter(Income.user_id == user.id,
                      income_ts >= start, income_ts <= end)
              .scalar()
        ) or 0.0
        exp = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id,
                      Expense.created_at >= start, Expense.created_at <= end)
              .scalar()
        ) or 0.0
        net = inc - exp
        stance = "surplus" if net >= 0 else "deficit"
        reply = f"For {period_label}, income is {_euro(inc)}, expenses are {_euro(exp)}, net is {_euro(net)} ({stance})."
        actions.append(AssistantAction(type="show_chart", label="Show Income vs Expenses", params={"period": params.get("period")}))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Budget status (category) ----
    if intent == "budget_status_category_period":
        cat = _clean_category(params.get("category", ""))
        if not cat:
            raise HTTPException(status_code=400, detail="Could not detect a category.")
        try:
            budget = _pick_budget(db, user.id, cat, (period_key or "month"), start, end)
            if not budget:
                return AssistantReply(
                    reply=f"I couldn’t find a {period_label} budget for '{cat}'.",
                    actions=[]
                )

            spent = (
                        db.query(func.coalesce(func.sum(Expense.amount), 0.0))
                        .filter(
                            Expense.user_id == user.id,
                            func.lower(Expense.category) == cat,
                            Expense.created_at >= start,
                            Expense.created_at <= end,
                        )
                        .scalar()
                    ) or 0.0

            limit_amt = float(budget.limit_amount or 0.0)
            remaining = limit_amt - spent
            status = "under" if remaining >= 0 else "over"

            reply = (
                f"Your {period_label} budget for '{cat}' is {_euro(limit_amt)}. "
                f"You’ve spent {_euro(spent)}, so you are {status} budget by {_euro(abs(remaining))}."
            )
            actions.append(AssistantAction(
                type="open_budgets",
                label="See budgets",
                params={"search": cat, "category": cat,
                        "start_date": start.isoformat(), "end_date": end.isoformat()},
            ))
            return AssistantReply(reply=reply, actions=actions)
        except Exception as e:
            # log e if you have a logger
            return AssistantReply(
                reply=f"I couldn’t find a {period_label} budget for '{cat}'.",
                actions=[]
            )

    # ---- Budget status (overall) → sum latest-per-category for the period ----
    if intent == "budget_status_period":
        # pick normalized storage value (weekly/monthly/quarterly/...)
        period_map = {
            "week": "weekly", "last_week": "weekly",
            "month": "monthly", "last_month": "monthly",
            "quarter": "quarterly", "last_quarter": "quarterly",
            "half_year": "half-yearly", "last_half_year": "half-yearly",
            "year": "yearly", "last_year": "yearly",
        }
        key = (period_key or _normalize_period(params.get("period")) or "month")
        storage_period = period_map.get(key, "monthly")

        # latest snapshot per category as of `end`
        latest = _latest_budgets_by_category(db, user.id, key, end)
        latest = [b for b in latest if float(b.limit_amount or 0.0) > 0.0 and (b.period == storage_period)]

        if not latest:
            return AssistantReply(
                reply=f"I couldn’t find any {period_label} budgets.",
                actions=[]
            )

        total_budget = sum(float(b.limit_amount or 0.0) for b in latest)

        total_spent = (
                          db.query(func.coalesce(func.sum(Expense.amount), 0.0))
                          .filter(
                              Expense.user_id == user.id,
                              Expense.created_at >= start,
                              Expense.created_at <= end,
                          )
                          .scalar()
                      ) or 0.0

        remaining = total_budget - total_spent
        status = "under" if remaining >= 0 else "over"

        # Optional: include how many categories we summed, to set expectations
        reply = (
            f"Your total {period_label} budget (across {len(latest)} categories) is {_euro(total_budget)}. "
            f"Total spent is {_euro(total_spent)}, so you are {status} budget by {_euro(abs(remaining))}."
        )
        assumed = (period_key is None and "start" not in params and "end" not in params)
        if assumed:
            reply += " (I am assuming this month — but please specify a period like 'this year' or 'this week' to change it.)"

        actions.append(AssistantAction(
            type="open_budgets",
            label="See budgets",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Highest / Lowest budget in a period (combined) ----
    if intent in ("highest_budget_period", "lowest_budget_period"):
        # Figure out which period family we’re in (weekly/monthly/quarterly/…)
        key = (period_key or _normalize_period(params.get("period")) or "year")

        # Get latest-per-category snapshots up to `end`
        latest = _latest_budgets_by_category(db, user.id, key, end)

        # Keep only meaningful amounts (skip 0/None)
        latest = [b for b in latest if float(b.limit_amount or 0.0) > 0.0]

        if not latest:
            return AssistantReply(
                reply=f"I couldn’t find any {period_label} budgets.",
                actions=[]
            )

        # Pick highest or lowest by limit_amount
        chooser = max if intent == "highest_budget_period" else min
        pick = chooser(latest, key=lambda b: float(b.limit_amount or 0.0))

        cat = (pick.category or "").strip()
        amt = float(pick.limit_amount or 0.0)
        adjective = "highest" if intent == "highest_budget_period" else "lowest"

        reply = f"Your {adjective} {period_label} budget is '{cat}' at {_euro(amt)}."

        actions.append(AssistantAction(
            type="open_budgets",
            label="See budgets",
            params={
                "search": cat.lower(),
                "category": cat.lower(),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Top category ----
    if intent == "top_category_in_period":
        row = (
            db.query(Expense.category, func.sum(Expense.amount).label("total"))
              .filter(Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .group_by(Expense.category)
              .order_by(desc("total"))
              .first()
        )
        if not row:
            return AssistantReply(reply=f"I couldn't find any expenses in {period_label}.", actions=[])
        top_cat, total = row[0], float(row[1] or 0.0)
        reply = f"Your top category in {period_label} is '{top_cat}' at {_euro(total)}."
        actions.append(AssistantAction(
            type="open_expenses", label="See expenses",
            params={"category": top_cat, "start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # Unknown
    return AssistantReply(
        reply='I didn’t quite get that. Try: “How much did I spend on groceries last month?”',
        actions=[]
    )