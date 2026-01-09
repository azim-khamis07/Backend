"""Report router endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.rate_limit import get_rate_limiter
from app.db.session import get_db
from app.modules.auth.router import get_current_user_id
from app.modules.reports.repo import ReportRepository
from app.modules.reports.schemas import (
    ReportCreateResponse,
    ReportDownloadResponse,
    ReportRequest,
    ReportStatusResponse,
)
from app.modules.reports.service import ReportService

limiter = get_rate_limiter()

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Dependency to get report service."""
    repo = ReportRepository(db)
    return ReportService(repo)


@router.post(
    "/pdf",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReportCreateResponse,
)
@limiter.limit("10/hour")  # Limit report generation
async def create_report(
    http_request: Request,
    request: ReportRequest,
    user_id: int = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
) -> ReportCreateResponse:
    """
    Create a PDF report generation job.

    **Parameters:**
    - `start_date`: Start date (YYYY-MM-DD)
    - `end_date`: End date (YYYY-MM-DD)
    - `category_ids`: Optional list of category IDs to filter
    - `include_receipts`: Whether to include receipt information (optional)
    - `transaction_types`: Optional list of types: ["expense", "income"]

    **Returns:**
    - Job ID and status
    - Use the job ID to check status and download the report

    **Note:** Report generation is asynchronous. Check status using the job ID.
    """
    params = request.model_dump()
    result = service.create_report_job(user_id=user_id, params=params)
    return ReportCreateResponse(**result)


@router.get(
    "/{job_id}/status",
    response_model=ReportStatusResponse,
)
async def get_report_status(
    job_id: int,
    user_id: int = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
) -> ReportStatusResponse:
    """
    Get report generation status.

    **Status Values:**
    - `pending`: Job is queued, waiting to start
    - `processing`: Report is being generated
    - `completed`: Report is ready for download
    - `failed`: Report generation failed (check error_message)

    Returns:
        Report job status and metadata
    """
    status_data = service.get_report_status(job_id=job_id, user_id=user_id)
    return ReportStatusResponse(**status_data)


@router.get(
    "/{job_id}/download",
    response_model=ReportDownloadResponse,
)
async def download_report(
    job_id: int,
    expiration: int = Query(
        default=3600, ge=60, le=604800, description="URL expiration in seconds (60-604800)"
    ),
    user_id: int = Depends(get_current_user_id),
    service: ReportService = Depends(get_report_service),
) -> ReportDownloadResponse:
    """
    Get pre-signed URL for downloading a completed report.

    **Query Parameters:**
    - `expiration`: URL expiration time in seconds (default: 3600 = 1 hour, max: 604800 = 7 days)

    **Note:** Only completed reports can be downloaded. Check status first.

    Returns:
        Pre-signed URL for downloading the PDF report
    """
    download_data = service.get_report_download_url(
        job_id=job_id,
        user_id=user_id,
        expiration=expiration,
    )
    return ReportDownloadResponse(**download_data)
