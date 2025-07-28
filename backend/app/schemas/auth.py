"""Authentication schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    remember_me: bool = Field(default=False, description="Keep session active")


class RefreshRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str = Field(..., description="Refresh token")


class GoogleLoginRequest(BaseModel):
    """Google OAuth login request."""

    id_token: str = Field(..., description="Google ID token from OAuth")
    access_token: Optional[str] = Field(None, description="Google access token")


class MFASetupRequest(BaseModel):
    """MFA setup request."""

    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(default="totp", pattern="^(totp|sms|email)$")
    phone_number: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    email: Optional[EmailStr] = None

    @validator("phone_number")
    def validate_phone_for_sms(cls, v, values):
        """Validate phone number is provided for SMS type."""
        if values.get("device_type") == "sms" and not v:
            raise ValueError("Phone number is required for SMS MFA")
        return v

    @validator("email")
    def validate_email_for_email_type(cls, v, values):
        """Validate email is provided for email type."""
        if values.get("device_type") == "email" and not v:
            raise ValueError("Email is required for email MFA")
        return v


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""

    code: str = Field(..., pattern=r"^\d{6}$", description="6-digit TOTP code")
    challenge_token: Optional[str] = None


class MFABackupCodeVerifyRequest(BaseModel):
    """MFA backup code verification request."""

    backup_code: str = Field(..., min_length=8, max_length=20)
    challenge_token: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8)


class LogoutRequest(BaseModel):
    """Logout request."""

    all_sessions: bool = Field(default=False, description="Logout from all sessions")


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=86400, description="Token expiration in seconds")
    requires_mfa: bool = Field(default=False, description="MFA required flag")
    mfa_token: Optional[str] = Field(None, description="Temporary MFA challenge token")


class MFASetupResponse(BaseModel):
    """MFA setup response."""

    device_id: int
    secret: Optional[str] = None
    qr_code: Optional[str] = None
    backup_codes: Optional[list[str]] = None
    verification_required: bool = True


class MFAChallengeResponse(BaseModel):
    """MFA challenge response."""

    challenge_token: str
    expires_at: datetime
    devices: list[dict]  # List of available MFA devices


class AuthenticatedUser(BaseModel):
    """Authenticated user response."""

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    mfa_enabled: bool
    last_login_at: Optional[datetime]
    session_timeout_hours: int = 8
    idle_timeout_minutes: int = 30


class SessionInfo(BaseModel):
    """Session information."""

    id: int
    session_token: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False


class SessionListResponse(BaseModel):
    """Session list response."""

    sessions: list[SessionInfo]
    total: int
    active_count: int


class SessionSettingsRequest(BaseModel):
    """Session settings request."""

    session_timeout_hours: int = Field(..., ge=1, le=24)
    idle_timeout_minutes: int = Field(..., ge=15, le=120)


class SessionSettingsResponse(BaseModel):
    """Session settings response."""

    session_timeout_hours: int
    idle_timeout_minutes: int
