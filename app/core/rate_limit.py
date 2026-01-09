"""Rate limiting middleware using slowapi."""

from typing import Callable, Optional
import inspect
from functools import wraps

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global limiter instance (initialized at startup)
_limiter: Optional[Limiter] = None


def init_rate_limiter() -> Optional[Limiter]:
    """
    Initialize rate limiter based on settings.
    
    Returns:
        Limiter instance if rate limiting is enabled, None otherwise
    """
    settings = get_settings()
    
    # Disable rate limiting in test environment or if explicitly disabled
    if settings.is_test or not settings.RATE_LIMIT_ENABLED:
        logger.info("Rate limiting disabled", extra={"reason": "test environment" if settings.is_test else "disabled in config"})
        return None
    
    # Determine storage URI
    storage_uri = settings.REDIS_URL or "memory://"
    
    # Initialize limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[],  # No default limits, use decorator-specific limits
        storage_uri=storage_uri,
    )
    
    logger.info("Rate limiter initialized", extra={"storage": storage_uri})
    return limiter


def get_rate_limiter() -> Optional[Limiter]:
    """
    Get rate limiter instance.
    
    Returns:
        Limiter instance or None if rate limiting is disabled
    """
    global _limiter
    # Always check settings fresh (important for tests)
    settings = get_settings()
    if settings.is_test or not settings.RATE_LIMIT_ENABLED:
        _limiter = None  # Reset limiter if disabled
        return None
    if _limiter is None:
        _limiter = init_rate_limiter()
    return _limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        limiter = get_rate_limiter()
        
        # Skip if rate limiting is disabled
        if limiter is None:
            return await call_next(request)
        
        # Middleware doesn't apply default limits (decorators handle specific limits)
        return await call_next(request)


def rate_limit(limit_str: str):
    """
    Simple rate limit decorator that checks settings at runtime.
    
    Usage:
        @rate_limit("10/minute")
        async def my_endpoint(...):
            ...
    
    Args:
        limit_str: Rate limit string (e.g., "10/minute", "100/hour")
    
    Returns:
        Decorator function
    """
    def decorator(func):
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Check settings at runtime (important for tests)
                limiter = get_rate_limiter()
                
                # If rate limiting is disabled, call original function
                if limiter is None:
                    return await func(*args, **kwargs)
                
                # Apply rate limit
                try:
                    limited_func = limiter.limit(limit_str)(func)
                    return await limited_func(*args, **kwargs)
                except RateLimitExceeded:
                    # Extract request for logging
                    request = None
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get("request") or kwargs.get("http_request")
                    
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
                # Check settings at runtime (important for tests)
                limiter = get_rate_limiter()
                
                # If rate limiting is disabled, call original function
                if limiter is None:
                    return func(*args, **kwargs)
                
                # Apply rate limit
                try:
                    limited_func = limiter.limit(limit_str)(func)
                    return limited_func(*args, **kwargs)
                except RateLimitExceeded:
                    # Extract request for logging
                    request = None
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get("request") or kwargs.get("http_request")
                    
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
            
            return sync_wrapper
    
    return decorator


# Backward compatibility alias
conditional_rate_limit = rate_limit
