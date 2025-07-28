"""Multi-Factor Authentication schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MFADeviceResponse(BaseModel):
    """MFA device response."""

    id: int
    device_name: str
    device_type: str
    is_primary: bool
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    verified_at: Optional[datetime]

    class Config:
        """Pydantic config."""

        orm_mode = True


class MFADeviceListResponse(BaseModel):
    """MFA device list response."""

    devices: list[MFADeviceResponse]
    total: int
    has_primary: bool


class MFABackupCodesResponse(BaseModel):
    """MFA backup codes response."""

    codes: list[str]
    created_at: datetime
    warning: str = "Please store these codes in a safe place. Each code can only be used once."


class MFAChallengeRequest(BaseModel):
    """MFA challenge request."""

    user_id: int
    challenge_type: str = Field(..., pattern="^(login|sensitive_action|verification)$")
    device_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class MFAChallengeVerifyRequest(BaseModel):
    """MFA challenge verification request."""

    challenge_token: str
    code: str = Field(..., pattern=r"^\d{6}$")


class MFAStatusResponse(BaseModel):
    """MFA status response."""

    enabled: bool
    devices_count: int
    has_backup_codes: bool
    last_verified_at: Optional[datetime]