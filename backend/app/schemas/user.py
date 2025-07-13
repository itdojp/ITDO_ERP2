"""User schemas."""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(
        ..., min_length=1, max_length=100, description="User full name"
    )
    phone: str | None = Field(None, max_length=20, description="User phone number")
    is_active: bool = Field(default=True, description="Whether user is active")


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8, description="User password")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least 3 of: uppercase, lowercase, digit, special char
        checks = [
            bool(re.search(r"[A-Z]", v)),  # Has uppercase
            bool(re.search(r"[a-z]", v)),  # Has lowercase
            bool(re.search(r"\d", v)),  # Has digit
            bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", v)),  # Has special char
        ]

        if sum(checks) < 3:
            raise ValueError(
                "Password must contain at least 3 of: uppercase letter, "
                "lowercase letter, digit, special character"
            )

        return v


class UserResponse(UserBase):
    """User response schema."""

    id: int = Field(..., description="User ID")
    phone: str | None = Field(None, max_length=20, description="User phone number")
    profile_image_url: str | None = Field(
        None, max_length=500, description="Profile image URL"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class UserInDB(UserResponse):
    """User in database schema."""

    hashed_password: str = Field(..., description="Hashed password")
    is_superuser: bool = Field(default=False, description="Whether user is superuser")


# Additional schemas for backwards compatibility
class UserUpdate(BaseModel):
    """User update schema."""

    full_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    profile_image_url: str | None = Field(
        None, max_length=500, description="Profile image URL"
    )
    is_active: bool | None = None


# UserCreateExtended is defined in user_extended.py


# UserSearchParams is defined in user_extended.py


class UserBasic(BaseModel):
    """Basic user information."""

    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    is_active: bool = Field(..., description="Whether user is active")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
