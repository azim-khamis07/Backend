"""AWS S3 client setup and file upload helpers."""

from typing import Optional

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Global S3 client instance
_s3_client: Optional[BaseClient] = None


def get_s3_client() -> BaseClient:
    """Get or create S3 client instance."""
    global _s3_client
    if _s3_client is None:
        s3_config = {
            "service_name": "s3",
            "region_name": settings.AWS_REGION,
        }

        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            s3_config["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            s3_config["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        if settings.AWS_S3_ENDPOINT_URL:
            s3_config["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL

        _s3_client = boto3.client(**s3_config)
        logger.info("S3 client initialized", extra={"region": settings.AWS_REGION})
    return _s3_client


class S3Service:
    """Service for S3 operations."""

    def __init__(self, s3_client: Optional[BaseClient] = None) -> None:
        """Initialize S3 service."""
        self.s3 = s3_client or get_s3_client()
        self.bucket_name = settings.AWS_S3_BUCKET_NAME

    def upload_file(
        self,
        file_content: bytes,
        s3_key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> bool:
        """Upload file to S3."""
        if not self.bucket_name:
            logger.error("S3 bucket name not configured")
            return False

        try:
            extra_args = {"ContentType": content_type}
            if metadata:
                extra_args["Metadata"] = {str(k): str(v) for k, v in metadata.items()}

            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                **extra_args,
            )
            logger.info("File uploaded to S3", extra={"key": s3_key, "bucket": self.bucket_name})
            return True
        except ClientError as e:
            logger.error("S3 upload error", extra={"key": s3_key, "error": str(e)}, exc_info=True)
            return False

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3."""
        if not self.bucket_name:
            logger.error("S3 bucket name not configured")
            return False

        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info("File deleted from S3", extra={"key": s3_key, "bucket": self.bucket_name})
            return True
        except ClientError as e:
            logger.error("S3 delete error", extra={"key": s3_key, "error": str(e)}, exc_info=True)
            return False

    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> Optional[str]:
        """Generate pre-signed URL for file access."""
        if not self.bucket_name:
            logger.error("S3 bucket name not configured")
            return None

        try:
            params = {
                "Bucket": self.bucket_name,
                "Key": s3_key,
            }

            url = self.s3.generate_presigned_url(
                ClientMethod=f"{http_method.lower()}_object",
                Params=params,
                ExpiresIn=expiration,
            )
            logger.debug(
                "Pre-signed URL generated", extra={"key": s3_key, "expiration": expiration}
            )
            return url
        except ClientError as e:
            logger.error(
                "Pre-signed URL generation error",
                extra={"key": s3_key, "error": str(e)},
                exc_info=True,
            )
            return None

    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3."""
        if not self.bucket_name:
            return False

        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False


# Singleton instance
s3_service = S3Service()
