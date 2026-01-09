"""Receipt repository for database operations."""

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.transaction import Transaction


class ReceiptRepository:
    """Repository for receipt-related database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, receipt_id: int, user_id: int) -> Optional[Receipt]:
        """
        Get receipt by ID (user-scoped via transaction).

        Args:
            receipt_id: Receipt ID
            user_id: User ID (for authorization)

        Returns:
            Receipt if found and user owns the transaction, None otherwise
        """
        stmt = (
            select(Receipt)
            .join(Transaction, Receipt.transaction_id == Transaction.id)
            .where(and_(Receipt.id == receipt_id, Transaction.user_id == user_id))
        )
        return self.db.scalar(stmt)

    def get_by_transaction_id(self, transaction_id: int, user_id: int) -> Optional[Receipt]:
        """
        Get receipt by transaction ID (user-scoped).

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for authorization)

        Returns:
            Receipt if found and user owns the transaction, None otherwise
        """
        stmt = (
            select(Receipt)
            .join(Transaction, Receipt.transaction_id == Transaction.id)
            .where(and_(Receipt.transaction_id == transaction_id, Transaction.user_id == user_id))
        )
        return self.db.scalar(stmt)

    def create(
        self,
        transaction_id: int,
        s3_key: str,
        content_type: str,
        size: int,
    ) -> Receipt:
        """
        Create a new receipt record.

        Args:
            transaction_id: Transaction ID
            s3_key: S3 object key
            content_type: File content type (MIME type)
            size: File size in bytes

        Returns:
            Created receipt
        """
        receipt = Receipt(
            transaction_id=transaction_id,
            s3_key=s3_key,
            content_type=content_type,
            size=size,
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def delete(self, receipt: Receipt) -> bool:
        """
        Delete receipt record.

        Args:
            receipt: Receipt to delete

        Returns:
            True if deleted
        """
        self.db.delete(receipt)
        self.db.commit()
        return True

    def verify_transaction_ownership(self, transaction_id: int, user_id: int) -> bool:
        """
        Verify that transaction belongs to user.

        Args:
            transaction_id: Transaction ID
            user_id: User ID

        Returns:
            True if user owns the transaction
        """
        stmt = select(Transaction).where(
            and_(Transaction.id == transaction_id, Transaction.user_id == user_id)
        )
        transaction = self.db.scalar(stmt)
        return transaction is not None
