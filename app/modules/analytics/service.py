"""Analytics service with Redis caching."""

from datetime import datetime, timedelta
from typing import Optional

from app.core.logging import get_logger
from app.infra.redis import cache_service
from app.modules.analytics.repo import AnalyticsRepository

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics with caching."""

    def __init__(self, repo: AnalyticsRepository, redis_client=None) -> None:
        """Initialize service with repository and optional Redis client."""
        self.repo = repo
        self.redis = redis_client or cache_service

    def _get_cache_key(self, key_type: str, user_id: int, **kwargs) -> str:
        """Generate cache key."""
        parts = [f"analytics:{key_type}", f"user:{user_id}"]
        for key, value in sorted(kwargs.items()):
            if value is not None:
                parts.append(f"{key}:{value}")
        return ":".join(parts)

    def get_dashboard_summary(self, user_id: int, month: Optional[str] = None) -> dict:
        """
        Get dashboard summary for a month.

        Args:
            user_id: User ID
            month: Month in YYYY-MM format (defaults to current month)

        Returns:
            Dashboard summary with top categories
        """
        # Default to current month
        if month is None:
            now = datetime.now()
            year, month_num = now.year, now.month
        else:
            year, month_num = map(int, month.split("-"))

        # Try cache first
        cache_key = self._get_cache_key("dashboard", user_id, month=month)
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug("Cache hit for dashboard summary", extra={"cache_key": cache_key})
                return cached

        # Get monthly summary
        summary = self.repo.get_monthly_summary(user_id, year, month_num)

        # Get top categories
        top_categories = self.repo.get_top_categories(user_id, year, month_num, limit=5)

        result = {
            **summary,
            "top_categories": top_categories,
        }

        # Cache for 5 minutes
        if self.redis:
            self.redis.set(cache_key, result, ttl=300)
            logger.debug("Cached dashboard summary", extra={"cache_key": cache_key})

        return result

    def get_monthly_summary(self, user_id: int, month: str) -> dict:
        """
        Get monthly summary.

        Args:
            user_id: User ID
            month: Month in YYYY-MM format

        Returns:
            Monthly summary
        """
        year, month_num = map(int, month.split("-"))

        # Try cache first
        cache_key = self._get_cache_key("monthly", user_id, month=month)
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug("Cache hit for monthly summary", extra={"cache_key": cache_key})
                return cached

        # Get from database
        result = self.repo.get_monthly_summary(user_id, year, month_num)

        # Cache for 5 minutes
        if self.redis:
            self.redis.set(cache_key, result, ttl=300)
            logger.debug("Cached monthly summary", extra={"cache_key": cache_key})

        return result

    def get_category_breakdown(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get category breakdown.

        Args:
            user_id: User ID
            start_date: Start date (defaults to start of current month)
            end_date: End date (defaults to end of current month)

        Returns:
            Category breakdown
        """
        # Default to current month
        now = datetime.now()
        if start_date is None:
            start_date = datetime(now.year, now.month, 1)
        if end_date is None:
            if now.month == 12:
                end_date = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end_date = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)

        # Try cache first
        cache_key = self._get_cache_key(
            "category_breakdown",
            user_id,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug("Cache hit for category breakdown", extra={"cache_key": cache_key})
                return cached

        # Get from database
        result = self.repo.get_category_breakdown(user_id, start_date, end_date)

        # Cache for 10 minutes
        if self.redis:
            self.redis.set(cache_key, result, ttl=600)
            logger.debug("Cached category breakdown", extra={"cache_key": cache_key})

        return result

    def get_cashflow(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "day",
    ) -> dict:
        """
        Get cashflow data.

        Args:
            user_id: User ID
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to today)
            interval: Interval type (day/week/month)

        Returns:
            Cashflow data
        """
        # Default to last 30 days
        now = datetime.now()
        if end_date is None:
            end_date = now
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Try cache first
        cache_key = self._get_cache_key(
            "cashflow",
            user_id,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            interval=interval,
        )
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug("Cache hit for cashflow", extra={"cache_key": cache_key})
                return cached

        # Get from database
        result = self.repo.get_cashflow(user_id, start_date, end_date, interval)

        # Cache for 10 minutes
        if self.redis:
            self.redis.set(cache_key, result, ttl=600)
            logger.debug("Cached cashflow", extra={"cache_key": cache_key})

        return result

    def invalidate_user_cache(self, user_id: int) -> None:
        """
        Invalidate all analytics cache for a user.

        Args:
            user_id: User ID
        """
        if self.redis:
            pattern = f"analytics:*:user:{user_id}:*"
            self.redis.delete_pattern(pattern)
            logger.info(
                "Invalidated analytics cache", extra={"user_id": user_id, "pattern": pattern}
            )
