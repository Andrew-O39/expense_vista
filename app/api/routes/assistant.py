from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.income import Income
from app.schemas.assistant import AssistantMessage, AssistantReply, AssistantAction
from app.services.nl_interpreter import parse_intent
from app.utils.assistant_dates import period_range

router = APIRouter(prefix="/ai", tags=["AI"])

def _norm(s: str) -> str:
    # mirror frontend normalization (lower + trim + collapse spaces)
    return " ".join((s or "").lower().strip().split())

def _euro(n: float) -> str:
    return f"€{(n or 0):.2f}"

@router.post("/assistant", response_model=AssistantReply)
def ai_assistant(
    payload: AssistantMessage,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Natural-language assistant MVP:
    - Parses period + optional category from text
    - Computes figures using existing ORM models
    - Returns a human-friendly reply + UI actions that the frontend can navigate with
    """
    intent, params = parse_intent(payload.message or "")
    period = params.get("period", "month")
    start, end = period_range(period)
    actions: List[AssistantAction] = []

    # ---- Spend in a specific category over a period ----
    if intent == "spend_in_category_period":
        raw_cat = (params.get("category") or "").strip()
        cat_norm = _norm(raw_cat)
        if not cat_norm:
            raise HTTPException(status_code=400, detail="Could not detect a category.")

        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user.id,
                func.lower(Expense.category) == cat_norm,   # <-- normalize compare
                Expense.created_at >= start,
                Expense.created_at <= end,
            )
            .scalar()
        ) or 0.0

        reply = f"You spent {_euro(total)} on {raw_cat or cat_norm} this {period.replace('_', ' ')}."

        # return EXACT params ExpenseList understands via the assistant action
        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={
                "search": cat_norm,                    # ExpenseList treats category as search anyway
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "page": 1,
                "limit": 10,
            },
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Spend (all categories) over a period ----
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

        reply = f"You spent {_euro(total)} this {period.replace('_', ' ')}."

        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "page": 1,
                "limit": 10,
            },
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Income vs expenses over a period ----
    if intent == "income_expense_overview_period":
        inc = (
            db.query(func.coalesce(func.sum(Income.amount), 0.0))
            .filter(
                Income.user_id == user.id,
                Income.created_at >= start,
                Income.created_at <= end,
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
        reply = (
            f"For this {period.replace('_', ' ')}, income is {_euro(inc)}, "
            f"expenses are {_euro(exp)}, net is {_euro(net)}."
        )

        actions.append(AssistantAction(
            type="show_chart",
            label="Show Income vs Expenses",
            params={"period": period},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ---- Simple quarterly “on track” placeholder ----
    if intent == "on_track_quarter":
        q_start, q_end = period_range("quarter")
        exp = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user.id,
                Expense.created_at >= q_start,
                Expense.created_at <= q_end,
            )
            .scalar()
        ) or 0.0

        reply = f"So far this quarter, you've spent {_euro(exp)}. We can add a proper budget target check later."
        actions.append(AssistantAction(
            type="navigate",
            label="Open Dashboard",
            params={"route": "/dashboard"},
        ))
        return AssistantReply(reply=reply, actions=actions)

    return AssistantReply(
        reply="I didn’t quite get that. Try: “How much did I spend on groceries last month?”",
        actions=[]
    )