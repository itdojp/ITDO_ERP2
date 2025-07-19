"""Audit log API endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.schemas.audit import (
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
) -> AuditLogListResponse:
    """Get audit logs for an organization."""
    # Create filter params
    filter_params = AuditLogFilter(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        date_from=date_from,
        date_to=date_to,
    )

    service = AuditService()
    try:
        return service.get_organization_audit_logs(
            organization_id=organization_id,
            requester=current_user,
            db=db,
            limit=limit,
            offset=offset
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
) -> AuditLogListResponse:
    """Advanced search for audit logs."""
    # Ensure organization ID matches
    search_params.organization_id = organization_id

    service = AuditService()
    try:
        return service.search_audit_logs(search_params, current_user, db)
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )


@router.get("/organizations/{organization_id}/logs/stats", response_model=AuditLogStats)
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
            db=db,
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )


@router.get("/organizations/{organization_id}/logs/export")
def export_audit_logs(
    organization_id: int,
    date_from: datetime = Query(..., description="Export start date"),
    date_to: datetime = Query(..., description="Export end date"),
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

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
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
            detail="監査ログの整合性を確認する権限がありません",
        )


@router.get("/organizations/{organization_id}/logs/recent")
def get_recent_activity(
    organization_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(50, ge=1, le=500, description="Number of results"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
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
        return service.search_audit_logs(search_params, current_user, db)
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="組織の監査ログにアクセスする権限がありません",
        )
