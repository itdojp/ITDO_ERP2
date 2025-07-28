"""User authentication and management schemas."""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserProfileUpdate(BaseModel):
    """User profile update schema."""

    full_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    bio: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=100)
    website: str | None = Field(None, max_length=255)


class PasswordChange(BaseModel):
    """Password change schema."""

    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        """Validate password strength and difference."""
        values = info.data
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("New password must be different from current password")

        # Same validation as UserCreate
        checks = [
            bool(re.search(r"[A-Z]", v)),
            bool(re.search(r"[a-z]", v)),
            bool(re.search(r"\d", v)),
            bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", v)),
        ]

        if sum(checks) < 3:
            raise ValueError(
                "Password must contain at least 3 of: uppercase, lowercase, digit, special character"
            )

        return v


class AdminPasswordReset(BaseModel):
    """Admin password reset schema."""

    new_password: str = Field(..., min_length=8)
    must_change: bool = True


class UserMFAStatus(BaseModel):
    """User MFA status."""

    mfa_enabled: bool
    mfa_devices_count: int
    has_backup_codes: bool
    last_verified_at: datetime | None = None


class UserActivitySummary(BaseModel):
    """User activity summary."""

    total_logins: int
    last_login_at: datetime | None = None
    failed_login_attempts: int
    active_sessions: int
    last_password_change: datetime


class UserListResponse(BaseModel):
    """User list response."""

    users: list["UserResponse"]
    total: int
    page: int
    page_size: int


class UserAuthResponse(BaseModel):
    """User response for authentication endpoints."""

    id: int
    email: EmailStr
    full_name: str
    phone: str | None = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None
    mfa_enabled: bool = Field(alias="mfa_required")
    department_id: int | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True
        populate_by_name = True


# Import for forward reference
from app.schemas.user import UserResponse
