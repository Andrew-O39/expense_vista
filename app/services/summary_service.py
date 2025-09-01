from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Union, List, Literal
from datetime import datetime, timezone

from app.db.models.expense import Expense
from app.db.models.income import Income
from app.utils.date_utils import get_date_range


def get_spending_summary(
    db: Session,
    user_id: int,
    period: str,
    category: Optional[str] = None
) -> Dict[str, Union[str, float, Dict[str, float]]]:
    """
    Get total spending for a user in a given period.

    - With a category: returns {"category", "total_spent", "period"}
    - Without a category: returns {"period", "summary": {category: amount}}

    Args:
        db: Database session
        user_id: ID of the user
        period: 'weekly', 'monthly', or 'yearly'
        category: Optional category filter

    Returns:
        dict: Spending summary
    """
    today = datetime.utcnow()
    start_date, end_date = get_date_range(today, period)

    query = db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start_date,
        Expense.created_at <= end_date
    )

    if category:
        normalized_category = category.strip().lower()
        total = (
            db.query(func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user_id,
                Expense.category == normalized_category,
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
            .scalar()
        )
        return {
            "category": normalized_category,
            "total_spent": round(total, 2),
            "period": period
        }

    else:
        results = (
            db.query(Expense.category, func.coalesce(func.sum(Expense.amount), 0.0))
            .filter(
                Expense.user_id == user_id,
                Expense.created_at >= start_date,
                Expense.created_at <= end_date
            )
            .group_by(Expense.category)
            .all()
        )

        summary = {category: round(amount, 2) for category, amount in results}
        return {
            "period": period,
            "summary": summary
        }


def get_financial_overview(
    db: Session,
    user_id: int,
    period: str,
    category: Optional[str] = None
) -> Dict:
    """
    Return total income, total expenses, and net balance for the period.
    - If `category` provided: restrict expenses to that category.
    - Income never filters by expense category (it’s global to the user).
    """
    # Date window (UTC-aligned)
    start_date, end_date = get_date_range(datetime.now(timezone.utc), period)

    # --- Expenses ---
    exp_query = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start_date,
        Expense.created_at <= end_date,
    )
    if category:
        exp_query = exp_query.filter(func.lower(Expense.category) == category.strip().lower())
    total_expenses = float(exp_query.scalar() or 0.0)

    # --- Income (always part of overview) ---
    inc_query = db.query(func.coalesce(func.sum(Income.amount), 0.0)).filter(
        Income.user_id == user_id,
        Income.received_at >= start_date,
        Income.received_at <= end_date,
    )
    total_income = float(inc_query.scalar() or 0.0)

    net_balance = round(total_income - total_expenses, 2)

    result: Dict = {
        "period": period,
        "category": category.strip().lower() if isinstance(category, str) else None,
        "total_expenses": round(total_expenses, 2),
        "total_income": round(total_income, 2),
        "net_balance": net_balance,
    }

    # Only add per-category breakdown when no single category is requested
    if not category:
        rows = (
            db.query(Expense.category, func.coalesce(func.sum(Expense.amount), 0.0))
              .filter(
                  Expense.user_id == user_id,
                  Expense.created_at >= start_date,
                  Expense.created_at <= end_date,
              )
              .group_by(Expense.category)
              .all()
        )
        result["breakdown"] = {cat: float(total or 0.0) for cat, total in rows}

    return result


GroupBy = Literal["monthly", "quarterly", "half-yearly"]

def _label_week(ts_col):
    # date_trunc('week', ...) gives the Monday of that ISO week in Postgres
    # IYYY = ISO year, IW = ISO week number (01-53)
    return func.concat(func.to_char(ts_col, "IYYY"), "-W", func.to_char(ts_col, "IW"))

def _label_month(ts_col) -> str:
    # Postgres: YYYY-MM label
    return func.to_char(ts_col, "YYYY-MM")

def _label_quarter(ts_col) -> str:
    # Postgres: YYYY-Qn
    return func.concat(func.to_char(ts_col, "YYYY"), "-Q", func.to_char(func.date_part("quarter", ts_col), "FM9"))

def get_overview_totals(
    db: Session,
    user_id: int,
    period: str,
    category: Optional[str] = None
) -> Dict:
    """Existing behavior: totals + category breakdown for the period."""
    start, end = get_date_range(datetime.now(timezone.utc), period)

    exp_q = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at <= end
    )
    inc_q = db.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.received_at >= start,
        Income.received_at <= end
    )

    if category:
        norm_cat = category.strip().lower()
        exp_q = exp_q.filter(func.lower(Expense.category) == norm_cat)

    total_expenses = float(exp_q.scalar() or 0.0)
    total_income = float(inc_q.scalar() or 0.0)
    net_balance = total_income - total_expenses

    # Breakdown by expense category within the window
    breakdown_rows = db.query(
        Expense.category,
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at <= end
    ).group_by(Expense.category).all()

    breakdown: Dict[str, float] = {c: float(s or 0.0) for c, s in breakdown_rows}

    return {
        "period": period,
        "category": category,
        "total_expenses": total_expenses,
        "total_income": total_income,
        "net_balance": net_balance,
        "breakdown": breakdown
    }

def get_grouped_overview(
    db: Session,
    user_id: int,
    period: str,
    group_by: GroupBy,
    category: Optional[str] = None
) -> Dict:
    """
    Group incomes/expenses within the selected window into monthly, quarterly, or half-yearly buckets.
    """
    start, end = get_date_range(datetime.now(timezone.utc), period)

    # Base filters
    exp_filters = [
        Expense.user_id == user_id,
        Expense.created_at >= start,
        Expense.created_at <= end
    ]
    inc_filters = [
        Income.user_id == user_id,
        Income.received_at >= start,
        Income.received_at <= end
    ]
    if category:
        norm_cat = category.strip().lower()
        exp_filters.append(func.lower(Expense.category) == norm_cat)

    # ---------- choose label ----------
    if group_by == "weekly":
        exp_label = _label_week(Expense.created_at)
        inc_label = _label_week(Income.received_at)
    elif group_by == "monthly":
        exp_label = _label_month(Expense.created_at)
        inc_label = _label_month(Income.received_at)
    elif group_by == "quarterly":
        exp_label = _label_quarter(Expense.created_at)
        inc_label = _label_quarter(Income.received_at)
    elif group_by == "half-yearly":
        exp_label = _label_quarter(Expense.created_at)  # fold later
        inc_label = _label_quarter(Income.received_at)
    else:
        raise ValueError("Unsupported group_by value")

    # ---------- run grouped SUMs ----------
    # Expenses grouped
    exp_rows = db.query(
        exp_label.label("bucket"),
        func.sum(Expense.amount).label("total"),
    ).filter(*exp_filters).group_by("bucket").all()
    exp_map = {r.bucket: float(r.total or 0.0) for r in exp_rows}

    # Incomes grouped
    inc_rows = db.query(
        inc_label.label("bucket"),
        func.sum(Income.amount).label("total"),
    ).filter(*inc_filters).group_by("bucket").all()
    inc_map = {r.bucket: float(r.total or 0.0) for r in inc_rows}

    if group_by != "half-yearly":
        # Merge keys and build buckets directly
        all_keys = sorted(set(exp_map.keys()) | set(inc_map.keys()))
        results = []
        for k in all_keys:
            inc_total = inc_map.get(k, 0.0)
            exp_total = exp_map.get(k, 0.0)
            results.append({
                "period": k,
                "total_income": inc_total,
                "total_expenses": exp_total,
                "net_balance": inc_total - exp_total
            })
        return {
            "group_by": group_by,
            "start": start,
            "end": end,
            "category": category,
            "results": results
        }

    # Half-yearly: fold quarterly (YYYY-Qn) into YYYY-H1 / YYYY-H2
    if group_by == "half-yearly":
        def quarter_to_half(quarter_label: str) -> str:
            year, q = quarter_label.split("-Q")
            return f"{year}-H1" if q in {"1", "2"} else f"{year}-H2"

        half_exp, half_inc = {}, {}
        for k, v in exp_map.items():
            hk = quarter_to_half(k)
            half_exp[hk] = half_exp.get(hk, 0.0) + v
        for k, v in inc_map.items():
            hk = quarter_to_half(k)
            half_inc[hk] = half_inc.get(hk, 0.0) + v

        keys = sorted(set(half_exp) | set(half_inc))
        results = [{
            "period": k,
            "total_income": half_inc.get(k, 0.0),
            "total_expenses": half_exp.get(k, 0.0),
            "net_balance": half_inc.get(k, 0.0) - half_exp.get(k, 0.0),
        } for k in keys]

        return {"group_by": group_by, "start": start, "end": end, "category": category, "results": results}

    # ---------- weekly/monthly/quarterly directly ----------
    keys = sorted(set(exp_map) | set(inc_map))
    results = [{
        "period": k,
        "total_income": inc_map.get(k, 0.0),
        "total_expenses": exp_map.get(k, 0.0),
        "net_balance": inc_map.get(k, 0.0) - exp_map.get(k, 0.0),
    } for k in keys]

    return {"group_by": group_by, "start": start, "end": end, "category": category, "results": results}