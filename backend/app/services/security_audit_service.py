"""Security audit service for enhanced monitoring."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_audit import (
    RiskLevel,
    SecurityAlert,
    SecurityAuditLog,
    SecurityEventType,
)
from app.schemas.security_audit import (
    SecurityAlertCreate,
    SecurityAlertResponse,
    SecurityAnalytics,
    SecurityAuditLogCreate,
    SecurityAuditLogResponse,
    SecurityAuditLogUpdate,
    SecurityEventFilter,
    SecurityReport,
)

logger = logging.getLogger(__name__)


class SecurityAuditService:
    """Service for managing security audit logs and monitoring."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_security_event(
        self, event_data: SecurityAuditLogCreate
    ) -> SecurityAuditLogResponse:
        """Log a security event."""
        try:
            # Determine risk level based on event type
            risk_level = self._determine_risk_level(event_data.event_type)
            
            security_log = SecurityAuditLog(
                user_id=event_data.user_id,
                event_type=event_data.event_type,
                risk_level=risk_level,
                resource_type=event_data.resource_type,
                resource_id=event_data.resource_id,
                organization_id=event_data.organization_id,
                ip_address=event_data.ip_address,
                user_agent=event_data.user_agent,
                session_id=event_data.session_id,
                description=event_data.description,
                details=event_data.details,
                detection_method=event_data.detection_method,
                is_automated_detection=event_data.is_automated_detection,
                requires_attention=self._requires_attention(event_data.event_type, risk_level),
            )

            self.db.add(security_log)
            await self.db.commit()
            await self.db.refresh(security_log)

            # Check for suspicious patterns
            await self._analyze_for_suspicious_patterns(security_log)

            # Create alert if necessary
            if security_log.requires_attention or risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                await self._create_security_alert(security_log)

            return SecurityAuditLogResponse.model_validate(security_log)

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            await self.db.rollback()
            raise

    async def get_security_events(
        self,
        filters: SecurityEventFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SecurityAuditLogResponse]:
        """Get security events with filtering."""
        query = select(SecurityAuditLog)

        # Apply filters
        conditions: List[Union[BinaryExpression[bool], ColumnElement[bool]]] = []
        
        if filters.event_types:
            conditions.append(SecurityAuditLog.event_type.in_(filters.event_types))
        
        if filters.risk_levels:
            conditions.append(SecurityAuditLog.risk_level.in_(filters.risk_levels))
        
        if filters.user_id:
            conditions.append(SecurityAuditLog.user_id == filters.user_id)
        
        if filters.organization_id:
            conditions.append(SecurityAuditLog.organization_id == filters.organization_id)
        
        if filters.ip_address:
            conditions.append(SecurityAuditLog.ip_address == filters.ip_address)
        
        if filters.requires_attention is not None:
            conditions.append(SecurityAuditLog.requires_attention == filters.requires_attention)
        
        if filters.is_resolved is not None:
            conditions.append(SecurityAuditLog.is_resolved == filters.is_resolved)
        
        if filters.start_date:
            conditions.append(SecurityAuditLog.created_at >= filters.start_date)
        
        if filters.end_date:
            conditions.append(SecurityAuditLog.created_at <= filters.end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(SecurityAuditLog.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        events = result.scalars().all()

        return [SecurityAuditLogResponse.model_validate(event) for event in events]

    async def resolve_security_event(
        self, event_id: int, resolution_data: SecurityAuditLogUpdate, resolved_by: int
    ) -> Optional[SecurityAuditLogResponse]:
        """Resolve a security event."""
        query = select(SecurityAuditLog).where(SecurityAuditLog.id == event_id)
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            return None

        event.is_resolved = resolution_data.is_resolved or True
        event.resolved_by = resolved_by
        event.resolved_at = datetime.utcnow()
        event.resolution_notes = resolution_data.resolution_notes
        event.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(event)

        return SecurityAuditLogResponse.model_validate(event)

    async def get_security_analytics(
        self, organization_id: Optional[int] = None, days: int = 30
    ) -> SecurityAnalytics:
        """Get security analytics for the specified period."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query
        base_query = select(SecurityAuditLog).where(
            SecurityAuditLog.created_at >= start_date
        )
        
        if organization_id:
            base_query = base_query.where(
                SecurityAuditLog.organization_id == organization_id
            )

        # Total events
        total_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_events = total_result.scalar() or 0

        # Events by type
        type_query = (
            base_query.group_by(SecurityAuditLog.event_type)
            .with_only_columns(
                SecurityAuditLog.event_type,
                func.count(SecurityAuditLog.id).label("count")
            )
        )
        type_result = await self.db.execute(type_query)
        events_by_type: Dict[str, int] = {}
        for row in type_result:
            events_by_type[str(row[0])] = row[1]

        # Events by risk level
        risk_query = (
            base_query.group_by(SecurityAuditLog.risk_level)
            .with_only_columns(
                SecurityAuditLog.risk_level,
                func.count(SecurityAuditLog.id).label("count")
            )
        )
        risk_result = await self.db.execute(risk_query)
        events_by_risk_level: Dict[str, int] = {}
        for risk_row in risk_result:
            events_by_risk_level[str(risk_row[0])] = risk_row[1]

        # Unresolved high risk events
        high_risk_query = select(func.count()).where(
            and_(
                SecurityAuditLog.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
                SecurityAuditLog.is_resolved == False,  # noqa: E712
                SecurityAuditLog.created_at >= start_date,
            )
        )
        if organization_id:
            high_risk_query = high_risk_query.where(
                SecurityAuditLog.organization_id == organization_id
            )
        
        high_risk_result = await self.db.execute(high_risk_query)
        unresolved_high_risk_count = high_risk_result.scalar() or 0

        # Failed login attempts
        failed_login_query = select(func.count()).where(
            and_(
                SecurityAuditLog.event_type == SecurityEventType.LOGIN_FAILURE,
                SecurityAuditLog.created_at >= start_date,
            )
        )
        if organization_id:
            failed_login_query = failed_login_query.where(
                SecurityAuditLog.organization_id == organization_id
            )
        
        failed_login_result = await self.db.execute(failed_login_query)
        failed_login_attempts = failed_login_result.scalar() or 0

        # Suspicious activities
        suspicious_query = select(func.count()).where(
            and_(
                SecurityAuditLog.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY,
                SecurityAuditLog.created_at >= start_date,
            )
        )
        if organization_id:
            suspicious_query = suspicious_query.where(
                SecurityAuditLog.organization_id == organization_id
            )
        
        suspicious_result = await self.db.execute(suspicious_query)
        suspicious_activities = suspicious_result.scalar() or 0

        # Recent privilege escalations
        escalation_query = (
            base_query.where(
                SecurityAuditLog.event_type == SecurityEventType.PRIVILEGE_ESCALATION
            )
            .order_by(desc(SecurityAuditLog.created_at))
            .limit(10)
        )
        escalation_result = await self.db.execute(escalation_query)
        escalations = escalation_result.scalars().all()
        recent_privilege_escalations = [
            SecurityAuditLogResponse.model_validate(event) for event in escalations
        ]

        return SecurityAnalytics(
            total_events=total_events,
            events_by_type=events_by_type,
            events_by_risk_level=events_by_risk_level,
            unresolved_high_risk_count=unresolved_high_risk_count,
            top_users_by_activity=[],  # TODO: Implement user activity ranking
            top_ip_addresses=[],  # TODO: Implement IP address ranking
            failed_login_attempts=failed_login_attempts,
            suspicious_activities=suspicious_activities,
            recent_privilege_escalations=recent_privilege_escalations,
            security_trend={},  # TODO: Implement trend analysis
        )

    async def create_security_report(
        self, organization_id: Optional[int] = None, days: int = 30
    ) -> SecurityReport:
        """Generate comprehensive security report."""
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        analytics = await self.get_security_analytics(organization_id, days)
        
        # Get critical events
        critical_filter = SecurityEventFilter(
            risk_levels=[RiskLevel.CRITICAL],
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id,
        )
        critical_events = await self.get_security_events(critical_filter, limit=50)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analytics)
        
        return SecurityReport(
            period=f"{days} days",
            start_date=start_date,
            end_date=end_date,
            summary=analytics,
            critical_events=critical_events,
            recommendations=recommendations,
            compliance_status={},  # TODO: Implement compliance checking
        )

    def _determine_risk_level(self, event_type: SecurityEventType) -> RiskLevel:
        """Determine risk level based on event type."""
        high_risk_events = {
            SecurityEventType.MULTIPLE_LOGIN_ATTEMPTS,
            SecurityEventType.PRIVILEGE_ESCALATION,
            SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
            SecurityEventType.SUSPICIOUS_ACTIVITY,
        }
        
        critical_events = {
            SecurityEventType.SENSITIVE_DATA_ACCESS,
            SecurityEventType.DATA_EXPORT,
        }
        
        if event_type in critical_events:
            return RiskLevel.CRITICAL
        elif event_type in high_risk_events:
            return RiskLevel.HIGH
        elif event_type in {SecurityEventType.LOGIN_FAILURE}:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _requires_attention(self, event_type: SecurityEventType, risk_level: RiskLevel) -> bool:
        """Determine if event requires immediate attention."""
        return risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] or event_type in {
            SecurityEventType.MULTIPLE_LOGIN_ATTEMPTS,
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            SecurityEventType.PRIVILEGE_ESCALATION,
            SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
        }

    async def _analyze_for_suspicious_patterns(self, security_log: SecurityAuditLog) -> None:
        """Analyze for suspicious patterns and create additional logs if needed."""
        if security_log.event_type == SecurityEventType.LOGIN_FAILURE:
            await self._check_multiple_login_failures(security_log)
        
        # TODO: Add more pattern analysis

    async def _check_multiple_login_failures(self, security_log: SecurityAuditLog) -> None:
        """Check for multiple login failures from same IP."""
        if not security_log.ip_address:
            return
        
        # Check failures in last 15 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
        
        failure_query = select(func.count()).where(
            and_(
                SecurityAuditLog.event_type == SecurityEventType.LOGIN_FAILURE,
                SecurityAuditLog.ip_address == security_log.ip_address,
                SecurityAuditLog.created_at >= cutoff_time,
            )
        )
        
        result = await self.db.execute(failure_query)
        failure_count = result.scalar() or 0
        
        if failure_count >= 5:  # Threshold for suspicious activity
            suspicious_log = SecurityAuditLog(
                event_type=SecurityEventType.MULTIPLE_LOGIN_ATTEMPTS,
                risk_level=RiskLevel.HIGH,
                description=f"Multiple login failures detected from IP {security_log.ip_address}",
                details={
                    "failure_count": failure_count,
                    "time_window": "15 minutes",
                    "source_ip": security_log.ip_address,
                },
                ip_address=security_log.ip_address,
                detection_method="automated_pattern_analysis",
                is_automated_detection=True,
                requires_attention=True,
            )
            
            self.db.add(suspicious_log)
            await self.db.commit()

    async def _create_security_alert(self, security_log: SecurityAuditLog) -> None:
        """Create security alert for high-priority events."""
        alert_data = SecurityAlertCreate(
            security_audit_log_id=security_log.id,
            alert_type=security_log.event_type.value,
            severity=security_log.risk_level,
            title=f"Security Event: {security_log.event_type.value.replace('_', ' ').title()}",
            message=security_log.description,
            recipients=["security@company.com"],  # TODO: Make configurable
        )
        
        alert = SecurityAlert(**alert_data.model_dump())
        self.db.add(alert)
        await self.db.commit()

    def _generate_recommendations(self, analytics: SecurityAnalytics) -> List[str]:
        """Generate security recommendations based on analytics."""
        recommendations = []
        
        if analytics.failed_login_attempts > 100:
            recommendations.append(
                "Consider implementing stronger password policies or account lockout mechanisms"
            )
        
        if analytics.unresolved_high_risk_count > 0:
            recommendations.append(
                f"There are {analytics.unresolved_high_risk_count} unresolved high-risk security events requiring attention"
            )
        
        if analytics.suspicious_activities > 5:
            recommendations.append(
                "Investigate recent suspicious activities and consider additional monitoring"
            )
        
        if not recommendations:
            recommendations.append("No immediate security concerns identified")
        
        return recommendations