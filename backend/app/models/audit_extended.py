"""
Audit Log System Models - CC02 v31.0 Phase 2

Comprehensive audit log system with:
- System-wide Activity Tracking
- Compliance & Regulatory Auditing
- Security Event Monitoring
- Data Change Tracking
- User Action Logging
- Performance Monitoring
- Risk Assessment & Alerting
- Forensic Analysis Support
- Real-time Monitoring
- Automated Compliance Reporting

Provides complete audit trail for enterprise compliance and security
"""

import uuid
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
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


class AuditEventType(str, Enum):
    """Audit event type enumeration."""

    # Authentication & Authorization
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"

    # Data Operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"

    # System Operations
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIGURATION_CHANGE = "configuration_change"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"

    # Security Events
    SECURITY_VIOLATION = "security_violation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALWARE_DETECTED = "malware_detected"

    # Workflow Events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    TASK_ASSIGNED = "task_assigned"
    APPROVAL_GRANTED = "approval_granted"

    # Financial Events
    PAYMENT_PROCESSED = "payment_processed"
    TRANSACTION_CREATED = "transaction_created"
    BUDGET_EXCEEDED = "budget_exceeded"

    # Custom Events
    CUSTOM = "custom"


class AuditSeverity(str, Enum):
    """Audit severity level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """Audit status enumeration."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class ComplianceFramework(str, Enum):
    """Compliance framework enumeration."""

    SOX = "sox"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    SOC2 = "soc2"
    CUSTOM = "custom"


class AuditLogEntry(Base):
    """Audit Log Entry - Individual audit log entries for system events."""

    __tablename__ = "audit_log_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Event identification
    event_type = Column(SQLEnum(AuditEventType), nullable=False)
    event_category = Column(String(100), nullable=False)
    event_name = Column(String(200), nullable=False)
    event_description = Column(Text)

    # Actor information
    user_id = Column(String, ForeignKey("users.id"))
    actor_type = Column(String(50), default="user")  # user, system, service, api
    actor_name = Column(String(200))
    impersonated_user_id = Column(String, ForeignKey("users.id"))

    # Target/Resource information
    resource_type = Column(String(100))  # table, file, endpoint, etc.
    resource_id = Column(String(200))
    resource_name = Column(String(500))

    # Event details
    action_performed = Column(String(200))
    outcome = Column(String(50))  # success, failure, partial
    severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.LOW)

    # Context data
    old_values = Column(JSON)
    new_values = Column(JSON)
    change_details = Column(JSON, default={})
    event_data = Column(JSON, default={})

    # Session and request information
    session_id = Column(String(200))
    request_id = Column(String(200))
    correlation_id = Column(String(200))

    # Network information
    ip_address = Column(String(45))
    user_agent = Column(String(1000))
    source_system = Column(String(100))

    # Compliance and risk
    compliance_frameworks = Column(JSON, default=[])
    risk_score = Column(Integer, default=0)
    tags = Column(JSON, default=[])

    # Status and handling
    status = Column(SQLEnum(AuditStatus), default=AuditStatus.ACTIVE)
    acknowledged_by = Column(String, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    resolution_notes = Column(Text)

    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    user = relationship("User", foreign_keys=[user_id])
    impersonated_user = relationship("User", foreign_keys=[impersonated_user_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])


class AuditRule(Base):
    """Audit Rule - Rules for automatic audit log generation and alerting."""

    __tablename__ = "audit_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Rule identification
    name = Column(String(200), nullable=False)
    description = Column(Text)
    rule_type = Column(String(100), nullable=False)  # event_trigger, threshold, pattern

    # Rule conditions
    conditions = Column(JSON, nullable=False)
    event_filters = Column(JSON, default={})
    threshold_config = Column(JSON, default={})

    # Actions
    actions = Column(JSON, default=[])  # log, alert, email, webhook
    alert_severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.MEDIUM)

    # Compliance mapping
    compliance_frameworks = Column(JSON, default=[])
    regulatory_requirements = Column(JSON, default=[])

    # Rule settings
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=50)
    evaluation_frequency = Column(String(100))  # real_time, hourly, daily

    # Performance tracking
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)
    false_positive_count = Column(Integer, default=0)

    # Metadata
    rule_metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")


class AuditAlert(Base):
    """Audit Alert - Alerts generated from audit rule violations."""

    __tablename__ = "audit_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    rule_id = Column(String, ForeignKey("audit_rules.id"), nullable=False)

    # Alert identification
    alert_type = Column(String(100), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    severity = Column(SQLEnum(AuditSeverity), nullable=False)

    # Triggering events
    triggering_event_ids = Column(JSON, default=[])
    event_count = Column(Integer, default=1)

    # Alert details
    alert_data = Column(JSON, default={})
    risk_assessment = Column(JSON, default={})
    recommended_actions = Column(JSON, default=[])

    # Status tracking
    status = Column(
        String(50), default="open"
    )  # open, investigating, resolved, false_positive
    assigned_to = Column(String, ForeignKey("users.id"))
    priority = Column(Integer, default=50)

    # Response tracking
    acknowledged_by = Column(String, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(String, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

    # Escalation
    escalation_level = Column(Integer, default=0)
    escalated_to = Column(JSON, default=[])
    escalation_history = Column(JSON, default=[])

    # Compliance
    compliance_impact = Column(String(100))
    regulatory_notification_required = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)

    # Timestamps
    first_occurrence = Column(DateTime(timezone=True), nullable=False)
    last_occurrence = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    rule = relationship("AuditRule")
    assignee = relationship("User", foreign_keys=[assigned_to])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])


class AuditReport(Base):
    """Audit Report - Generated compliance and audit reports."""

    __tablename__ = "audit_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Report identification
    report_name = Column(String(300), nullable=False)
    report_type = Column(
        String(100), nullable=False
    )  # compliance, security, operational, custom
    description = Column(Text)

    # Report parameters
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    report_filters = Column(JSON, default={})
    report_config = Column(JSON, default={})

    # Compliance framework
    compliance_framework = Column(SQLEnum(ComplianceFramework))
    regulatory_requirements = Column(JSON, default=[])

    # Report content
    executive_summary = Column(Text)
    findings = Column(JSON, default=[])
    recommendations = Column(JSON, default=[])
    metrics = Column(JSON, default={})

    # Report data
    total_events = Column(Integer, default=0)
    critical_events = Column(Integer, default=0)
    violations = Column(Integer, default=0)
    compliance_score = Column(Numeric(5, 2))

    # File information
    file_path = Column(String(1000))
    file_format = Column(String(50))  # pdf, xlsx, csv, json
    file_size = Column(Integer)

    # Generation details
    generated_by = Column(String, ForeignKey("users.id"), nullable=False)
    generation_status = Column(
        String(50), default="pending"
    )  # pending, generating, completed, failed
    generation_progress = Column(Integer, default=0)
    generation_error = Column(Text)

    # Distribution
    recipients = Column(JSON, default=[])
    distributed_at = Column(DateTime)
    distribution_status = Column(String(50))

    # Retention
    retention_period_days = Column(Integer, default=2555)  # 7 years default
    expires_at = Column(Date)
    is_archived = Column(Boolean, default=False)

    # Timestamps
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    generator = relationship("User")


class AuditSession(Base):
    """Audit Session - User session tracking for security monitoring."""

    __tablename__ = "audit_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Session identification
    session_token = Column(String(500), nullable=False, unique=True, index=True)
    session_type = Column(String(50), default="web")  # web, api, mobile, desktop

    # Authentication details
    authentication_method = Column(String(100))  # password, sso, mfa, api_key
    mfa_verified = Column(Boolean, default=False)
    authentication_factors = Column(JSON, default=[])

    # Session details
    ip_address = Column(String(45))
    user_agent = Column(String(1000))
    device_fingerprint = Column(String(500))
    geolocation = Column(JSON)

    # Session status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True))
    inactivity_duration = Column(Integer)  # seconds

    # Security monitoring
    suspicious_activity_count = Column(Integer, default=0)
    failed_action_count = Column(Integer, default=0)
    risk_score = Column(Integer, default=0)

    # Session metrics
    actions_performed = Column(Integer, default=0)
    data_accessed = Column(JSON, default=[])
    permissions_used = Column(JSON, default=[])

    # Termination
    terminated_reason = Column(String(200))
    terminated_by = Column(String(100))  # user, system, admin, timeout

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")


class AuditDataRetention(Base):
    """Audit Data Retention - Policies for audit data retention and archival."""

    __tablename__ = "audit_data_retention"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Policy identification
    policy_name = Column(String(200), nullable=False)
    description = Column(Text)
    policy_type = Column(
        String(100), nullable=False
    )  # event_based, time_based, size_based

    # Retention rules
    retention_criteria = Column(JSON, nullable=False)
    retention_period_days = Column(Integer)
    archive_after_days = Column(Integer)
    delete_after_days = Column(Integer)

    # Data scope
    applicable_event_types = Column(JSON, default=[])
    data_categories = Column(JSON, default=[])
    severity_levels = Column(JSON, default=[])

    # Archive settings
    archive_location = Column(String(500))
    archive_format = Column(String(50))  # compressed, encrypted, both
    archive_encryption = Column(Boolean, default=True)

    # Compliance requirements
    compliance_frameworks = Column(JSON, default=[])
    legal_hold_override = Column(Boolean, default=False)
    minimum_retention_days = Column(Integer)

    # Execution tracking
    last_executed = Column(DateTime)
    records_processed = Column(Integer, default=0)
    records_archived = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)

    # Policy status
    is_active = Column(Boolean, default=True)
    execution_schedule = Column(String(100))  # daily, weekly, monthly

    # Timestamps
    effective_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")


class AuditCompliance(Base):
    """Audit Compliance - Compliance status tracking and reporting."""

    __tablename__ = "audit_compliance"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Compliance framework
    framework = Column(SQLEnum(ComplianceFramework), nullable=False)
    framework_version = Column(String(50))
    requirement_id = Column(String(100))
    requirement_name = Column(String(300), nullable=False)
    requirement_description = Column(Text)

    # Assessment period
    assessment_period_start = Column(Date, nullable=False)
    assessment_period_end = Column(Date, nullable=False)

    # Compliance status
    compliance_status = Column(
        String(50), nullable=False
    )  # compliant, non_compliant, partial, not_assessed
    compliance_score = Column(Numeric(5, 2))
    risk_level = Column(String(50))  # low, medium, high, critical

    # Evidence and documentation
    evidence_items = Column(JSON, default=[])
    supporting_documents = Column(JSON, default=[])
    test_results = Column(JSON, default={})

    # Findings
    findings = Column(JSON, default=[])
    gaps_identified = Column(JSON, default=[])
    remediation_actions = Column(JSON, default=[])

    # Assessment details
    assessed_by = Column(String, ForeignKey("users.id"))
    assessment_method = Column(String(100))  # automated, manual, hybrid
    assessment_notes = Column(Text)

    # Remediation tracking
    remediation_plan = Column(JSON)
    remediation_deadline = Column(Date)
    remediation_status = Column(String(50))
    remediation_owner = Column(String, ForeignKey("users.id"))

    # Review and approval
    reviewed_by = Column(String, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    approved_by = Column(String, ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Next assessment
    next_assessment_due = Column(Date)
    assessment_frequency = Column(String(50))  # annual, semi_annual, quarterly, monthly

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    assessor = relationship("User", foreign_keys=[assessed_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])
    remediation_owner_user = relationship("User", foreign_keys=[remediation_owner])


class AuditConfiguration(Base):
    """Audit Configuration - System-wide audit configuration settings."""

    __tablename__ = "audit_configurations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Configuration identification
    config_name = Column(String(200), nullable=False)
    config_type = Column(
        String(100), nullable=False
    )  # logging, alerting, retention, compliance
    description = Column(Text)

    # Configuration settings
    config_data = Column(JSON, nullable=False)
    default_settings = Column(JSON, default={})
    override_settings = Column(JSON, default={})

    # Logging configuration
    log_levels = Column(JSON, default=["INFO", "WARN", "ERROR"])
    event_categories = Column(JSON, default=[])
    excluded_events = Column(JSON, default=[])

    # Alert configuration
    alert_thresholds = Column(JSON, default={})
    notification_channels = Column(JSON, default=[])
    escalation_rules = Column(JSON, default=[])

    # Performance settings
    batch_size = Column(Integer, default=1000)
    processing_interval = Column(Integer, default=60)  # seconds
    max_queue_size = Column(Integer, default=10000)

    # Storage settings
    storage_location = Column(String(500))
    compression_enabled = Column(Boolean, default=True)
    encryption_enabled = Column(Boolean, default=True)

    # Compliance settings
    compliance_frameworks = Column(JSON, default=[])
    data_classification = Column(JSON, default={})
    privacy_settings = Column(JSON, default={})

    # Configuration status
    is_active = Column(Boolean, default=True)
    version = Column(String(50), default="1.0")
    effective_date = Column(DateTime, nullable=False)

    # Change tracking
    change_history = Column(JSON, default=[])
    last_modified_by = Column(String, ForeignKey("users.id"))
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String, ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])
    modifier = relationship("User", foreign_keys=[last_modified_by])
    approver = relationship("User", foreign_keys=[approved_by])


class AuditMetrics(Base):
    """Audit Metrics - Performance and operational metrics for audit system."""

    __tablename__ = "audit_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    # Metrics period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(50), nullable=False)  # hourly, daily, weekly, monthly

    # Event metrics
    total_events = Column(Integer, default=0)
    events_by_type = Column(JSON, default={})
    events_by_severity = Column(JSON, default={})
    failed_events = Column(Integer, default=0)

    # Alert metrics
    total_alerts = Column(Integer, default=0)
    alerts_by_severity = Column(JSON, default={})
    false_positive_rate = Column(Numeric(5, 2))
    average_resolution_time = Column(Numeric(10, 2))  # minutes

    # Performance metrics
    processing_latency_avg = Column(Numeric(10, 3))  # milliseconds
    processing_latency_max = Column(Numeric(10, 3))
    throughput = Column(Integer)  # events per second
    error_rate = Column(Numeric(5, 2))

    # Storage metrics
    storage_used = Column(Numeric(15, 2))  # MB
    storage_growth_rate = Column(Numeric(10, 2))  # MB per day
    archived_records = Column(Integer, default=0)
    deleted_records = Column(Integer, default=0)

    # User activity metrics
    active_users = Column(Integer, default=0)
    suspicious_activities = Column(Integer, default=0)
    policy_violations = Column(Integer, default=0)

    # Compliance metrics
    compliance_score = Column(Numeric(5, 2))
    assessment_completion_rate = Column(Numeric(5, 2))
    remediation_completion_rate = Column(Numeric(5, 2))

    # System health
    system_uptime = Column(Numeric(5, 2))  # percentage
    queue_backlog = Column(Integer, default=0)
    resource_utilization = Column(JSON, default={})

    # Calculated at
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    organization = relationship("Organization")
