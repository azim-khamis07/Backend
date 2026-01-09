"""Transaction service for business logic."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.transaction import transaction
from app.infra.redis import cache_service
from app.models.transaction import Transaction
from app.modules.transactions.repo import TransactionRepository

logger = get_logger(__name__)


class TransactionService:
    """Service for transaction business logic."""

    def __init__(self, repo: TransactionRepository) -> None:
        """Initialize service with repository."""
        self.repo = repo

    def get_transaction(self, transaction_id: int, user_id: int) -> dict:
        """
        Get transaction by ID.

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for authorization)

        Returns:
            Transaction data

        Raises:
            NotFoundError: If transaction not found
        """
        transaction = self.repo.get_by_id(transaction_id, user_id)
        if not transaction:
            raise NotFoundError("Transaction")

        return self._transaction_to_dict(transaction)

    def list_transactions(
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
    ) -> dict:
        """
        List transactions for a user with filtering and pagination.

        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            category_id: Optional category filter
            type_filter: Optional type filter (expense/income)
            min_amount: Optional minimum amount filter
            max_amount: Optional maximum amount filter
            cursor: Optional cursor for pagination
            limit: Maximum number of records to return

        Returns:
            Paginated transaction list with metadata
        """
        transactions, next_cursor, has_more, total = self.repo.get_all_by_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            type_filter=type_filter,
            min_amount=min_amount,
            max_amount=max_amount,
            cursor=cursor,
            limit=limit,
        )

        items = [self._transaction_to_dict(tx) for tx in transactions]

        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "total": total,
        }

    def create_transaction(
        self,
        db: Session,
        user_id: int,
        amount: Decimal,
        type: str,
        occurred_at: datetime,
        category_id: Optional[int] = None,
        note: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> dict:
        """
        Create a new transaction.

        Args:
            db: Database session
            user_id: User ID
            amount: Transaction amount
            type: Transaction type (expense/income)
            occurred_at: When transaction occurred
            category_id: Optional category ID
            note: Optional note
            tags: Optional comma-separated tags

        Returns:
            Created transaction data

        Raises:
            ValidationError: If validation fails
            NotFoundError: If category not found
        """
        # Validate type
        if type.lower() not in ("expense", "income"):
            raise ValidationError("Transaction type must be 'expense' or 'income'")

        # Validate date (expenses cannot be in the future)
        if type.lower() == "expense":
            now = datetime.now(timezone.utc)
            if occurred_at.tzinfo is None:
                # Assume naive datetime is UTC
                occurred_at = occurred_at.replace(tzinfo=timezone.utc)
            if occurred_at > now:
                raise ValidationError("Expense transactions cannot be in the future")

        # Verify category ownership if provided
        if category_id:
            if not self.repo.verify_category_ownership(category_id, user_id):
                raise NotFoundError(
                    resource="Category",
                    resource_id=category_id,
                    context={"user_id": user_id}
                )

        # Create transaction within a transaction boundary
        with transaction(db):
            transaction_obj = self.repo.create(
                user_id=user_id,
                amount=amount,
                type=type.lower(),
                occurred_at=occurred_at,
                category_id=category_id,
                note=note,
                tags=tags,
            )

        logger.info(
            "Transaction created",
            extra={
                "transaction_id": transaction_obj.id,
                "user_id": user_id,
                "amount": str(amount),
                "type": type.lower(),
            },
        )

        # Invalidate cache for this user's analytics and dashboard
        cache_patterns = [
            f"dashboard:{user_id}:*",
            f"analytics:{user_id}:*",
            f"cashflow:{user_id}:*",
            f"category_breakdown:{user_id}:*",
            f"monthly_summary:{user_id}:*",
        ]
        cache_service.invalidate_patterns(cache_patterns)

        return self._transaction_to_dict(transaction_obj)

    def update_transaction(
        self,
        db: Session,
        transaction_id: int,
        user_id: int,
        amount: Optional[Decimal] = None,
        type: Optional[str] = None,
        category_id: Optional[int] = None,
        occurred_at: Optional[datetime] = None,
        note: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> dict:
        """
        Update transaction.

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for authorization)
            amount: New amount (optional)
            type: New type (optional)
            category_id: New category ID (optional)
            occurred_at: New occurred date (optional)
            note: New note (optional)
            tags: New tags (optional)

        Returns:
            Updated transaction data

        Raises:
            NotFoundError: If transaction or category not found
            ValidationError: If validation fails
        """
        # Get transaction
        transaction = self.repo.get_by_id(transaction_id, user_id)
        if not transaction:
            raise NotFoundError(
                resource="Transaction",
                resource_id=transaction_id,
                context={"user_id": user_id}
            )

        # Validate and update type
        if type is not None:
            type_lower = type.lower()
            if type_lower not in ("expense", "income"):
                raise ValidationError("Transaction type must be 'expense' or 'income'")
            transaction.type = type_lower

        # Validate and update date
        if occurred_at is not None:
            # Normalize timezone
            if occurred_at.tzinfo is None:
                occurred_at = occurred_at.replace(tzinfo=timezone.utc)

            # Validate expense date
            tx_type = type.lower() if type else transaction.type
            if tx_type == "expense":
                now = datetime.now(timezone.utc)
                if occurred_at > now:
                    raise ValidationError("Expense transactions cannot be in the future")
            transaction.occurred_at = occurred_at

        # Validate and update category
        if category_id is not None:
            if category_id != transaction.category_id:  # Only check if changing
                if not self.repo.verify_category_ownership(category_id, user_id):
                    raise NotFoundError(
                        resource="Category",
                        resource_id=category_id,
                        context={"user_id": user_id}
                    )
            transaction.category_id = category_id

        # Update other fields
        if amount is not None:
            transaction.amount = amount
        if note is not None:
            transaction.note = note
        if tags is not None:
            transaction.tags = tags

        # Save changes within a transaction boundary
        with transaction(db):
            transaction = self.repo.update(transaction)

        logger.info(
            "Transaction updated", extra={"transaction_id": transaction_id, "user_id": user_id}
        )

        # Invalidate cache for this user's analytics and dashboard
        cache_patterns = [
            f"dashboard:{user_id}:*",
            f"analytics:{user_id}:*",
            f"cashflow:{user_id}:*",
            f"category_breakdown:{user_id}:*",
            f"monthly_summary:{user_id}:*",
        ]
        cache_service.invalidate_patterns(cache_patterns)

        return self._transaction_to_dict(transaction)

    def delete_transaction(self, db: Session, transaction_id: int, user_id: int) -> dict:
        """
        Delete transaction.

        Args:
            db: Database session
            transaction_id: Transaction ID
            user_id: User ID (for authorization)

        Returns:
            Success message

        Raises:
            NotFoundError: If transaction not found
        """
        # Get transaction
        transaction_obj = self.repo.get_by_id(transaction_id, user_id)
        if not transaction_obj:
            raise NotFoundError(
                resource="Transaction",
                resource_id=transaction_id,
                context={"user_id": user_id}
            )

        # Delete transaction within a transaction boundary
        with transaction(db):
            self.repo.delete(transaction_obj)

        logger.info(
            "Transaction deleted", extra={"transaction_id": transaction_id, "user_id": user_id}
        )

        # Invalidate cache for this user's analytics and dashboard
        cache_patterns = [
            f"dashboard:{user_id}:*",
            f"analytics:{user_id}:*",
            f"cashflow:{user_id}:*",
            f"category_breakdown:{user_id}:*",
            f"monthly_summary:{user_id}:*",
        ]
        cache_service.invalidate_patterns(cache_patterns)

        return {"message": "Transaction deleted successfully"}

    def _transaction_to_dict(self, transaction: Transaction) -> dict:
        """Convert transaction model to dict."""
        return {
            "id": transaction.id,
            "user_id": transaction.user_id,
            "category_id": transaction.category_id,
            "amount": transaction.amount,
            "type": transaction.type,
            "occurred_at": transaction.occurred_at,
            "note": transaction.note,
            "tags": transaction.tags,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            "category": (
                {
                    "id": transaction.category.id,
                    "user_id": transaction.category.user_id,
                    "name": transaction.category.name,
                    "type": transaction.category.type,
                    "description": transaction.category.description,
                    "color": transaction.category.color,
                    "created_at": transaction.category.created_at,
                    "updated_at": transaction.category.updated_at,
                }
                if transaction.category
                else None
            ),
        }
