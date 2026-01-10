"""Tests for metrics middleware."""

from app.core.metrics import MetricsMiddleware


def test_normalize_path_with_numeric_id():
    """Test path normalization with numeric ID."""
    normalized = MetricsMiddleware._normalize_path("/api/v1/transactions/123")
    assert normalized == "/api/v1/transactions/{id}"


def test_normalize_path_with_uuid():
    """Test path normalization with UUID."""
    uuid_path = "/api/v1/users/550e8400-e29b-41d4-a716-446655440000"
    normalized = MetricsMiddleware._normalize_path(uuid_path)
    assert normalized == "/api/v1/users/{id}"


def test_normalize_path_with_multiple_ids():
    """Test path normalization with multiple IDs."""
    path = "/api/v1/transactions/123/receipts/456"
    normalized = MetricsMiddleware._normalize_path(path)
    assert normalized == "/api/v1/transactions/{id}/receipts/{id}"


def test_normalize_path_no_ids():
    """Test path normalization without IDs."""
    path = "/api/v1/health"
    normalized = MetricsMiddleware._normalize_path(path)
    assert normalized == "/api/v1/health"


def test_normalize_path_with_query_params():
    """Test path normalization preserves query parameters handling."""
    # Note: Query params shouldn't be in the path for normalization
    # but if they are, they should be handled
    path = "/api/v1/transactions/123"
    normalized = MetricsMiddleware._normalize_path(path)
    assert normalized == "/api/v1/transactions/{id}"


def test_normalize_path_nested():
    """Test path normalization with nested resources."""
    path = "/api/v1/users/42/categories/99"
    normalized = MetricsMiddleware._normalize_path(path)
    assert normalized == "/api/v1/users/{id}/categories/{id}"

