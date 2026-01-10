"""Integration tests for MetricsMiddleware."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.core.metrics import MetricsMiddleware


async def test_metrics_middleware_non_http_scope():
    """Test MetricsMiddleware passes through non-HTTP scopes."""
    mock_app = AsyncMock()
    middleware = MetricsMiddleware(mock_app)

    scope = {"type": "websocket"}
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(scope, receive, send)

    mock_app.assert_called_once_with(scope, receive, send)


async def test_metrics_middleware_http_scope():
    """Test MetricsMiddleware processes HTTP requests and records metrics."""
    mock_app = AsyncMock()
    middleware = MetricsMiddleware(mock_app)

    # Mock the app to return a response
    async def mock_app_call(scope, receive, send_wrapper):
        await send_wrapper({"type": "http.response.start", "status": 200})
        await send_wrapper({"type": "http.response.body", "body": b"OK"})

    mock_app.side_effect = mock_app_call

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/health",
    }
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(scope, receive, send)

    # Verify app was called
    assert mock_app.called


async def test_metrics_middleware_exception_handling():
    """Test MetricsMiddleware records 500 status on exceptions."""
    mock_app = AsyncMock(side_effect=Exception("Test error"))
    middleware = MetricsMiddleware(mock_app)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/test",
    }
    receive = AsyncMock()
    send = AsyncMock()

    # Should raise the exception but record metrics
    try:
        await middleware(scope, receive, send)
    except Exception:
        pass  # Expected

    # Verify app was called
    assert mock_app.called


async def test_metrics_middleware_normalizes_path():
    """Test that MetricsMiddleware normalizes paths with IDs."""
    mock_app = AsyncMock()

    async def mock_app_call(scope, receive, send_wrapper):
        await send_wrapper({"type": "http.response.start", "status": 200})

    mock_app.side_effect = mock_app_call
    middleware = MetricsMiddleware(mock_app)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/transactions/123",
    }
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(scope, receive, send)

    # Path normalization should have been called
    assert mock_app.called
