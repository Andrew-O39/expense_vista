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
    - Returns a human-friendly reply + suggested UI actions
    """
    intent, params = parse_intent(payload.message or "")
    period = params.get("period", "month")
    start, end = period_range(period)
    actions: List[AssistantAction] = []

    def euro(n: float) -> str:
        return f"€{(n or 0):.2f}"

    if intent == "spend_in_category_period":
        cat = (params.get("category") or "").strip().lower()
        if not cat:
            raise HTTPException(status_code=400, detail="Could not detect a category.")

        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user.id,
                Expense.category == cat,
                Expense.created_at >= start,
                Expense.created_at <= end,
            )
            .scalar()
        )
        reply = f"You spent {euro(total)} on {cat} in this {period.replace('_', ' ')}."
        actions.append(AssistantAction(
            type="navigate",
            label="See expenses",
            params={"route": "/expenses", "period": period, "category": cat},
        ))
        return AssistantReply(reply=reply, actions=actions)

    if intent == "spend_in_period":
        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user.id,
                Expense.created_at >= start,
                Expense.created_at <= end,
            )
            .scalar()
        )
        reply = f"You spent {euro(total)} in this {period.replace('_', ' ')}."
        actions.append(AssistantAction(
            type="navigate",
            label="See expenses",
            params={"route": "/expenses", "period": period},
        ))
        return AssistantReply(reply=reply, actions=actions)

    if intent == "income_expense_overview_period":
        inc = (
            db.query(func.coalesce(func.sum(Income.amount), 0.0))
            .filter(
                Income.user_id == user.id,
                Income.created_at >= start,
                Income.created_at <= end,
            )
            .scalar()
        )
        exp = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user.id,
                Expense.created_at >= start,
                Expense.created_at <= end,
            )
            .scalar()
        )
        net = (inc or 0) - (exp or 0)
        reply = f"For this {period.replace('_', ' ')}, income is {euro(inc)}, expenses are {euro(exp)}, net is {euro(net)}."
        actions.append(AssistantAction(
            type="show_chart",
            label="Show Income vs Expenses",
            params={"period": period},
        ))
        return AssistantReply(reply=reply, actions=actions)

    if intent == "on_track_quarter":
        # Simple heuristic: compare spent so far vs average month in quarter
        q_start, q_end = period_range("quarter")
        exp = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user.id,
                Expense.created_at >= q_start,
                Expense.created_at <= q_end,
            )
            .scalar()
        )
        reply = f"So far this quarter, you've spent {euro(exp)}. We can add a proper budget target check later."
        actions.append(AssistantAction(
            type="navigate",
            label="Open Dashboard",
            params={"route": "/dashboard"},
        ))
        return AssistantReply(reply=reply, actions=actions)

    return AssistantReply(reply="I didn’t quite get that. Try asking: “How much did I spend on groceries last month?”", actions=[])