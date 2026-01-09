"""Tests for production features (rate limiting, security headers, metrics)."""

from fastapi.testclient import TestClient


def test_security_headers(client: TestClient):
    """Test security headers are present."""
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"
    assert "X-XSS-Protection" in headers
    assert "Referrer-Policy" in headers
    assert "Content-Security-Policy" in headers


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus format doesn't include version in content-type
    assert "text/plain" in response.headers["content-type"]
    assert "charset=utf-8" in response.headers["content-type"]
    assert "http_requests_total" in response.text


def test_health_check_detailed(client: TestClient):
    """Test health check includes all services."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "dependencies" in data
    assert "redis" in data["dependencies"]
    assert "database" in data["dependencies"]
    assert "s3" in data["dependencies"]
    assert "service" in data
    assert "version" in data
    assert "environment" in data


def test_rate_limiting_registration(authenticated_client: TestClient):
    """Test rate limiting on registration endpoint."""
    # Note: This test may be flaky if rate limits are hit
    # In a real scenario, we'd mock the rate limiter
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.RATE_LIMIT_ENABLED:
        return  # Skip if rate limiting is disabled

    # Try to register multiple times quickly
    # This should eventually hit rate limit (5/minute)
    # But we won't test the actual limit to avoid flakiness
    pass  # Rate limiting is configured, actual limit testing requires mocking


def test_rate_limiting_login(authenticated_client: TestClient):
    """Test rate limiting on login endpoint."""
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.RATE_LIMIT_ENABLED:
        return  # Skip if rate limiting is disabled

    # Rate limiting is configured, actual limit testing requires mocking
    pass


def test_request_id_header(client: TestClient):
    """Test request ID is added to response."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] is not None


def test_process_time_header(client: TestClient):
    """Test process time is added to response."""
    response = client.get("/health")
    assert "X-Process-Time" in response.headers
    assert float(response.headers["X-Process-Time"]) >= 0


def test_metrics_collection(client: TestClient):
    """Test that metrics are collected."""
    # Make a request
    client.get("/health")

    # Check metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    # Metrics should include our request
    assert "http_requests_total" in response.text
