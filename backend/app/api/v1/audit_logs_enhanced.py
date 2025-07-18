"""
Enhanced Audit Logs API endpoints for Issue #46 - Security Audit Log and Monitoring Features.
拡張監査ログAPIエンドポイント（Issue #46 - セキュリティ監査ログとモニタリング機能）
"""

import io
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.security_monitoring import (
    AuditLogExport,
    AuditLogFilter,
    AuditLogListResponse,
    AuditLogResponse,
)

router = APIRouter()


@router.get("/", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get paginated audit logs with filtering.
    フィルタリング付きページネーション監査ログ取得
    """
    # Check permissions
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        # Non-admin users can only see their own logs
        if user_id and user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Can only view own audit logs."
            )
        user_id = current_user.id

    # Build query
    query = select(AuditLog).order_by(desc(AuditLog.created_at))

    # Apply filters
    conditions = []
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    if organization_id:
        conditions.append(AuditLog.organization_id == organization_id)
    elif not current_user.is_superuser:
        # Non-superusers see only their organization's logs
        conditions.append(AuditLog.organization_id == current_user.organization_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count(AuditLog.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    audit_logs = result.scalars().all()

    # Convert to response format
    items = []
    for log in audit_logs:
        # Verify integrity
        integrity_verified = log.verify_integrity()
        
        items.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=log.user.email if log.user else "Unknown",
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            organization_id=log.organization_id,
            changes=log.changes,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at.isoformat(),
            integrity_verified=integrity_verified
        ))

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=total > page * limit,
        has_prev=page > 1
    )


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log_detail(
    audit_log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed audit log information.
    詳細監査ログ情報取得
    """
    # Get audit log
    query = select(AuditLog).where(AuditLog.id == audit_log_id)
    result = await db.execute(query)
    audit_log = result.scalar_one_or_none()

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )

    # Check permissions
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        if audit_log.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Can only view own audit logs."
            )

    # Verify integrity
    integrity_verified = audit_log.verify_integrity()

    return AuditLogResponse(
        id=audit_log.id,
        user_id=audit_log.user_id,
        username=audit_log.user.email if audit_log.user else "Unknown",
        action=audit_log.action,
        resource_type=audit_log.resource_type,
        resource_id=audit_log.resource_id,
        organization_id=audit_log.organization_id,
        changes=audit_log.changes,
        ip_address=audit_log.ip_address,
        user_agent=audit_log.user_agent,
        created_at=audit_log.created_at.isoformat(),
        integrity_verified=integrity_verified
    )


@router.get("/export/csv")
async def export_audit_logs_csv(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    include_user_details: bool = Query(True, description="Include user information"),
    include_changes: bool = Query(True, description="Include change details"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export audit logs to CSV format.
    監査ログのCSVエクスポート
    """
    # Check permissions
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required for export."
        )

    # Build query
    query = select(AuditLog).order_by(desc(AuditLog.created_at))

    # Apply filters
    conditions = []
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    if organization_id:
        conditions.append(AuditLog.organization_id == organization_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Execute query
    result = await db.execute(query)
    audit_logs = result.scalars().all()

    # Generate CSV content
    csv_content = _generate_csv_content(
        audit_logs, include_user_details, include_changes
    )

    # Return as streaming response
    def generate():
        yield csv_content

    filename = f"audit_logs_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/json")
async def export_audit_logs_json(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    include_user_details: bool = Query(True, description="Include user information"),
    include_changes: bool = Query(True, description="Include change details"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export audit logs to JSON format.
    監査ログのJSONエクスポート
    """
    # Check permissions
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required for export."
        )

    # Build query (same as CSV export)
    query = select(AuditLog).order_by(desc(AuditLog.created_at))

    # Apply filters
    conditions = []
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    if organization_id:
        conditions.append(AuditLog.organization_id == organization_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Execute query
    result = await db.execute(query)
    audit_logs = result.scalars().all()

    # Convert to JSON format
    export_data = {
        "export_info": {
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": current_user.email,
            "total_records": len(audit_logs),
            "filters_applied": {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "organization_id": organization_id
            }
        },
        "audit_logs": []
    }

    for log in audit_logs:
        log_data = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "organization_id": log.organization_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
            "integrity_verified": log.verify_integrity()
        }

        if include_user_details and log.user:
            log_data["user_details"] = {
                "email": log.user.email,
                "full_name": log.user.full_name
            }

        if include_changes:
            log_data["changes"] = log.changes

        if include_user_details:
            log_data["user_agent"] = log.user_agent

        export_data["audit_logs"].append(log_data)

    return export_data


@router.get("/statistics/summary")
async def get_audit_statistics(
    days_back: int = Query(30, ge=1, le=365, description="Days to analyze"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get audit log statistics and summary.
    監査ログ統計とサマリー取得
    """
    if not (current_user.is_superuser or "security_officer" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Security officer privileges required."
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

    # Base query conditions
    conditions = [AuditLog.created_at >= start_date]
    if organization_id:
        conditions.append(AuditLog.organization_id == organization_id)

    # Total logs count
    total_query = select(func.count(AuditLog.id)).where(and_(*conditions))
    total_result = await db.execute(total_query)
    total_logs = total_result.scalar()

    # Logs by action
    action_query = (
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .where(and_(*conditions))
        .group_by(AuditLog.action)
        .order_by(desc("count"))
    )
    action_result = await db.execute(action_query)
    actions_stats = [{"action": row.action, "count": row.count} for row in action_result]

    # Logs by resource type
    resource_query = (
        select(AuditLog.resource_type, func.count(AuditLog.id).label("count"))
        .where(and_(*conditions))
        .group_by(AuditLog.resource_type)
        .order_by(desc("count"))
    )
    resource_result = await db.execute(resource_query)
    resources_stats = [{"resource_type": row.resource_type, "count": row.count} for row in resource_result]

    # Most active users
    user_query = (
        select(AuditLog.user_id, func.count(AuditLog.id).label("count"))
        .where(and_(*conditions))
        .group_by(AuditLog.user_id)
        .order_by(desc("count"))
        .limit(10)
    )
    user_result = await db.execute(user_query)
    active_users = []
    
    for row in user_result:
        # Get user details
        user_detail_query = select(User).where(User.id == row.user_id)
        user_detail_result = await db.execute(user_detail_query)
        user = user_detail_result.scalar_one_or_none()
        
        active_users.append({
            "user_id": row.user_id,
            "username": user.email if user else "Unknown",
            "activity_count": row.count
        })

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days_back
        },
        "summary": {
            "total_logs": total_logs,
            "daily_average": round(total_logs / days_back, 2) if days_back > 0 else 0,
            "organization_id": organization_id
        },
        "breakdown": {
            "by_action": actions_stats,
            "by_resource_type": resources_stats,
            "most_active_users": active_users
        }
    }


def _generate_csv_content(
    audit_logs: List[AuditLog], 
    include_user_details: bool, 
    include_changes: bool
) -> str:
    """Generate CSV content from audit logs."""
    import csv
    
    output = io.StringIO()
    
    # Define headers
    headers = [
        "id", "user_id", "action", "resource_type", "resource_id", 
        "organization_id", "ip_address", "created_at", "integrity_verified"
    ]
    
    if include_user_details:
        headers.extend(["username", "user_agent"])
    
    if include_changes:
        headers.append("changes")
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    # Write data
    for log in audit_logs:
        row = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "organization_id": log.organization_id,
            "ip_address": log.ip_address or "",
            "created_at": log.created_at.isoformat(),
            "integrity_verified": log.verify_integrity()
        }
        
        if include_user_details:
            row["username"] = log.user.email if log.user else "Unknown"
            row["user_agent"] = log.user_agent or ""
        
        if include_changes:
            row["changes"] = json.dumps(log.changes) if log.changes else ""
        
        writer.writerow(row)
    
    return output.getvalue()