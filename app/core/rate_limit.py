"""Rate limiting middleware using slowapi."""

from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"] if settings.RATE_LIMIT_ENABLED else [],
    storage_uri=settings.REDIS_URL if settings.RATE_LIMIT_ENABLED else "memory://",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        if not settings.RATE_LIMIT_ENABLED:
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

