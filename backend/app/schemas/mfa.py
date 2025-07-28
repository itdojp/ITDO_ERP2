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
    is_active: bool = True
    created_at: datetime
    last_used_at: datetime | None = None

    class Config:
        """Pydantic config."""

        orm_mode = True


class MFAStatusResponse(BaseModel):
    """MFA status response."""

    mfa_enabled: bool
    mfa_setup_at: datetime | None = None
    devices: list[MFADeviceResponse]
    backup_codes_count: int


class MFASetupResponse(BaseModel):
    """MFA setup response with TOTP details."""

    secret: str = Field(..., description="TOTP secret key")
    qr_code_uri: str = Field(..., description="QR code provisioning URI")
    manual_entry_key: str = Field(..., description="Manual entry key")
    manual_entry_setup: dict = Field(..., description="Manual setup parameters")


class MFAVerifySetupRequest(BaseModel):
    """MFA setup verification request."""

    code: str = Field(..., min_length=6, max_length=6, description="TOTP code")
    device_name: str = Field(..., min_length=1, max_length=100, description="Device name")


class MFAEnableRequest(BaseModel):
    """MFA enable request."""

    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(default="totp", pattern="^(totp|sms|email)$")


class MFADisableRequest(BaseModel):
    """MFA disable request."""

    password: str = Field(..., description="User password for confirmation")
    reason: str | None = Field(None, description="Reason for disabling MFA")


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""

    code: str = Field(..., min_length=6, max_length=6, description="TOTP or backup code")
    trust_device: bool = Field(default=False, description="Trust this device")


class BackupCodesResponse(BaseModel):
    """Backup codes response."""

    backup_codes: list[str]
    warning: str = Field(..., description="Warning message about backup codes")


class MFARecoveryRequest(BaseModel):
    """MFA recovery request using backup code."""

    backup_code: str = Field(..., description="Backup code")
    new_device_name: str | None = Field(None, description="Name for new device after recovery")


# Legacy schemas for compatibility
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