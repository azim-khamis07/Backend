"""Analytics and dashboard schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MonthlySummaryResponse(BaseModel):
    """Monthly summary response schema."""

    month: str = Field(..., description="Month in YYYY-MM format")
    total_income: Decimal = Field(..., description="Total income for the month")
    total_expenses: Decimal = Field(..., description="Total expenses for the month")
    net_amount: Decimal = Field(..., description="Net amount (income - expenses)")
    transaction_count: int = Field(..., description="Total number of transactions")
    income_count: int = Field(..., description="Number of income transactions")
    expense_count: int = Field(..., description="Number of expense transactions")


class CategoryBreakdownItem(BaseModel):
    """Category breakdown item schema."""

    category_id: Optional[int] = Field(None, description="Category ID")
    category_name: Optional[str] = Field(None, description="Category name")
    total_amount: Decimal = Field(..., description="Total amount for this category")
    transaction_count: int = Field(..., description="Number of transactions")
    type: str = Field(..., description="Transaction type (expense/income)")


class CategoryBreakdownResponse(BaseModel):
    """Category breakdown response schema."""

    start_date: datetime = Field(..., description="Start date of the period")
    end_date: datetime = Field(..., description="End date of the period")
    total_income: Decimal = Field(..., description="Total income in period")
    total_expenses: Decimal = Field(..., description="Total expenses in period")
    net_amount: Decimal = Field(..., description="Net amount (income - expenses)")
    by_category: list[CategoryBreakdownItem] = Field(..., description="Breakdown by category")
    uncategorized_income: Decimal = Field(
        default=Decimal("0"), description="Income without category"
    )
    uncategorized_expenses: Decimal = Field(
        default=Decimal("0"), description="Expenses without category"
    )


class CashflowItem(BaseModel):
    """Cashflow item schema."""

    period: str = Field(..., description="Period identifier (date string)")
    income: Decimal = Field(..., description="Income for this period")
    expenses: Decimal = Field(..., description="Expenses for this period")
    net: Decimal = Field(..., description="Net amount (income - expenses)")
    transaction_count: int = Field(..., description="Number of transactions")


class CashflowResponse(BaseModel):
    """Cashflow response schema."""

    start_date: datetime = Field(..., description="Start date of the period")
    end_date: datetime = Field(..., description="End date of the period")
    interval: str = Field(..., description="Interval type (day/week/month)")
    total_income: Decimal = Field(..., description="Total income in period")
    total_expenses: Decimal = Field(..., description="Total expenses in period")
    net_amount: Decimal = Field(..., description="Net amount (income - expenses)")
    data: list[CashflowItem] = Field(..., description="Cashflow data points")


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response schema."""

    month: str = Field(..., description="Month in YYYY-MM format")
    total_income: Decimal = Field(..., description="Total income for the month")
    total_expenses: Decimal = Field(..., description="Total expenses for the month")
    net_amount: Decimal = Field(..., description="Net amount (income - expenses)")
    transaction_count: int = Field(..., description="Total number of transactions")
    income_count: int = Field(..., description="Number of income transactions")
    expense_count: int = Field(..., description="Number of expense transactions")
    top_categories: list[CategoryBreakdownItem] = Field(
        default_factory=list, description="Top spending categories"
    )


class AnalyticsFilters(BaseModel):
    """Analytics filter parameters."""

    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    month: Optional[str] = Field(
        None, pattern="^\\d{4}-\\d{2}$", description="Month in YYYY-MM format"
    )
    interval: Optional[str] = Field(
        None, pattern="^(day|week|month)$", description="Interval for cashflow (day/week/month)"
    )

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate date range."""
        if "start_date" in info.data and "end_date" in info.data:
            start = info.data.get("start_date")
            end = info.data.get("end_date")
            if start and end and start > end:
                raise ValueError("start_date must be before end_date")
        return v

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: Optional[str]) -> Optional[str]:
        """Normalize interval."""
        if v is not None:
            return v.lower()
        return v
