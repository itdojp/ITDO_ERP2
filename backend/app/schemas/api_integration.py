"""Pydantic schemas for API Integration Platform - CC02 v64.0 Day 9."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.api_integration import (
    IntegrationType,
    AuthenticationType,
    ConnectionStatus,
    SyncDirection,
    SyncStatus,
    WebhookStatus,
)


# API Gateway Schemas
class APIGatewayBase(BaseModel):
    """Base schema for API Gateway."""
    
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    version: str = Field(default="1.0", max_length=20)
    base_url: str = Field(..., max_length=500)
    public_url: Optional[str] = Field(None, max_length=500)
    internal_url: Optional[str] = Field(None, max_length=500)
    supported_protocols: List[str] = Field(default=["https", "http"])
    default_protocol: str = Field(default="https", max_length=20)
    authentication_required: bool = Field(default=True)
    default_auth_type: AuthenticationType = Field(default=AuthenticationType.API_KEY)
    cors_enabled: bool = Field(default=True)
    cors_origins: Optional[List[str]] = Field(default_factory=list)
    rate_limit_enabled: bool = Field(default=True)
    default_rate_limit: int = Field(default=1000, ge=1)
    burst_limit: int = Field(default=100, ge=1)
    load_balancing_enabled: bool = Field(default=False)
    load_balancing_strategy: Optional[str] = Field(None, max_length=50)
    upstream_servers: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    logging_enabled: bool = Field(default=True)
    metrics_enabled: bool = Field(default=True)
    health_check_enabled: bool = Field(default=True)
    health_check_interval_seconds: int = Field(default=30, ge=1)
    cache_enabled: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300, ge=1)
    compression_enabled: bool = Field(default=True)
    gateway_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class APIGatewayCreate(APIGatewayBase):
    """Schema for creating API Gateway."""
    pass


class APIGatewayUpdate(BaseModel):
    """Schema for updating API Gateway."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    base_url: Optional[str] = Field(None, max_length=500)
    public_url: Optional[str] = Field(None, max_length=500)
    internal_url: Optional[str] = Field(None, max_length=500)
    supported_protocols: Optional[List[str]] = None
    default_protocol: Optional[str] = Field(None, max_length=20)
    authentication_required: Optional[bool] = None
    default_auth_type: Optional[AuthenticationType] = None
    cors_enabled: Optional[bool] = None
    cors_origins: Optional[List[str]] = None
    rate_limit_enabled: Optional[bool] = None
    default_rate_limit: Optional[int] = Field(None, ge=1)
    burst_limit: Optional[int] = Field(None, ge=1)
    load_balancing_enabled: Optional[bool] = None
    load_balancing_strategy: Optional[str] = Field(None, max_length=50)
    upstream_servers: Optional[List[Dict[str, Any]]] = None
    logging_enabled: Optional[bool] = None
    metrics_enabled: Optional[bool] = None
    health_check_enabled: Optional[bool] = None
    health_check_interval_seconds: Optional[int] = Field(None, ge=1)
    cache_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=1)
    compression_enabled: Optional[bool] = None
    status: Optional[ConnectionStatus] = None
    gateway_data: Optional[Dict[str, Any]] = None


class APIGatewayResponse(APIGatewayBase):
    """Schema for API Gateway response."""
    
    id: int
    gateway_id: str
    organization_id: str
    status: ConnectionStatus
    last_health_check: Optional[datetime]
    uptime_percentage: Optional[float]
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: Optional[float]
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# External Integration Schemas
class ExternalIntegrationBase(BaseModel):
    """Base schema for External Integration."""
    
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    integration_type: IntegrationType
    provider: str = Field(..., max_length=100)
    gateway_id: Optional[int] = None
    endpoint_url: str = Field(..., max_length=1000)
    base_path: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, max_length=20)
    auth_type: AuthenticationType
    auth_config: Dict[str, Any]
    default_headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    default_params: Optional[Dict[str, str]] = Field(default_factory=dict)
    field_mappings: Optional[Dict[str, str]] = Field(default_factory=dict)
    transformation_rules: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    sync_enabled: bool = Field(default=True)
    sync_direction: SyncDirection = Field(default=SyncDirection.BIDIRECTIONAL)
    sync_frequency_minutes: int = Field(default=60, ge=1)
    retry_enabled: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: int = Field(default=60, ge=1)
    rate_limit_requests: Optional[int] = Field(None, ge=1)
    rate_limit_window_seconds: int = Field(default=3600, ge=1)
    health_check_enabled: bool = Field(default=True)
    health_check_endpoint: Optional[str] = Field(None, max_length=500)
    health_check_interval_minutes: int = Field(default=15, ge=1)
    is_enabled: bool = Field(default=True)
    tags: Optional[List[str]] = Field(default_factory=list)
    integration_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ExternalIntegrationCreate(ExternalIntegrationBase):
    """Schema for creating External Integration."""
    pass


class ExternalIntegrationUpdate(BaseModel):
    """Schema for updating External Integration."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    integration_type: Optional[IntegrationType] = None
    provider: Optional[str] = Field(None, max_length=100)
    gateway_id: Optional[int] = None
    endpoint_url: Optional[str] = Field(None, max_length=1000)
    base_path: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, max_length=20)
    auth_type: Optional[AuthenticationType] = None
    auth_config: Optional[Dict[str, Any]] = None
    default_headers: Optional[Dict[str, str]] = None
    default_params: Optional[Dict[str, str]] = None
    field_mappings: Optional[Dict[str, str]] = None
    transformation_rules: Optional[List[Dict[str, Any]]] = None
    sync_enabled: Optional[bool] = None
    sync_direction: Optional[SyncDirection] = None
    sync_frequency_minutes: Optional[int] = Field(None, ge=1)
    retry_enabled: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0)
    retry_backoff_seconds: Optional[int] = Field(None, ge=1)
    rate_limit_requests: Optional[int] = Field(None, ge=1)
    rate_limit_window_seconds: Optional[int] = Field(None, ge=1)
    health_check_enabled: Optional[bool] = None
    health_check_endpoint: Optional[str] = Field(None, max_length=500)
    health_check_interval_minutes: Optional[int] = Field(None, ge=1)
    status: Optional[ConnectionStatus] = None
    is_enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    integration_data: Optional[Dict[str, Any]] = None


class ExternalIntegrationResponse(ExternalIntegrationBase):
    """Schema for External Integration response."""
    
    id: int
    integration_id: str
    organization_id: str
    status: ConnectionStatus
    last_sync_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    success_rate: Optional[float]
    avg_response_time_ms: Optional[float]
    total_requests: int
    failed_requests: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Data Sync Job Schemas
class DataSyncJobBase(BaseModel):
    """Base schema for Data Sync Job."""
    
    job_name: str = Field(..., max_length=200)
    sync_direction: SyncDirection
    sync_type: str = Field(..., max_length=50)
    is_scheduled: bool = Field(default=False)
    schedule_cron: Optional[str] = Field(None, max_length=100)
    source_system: str = Field(..., max_length=100)
    target_system: str = Field(..., max_length=100)
    entity_type: str = Field(..., max_length=100)
    sync_config: Dict[str, Any]
    filter_conditions: Optional[Dict[str, Any]] = None
    field_mappings: Optional[Dict[str, str]] = None
    max_retries: int = Field(default=3, ge=0)
    job_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    triggered_by: str = Field(..., max_length=255)


class DataSyncJobCreate(DataSyncJobBase):
    """Schema for creating Data Sync Job."""
    
    integration_id: int


class DataSyncJobResponse(DataSyncJobBase):
    """Schema for Data Sync Job response."""
    
    id: int
    job_id: str
    integration_id: int
    organization_id: str
    status: SyncStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    records_processed: int
    records_created: int
    records_updated: int
    records_deleted: int
    records_failed: int
    error_message: Optional[str]
    error_details: Optional[List[Dict[str, Any]]]
    retry_count: int
    data_quality_score: Optional[float]
    validation_errors: Optional[List[str]]
    duplicate_records: int
    progress_percentage: float
    current_operation: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Webhook Schemas
class WebhookEndpointBase(BaseModel):
    """Base schema for Webhook Endpoint."""
    
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    endpoint_url: str = Field(..., max_length=1000)
    http_method: str = Field(default="POST", max_length=10)
    content_type: str = Field(default="application/json", max_length=100)
    trigger_events: List[str]
    event_filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    auth_type: AuthenticationType = Field(default=AuthenticationType.NONE)
    auth_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    custom_headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    payload_template: Optional[str] = None
    include_metadata: bool = Field(default=True)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    retry_enabled: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: int = Field(default=60, ge=1)
    secret_key: Optional[str] = Field(None, max_length=500)
    signature_header: Optional[str] = Field(None, max_length=100)
    verify_ssl: bool = Field(default=True)
    is_enabled: bool = Field(default=True)
    webhook_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WebhookEndpointCreate(WebhookEndpointBase):
    """Schema for creating Webhook Endpoint."""
    
    integration_id: Optional[int] = None


class WebhookEndpointUpdate(BaseModel):
    """Schema for updating Webhook Endpoint."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    endpoint_url: Optional[str] = Field(None, max_length=1000)
    http_method: Optional[str] = Field(None, max_length=10)
    content_type: Optional[str] = Field(None, max_length=100)
    trigger_events: Optional[List[str]] = None
    event_filters: Optional[Dict[str, Any]] = None
    auth_type: Optional[AuthenticationType] = None
    auth_config: Optional[Dict[str, Any]] = None
    custom_headers: Optional[Dict[str, str]] = None
    payload_template: Optional[str] = None
    include_metadata: Optional[bool] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    retry_enabled: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0)
    retry_backoff_seconds: Optional[int] = Field(None, ge=1)
    secret_key: Optional[str] = Field(None, max_length=500)
    signature_header: Optional[str] = Field(None, max_length=100)
    verify_ssl: Optional[bool] = None
    status: Optional[WebhookStatus] = None
    is_enabled: Optional[bool] = None
    webhook_data: Optional[Dict[str, Any]] = None


class WebhookEndpointResponse(WebhookEndpointBase):
    """Schema for Webhook Endpoint response."""
    
    id: int
    webhook_id: str
    integration_id: Optional[int]
    organization_id: str
    status: WebhookStatus
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    avg_response_time_ms: Optional[float]
    success_rate: Optional[float]
    last_triggered_at: Optional[datetime]
    last_successful_delivery: Optional[datetime]
    last_failure_at: Optional[datetime]
    last_error_message: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Webhook Delivery Schemas
class WebhookDeliveryResponse(BaseModel):
    """Schema for Webhook Delivery response."""
    
    id: int
    delivery_id: str
    webhook_id: int
    organization_id: str
    event_type: str
    event_id: str
    request_url: str
    request_method: str
    request_headers: Optional[Dict[str, str]]
    request_payload: Optional[Dict[str, Any]]
    request_size_bytes: Optional[int]
    response_status_code: Optional[int]
    response_headers: Optional[Dict[str, str]]
    response_body: Optional[str]
    response_size_bytes: Optional[int]
    response_time_ms: Optional[int]
    is_successful: bool
    attempts: int
    max_attempts: int
    error_message: Optional[str]
    error_type: Optional[str]
    scheduled_at: datetime
    attempted_at: Optional[datetime]
    completed_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    delivery_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# API Key Schemas
class APIKeyBase(BaseModel):
    """Base schema for API Key."""
    
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    key_prefix: Optional[str] = Field(None, max_length=20)
    scopes: List[str]
    permissions: Dict[str, List[str]]
    allowed_origins: Optional[List[str]] = Field(default_factory=list)
    allowed_ips: Optional[List[str]] = Field(default_factory=list)
    rate_limit_requests: int = Field(default=1000, ge=1)
    rate_limit_window_seconds: int = Field(default=3600, ge=1)
    burst_limit: int = Field(default=100, ge=1)
    expires_at: Optional[datetime] = None
    rotation_interval_days: Optional[int] = Field(None, ge=1)
    owner_type: str = Field(..., max_length=50)
    owner_id: str = Field(..., max_length=255)
    key_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class APIKeyCreate(APIKeyBase):
    """Schema for creating API Key."""
    
    gateway_id: int


class APIKeyResponse(APIKeyBase):
    """Schema for API Key response."""
    
    id: int
    key_id: str
    gateway_id: int
    organization_id: str
    key_value: str  # Only shown on creation/rotation
    is_active: bool
    last_used_at: Optional[datetime]
    total_requests: int
    requests_today: int
    successful_requests: int
    failed_requests: int
    last_rotation_at: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# API Usage Log Schemas
class APIUsageLogResponse(BaseModel):
    """Schema for API Usage Log response."""
    
    id: int
    log_id: str
    api_key_id: Optional[int]
    organization_id: str
    request_id: str
    method: str
    endpoint: str
    path: str
    query_params: Optional[Dict[str, Any]]
    client_ip: str
    user_agent: Optional[str]
    referer: Optional[str]
    auth_method: Optional[str]
    user_id: Optional[str]
    status_code: int
    response_size_bytes: Optional[int]
    response_time_ms: int
    error_message: Optional[str]
    error_type: Optional[str]
    database_time_ms: Optional[int]
    cache_hit: bool
    timestamp: datetime
    request_headers: Optional[Dict[str, str]]
    response_headers: Optional[Dict[str, str]]
    log_data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


# Data Mapping Schemas
class DataMappingBase(BaseModel):
    """Base schema for Data Mapping."""
    
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    version: str = Field(default="1.0", max_length=20)
    source_system: str = Field(..., max_length=100)
    target_system: str = Field(..., max_length=100)
    entity_type: str = Field(..., max_length=100)
    field_mappings: Dict[str, Dict[str, Any]]
    transformation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    default_values: Optional[Dict[str, Any]] = Field(default_factory=dict)
    null_handling: Dict[str, str] = Field(default_factory=dict)
    conditional_mappings: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    mapping_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DataMappingCreate(DataMappingBase):
    """Schema for creating Data Mapping."""
    pass


class DataMappingResponse(DataMappingBase):
    """Schema for Data Mapping response."""
    
    id: int
    mapping_id: str
    organization_id: str
    is_validated: bool
    usage_count: int
    success_rate: Optional[float]
    last_used_at: Optional[datetime]
    validation_errors: Optional[List[str]]
    test_results: Optional[Dict[str, Any]]
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Integration Health Schemas
class IntegrationHealthCheck(BaseModel):
    """Schema for triggering integration health check."""
    
    check_type: str = Field(default="connectivity", max_length=50)
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class IntegrationHealthResponse(BaseModel):
    """Schema for Integration Health response."""
    
    id: int
    health_id: str
    integration_id: str
    organization_id: str
    check_timestamp: datetime
    check_type: str
    is_healthy: bool
    health_score: float
    status_message: Optional[str]
    response_time_ms: Optional[int]
    throughput_requests_per_second: Optional[float]
    error_rate: Optional[float]
    success_rate: Optional[float]
    connection_successful: bool
    ssl_valid: Optional[bool]
    certificate_expires_at: Optional[datetime]
    data_quality_score: Optional[float]
    validation_errors: Optional[List[str]]
    data_freshness_minutes: Optional[int]
    issues_detected: List[str]
    recommendations: List[str]
    severity_level: str
    previous_health_score: Optional[float]
    trend_direction: Optional[str]
    check_config: Optional[Dict[str, Any]]
    health_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Request/Response Schemas for API endpoints
class WebhookDeliveryRequest(BaseModel):
    """Schema for webhook delivery request."""
    
    event_type: str = Field(..., max_length=100)
    event_id: str = Field(..., max_length=100)
    payload: Dict[str, Any]
    immediate: bool = Field(default=True)


class BulkSyncRequest(BaseModel):
    """Schema for bulk synchronization request."""
    
    sync_jobs: List[DataSyncJobCreate]
    batch_id: Optional[str] = None
    parallel_execution: bool = Field(default=False)
    max_concurrent_jobs: int = Field(default=5, ge=1, le=20)


class HealthCheckSummaryResponse(BaseModel):
    """Schema for health check summary response."""
    
    total_integrations: int
    healthy_integrations: int
    unhealthy_integrations: int
    average_health_score: float
    critical_issues: List[str]
    warning_issues: List[str]
    last_updated: datetime
    
    class Config:
        from_attributes = True


# Validators
@validator('supported_protocols')
def validate_protocols(cls, v):
    """Validate supported protocols."""
    valid_protocols = {'http', 'https', 'ws', 'wss'}
    for protocol in v:
        if protocol not in valid_protocols:
            raise ValueError(f'Invalid protocol: {protocol}')
    return v


@validator('load_balancing_strategy')
def validate_load_balancing_strategy(cls, v):
    """Validate load balancing strategy."""
    if v is not None:
        valid_strategies = {'round_robin', 'least_connections', 'ip_hash', 'weighted'}
        if v not in valid_strategies:
            raise ValueError(f'Invalid load balancing strategy: {v}')
    return v


@validator('http_method')
def validate_http_method(cls, v):
    """Validate HTTP method."""
    valid_methods = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}
    if v.upper() not in valid_methods:
        raise ValueError(f'Invalid HTTP method: {v}')
    return v.upper()


@validator('severity_level')
def validate_severity_level(cls, v):
    """Validate severity level."""
    valid_levels = {'info', 'warning', 'error', 'critical'}
    if v not in valid_levels:
        raise ValueError(f'Invalid severity level: {v}')
    return v