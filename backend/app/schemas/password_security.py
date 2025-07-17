"""Password security related Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class PasswordPolicySchema(BaseModel):
    """Schema for password policy configuration."""
    
    id: Optional[int] = None
    organization_id: Optional[int] = Field(None, description="Organization ID (null for global policy)")
    name: str = Field(..., min_length=1, max_length=100, description="Policy name")
    description: Optional[str] = Field(None, max_length=500, description="Policy description")
    
    # Complexity requirements
    minimum_length: int = Field(8, ge=1, le=128, description="Minimum password length")
    require_uppercase: bool = Field(True, description="Require uppercase letters")
    require_lowercase: bool = Field(True, description="Require lowercase letters")
    require_numbers: bool = Field(True, description="Require numbers")
    require_special_chars: bool = Field(True, description="Require special characters")
    special_chars_set: str = Field("!@#$%^&*()_+-=[]{}|;:,.<>?", description="Allowed special characters")
    
    # History and expiration
    password_history_count: int = Field(3, ge=0, le=20, description="Password history to remember")
    password_expiry_days: int = Field(90, ge=0, le=365, description="Password expiry in days")
    password_warning_days: int = Field(7, ge=0, le=30, description="Warning days before expiry")
    
    # Account lockout
    max_failed_attempts: int = Field(5, ge=1, le=20, description="Max failed login attempts")
    lockout_duration_minutes: int = Field(30, ge=1, le=1440, description="Lockout duration in minutes")
    
    # Restrictions
    disallow_user_info: bool = Field(True, description="Disallow user information in password")
    disallow_common_passwords: bool = Field(True, description="Disallow common passwords")
    
    is_active: bool = Field(True, description="Whether policy is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('password_warning_days')
    def warning_days_must_be_less_than_expiry(cls, v, values):
        if 'password_expiry_days' in values and v >= values['password_expiry_days']:
            raise ValueError('Warning days must be less than expiry days')
        return v

    class Config:
        from_attributes = True


class PasswordPolicyCreate(BaseModel):
    """Schema for creating a password policy."""
    
    organization_id: Optional[int] = Field(None, description="Organization ID (null for global policy)")
    name: str = Field(..., min_length=1, max_length=100, description="Policy name")
    description: Optional[str] = Field(None, max_length=500, description="Policy description")
    
    # Complexity requirements
    minimum_length: int = Field(8, ge=1, le=128, description="Minimum password length")
    require_uppercase: bool = Field(True, description="Require uppercase letters")
    require_lowercase: bool = Field(True, description="Require lowercase letters")
    require_numbers: bool = Field(True, description="Require numbers")
    require_special_chars: bool = Field(True, description="Require special characters")
    special_chars_set: str = Field("!@#$%^&*()_+-=[]{}|;:,.<>?", description="Allowed special characters")
    
    # History and expiration
    password_history_count: int = Field(3, ge=0, le=20, description="Password history to remember")
    password_expiry_days: int = Field(90, ge=0, le=365, description="Password expiry in days")
    password_warning_days: int = Field(7, ge=0, le=30, description="Warning days before expiry")
    
    # Account lockout
    max_failed_attempts: int = Field(5, ge=1, le=20, description="Max failed login attempts")
    lockout_duration_minutes: int = Field(30, ge=1, le=1440, description="Lockout duration in minutes")
    
    # Restrictions
    disallow_user_info: bool = Field(True, description="Disallow user information in password")
    disallow_common_passwords: bool = Field(True, description="Disallow common passwords")


class PasswordValidationRequest(BaseModel):
    """Schema for password validation request."""
    
    password: str = Field(..., min_length=1, description="Password to validate")
    user_id: int = Field(..., description="User ID for context-specific validation")
    check_history: bool = Field(True, description="Check against password history")


class PasswordValidationResponse(BaseModel):
    """Schema for password validation response."""
    
    is_valid: bool = Field(..., description="Whether password is valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    strength_score: int = Field(..., ge=0, le=100, description="Password strength score (0-100)")
    policy_name: str = Field(..., description="Name of the policy used for validation")


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    
    current_password: Optional[str] = Field(None, description="Current password (required unless force change)")
    new_password: str = Field(..., min_length=1, description="New password")
    force_change: bool = Field(False, description="Force change without current password verification")


class PasswordChangeResponse(BaseModel):
    """Schema for password change response."""
    
    success: bool = Field(..., description="Whether password change was successful")
    message: Optional[str] = Field(None, description="Success or error message")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")
    strength_score: Optional[int] = Field(None, ge=0, le=100, description="New password strength score")


class PasswordExpiryInfo(BaseModel):
    """Schema for password expiry information."""
    
    is_expired: bool = Field(..., description="Whether password is expired")
    days_until_expiry: int = Field(..., description="Days until expiry (negative if expired)")
    warning: bool = Field(..., description="Whether user should be warned")
    password_age_days: int = Field(..., description="Days since password was last changed")
    policy_expiry_days: int = Field(..., description="Policy expiry period in days")


class AccountLockoutInfo(BaseModel):
    """Schema for account lockout information."""
    
    locked: bool = Field(..., description="Whether account is locked")
    locked_until: Optional[datetime] = Field(None, description="When lock expires")
    lockout_duration_minutes: Optional[int] = Field(None, description="Lockout duration in minutes")
    failed_attempts: int = Field(..., description="Number of failed login attempts")
    attempts_remaining: Optional[int] = Field(None, description="Remaining attempts before lockout")


class SecurityStatusResponse(BaseModel):
    """Schema for comprehensive user security status."""
    
    user_id: int = Field(..., description="User ID")
    account_locked: bool = Field(..., description="Whether account is locked")
    password_expired: bool = Field(..., description="Whether password is expired")
    password_expiry_warning: bool = Field(..., description="Whether to show expiry warning")
    days_until_expiry: int = Field(..., description="Days until password expires")
    failed_login_attempts: int = Field(..., description="Current failed login attempts")
    must_change_password: bool = Field(..., description="Whether user must change password")
    last_login: Optional[datetime] = Field(None, description="Last successful login")
    password_last_changed: datetime = Field(..., description="When password was last changed")
    policy_name: str = Field(..., description="Applied password policy name")


class PasswordStrengthRequest(BaseModel):
    """Schema for password strength check request."""
    
    password: str = Field(..., min_length=1, description="Password to check")
    user_id: Optional[int] = Field(None, description="User ID for context (optional)")


class PasswordStrengthResponse(BaseModel):
    """Schema for password strength response."""
    
    strength_score: int = Field(..., ge=0, le=100, description="Password strength score (0-100)")
    strength_level: str = Field(..., description="Strength level (weak/fair/good/strong)")
    feedback: List[str] = Field(default_factory=list, description="Improvement suggestions")

    @validator('strength_level', pre=True, always=True)
    def determine_strength_level(cls, v, values):
        if 'strength_score' in values:
            score = values['strength_score']
            if score < 25:
                return "weak"
            elif score < 50:
                return "fair"
            elif score < 75:
                return "good"
            else:
                return "strong"
        return v


class UnlockAccountRequest(BaseModel):
    """Schema for account unlock request."""
    
    user_id: int = Field(..., description="User ID to unlock")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for unlocking")


class ForcePasswordChangeRequest(BaseModel):
    """Schema for forcing password change."""
    
    user_id: int = Field(..., description="User ID to force password change")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for forcing change")


class SecurityEventLog(BaseModel):
    """Schema for security event logging."""
    
    event_type: str = Field(..., description="Type of security event")
    user_id: int = Field(..., description="User ID associated with event")
    details: dict = Field(default_factory=dict, description="Event details")
    ip_address: Optional[str] = Field(None, description="IP address of the event")
    user_agent: Optional[str] = Field(None, description="User agent of the event")


class SecurityMetrics(BaseModel):
    """Schema for security metrics and statistics."""
    
    total_users: int = Field(..., description="Total number of users")
    locked_accounts: int = Field(..., description="Number of locked accounts")
    expired_passwords: int = Field(..., description="Number of expired passwords")
    weak_passwords: int = Field(..., description="Number of weak passwords")
    recent_failures: int = Field(..., description="Recent failed login attempts")
    policy_violations: int = Field(..., description="Recent policy violations")
    last_updated: datetime = Field(..., description="When metrics were last calculated")