"""
Integration System Models - CC02 v31.0 Phase 2

Comprehensive integration system with:
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

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class IntegrationType(str, Enum):
    """Integration type enumeration."""

    API = "api"
    DATABASE = "database"
    FILE = "file"
    MESSAGE_QUEUE = "message_queue"
    WEBHOOK = "webhook"
    FTP = "ftp"
    EMAIL = "email"
    CLOUD_STORAGE = "cloud_storage"
    ERP = "erp"
    CRM = "crm"
    ACCOUNTING = "accounting"
    ECOMMERCE = "ecommerce"


class ConnectionStatus(str, Enum):
    """Connection status enumeration."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"


class SyncDirection(str, Enum):
    """Sync direction enumeration."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Sync status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class DataFormat(str, Enum):
    """Data format enumeration."""

    JSON = "json"
    XML = "xml"
    CSV = "csv"
    EXCEL = "excel"
    FIXED_WIDTH = "fixed_width"
    EDI = "edi"
    CUSTOM = "custom"


class TransformationType(str, Enum):
    """Transformation type enumeration."""

    FIELD_MAPPING = "field_mapping"
    DATA_CONVERSION = "data_conversion"
    AGGREGATION = "aggregation"
    FILTERING = "filtering"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    CUSTOM_SCRIPT = "custom_script"


class ExternalSystem(Base):
    """External System - Configuration for external system connections."""

    __tablename__ = "external_systems"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # System identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    integration_type = Column(SQLEnum(IntegrationType), nullable=False)

    # Connection configuration
    base_url = Column(String(1000))
    api_version = Column(String(50))
    endpoint_prefix = Column(String(200))
    connection_config = Column(JSON, default={})

    # Authentication
    auth_type = Column(String(100))  # oauth2, api_key, basic, bearer, custom
    auth_config = Column(JSON, default={})
    credentials = Column(JSON, default={})  # Encrypted
    auth_expires_at = Column(DateTime)

    # Rate limiting
    rate_limit_requests = Column(Integer)
    rate_limit_period = Column(Integer)  # seconds
    rate_limit_remaining = Column(Integer)
    rate_limit_reset_at = Column(DateTime)

    # Health monitoring
    connection_status = Column(
        SQLEnum(ConnectionStatus), default=ConnectionStatus.DISCONNECTED
    )
    last_health_check = Column(DateTime)
    health_check_interval = Column(Integer, default=300)  # seconds
    uptime_percentage = Column(Numeric(5, 2))

    # Performance metrics
    average_response_time = Column(Numeric(8, 2))
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)

    # Configuration
    timeout_seconds = Column(Integer, default=30)
    retry_attempts = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=5)
    enable_logging = Column(Boolean, default=True)

    # Status and settings
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)

    # Metadata
    vendor = Column(String(200))
    version = Column(String(100))
    documentation_url = Column(String(1000))
    support_contact = Column(String(500))
    tags = Column(JSON, default=[])
    integration_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")
    connectors = relationship("IntegrationConnector", back_populates="external_system")


class IntegrationConnector(Base):
    """Integration Connector - Specific integration endpoints and operations."""

    __tablename__ = "integration_connectors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    external_system_id = Column(
        String, ForeignKey("external_systems.id"), nullable=False
    )

    # Connector identification
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    operation_type = Column(
        String(100), nullable=False
    )  # create, read, update, delete, sync, custom

    # Endpoint configuration
    endpoint_url = Column(String(1000), nullable=False)
    http_method = Column(String(20), default="GET")
    request_headers = Column(JSON, default={})
    request_parameters = Column(JSON, default={})
    request_body_template = Column(Text)

    # Data handling
    data_format = Column(SQLEnum(DataFormat), default=DataFormat.JSON)
    sync_direction = Column(SQLEnum(SyncDirection), nullable=False)
    entity_type = Column(String(100))  # users, products, orders, etc.

    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_cron = Column(String(100))
    schedule_config = Column(JSON, default={})
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)

    # Execution settings
    batch_size = Column(Integer, default=100)
    parallel_workers = Column(Integer, default=1)
    timeout_seconds = Column(Integer, default=300)
    max_retries = Column(Integer, default=3)

    # Status and monitoring
    is_active = Column(Boolean, default=True)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    average_execution_time = Column(Numeric(10, 2))

    # Data tracking
    total_records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)

    # Error handling
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    alert_on_failure = Column(Boolean, default=True)
    notification_recipients = Column(JSON, default=[])

    # Metadata
    tags = Column(JSON, default=[])
    connector_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    external_system = relationship("ExternalSystem", back_populates="connectors")
    creator = relationship("User")
    executions = relationship("IntegrationExecution", back_populates="connector")
    transformations = relationship("DataTransformation", back_populates="connector")


class DataMapping(Base):
    """Data Mapping - Field mappings between internal and external systems."""

    __tablename__ = "data_mappings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    connector_id = Column(
        String, ForeignKey("integration_connectors.id"), nullable=False
    )

    # Mapping identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    entity_type = Column(String(100), nullable=False)
    sync_direction = Column(SQLEnum(SyncDirection), nullable=False)

    # Field mappings
    source_schema = Column(JSON, default={})
    target_schema = Column(JSON, default={})
    field_mappings = Column(JSON, nullable=False)  # source_field -> target_field

    # Transformation rules
    transformation_rules = Column(JSON, default=[])
    validation_rules = Column(JSON, default={})
    default_values = Column(JSON, default={})
    conditional_mappings = Column(JSON, default=[])

    # Data processing
    data_filters = Column(JSON, default={})
    aggregation_rules = Column(JSON, default={})
    grouping_rules = Column(JSON, default={})
    sorting_rules = Column(JSON, default=[])

    # Quality control
    enable_validation = Column(Boolean, default=True)
    required_fields = Column(JSON, default=[])
    unique_fields = Column(JSON, default=[])
    data_type_validation = Column(JSON, default={})

    # Performance
    use_bulk_operations = Column(Boolean, default=True)
    chunk_size = Column(Integer, default=1000)
    enable_caching = Column(Boolean, default=False)
    cache_ttl_seconds = Column(Integer, default=3600)

    # Status and metrics
    is_active = Column(Boolean, default=True)
    records_mapped = Column(Integer, default=0)
    mapping_errors = Column(Integer, default=0)
    last_validation_errors = Column(JSON, default=[])

    # Versioning
    version = Column(String(50), default="1.0")
    change_log = Column(JSON, default=[])

    # Metadata
    tags = Column(JSON, default=[])
    mapping_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")


class DataTransformation(Base):
    """Data Transformation - Complex data transformation logic."""

    __tablename__ = "data_transformations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    connector_id = Column(String, ForeignKey("integration_connectors.id"))

    # Transformation identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    transformation_type = Column(SQLEnum(TransformationType), nullable=False)

    # Transformation logic
    input_schema = Column(JSON, default={})
    output_schema = Column(JSON, default={})
    transformation_script = Column(Text)
    transformation_config = Column(JSON, default={})

    # Processing settings
    language = Column(String(50), default="python")  # python, javascript, sql
    execution_environment = Column(String(100))
    dependencies = Column(JSON, default=[])
    resource_limits = Column(JSON, default={})

    # Performance
    execution_timeout = Column(Integer, default=300)  # seconds
    memory_limit_mb = Column(Integer, default=512)
    cpu_limit_percent = Column(Numeric(5, 2), default=50.0)

    # Monitoring
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    average_execution_time = Column(Numeric(8, 2))

    # Error handling
    last_error = Column(Text)
    error_handling_strategy = Column(String(100), default="skip")  # skip, retry, fail
    max_error_rate = Column(Numeric(5, 2), default=5.0)

    # Testing
    test_cases = Column(JSON, default=[])
    last_test_results = Column(JSON, default={})
    test_coverage_percentage = Column(Numeric(5, 2))

    # Status and versioning
    is_active = Column(Boolean, default=True)
    version = Column(String(50), default="1.0")
    change_log = Column(JSON, default=[])

    # Metadata
    tags = Column(JSON, default=[])
    transformation_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    connector = relationship("IntegrationConnector", back_populates="transformations")
    creator = relationship("User")


class IntegrationExecution(Base):
    """Integration Execution - Individual execution records."""

    __tablename__ = "integration_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    connector_id = Column(
        String, ForeignKey("integration_connectors.id"), nullable=False
    )

    # Execution details
    execution_type = Column(
        String(50), nullable=False
    )  # scheduled, manual, triggered, webhook
    trigger_source = Column(String(100))
    triggered_by = Column(String, ForeignKey("users.id"))

    # Status and timing
    status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)

    # Request details
    request_id = Column(String(200))
    request_headers = Column(JSON, default={})
    request_body = Column(Text)
    request_size_bytes = Column(Integer)

    # Response details
    response_status_code = Column(Integer)
    response_headers = Column(JSON, default={})
    response_body = Column(Text)
    response_size_bytes = Column(Integer)

    # Data processing
    records_requested = Column(Integer, default=0)
    records_received = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Performance metrics
    network_time_ms = Column(Integer)
    processing_time_ms = Column(Integer)
    database_time_ms = Column(Integer)
    transformation_time_ms = Column(Integer)

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)

    # Data samples
    sample_request_data = Column(JSON)
    sample_response_data = Column(JSON)

    # Metadata
    execution_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    connector = relationship("IntegrationConnector", back_populates="executions")
    triggered_by_user = relationship("User")


class WebhookEndpoint(Base):
    """Webhook Endpoint - Incoming webhook configuration."""

    __tablename__ = "webhook_endpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Webhook identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    endpoint_url = Column(String(1000), nullable=False, unique=True, index=True)
    webhook_secret = Column(String(500))  # For signature verification

    # Configuration
    allowed_methods = Column(JSON, default=["POST"])
    content_types = Column(JSON, default=["application/json"])
    max_body_size_mb = Column(Integer, default=10)
    enable_signature_verification = Column(Boolean, default=True)

    # Security
    allowed_ips = Column(JSON, default=[])
    require_authentication = Column(Boolean, default=False)
    rate_limit_per_minute = Column(Integer, default=100)

    # Processing
    processing_script = Column(Text)
    processing_config = Column(JSON, default={})
    enable_async_processing = Column(Boolean, default=True)

    # Response configuration
    response_template = Column(Text)
    response_headers = Column(JSON, default={})
    success_status_code = Column(Integer, default=200)

    # Monitoring
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    last_request_at = Column(DateTime)

    # Metadata
    tags = Column(JSON, default=[])
    webhook_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")
    requests = relationship("WebhookRequest", back_populates="webhook_endpoint")


class WebhookRequest(Base):
    """Webhook Request - Individual webhook request logs."""

    __tablename__ = "webhook_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    webhook_endpoint_id = Column(
        String, ForeignKey("webhook_endpoints.id"), nullable=False
    )

    # Request details
    method = Column(String(20), nullable=False)
    headers = Column(JSON, default={})
    query_parameters = Column(JSON, default={})
    body = Column(Text)
    content_type = Column(String(200))
    content_length = Column(Integer)

    # Client information
    client_ip = Column(String(45))
    user_agent = Column(String(500))
    referer = Column(String(1000))

    # Processing
    processing_status = Column(String(50), default="pending")
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_duration_ms = Column(Integer)

    # Response
    response_status_code = Column(Integer)
    response_headers = Column(JSON, default={})
    response_body = Column(Text)
    response_size_bytes = Column(Integer)

    # Security
    signature_verified = Column(Boolean)
    ip_allowed = Column(Boolean)
    rate_limit_hit = Column(Boolean)

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)

    # Metadata
    request_metadata = Column(JSON, default={})

    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    webhook_endpoint = relationship("WebhookEndpoint", back_populates="requests")


class IntegrationMessage(Base):
    """Integration Message - Message queue for async processing."""

    __tablename__ = "integration_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Message identification
    message_id = Column(String(200), unique=True, index=True)
    correlation_id = Column(String(200), index=True)
    parent_message_id = Column(String(200))

    # Message content
    message_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, default={})

    # Routing
    source_system = Column(String(200))
    target_system = Column(String(200))
    routing_key = Column(String(200))
    exchange = Column(String(200))
    queue_name = Column(String(200))

    # Processing
    status = Column(
        String(50), default="pending"
    )  # pending, processing, completed, failed, dead_letter
    priority = Column(Integer, default=5)  # 1-10, higher is more important
    scheduled_at = Column(DateTime)

    # Delivery
    max_attempts = Column(Integer, default=3)
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    next_attempt_at = Column(DateTime)

    # Timing
    expires_at = Column(DateTime)
    processing_timeout = Column(Integer, default=300)  # seconds
    delay_seconds = Column(Integer, default=0)

    # Results
    result_data = Column(JSON)
    error_message = Column(Text)
    error_details = Column(JSON)

    # Metadata
    tags = Column(JSON, default=[])
    message_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")


class IntegrationAuditLog(Base):
    """Integration Audit Log - Comprehensive audit trail for integration operations."""

    __tablename__ = "integration_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Action details
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String, nullable=False)

    # User and session
    user_id = Column(String, ForeignKey("users.id"))
    session_id = Column(String(200))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes_summary = Column(String(1000))

    # Context
    integration_system = Column(String(200))
    operation_context = Column(JSON, default={})
    related_entities = Column(JSON, default=[])

    # Impact assessment
    impact_level = Column(String(50))  # low, medium, high, critical
    affected_records = Column(Integer)
    data_sensitivity = Column(String(50))

    # Performance
    execution_time_ms = Column(Integer)
    resource_usage = Column(JSON, default={})

    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
