"""
ITDO ERP Backend - Security Configuration Module
Comprehensive security settings and configurations for production deployment
"""

from __future__ import annotations

import os
from typing import List, Optional, Set

from pydantic import BaseSettings, Field, validator


class SecuritySettings(BaseSettings):
    """Security configuration settings for the ITDO ERP system"""

    # Authentication settings
    secret_key: str = Field(..., min_length=32)
    algorithm: str = Field(
        default="HS256", regex="^(HS256|HS384|HS512|RS256|RS384|RS512)$"
    )
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    bcrypt_rounds: int = Field(default=12, ge=10, le=15)
    password_min_length: int = Field(default=8, ge=8, le=128)

    # JWT Configuration
    jwt_issuer: str = Field(default="itdo-erp-system")
    jwt_audience: str = Field(default="itdo-erp-users")

    # Security Headers
    security_headers_enabled: bool = Field(default=True)
    x_frame_options: str = Field(default="DENY")
    x_content_type_options: str = Field(default="nosniff")
    x_xss_protection: str = Field(default="1; mode=block")
    strict_transport_security: str = Field(
        default="max-age=31536000; includeSubDomains"
    )
    content_security_policy: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
        "font-src 'self' https:; connect-src 'self' https:"
    )
    referrer_policy: str = Field(default="strict-origin-when-cross-origin")

    # Session Security
    session_cookie_secure: bool = Field(
        default=False
    )  # Set to True in production with HTTPS
    session_cookie_httponly: bool = Field(default=True)
    session_cookie_samesite: str = Field(default="strict", regex="^(strict|lax|none)$")
    csrf_protection_enabled: bool = Field(default=True)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=100, ge=1, le=10000)
    rate_limit_auth_requests_per_minute: int = Field(default=5, ge=1, le=100)
    rate_limit_burst_size: int = Field(default=10, ge=1, le=100)
    rate_limit_storage_url: Optional[str] = Field(default=None)

    # IP Security
    admin_ip_whitelist: List[str] = Field(default_factory=lambda: ["127.0.0.1", "::1"])
    blocked_ip_addresses: Set[str] = Field(default_factory=set)
    enable_ip_blocking: bool = Field(default=True)
    max_failed_login_attempts: int = Field(default=5, ge=1, le=50)
    lockout_duration_minutes: int = Field(default=15, ge=1, le=1440)

    # HTTPS and TLS
    force_https: bool = Field(default=False)  # Set to True in production
    min_tls_version: str = Field(default="1.2", regex="^(1.0|1.1|1.2|1.3)$")

    # API Security
    api_key_header_name: str = Field(default="X-API-Key")
    require_api_key_for_admin: bool = Field(default=True)
    api_versioning_enabled: bool = Field(default=True)

    # File Upload Security
    max_file_size_mb: int = Field(default=50, ge=1, le=1000)
    allowed_file_types: List[str] = Field(
        default_factory=lambda: [
            "pdf",
            "xlsx",
            "xls",
            "csv",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "zip",
            "txt",
        ]
    )
    upload_path: str = Field(default="/opt/itdo-erp/uploads")
    scan_uploads_for_malware: bool = Field(default=True)

    # Database Security
    database_ssl_enabled: bool = Field(default=False)
    database_ssl_cert_path: Optional[str] = Field(default=None)
    database_connection_encryption: bool = Field(default=True)

    # Audit and Compliance
    enable_audit_logging: bool = Field(default=True)
    audit_log_path: str = Field(default="/var/log/itdo-erp/audit.log")
    audit_sensitive_operations: bool = Field(default=True)
    gdpr_compliance_enabled: bool = Field(default=True)
    pci_dss_compliance: bool = Field(default=False)
    data_retention_days: int = Field(default=2555, ge=1)  # 7 years for financial data

    # Encryption
    encryption_key: Optional[str] = Field(default=None, min_length=32)
    encrypt_sensitive_data: bool = Field(default=True)
    encryption_algorithm: str = Field(default="AES-256-GCM")

    # Backup Security
    backup_encryption_enabled: bool = Field(default=True)
    backup_encryption_key: Optional[str] = Field(default=None, min_length=32)
    backup_access_control: bool = Field(default=True)

    # Network Security
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    enable_network_security_monitoring: bool = Field(default=True)

    # Development/Debug Security
    debug_mode_allowed_ips: List[str] = Field(
        default_factory=lambda: ["127.0.0.1", "::1"]
    )
    production_mode: bool = Field(default=True)

    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength"""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")

        # Check for common weak patterns
        weak_patterns = ["12345", "password", "secret", "key", "admin"]
        if any(pattern in v.lower() for pattern in weak_patterns):
            raise ValueError("Secret key contains weak patterns")

        return v

    @validator("admin_ip_whitelist", pre=True)
    def parse_ip_whitelist(cls, v) -> List[str]:
        """Parse IP whitelist from string or list"""
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return v

    @validator("allowed_file_types", pre=True)
    def parse_file_types(cls, v) -> List[str]:
        """Parse allowed file types"""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",") if ext.strip()]
        return [ext.lower() for ext in v]

    class Config:
        env_prefix = ""
        case_sensitive = False
        env_file = ".env"


class ProductionSecuritySettings(SecuritySettings):
    """Production-specific security settings with stricter defaults"""

    # Override defaults for production
    session_cookie_secure: bool = Field(default=True)
    force_https: bool = Field(default=True)
    production_mode: bool = Field(default=True)
    debug_mode_allowed_ips: List[str] = Field(
        default_factory=list
    )  # No debug in production
    rate_limit_requests_per_minute: int = Field(default=60)  # More restrictive

    # Additional production validations
    @validator("secret_key")
    def validate_production_secret_key(cls, v: str) -> str:
        """Enhanced validation for production secret key"""
        if len(v) < 64:
            raise ValueError(
                "Production secret key must be at least 64 characters long"
            )

        # Check entropy (basic check for randomness)
        unique_chars = len(set(v))
        if unique_chars < 16:
            raise ValueError("Secret key has insufficient entropy")

        return v


def get_security_settings(production: bool = None) -> SecuritySettings:
    """
    Get security settings based on environment

    Args:
        production: If True, use production settings. If None, auto-detect from environment

    Returns:
        SecuritySettings instance configured for the environment
    """
    if production is None:
        production = os.getenv("ENVIRONMENT", "development").lower() in (
            "production",
            "prod",
        )

    if production:
        return ProductionSecuritySettings()
    else:
        return SecuritySettings()


# Security middleware configuration
SECURITY_MIDDLEWARE_CONFIG = {
    "trusted_hosts": ["*"],  # Configure appropriately for production
    "allowed_hosts": ["*"],  # Configure appropriately for production
    "https_redirect": False,  # Set to True in production
    "force_https": False,  # Set to True in production
}


# CORS security configuration
CORS_SECURITY_CONFIG = {
    "allow_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": ["*"],
    "expose_headers": ["X-Process-Time", "X-Request-ID"],
    "max_age": 3600,
}


# Security monitoring configuration
SECURITY_MONITORING_CONFIG = {
    "log_failed_logins": True,
    "log_privilege_escalations": True,
    "log_data_access": True,
    "log_configuration_changes": True,
    "alert_on_suspicious_activity": True,
    "alert_email": "security@itdo.com",
    "alert_threshold_failed_logins": 10,
    "alert_threshold_timeframe_minutes": 5,
}


# Input validation configuration
INPUT_VALIDATION_CONFIG = {
    "max_request_size_mb": 100,
    "max_json_payload_size_mb": 50,
    "sanitize_html_input": True,
    "validate_sql_injection": True,
    "validate_xss_attempts": True,
    "validate_file_uploads": True,
    "max_query_parameters": 100,
    "max_header_size_kb": 8,
}


# Default security policies
DEFAULT_SECURITY_POLICIES = {
    "password_policy": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
        "max_age_days": 90,
        "history_count": 5,
        "lockout_after_failures": 5,
        "lockout_duration_minutes": 15,
    },
    "session_policy": {
        "timeout_minutes": 30,
        "absolute_timeout_hours": 8,
        "concurrent_sessions_limit": 3,
        "require_secure_transport": True,
        "invalidate_on_ip_change": True,
    },
    "access_control_policy": {
        "principle_of_least_privilege": True,
        "require_mfa_for_admin": True,
        "audit_privileged_operations": True,
        "regular_access_review": True,
        "auto_disable_inactive_users_days": 90,
    },
}


# Export security settings instance
security_settings = get_security_settings()
