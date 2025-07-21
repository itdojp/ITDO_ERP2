"""Comprehensive audit system models with tamper-proof trail."""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuditEventType(str, Enum):
    """Types of audit events."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    SYSTEM_CONFIG = "system_config"
    SECURITY_EVENT = "security_event"
    API_CALL = "api_call"
    BULK_OPERATION = "bulk_operation"
    ADMIN_ACTION = "admin_action"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    SOX = "sox"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    SOC2 = "soc2"
    NIST = "nist"


class ComprehensiveAuditLog(Base):
    """Comprehensive audit log with tamper-proof features."""
    
    __tablename__ = "comprehensive_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Unique identifier for traceability
    audit_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid4()))
    
    # Event identification
    event_type: Mapped[AuditEventType] = mapped_column(String(50), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AuditSeverity] = mapped_column(String(20), default=AuditSeverity.MEDIUM, index=True)
    
    # Actor information
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    user_ip_address: Mapped[Optional[str]] = mapped_column(String(45), index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Resource information
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Context and metadata
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id"), index=True)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    http_method: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Change tracking
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    changes_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # Additional context
    additional_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)  # For categorization and search
    
    # Compliance and regulatory
    compliance_frameworks: Mapped[Optional[List[ComplianceFramework]]] = mapped_column(JSON)
    retention_period_days: Mapped[int] = mapped_column(Integer, default=2555)  # 7 years default
    
    # Timing
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    event_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)  # Event processing time
    
    # Status and flags
    is_successful: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    requires_investigation: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Tamper-proof features
    previous_log_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    current_log_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chain_integrity_verified: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Geolocation (if available)
    country: Mapped[Optional[str]] = mapped_column(String(3), index=True)  # ISO country code
    region: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column()
    longitude: Mapped[Optional[float]] = mapped_column()
    
    # Data classification
    data_classification: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # public, internal, confidential, restricted
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    contains_financial_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    contains_health_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Export and archival
    is_exported: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    export_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    archive_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    department = relationship("Department", foreign_keys=[department_id])
    
    def __init__(self, **kwargs):
        """Initialize audit log with automatic hash calculation."""
        super().__init__(**kwargs)
        self._calculate_hash()
    
    def _calculate_hash(self) -> None:
        """Calculate tamper-proof hash for this log entry."""
        # Create a deterministic string representation of the log data
        hash_data = {
            "audit_id": self.audit_id,
            "event_type": self.event_type,
            "event_name": self.event_name,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "additional_data": self.additional_data
        }
        
        # Create JSON string and hash it
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        
        # Include previous hash to create chain
        if self.previous_log_hash:
            hash_string += self.previous_log_hash
        
        self.current_log_hash = hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_integrity(self, previous_log: Optional['ComprehensiveAuditLog'] = None) -> bool:
        """Verify the integrity of this audit log entry."""
        # Recalculate hash and compare
        original_hash = self.current_log_hash
        self._calculate_hash()
        hash_matches = self.current_log_hash == original_hash
        
        # Verify chain integrity
        if previous_log:
            chain_valid = self.previous_log_hash == previous_log.current_log_hash
        else:
            chain_valid = self.previous_log_hash is None
        
        self.chain_integrity_verified = hash_matches and chain_valid
        return self.chain_integrity_verified
    
    def to_export_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "event_name": self.event_name,
            "event_description": self.event_description,
            "severity": self.severity,
            "user_email": self.user_email,
            "user_ip_address": self.user_ip_address,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "changes_summary": self.changes_summary,
            "additional_data": self.additional_data,
            "is_successful": self.is_successful,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "compliance_frameworks": self.compliance_frameworks,
            "tags": self.tags,
            "current_log_hash": self.current_log_hash,
            "chain_integrity_verified": self.chain_integrity_verified
        }

    def __repr__(self) -> str:
        return f"<ComprehensiveAuditLog(id={self.id}, event='{self.event_name}', user_id={self.user_id})>"


class AuditSearchQuery(Base):
    """Saved audit search queries for compliance reporting."""
    
    __tablename__ = "audit_search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Query identification
    query_name: Mapped[str] = mapped_column(String(200), nullable=False)
    query_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Search criteria
    search_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Time range
    date_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    date_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Compliance and reporting
    compliance_framework: Mapped[Optional[ComplianceFramework]] = mapped_column(String(50))
    is_compliance_query: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    scheduled_frequency: Mapped[Optional[str]] = mapped_column(String(50))  # daily, weekly, monthly, quarterly
    
    # Access control
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    last_executed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    organization = relationship("Organization", foreign_keys=[organization_id])

    def __repr__(self) -> str:
        return f"<AuditSearchQuery(id={self.id}, name='{self.query_name}')>"


class AuditExport(Base):
    """Audit data export tracking."""
    
    __tablename__ = "audit_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Export identification
    export_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid4()))
    export_name: Mapped[str] = mapped_column(String(200), nullable=False)
    export_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Export criteria
    search_query_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("audit_search_queries.id"))
    export_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Time range
    date_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Export details
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # csv, json, pdf, xlsx
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    download_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Compliance
    compliance_framework: Mapped[Optional[ComplianceFramework]] = mapped_column(String(50))
    regulatory_purpose: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Access control
    requested_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    access_granted_to: Mapped[Optional[List[str]]] = mapped_column(JSON)  # List of user emails
    
    # Timing
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Security
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    password_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    access_log: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)  # Track who accessed the export
    
    # Relationships
    requester = relationship("User", foreign_keys=[requested_by])
    organization = relationship("Organization", foreign_keys=[organization_id])
    search_query = relationship("AuditSearchQuery", foreign_keys=[search_query_id])

    def __repr__(self) -> str:
        return f"<AuditExport(id={self.id}, name='{self.export_name}', status='{self.status}')>"


class ComplianceReport(Base):
    """Compliance reporting for various frameworks."""
    
    __tablename__ = "compliance_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Report identification
    report_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid4()))
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    report_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Compliance framework
    compliance_framework: Mapped[ComplianceFramework] = mapped_column(String(50), nullable=False, index=True)
    framework_version: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Reporting period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Report content
    total_events_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    compliance_score: Mapped[Optional[float]] = mapped_column()  # 0.0 to 100.0
    findings: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    recommendations: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Report data
    summary_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    detailed_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # File information
    report_format: Mapped[str] = mapped_column(String(20), default="pdf")
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Status and metadata
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)  # draft, final, approved, rejected
    generated_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    
    # Timing
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    generator = relationship("User", foreign_keys=[generated_by])
    approver = relationship("User", foreign_keys=[approved_by])
    organization = relationship("Organization", foreign_keys=[organization_id])

    def __repr__(self) -> str:
        return f"<ComplianceReport(id={self.id}, framework='{self.compliance_framework}', status='{self.status}')>"


# Database indexes for performance
Index("idx_audit_logs_timestamp_user", ComprehensiveAuditLog.timestamp, ComprehensiveAuditLog.user_id)
Index("idx_audit_logs_resource_timestamp", ComprehensiveAuditLog.resource_type, ComprehensiveAuditLog.resource_id, ComprehensiveAuditLog.timestamp)
Index("idx_audit_logs_event_type_timestamp", ComprehensiveAuditLog.event_type, ComprehensiveAuditLog.timestamp)
Index("idx_audit_logs_org_timestamp", ComprehensiveAuditLog.organization_id, ComprehensiveAuditLog.timestamp)
Index("idx_audit_logs_compliance_timestamp", ComprehensiveAuditLog.compliance_frameworks, ComprehensiveAuditLog.timestamp)
Index("idx_audit_logs_severity_timestamp", ComprehensiveAuditLog.severity, ComprehensiveAuditLog.timestamp)
Index("idx_audit_logs_hash_chain", ComprehensiveAuditLog.current_log_hash, ComprehensiveAuditLog.previous_log_hash)