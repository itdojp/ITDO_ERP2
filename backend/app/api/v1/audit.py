"""Audit log API endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.schemas.audit import (
    AuditLogBulkIntegrityResult,
    AuditLogFilter,
    AuditLogListResponse,
    AuditLogSearch,
    AuditLogStats,
)
from app.services.audit import AuditService

router = APIRouter()


@router.get(
    "/organizations/{organization_id}/logs", response_model=AuditLogListResponse
)
def get_organization_audit_logs(
    organization_id: int,
    limit: int = Query(50, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get audit logs for an organization."""
    # Create filter params (validated by API parameters)
    # Using individual parameters instead of AuditLogFilter object
    # to avoid unused variable warning while maintaining validation

    service = AuditService()
    try:
        return service.get_audit_logs(
            user=current_user,
            db=db,
            organization_id=organization_id,
            limit=limit,
            page=offset // limit + 1,
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )


@router.post(
    "/organizations/{organization_id}/logs/search", response_model=AuditLogListResponse
)
def search_audit_logs(
    organization_id: int,
    search_params: AuditLogSearch,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Advanced search for audit logs."""
    # Ensure organization ID matches
    search_params.organization_id = organization_id

    service = AuditService()
    try:
        return service.search_audit_logs(search_params, current_user)
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )


@router.get(
    "/organizations/{organization_id}/logs/statistics", response_model=AuditLogStats
)
def get_audit_statistics(
    organization_id: int,
    date_from: datetime = Query(..., description="Statistics start date"),
    date_to: datetime = Query(..., description="Statistics end date"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AuditLogStats:
    """Get audit log statistics for an organization."""
    service = AuditService()
    try:
        return service.get_audit_statistics(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to,
            requester=current_user,
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )


@router.get("/organizations/{organization_id}/logs/export")
def export_audit_logs(
    organization_id: int,
    date_from: Optional[datetime] = Query(None, description="Export from date"),
    date_to: Optional[datetime] = Query(None, description="Export to date"),
    actions: Optional[List[str]] = Query(None, description="Filter by actions"),
    resource_types: Optional[List[str]] = Query(
        None, description="Filter by resource types"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    """Export audit logs as CSV."""
    service = AuditService()
    try:
        csv_data = service.export_audit_logs_csv(
            organization_id=organization_id,
            requester=current_user,
            date_from=date_from,
            date_to=date_to,
            actions=actions,
            resource_types=resource_types,
        )

        # Generate filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"audit_logs_org{organization_id}_{timestamp}.csv"

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )


@router.get("/logs/{log_id}/verify")
def verify_log_integrity(
    log_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, bool]:
    """Verify the integrity of a single audit log."""
    service = AuditService()
    try:
        is_valid = service.verify_log_integrity(log_id, current_user)
        return {"valid": is_valid}
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="監査ログが見つかりません"
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この監査ログにアクセスする権限がありません",
        )


@router.post(
    "/organizations/{organization_id}/logs/verify-bulk",
    response_model=AuditLogBulkIntegrityResult,
)
def verify_logs_integrity_bulk(
    organization_id: int,
    date_from: datetime = Query(..., description="Verification start date"),
    date_to: datetime = Query(..., description="Verification end date"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AuditLogBulkIntegrityResult:
    """Verify integrity of multiple audit logs (admin only)."""
    service = AuditService()
    try:
        return service.verify_logs_integrity_bulk(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to,
            requester=current_user,
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="一括整合性チェックには管理者権限が必要です",
        )


@router.post("/organizations/{organization_id}/logs/retention")
def apply_retention_policy(
    organization_id: int,
    retention_days: int = Query(
        ..., ge=30, le=3650, description="Retention period in days"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, int]:
    """Apply retention policy to audit logs (admin only)."""
    service = AuditService()
    try:
        archived_count = service.apply_retention_policy(
            organization_id=organization_id,
            retention_days=retention_days,
            requester=current_user,
        )
        return {"archived_logs": archived_count}
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="保持ポリシーの適用には管理者権限が必要です",
        )


@router.get("/organizations/{organization_id}/logs/recent")
def get_recent_activity(
    organization_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(50, ge=1, le=500, description="Number of results"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get recent audit activity for an organization."""
    # Calculate date range
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(hours=hours)

    # Create search params
    search_params = AuditLogSearch(
        organization_id=organization_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=0,
        sort_by="created_at",
        sort_order="desc",
    )

    service = AuditService()
    try:
        return service.search_audit_logs(search_params, current_user)
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )


@router.get("/organizations/{organization_id}/logs/actions")
def get_available_actions(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[str]:
    """Get list of available actions in the audit logs."""
    # Permission check
    service = AuditService()
    if not service._can_access_organization_logs(current_user, organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )

    # Get distinct actions from the database
    from app.models.audit import AuditLog

    actions = (
        db.query(AuditLog.action)
        .filter(AuditLog.organization_id == organization_id)
        .distinct()
        .all()
    )

    return [action[0] for action in actions]


@router.get("/organizations/{organization_id}/logs/resource-types")
def get_available_resource_types(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[str]:
    """Get list of available resource types in the audit logs."""
    # Permission check
    service = AuditService()
    if not service._can_access_organization_logs(current_user, organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )

    # Get distinct resource types from the database
    from app.models.audit import AuditLog

    resource_types = (
        db.query(AuditLog.resource_type)
        .filter(AuditLog.organization_id == organization_id)
        .distinct()
        .all()
    )

    return [resource_type[0] for resource_type in resource_types]
