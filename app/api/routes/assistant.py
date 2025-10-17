from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from unicodedata import normalize as u_norm
from datetime import datetime, timezone

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.income import Income
from app.db.models.budget import Budget
from app.core.config import settings
from app.schemas.assistant import AssistantMessage, AssistantReply, AssistantAction
from app.services.nl_interpreter import parse_intent, PERIOD_ALIASES
from app.services.llm_client import llm_complete_json
from app.utils.assistant_dates import period_range

router = APIRouter(prefix="/ai", tags=["AI"])

# ---------- Helpers ----------

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

def _normalize_period(p: Optional[str]) -> str:
    if not p:
        return "month"
    p = " ".join((p or "").lower().split())
    return PERIOD_ALIASES.get(p, p)

def _resolve_range(params: dict) -> tuple[datetime, datetime, str, str]:
    """
    Prefer explicit start/end from params; otherwise use normalized period.
    Returns (start, end, period_key, period_label_for_reply)
    """
    if "start" in params and "end" in params:
        start = _parse_iso(params["start"])
        end   = _parse_iso(params["end"])
        return start, end, "custom", "period"  # neutral label

    period = _normalize_period(params.get("period"))
    start, end = period_range(period)
    label = period.replace("_", " ")
    return start, end, period, label

def _pick_budget(db: Session, user_id: int, category: Optional[str], period_key: str, end_dt: datetime) -> Optional[Budget]:
    period_map = {
        "week": "weekly", "last_week": "weekly",
        "month": "monthly", "last_month": "monthly",
        "quarter": "quarterly", "last_quarter": "quarterly",
        "half_year": "half-yearly", "last_half_year": "half-yearly",
        "year": "yearly", "last_year": "yearly",
        "custom": "monthly",  # reasonable fallback
    }
    target = period_map.get(period_key, "monthly")

    q = (db.query(Budget)
           .filter(Budget.user_id == user_id,
                   Budget.period == target,
                   Budget.created_at <= end_dt))
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

# ---------- Assistant endpoint (AI-first, rules fallback) ----------

@router.post("/assistant", response_model=AssistantReply)
def ai_assistant(
    payload: AssistantMessage,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    text = (payload.message or "").strip()

    intent, params = "unknown", {}

    # 1) AI first
    if settings.ai_assistant_enabled and settings.ai_provider == "openai":
        try:
            prompt = (
                "You are a finance intent extractor. Respond ONLY with strict JSON.\n"
                "Allowed intents: [\n"
                "  'spend_in_period', 'spend_in_category_period',\n"
                "  'income_expense_overview_period', 'top_category_in_period',\n"
                "  'budget_status_category_period', 'budget_status_period',\n"
                "  'income_in_period'\n"
                "]\n"
                "Params may include: { 'period'?: str, 'category'?: str, 'start'?: str, 'end'?: str }.\n"
                "Use ISO UTC for start/end when the user names months/ranges or says 'since ...'.\n"
                "If start/end are present, omit 'period'. Return ONLY JSON.\n\n"
                f"User: {text}"
            )
            parsed = llm_complete_json(prompt)
            if parsed:
                alias_map = {
                    "budget_status": "budget_status_period",
                    "top_category_period": "top_category_in_period",
                }
                i = (parsed.get("intent") or "unknown").lower()
                intent = alias_map.get(i, i)
                params = parsed.get("params") or {}
        except Exception as e:
            print("LLM parse failed:", e)

    # 2) Rules fallback if AI failed
    if intent == "unknown":
        intent, parsed_params = parse_intent(text)
        # keep any AI-provided start/end if they existed (here they don't, but keeps the pattern)
        params = {**parsed_params, **({} if "start" in params or "end" in params else {})}

    # 3) Resolve the date range ONCE, then pass to handlers
    start, end, period_key, period_label = _resolve_range(params)
    actions: List[AssistantAction] = []

    # ---- Spend in category over a period ----
    if intent == "spend_in_category_period":
        cat = _clean_category(params.get("category", ""))
        if not cat:
            raise HTTPException(status_code=400, detail="Could not detect a category.")
        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(
                  Expense.user_id == user.id,
                  func.lower(Expense.category) == cat,
                  Expense.created_at >= start,
                  Expense.created_at <= end,
              ).scalar()
        ) or 0.0
        reply = f"You spent {_euro(total)} on {cat} in this {period_label}."
        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={
                "search": cat,
                "category": cat,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Spend total over a period ----
    if intent == "spend_in_period":
        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(
                  Expense.user_id == user.id,
                  Expense.created_at >= start,
                  Expense.created_at <= end,
              ).scalar()
        ) or 0.0
        reply = f"You spent {_euro(total)} in this {period_label}."
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
              .filter(
                  Income.user_id == user.id,
                  ts >= start,
                  ts <= end,
              ).scalar()
        ) or 0.0
        reply = f"Your income this {period_label} is {_euro(inc)}."
        actions.append(AssistantAction(
            type="open_incomes",
            label="See incomes",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Income vs expenses over a period ----
    if intent == "income_expense_overview_period":
        income_ts = func.coalesce(Income.received_at, Income.created_at)
        inc = (
            db.query(func.coalesce(func.sum(Income.amount), 0.0))
              .filter(Income.user_id == user.id, income_ts >= start, income_ts <= end)
              .scalar()
        ) or 0.0
        exp = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id, Expense.created_at >= start, Expense.created_at <= end)
              .scalar()
        ) or 0.0
        net = inc - exp
        stance = "surplus" if net >= 0 else "deficit"
        reply = (
            f"For this {period_label}, income is {_euro(inc)}, "
            f"expenses are {_euro(exp)}, net is {_euro(net)} ({stance})."
        )
        actions.append(AssistantAction(type="show_chart", label="Show Income vs Expenses", params={"period": period_key}))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Budget status for a category ----
    if intent == "budget_status_category_period":
        cat = _clean_category(params.get("category", ""))
        if not cat:
            raise HTTPException(status_code=400, detail="Could not detect a category.")
        budget = _pick_budget(db, user.id, cat, period_key, end)
        if not budget:
            return AssistantReply(reply=f"I couldn’t find a {period_label} budget for '{cat}'.", actions=[])
        spent = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id,
                      func.lower(Expense.category) == cat,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .scalar()
        ) or 0.0
        remaining = (budget.limit_amount or 0.0) - spent
        status = "under" if remaining >= 0 else "over"
        reply = (
            f"Your {period_label} budget for '{cat}' is {_euro(budget.limit_amount or 0)}. "
            f"You’ve spent {_euro(spent)}, so you are {status} budget by {_euro(abs(remaining))}."
        )
        actions.append(AssistantAction(
            type="open_budgets",
            label="See budgets",
            params={"search": cat, "category": cat, "start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Budget status overall ----
    if intent == "budget_status_period":
        period_map = {
            "week": "weekly", "last_week": "weekly",
            "month": "monthly", "last_month": "monthly",
            "quarter": "quarterly", "last_quarter": "quarterly",
            "half_year": "half-yearly", "last_half_year": "half-yearly",
            "year": "yearly", "last_year": "yearly",
            "custom": "monthly",
        }
        target = period_map.get(period_key, "monthly")
        total_budget = (
            db.query(func.coalesce(func.sum(Budget.limit_amount), 0.0))
              .filter(Budget.user_id == user.id, Budget.period == target, Budget.created_at <= end)
              .scalar()
        ) or 0.0
        total_spent = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id, Expense.created_at >= start, Expense.created_at <= end)
              .scalar()
        ) or 0.0
        if total_budget == 0.0:
            return AssistantReply(reply=f"I couldn’t find any {period_label} budgets.", actions=[])
        remaining = total_budget - total_spent
        status = "under" if remaining >= 0 else "over"
        reply = (
            f"Your total {period_label} budget is {_euro(total_budget)}. "
            f"Total spent is {_euro(total_spent)}, so you are {status} budget by {_euro(abs(remaining))}."
        )
        actions.append(AssistantAction(type="open_expenses", label="See expenses",
                                       params={"start_date": start.isoformat(), "end_date": end.isoformat()}))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Top category in period ----
    if intent == "top_category_in_period":
        row = (
            db.query(Expense.category, func.sum(Expense.amount).label("total"))
              .filter(Expense.user_id == user.id, Expense.created_at >= start, Expense.created_at <= end)
              .group_by(Expense.category)
              .order_by(desc("total"))
              .first()
        )
        if not row:
            return AssistantReply(reply=f"I couldn't find any expenses in this {period_label}.", actions=[])
        top_cat, total = row[0], float(row[1] or 0.0)
        reply = f"Your top category this {period_label} is '{top_cat}' at {_euro(total)}."
        actions.append(AssistantAction(
            type="open_expenses", label="See expenses",
            params={"category": top_cat, "start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Unknown ----
    return AssistantReply(
        reply="I didn’t quite get that. Try: “How much did I spend on groceries last month?”",
        actions=[]
    )