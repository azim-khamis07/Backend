"""Custom middleware for request processing."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.metrics import (
    http_request_duration_seconds,
    http_requests_total,
)

logger = get_logger(__name__)


def normalize_path(path: str) -> str:
    """Normalize path by replacing IDs with placeholders."""
    import re

    # Replace UUIDs
    path = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "{id}",
        path,
    )
    # Replace numeric IDs
    path = re.sub(r"/\d+", "/{id}", path)
    return path


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add request ID."""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add timing information to requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Measure request processing time."""
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))

        # Log slow requests
        if process_time > 1.0:
            logger.warning(
                "Slow request",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": process_time,
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response."""
        request_id = getattr(request.state, "request_id", None)

        logger.info(
            "Request started",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else None,
                "request_id": request_id,
            },
        )

        try:
            # Track metrics
            endpoint = normalize_path(request.url.path)
            method = request.method

            # Track request duration
            import time

            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
                duration
            )
            http_requests_total.labels(
                method=method, endpoint=endpoint, status=response.status_code
            ).inc()

            logger.info(
                "Request completed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "request_id": request_id,
                },
            )
            return response
        except Exception as exc:
            logger.error(
                "Request failed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(exc),
                    "request_id": request_id,
                },
                exc_info=True,
            )
            raise
