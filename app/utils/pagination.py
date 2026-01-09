"""Pagination utilities for cursor-based pagination."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    limit: int = 20
    cursor: Optional[str] = None

    def __init__(self, limit: int = 20, cursor: Optional[str] = None, **kwargs) -> None:
        """Initialize pagination params with validation."""
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        super().__init__(limit=limit, cursor=cursor, **kwargs)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    items: list[T]
    next_cursor: Optional[str] = None
    has_more: bool = False
    total: Optional[int] = None
