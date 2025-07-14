"""Audit log API endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_current_superuser, get_db
from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.schemas.audit_log_extended import (
    AuditLogAlert,
    AuditLogAlertCreate,
    AuditLogDetail,
    AuditLogExport,
    AuditLogFilter,
    AuditLogRetentionPolicy,
    AuditLogSummary,
    AuditTrailReport,
)
from app.schemas.error import ErrorResponse
from app.services.audit_log import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=List[AuditLogDetail],
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def list_audit_logs(
    filter: AuditLogFilter = Depends(),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[AuditLogDetail]:
    """List audit logs with filtering."""
    service = AuditLogService(db)
    
    # Check permission
    if not current_user.is_superuser:
        # Regular users can only view their own logs
        if filter.user_id and filter.user_id != current_user.id:
            raise PermissionDenied("Cannot view other users' audit logs")
        filter.user_id = current_user.id
    
    return service.list_audit_logs(filter, limit, offset)


@router.get(
    "/summary",
    response_model=AuditLogSummary,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def get_audit_log_summary(
    filter: AuditLogFilter = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> AuditLogSummary:
    """Get audit log summary statistics (admin only)."""
    service = AuditLogService(db)
    return service.get_audit_log_summary(filter)


@router.post(
    "/export",
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def export_audit_logs(
    export_request: AuditLogExport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> StreamingResponse:
    """Export audit logs in various formats (admin only)."""
    service = AuditLogService(db)
    
    # Generate export
    file_content, filename, content_type = service.export_audit_logs(
        export_request.filter,
        export_request.format,
        export_request.include_fields,
        export_request.exclude_fields,
        export_request.timezone,
    )
    
    return StreamingResponse(
        file_content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/retention-policies",
    response_model=List[AuditLogRetentionPolicy],
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def list_retention_policies(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> List[AuditLogRetentionPolicy]:
    """List audit log retention policies (admin only)."""
    service = AuditLogService(db)
    return service.list_retention_policies(is_active)


@router.post(
    "/retention-policies",
    response_model=AuditLogRetentionPolicy,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def create_retention_policy(
    policy: AuditLogRetentionPolicy,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> AuditLogRetentionPolicy:
    """Create audit log retention policy (admin only)."""
    service = AuditLogService(db)
    return service.create_retention_policy(policy, created_by=current_user.id)


@router.get(
    "/alerts",
    response_model=List[AuditLogAlert],
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def list_audit_alerts(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> List[AuditLogAlert]:
    """List audit log alerts (admin only)."""
    service = AuditLogService(db)
    return service.list_audit_alerts(is_active)


@router.post(
    "/alerts",
    response_model=AuditLogAlert,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def create_audit_alert(
    alert: AuditLogAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> AuditLogAlert:
    """Create audit log alert (admin only)."""
    service = AuditLogService(db)
    return service.create_audit_alert(alert, created_by=current_user.id)


@router.put(
    "/alerts/{alert_id}",
    response_model=AuditLogAlert,
    responses={
        404: {"model": ErrorResponse, "description": "Alert not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def update_audit_alert(
    alert_id: int,
    alert: AuditLogAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> AuditLogAlert:
    """Update audit log alert (admin only)."""
    service = AuditLogService(db)
    try:
        return service.update_audit_alert(alert_id, alert, updated_by=current_user.id)
    except ValueError as e:
        raise NotFound(str(e))


@router.delete(
    "/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Alert not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def delete_audit_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> None:
    """Delete audit log alert (admin only)."""
    service = AuditLogService(db)
    try:
        service.delete_audit_alert(alert_id)
    except ValueError as e:
        raise NotFound(str(e))


@router.get(
    "/trail-report",
    response_model=AuditTrailReport,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def generate_audit_trail_report(
    period_start: datetime = Query(..., description="Report period start"),
    period_end: datetime = Query(..., description="Report period end"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> AuditTrailReport:
    """Generate comprehensive audit trail report (admin only)."""
    service = AuditLogService(db)
    
    # Validate date range
    if period_end <= period_start:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )
    
    if period_end - period_start > timedelta(days=90):
        raise HTTPException(
            status_code=400,
            detail="Report period cannot exceed 90 days"
        )
    
    return service.generate_audit_trail_report(
        period_start,
        period_end,
        generated_by=current_user.id
    )


@router.post(
    "/cleanup",
    response_model=dict,
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def cleanup_audit_logs(
    apply_retention_policies: bool = True,
    archive_before_delete: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> dict:
    """Clean up audit logs based on retention policies (admin only)."""
    service = AuditLogService(db)
    
    deleted_count, archived_count = service.cleanup_audit_logs(
        apply_retention_policies,
        archive_before_delete,
        performed_by=current_user.id
    )
    
    return {
        "message": "Audit log cleanup completed",
        "deleted_count": deleted_count,
        "archived_count": archived_count,
    }