"""Session management schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    """Session creation request (internal use)."""

    user_id: int
    session_token: str
    refresh_token: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime


class SessionInvalidateRequest(BaseModel):
    """Session invalidation request."""

    session_id: int


class SessionUpdateRequest(BaseModel):
    """Session update request."""

    last_activity: datetime = Field(default_factory=datetime.now)


class SessionResponse(BaseModel):
    """Session response."""

    id: int
    ip_address: str
    user_agent: str
    device_name: str | None = None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_current: bool = False

    class Config:
        """Pydantic config."""

        orm_mode = True


class SessionListResponse(BaseModel):
    """Session list response."""

    sessions: list[SessionResponse]
    total: int


class SessionConfigurationResponse(BaseModel):
    """Session configuration response."""

    session_timeout_hours: int = Field(
        ..., description="Default session timeout in hours"
    )
    max_session_timeout_hours: int = Field(
        ..., description="Maximum allowed session timeout"
    )
    refresh_token_days: int = Field(..., description="Refresh token validity in days")
    allow_multiple_sessions: bool = Field(
        ..., description="Whether multiple sessions are allowed"
    )
    max_concurrent_sessions: int = Field(
        ..., description="Maximum number of concurrent sessions"
    )
    require_mfa_for_new_device: bool = Field(
        ..., description="Require MFA for new devices"
    )
    notify_new_device_login: bool = Field(
        ..., description="Send notification for new device login"
    )
    notify_suspicious_activity: bool = Field(
        ..., description="Send notification for suspicious activity"
    )


class SessionConfigUpdate(BaseModel):
    """Session configuration update schema."""

    session_timeout_hours: int | None = Field(None, ge=1, le=24)
    allow_multiple_sessions: bool | None = None
    max_concurrent_sessions: int | None = Field(None, ge=1, le=10)
    require_mfa_for_new_device: bool | None = None
    notify_new_device_login: bool | None = None
    notify_suspicious_activity: bool | None = None


class TrustedDeviceRequest(BaseModel):
    """Trusted device request schema."""

    device_id: str | None = Field(None, max_length=100)
    device_name: str | None = Field(None, max_length=100)


class ActiveSessionsResponse(BaseModel):
    """Active sessions response (legacy)."""

    sessions: list[SessionResponse]
    total: int
    limit: int
