"""Report job model for async PDF generation."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin


class ReportJob(Base, TimestampMixin):
    """Report job model for tracking async PDF generation."""

    __tablename__ = "report_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    params_json: Mapped[dict] = mapped_column(
        JSON, nullable=False
    )  # Report parameters (JSONB in PostgreSQL, JSON in SQLite)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, processing, completed, failed
    s3_key: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # S3 key for generated PDF
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="report_jobs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ReportJob(id={self.id}, status={self.status}, user_id={self.user_id})>"
