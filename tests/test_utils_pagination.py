"""Tests for pagination utilities."""

import pytest

from app.utils.pagination import PaginatedResponse, PaginationParams


def test_pagination_params_default():
    """Test pagination params with default values."""
    params = PaginationParams()
    assert params.limit == 20
    assert params.cursor is None


def test_pagination_params_custom():
    """Test pagination params with custom values."""
    params = PaginationParams(limit=10, cursor="abc123")
    assert params.limit == 10
    assert params.cursor == "abc123"


def test_pagination_params_validation_too_small():
    """Test pagination params validation - limit too small."""
    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        PaginationParams(limit=0)


def test_pagination_params_validation_too_large():
    """Test pagination params validation - limit too large."""
    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        PaginationParams(limit=101)


def test_pagination_params_valid_range():
    """Test pagination params with valid limits."""
    # Minimum valid
    params1 = PaginationParams(limit=1)
    assert params1.limit == 1

    # Maximum valid
    params2 = PaginationParams(limit=100)
    assert params2.limit == 100

    # Middle value
    params3 = PaginationParams(limit=50)
    assert params3.limit == 50


def test_paginated_response_default():
    """Test paginated response with default values."""
    response = PaginatedResponse(items=[1, 2, 3])
    assert response.items == [1, 2, 3]
    assert response.next_cursor is None
    assert response.has_more is False
    assert response.total is None


def test_paginated_response_with_all_fields():
    """Test paginated response with all fields."""
    response = PaginatedResponse(
        items=["a", "b", "c"], next_cursor="cursor123", has_more=True, total=100
    )
    assert response.items == ["a", "b", "c"]
    assert response.next_cursor == "cursor123"
    assert response.has_more is True
    assert response.total == 100


def test_paginated_response_empty():
    """Test paginated response with empty items."""
    response = PaginatedResponse(items=[])
    assert response.items == []
    assert response.has_more is False


def test_paginated_response_with_more():
    """Test paginated response indicating more items."""
    response = PaginatedResponse(items=[1, 2], has_more=True, next_cursor="next")
    assert len(response.items) == 2
    assert response.has_more is True
    assert response.next_cursor == "next"

