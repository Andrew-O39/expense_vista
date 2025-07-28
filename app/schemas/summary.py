from typing import Dict
from pydantic import BaseModel, Field


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