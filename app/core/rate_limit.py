"""Rate limiting middleware using slowapi."""

from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize rate limiter with empty limits (will be set based on settings)
# Settings are checked dynamically to support test environment
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # Will be set dynamically
    storage_uri="memory://",  # Default to memory, will be updated if needed
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        # Check settings dynamically (not cached) to support test environment
        settings = get_settings()

        # Disable rate limiting in test environment or if explicitly disabled
        if not settings.RATE_LIMIT_ENABLED or settings.is_test:
            return await call_next(request)

        # For decorator-based rate limits, skip check if default limits are empty
        # (indicates rate limiting is disabled)
        if not limiter.default_limits:
            return await call_next(request)

        try:
            # Check rate limit
            limiter.check()
        except RateLimitExceeded:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client": get_remote_address(request),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            # Return rate limit error
            from fastapi import status
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "message": "Rate limit exceeded. Please try again later.",
                        "detail": {"retry_after": 60},
                        "path": request.url.path,
                    }
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


def get_rate_limiter() -> Limiter:
    """Get rate limiter instance."""
    return limiter
