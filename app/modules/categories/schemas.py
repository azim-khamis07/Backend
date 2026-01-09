"""Category schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    """Base category schema."""

    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(expense|income)$")
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Trim and validate name."""
        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Normalize type."""
        return v.lower()


class CategoryCreate(CategoryBase):
    """Category creation schema."""

    pass


class CategoryUpdate(BaseModel):
    """Category update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, pattern="^(expense|income)$")
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=7, pattern="^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Trim name if provided."""
        if v is not None:
            return v.strip()
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        """Normalize type if provided."""
        if v is not None:
            return v.lower()
        return v


class CategoryResponse(BaseModel):
    """Category response schema."""

    model_config = {"from_attributes": True}

    id: int
    user_id: int
    name: str
    type: str
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    """Category list response schema."""

    items: list[CategoryResponse]
    total: int
