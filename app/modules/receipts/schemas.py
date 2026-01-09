"""Receipt schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReceiptResponse(BaseModel):
    """Receipt response schema."""

    model_config = {"from_attributes": True}

    id: int
    transaction_id: int
    s3_key: str
    content_type: str
    size: int
    created_at: datetime


class ReceiptUploadResponse(BaseModel):
    """Receipt upload response schema."""

    id: int
    transaction_id: int
    s3_key: str
    content_type: str
    size: int
    created_at: datetime
    message: str = Field(default="Receipt uploaded successfully")


class ReceiptURLResponse(BaseModel):
    """Receipt URL response schema."""

    receipt_id: int
    transaction_id: int
    url: str = Field(..., description="Pre-signed URL for downloading the receipt")
    expires_in: int = Field(..., description="URL expiration time in seconds")
