"""Comprehensive audit system API endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.comprehensive_audit import (
    AuditEventType,
    AuditSeverity,
    ComplianceFramework,
)
from app.models.user import User
from app.services.comprehensive_audit_service import (
    ComprehensiveAuditService,
    AuditSearchQueryService,
    AuditExportService,
    ComplianceReportService,
    check_audit_health,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# Pydantic schemas
class AuditEventCreate(BaseModel):
    """Create audit event schema."""
    event_type: AuditEventType
    event_name: str = Field(..., max_length=200)
    event_description: str = Field(..., max_length=1000)
    resource_type: str = Field(..., max_length=100)
    resource_id: Optional[str] = Field(None, max_length=100)
    resource_name: Optional[str] = Field(None, max_length=255)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None
    severity: AuditSeverity = AuditSeverity.MEDIUM
    compliance_frameworks: Optional[List[ComplianceFramework]] = []
    tags: Optional[List[str]] = []


class AuditEventResponse(BaseModel):
    """Audit event response schema."""
    id: int
    audit_id: str
    event_type: AuditEventType
    event_name: str
    event_description: str
    severity: AuditSeverity
    user_email: Optional[str]
    user_ip_address: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    resource_name: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    changes_summary: Optional[str]
    additional_data: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    compliance_frameworks: Optional[List[ComplianceFramework]]
    timestamp: datetime
    is_successful: bool
    error_message: Optional[str]
    current_log_hash: str
    chain_integrity_verified: bool
    contains_pii: bool
    contains_financial_data: bool
    contains_health_data: bool

    class Config:
        from_attributes = True


class AuditSearchRequest(BaseModel):
    """Audit search request schema."""
    filters: Dict[str, Any] = {}
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    include_pii: bool = False  # Require explicit opt-in for PII data


class AuditSearchResponse(BaseModel):
    """Audit search response schema."""
    logs: List[AuditEventResponse]
    total_count: int
    page_size: int
    current_page: int
    total_pages: int


class SavedQueryCreate(BaseModel):
    """Create saved query schema."""
    query_name: str = Field(..., max_length=200)
    query_description: Optional[str] = Field(None, max_length=1000)
    search_criteria: Dict[str, Any]
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    compliance_framework: Optional[ComplianceFramework] = None
    is_public: bool = False


class SavedQueryResponse(BaseModel):
    """Saved query response schema."""
    id: int
    query_name: str
    query_description: Optional[str]
    search_criteria: Dict[str, Any]
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    compliance_framework: Optional[ComplianceFramework]
    is_compliance_query: bool
    created_at: datetime
    last_executed: Optional[datetime]
    execution_count: int

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    """Export request schema."""
    export_name: Optional[str] = None
    export_criteria: Dict[str, Any]
    format: str = Field(..., pattern=r'^(csv|json|pdf|xlsx)$')
    compliance_framework: Optional[ComplianceFramework] = None
    include_sensitive_data: bool = False


class ExportResponse(BaseModel):
    """Export response schema."""
    id: int
    export_id: str
    export_name: str
    format: str
    status: str
    total_records: int
    file_size_bytes: Optional[int]
    download_url: Optional[str]
    requested_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class ComplianceReportRequest(BaseModel):
    """Compliance report request schema."""
    compliance_framework: ComplianceFramework
    period_start: datetime
    period_end: datetime
    include_detailed_findings: bool = True


class ComplianceReportResponse(BaseModel):
    """Compliance report response schema."""
    id: int
    report_id: str
    report_name: str
    compliance_framework: ComplianceFramework
    period_start: datetime
    period_end: datetime
    total_events_analyzed: int
    compliance_score: Optional[float]
    status: str
    generated_at: datetime
    file_path: Optional[str]

    class Config:
        from_attributes = True


class IntegrityVerificationResponse(BaseModel):
    """Chain integrity verification response."""
    total_logs_checked: int
    integrity_violations: List[Dict[str, Any]]
    chain_breaks: List[Dict[str, Any]]
    overall_integrity: bool
    verification_timestamp: datetime


# Audit logging endpoints
@router.post("/events", response_model=AuditEventResponse)
async def create_audit_event(
    event_data: AuditEventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new audit event."""
    service = ComprehensiveAuditService(db)
    
    audit_log = await service.log_event(
        event_type=event_data.event_type,
        event_name=event_data.event_name,
        event_description=event_data.event_description,
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type=event_data.resource_type,
        resource_id=event_data.resource_id,
        resource_name=event_data.resource_name,
        old_values=event_data.old_values,
        new_values=event_data.new_values,
        additional_data=event_data.additional_data,
        severity=event_data.severity,
        organization_id=current_user.organization_id,
        request=request,
        compliance_frameworks=event_data.compliance_frameworks,
        tags=event_data.tags
    )
    
    return audit_log


@router.post("/events/search", response_model=AuditSearchResponse)
async def search_audit_events(
    search_request: AuditSearchRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search audit events with advanced filtering."""
    service = ComprehensiveAuditService(db)
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Filter sensitive data access unless explicitly requested
    if not search_request.include_pii and not current_user.is_superuser:
        # Add filters to exclude PII data for non-admin users
        search_request.filters["contains_pii"] = False
    
    logs, total_count = await service.search_audit_logs(
        filters=search_request.filters,
        start_date=search_request.start_date,
        end_date=search_request.end_date,
        limit=page_size,
        offset=offset,
        sort_by=search_request.sort_by,
        sort_order=search_request.sort_order,
        organization_id=current_user.organization_id
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    return AuditSearchResponse(
        logs=logs,
        total_count=total_count,
        page_size=page_size,
        current_page=page,
        total_pages=total_pages
    )


@router.get("/events/{audit_id}", response_model=AuditEventResponse)
async def get_audit_event(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific audit event by ID."""
    service = ComprehensiveAuditService(db)
    
    audit_log = await service.get_by_filters({"audit_id": audit_id})
    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit event not found"
        )
    
    # Check access permissions
    if (audit_log.organization_id and 
        audit_log.organization_id != current_user.organization_id and 
        not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return audit_log


# Saved queries endpoints
@router.post("/queries", response_model=SavedQueryResponse)
async def create_saved_query(
    query_data: SavedQueryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a saved audit search query."""
    service = AuditSearchQueryService(db)
    
    saved_query = await service.save_search_query(
        query_name=query_data.query_name,
        search_criteria=query_data.search_criteria,
        user_id=current_user.id,
        description=query_data.query_description,
        date_from=query_data.date_from,
        date_to=query_data.date_to,
        compliance_framework=query_data.compliance_framework,
        organization_id=current_user.organization_id
    )
    
    return saved_query


@router.get("/queries", response_model=List[SavedQueryResponse])
async def list_saved_queries(
    compliance_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List saved audit queries."""
    service = AuditSearchQueryService(db)
    
    filters = {"created_by": current_user.id}
    if compliance_only:
        filters["is_compliance_query"] = True
    
    queries = await service.get_multi(
        skip=skip,
        limit=limit,
        filters=filters,
        organization_id=current_user.organization_id
    )
    
    return queries


@router.post("/queries/{query_id}/execute", response_model=AuditSearchResponse)
async def execute_saved_query(
    query_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a saved audit query."""
    query_service = AuditSearchQueryService(db)
    audit_service = ComprehensiveAuditService(db)
    
    # Check query access
    saved_query = await query_service.get_by_id(query_id)
    if not saved_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    if (saved_query.created_by != current_user.id and 
        not saved_query.is_public and 
        not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Execute query
    logs, total_count = await query_service.execute_saved_query(
        query_id=query_id,
        audit_service=audit_service,
        limit=page_size,
        offset=offset
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    return AuditSearchResponse(
        logs=logs,
        total_count=total_count,
        page_size=page_size,
        current_page=page,
        total_pages=total_pages
    )


# Export endpoints
@router.post("/exports", response_model=ExportResponse)
async def create_audit_export(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create audit data export."""
    service = AuditExportService(db)
    
    # Check permissions for sensitive data
    if export_request.include_sensitive_data and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required for sensitive data export"
        )
    
    export = await service.create_export(
        export_criteria=export_request.export_criteria,
        format=export_request.format,
        requested_by=current_user.id,
        organization_id=current_user.organization_id,
        compliance_framework=export_request.compliance_framework,
        export_name=export_request.export_name
    )
    
    return export


@router.get("/exports", response_model=List[ExportResponse])
async def list_exports(
    status_filter: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List audit exports."""
    service = AuditExportService(db)
    
    filters = {"requested_by": current_user.id}
    if status_filter:
        filters["status"] = status_filter
    
    exports = await service.get_multi(
        skip=skip,
        limit=limit,
        filters=filters,
        organization_id=current_user.organization_id
    )
    
    return exports


@router.get("/exports/{export_id}", response_model=ExportResponse)
async def get_export_status(
    export_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get export status."""
    service = AuditExportService(db)
    
    export = await service.get_by_filters({"export_id": export_id})
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    # Check access permissions
    if (export.requested_by != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return export


# Compliance reporting endpoints
@router.post("/compliance/reports", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    report_request: ComplianceReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate compliance report."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required for compliance reports"
        )
    
    service = ComplianceReportService(db)
    
    report = await service.generate_report(
        compliance_framework=report_request.compliance_framework,
        period_start=report_request.period_start,
        period_end=report_request.period_end,
        generated_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    return report


@router.get("/compliance/reports", response_model=List[ComplianceReportResponse])
async def list_compliance_reports(
    framework: Optional[ComplianceFramework] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List compliance reports."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    service = ComplianceReportService(db)
    
    filters = {}
    if framework:
        filters["compliance_framework"] = framework
    
    reports = await service.get_multi(
        skip=skip,
        limit=limit,
        filters=filters,
        organization_id=current_user.organization_id
    )
    
    return reports


# Integrity verification endpoints
@router.post("/verify-integrity", response_model=IntegrityVerificationResponse)
async def verify_audit_integrity(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify audit log chain integrity."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    service = ComprehensiveAuditService(db)
    
    verification_result = await service.verify_chain_integrity(
        start_date=start_date,
        end_date=end_date,
        organization_id=current_user.organization_id
    )
    
    return IntegrityVerificationResponse(
        verification_timestamp=datetime.utcnow(),
        **verification_result
    )


# Security event logging endpoint
@router.post("/security-events")
async def log_security_event(
    event_name: str,
    event_description: str,
    threat_level: str = Query("medium", pattern=r'^(low|medium|high|critical)$'),
    indicators: Optional[List[str]] = None,
    remediation_taken: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log security-related audit events."""
    service = ComprehensiveAuditService(db)
    
    audit_log = await service.log_security_event(
        event_name=event_name,
        event_description=event_description,
        user_id=current_user.id,
        user_email=current_user.email,
        threat_level=threat_level,
        indicators=indicators,
        remediation_taken=remediation_taken,
        organization_id=current_user.organization_id,
        request=request
    )
    
    return {"message": "Security event logged", "audit_id": audit_log.audit_id}


# Statistics and dashboard endpoints
@router.get("/statistics")
async def get_audit_statistics(
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit statistics for dashboard."""
    service = ComprehensiveAuditService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get basic statistics
    total_logs, _ = await service.search_audit_logs(
        filters={},
        start_date=start_date,
        end_date=end_date,
        limit=1,
        organization_id=current_user.organization_id
    )
    
    # Get security events
    security_logs, _ = await service.search_audit_logs(
        filters={"event_type": AuditEventType.SECURITY_EVENT},
        start_date=start_date,
        end_date=end_date,
        limit=1,
        organization_id=current_user.organization_id
    )
    
    # Get failed events
    failed_logs, _ = await service.search_audit_logs(
        filters={"is_successful": False},
        start_date=start_date,
        end_date=end_date,
        limit=1,
        organization_id=current_user.organization_id
    )
    
    return {
        "period_days": period_days,
        "total_events": len(total_logs),
        "security_events": len(security_logs),
        "failed_events": len(failed_logs),
        "success_rate": ((len(total_logs) - len(failed_logs)) / max(len(total_logs), 1)) * 100,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat()
    }


@router.get("/health")
async def audit_health_check():
    """Check audit system health."""
    health_info = await check_audit_health()
    
    if health_info["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_info
        )
    
    return health_info