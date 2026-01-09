"""Transaction schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.categories.schemas import CategoryResponse


class TransactionBase(BaseModel):
    """Base transaction schema."""

    amount: Decimal = Field(
        ..., gt=0, decimal_places=2, description="Transaction amount (must be positive)"
    )
    type: str = Field(..., pattern="^(expense|income)$", description="Transaction type")
    occurred_at: datetime = Field(..., description="When the transaction occurred")
    note: Optional[str] = Field(None, max_length=1000, description="Optional note")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive and reasonable."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > 9999999.99:
            raise ValueError("Amount exceeds maximum allowed value")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Normalize type."""
        return v.lower()

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: Optional[str]) -> Optional[str]:
        """Trim note if provided."""
        if v is not None:
            return v.strip() or None
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[str]) -> Optional[str]:
        """Trim tags if provided."""
        if v is not None:
            return v.strip() or None
        return v


class TransactionCreate(TransactionBase):
    """Transaction creation schema."""

    category_id: Optional[int] = Field(None, description="Optional category ID")


class TransactionUpdate(BaseModel):
    """Transaction update schema."""

    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    type: Optional[str] = Field(None, pattern="^(expense|income)$")
    category_id: Optional[int] = None
    occurred_at: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=1000)
    tags: Optional[str] = Field(None, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate amount if provided."""
        if v is not None:
            if v <= 0:
                raise ValueError("Amount must be positive")
            if v > 9999999.99:
                raise ValueError("Amount exceeds maximum allowed value")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Normalize type if provided."""
        if v is not None:
            return v.lower()
        return v

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: Optional[str]) -> Optional[str]:
        """Trim note if provided."""
        if v is not None:
            return v.strip() or None
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[str]) -> Optional[str]:
        """Trim tags if provided."""
        if v is not None:
            return v.strip() or None
        return v


class TransactionResponse(BaseModel):
    """Transaction response schema."""

    model_config = {"from_attributes": True}

    id: int
    user_id: int
    category_id: Optional[int] = None
    amount: Decimal
    type: str
    occurred_at: datetime
    note: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None


class TransactionListResponse(BaseModel):
    """Transaction list response with cursor pagination."""

    items: list[TransactionResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False
    total: Optional[int] = None


class TransactionFilters(BaseModel):
    """Transaction filter parameters."""

    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    category_id: Optional[int] = Field(None, description="Filter by category ID")
    type: Optional[str] = Field(None, pattern="^(expense|income)$", description="Filter by type")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum amount")
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    limit: int = Field(20, ge=1, le=100, description="Number of items per page")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate date range."""
        if "start_date" in info.data and "end_date" in info.data:
            start = info.data.get("start_date")
            end = info.data.get("end_date")
            if start and end and start > end:
                raise ValueError("start_date must be before end_date")
        return v

    @field_validator("min_amount", "max_amount")
    @classmethod
    def validate_amount_range(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        """Validate amount range."""
        if "min_amount" in info.data and "max_amount" in info.data:
            min_amt = info.data.get("min_amount")
            max_amt = info.data.get("max_amount")
            if min_amt is not None and max_amt is not None and min_amt > max_amt:
                raise ValueError("min_amount must be less than or equal to max_amount")
        return v
