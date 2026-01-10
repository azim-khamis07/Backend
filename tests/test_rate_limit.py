"""Tests for rate limiting functionality."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.responses import Response

import app.core.rate_limit as rate_limit_module
from app.core.config import get_settings
from app.core.rate_limit import (
    RateLimitMiddleware,
    get_rate_limiter,
    init_rate_limiter,
    rate_limit,
)


def test_init_rate_limiter_disabled_in_test():
    """Test init_rate_limiter returns None in test environment."""
    get_settings.cache_clear()
    result = init_rate_limiter()
    assert result is None


def test_init_rate_limiter_disabled_when_rate_limit_disabled():
    """Test init_rate_limiter returns None when RATE_LIMIT_ENABLED is False."""
    get_settings.cache_clear()
    with patch.dict(os.environ, {"RATE_LIMIT_ENABLED": "false", "ENVIRONMENT": "production"}):
        result = init_rate_limiter()
        assert result is None


def test_init_rate_limiter_enabled():
    """Test init_rate_limiter creates limiter when enabled."""
    get_settings.cache_clear()
    with patch.dict(
        os.environ,
        {"RATE_LIMIT_ENABLED": "true", "ENVIRONMENT": "production", "REDIS_URL": "memory://"},
    ):
        result = init_rate_limiter()
        assert result is not None
        assert isinstance(result, Limiter)


def test_get_rate_limiter_returns_none_when_disabled():
    """Test get_rate_limiter returns None when rate limiting is disabled."""
    get_settings.cache_clear()
    # Reset global limiter
    rate_limit_module._limiter = None
    result = get_rate_limiter()
    assert result is None


async def test_rate_limit_middleware_skips_when_disabled():
    """Test RateLimitMiddleware passes through when limiter is None."""
    mock_response = Mock(spec=Response)
    mock_app = AsyncMock(return_value=mock_response)
    middleware = RateLimitMiddleware(mock_app)
    mock_request = MagicMock(spec=Request)

    async def mock_call_next(request):
        return mock_response

    # Mock get_rate_limiter to return None
    with patch("app.core.rate_limit.get_rate_limiter", return_value=None):
        result = await middleware.dispatch(mock_request, mock_call_next)
        assert result == mock_response


async def test_rate_limit_middleware_with_limiter():
    """Test RateLimitMiddleware passes through when limiter is enabled (but no default limits)."""
    mock_response = Mock(spec=Response)
    mock_app = AsyncMock(return_value=mock_response)
    middleware = RateLimitMiddleware(mock_app)
    mock_request = MagicMock(spec=Request)

    async def mock_call_next(request):
        return mock_response

    # Mock get_rate_limiter to return a limiter
    mock_limiter = MagicMock(spec=Limiter)
    with patch("app.core.rate_limit.get_rate_limiter", return_value=mock_limiter):
        result = await middleware.dispatch(mock_request, mock_call_next)
        assert result == mock_response


async def test_rate_limit_decorator_async_function_disabled():
    """Test rate_limit decorator with async function when rate limiting disabled."""

    @rate_limit("10/minute")
    async def async_endpoint():
        return {"message": "success"}

    get_settings.cache_clear()
    rate_limit_module._limiter = None

    result = await async_endpoint()
    assert result == {"message": "success"}


def test_rate_limit_decorator_sync_function_disabled():
    """Test rate_limit decorator with sync function when rate limiting disabled."""

    @rate_limit("10/minute")
    def sync_endpoint():
        return {"message": "success"}

    get_settings.cache_clear()
    rate_limit_module._limiter = None

    result = sync_endpoint()
    assert result == {"message": "success"}


async def test_rate_limit_decorator_async_with_rate_limit_exceeded():
    """Test rate_limit decorator handles RateLimitExceeded for async functions."""
    mock_limiter = MagicMock(spec=Limiter)

    @rate_limit("10/minute")
    async def async_endpoint(request: Request):
        return {"message": "success"}

    # Create a function that raises RateLimitExceeded when called
    def raise_rate_limit(*args, **kwargs):
        raise RateLimitExceeded()

    # Mock the limiter.limit() to return a function that raises the exception
    mock_limited_func = AsyncMock(side_effect=RateLimitExceeded())
    mock_limit_decorator = Mock(return_value=mock_limited_func)
    mock_limiter.limit = Mock(return_value=mock_limit_decorator)

    with patch("app.core.rate_limit.get_rate_limiter", return_value=mock_limiter):
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        mock_request.url = MagicMock()
        mock_request.url.path = "/test"

        result = await async_endpoint(mock_request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429


async def test_rate_limit_decorator_async_request_from_kwargs():
    """Test rate_limit decorator extracts request from kwargs when RateLimitExceeded."""

    @rate_limit("10/minute")
    async def async_endpoint(http_request: Request):
        return {"message": "success"}

    mock_limiter = MagicMock(spec=Limiter)
    mock_limited_func = AsyncMock(side_effect=RateLimitExceeded())
    mock_limit_decorator = Mock(return_value=mock_limited_func)
    mock_limiter.limit = Mock(return_value=mock_limit_decorator)

    with patch("app.core.rate_limit.get_rate_limiter", return_value=mock_limiter):
        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/test"
        mock_request.method = "POST"

        result = await async_endpoint(http_request=mock_request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429


def test_rate_limit_decorator_sync_with_rate_limit_exceeded():
    """Test rate_limit decorator handles RateLimitExceeded for sync functions."""

    @rate_limit("10/minute")
    def sync_endpoint(request: Request):
        return {"message": "success"}

    mock_limiter = MagicMock(spec=Limiter)
    mock_limited_func = Mock(side_effect=RateLimitExceeded())
    mock_limit_decorator = Mock(return_value=mock_limited_func)
    mock_limiter.limit = Mock(return_value=mock_limit_decorator)

    with patch("app.core.rate_limit.get_rate_limiter", return_value=mock_limiter):
        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/test"
        mock_request.method = "PUT"

        result = sync_endpoint(mock_request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429


async def test_rate_limit_decorator_no_request_object():
    """Test rate_limit decorator handles RateLimitExceeded when no request object found."""

    @rate_limit("10/minute")
    async def async_endpoint(some_arg: str):
        return {"message": "success"}

    mock_limiter = MagicMock(spec=Limiter)
    mock_limited_func = AsyncMock(side_effect=RateLimitExceeded())
    mock_limit_decorator = Mock(return_value=mock_limited_func)
    mock_limiter.limit = Mock(return_value=mock_limit_decorator)

    with patch("app.core.rate_limit.get_rate_limiter", return_value=mock_limiter):
        result = await async_endpoint("test")
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429
        # Should handle missing request gracefully
        assert "unknown" in result.body.decode()


async def test_rate_limit_decorator_async_with_enabled_limiter():
    """Test rate_limit decorator with enabled limiter (successful call)."""

    @rate_limit("10/minute")
    async def async_endpoint(request: Request):
        return {"message": "success"}

    mock_limiter = MagicMock(spec=Limiter)
    mock_limited_func = AsyncMock(return_value={"message": "success"})
    mock_limit_decorator = Mock(return_value=mock_limited_func)
    mock_limiter.limit = Mock(return_value=mock_limit_decorator)

    with patch("app.core.rate_limit.get_rate_limiter", return_value=mock_limiter):
        mock_request = MagicMock(spec=Request)
        result = await async_endpoint(mock_request)
        assert result == {"message": "success"}
        mock_limiter.limit.assert_called_once_with("10/minute")


def test_get_rate_limiter_initializes_on_first_call():
    """Test get_rate_limiter initializes limiter on first call when enabled."""
    get_settings.cache_clear()
    rate_limit_module._limiter = None

    with patch.dict(
        os.environ,
        {"RATE_LIMIT_ENABLED": "true", "ENVIRONMENT": "production", "REDIS_URL": "memory://"},
    ):
        with patch("app.core.rate_limit.init_rate_limiter") as mock_init:
            mock_init.return_value = MagicMock(spec=Limiter)
            result = get_rate_limiter()
            mock_init.assert_called_once()
            assert result is not None
