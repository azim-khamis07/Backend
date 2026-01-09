"""Report repository for database operations."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.report_job import ReportJob


class ReportRepository:
    """Repository for report job database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def create(
        self,
        user_id: int,
        params_json: dict,
        status: str = "pending",
    ) -> ReportJob:
        """
        Create a new report job.

        Args:
            user_id: User ID
            params_json: Report parameters (JSON)
            status: Initial status (default: pending)

        Returns:
            Created report job
        """
        job = ReportJob(
            user_id=user_id,
            params_json=params_json,
            status=status,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_id(self, job_id: int, user_id: int) -> Optional[ReportJob]:
        """
        Get report job by ID (user-scoped).

        Args:
            job_id: Report job ID
            user_id: User ID (for authorization)

        Returns:
            Report job if found and belongs to user, None otherwise
        """
        stmt = select(ReportJob).where(ReportJob.id == job_id, ReportJob.user_id == user_id)
        return self.db.scalar(stmt)

    def update_status(
        self,
        job_id: int,
        status: str,
        s3_key: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ReportJob]:
        """
        Update report job status.

        Args:
            job_id: Report job ID
            status: New status
            s3_key: S3 key for generated PDF (optional)
            error_message: Error message if failed (optional)

        Returns:
            Updated report job
        """
        job = self.db.get(ReportJob, job_id)
        if not job:
            return None

        job.status = status
        if s3_key:
            job.s3_key = s3_key
        if error_message:
            job.error_message = error_message

        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_started(self, job_id: int) -> Optional[ReportJob]:
        """
        Mark report job as started.

        Args:
            job_id: Report job ID

        Returns:
            Updated report job
        """
        from datetime import datetime, timezone

        job = self.db.get(ReportJob, job_id)
        if not job:
            return None

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_completed(self, job_id: int, s3_key: str) -> Optional[ReportJob]:
        """
        Mark report job as completed.

        Args:
            job_id: Report job ID
            s3_key: S3 key for generated PDF

        Returns:
            Updated report job
        """
        from datetime import datetime, timezone

        job = self.db.get(ReportJob, job_id)
        if not job:
            return None

        job.status = "completed"
        job.s3_key = s3_key
        job.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_failed(self, job_id: int, error_message: str) -> Optional[ReportJob]:
        """
        Mark report job as failed.

        Args:
            job_id: Report job ID
            error_message: Error message

        Returns:
            Updated report job
        """
        from datetime import datetime, timezone

        job = self.db.get(ReportJob, job_id)
        if not job:
            return None

        job.status = "failed"
        job.error_message = error_message
        job.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ReportJob], int]:
        """
        List report jobs for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (report jobs list, total count)
        """
        # Get total count
        count_stmt = select(func.count(ReportJob.id)).where(ReportJob.user_id == user_id)
        total = self.db.scalar(count_stmt) or 0

        # Get jobs
        stmt = (
            select(ReportJob)
            .where(ReportJob.user_id == user_id)
            .order_by(ReportJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        jobs = list(self.db.scalars(stmt).all())

        return jobs, total
