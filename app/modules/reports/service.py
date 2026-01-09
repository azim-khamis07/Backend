"""Report service for business logic."""

from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.infra.s3 import s3_service
from app.modules.reports.repo import ReportRepository
from app.modules.reports.tasks import generate_pdf_report_task

logger = get_logger(__name__)


class ReportService:
    """Service for report business logic."""

    def __init__(self, repo: ReportRepository) -> None:
        """Initialize service with repository."""
        self.repo = repo

    def create_report_job(self, user_id: int, params: dict) -> dict:
        """
        Create a report generation job.

        Args:
            user_id: User ID
            params: Report parameters

        Returns:
            Report job data

        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate date range
        try:
            start_date = datetime.strptime(params["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(params["end_date"], "%Y-%m-%d")
        except (ValueError, KeyError) as e:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD") from e

        if start_date > end_date:
            raise ValidationError("Start date must be before or equal to end date")

        # Validate transaction types if provided
        if params.get("transaction_types"):
            valid_types = {"expense", "income"}
            provided_types = set(params["transaction_types"])
            if not provided_types.issubset(valid_types):
                raise ValidationError("Transaction types must be 'expense' and/or 'income'")

        # Create report job
        job = self.repo.create(user_id=user_id, params_json=params)

        # Enqueue Celery task
        try:
            generate_pdf_report_task.delay(job.id)
            logger.info(
                "Report job created and enqueued",
                extra={"job_id": job.id, "user_id": user_id},
            )
        except Exception as e:
            # Mark job as failed if enqueue fails
            self.repo.mark_failed(job.id, f"Failed to enqueue job: {str(e)}")
            logger.error(
                "Failed to enqueue report job",
                extra={"job_id": job.id, "user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise ValidationError("Failed to start report generation") from e

        return {
            "job_id": job.id,
            "status": job.status,
            "message": "Report generation started",
        }

    def get_report_status(self, job_id: int, user_id: int) -> dict:
        """
        Get report job status.

        Args:
            job_id: Report job ID
            user_id: User ID (for authorization)

        Returns:
            Report status data

        Raises:
            NotFoundError: If job not found
        """
        job = self.repo.get_by_id(job_id, user_id)
        if not job:
            raise NotFoundError("Report job")

        return {
            "job_id": job.id,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "error_message": job.error_message,
        }

    def get_report_download_url(self, job_id: int, user_id: int, expiration: int = 3600) -> dict:
        """
        Get pre-signed URL for downloading report.

        Args:
            job_id: Report job ID
            user_id: User ID (for authorization)
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Download URL data

        Raises:
            NotFoundError: If job not found
            ValidationError: If job is not completed
        """
        job = self.repo.get_by_id(job_id, user_id)
        if not job:
            raise NotFoundError("Report job")

        if job.status != "completed":
            raise ValidationError(
                f"Report job is {job.status}. Only completed reports can be downloaded."
            )

        if not job.s3_key:
            raise ValidationError("Report file not found")

        # Generate pre-signed URL
        try:
            url = s3_service.generate_presigned_url(job.s3_key, expiration=expiration)
            if not url:
                raise ValidationError("S3 is not configured. Cannot generate download URL.")

            # Generate filename
            filename = f"expense_report_{job.id}.pdf"

            logger.info(
                "Report download URL generated",
                extra={"job_id": job.id, "user_id": user_id},
            )
        except Exception as e:
            logger.error(
                "Failed to generate report download URL",
                extra={"job_id": job.id, "error": str(e)},
                exc_info=True,
            )
            raise ValidationError(f"Failed to generate download URL: {str(e)}") from e

        return {
            "job_id": job.id,
            "url": url,
            "expires_in": expiration,
            "filename": filename,
        }
