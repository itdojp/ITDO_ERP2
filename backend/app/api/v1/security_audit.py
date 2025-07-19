"""Security audit API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.security_audit import RiskLevel, SecurityEventType
from app.schemas.security_audit import (
    SecurityAnalytics,
    SecurityAuditLogCreate,
    SecurityAuditLogResponse,
    SecurityAuditLogUpdate,
    SecurityEventFilter,
    SecurityReport,
)
from app.services.security_audit_service import SecurityAuditService

router = APIRouter(prefix="/security-audit", tags=["Security Audit"])


@router.post("/events", response_model=SecurityAuditLogResponse)
async def log_security_event(
    event_data: SecurityAuditLogCreate,
    db: AsyncSession = Depends(get_db),
) -> SecurityAuditLogResponse:
    """Log a security event."""
    service = SecurityAuditService(db)
    return await service.log_security_event(event_data)


@router.get("/events", response_model=List[SecurityAuditLogResponse])
async def get_security_events(
    event_types: Optional[List[SecurityEventType]] = Query(None),
    risk_levels: Optional[List[RiskLevel]] = Query(None),
    user_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    ip_address: Optional[str] = Query(None),
    requires_attention: Optional[bool] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> List[SecurityAuditLogResponse]:
    """Get security events with filtering options."""
    filters = SecurityEventFilter(
        event_types=event_types,
        risk_levels=risk_levels,
        user_id=user_id,
        organization_id=organization_id,
        ip_address=ip_address,
        requires_attention=requires_attention,
        is_resolved=is_resolved,
    )

    service = SecurityAuditService(db)
    return await service.get_security_events(filters, skip, limit)


@router.get("/events/{event_id}", response_model=SecurityAuditLogResponse)
async def get_security_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> SecurityAuditLogResponse:
    """Get a specific security event by ID."""
    filters = SecurityEventFilter()
    service = SecurityAuditService(db)
    events = await service.get_security_events(filters, skip=0, limit=1)

    # Find the specific event (this is a simplified approach)
    # In production, you might want a dedicated get_event_by_id method
    for event in events:
        if event.id == event_id:
            return event

    raise HTTPException(status_code=404, detail="Security event not found")


@router.patch("/events/{event_id}/resolve", response_model=SecurityAuditLogResponse)
async def resolve_security_event(
    event_id: int,
    resolution_data: SecurityAuditLogUpdate,
    resolved_by: int,  # In a real app, this would come from authentication
    db: AsyncSession = Depends(get_db),
) -> SecurityAuditLogResponse:
    """Resolve a security event."""
    service = SecurityAuditService(db)
    result = await service.resolve_security_event(event_id, resolution_data, resolved_by)

    if not result:
        raise HTTPException(status_code=404, detail="Security event not found")

    return result


@router.get("/analytics", response_model=SecurityAnalytics)
async def get_security_analytics(
    organization_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> SecurityAnalytics:
    """Get security analytics for the specified period."""
    service = SecurityAuditService(db)
    return await service.get_security_analytics(organization_id, days)


@router.get("/report", response_model=SecurityReport)
async def get_security_report(
    organization_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> SecurityReport:
    """Generate comprehensive security report."""
    service = SecurityAuditService(db)
    return await service.create_security_report(organization_id, days)


@router.get("/events/unresolved", response_model=List[SecurityAuditLogResponse])
async def get_unresolved_events(
    organization_id: Optional[int] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> List[SecurityAuditLogResponse]:
    """Get unresolved security events."""
    filters = SecurityEventFilter(
        organization_id=organization_id,
        risk_levels=[risk_level] if risk_level else None,
        is_resolved=False,
    )

    service = SecurityAuditService(db)
    return await service.get_security_events(filters, skip, limit)


@router.get("/events/high-risk", response_model=List[SecurityAuditLogResponse])
async def get_high_risk_events(
    organization_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> List[SecurityAuditLogResponse]:
    """Get high-risk security events."""
    filters = SecurityEventFilter(
        organization_id=organization_id,
        risk_levels=[RiskLevel.HIGH, RiskLevel.CRITICAL],
    )

    service = SecurityAuditService(db)
    return await service.get_security_events(filters, skip, limit)
