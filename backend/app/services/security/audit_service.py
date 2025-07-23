"""Security audit service."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.security.audit_log import SecurityAuditLog
from app.schemas.security.audit_log import (
    SecurityAuditLogCreate,
    SecurityAuditLogFilter,
    SecurityMetrics,
)


class SecurityAuditService:
    """Service for managing security audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(self, event_data: SecurityAuditLogCreate) -> SecurityAuditLog:
        """Log a security event."""
        try:
            audit_log = SecurityAuditLog(**event_data.model_dump())
            self.db.add(audit_log)
            await self.db.commit()
            await self.db.refresh(audit_log)
            return audit_log
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Failed to log security event: {str(e)}")

    async def get_logs(
        self,
        filters: SecurityAuditLogFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[SecurityAuditLog]:
        """Get security audit logs with filters."""
        query = select(SecurityAuditLog)

        # Apply filters
        conditions = []
        if filters.event_type:
            conditions.append(SecurityAuditLog.event_type == filters.event_type)
        if filters.severity:
            conditions.append(SecurityAuditLog.severity == filters.severity)
        if filters.user_id:
            conditions.append(SecurityAuditLog.user_id == filters.user_id)
        if filters.start_date:
            conditions.append(SecurityAuditLog.created_at >= filters.start_date)
        if filters.end_date:
            conditions.append(SecurityAuditLog.created_at <= filters.end_date)
        if filters.result:
            conditions.append(SecurityAuditLog.result == filters.result)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(SecurityAuditLog.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SecurityMetrics:
        """Get security metrics summary."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # Base query with date filter
        base_query = select(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        )

        # Total events
        total_query = select(func.count()).select_from(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        )
        total_result = await self.db.execute(total_query)
        total_events = total_result.scalar() or 0

        # Events by type
        type_query = select(
            SecurityAuditLog.event_type,
            func.count().label('count')
        ).where(
            and_(
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        ).group_by(SecurityAuditLog.event_type)

        type_result = await self.db.execute(type_query)
        events_by_type = {row.event_type: row.count for row in type_result}

        # Events by severity
        severity_query = select(
            SecurityAuditLog.severity,
            func.count().label('count')
        ).where(
            and_(
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        ).group_by(SecurityAuditLog.severity)

        severity_result = await self.db.execute(severity_query)
        events_by_severity = {row.severity: row.count for row in severity_result}

        # Failed login attempts
        failed_login_query = select(func.count()).select_from(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.event_type == 'login_failure',
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        )
        failed_login_result = await self.db.execute(failed_login_query)
        failed_login_attempts = failed_login_result.scalar() or 0

        # Suspicious activities
        suspicious_query = select(func.count()).select_from(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.event_type == 'suspicious_activity',
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        )
        suspicious_result = await self.db.execute(suspicious_query)
        suspicious_activities = suspicious_result.scalar() or 0

        # Blocked requests
        blocked_query = select(func.count()).select_from(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.result == 'BLOCKED',
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        )
        blocked_result = await self.db.execute(blocked_query)
        blocked_requests = blocked_result.scalar() or 0

        # Unique users affected
        unique_users_query = select(
            func.count(func.distinct(SecurityAuditLog.user_id))
        ).where(
            and_(
                SecurityAuditLog.user_id.isnot(None),
                SecurityAuditLog.created_at >= start_date,
                SecurityAuditLog.created_at <= end_date
            )
        )
        unique_users_result = await self.db.execute(unique_users_query)
        unique_users_affected = unique_users_result.scalar() or 0

        return SecurityMetrics(
            total_events=total_events,
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            failed_login_attempts=failed_login_attempts,
            suspicious_activities=suspicious_activities,
            blocked_requests=blocked_requests,
            unique_users_affected=unique_users_affected,
            time_range={
                "start": start_date,
                "end": end_date
            }
        )

    async def detect_anomalies(self, user_id: UUID) -> Dict[str, Any]:
        """Detect security anomalies for a user."""
        # Check recent failed login attempts
        recent_failures_query = select(func.count()).select_from(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.user_id == user_id,
                SecurityAuditLog.event_type == 'login_failure',
                SecurityAuditLog.created_at >= datetime.utcnow() - timedelta(hours=1)
            )
        )
        recent_failures_result = await self.db.execute(recent_failures_query)
        recent_failures = recent_failures_result.scalar() or 0

        # Check for unusual activity patterns
        unusual_activity_query = select(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.user_id == user_id,
                SecurityAuditLog.severity.in_(['ERROR', 'CRITICAL']),
                SecurityAuditLog.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).limit(10)

        unusual_activity_result = await self.db.execute(unusual_activity_query)
        unusual_activities = unusual_activity_result.scalars().all()

        anomalies = {
            "high_failure_rate": recent_failures > 5,
            "recent_failures": recent_failures,
            "critical_events": len([a for a in unusual_activities if a.severity == 'CRITICAL']),
            "suspicious_patterns": len(unusual_activities) > 5,
            "requires_attention": recent_failures > 5 or len(unusual_activities) > 5
        }

        return anomalies
