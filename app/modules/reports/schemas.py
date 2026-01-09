"""Report schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Report request schema."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    category_ids: Optional[list[int]] = Field(
        default=None, description="Filter by category IDs (optional)"
    )
    include_receipts: bool = Field(
        default=False, description="Include receipt information in report"
    )
    transaction_types: Optional[list[str]] = Field(
        default=None, description="Filter by transaction types: expense, income (optional)"
    )


class ReportJobResponse(BaseModel):
    """Report job response schema."""

    model_config = {"from_attributes": True}

    id: int
    user_id: int
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    params_json: dict
    s3_key: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ReportCreateResponse(BaseModel):
    """Report creation response schema."""

    job_id: int
    status: str
    message: str = Field(default="Report generation started")


class ReportStatusResponse(BaseModel):
    """Report status response schema."""

    job_id: int
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ReportDownloadResponse(BaseModel):
    """Report download response schema."""

    job_id: int
    url: str = Field(..., description="Pre-signed URL for downloading the report")
    expires_in: int = Field(..., description="URL expiration time in seconds")
    filename: str = Field(..., description="Report filename")
