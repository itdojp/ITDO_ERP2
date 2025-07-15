"""User profile related schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information."""

    full_name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=500)
    location: str | None = Field(None, max_length=100)
    website: HttpUrl | str | None = None

    @field_validator("website", mode="before")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        """Validate website URL."""
        if v and not v.startswith(("http://", "https://")):
            return f"https://{v}"
        return v


class ProfileImageUploadResponse(BaseModel):
    """Response schema for profile image upload."""

    url: str
    size: int
    content_type: str
    uploaded_at: datetime


class UserProfileSettingsUpdate(BaseModel):
    """Schema for updating user profile settings."""

    language: str | None = Field(None, pattern="^[a-z]{2}$")
    timezone: str | None = None
    date_format: str | None = Field(
        None, pattern="^(YYYY-MM-DD|DD/MM/YYYY|MM/DD/YYYY)$"
    )
    time_format: Literal["12h", "24h"] | None = None
    notification_email: bool | None = None
    notification_push: bool | None = None


class UserProfileSettings(BaseModel):
    """Schema for user profile settings."""

    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: Literal["12h", "24h"] = "24h"
    notification_email: bool = True
    notification_push: bool = True
    updated_at: datetime


class UserPrivacySettingsUpdate(BaseModel):
    """Schema for updating user privacy settings."""

    profile_visibility: (
        Literal["public", "organization", "department", "private"] | None
    ) = None
    email_visibility: (
        Literal["public", "organization", "department", "private"] | None
    ) = None
    phone_visibility: (
        Literal["public", "organization", "department", "private"] | None
    ) = None
    allow_direct_messages: bool | None = None
    show_online_status: bool | None = None


class UserPrivacySettings(BaseModel):
    """Schema for user privacy settings."""

    profile_visibility: Literal["public", "organization", "department", "private"] = (
        "organization"
    )
    email_visibility: Literal["public", "organization", "department", "private"] = (
        "organization"
    )
    phone_visibility: Literal["public", "organization", "department", "private"] = (
        "department"
    )
    allow_direct_messages: bool = True
    show_online_status: bool = True
    updated_at: datetime


class UserProfileResponse(BaseModel):
    """Response schema for user profile with privacy applied."""

    id: int
    full_name: str
    email: str | None  # May be hidden based on privacy settings
    phone: str | None  # May be hidden based on privacy settings
    profile_image_url: str | None
    bio: str | None
    location: str | None
    website: str | None
    is_online: bool | None  # May be hidden based on privacy settings
    last_seen_at: datetime | None  # May be hidden based on privacy settings
