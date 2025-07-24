"""
Integration System Schemas - CC02 v31.0 Phase 2

Comprehensive Pydantic schemas for integration system including:
- External System Integration & API Management
- Data Synchronization & ETL Pipelines
- Third-Party Service Connectors
- Webhook & Event-Driven Integration
- API Gateway & Rate Limiting
- Data Transformation & Mapping
- Integration Monitoring & Health Checks
- Message Queuing & Async Processing
- Authentication & Security Management
- Integration Analytics & Performance Tracking
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models.integration_extended import (
    ConnectionStatus,
    DataFormat,
    IntegrationType,
    SyncDirection,
    SyncStatus,
    TransformationType,
)

# =============================================================================
# Base Schemas
# =============================================================================


class BaseIntegrationSchema(BaseModel):
    """Base schema for integration-related models."""

    class Config:
        orm_mode = True
        use_enum_values = True


# =============================================================================
# External System Schemas
# =============================================================================


class ExternalSystemCreateRequest(BaseIntegrationSchema):
    """Schema for creating a new external system."""

    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="System name")
    code: str = Field(..., min_length=1, max_length=100, description="System code")
    description: Optional[str] = Field(None, description="System description")
    integration_type: IntegrationType = Field(..., description="Integration type")

    # Connection configuration
    base_url: Optional[str] = Field(None, max_length=1000, description="Base URL")
    api_version: Optional[str] = Field(None, max_length=50, description="API version")
    endpoint_prefix: Optional[str] = Field(
        None, max_length=200, description="Endpoint prefix"
    )
    connection_config: Dict[str, Any] = Field(
        default_factory=dict, description="Connection configuration"
    )

    # Authentication
    auth_type: Optional[str] = Field(
        None, max_length=100, description="Authentication type"
    )
    auth_config: Dict[str, Any] = Field(
        default_factory=dict, description="Authentication configuration"
    )
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Credentials")

    # Rate limiting
    rate_limit_requests: Optional[int] = Field(
        None, ge=1, description="Rate limit requests"
    )
    rate_limit_period: Optional[int] = Field(
        None, ge=1, description="Rate limit period (seconds)"
    )

    # Configuration
    timeout_seconds: int = Field(30, ge=1, le=600, description="Request timeout")
    retry_attempts: int = Field(3, ge=0, le=10, description="Retry attempts")
    retry_delay_seconds: int = Field(5, ge=1, le=60, description="Retry delay")
    enable_logging: bool = Field(True, description="Enable logging")

    # Status and settings
    is_active: bool = Field(True, description="Active status")
    is_primary: bool = Field(False, description="Primary system")
    maintenance_mode: bool = Field(False, description="Maintenance mode")

    # Metadata
    vendor: Optional[str] = Field(None, max_length=200, description="Vendor name")
    version: Optional[str] = Field(None, max_length=100, description="System version")
    documentation_url: Optional[str] = Field(
        None, max_length=1000, description="Documentation URL"
    )
    support_contact: Optional[str] = Field(
        None, max_length=500, description="Support contact"
    )
    tags: List[str] = Field(default_factory=list, description="Tags")
    integration_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("base_url")
    def validate_base_url(cls, v) -> dict:
        """Validate base URL format."""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return v


class ExternalSystemUpdateRequest(BaseIntegrationSchema):
    """Schema for updating an external system."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="System name"
    )
    description: Optional[str] = Field(None, description="System description")
    base_url: Optional[str] = Field(None, max_length=1000, description="Base URL")
    api_version: Optional[str] = Field(None, max_length=50, description="API version")
    connection_config: Optional[Dict[str, Any]] = Field(
        None, description="Connection configuration"
    )
    auth_config: Optional[Dict[str, Any]] = Field(
        None, description="Authentication configuration"
    )
    timeout_seconds: Optional[int] = Field(
        None, ge=1, le=600, description="Request timeout"
    )
    is_active: Optional[bool] = Field(None, description="Active status")
    maintenance_mode: Optional[bool] = Field(None, description="Maintenance mode")
    tags: Optional[List[str]] = Field(None, description="Tags")
    integration_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


class ExternalSystemResponse(BaseIntegrationSchema):
    """Schema for external system response."""

    id: str = Field(..., description="System ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="System name")
    code: str = Field(..., description="System code")
    description: Optional[str] = Field(None, description="System description")
    integration_type: IntegrationType = Field(..., description="Integration type")

    # Connection configuration
    base_url: Optional[str] = Field(None, description="Base URL")
    api_version: Optional[str] = Field(None, description="API version")
    connection_status: ConnectionStatus = Field(..., description="Connection status")

    # Health monitoring
    last_health_check: Optional[datetime] = Field(None, description="Last health check")
    uptime_percentage: Optional[Decimal] = Field(None, description="Uptime percentage")

    # Performance metrics
    average_response_time: Optional[Decimal] = Field(
        None, description="Average response time (ms)"
    )
    total_requests: int = Field(..., description="Total requests")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")

    # Status and settings
    is_active: bool = Field(..., description="Active status")
    is_primary: bool = Field(..., description="Primary system")
    maintenance_mode: bool = Field(..., description="Maintenance mode")

    # Metadata
    vendor: Optional[str] = Field(None, description="Vendor name")
    version: Optional[str] = Field(None, description="System version")
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class ExternalSystemListResponse(BaseIntegrationSchema):
    """Schema for external system list response."""

    external_systems: List[ExternalSystemResponse] = Field(
        ..., description="External systems"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class SystemConnectionTestRequest(BaseIntegrationSchema):
    """Schema for testing system connection."""

    test_type: str = Field("basic", description="Test type")
    test_url: Optional[str] = Field(None, description="Override test URL")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="Test timeout")
    include_response_body: bool = Field(False, description="Include response body")


# =============================================================================
# Integration Connector Schemas
# =============================================================================


class IntegrationConnectorCreateRequest(BaseIntegrationSchema):
    """Schema for creating an integration connector."""

    organization_id: str = Field(..., description="Organization ID")
    external_system_id: str = Field(..., description="External system ID")
    name: str = Field(..., min_length=1, max_length=200, description="Connector name")
    code: str = Field(..., min_length=1, max_length=100, description="Connector code")
    description: Optional[str] = Field(None, description="Connector description")
    operation_type: str = Field(..., max_length=100, description="Operation type")

    # Endpoint configuration
    endpoint_url: str = Field(..., max_length=1000, description="Endpoint URL")
    http_method: str = Field("GET", description="HTTP method")
    request_headers: Dict[str, str] = Field(
        default_factory=dict, description="Request headers"
    )
    request_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Request parameters"
    )
    request_body_template: Optional[str] = Field(
        None, description="Request body template"
    )

    # Data handling
    data_format: DataFormat = Field(DataFormat.JSON, description="Data format")
    sync_direction: SyncDirection = Field(..., description="Sync direction")
    entity_type: Optional[str] = Field(None, max_length=100, description="Entity type")

    # Scheduling
    is_scheduled: bool = Field(False, description="Scheduled execution")
    schedule_cron: Optional[str] = Field(
        None, max_length=100, description="Cron schedule"
    )
    schedule_config: Dict[str, Any] = Field(
        default_factory=dict, description="Schedule configuration"
    )

    # Execution settings
    batch_size: int = Field(100, ge=1, le=10000, description="Batch size")
    parallel_workers: int = Field(1, ge=1, le=10, description="Parallel workers")
    timeout_seconds: int = Field(300, ge=1, le=3600, description="Execution timeout")
    max_retries: int = Field(3, ge=0, le=10, description="Max retries")

    # Error handling
    alert_on_failure: bool = Field(True, description="Alert on failure")
    notification_recipients: List[str] = Field(
        default_factory=list, description="Notification recipients"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    connector_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")

    @validator("http_method")
    def validate_http_method(cls, v) -> dict:
        """Validate HTTP method."""
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
        if v.upper() not in allowed_methods:
            raise ValueError(
                f"HTTP method must be one of: {', '.join(allowed_methods)}"
            )
        return v.upper()


class IntegrationConnectorResponse(BaseIntegrationSchema):
    """Schema for integration connector response."""

    id: str = Field(..., description="Connector ID")
    organization_id: str = Field(..., description="Organization ID")
    external_system_id: str = Field(..., description="External system ID")
    name: str = Field(..., description="Connector name")
    code: str = Field(..., description="Connector code")
    description: Optional[str] = Field(None, description="Connector description")
    operation_type: str = Field(..., description="Operation type")

    # Endpoint configuration
    endpoint_url: str = Field(..., description="Endpoint URL")
    http_method: str = Field(..., description="HTTP method")
    data_format: DataFormat = Field(..., description="Data format")
    sync_direction: SyncDirection = Field(..., description="Sync direction")
    entity_type: Optional[str] = Field(None, description="Entity type")

    # Scheduling
    is_scheduled: bool = Field(..., description="Scheduled execution")
    schedule_cron: Optional[str] = Field(None, description="Cron schedule")
    last_run_at: Optional[datetime] = Field(None, description="Last run timestamp")
    next_run_at: Optional[datetime] = Field(None, description="Next run timestamp")

    # Status and monitoring
    is_active: bool = Field(..., description="Active status")
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")
    average_execution_time: Optional[Decimal] = Field(
        None, description="Average execution time (ms)"
    )

    # Data tracking
    total_records_processed: int = Field(..., description="Total records processed")
    records_created: int = Field(..., description="Records created")
    records_updated: int = Field(..., description="Records updated")
    records_deleted: int = Field(..., description="Records deleted")

    # Error handling
    last_error: Optional[str] = Field(None, description="Last error message")
    error_count: int = Field(..., description="Error count")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class ConnectorExecutionRequest(BaseIntegrationSchema):
    """Schema for connector execution request."""

    execution_type: str = Field("manual", description="Execution type")
    triggered_by: Optional[str] = Field(None, description="Triggered by user ID")
    data: Optional[List[Dict[str, Any]]] = Field(
        None, description="Data for outbound sync"
    )
    config_overrides: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration overrides"
    )
    dry_run: bool = Field(False, description="Dry run mode")


# =============================================================================
# Data Mapping Schemas
# =============================================================================


class DataMappingCreateRequest(BaseIntegrationSchema):
    """Schema for creating a data mapping."""

    organization_id: str = Field(..., description="Organization ID")
    connector_id: str = Field(..., description="Connector ID")
    name: str = Field(..., min_length=1, max_length=200, description="Mapping name")
    description: Optional[str] = Field(None, description="Mapping description")
    entity_type: str = Field(..., max_length=100, description="Entity type")
    sync_direction: SyncDirection = Field(..., description="Sync direction")

    # Field mappings
    source_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Source schema"
    )
    target_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Target schema"
    )
    field_mappings: Dict[str, str] = Field(..., description="Field mappings")

    # Transformation rules
    transformation_rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="Transformation rules"
    )
    validation_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Validation rules"
    )
    default_values: Dict[str, Any] = Field(
        default_factory=dict, description="Default values"
    )

    # Data processing
    data_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Data filters"
    )
    aggregation_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Aggregation rules"
    )

    # Quality control
    enable_validation: bool = Field(True, description="Enable validation")
    required_fields: List[str] = Field(
        default_factory=list, description="Required fields"
    )
    unique_fields: List[str] = Field(default_factory=list, description="Unique fields")

    # Performance
    use_bulk_operations: bool = Field(True, description="Use bulk operations")
    chunk_size: int = Field(1000, ge=1, le=10000, description="Chunk size")
    enable_caching: bool = Field(False, description="Enable caching")
    cache_ttl_seconds: Optional[int] = Field(None, ge=60, description="Cache TTL")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    mapping_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")


class DataMappingResponse(BaseIntegrationSchema):
    """Schema for data mapping response."""

    id: str = Field(..., description="Mapping ID")
    organization_id: str = Field(..., description="Organization ID")
    connector_id: str = Field(..., description="Connector ID")
    name: str = Field(..., description="Mapping name")
    description: Optional[str] = Field(None, description="Mapping description")
    entity_type: str = Field(..., description="Entity type")
    sync_direction: SyncDirection = Field(..., description="Sync direction")

    # Field mappings
    field_mappings: Dict[str, str] = Field(..., description="Field mappings")
    transformation_rules: List[Dict[str, Any]] = Field(
        ..., description="Transformation rules"
    )

    # Status and metrics
    is_active: bool = Field(..., description="Active status")
    records_mapped: int = Field(..., description="Records mapped")
    mapping_errors: int = Field(..., description="Mapping errors")

    # Versioning
    version: str = Field(..., description="Mapping version")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


# =============================================================================
# Data Transformation Schemas
# =============================================================================


class DataTransformationCreateRequest(BaseIntegrationSchema):
    """Schema for creating a data transformation."""

    organization_id: str = Field(..., description="Organization ID")
    connector_id: Optional[str] = Field(None, description="Connector ID")
    name: str = Field(
        ..., min_length=1, max_length=200, description="Transformation name"
    )
    description: Optional[str] = Field(None, description="Transformation description")
    transformation_type: TransformationType = Field(
        ..., description="Transformation type"
    )

    # Transformation logic
    input_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Input schema"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict, description="Output schema"
    )
    transformation_script: Optional[str] = Field(
        None, description="Transformation script"
    )
    transformation_config: Dict[str, Any] = Field(
        default_factory=dict, description="Transformation configuration"
    )

    # Processing settings
    language: str = Field("python", description="Script language")
    execution_environment: Optional[str] = Field(
        None, description="Execution environment"
    )
    dependencies: List[str] = Field(default_factory=list, description="Dependencies")

    # Performance
    execution_timeout: int = Field(300, ge=1, le=3600, description="Execution timeout")
    memory_limit_mb: int = Field(512, ge=64, le=4096, description="Memory limit (MB)")
    cpu_limit_percent: Decimal = Field(
        Decimal("50.0"), ge=1, le=100, description="CPU limit (%)"
    )

    # Error handling
    error_handling_strategy: str = Field("skip", description="Error handling strategy")
    max_error_rate: Decimal = Field(
        Decimal("5.0"), ge=0, le=100, description="Max error rate (%)"
    )

    # Testing
    test_cases: List[Dict[str, Any]] = Field(
        default_factory=list, description="Test cases"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    transformation_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")


class DataTransformationResponse(BaseIntegrationSchema):
    """Schema for data transformation response."""

    id: str = Field(..., description="Transformation ID")
    organization_id: str = Field(..., description="Organization ID")
    connector_id: Optional[str] = Field(None, description="Connector ID")
    name: str = Field(..., description="Transformation name")
    description: Optional[str] = Field(None, description="Transformation description")
    transformation_type: TransformationType = Field(
        ..., description="Transformation type"
    )

    # Processing settings
    language: str = Field(..., description="Script language")
    execution_timeout: int = Field(..., description="Execution timeout")

    # Monitoring
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")
    average_execution_time: Optional[Decimal] = Field(
        None, description="Average execution time (ms)"
    )

    # Error handling
    last_error: Optional[str] = Field(None, description="Last error message")

    # Testing
    test_coverage_percentage: Optional[Decimal] = Field(
        None, description="Test coverage (%)"
    )

    # Status and versioning
    is_active: bool = Field(..., description="Active status")
    version: str = Field(..., description="Transformation version")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class TransformationExecutionRequest(BaseIntegrationSchema):
    """Schema for transformation execution request."""

    input_data: List[Dict[str, Any]] = Field(..., description="Input data")
    execution_config: Dict[str, Any] = Field(
        default_factory=dict, description="Execution configuration"
    )
    dry_run: bool = Field(False, description="Dry run mode")


# =============================================================================
# Execution Schemas
# =============================================================================


class IntegrationExecutionResponse(BaseIntegrationSchema):
    """Schema for integration execution response."""

    id: str = Field(..., description="Execution ID")
    organization_id: str = Field(..., description="Organization ID")
    connector_id: str = Field(..., description="Connector ID")
    execution_type: str = Field(..., description="Execution type")
    trigger_source: Optional[str] = Field(None, description="Trigger source")

    # Status and timing
    status: SyncStatus = Field(..., description="Execution status")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_ms: Optional[int] = Field(None, description="Duration (ms)")

    # Request/response details
    request_id: Optional[str] = Field(None, description="Request ID")
    response_status_code: Optional[int] = Field(
        None, description="Response status code"
    )

    # Data processing
    records_requested: int = Field(0, description="Records requested")
    records_received: int = Field(0, description="Records received")
    records_processed: int = Field(0, description="Records processed")
    records_created: int = Field(0, description="Records created")
    records_updated: int = Field(0, description="Records updated")
    records_deleted: int = Field(0, description="Records deleted")
    records_skipped: int = Field(0, description="Records skipped")
    records_failed: int = Field(0, description="Records failed")

    # Performance metrics
    network_time_ms: Optional[int] = Field(None, description="Network time (ms)")
    processing_time_ms: Optional[int] = Field(None, description="Processing time (ms)")
    database_time_ms: Optional[int] = Field(None, description="Database time (ms)")

    # Error handling
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: int = Field(0, description="Retry count")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")


# =============================================================================
# Webhook Schemas
# =============================================================================


class WebhookEndpointCreateRequest(BaseIntegrationSchema):
    """Schema for creating a webhook endpoint."""

    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Webhook name")
    description: Optional[str] = Field(None, description="Webhook description")
    endpoint_url: Optional[str] = Field(
        None, max_length=1000, description="Endpoint URL"
    )

    # Configuration
    allowed_methods: List[str] = Field(
        default_factory=lambda: ["POST"], description="Allowed HTTP methods"
    )
    content_types: List[str] = Field(
        default_factory=lambda: ["application/json"],
        description="Allowed content types",
    )
    max_body_size_mb: int = Field(10, ge=1, le=100, description="Max body size (MB)")
    enable_signature_verification: bool = Field(
        True, description="Enable signature verification"
    )

    # Security
    allowed_ips: List[str] = Field(
        default_factory=list, description="Allowed IP addresses"
    )
    require_authentication: bool = Field(False, description="Require authentication")
    rate_limit_per_minute: int = Field(
        100, ge=1, le=10000, description="Rate limit per minute"
    )

    # Processing
    processing_script: Optional[str] = Field(None, description="Processing script")
    processing_config: Dict[str, Any] = Field(
        default_factory=dict, description="Processing configuration"
    )
    enable_async_processing: bool = Field(True, description="Enable async processing")

    # Response configuration
    response_template: Optional[str] = Field(None, description="Response template")
    response_headers: Dict[str, str] = Field(
        default_factory=dict, description="Response headers"
    )
    success_status_code: int = Field(
        200, ge=200, le=299, description="Success status code"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    webhook_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_by: str = Field(..., description="Creator user ID")


class WebhookEndpointResponse(BaseIntegrationSchema):
    """Schema for webhook endpoint response."""

    id: str = Field(..., description="Webhook ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Webhook name")
    description: Optional[str] = Field(None, description="Webhook description")
    endpoint_url: str = Field(..., description="Endpoint URL")

    # Configuration
    allowed_methods: List[str] = Field(..., description="Allowed HTTP methods")
    content_types: List[str] = Field(..., description="Allowed content types")
    max_body_size_mb: int = Field(..., description="Max body size (MB)")
    enable_signature_verification: bool = Field(
        ..., description="Enable signature verification"
    )

    # Security
    rate_limit_per_minute: int = Field(..., description="Rate limit per minute")

    # Monitoring
    total_requests: int = Field(..., description="Total requests")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    blocked_requests: int = Field(..., description="Blocked requests")

    # Status
    is_active: bool = Field(..., description="Active status")
    last_request_at: Optional[datetime] = Field(
        None, description="Last request timestamp"
    )

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


class WebhookRequestProcessing(BaseIntegrationSchema):
    """Schema for webhook request processing."""

    method: str = Field(..., description="HTTP method")
    headers: Dict[str, str] = Field(..., description="Request headers")
    query_parameters: Dict[str, str] = Field(
        default_factory=dict, description="Query parameters"
    )
    body: str = Field("", description="Request body")
    content_type: Optional[str] = Field(None, description="Content type")
    client_ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent")


# =============================================================================
# Message Queue Schemas
# =============================================================================


class IntegrationMessageCreateRequest(BaseIntegrationSchema):
    """Schema for creating an integration message."""

    organization_id: str = Field(..., description="Organization ID")
    message_type: str = Field(..., max_length=100, description="Message type")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    headers: Dict[str, str] = Field(default_factory=dict, description="Message headers")

    # Routing
    source_system: Optional[str] = Field(
        None, max_length=200, description="Source system"
    )
    target_system: Optional[str] = Field(
        None, max_length=200, description="Target system"
    )
    routing_key: Optional[str] = Field(None, max_length=200, description="Routing key")
    queue_name: Optional[str] = Field(None, max_length=200, description="Queue name")

    # Processing
    priority: int = Field(5, ge=1, le=10, description="Message priority")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled time")

    # Delivery
    max_attempts: int = Field(3, ge=1, le=10, description="Max delivery attempts")
    processing_timeout: int = Field(
        300, ge=1, le=3600, description="Processing timeout"
    )
    delay_seconds: int = Field(0, ge=0, le=86400, description="Delay before processing")
    ttl_seconds: Optional[int] = Field(None, ge=60, description="Time to live")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    message_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class IntegrationMessageResponse(BaseIntegrationSchema):
    """Schema for integration message response."""

    id: str = Field(..., description="Message ID")
    organization_id: str = Field(..., description="Organization ID")
    message_id: str = Field(..., description="Unique message ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    message_type: str = Field(..., description="Message type")

    # Routing
    source_system: Optional[str] = Field(None, description="Source system")
    target_system: Optional[str] = Field(None, description="Target system")
    routing_key: Optional[str] = Field(None, description="Routing key")

    # Processing
    status: str = Field(..., description="Message status")
    priority: int = Field(..., description="Message priority")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled time")

    # Delivery
    attempt_count: int = Field(..., description="Attempt count")
    max_attempts: int = Field(..., description="Max attempts")
    last_attempt_at: Optional[datetime] = Field(None, description="Last attempt time")
    next_attempt_at: Optional[datetime] = Field(None, description="Next attempt time")

    # Timing
    expires_at: Optional[datetime] = Field(None, description="Expiration time")

    # Results
    error_message: Optional[str] = Field(None, description="Error message")

    # Metadata
    tags: List[str] = Field(..., description="Tags")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")


# =============================================================================
# Analytics & Health Schemas
# =============================================================================


class IntegrationHealthResponse(BaseIntegrationSchema):
    """Schema for integration system health response."""

    overall_health_score: float = Field(..., description="Overall health score (0-100)")
    status: str = Field(..., description="Health status")

    external_systems: Dict[str, Any] = Field(..., description="External systems health")
    connectors: Dict[str, Any] = Field(..., description="Connectors health")
    executions_24h: Dict[str, Any] = Field(..., description="24h execution statistics")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")

    checked_at: str = Field(..., description="Health check timestamp")


class IntegrationAnalyticsRequest(BaseIntegrationSchema):
    """Schema for integration analytics request."""

    organization_id: str = Field(..., description="Organization ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    # Filters
    system_ids: Optional[List[str]] = Field(None, description="Filter by system IDs")
    connector_ids: Optional[List[str]] = Field(
        None, description="Filter by connector IDs"
    )
    integration_types: Optional[List[str]] = Field(
        None, description="Filter by integration types"
    )

    # Grouping
    group_by: List[str] = Field(default_factory=list, description="Group by fields")
    include_details: bool = Field(False, description="Include detailed metrics")


class IntegrationAnalyticsResponse(BaseIntegrationSchema):
    """Schema for integration analytics response."""

    organization_id: str = Field(..., description="Organization ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    # System metrics
    total_systems: int = Field(..., description="Total external systems")
    active_systems: int = Field(..., description="Active systems")
    connected_systems: int = Field(..., description="Connected systems")

    # Connector metrics
    total_connectors: int = Field(..., description="Total connectors")
    active_connectors: int = Field(..., description="Active connectors")

    # Execution metrics
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")
    success_rate: float = Field(..., description="Success rate percentage")

    # Data metrics
    total_records_processed: int = Field(..., description="Total records processed")
    records_created: int = Field(..., description="Records created")
    records_updated: int = Field(..., description="Records updated")
    records_deleted: int = Field(..., description="Records deleted")

    # Performance metrics
    average_execution_time_ms: Optional[float] = Field(
        None, description="Average execution time"
    )
    average_response_time_ms: Optional[float] = Field(
        None, description="Average response time"
    )

    # Error analysis
    top_errors: List[Dict[str, Any]] = Field(..., description="Top error messages")
    error_trends: List[Dict[str, Any]] = Field(..., description="Error trends")

    # Generated timestamp
    generated_at: datetime = Field(..., description="Analytics generation timestamp")


# =============================================================================
# Bulk Operation Schemas
# =============================================================================


class BulkConnectorExecutionRequest(BaseIntegrationSchema):
    """Schema for bulk connector execution."""

    connector_ids: List[str] = Field(
        ..., min_items=1, max_items=100, description="Connector IDs"
    )
    execution_type: str = Field("manual", description="Execution type")
    triggered_by: Optional[str] = Field(None, description="Triggered by user ID")
    parallel_execution: bool = Field(False, description="Execute in parallel")
    config_overrides: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration overrides"
    )


class BulkExecutionResponse(BaseIntegrationSchema):
    """Schema for bulk execution response."""

    execution_id: str = Field(..., description="Bulk execution ID")
    total_requested: int = Field(..., description="Total requested")
    successful: int = Field(..., description="Successful executions")
    failed: int = Field(..., description="Failed executions")

    # Results
    execution_results: List[Dict[str, Any]] = Field(
        ..., description="Individual execution results"
    )
    errors: List[Dict[str, Any]] = Field(..., description="Error details")

    # Timing
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    total_duration_ms: Optional[int] = Field(None, description="Total duration (ms)")


# =============================================================================
# List Response Schemas
# =============================================================================


class ConnectorListResponse(BaseIntegrationSchema):
    """Schema for connector list response."""

    connectors: List[IntegrationConnectorResponse] = Field(
        ..., description="Connectors"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class ExecutionListResponse(BaseIntegrationSchema):
    """Schema for execution list response."""

    executions: List[IntegrationExecutionResponse] = Field(
        ..., description="Executions"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class MappingListResponse(BaseIntegrationSchema):
    """Schema for mapping list response."""

    mappings: List[DataMappingResponse] = Field(..., description="Data mappings")
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class TransformationListResponse(BaseIntegrationSchema):
    """Schema for transformation list response."""

    transformations: List[DataTransformationResponse] = Field(
        ..., description="Transformations"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class WebhookListResponse(BaseIntegrationSchema):
    """Schema for webhook list response."""

    webhooks: List[WebhookEndpointResponse] = Field(
        ..., description="Webhook endpoints"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")


class MessageListResponse(BaseIntegrationSchema):
    """Schema for message list response."""

    messages: List[IntegrationMessageResponse] = Field(
        ..., description="Integration messages"
    )
    total_count: int = Field(..., description="Total count")
    page: int = Field(1, description="Current page")
    per_page: int = Field(50, description="Items per page")
    has_more: bool = Field(False, description="Has more items")
