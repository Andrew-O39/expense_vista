from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.expense import Expense
from app.db.models.income import Income
from app.db.models.budget import Budget
from app.schemas.assistant import AssistantMessage, AssistantReply, AssistantAction
from app.services.nl_interpreter import parse_intent
from app.utils.assistant_dates import period_range

router = APIRouter(prefix="/ai", tags=["AI"])

def _norm(s: str) -> str:
    # mirror frontend normalization (lower + trim + collapse spaces)
    return " ".join((s or "").lower().strip().split())

def _euro(n: float) -> str:
    return f"€{(n or 0):.2f}"

def _budget_rows_for_period(db, user_id: int, period: str, category: str | None = None) -> list[Budget]:
    q = db.query(Budget).filter(Budget.user_id == user_id, Budget.period == period)
    if category:
        q = q.filter(func.lower(Budget.category) == category.lower())
    return q.all()

def _spent_by_category(db, user_id: int, start, end) -> Dict[str, float]:
    rows = (
        db.query(Expense.category, func.coalesce(func.sum(Expense.amount), 0.0))
        .filter(
            Expense.user_id == user_id,
            Expense.created_at >= start,
            Expense.created_at <= end,
        )
        .group_by(Expense.category)
        .all()
    )
    return { (c or "").lower(): float(total or 0) for (c, total) in rows }

@router.post("/assistant", response_model=AssistantReply)
def ai_assistant(
    payload: AssistantMessage,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    intent, params = parse_intent(payload.message or "")
    period = params.get("period", "month")
    start, end = period_range(period)
    actions: List[AssistantAction] = []

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

    # -------------------- INCOME --------------------
    if intent == "income_in_period":
        q = db.query(func.coalesce(func.sum(Income.amount), 0.0)).filter(
            Income.user_id == user.id,
            Income.created_at >= start,
            Income.created_at <= end,
        )

        source = (params.get("source") or "").strip().lower()
        label = f"in this {period.replace('_', ' ')}"
        if source:
            # try match against source OR category (depending on how you store it)
            q = q.filter(
                func.lower(Income.source) == source
            )
            label = f"from {source} {label}"

        total_inc = q.scalar()
        reply = f"Your income {label} is {_euro(total_inc)}."

        actions.append(AssistantAction(
            type="open_incomes",
            label="See incomes",
            params={
                # show the same filter in the list
                "search": source or None,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
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
        period_label = period.replace("_", " ")

        # Friendlier summary (surplus/deficit)
        if net >= 0:
            net_phrase = f"leaving a surplus of {_euro(net)}"
        else:
            net_phrase = f"leaving a deficit of {_euro(abs(net))}"

        reply = (
            f"For this {period_label}, income is {_euro(inc)} and expenses are {_euro(exp)}, "
            f"{net_phrase}."
        )

        # Actions: open filtered incomes/expenses immediately, plus a chart hook
        actions.append(AssistantAction(
            type="open_expenses",
            label="See expenses",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                # optional: you could also include "search" or "category" here later
            },
        ))
        actions.append(AssistantAction(
            type="open_incomes",
            label="See incomes",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        ))
        actions.append(AssistantAction(
            type="show_chart",
            label="Show Income vs Expenses",
            params={
                "period": period,  # keep period for charting
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
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

        reply = (
            f"So far this quarter, you've spent {_euro(exp)}. "
            f"We can add a proper budget target check later."
        )
        actions.append(AssistantAction(
            type="open_expenses",
            label="See this quarter’s expenses",
            params={
                "start_date": q_start.isoformat(),
                "end_date": q_end.isoformat(),
            },
        ))
        actions.append(AssistantAction(
            type="navigate",
            label="Open Dashboard",
            params={"route": "/dashboard"},
        ))
        return AssistantReply(reply=reply, actions=actions)

    # ===== Status for a specific category vs budget =====
    if intent == "budget_status_category_period":
        cat = (params.get("category") or "").strip().lower()
        if not cat:
            return AssistantReply(
                reply="Which category did you mean? For example: “Am I on track for groceries this month?”",
                actions=[]
            )

        budgets = _budget_rows_for_period(db, user.id, period, cat)
        if not budgets:
            return AssistantReply(
                reply=f"You don't have a {period} budget set for “{cat}”.",
                actions=[AssistantAction(type="navigate", label="Open Budgets", params={"route": "/budgets"})]
            )

        # If multiple budgets for same category/period exist, sum them (rare but safe)
        budget_limit = sum(float(b.limit_amount or 0) for b in budgets)

        spent_map = _spent_by_category(db, user.id, start, end)
        spent = spent_map.get(cat, 0.0)
        remaining = budget_limit - spent
        status = "on track" if remaining >= 0 else "over budget"

        reply = (
            f"For {cat} this {period.replace('_', ' ')}, your budget is {_euro(budget_limit)}. "
            f"You've spent {_euro(spent)}, so you have {_euro(abs(remaining))} "
            f"{'remaining' if remaining >= 0 else 'over'} — you’re {status}."
        )

        actions.extend([
            AssistantAction(
                type="open_expenses",
                label="See expenses",
                params={
                    "search": cat,  # ExpenseList will treat as search
                    "category": cat,  # and also as category filter
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "page": 1, "limit": 10,
                },
            ),
            AssistantAction(
                type="navigate",
                label="Open Budgets",
                params={"route": "/budgets", "period": period, "category": cat},
            ),
        ])
        return AssistantReply(reply=reply, actions=actions)

    # ===== Overview of all budgets for a period =====
    if intent == "budgets_overview_period":
        budgets = _budget_rows_for_period(db, user.id, period)
        if not budgets:
            return AssistantReply(
                reply=f"You have no {period} budgets yet.",
                actions=[AssistantAction(type="navigate", label="Create a budget", params={"route": "/create-budget"})]
            )

        spent_map = _spent_by_category(db, user.id, start, end)
        lines = []
        overs = []

        for b in budgets:
            cat = (b.category or "").lower()
            limit_amt = float(b.limit_amount or 0)
            s = float(spent_map.get(cat, 0.0))
            left = limit_amt - s
            lines.append(
                f"• {cat}: {_euro(s)} / {_euro(limit_amt)} ({'left ' + _euro(left) if left >= 0 else 'over ' + _euro(-left)})")
            if left < 0:
                overs.append(cat)

        reply = "Budget status:\n" + "\n".join(lines)
        if overs:
            reply += f"\n\nOver budget: {', '.join(overs)}."

        actions.append(AssistantAction(type="navigate", label="Open Budgets", params={"route": "/budgets"}))
        return AssistantReply(reply=reply, actions=actions)

    # ===== Which budgets are overspent this period =====
    if intent == "budgets_overspent_period":
        budgets = _budget_rows_for_period(db, user.id, period)
        if not budgets:
            return AssistantReply(
                reply=f"You have no {period} budgets yet.",
                actions=[AssistantAction(type="navigate", label="Create a budget", params={"route": "/create-budget"})]
            )

        spent_map = _spent_by_category(db, user.id, start, end)
        overs = []
        for b in budgets:
            cat = (b.category or "").lower()
            limit_amt = float(b.limit_amount or 0)
            s = float(spent_map.get(cat, 0.0))
            if s > limit_amt:
                overs.append((cat, s, limit_amt))

        if not overs:
            return AssistantReply(
                reply=f"No budgets are overspent this {period.replace('_', ' ')}. Nice!",
                actions=[AssistantAction(type="navigate", label="Open Budgets", params={"route": "/budgets"})]
            )

        # Build reply + actions to jump to each category’s expenses
        lines = [f"• {cat}: {_euro(s)} vs {_euro(limit_amt)} (over {_euro(s - limit_amt)})" for (cat, s, limit_amt) in
                 overs]
        reply = "Overspent budgets:\n" + "\n".join(lines)

        # Offer up to 3 quick action buttons
        for (cat, _, _) in overs[:3]:
            actions.append(AssistantAction(
                type="open_expenses",
                label=f"See {cat}",
                params={
                    "search": cat,
                    "category": cat,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "page": 1, "limit": 10,
                },
            ))

        return AssistantReply(reply=reply, actions=actions)

    # ===== Fallback =====
    return AssistantReply(
        reply="I didn’t quite get that. Try: “Am I on track for groceries this month?” or “Which budgets are over budget this month?”",
        actions=[]
    )