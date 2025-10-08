from typing import Dict, Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SingleCategorySummary(BaseModel):
    """
    Spending summary for a single category over a specified time period.

    Attributes:
        period (str): The time frame for the summary (e.g., 'weekly', 'monthly', 'yearly').
        category (str): The category being summarized.
        total_spent (float): Total amount spent in that category during the period.
    """
    period: str = Field(..., example="monthly", description="Summary period (e.g., 'weekly', 'monthly')")
    category: str = Field(..., example="groceries", description="Category of expenses")
    total_spent: float = Field(..., example=125.50, description="Total spent in this category and period")


class MultiCategorySummary(BaseModel):
    """
    Spending summary grouped by all categories over a specified time period.

    Attributes:
        period (str): The time frame for the summary (e.g., 'weekly', 'monthly', 'yearly').
        summary (Dict[str, float]): Mapping of categories to their total spending.
    """
    period: str = Field(..., example="monthly", description="Summary period (e.g., 'weekly', 'monthly')")
    summary: Dict[str, float] = Field(..., example={"groceries": 200.0, "utilities": 150.0},description="Spending breakdown by category")



class FinancialOverview(BaseModel):
    """
    Unified financial snapshot for a period (and optional category).
    - If `category` is provided: shows totals for that category only.
    - If `category` is omitted: shows totals for all expenses and per-category breakdown.
    """
    period: str
    category: Optional[str] = None
    total_expenses: float
    total_income: float
    net_balance: float  # total_income - total_expenses
    breakdown: Optional[Dict[str, float]] = None  # category -> expense total (only when category not provided)


class GroupBucket(BaseModel):
    """
    Represents a single grouped financial summary bucket.

    Each bucket corresponds to a specific time grouping (e.g., a month, quarter, or half-year)
    and contains the total income, expenses, and resulting net balance for that period.

    Attributes:
        period (str): The label representing the group period.
            Examples:
                - "2025-01" → January 2025 (monthly)
                - "2025-Q1" → First quarter of 2025 (quarterly)
                - "2025-H1" → First half of 2025 (half-yearly)
        total_income (float): Sum of all income recorded within this group period.
        total_expenses (float): Sum of all expenses recorded within this group period.
        net_balance (float): Net result (total_income - total_expenses) for the group period.
    """
    period: str  # e.g. "2025-01", "2025-Q1", "2025-H1"
    total_income: float
    total_expenses: float
    net_balance: float

class FinancialGroupOverview(BaseModel):
    """
    Schema representing grouped financial data summaries over time.

    This model is used to return aggregated income and expense statistics
    grouped by a specific time interval (e.g., weekly, monthly, quarterly, or half-yearly).

    Attributes:
        group_by (Literal["weekly", "monthly", "quarterly", "half-yearly"]):
            Defines the interval used to group financial data.
        start (datetime):
            The start date of the grouping period.
        end (datetime):
            The end date of the grouping period.
        category (Optional[str]):
            Optional filter for a specific expense or income category.
        results (List[GroupBucket]):
            A list of grouped results, where each bucket represents a time
            range containing aggregated totals (e.g., total income, total expenses, net balance).
    """
    group_by: Literal["weekly", "monthly", "quarterly", "half-yearly"]
    start: datetime
    end: datetime
    category: Optional[str] = None
    results: List[GroupBucket]