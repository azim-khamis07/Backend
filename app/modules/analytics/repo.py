"""Analytics repository for aggregation queries."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction


class AnalyticsRepository:
    """Repository for analytics aggregation queries."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_monthly_summary(self, user_id: int, year: int, month: int) -> dict:
        """
        Get monthly summary for a user.

        Args:
            user_id: User ID
            year: Year (e.g., 2026)
            month: Month (1-12)

        Returns:
            Dictionary with summary statistics
        """
        # Calculate date range
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Build query
        stmt = select(
            func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)).label(
                "total_income"
            ),
            func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)).label(
                "total_expenses"
            ),
            func.count(Transaction.id).label("transaction_count"),
            func.sum(case((Transaction.type == "income", 1), else_=0)).label("income_count"),
            func.sum(case((Transaction.type == "expense", 1), else_=0)).label("expense_count"),
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.occurred_at >= start_date,
                Transaction.occurred_at < end_date,
            )
        )

        result = self.db.execute(stmt).one()

        total_income = result.total_income or Decimal("0")
        total_expenses = result.total_expenses or Decimal("0")
        net_amount = total_income - total_expenses

        return {
            "month": f"{year:04d}-{month:02d}",
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_amount": net_amount,
            "transaction_count": result.transaction_count or 0,
            "income_count": result.income_count or 0,
            "expense_count": result.expense_count or 0,
        }

    def get_category_breakdown(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> dict:
        """
        Get category breakdown for a user in a date range.

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with category breakdown
        """
        # Get totals
        totals_stmt = select(
            func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)).label(
                "total_income"
            ),
            func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)).label(
                "total_expenses"
            ),
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.occurred_at >= start_date,
                Transaction.occurred_at <= end_date,
            )
        )
        totals_result = self.db.execute(totals_stmt).one()
        total_income = totals_result.total_income or Decimal("0")
        total_expenses = totals_result.total_expenses or Decimal("0")
        net_amount = total_income - total_expenses

        # Get breakdown by category
        breakdown_stmt = (
            select(
                Transaction.category_id,
                Category.name.label("category_name"),
                Transaction.type,
                func.sum(Transaction.amount).label("total_amount"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .outerjoin(Category, Transaction.category_id == Category.id)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.occurred_at >= start_date,
                    Transaction.occurred_at <= end_date,
                )
            )
            .group_by(Transaction.category_id, Category.name, Transaction.type)
            .order_by(func.sum(Transaction.amount).desc())
        )

        breakdown_results = self.db.execute(breakdown_stmt).all()

        by_category = []
        uncategorized_income = Decimal("0")
        uncategorized_expenses = Decimal("0")

        for row in breakdown_results:
            if row.category_id is None:
                if row.type == "income":
                    uncategorized_income += row.total_amount
                else:
                    uncategorized_expenses += row.total_amount
            else:
                by_category.append(
                    {
                        "category_id": row.category_id,
                        "category_name": row.category_name,
                        "total_amount": row.total_amount,
                        "transaction_count": row.transaction_count,
                        "type": row.type,
                    }
                )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_amount": net_amount,
            "by_category": by_category,
            "uncategorized_income": uncategorized_income,
            "uncategorized_expenses": uncategorized_expenses,
        }

    def get_cashflow(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
    ) -> dict:
        """
        Get cashflow data for a user in a date range.

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date
            interval: Interval type (day/week/month)

        Returns:
            Dictionary with cashflow data
        """
        # Determine date truncation based on interval
        # Use database-specific functions for compatibility (SQLite vs PostgreSQL)
        is_sqlite = "sqlite" in str(self.db.bind.url)

        if is_sqlite:
            # SQLite-compatible date formatting
            if interval == "day":
                date_trunc = func.date(Transaction.occurred_at)
            elif interval == "week":
                # SQLite: Use date() to truncate to day, then we'll handle week grouping in Python
                date_trunc = func.date(Transaction.occurred_at)
            elif interval == "month":
                date_trunc = func.strftime("%Y-%m-01", Transaction.occurred_at)
            else:
                date_trunc = func.date(Transaction.occurred_at)
        else:
            # PostgreSQL date_trunc
            if interval == "day":
                date_trunc = func.date_trunc("day", Transaction.occurred_at)
            elif interval == "week":
                date_trunc = func.date_trunc("week", Transaction.occurred_at)
            elif interval == "month":
                date_trunc = func.date_trunc("month", Transaction.occurred_at)
            else:
                date_trunc = func.date_trunc("day", Transaction.occurred_at)

        # Get totals
        totals_stmt = select(
            func.sum(case((Transaction.type == "income", Transaction.amount), else_=0)).label(
                "total_income"
            ),
            func.sum(case((Transaction.type == "expense", Transaction.amount), else_=0)).label(
                "total_expenses"
            ),
        ).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.occurred_at >= start_date,
                Transaction.occurred_at <= end_date,
            )
        )
        totals_result = self.db.execute(totals_stmt).one()
        total_income = totals_result.total_income or Decimal("0")
        total_expenses = totals_result.total_expenses or Decimal("0")
        net_amount = total_income - total_expenses

        # Get cashflow by interval
        # For SQLite, we need to handle date_trunc differently
        if is_sqlite and interval == "week":
            # SQLite doesn't support week truncation easily, use day and process in Python
            # Get all transactions and group by week in Python
            cashflow_stmt = (
                select(
                    func.date(Transaction.occurred_at).label("period"),
                    func.sum(
                        case((Transaction.type == "income", Transaction.amount), else_=0)
                    ).label("income"),
                    func.sum(
                        case((Transaction.type == "expense", Transaction.amount), else_=0)
                    ).label("expenses"),
                    func.count(Transaction.id).label("transaction_count"),
                )
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.occurred_at >= start_date,
                        Transaction.occurred_at <= end_date,
                    )
                )
                .group_by(func.date(Transaction.occurred_at))
                .order_by(func.date(Transaction.occurred_at))
            )
        else:
            # PostgreSQL or SQLite with day/month interval
            cashflow_stmt = (
                select(
                    date_trunc.label("period"),
                    func.sum(
                        case((Transaction.type == "income", Transaction.amount), else_=0)
                    ).label("income"),
                    func.sum(
                        case((Transaction.type == "expense", Transaction.amount), else_=0)
                    ).label("expenses"),
                    func.count(Transaction.id).label("transaction_count"),
                )
                .where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.occurred_at >= start_date,
                        Transaction.occurred_at <= end_date,
                    )
                )
                .group_by(date_trunc)
                .order_by(date_trunc)
            )

        cashflow_results = self.db.execute(cashflow_stmt).all()

        data = []
        for row in cashflow_results:
            income = row.income or Decimal("0")
            expenses = row.expenses or Decimal("0")
            net = income - expenses

            # Format period based on interval and database
            if is_sqlite:
                # SQLite returns string for date/strftime
                if isinstance(row.period, str):
                    period_str = row.period
                    # For month interval, period_str is already in "YYYY-MM-01" format
                    if interval == "month":
                        period_str = period_str[:7]  # Extract "YYYY-MM"
                else:
                    if hasattr(row.period, "strftime"):
                        period_str = row.period.strftime("%Y-%m-%d")
                    else:
                        period_str = str(row.period)
            else:
                # PostgreSQL returns datetime
                if hasattr(row.period, "strftime"):
                    period_str = row.period.strftime("%Y-%m-%d")
                else:
                    period_str = str(row.period)

            if interval == "week":
                period_str = f"Week of {period_str}"
            elif interval == "month" and not is_sqlite:
                if hasattr(row.period, "strftime"):
                    period_str = row.period.strftime("%Y-%m")
                else:
                    period_str = period_str[:7]

            data.append(
                {
                    "period": period_str,
                    "income": income,
                    "expenses": expenses,
                    "net": net,
                    "transaction_count": row.transaction_count or 0,
                }
            )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_amount": net_amount,
            "data": data,
        }

    def get_top_categories(self, user_id: int, year: int, month: int, limit: int = 5) -> list[dict]:
        """
        Get top spending categories for a month.

        Args:
            user_id: User ID
            year: Year
            month: Month
            limit: Number of top categories to return

        Returns:
            List of top category breakdowns
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        stmt = (
            select(
                Transaction.category_id,
                Category.name.label("category_name"),
                func.sum(Transaction.amount).label("total_amount"),
                func.count(Transaction.id).label("transaction_count"),
                Transaction.type,
            )
            .outerjoin(Category, Transaction.category_id == Category.id)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.occurred_at >= start_date,
                    Transaction.occurred_at < end_date,
                    Transaction.type == "expense",  # Only expenses for top categories
                )
            )
            .group_by(Transaction.category_id, Category.name, Transaction.type)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        )

        results = self.db.execute(stmt).all()

        return [
            {
                "category_id": row.category_id,
                "category_name": row.category_name or "Uncategorized",
                "total_amount": row.total_amount,
                "transaction_count": row.transaction_count,
                "type": row.type,
            }
            for row in results
        ]
