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
    user_id: int
    session_token: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    requires_verification: bool = False
    security_alert: Optional[str] = None

    class Config:
        """Pydantic config."""

        orm_mode = True


class ActiveSessionsResponse(BaseModel):
    """Active sessions response."""

    sessions: list[SessionResponse]
    total: int
    limit: int