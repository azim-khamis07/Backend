"""Receipt router endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.infra.s3 import s3_service
from app.modules.auth.router import get_current_user_id
from app.modules.receipts.repo import ReceiptRepository
from app.modules.receipts.schemas import (
    ReceiptUploadResponse,
    ReceiptURLResponse,
)
from app.modules.receipts.service import ReceiptService

router = APIRouter(prefix="/transactions", tags=["receipts"])


def get_receipt_service(
    db: Session = Depends(get_db),
) -> ReceiptService:
    """Dependency to get receipt service."""
    repo = ReceiptRepository(db)
    return ReceiptService(repo, s3_service)


@router.post(
    "/{transaction_id}/receipt",
    status_code=status.HTTP_201_CREATED,
    response_model=ReceiptUploadResponse,
)
async def upload_receipt(
    transaction_id: int,
    file: UploadFile = File(..., description="Receipt file (image or PDF)"),
    user_id: int = Depends(get_current_user_id),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptUploadResponse:
    """
    Upload a receipt for a transaction.

    **File Requirements:**
    - Allowed types: JPEG, PNG, GIF, WebP, PDF
    - Maximum size: 10MB

    **Note:** Only one receipt per transaction. Delete existing receipt before uploading a new one.

    Returns:
        Receipt upload confirmation with metadata
    """
    # Validate file
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content type is required",
        )

    # Upload receipt
    receipt_data = service.upload_receipt(
        transaction_id=transaction_id,
        user_id=user_id,
        file=file.file,
        content_type=file.content_type,
        filename=file.filename or "receipt",
    )

    return ReceiptUploadResponse(**receipt_data)


@router.get("/{transaction_id}/receipt", response_model=ReceiptURLResponse)
async def get_receipt_url(
    transaction_id: int,
    expiration: int = 3600,
    user_id: int = Depends(get_current_user_id),
    service: ReceiptService = Depends(get_receipt_service),
) -> ReceiptURLResponse:
    """
    Get pre-signed URL for downloading a receipt.

    **Query Parameters:**
    - `expiration`: URL expiration time in seconds (default: 3600 = 1 hour, max: 604800 = 7 days)

    Returns:
        Pre-signed URL for downloading the receipt
    """
    # Validate expiration
    if expiration < 60 or expiration > 604800:  # 1 minute to 7 days
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiration must be between 60 and 604800 seconds",
        )

    receipt_url_data = service.get_receipt_url(
        transaction_id=transaction_id,
        user_id=user_id,
        expiration=expiration,
    )

    return ReceiptURLResponse(**receipt_url_data)


@router.delete("/{transaction_id}/receipt", status_code=status.HTTP_200_OK)
async def delete_receipt(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    service: ReceiptService = Depends(get_receipt_service),
) -> dict:
    """
    Delete a receipt for a transaction.

    This will delete the receipt from both S3 and the database.

    Returns:
        Success message
    """
    result = service.delete_receipt(transaction_id=transaction_id, user_id=user_id)
    return result
