"""Prometheus metrics collection."""

from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from starlette.responses import Response

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# Business metrics
transactions_created_total = Counter(
    "transactions_created_total",
    "Total transactions created",
    ["type"],
)

categories_created_total = Counter(
    "categories_created_total",
    "Total categories created",
)

reports_generated_total = Counter(
    "reports_generated_total",
    "Total reports generated",
    ["status"],
)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)


def get_metrics() -> Response:
    """Get Prometheus metrics."""
    return Response(content=generate_latest(REGISTRY), media_type="text/plain")


class MetricsMiddleware:
    """Middleware to collect Prometheus metrics."""

    def __init__(self, app):
        """Initialize metrics middleware."""
        self.app = app

    async def __call__(self, scope, receive, send):
        """Collect metrics for requests."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # Normalize path for metrics (remove IDs)
        endpoint = self._normalize_path(path)

        # Track request duration
        with http_request_duration_seconds.labels(method=method, endpoint=endpoint).time():
            status_code = 500

            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                await send(message)

            try:
                await self.app(scope, receive, send_wrapper)
            except Exception:
                status_code = 500
                raise
            finally:
                # Record metrics
                http_requests_total.labels(
                    method=method, endpoint=endpoint, status=status_code
                ).inc()

    @staticmethod
    def _normalize_path(path: str) -> str:
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

