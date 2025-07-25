"""API integration and external system connectivity models for CC02 v64.0 - Day 9: API Integration Platform."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IntegrationType(str, Enum):
    """Integration type enumeration."""
    
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    SOAP = "soap"
    WEBHOOK = "webhook"
    FTP = "ftp"
    SFTP = "sftp"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_UPLOAD = "file_upload"
    CUSTOM = "custom"


class AuthenticationType(str, Enum):
    """Authentication type enumeration."""
    
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    CUSTOM = "custom"


class ConnectionStatus(str, Enum):
    """Connection status enumeration."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


class SyncDirection(str, Enum):
    """Data synchronization direction."""
    
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Synchronization status enumeration."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WebhookStatus(str, Enum):
    """Webhook status enumeration."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    PAUSED = "paused"


class APIGateway(Base):
    """API Gateway configuration and management."""
    
    __tablename__ = "api_gateways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gateway_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Gateway Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    
    # Network Configuration
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[Optional[str]] = mapped_column(String(500))
    internal_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Protocol Support
    supported_protocols: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    default_protocol: Mapped[str] = mapped_column(String(20), default="https", nullable=False)
    
    # Security Configuration
    authentication_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_auth_type: Mapped[AuthenticationType] = mapped_column(String(50), default=AuthenticationType.API_KEY, nullable=False)
    cors_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cors_origins: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Rate Limiting
    rate_limit_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_rate_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)  # requests per hour
    burst_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # requests per minute
    
    # Load Balancing
    load_balancing_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    load_balancing_strategy: Mapped[Optional[str]] = mapped_column(String(50))  # round_robin, least_connections, ip_hash
    upstream_servers: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    
    # Monitoring & Logging
    logging_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metrics_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    health_check_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    health_check_interval_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    
    # Performance
    cache_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cache_ttl_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    compression_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Status & Health
    status: Mapped[ConnectionStatus] = mapped_column(String(20), default=ConnectionStatus.ACTIVE, nullable=False, index=True)
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime)
    uptime_percentage: Mapped[Optional[float]] = mapped_column(Float)
    
    # Usage Statistics
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    
    # Metadata
    gateway_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    integrations: Mapped[List["ExternalIntegration"]] = relationship("ExternalIntegration", back_populates="gateway")
    api_keys: Mapped[List["APIKey"]] = relationship("APIKey", back_populates="gateway", cascade="all, delete-orphan")


class ExternalIntegration(Base):
    """External system integration configuration."""
    
    __tablename__ = "external_integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    integration_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Integration Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    integration_type: Mapped[IntegrationType] = mapped_column(String(50), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)  # salesforce, hubspot, slack, etc.
    
    # Gateway Association
    gateway_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("api_gateways.id"))
    
    # Connection Configuration
    endpoint_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    base_path: Mapped[Optional[str]] = mapped_column(String(200))
    version: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Authentication
    auth_type: Mapped[AuthenticationType] = mapped_column(String(50), nullable=False)
    auth_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Headers & Parameters
    default_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, default=dict)
    default_params: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, default=dict)
    
    # Data Mapping
    field_mappings: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, default=dict)
    transformation_rules: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    
    # Synchronization Settings
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sync_direction: Mapped[SyncDirection] = mapped_column(String(20), default=SyncDirection.BIDIRECTIONAL, nullable=False)
    sync_frequency_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Error Handling
    retry_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_backoff_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    
    # Rate Limiting
    rate_limit_requests: Mapped[Optional[int]] = mapped_column(Integer)
    rate_limit_window_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    
    # Monitoring
    health_check_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    health_check_endpoint: Mapped[Optional[str]] = mapped_column(String(500))
    health_check_interval_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    
    # Status
    status: Mapped[ConnectionStatus] = mapped_column(String(20), default=ConnectionStatus.ACTIVE, nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Performance Metrics
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_response_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    integration_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    gateway: Mapped[Optional["APIGateway"]] = relationship("APIGateway", back_populates="integrations")
    sync_jobs: Mapped[List["DataSyncJob"]] = relationship("DataSyncJob", back_populates="integration", cascade="all, delete-orphan")
    webhooks: Mapped[List["WebhookEndpoint"]] = relationship("WebhookEndpoint", back_populates="integration", cascade="all, delete-orphan")


class DataSyncJob(Base):
    """Data synchronization job tracking."""
    
    __tablename__ = "data_sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    integration_id: Mapped[int] = mapped_column(Integer, ForeignKey("external_integrations.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Job Details
    job_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sync_direction: Mapped[SyncDirection] = mapped_column(String(20), nullable=False)
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)  # full, incremental, delta
    
    # Scheduling
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100))
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Execution Status
    status: Mapped[SyncStatus] = mapped_column(String(20), default=SyncStatus.PENDING, nullable=False, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Data Processing
    source_system: Mapped[str] = mapped_column(String(100), nullable=False)
    target_system: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # customers, orders, products, etc.
    
    # Results
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Configuration
    sync_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    filter_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    field_mappings: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    
    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Data Quality
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float)
    validation_errors: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Progress Tracking
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_operation: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Metadata
    job_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    triggered_by: Mapped[str] = mapped_column(String(255), nullable=False)  # user, system, schedule
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    integration: Mapped["ExternalIntegration"] = relationship("ExternalIntegration", back_populates="sync_jobs")


class WebhookEndpoint(Base):
    """Webhook endpoint management."""
    
    __tablename__ = "webhook_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    webhook_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    integration_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("external_integrations.id"))
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Webhook Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    endpoint_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Configuration
    http_method: Mapped[str] = mapped_column(String(10), default="POST", nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), default="application/json", nullable=False)
    
    # Event Triggers
    trigger_events: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    event_filters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Authentication
    auth_type: Mapped[AuthenticationType] = mapped_column(String(50), default=AuthenticationType.NONE, nullable=False)
    auth_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Headers & Payload
    custom_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, default=dict)
    payload_template: Mapped[Optional[str]] = mapped_column(Text)
    include_metadata: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Delivery Settings
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    retry_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_backoff_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    
    # Security
    secret_key: Mapped[Optional[str]] = mapped_column(String(500))
    signature_header: Mapped[Optional[str]] = mapped_column(String(100))
    verify_ssl: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Status
    status: Mapped[WebhookStatus] = mapped_column(String(20), default=WebhookStatus.ACTIVE, nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Performance Metrics
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    # Last Activity
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_successful_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    webhook_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    integration: Mapped[Optional["ExternalIntegration"]] = relationship("ExternalIntegration", back_populates="webhooks")
    deliveries: Mapped[List["WebhookDelivery"]] = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    """Webhook delivery tracking."""
    
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    webhook_id: Mapped[int] = mapped_column(Integer, ForeignKey("webhook_endpoints.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Delivery Details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Request Details
    request_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    request_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    request_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    request_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Response Details
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer)
    response_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    response_body: Mapped[Optional[str]] = mapped_column(Text)
    response_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Delivery Status
    is_successful: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_type: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timing
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Metadata
    delivery_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    webhook: Mapped["WebhookEndpoint"] = relationship("WebhookEndpoint", back_populates="deliveries")


class APIKey(Base):
    """API key management for gateway access."""
    
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    gateway_id: Mapped[int] = mapped_column(Integer, ForeignKey("api_gateways.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Key Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    key_value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    key_prefix: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Access Control
    scopes: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    permissions: Mapped[Dict[str, List[str]]] = mapped_column(JSON, nullable=False)
    allowed_origins: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    allowed_ips: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Rate Limiting
    rate_limit_requests: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    rate_limit_window_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    burst_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    
    # Status & Lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Usage Statistics
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Security
    last_rotation_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rotation_interval_days: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Owner Information
    owner_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, service, application
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Metadata
    key_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationships
    gateway: Mapped["APIGateway"] = relationship("APIGateway", back_populates="api_keys")
    usage_logs: Mapped[List["APIUsageLog"]] = relationship("APIUsageLog", back_populates="api_key", cascade="all, delete-orphan")


class APIUsageLog(Base):
    """API usage logging and monitoring."""
    
    __tablename__ = "api_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    api_key_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("api_keys.id"))
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Request Details
    request_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    query_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Client Information
    client_ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(String(1000))
    referer: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Authentication
    auth_method: Mapped[Optional[str]] = mapped_column(String(50))
    user_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Response Details
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    response_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Error Information
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_type: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Performance Metrics
    database_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, index=True)
    
    # Metadata
    request_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    response_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    log_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Relationships
    api_key: Mapped[Optional["APIKey"]] = relationship("APIKey", back_populates="usage_logs")


class DataMapping(Base):
    """Data field mapping configuration between systems."""
    
    __tablename__ = "data_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mapping_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Mapping Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    
    # Source & Target Systems
    source_system: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_system: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # customer, order, product, etc.
    
    # Field Mappings
    field_mappings: Mapped[Dict[str, Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    
    # Transformation Rules
    transformation_rules: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    validation_rules: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Default Values
    default_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    null_handling: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)  # ignore, default, error
    
    # Conditional Logic
    conditional_mappings: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Usage Statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Validation Results
    validation_errors: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    test_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Metadata
    mapping_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class IntegrationHealth(Base):
    """Integration health monitoring and status tracking."""
    
    __tablename__ = "integration_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    health_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    integration_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Health Check Details
    check_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)  # connectivity, data_quality, performance
    
    # Health Status
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    health_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    status_message: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Performance Metrics
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    throughput_requests_per_second: Mapped[Optional[float]] = mapped_column(Float)
    error_rate: Mapped[Optional[float]] = mapped_column(Float)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    # Connectivity
    connection_successful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ssl_valid: Mapped[Optional[bool]] = mapped_column(Boolean)
    certificate_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Data Quality
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float)
    validation_errors: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    data_freshness_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Issues & Recommendations
    issues_detected: Mapped[List[str]] = mapped_column(JSON, default=list)
    recommendations: Mapped[List[str]] = mapped_column(JSON, default=list)
    severity_level: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info, warning, error, critical
    
    # Historical Context
    previous_health_score: Mapped[Optional[float]] = mapped_column(Float)
    trend_direction: Mapped[Optional[str]] = mapped_column(String(20))  # improving, stable, degrading
    
    # Metadata
    check_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    health_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)