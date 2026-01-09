"""Receipt service for business logic."""

import os
import uuid
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.transaction import transaction
from app.infra.s3 import S3Service
from app.modules.receipts.repo import ReceiptRepository

logger = get_logger(__name__)

# Allowed file types for receipts
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",  # Alternative MIME type
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
}

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Minimum file size: 1KB (to prevent empty or corrupted files)
MIN_FILE_SIZE = 1024  # 1KB in bytes

# Allowed file extensions (for additional validation)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}


class ReceiptService:
    """Service for receipt business logic."""

    def __init__(self, repo: ReceiptRepository, s3_client: S3Service) -> None:
        """Initialize service with repository and S3 client."""
        self.repo = repo
        self.s3_client = s3_client

    def validate_file(self, file: BinaryIO, content_type: str, filename: str = "") -> None:
        """
        Validate uploaded file with comprehensive checks.

        Args:
            file: File object
            content_type: Content type (MIME type)
            filename: Original filename (optional, for extension validation)

        Raises:
            ValidationError: If file is invalid
        """
        # Check content type
        if not content_type:
            raise ValidationError("Content type is required")
        
        # Normalize content type (handle variations like image/jpg vs image/jpeg)
        content_type_lower = content_type.lower()
        if content_type_lower == "image/jpg":
            content_type_lower = "image/jpeg"
        
        if content_type_lower not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                f"Invalid file type '{content_type}'. Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            )

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size == 0:
            raise ValidationError("File is empty")

        if file_size < MIN_FILE_SIZE:
            raise ValidationError(
                f"File size is too small. Minimum size: {MIN_FILE_SIZE / 1024:.1f}KB"
            )

        if file_size > MAX_FILE_SIZE:
            raise ValidationError(
                f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024):.1f}MB. "
                f"File size: {file_size / (1024 * 1024):.2f}MB"
            )

        # Validate file extension if filename provided
        if filename:
            file_ext = os.path.splitext(filename.lower())[1]
            if file_ext not in ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"Invalid file extension '{file_ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                )
            
            # Additional validation: check if extension matches content type
            extension_to_mime = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".pdf": "application/pdf",
            }
            expected_mime = extension_to_mime.get(file_ext)
            if expected_mime and content_type_lower != expected_mime:
                logger.warning(
                    "Content type mismatch",
                    extra={
                        "filename": filename,
                        "content_type": content_type,
                        "expected_mime": expected_mime,
                    },
                )
                # Don't fail, but log warning (some browsers send incorrect MIME types)

        # Validate file content (basic magic number check for images)
        if content_type_lower.startswith("image/"):
            file.seek(0)
            header = file.read(12)
            file.seek(0)
            
            # Check for common image file signatures
            is_valid_image = False
            if content_type_lower == "image/jpeg":
                is_valid_image = header[:2] == b"\xff\xd8"
            elif content_type_lower == "image/png":
                is_valid_image = header[:8] == b"\x89PNG\r\n\x1a\n"
            elif content_type_lower == "image/gif":
                is_valid_image = header[:6] in (b"GIF87a", b"GIF89a")
            elif content_type_lower == "image/webp":
                is_valid_image = header[8:12] == b"WEBP"
            
            if not is_valid_image:
                raise ValidationError(
                    f"File content does not match declared type '{content_type}'. "
                    "File may be corrupted or incorrectly labeled."
                )

    def upload_receipt(
        self,
        db: Session,
        transaction_id: int,
        user_id: int,
        file: BinaryIO,
        content_type: str,
        filename: str,
    ) -> dict:
        """
        Upload receipt to S3 and create database record.

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for authorization)
            file: File object to upload
            content_type: Content type (MIME type)
            filename: Original filename

        Returns:
            Receipt data

        Raises:
            NotFoundError: If transaction not found or user doesn't own it
            ValidationError: If file is invalid
        """
        # Verify transaction ownership
        if not self.repo.verify_transaction_ownership(transaction_id, user_id):
            raise NotFoundError("Transaction")

        # Check if receipt already exists for this transaction
        existing = self.repo.get_by_transaction_id(transaction_id, user_id)
        if existing:
            raise ValidationError(
                "Receipt already exists for this transaction. Delete existing receipt first."
            )

        # Validate file
        self.validate_file(file, content_type, filename)

        # Generate S3 key
        file_extension = os.path.splitext(filename)[1] or ".jpg"
        s3_key = f"receipts/{user_id}/{transaction_id}/{uuid.uuid4()}{file_extension}"

        # Get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        # Upload to S3 and create database record within a transaction
        with transaction(db):
            # Upload to S3
            try:
                # Read file content
                file.seek(0)  # Reset to beginning
                file_content = file.read()

                # Upload to S3
                success = self.s3_client.upload_file(file_content, s3_key, content_type)
                if not success:
                    raise ValidationError(
                        "S3 is not configured or upload failed. Please check S3 configuration."
                    )

                logger.info(
                    "Receipt uploaded to S3",
                    extra={
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                        "s3_key": s3_key,
                        "file_size": file_size,
                    },
                )
            except Exception as e:
                logger.error(
                    "S3 upload failed",
                    extra={"transaction_id": transaction_id, "user_id": user_id, "error": str(e)},
                    exc_info=True,
                )
                raise ValidationError(f"Failed to upload receipt: {str(e)}")

            # Create database record
            receipt = self.repo.create(
                transaction_id=transaction_id,
                s3_key=s3_key,
                content_type=content_type,
                size=file_size,
            )

        return {
            "id": receipt.id,
            "transaction_id": receipt.transaction_id,
            "s3_key": receipt.s3_key,
            "content_type": receipt.content_type,
            "size": receipt.size,
            "created_at": receipt.created_at,
        }

    def get_receipt_url(self, transaction_id: int, user_id: int, expiration: int = 3600) -> dict:
        """
        Get pre-signed URL for receipt download.

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for authorization)
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Receipt URL data

        Raises:
            NotFoundError: If receipt or transaction not found
        """
        # Get receipt (this also verifies transaction ownership)
        receipt = self.repo.get_by_transaction_id(transaction_id, user_id)
        if not receipt:
            raise NotFoundError("Receipt")

        # Generate pre-signed URL
        try:
            url = self.s3_client.generate_presigned_url(receipt.s3_key, expiration=expiration)
            if not url:
                raise ValidationError("S3 is not configured. Cannot generate receipt URL.")
            logger.info(
                "Receipt URL generated",
                extra={
                    "receipt_id": receipt.id,
                    "transaction_id": transaction_id,
                    "user_id": user_id,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to generate receipt URL",
                extra={"receipt_id": receipt.id, "error": str(e)},
                exc_info=True,
            )
            raise ValidationError(f"Failed to generate receipt URL: {str(e)}")

        return {
            "receipt_id": receipt.id,
            "transaction_id": transaction_id,
            "url": url,
            "expires_in": expiration,
        }

    def delete_receipt(self, db: Session, transaction_id: int, user_id: int) -> dict:
        """
        Delete receipt from S3 and database.

        Args:
            transaction_id: Transaction ID
            user_id: User ID (for authorization)

        Returns:
            Success message

        Raises:
            NotFoundError: If receipt not found
        """
        # Get receipt (this also verifies transaction ownership)
        receipt = self.repo.get_by_transaction_id(transaction_id, user_id)
        if not receipt:
            raise NotFoundError("Receipt")

        # Delete from S3 and database within a transaction
        with transaction(db):
            # Delete from S3
            try:
                self.s3_client.delete_file(receipt.s3_key)
                logger.info(
                    "Receipt deleted from S3",
                    extra={
                        "receipt_id": receipt.id,
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                    },
                )
            except Exception as e:
                logger.warning(
                    "Failed to delete receipt from S3 (continuing with DB deletion)",
                    extra={"receipt_id": receipt.id, "s3_key": receipt.s3_key, "error": str(e)},
                )
                # Continue with database deletion even if S3 deletion fails

            # Delete from database
            self.repo.delete(receipt)

        logger.info(
            "Receipt deleted",
            extra={"receipt_id": receipt.id, "transaction_id": transaction_id, "user_id": user_id},
        )

        return {"message": "Receipt deleted successfully"}
