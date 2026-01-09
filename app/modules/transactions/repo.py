"""Transaction repository for database operations."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.transaction import Transaction


class TransactionRepository:
    """Repository for transaction-related database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, transaction_id: int, user_id: int) -> Optional[Transaction]:
        """Get transaction by ID (user-scoped)."""
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(and_(Transaction.id == transaction_id, Transaction.user_id == user_id))
        )
        return self.db.scalar(stmt)

    def get_all_by_user(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category_id: Optional[int] = None,
        type_filter: Optional[str] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[list[Transaction], Optional[str], bool, int]:
        """
        Get transactions for user with filtering and cursor pagination.

        Returns:
            Tuple of (transactions, next_cursor, has_more, total_count)
        """
        # Base query
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.user_id == user_id)
        )

        # Apply filters
        if start_date:
            stmt = stmt.where(Transaction.occurred_at >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.occurred_at <= end_date)
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
        if type_filter:
            stmt = stmt.where(Transaction.type == type_filter.lower())
        if min_amount is not None:
            stmt = stmt.where(Transaction.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(Transaction.amount <= max_amount)

        # Count total (before cursor filtering)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Cursor pagination
        if cursor:
            try:
                cursor_id = int(cursor)
                stmt = stmt.where(Transaction.id < cursor_id)
            except ValueError:
                pass  # Invalid cursor, ignore it

        # Order by ID descending (newest first) and limit
        stmt = stmt.order_by(desc(Transaction.id)).limit(limit + 1)

        transactions = list(self.db.scalars(stmt).unique().all())

        # Check if there are more items
        has_more = len(transactions) > limit
        if has_more:
            transactions = transactions[:-1]

        # Generate next cursor
        next_cursor = None
        if has_more and transactions:
            next_cursor = str(transactions[-1].id)

        return transactions, next_cursor, has_more, total

    def create(
        self,
        user_id: int,
        amount: Decimal,
        type: str,
        occurred_at: datetime,
        category_id: Optional[int] = None,
        note: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            type=type.lower(),
            occurred_at=occurred_at,
            note=note,
            tags=tags,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        # Reload with category if needed
        if category_id:
            self.db.refresh(transaction)
            # Eager load category
            stmt = (
                select(Transaction)
                .options(joinedload(Transaction.category))
                .where(Transaction.id == transaction.id)
            )
            transaction = self.db.scalar(stmt)
        return transaction

    def update(self, transaction: Transaction) -> Transaction:
        """Update transaction."""
        self.db.commit()
        self.db.refresh(transaction)
        # Reload with category
        stmt = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.id == transaction.id)
        )
        return self.db.scalar(stmt) or transaction

    def delete(self, transaction: Transaction) -> bool:
        """Delete transaction."""
        self.db.delete(transaction)
        self.db.commit()
        return True

    def verify_category_ownership(self, category_id: int, user_id: int) -> bool:
        """Verify that category belongs to user."""
        stmt = select(Category).where(and_(Category.id == category_id, Category.user_id == user_id))
        category = self.db.scalar(stmt)
        return category is not None
