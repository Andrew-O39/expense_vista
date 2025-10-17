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
from typing import Any, Dict


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
    q = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.period.in_(["weekly","monthly","quarterly","half-yearly","yearly"])
    )
    period_map = {
        "week": "weekly", "last_week": "weekly",
        "month": "monthly", "last_month": "monthly",
        "quarter": "quarterly", "last_quarter": "quarterly",
        "half_year": "half-yearly", "last_half_year": "half-yearly",
        "year": "yearly", "last_year": "yearly",
    }
    target = period_map.get(period_key, "monthly")
    q = q.filter(Budget.period == target)
    if category:
        q = q.filter(func.lower(Budget.category) == _clean_category(category))
    q = q.filter(Budget.created_at <= end).order_by(desc(Budget.created_at))
    return q.first()



@router.get("/_ai_health")
def ai_health() -> Dict[str, Any]:
    """Quick toggle check for AI assistant availability."""
    return {
        "assistant_enabled": bool(getattr(settings, "ai_assistant_enabled", False)),
        "provider": getattr(settings, "ai_provider", "none"),
        "model": getattr(settings, "ai_model", None),
        "category_suggestion_enabled": bool(getattr(settings, "ai_category_suggestion_enabled", False)),
    }

@router.post("/_intent_debug")
def intent_debug(payload: AssistantMessage):
    """
    Debug endpoint to see how messages are interpreted.
    Tries LLM JSON intent FIRST (if enabled); if that fails/disabled, falls back to regex parser.
    Returns both the LLM attempt (if any) and the parser result.
    """
    msg = (payload.message or "").strip()

    llm_attempt: Dict[str, Any] | None = None
    llm_used = False
    if getattr(settings, "ai_assistant_enabled", False) and getattr(settings, "ai_provider", "") == "openai":
        try:
            prompt = (
                "Extract a JSON object for a finance question.\n"
                "Allowed intents: ['spend_in_period','spend_in_category_period','budget_status_category_period',"
                "'budget_status_period','income_expense_overview_period','income_in_period','top_category_in_period'].\n"
                "Params may include: { 'period'?: str, 'category'?: str }.\n"
                "Respond only with JSON.\n\n"
                f"User: {msg}"
            )
            llm_attempt = llm_complete_json(prompt)
            llm_used = True
        except Exception as e:
            llm_attempt = {"error": str(e)}

    parsed_intent, parsed_params = parse_intent(msg)

    return {
        "assistant_enabled": bool(getattr(settings, "ai_assistant_enabled", False)),
        "model": getattr(settings, "ai_model", None),
        "llm_used": llm_used,
        "llm_attempt": llm_attempt,              # what the model returned (or error)
        "parser_result": {
            "intent": parsed_intent,
            "params": parsed_params,
        },
        "message": msg,
    }

@router.post("/assistant", response_model=AssistantReply)
def ai_assistant(payload: AssistantMessage, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Hybrid assistant:
    1) Try rule-based intent parsing
    2) If unknown and AI enabled -> ask LLM for a JSON intent
    3) Map AI's intent aliases to our internal intent names and re-dispatch
    """
    def handle_intent(intent: str, params: dict) -> Optional[AssistantReply]:
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
                  .filter(
                      Expense.user_id == user.id,
                      func.lower(Expense.category) == cat,
                      Expense.created_at >= start,
                      Expense.created_at <= end,
                  )
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
                  .filter(
                      Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end,
                  )
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
                  .filter(
                      Income.user_id == user.id,
                      ts >= start,
                      ts <= end,
                  )
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
                  .filter(
                      Income.user_id == user.id,
                      income_ts >= start,
                      income_ts <= end,
                  )
                  .scalar()
            ) or 0.0
            exp = (
                db.query(func.coalesce(func.sum(Expense.amount), 0.0))
                  .filter(
                      Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end,
                  )
                  .scalar()
            ) or 0.0
            net = inc - exp
            stance = "surplus" if net >= 0 else "deficit"
            reply = (
                f"For this {period.replace('_', ' ')}, income is {_euro(inc)}, "
                f"expenses are {_euro(exp)}, net is {_euro(net)} ({stance})."
            )
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
                  .filter(
                      Expense.user_id == user.id,
                      func.lower(Expense.category) == cat,
                      Expense.created_at >= start,
                      Expense.created_at <= end,
                  )
                  .scalar()
            ) or 0.0
            remaining = (budget.limit_amount or 0) - spent
            status = "under" if remaining >= 0 else "over"
            reply = (
                f"Your {period.replace('_',' ')} budget for '{cat}' is {_euro(budget.limit_amount or 0)}. "
                f"You’ve spent {_euro(spent)}, so you are {status} budget by {_euro(abs(remaining))}."
            )
            actions.append(AssistantAction(
                type="open_budgets",
                label="See budgets",
                params={
                    "search": cat,
                    "category": cat,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                },
            ))
            return AssistantReply(reply=reply, actions=actions)

        # ---- Budget status overall (no category) ----
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
                  .filter(
                      Budget.user_id == user.id,
                      Budget.period == target,
                      Budget.created_at <= end,
                  )
                  .scalar()
            ) or 0.0
            total_spent = (
                db.query(func.coalesce(func.sum(Expense.amount), 0.0))
                  .filter(
                      Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end,
                  )
                  .scalar()
            ) or 0.0
            if total_budget == 0.0:
                return AssistantReply(reply=f"I couldn’t find any {period.replace('_', ' ')} budgets.", actions=[])
            remaining = total_budget - total_spent
            status = "under" if remaining >= 0 else "over"
            reply = (
                f"Your total {period.replace('_', ' ')} budget is {_euro(total_budget)}. "
                f"Total spent is {_euro(total_spent)}, so you are {status} budget by {_euro(abs(remaining))}."
            )
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
                  .filter(
                      Expense.user_id == user.id,
                      Expense.created_at >= start,
                      Expense.created_at <= end,
                  )
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
                params={"category": top_cat, "start_date": start.isoformat(), "end_date": end.isoformat()},
            ))
            return AssistantReply(reply=reply, actions=actions)

        # ---- Simple quarterly “on track” placeholder ----
        if intent == "on_track_quarter":
            q_start, q_end = period_range("quarter")
            exp = (
                db.query(func.coalesce(func.sum(Expense.amount), 0.0))
                  .filter(Expense.user_id == user.id, Expense.created_at >= q_start, Expense.created_at <= q_end)
                  .scalar()
            ) or 0.0
            reply = f"So far this quarter, you've spent {_euro(exp)}. We can add a proper budget target check later."
            actions.append(AssistantAction(type="navigate", label="Open Dashboard", params={"route": "/dashboard"}))
            return AssistantReply(reply=reply, actions=actions)

        return None  # not handled

    # 1) Try local parser
    intent, params = parse_intent(payload.message or "")
    handled = handle_intent(intent, params)
    if handled:
        return handled

    # 2) LLM fallback if enabled
    if settings.ai_assistant_enabled and (settings.ai_provider or "").lower() == "openai":
        try:
            prompt = (
                "Extract a JSON object for a finance question.\n"
                "Allowed intents: ['spend_in_period','spend_in_category_period','budget_status_period',"
                "'budget_status_category_period','income_expense_overview_period','top_category_in_period','income_in_period'].\n"
                "Params may include: { 'period'?: str, 'category'?: str }.\n"
                "Respond only with JSON.\n\n"
                f"User: {payload.message}"
            )
            data = llm_complete_json(prompt) or {}
            raw_intent = (data.get("intent") or "").strip().lower()
            new_params = data.get("params") or {}

            # Map common aliases from the LLM to internal handlers
            alias_map = {
                "budget_status": "budget_status_period",
                "top_category_period": "top_category_in_period",
                "total_income_period": "income_in_period",
                # Be tolerant on naming:
                "income_vs_expenses": "income_expense_overview_period",
                "income_vs_spend": "income_expense_overview_period",
                "spend_total_period": "spend_in_period",
                "spend_category_period": "spend_in_category_period",
            }
            mapped_intent = alias_map.get(raw_intent, raw_intent)

            # Re-dispatch
            handled = handle_intent(mapped_intent, new_params)
            if handled:
                return handled

            # If still not handled, try merging params with original
            merged = {**params, **new_params}
            handled = handle_intent(mapped_intent, merged)
            if handled:
                return handled

        except Exception as e:
            # Log but don’t expose sensitive details to the client
            print("LLM fallback failed:", repr(e))

    # 3) Default reply
    return AssistantReply(
        reply='I didn’t quite get that. For example: “How much did I spend on groceries last month?”',
        actions=[]
    )