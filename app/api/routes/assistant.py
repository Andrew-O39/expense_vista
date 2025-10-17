from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from unicodedata import normalize as u_norm

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.income import Income
from app.db.models.budget import Budget
from app.core.config import settings
from app.schemas.assistant import AssistantMessage, AssistantReply, AssistantAction
from app.services.nl_interpreter import parse_intent
from app.services.llm_client import llm_complete_json
from app.utils.assistant_dates import period_range

router = APIRouter(prefix="/ai", tags=["AI"])

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

def _pick_budget(db: Session, user_id: int, category: Optional[str], period_key: str, start, end) -> Optional[Budget]:
    period_map = {
        "week": "weekly", "last_week": "weekly",
        "month": "monthly", "last_month": "monthly",
        "quarter": "quarterly", "last_quarter": "quarterly",
        "half_year": "half-yearly", "last_half_year": "half-yearly",
        "year": "yearly", "last_year": "yearly",
    }
    target = period_map.get(period_key, "monthly")

    q = (db.query(Budget)
           .filter(Budget.user_id == user_id,
                   Budget.period == target,
                   Budget.created_at <= end))
    if category:
        q = q.filter(func.lower(Budget.category) == _clean_category(category))
    return q.order_by(desc(Budget.created_at)).first()

def _dispatch_intent(intent: str, params: dict, db: Session, user) -> AssistantReply:
    """Your existing intent handlers factored into one dispatcher."""
    period = params.get("period", "month")
    start, end = period_range(period)
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
        reply = f"You spent {_euro(total)} on {cat} in this {period.replace('_', ' ')}."
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
              .filter(Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .scalar()
        ) or 0.0
        reply = f"You spent {_euro(total)} in this {period.replace('_', ' ')}."
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
        reply = f"Your income this {period.replace('_', ' ')} is {_euro(inc)}."
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
              .filter(Income.user_id == user.id,
                      income_ts >= start,
                      income_ts <= end)
              .scalar()
        ) or 0.0
        exp = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .scalar()
        ) or 0.0
        net = inc - exp
        stance = "surplus" if net >= 0 else "deficit"
        reply = (f"For this {period.replace('_', ' ')}, income is {_euro(inc)}, "
                 f"expenses are {_euro(exp)}, net is {_euro(net)} ({stance}).")
        actions.append(AssistantAction(
            type="show_chart",
            label="Show Income vs Expenses",
            params={"period": period},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Budget status for a category ----
    if intent == "budget_status_category_period":
        cat = _clean_category(params.get("category", ""))
        if not cat:
            raise HTTPException(status_code=400, detail="Could not detect a category.")
        budget = _pick_budget(db, user.id, cat, period, start, end)
        if not budget:
            return AssistantReply(
                reply=f"I couldn’t find a {period.replace('_',' ')} budget for '{cat}'.",
                actions=[]
            )
        spent = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id,
                      func.lower(Expense.category) == cat,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .scalar()
        ) or 0.0
        remaining = (budget.limit_amount or 0) - spent
        status = "under" if remaining >= 0 else "over"
        reply = (f"Your {period.replace('_',' ')} budget for '{cat}' is {_euro(budget.limit_amount or 0)}. "
                 f"You’ve spent {_euro(spent)}, so you are {status} budget by {_euro(abs(remaining))}.")
        actions.append(AssistantAction(
            type="open_budgets",
            label="See budgets",
            params={"search": cat, "category": cat,
                    "start_date": start.isoformat(), "end_date": end.isoformat()},
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
        }
        target = period_map.get(period, "monthly")
        total_budget = (
            db.query(func.coalesce(func.sum(Budget.limit_amount), 0.0))
              .filter(Budget.user_id == user.id,
                      Budget.period == target,
                      Budget.created_at <= end)
              .scalar()
        ) or 0.0
        total_spent = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end)
              .scalar()
        ) or 0.0
        if total_budget == 0.0:
            return AssistantReply(
                reply=f"I couldn’t find any {period.replace('_', ' ')} budgets.",
                actions=[]
            )
        remaining = total_budget - total_spent
        status = "under" if remaining >= 0 else "over"
        reply = (f"Your total {period.replace('_', ' ')} budget is {_euro(total_budget)}. "
                 f"Total spent is {_euro(total_spent)}, so you are {status} budget by {_euro(abs(remaining))}.")
        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Top category in period ----
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
            return AssistantReply(
                reply=f"I couldn't find any expenses in this {period.replace('_', ' ')}.",
                actions=[]
            )
        top_cat, total = row[0], float(row[1] or 0.0)
        reply = f"Your top category this {period.replace('_', ' ')} is '{top_cat}' at {_euro(total)}."
        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={"category": top_cat,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat()},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # Unknown
    return AssistantReply(
        reply="I didn’t quite get that. Try: “How much did I spend on groceries last month?”",
        actions=[]
    )

@router.post("/_intent_debug")
def ai_intent_debug(payload: dict):
    """
    Dev-only: Ask the LLM to interpret the message and return the raw parsed JSON.
    Example:
      curl -X POST http://localhost:8000/ai/_intent_debug -H "Content-Type: application/json" \
           -d '{"message":"How much did I spend on groceries last month?"}'
    """
    if not settings.ai_assistant_enabled or settings.ai_provider != "openai":
        return {"enabled": False, "reason": "AI assistant disabled in settings."}

    msg = (payload.get("message") or "").strip()
    if not msg:
        raise HTTPException(400, "message is required")

    # Use the same prompt schema your assistant uses
    prompt = (
        "Extract a JSON object for a finance question.\n"
        "Allowed intents: ['spend_in_period','spend_in_category_period','budget_status_period',"
        "'budget_status_category_period','income_expense_overview_period','top_category_in_period',"
        "'income_in_period'].\n"
        "Params may include: { 'period'?: str, 'category'?: str }.\n"
        "Respond only with JSON.\n\n"
        f"User: {msg}"
    )
    parsed = llm_complete_json(prompt)
    return {"enabled": True, "model": settings.ai_model or "gpt-4o-mini", "parsed": parsed}


@router.post("/assistant", response_model=AssistantReply)
def ai_assistant(payload: AssistantMessage, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    AI-first: try LLM to interpret {intent, params}. If it fails or is disabled, fall back to rules.
    """
    text = (payload.message or "").strip()

    intent, params = "unknown", {}
    # 1) AI first (if enabled)
    if settings.ai_assistant_enabled and settings.ai_provider == "openai":
        prompt = (
            "Extract a JSON object for a finance question.\n"
            "Allowed intents: ['spend_in_period','spend_in_category_period','budget_status_period',"
            "'budget_status_category_period','income_expense_overview_period','top_category_in_period',"
            "'income_in_period'].\n"
            "Params may include: { 'period'?: str, 'category'?: str }.\n"
            "Respond only with JSON.\n\n"
            f"User: {text}"
        )
        parsed = llm_complete_json(prompt)
        if parsed:
            # normalize aliases here if needed
            alias_map = {
                "budget_status": "budget_status_period",
                "top_category_period": "top_category_in_period",
                # add more if your model uses slightly different names
            }
            i = (parsed.get("intent") or "unknown").lower()
            intent = alias_map.get(i, i)
            params = parsed.get("params") or {}

    # 2) Rules fallback if AI failed or returned unknown/empty
    if intent == "unknown" or not intent:
        intent, params = parse_intent(text)

    # 3) Dispatch to handlers
    return _dispatch_intent(intent, params, db, user)