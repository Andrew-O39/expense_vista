from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Union, Literal
from datetime import datetime, timezone

from app.api.deps import get_current_user
from app.db.session import get_db
from app.utils.date_utils import get_date_range
from app.schemas.summary import SingleCategorySummary, MultiCategorySummary, FinancialOverview, FinancialGroupOverview
from app.services.summary_service import get_spending_summary, get_overview_totals, get_grouped_overview
from app.db.models.user import User
from app.db.models.expense import Expense


router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get("/", response_model=Union[SingleCategorySummary, MultiCategorySummary])
def get_spending_summary(
    period: str = Query(..., description="Time period to summarize ('weekly', 'monthly', or 'yearly')"),
    category: Optional[str] = Query(None, description="Optional category to filter by"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a summary of user spending for a given time period.

    - If a `category` is provided, returns the total spending in that category during the specified period.
    - If `category` is not provided, returns total spending grouped by category for that period.

    Examples:
    - `/summary?period=monthly` → multi-category summary
    - `/summary?period=monthly&category=groceries` → single-category summary
    """
    start_date, end_date = get_date_range(datetime.now(timezone.utc), period)

    if category:
        normalized_category = category.strip().lower()

        total_spent = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            func.lower(Expense.category) == normalized_category,
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).scalar() or 0.0

        return SingleCategorySummary(
            period=period,
            category=normalized_category,
            total_spent=total_spent
        )

    else:
        results = db.query(
            Expense.category,
            func.sum(Expense.amount)
        ).filter(
            Expense.user_id == current_user.id,
            Expense.created_at >= start_date,
            Expense.created_at <= end_date
        ).group_by(Expense.category).all()

        summary_data = {cat: float(total or 0.0) for cat, total in results}

        return MultiCategorySummary(
            period=period,
            summary=summary_data
        )


@router.get(
    "/overview",
    response_model=Union[FinancialOverview, FinancialGroupOverview],
    summary="Get financial overview or grouped snapshots",
)
def get_overview(
    period: str = Query(..., description="Window to analyze: 'weekly', 'monthly', or 'yearly'."),
    group_by: Optional[Literal["weekly", "monthly", "quarterly", "half-yearly"]] = Query(
        None, description="Bucket results by week, month, quarter, or half-year."
    ),
    category: Optional[str] = Query(None, description="Optional category filter for expenses."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    📊 **Financial Overview Endpoint**

    This endpoint provides a **summary of income, expenses, and net balance**
    for the current user.

    - **Without `group_by`** → returns a one-time snapshot:
        - If `category` is provided → shows totals for that category only.
        - If no `category` → shows totals across all categories.

    - **With `group_by`** → returns a **time series** of snapshots:
        - Useful for quarterly, half-yearly, or yearly trend analysis.
        - Each entry includes income, expenses, net balance for that period.

    ### Parameters
    - `period` (required): Defines the overall time window (e.g. `monthly`, `quarterly`, `yearly`).
    - `category` (optional): Restrict summary to a specific category (e.g. `housing`, `groceries`).
    - `group_by` (optional): Break down results by time intervals (`weekly`, `monthly`, `quarterly`, `yearly`).

    ### Example Responses
    **Snapshot (no group_by):**
    ```json
    {
      "period": "yearly",
      "category": null,
      "total_expenses": 2754,
      "total_income": 3100,
      "net_balance": 346,
      "breakdown": {
        "school": 400,
        "housing": 1470,
        "groceries": 229,
        "electronics": 500,
        "utilities": 55,
        "transport": 100
      }
    }
    ```

    **Time series (with group_by=monthly):**
    ```json
    {
      "period": "yearly",
      "group_by": "monthly",
      "series": [
        {
          "period": "2025-01",
          "total_expenses": 500,
          "total_income": 1000,
          "net_balance": 500
        },
        {
          "period": "2025-02",
          "total_expenses": 700,
          "total_income": 1200,
          "net_balance": 500
        }
      ]
    }
    ```
    """
    period = period.strip().lower()
    if group_by:
        return get_grouped_overview(db, current_user.id, period, group_by, category)
    return get_overview_totals(db, current_user.id, period, category)



