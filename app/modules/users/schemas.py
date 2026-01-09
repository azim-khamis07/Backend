"""User management schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserResponse(BaseModel):
    """User response schema."""

    model_config = {"from_attributes": True}

    id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """User profile update schema."""

    email: Optional[EmailStr] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email if provided."""
        if v is not None:
            return v.lower()
        return v


class PasswordChange(BaseModel):
    """Password change schema."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that new passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New passwords do not match")
        return v


class PasswordChangeResponse(BaseModel):
    """Password change response schema."""

    message: str = "Password changed successfully"
