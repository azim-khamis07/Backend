"""Transaction model."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.receipt import Receipt
    from app.models.user import User


class Transaction(Base, TimestampMixin):
    """Transaction model."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "expense" or "income"
    occurred_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Comma-separated tags

    # Relationships
    user: Mapped["User"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")
    receipt: Mapped["Receipt | None"] = relationship(
        back_populates="transaction", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
        CheckConstraint("type IN ('expense', 'income')", name="check_type_valid"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.type})>"
