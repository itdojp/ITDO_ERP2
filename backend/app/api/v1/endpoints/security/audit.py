"""Security audit API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.security.audit_log import (
    SecurityAuditLogCreate,
    SecurityAuditLogFilter,
    SecurityAuditLogResponse,
    SecurityEventType,
    SecurityMetrics,
    SecuritySeverity,
)
from app.services.security.audit_service import SecurityAuditService

router = APIRouter()


@router.post("/log", response_model=SecurityAuditLogResponse)
async def log_security_event(
    event_data: SecurityAuditLogCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> SecurityAuditLogResponse:
    """Log a security event (admin only)."""
    service = SecurityAuditService(db)
    audit_log = await service.log_event(event_data)
    return SecurityAuditLogResponse.model_validate(audit_log)


@router.get("/logs", response_model=List[SecurityAuditLogResponse])
async def get_security_logs(
    event_type: Optional[SecurityEventType] = None,
    severity: Optional[SecuritySeverity] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    result: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> List[SecurityAuditLogResponse]:
    """Get security audit logs with filters (admin only)."""
    filters = SecurityAuditLogFilter(
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        result=result,
    )

    service = SecurityAuditService(db)
    logs = await service.get_logs(filters, skip, limit)
    return [SecurityAuditLogResponse.model_validate(log) for log in logs]


@router.get("/metrics", response_model=SecurityMetrics)
async def get_security_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> SecurityMetrics:
    """Get security metrics summary (admin only)."""
    service = SecurityAuditService(db)
    metrics = await service.get_metrics(start_date, end_date)
    return metrics


@router.get("/anomalies/{user_id}")
async def detect_user_anomalies(
    user_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> dict:
    """Detect security anomalies for a user (admin only)."""
    service = SecurityAuditService(db)
    anomalies = await service.detect_anomalies(user_id)
    return anomalies


@router.get("/my-logs", response_model=List[SecurityAuditLogResponse])
async def get_my_security_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[SecurityAuditLogResponse]:
    """Get current user's security logs."""
    filters = SecurityAuditLogFilter(user_id=current_user.id)
    service = SecurityAuditService(db)
    logs = await service.get_logs(filters, skip, limit)
    return [SecurityAuditLogResponse.model_validate(log) for log in logs]
