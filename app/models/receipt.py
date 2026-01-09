"""Receipt model."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Receipt(Base, TimestampMixin):
    """Receipt model."""

    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # Size in bytes
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    transaction: Mapped["Transaction"] = relationship(back_populates="receipt")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Receipt(id={self.id}, transaction_id={self.transaction_id}, s3_key={self.s3_key})>"
        )
