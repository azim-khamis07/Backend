"""Analytics router endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.infra.redis import cache_service
from app.modules.analytics.repo import AnalyticsRepository
from app.modules.analytics.schemas import (
    CashflowResponse,
    CategoryBreakdownResponse,
    DashboardSummaryResponse,
    MonthlySummaryResponse,
)
from app.modules.analytics.service import AnalyticsService
from app.modules.auth.router import get_current_user_id

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(
    db: Session = Depends(get_db),
) -> AnalyticsService:
    """Dependency to get analytics service."""
    repo = AnalyticsRepository(db)
    return AnalyticsService(repo, cache_service)


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    month: Optional[str] = Query(
        None,
        pattern="^\\d{4}-\\d{2}$",
        description="Month in YYYY-MM format (defaults to current month)",
    ),
    user_id: int = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
) -> DashboardSummaryResponse:
    """
    Get dashboard summary for a month.

    Returns:
        Dashboard summary with top categories
    """
    result = service.get_dashboard_summary(user_id, month)
    return DashboardSummaryResponse(**result)


@router.get("/monthly", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    month: str = Query(..., pattern="^\\d{4}-\\d{2}$", description="Month in YYYY-MM format"),
    user_id: int = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
) -> MonthlySummaryResponse:
    """
    Get monthly summary.

    Returns:
        Monthly summary statistics
    """
    result = service.get_monthly_summary(user_id, month)
    return MonthlySummaryResponse(**result)


@router.get("/by-category", response_model=CategoryBreakdownResponse)
async def get_category_breakdown(
    start_date: Optional[datetime] = Query(
        None, description="Start date (defaults to start of current month)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date (defaults to end of current month)"
    ),
    user_id: int = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
) -> CategoryBreakdownResponse:
    """
    Get category breakdown for a date range.

    Returns:
        Category breakdown with totals
    """
    result = service.get_category_breakdown(user_id, start_date, end_date)
    return CategoryBreakdownResponse(**result)


@router.get("/cashflow", response_model=CashflowResponse)
async def get_cashflow(
    start_date: Optional[datetime] = Query(
        None, description="Start date (defaults to 30 days ago)"
    ),
    end_date: Optional[datetime] = Query(None, description="End date (defaults to today)"),
    interval: str = Query(
        "day", pattern="^(day|week|month)$", description="Interval type (day/week/month)"
    ),
    user_id: int = Depends(get_current_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
) -> CashflowResponse:
    """
    Get cashflow data for a date range.

    Returns:
        Cashflow data with interval breakdown
    """
    result = service.get_cashflow(user_id, start_date, end_date, interval)
    return CashflowResponse(**result)
