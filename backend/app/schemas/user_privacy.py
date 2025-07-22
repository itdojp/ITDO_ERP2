"""User privacy settings schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VisibilityLevel(str, Enum):
    """Visibility level enumeration."""

    PUBLIC = "public"  # Visible to everyone
    ORGANIZATION = "organization"  # Visible to same organization
    DEPARTMENT = "department"  # Visible to same department
    PRIVATE = "private"  # Visible to self only


class PrivacySettingsBase(BaseModel):
    """Base privacy settings schema."""

    # Profile visibility settings
    profile_visibility: VisibilityLevel = Field(
        default=VisibilityLevel.ORGANIZATION,
        description="Who can view user profile",
    )
    email_visibility: VisibilityLevel = Field(
        default=VisibilityLevel.ORGANIZATION,
        description="Who can view email address",
    )
    phone_visibility: VisibilityLevel = Field(
        default=VisibilityLevel.DEPARTMENT,
        description="Who can view phone number",
    )
    activity_visibility: VisibilityLevel = Field(
        default=VisibilityLevel.ORGANIZATION,
        description="Who can view user activity",
    )

    # Online status and messaging
    show_online_status: bool = Field(
        default=True,
        description="Show online/offline status",
    )
    allow_direct_messages: bool = Field(
        default=True,
        description="Allow receiving direct messages",
    )

    # Search settings
    searchable_by_email: bool = Field(
        default=True,
        description="Can be found by email search",
    )
    searchable_by_name: bool = Field(
        default=True,
        description="Can be found by name search",
    )


class PrivacySettingsCreate(PrivacySettingsBase):
    """Schema for creating privacy settings."""



class PrivacySettingsUpdate(BaseModel):
    """Schema for updating privacy settings."""

    profile_visibility: Optional[VisibilityLevel] = None
    email_visibility: Optional[VisibilityLevel] = None
    phone_visibility: Optional[VisibilityLevel] = None
    activity_visibility: Optional[VisibilityLevel] = None
    show_online_status: Optional[bool] = None
    allow_direct_messages: Optional[bool] = None
    searchable_by_email: Optional[bool] = None
    searchable_by_name: Optional[bool] = None


class PrivacySettingsResponse(PrivacySettingsBase):
    """Schema for privacy settings response."""

    id: int = Field(description="Settings ID")
    user_id: int = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        from_attributes = True


class PrivacyCheckResult(BaseModel):
    """Schema for privacy check result."""

    allowed: bool = Field(description="Whether access is allowed")
    reason: Optional[str] = Field(
        default=None, description="Reason for access decision"
    )
    requires_permission: Optional[str] = Field(
        default=None, description="Required permission if denied"
    )


class FilteredUserData(BaseModel):
    """Schema for privacy-filtered user data."""

    id: int = Field(description="User ID (always visible)")
    full_name: str = Field(description="Full name (visibility controlled)")
    email: Optional[str] = Field(default=None, description="Email (may be hidden)")
    phone: Optional[str] = Field(default=None, description="Phone (may be hidden)")
    profile_image_url: Optional[str] = Field(
        default=None, description="Profile image (may be hidden)"
    )
    is_online: Optional[bool] = Field(
        default=None, description="Online status (may be hidden)"
    )
    last_activity: Optional[datetime] = Field(
        default=None, description="Last activity (may be hidden)"
    )
