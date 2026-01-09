"""Custom exceptions and error handlers."""

from typing import Any, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseAPIException(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class NotFoundError(BaseAPIException):
    """Resource not found exception."""

    def __init__(
        self, 
        resource: str = "Resource", 
        resource_id: Optional[Any] = None,
        detail: Optional[Any] = None,
        context: Optional[dict] = None
    ) -> None:
        """
        Initialize NotFoundError.
        
        Args:
            resource: Resource name (e.g., "Transaction", "Category")
            resource_id: Optional resource ID that was not found
            detail: Optional additional detail
            context: Optional context dictionary for logging
        """
        message = f"{resource} not found"
        if resource_id is not None:
            message = f"{resource} with ID {resource_id} not found"
        
        error_detail = detail or {}
        if context:
            error_detail.update(context)
        if resource_id is not None:
            error_detail["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail,
        )


class ValidationError(BaseAPIException):
    """Validation error exception."""

    def __init__(self, message: str, detail: Optional[Any] = None, context: Optional[dict] = None) -> None:
        """
        Initialize ValidationError.
        
        Args:
            message: Error message
            detail: Optional additional detail
            context: Optional context dictionary for logging
        """
        error_detail = detail or {}
        if context:
            error_detail.update(context)
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_detail,
        )


class AuthenticationError(BaseAPIException):
    """Authentication error exception."""

    def __init__(
        self, message: str = "Authentication failed", detail: Optional[Any] = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class AuthorizationError(BaseAPIException):
    """Authorization error exception."""

    def __init__(
        self, message: str = "Insufficient permissions", detail: Optional[Any] = None
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ConflictError(BaseAPIException):
    """Resource conflict exception."""

    def __init__(self, message: str = "Resource conflict", detail: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handle base API exceptions."""
    logger.error(
        "API exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error_message": exc.message,  # Changed from "message" to avoid LogRecord conflict
            "detail": exc.detail,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "detail": exc.detail,
                "path": request.url.path,
            }
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors."""
    logger.error(
        "Database integrity error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc.orig),
        },
        exc_info=True,
    )

    # Check for common constraint violations
    error_message = str(exc.orig)
    if "unique constraint" in error_message.lower() or "duplicate key" in error_message.lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "message": "Resource already exists",
                    "detail": {"constraint": "unique_violation"},
                    "path": request.url.path,
                }
            },
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "message": "Database constraint violation",
                "detail": {},
                "path": request.url.path,
            }
        },
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle general SQLAlchemy errors."""
    logger.error(
        "Database error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Database error occurred",
                "detail": {},
                "path": request.url.path,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "Unexpected error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An unexpected error occurred",
                "detail": {},
                "path": request.url.path,
            }
        },
    )
