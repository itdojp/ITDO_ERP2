"""
CC02 v38.0 Enhanced Authentication Schemas
認証システム用のPydanticスキーマ定義
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

# =============================================================================
# Token Models
# =============================================================================


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []


# =============================================================================
# User Authentication Models
# =============================================================================


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# =============================================================================
# Multi-Factor Authentication Models
# =============================================================================


class MFASetupRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=100)


class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str  # Base64 encoded QR code image
    backup_codes: List[str]


class MFAVerifyRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=6)


class MFADevice(BaseModel):
    id: str
    device_name: str
    device_type: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


# =============================================================================
# API Key Management Models
# =============================================================================


class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    scopes: List[str] = Field(default=["read"])
    expires_at: Optional[datetime] = None

    @validator("expires_at")
    def validate_expires_at(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        return v


class APIKeyResponse(BaseModel):
    id: str
    key_id: str
    api_key: str  # Only returned once during creation
    name: str
    description: Optional[str]
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]


class APIKeyInfo(BaseModel):
    id: str
    key_id: str
    name: str
    description: Optional[str]
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    api_keys: List[APIKeyInfo]


# =============================================================================
# Session Management Models
# =============================================================================


class SessionInfo(BaseModel):
    session_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    last_activity: Optional[datetime]

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]


# =============================================================================
# Password Management Models
# =============================================================================


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


# =============================================================================
# OAuth2 Models
# =============================================================================


class OAuth2AuthorizeRequest(BaseModel):
    response_type: str = Field(..., regex="^code$")
    client_id: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)
    scope: str = Field(default="read")
    state: Optional[str] = None


class OAuth2TokenRequest(BaseModel):
    grant_type: str = Field(..., regex="^authorization_code$")
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)


class OAuth2Client(BaseModel):
    client_id: str
    client_name: str
    redirect_uris: List[str]
    scopes: List[str]
    is_active: bool

    class Config:
        from_attributes = True


# =============================================================================
# Permission & Role Models
# =============================================================================


class PermissionCheck(BaseModel):
    permission: str = Field(..., min_length=1, max_length=100)
    resource: Optional[str] = Field(None, max_length=100)


class PermissionResponse(BaseModel):
    user_id: str
    permission: str
    resource: Optional[str]
    has_permission: bool


class RoleAssignRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    role_name: str = Field(..., min_length=1, max_length=50)


class Role(BaseModel):
    id: str
    name: str
    description: Optional[str]
    permissions: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Permission(BaseModel):
    id: str
    name: str
    resource: str
    action: str
    description: Optional[str]

    class Config:
        from_attributes = True


# =============================================================================
# Login Attempt & Security Models
# =============================================================================


class LoginAttempt(BaseModel):
    id: str
    identifier: str  # username or email
    success: bool
    ip_address: Optional[str]
    user_agent: Optional[str]
    attempted_at: datetime
    failure_reason: Optional[str]

    class Config:
        from_attributes = True


class SecurityLog(BaseModel):
    id: str
    user_id: Optional[str]
    event_type: str
    event_description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    severity: str  # low, medium, high, critical

    class Config:
        from_attributes = True


# =============================================================================
# Account Management Models
# =============================================================================


class AccountInfo(BaseModel):
    user: UserResponse
    mfa_devices: List[MFADevice]
    active_sessions: int
    api_keys_count: int
    last_password_change: Optional[datetime]
    account_locked: bool
    failed_login_attempts: int


class AccountSecurity(BaseModel):
    password_strength: str  # weak, medium, strong
    mfa_enabled: bool
    recent_suspicious_activity: bool
    last_security_scan: datetime
    security_score: int  # 0-100


# =============================================================================
# Audit & Compliance Models
# =============================================================================


class AuditEvent(BaseModel):
    id: str
    user_id: Optional[str]
    event_type: str
    resource_type: str
    resource_id: Optional[str]
    action: str
    result: str  # success, failure, error
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class ComplianceReport(BaseModel):
    report_id: str
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_type: Dict[str, int]
    security_incidents: int
    policy_violations: int
    compliance_score: float


# =============================================================================
# Rate Limiting Models
# =============================================================================


class RateLimitInfo(BaseModel):
    identifier: str
    limit: int
    remaining: int
    reset_time: datetime
    blocked: bool


class RateLimitResponse(BaseModel):
    rate_limit: RateLimitInfo
    message: str


# =============================================================================
# Webhook Models
# =============================================================================


class WebhookEvent(BaseModel):
    event_id: str
    event_type: str
    user_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    signature: str


class WebhookConfig(BaseModel):
    id: str
    url: str
    events: List[str]
    secret: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Advanced Security Models
# =============================================================================


class IPWhitelist(BaseModel):
    id: str
    ip_address: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class DeviceInfo(BaseModel):
    device_id: str
    device_name: str
    device_type: str  # mobile, desktop, tablet
    os: str
    browser: str
    is_trusted: bool
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class TrustedDevice(BaseModel):
    id: str
    user_id: str
    device_info: DeviceInfo
    trusted_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True
