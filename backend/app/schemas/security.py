"""Security-related schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""

    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    require_mfa: bool = Field(..., description="Whether MFA should be required")
    risk_factors: list[str] = Field(..., description="Identified risk factors")
    recommendations: list[str | None] = Field(
        ..., description="Security recommendations"
    )


class SessionAnalyticsResponse(BaseModel):
    """Session analytics response."""

    total_sessions: int
    active_sessions: int
    unique_devices: int
    unique_locations: int
    device_breakdown: dict[str, int] = Field(..., description="Sessions by device type")
    location_breakdown: dict[str, int] = Field(..., description="Sessions by location")
    recent_activities: dict[str, int] = Field(
        ..., description="Activity counts by type"
    )


class SecurityEventResponse(BaseModel):
    """Security event response."""

    id: int
    event_type: str
    timestamp: datetime
    ip_address: str
    device_info: dict = Field(default_factory=dict)
    details: str | None = None
    severity: str = Field(..., pattern="^(low|medium|high)$")


class DeviceTrustRequest(BaseModel):
    """Device trust request."""

    device_fingerprint: str = Field(..., description="Device fingerprint")
    device_name: str | None = Field(None, description="Optional device name")


class SecurityAnalyticsResponse(BaseModel):
    """Security analytics response."""

    failed_login_attempts: int
    suspicious_activities: int
    security_score: int = Field(..., ge=0, le=100)
    last_security_review: datetime | None = None
    recommendations_count: int
