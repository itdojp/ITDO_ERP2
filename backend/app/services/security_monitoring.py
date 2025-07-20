"""Security monitoring service for Issue #46."""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.audit import AuditLogger


class SecurityThreat:
    """Security threat detection and classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __init__(self, threat_type: str, severity: str, description: str, details: Dict[str, Any]):
        self.threat_type = threat_type
        self.severity = severity
        self.description = description
        self.details = details
        self.timestamp = datetime.now(timezone.utc)


class SecurityMonitoringService:
    """Advanced security monitoring and threat detection service."""

    def __init__(self, db: Session | AsyncSession):
        """Initialize security monitoring service."""
        self.db = db
        self.audit_logger = AuditLogger(db)
        
        # Threat detection thresholds
        self.FAILED_LOGIN_THRESHOLD = 5
        self.FAILED_LOGIN_TIME_WINDOW = timedelta(minutes=15)
        self.BULK_ACCESS_THRESHOLD = 100
        self.BULK_ACCESS_TIME_WINDOW = timedelta(minutes=5)
        self.PRIVILEGE_ESCALATION_MONITORING = True

    async def monitor_failed_logins(self, user_id: Optional[int] = None, ip_address: Optional[str] = None) -> List[SecurityThreat]:
        """Monitor failed login attempts."""
        threats = []
        current_time = datetime.now(timezone.utc)
        time_threshold = current_time - self.FAILED_LOGIN_TIME_WINDOW

        if isinstance(self.db, AsyncSession):
            # Async query
            query = select(func.count(AuditLog.id), AuditLog.user_id, AuditLog.ip_address).where(
                and_(
                    AuditLog.action == "login_failed",
                    AuditLog.created_at >= time_threshold,
                )
            ).group_by(AuditLog.user_id, AuditLog.ip_address)
            
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            if ip_address:
                query = query.where(AuditLog.ip_address == ip_address)
                
            result = await self.db.execute(query)
            failed_attempts = result.fetchall()
        else:
            # Sync query
            query = self.db.query(
                func.count(AuditLog.id), AuditLog.user_id, AuditLog.ip_address
            ).filter(
                and_(
                    AuditLog.action == "login_failed",
                    AuditLog.created_at >= time_threshold,
                )
            ).group_by(AuditLog.user_id, AuditLog.ip_address)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if ip_address:
                query = query.filter(AuditLog.ip_address == ip_address)
                
            failed_attempts = query.all()

        for count, failed_user_id, failed_ip in failed_attempts:
            if count >= self.FAILED_LOGIN_THRESHOLD:
                severity = SecurityThreat.HIGH if count >= self.FAILED_LOGIN_THRESHOLD * 2 else SecurityThreat.MEDIUM
                threats.append(SecurityThreat(
                    threat_type="brute_force_attack",
                    severity=severity,
                    description=f"Multiple failed login attempts detected",
                    details={
                        "user_id": failed_user_id,
                        "ip_address": failed_ip,
                        "failed_attempts": count,
                        "time_window": str(self.FAILED_LOGIN_TIME_WINDOW),
                    }
                ))

        return threats

    async def monitor_bulk_data_access(self, user_id: Optional[int] = None) -> List[SecurityThreat]:
        """Monitor bulk data access patterns."""
        threats = []
        current_time = datetime.now(timezone.utc)
        time_threshold = current_time - self.BULK_ACCESS_TIME_WINDOW

        if isinstance(self.db, AsyncSession):
            query = select(func.count(AuditLog.id), AuditLog.user_id).where(
                and_(
                    AuditLog.action.in_(["read", "export", "download"]),
                    AuditLog.created_at >= time_threshold,
                )
            ).group_by(AuditLog.user_id)
            
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
                
            result = await self.db.execute(query)
            access_counts = result.fetchall()
        else:
            query = self.db.query(
                func.count(AuditLog.id), AuditLog.user_id
            ).filter(
                and_(
                    AuditLog.action.in_(["read", "export", "download"]),
                    AuditLog.created_at >= time_threshold,
                )
            ).group_by(AuditLog.user_id)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
                
            access_counts = query.all()

        for count, access_user_id in access_counts:
            if count >= self.BULK_ACCESS_THRESHOLD:
                severity = SecurityThreat.CRITICAL if count >= self.BULK_ACCESS_THRESHOLD * 3 else SecurityThreat.HIGH
                threats.append(SecurityThreat(
                    threat_type="bulk_data_access",
                    severity=severity,
                    description=f"Suspicious bulk data access detected",
                    details={
                        "user_id": access_user_id,
                        "access_count": count,
                        "time_window": str(self.BULK_ACCESS_TIME_WINDOW),
                    }
                ))

        return threats

    async def monitor_privilege_escalation(self, user_id: Optional[int] = None) -> List[SecurityThreat]:
        """Monitor privilege escalation attempts."""
        threats = []
        current_time = datetime.now(timezone.utc)
        time_threshold = current_time - timedelta(hours=24)

        if isinstance(self.db, AsyncSession):
            query = select(AuditLog).where(
                and_(
                    AuditLog.action.in_(["permission_grant", "role_change", "admin_access"]),
                    AuditLog.created_at >= time_threshold,
                )
            )
            
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
                
            result = await self.db.execute(query)
            escalation_logs = result.scalars().all()
        else:
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.action.in_(["permission_grant", "role_change", "admin_access"]),
                    AuditLog.created_at >= time_threshold,
                )
            )
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
                
            escalation_logs = query.all()

        # Group by user to detect patterns
        user_escalations = defaultdict(list)
        for log in escalation_logs:
            user_escalations[log.user_id].append(log)

        for escalation_user_id, logs in user_escalations.items():
            if len(logs) >= 2:  # Multiple privilege changes in 24h
                threats.append(SecurityThreat(
                    threat_type="privilege_escalation",
                    severity=SecurityThreat.HIGH,
                    description=f"Multiple privilege escalations detected",
                    details={
                        "user_id": escalation_user_id,
                        "escalation_count": len(logs),
                        "actions": [log.action for log in logs],
                        "time_span": "24 hours",
                    }
                ))

        return threats

    async def monitor_unusual_access_patterns(self, user_id: Optional[int] = None) -> List[SecurityThreat]:
        """Monitor unusual access patterns."""
        threats = []
        current_time = datetime.now(timezone.utc)
        
        # Check for access from unusual locations (different IP ranges)
        time_threshold = current_time - timedelta(hours=1)

        if isinstance(self.db, AsyncSession):
            query = select(AuditLog.user_id, func.count(func.distinct(AuditLog.ip_address))).where(
                and_(
                    AuditLog.action == "login_success",
                    AuditLog.created_at >= time_threshold,
                )
            ).group_by(AuditLog.user_id)
            
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
                
            result = await self.db.execute(query)
            ip_counts = result.fetchall()
        else:
            query = self.db.query(
                AuditLog.user_id, func.count(func.distinct(AuditLog.ip_address))
            ).filter(
                and_(
                    AuditLog.action == "login_success",
                    AuditLog.created_at >= time_threshold,
                )
            ).group_by(AuditLog.user_id)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
                
            ip_counts = query.all()

        for pattern_user_id, distinct_ips in ip_counts:
            if distinct_ips >= 3:  # Login from 3+ different IPs in 1 hour
                threats.append(SecurityThreat(
                    threat_type="unusual_access_pattern",
                    severity=SecurityThreat.MEDIUM,
                    description=f"Multiple IP addresses used for login",
                    details={
                        "user_id": pattern_user_id,
                        "distinct_ips": distinct_ips,
                        "time_window": "1 hour",
                    }
                ))

        return threats

    async def get_security_dashboard(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive security dashboard data."""
        current_time = datetime.now(timezone.utc)
        
        # Recent threats
        threats = []
        threats.extend(await self.monitor_failed_logins())
        threats.extend(await self.monitor_bulk_data_access())
        threats.extend(await self.monitor_privilege_escalation())
        threats.extend(await self.monitor_unusual_access_patterns())
        
        # Security metrics
        day_ago = current_time - timedelta(days=1)
        week_ago = current_time - timedelta(days=7)
        
        if isinstance(self.db, AsyncSession):
            # Failed logins today
            failed_logins_query = select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.action == "login_failed",
                    AuditLog.created_at >= day_ago,
                )
            )
            if organization_id:
                failed_logins_query = failed_logins_query.where(AuditLog.organization_id == organization_id)
            
            failed_logins_result = await self.db.execute(failed_logins_query)
            failed_logins_today = failed_logins_result.scalar() or 0
            
            # Successful logins today
            success_logins_query = select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.action == "login_success",
                    AuditLog.created_at >= day_ago,
                )
            )
            if organization_id:
                success_logins_query = success_logins_query.where(AuditLog.organization_id == organization_id)
            
            success_logins_result = await self.db.execute(success_logins_query)
            successful_logins_today = success_logins_result.scalar() or 0
            
        else:
            # Sync queries
            failed_logins_query = self.db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.action == "login_failed",
                    AuditLog.created_at >= day_ago,
                )
            )
            if organization_id:
                failed_logins_query = failed_logins_query.filter(AuditLog.organization_id == organization_id)
            
            failed_logins_today = failed_logins_query.scalar() or 0
            
            success_logins_query = self.db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.action == "login_success",
                    AuditLog.created_at >= day_ago,
                )
            )
            if organization_id:
                success_logins_query = success_logins_query.filter(AuditLog.organization_id == organization_id)
            
            successful_logins_today = success_logins_query.scalar() or 0

        # Threat statistics
        threat_counts = defaultdict(int)
        for threat in threats:
            threat_counts[threat.severity] += 1

        return {
            "timestamp": current_time.isoformat(),
            "organization_id": organization_id,
            "threats": {
                "total": len(threats),
                "critical": threat_counts[SecurityThreat.CRITICAL],
                "high": threat_counts[SecurityThreat.HIGH],
                "medium": threat_counts[SecurityThreat.MEDIUM],
                "low": threat_counts[SecurityThreat.LOW],
                "recent_threats": [
                    {
                        "type": threat.threat_type,
                        "severity": threat.severity,
                        "description": threat.description,
                        "details": threat.details,
                        "timestamp": threat.timestamp.isoformat(),
                    }
                    for threat in threats[:10]  # Latest 10 threats
                ],
            },
            "metrics": {
                "failed_logins_today": failed_logins_today,
                "successful_logins_today": successful_logins_today,
                "login_success_rate": (
                    (successful_logins_today / (successful_logins_today + failed_logins_today) * 100)
                    if (successful_logins_today + failed_logins_today) > 0
                    else 100
                ),
            },
            "monitoring_status": {
                "failed_login_monitoring": True,
                "bulk_access_monitoring": True,
                "privilege_escalation_monitoring": self.PRIVILEGE_ESCALATION_MONITORING,
                "unusual_pattern_monitoring": True,
            },
        }

    async def generate_security_report(
        self, 
        organization_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # Get audit logs for the period
        if isinstance(self.db, AsyncSession):
            query = select(AuditLog).where(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date,
                )
            )
            if organization_id:
                query = query.where(AuditLog.organization_id == organization_id)
            
            result = await self.db.execute(query)
            logs = result.scalars().all()
        else:
            query = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date,
                )
            )
            if organization_id:
                query = query.filter(AuditLog.organization_id == organization_id)
            
            logs = query.all()

        # Analyze logs
        action_counts = defaultdict(int)
        user_activity = defaultdict(int)
        ip_activity = defaultdict(int)
        resource_access = defaultdict(int)
        
        for log in logs:
            action_counts[log.action] += 1
            user_activity[log.user_id] += 1
            if log.ip_address:
                ip_activity[log.ip_address] += 1
            resource_access[log.resource_type] += 1

        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_events": len(logs),
                "unique_users": len(user_activity),
                "unique_ips": len(ip_activity),
                "action_types": len(action_counts),
            },
            "top_activities": {
                "actions": dict(sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "users": dict(sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]),
                "ip_addresses": dict(sorted(ip_activity.items(), key=lambda x: x[1], reverse=True)[:10]),
                "resources": dict(sorted(resource_access.items(), key=lambda x: x[1], reverse=True)[:10]),
            },
            "security_insights": {
                "failed_login_attempts": action_counts.get("login_failed", 0),
                "successful_logins": action_counts.get("login_success", 0),
                "privilege_changes": action_counts.get("permission_grant", 0) + action_counts.get("role_change", 0),
                "data_exports": action_counts.get("export", 0) + action_counts.get("download", 0),
            },
        }

    async def log_security_event(
        self,
        threat: SecurityThreat,
        user: User,
        organization_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log a security event for audit trail."""
        if isinstance(self.db, Session):
            self.audit_logger.log(
                action="security_threat_detected",
                resource_type="security_monitoring",
                resource_id=0,  # No specific resource
                user=user,
                changes={
                    "threat_type": threat.threat_type,
                    "severity": threat.severity,
                    "description": threat.description,
                    "details": threat.details,
                    "timestamp": threat.timestamp.isoformat(),
                },
                db=self.db,
                organization_id=organization_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()