"""Password reset schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr = Field(..., description="User email address")


class PasswordResetResponse(BaseModel):
    """Password reset response."""

    success: bool
    message: str


class VerifyResetTokenRequest(BaseModel):
    """Verify reset token request."""

    token: str = Field(..., description="Reset token")
    verification_code: str | None = Field(None, description="Optional verification code")


class VerifyResetTokenResponse(BaseModel):
    """Verify reset token response."""

    valid: bool
    user_email: str | None = None
    expires_at: datetime | None = None


class ResetPasswordRequest(BaseModel):
    """Reset password request."""

    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    verification_code: str | None = Field(None, description="Optional verification code")


class PasswordPolicyResponse(BaseModel):
    """Password policy response."""

    min_length: int = Field(default=8)
    require_uppercase: bool = Field(default=True)
    require_lowercase: bool = Field(default=True)
    require_numbers: bool = Field(default=True)
    require_special: bool = Field(default=True)
    min_categories: int = Field(default=3, description="Minimum number of character categories")
    prevent_reuse_count: int = Field(default=3, description="Number of previous passwords to check")