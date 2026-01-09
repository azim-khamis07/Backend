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


def conditional_rate_limit(limit_str: str):
    """
    Conditionally apply rate limit decorator based on settings.

    This decorator wrapper checks if rate limiting is enabled at runtime
    (when the function is called). In test environment or when rate limiting
    is disabled, it bypasses rate limiting completely.
    """

    def decorator(func):
        import inspect
        from functools import wraps

        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract request from args or kwargs for rate limiting check
                request = None
                if args and isinstance(args[0], Request):
                    request = args[0]
                elif "request" in kwargs and isinstance(kwargs["request"], Request):
                    request = kwargs["request"]
                elif "http_request" in kwargs and isinstance(kwargs["http_request"], Request):
                    request = kwargs["http_request"]

                # Check settings at runtime (when function is called)
                # Clear cache to ensure we get current settings
                get_settings.cache_clear()
                settings = get_settings()

                # Check if limiter is disabled (set by test fixture)
                limiter_disabled = not getattr(limiter, "enabled", True)

                if not settings.RATE_LIMIT_ENABLED or settings.is_test or limiter_disabled:
                    # Skip rate limit check - call original function directly
                    # Don't modify args/kwargs - let FastAPI handle parameter injection
                    return await func(*args, **kwargs)

                # Rate limiting is enabled - apply limiter and check
                if request is None:
                    # No request found, call function directly (shouldn't happen)
                    return await func(*args, **kwargs)

                try:
                    # Reset limiter state for fresh check
                    try:
                        limiter.reset()
                    except Exception:
                        pass  # Ignore if reset not supported

                    # Apply rate limit check using limiter decorator
                    # The limiter.limit() decorator expects request as first parameter
                    # We need to create a wrapper that matches the limiter's expectations
                    # Create a wrapper function that the limiter can use
                    async def limited_wrapper(req: Request, *inner_args, **inner_kwargs):
                        # FastAPI injects request, so we need to replace it in kwargs if present
                        # or use the one from inner_args
                        if inner_args and isinstance(inner_args[0], Request):
                            # Request is already in args, call with it
                            return await func(*inner_args, **inner_kwargs)
                        # Otherwise, replace request/http_request in kwargs
                        if "request" in inner_kwargs:
                            inner_kwargs["request"] = req
                        elif "http_request" in inner_kwargs:
                            inner_kwargs["http_request"] = req
                        return await func(*inner_args, **inner_kwargs)

                    # Apply limiter to the wrapper - limiter expects request as first arg
                    limited_func = limiter.limit(limit_str)(limited_wrapper)
                    # Call with request as first arg for the limiter
                    return await limited_func(request, *args, **kwargs)
                except RateLimitExceeded:
                    from fastapi import status
                    from fastapi.responses import JSONResponse

                    logger.warning(
                        "Rate limit exceeded",
                        extra={
                            "path": request.url.path if request else "unknown",
                            "method": request.method if request else "unknown",
                            "client": get_remote_address(request) if request else "unknown",
                        },
                    )
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": {
                                "message": "Rate limit exceeded. Please try again later.",
                                "detail": {"retry_after": 60},
                                "path": request.url.path if request else "unknown",
                            }
                        },
                        headers={"Retry-After": "60"},
                    )

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Clear cache to ensure we get current settings
                get_settings.cache_clear()
                settings = get_settings()

                # Check if limiter is disabled (set by test fixture)
                limiter_disabled = not getattr(limiter, "enabled", True)

                # Extract request from args or kwargs
                request = None
                if args and isinstance(args[0], Request):
                    request = args[0]
                elif "request" in kwargs and isinstance(kwargs["request"], Request):
                    request = kwargs["request"]
                elif "http_request" in kwargs and isinstance(kwargs["http_request"], Request):
                    request = kwargs["http_request"]

                if not settings.RATE_LIMIT_ENABLED or settings.is_test or limiter_disabled:
                    return func(*args, **kwargs)
                # Rate limiting enabled - apply limiter and check
                if request is None:
                    return func(*args, **kwargs)

                try:
                    # Reset limiter state for fresh check
                    try:
                        limiter.reset()
                    except Exception:
                        pass  # Ignore if reset not supported
                    limited_func = limiter.limit(limit_str)(func)
                    return limited_func(*args, **kwargs)
                except RateLimitExceeded:
                    from fastapi import status
                    from fastapi.responses import JSONResponse

                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": {
                                "message": "Rate limit exceeded. Please try again later.",
                                "detail": {"retry_after": 60},
                                "path": request.url.path if request else "unknown",
                            }
                        },
                        headers={"Retry-After": "60"},
                    )

            return sync_wrapper

    return decorator
