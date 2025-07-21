"""Enhanced security monitoring service for comprehensive audit logging."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.security_event import (
    SecurityAlert,
    SecurityEvent,
    SecurityEventType,
    SecurityIncident,
    SecurityIncidentStatus,
    ThreatLevel,
)
from app.models.user import User
from app.models.user_activity_log import UserActivityLog


class EnhancedSecurityService:
    """Enhanced security service for comprehensive monitoring and audit logging."""

    def __init__(self, db: AsyncSession | Session):
        """Initialize the enhanced security service."""
        self.db = db
        self.alert_subscribers: List[callable] = []

    # ===== EVENT LOGGING =====

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        title: str,
        description: str,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        threat_level: ThreatLevel = ThreatLevel.LOW,
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        auto_response: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        """Log a comprehensive security event."""
        event_id = str(uuid.uuid4())
        
        # Calculate risk score based on event type and threat level
        risk_score = self._calculate_risk_score(event_type, threat_level)
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(event_type, threat_level)
        
        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            threat_level=threat_level,
            user_id=user_id,
            organization_id=organization_id,
            title=title,
            description=description,
            details=details or {},
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session_id,
            api_endpoint=api_endpoint,
            http_method=http_method,
            risk_score=risk_score,
            evidence=evidence or {},
            recommended_actions=recommended_actions,
            auto_response_taken=auto_response or {},
        )
        
        # Calculate integrity checksum
        event.checksum = event.calculate_checksum()
        
        self.db.add(event)
        await self._async_commit()
        
        # Process automatic responses
        await self._process_automatic_response(event)
        
        # Notify subscribers
        await self._notify_alert_subscribers(event)
        
        return event

    async def log_user_activity(
        self,
        action: str,
        resource_type: str,
        resource_id: int,
        user: User,
        changes: Dict[str, Any],
        organization_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ) -> AuditLog:
        """Log user activity with enhanced security context."""
        # Create traditional audit log
        audit = AuditLog(
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        audit.checksum = audit.calculate_checksum()
        self.db.add(audit)
        
        # Analyze for security implications
        await self._analyze_activity_for_security_events(
            action, resource_type, user, changes, ip_address, user_agent, session_id, api_endpoint
        )
        
        await self._async_commit()
        return audit

    # ===== THREAT DETECTION =====

    async def detect_suspicious_activities(
        self,
        time_window_hours: int = 24,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Detect suspicious activities within a time window."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        # Build base query
        query = select(SecurityEvent).where(
            SecurityEvent.created_at >= start_time,
            SecurityEvent.created_at <= end_time
        )
        
        if organization_id:
            query = query.where(SecurityEvent.organization_id == organization_id)
        
        events = await self.db.execute(query)
        events = events.scalars().all()
        
        # Analyze patterns
        analysis = {
            "detection_time": end_time.isoformat(),
            "time_window_hours": time_window_hours,
            "total_events": len(events),
            "threat_summary": await self._analyze_threat_patterns(events),
            "high_risk_events": [
                self._event_to_dict(event) for event in events 
                if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
            ],
            "suspicious_patterns": await self._detect_behavioral_patterns(events),
            "recommendations": self._generate_security_recommendations(events),
        }
        
        return analysis

    async def analyze_user_risk_profile(
        self,
        user_id: int,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """Analyze comprehensive risk profile for a user."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        # Get user events
        events_query = select(SecurityEvent).where(
            SecurityEvent.user_id == user_id,
            SecurityEvent.created_at >= start_time,
        )
        events = await self.db.execute(events_query)
        events = events.scalars().all()
        
        # Get audit logs
        audit_query = select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= start_time,
        )
        audits = await self.db.execute(audit_query)
        audits = audits.scalars().all()
        
        # Calculate risk metrics
        risk_profile = {
            "user_id": user_id,
            "analysis_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days_back,
            },
            "event_summary": {
                "total_security_events": len(events),
                "total_audit_logs": len(audits),
                "high_risk_events": len([e for e in events if e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]),
                "failed_logins": len([e for e in events if e.event_type == SecurityEventType.LOGIN_FAILURE]),
                "privilege_escalations": len([e for e in events if e.event_type == SecurityEventType.PRIVILEGE_ESCALATION]),
            },
            "risk_score": self._calculate_user_risk_score(events, audits),
            "behavioral_anomalies": await self._detect_user_anomalies(user_id, events, audits),
            "access_patterns": self._analyze_access_patterns(events, audits),
            "recommendations": self._generate_user_recommendations(events),
        }
        
        return risk_profile

    # ===== INCIDENT MANAGEMENT =====

    async def create_security_incident(
        self,
        title: str,
        description: str,
        severity: ThreatLevel,
        category: str,
        organization_id: Optional[int] = None,
        assigned_to: Optional[int] = None,
        related_events: Optional[List[int]] = None,
        affected_users: Optional[List[int]] = None,
        affected_resources: Optional[List[str]] = None,
    ) -> SecurityIncident:
        """Create a new security incident."""
        incident_id = str(uuid.uuid4())
        
        incident = SecurityIncident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=SecurityIncidentStatus.OPEN,
            category=category,
            organization_id=organization_id,
            assigned_to=assigned_to,
            related_events=related_events or [],
            affected_users=affected_users or [],
            affected_resources=affected_resources or [],
            timeline=[{
                "timestamp": datetime.utcnow().isoformat(),
                "action": "incident_created",
                "description": "Security incident created",
            }],
        )
        
        self.db.add(incident)
        await self._async_commit()
        
        # Generate alert for high severity incidents
        if severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self.create_security_alert(
                alert_type="security_incident",
                severity=severity,
                title=f"High Severity Security Incident: {title}",
                message=description,
                organization_id=organization_id,
                related_incident_id=incident.id,
            )
        
        return incident

    async def update_incident_status(
        self,
        incident_id: int,
        status: SecurityIncidentStatus,
        notes: Optional[str] = None,
        updated_by: Optional[int] = None,
    ) -> SecurityIncident:
        """Update security incident status."""
        incident_query = select(SecurityIncident).where(SecurityIncident.id == incident_id)
        result = await self.db.execute(incident_query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        
        old_status = incident.status
        incident.status = status
        
        # Add to timeline
        timeline_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "status_changed",
            "description": f"Status changed from {old_status} to {status}",
            "updated_by": updated_by,
            "notes": notes,
        }
        
        if incident.timeline:
            incident.timeline.append(timeline_entry)
        else:
            incident.timeline = [timeline_entry]
        
        if status == SecurityIncidentStatus.RESOLVED:
            incident.resolved_at = datetime.utcnow()
            if notes:
                incident.resolution = notes
        
        await self._async_commit()
        return incident

    # ===== ALERT MANAGEMENT =====

    async def create_security_alert(
        self,
        alert_type: str,
        severity: ThreatLevel,
        title: str,
        message: str,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        related_event_id: Optional[int] = None,
        related_incident_id: Optional[int] = None,
        recipients: Optional[List[int]] = None,
        delivery_methods: Optional[List[str]] = None,
    ) -> SecurityAlert:
        """Create a security alert."""
        alert_id = str(uuid.uuid4())
        
        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            user_id=user_id,
            organization_id=organization_id,
            related_event_id=related_event_id,
            related_incident_id=related_incident_id,
            recipients=recipients or [],
            delivery_methods=delivery_methods or ["email", "in_app"],
        )
        
        self.db.add(alert)
        await self._async_commit()
        
        # Process alert delivery
        await self._deliver_alert(alert)
        
        return alert

    async def acknowledge_alert(
        self,
        alert_id: int,
        acknowledged_by: int,
    ) -> SecurityAlert:
        """Acknowledge a security alert."""
        alert_query = select(SecurityAlert).where(SecurityAlert.id == alert_id)
        result = await self.db.execute(alert_query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        await self._async_commit()
        return alert

    # ===== DASHBOARD AND REPORTING =====

    async def get_security_dashboard_data(
        self,
        organization_id: Optional[int] = None,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """Get comprehensive security dashboard data."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # Base queries
        events_query = select(SecurityEvent).where(
            SecurityEvent.created_at >= start_time
        )
        incidents_query = select(SecurityIncident).where(
            SecurityIncident.created_at >= start_time
        )
        alerts_query = select(SecurityAlert).where(
            SecurityAlert.created_at >= start_time
        )
        
        if organization_id:
            events_query = events_query.where(SecurityEvent.organization_id == organization_id)
            incidents_query = incidents_query.where(SecurityIncident.organization_id == organization_id)
            alerts_query = alerts_query.where(SecurityAlert.organization_id == organization_id)
        
        # Execute queries
        events_result = await self.db.execute(events_query)
        events = events_result.scalars().all()
        
        incidents_result = await self.db.execute(incidents_query)
        incidents = incidents_result.scalars().all()
        
        alerts_result = await self.db.execute(alerts_query)
        alerts = alerts_result.scalars().all()
        
        # Generate dashboard data
        dashboard = {
            "generated_at": end_time.isoformat(),
            "time_range_hours": time_range_hours,
            "organization_id": organization_id,
            "summary": {
                "total_events": len(events),
                "total_incidents": len(incidents),
                "total_alerts": len(alerts),
                "critical_events": len([e for e in events if e.threat_level == ThreatLevel.CRITICAL]),
                "open_incidents": len([i for i in incidents if i.status == SecurityIncidentStatus.OPEN]),
                "unacknowledged_alerts": len([a for a in alerts if not a.acknowledged]),
            },
            "threat_levels": {
                "critical": len([e for e in events if e.threat_level == ThreatLevel.CRITICAL]),
                "high": len([e for e in events if e.threat_level == ThreatLevel.HIGH]),
                "medium": len([e for e in events if e.threat_level == ThreatLevel.MEDIUM]),
                "low": len([e for e in events if e.threat_level == ThreatLevel.LOW]),
            },
            "event_types": self._group_events_by_type(events),
            "recent_critical_events": [
                self._event_to_dict(e) for e in events 
                if e.threat_level == ThreatLevel.CRITICAL
            ][:10],
            "active_incidents": [
                self._incident_to_dict(i) for i in incidents 
                if i.status in [SecurityIncidentStatus.OPEN, SecurityIncidentStatus.INVESTIGATING]
            ][:10],
            "security_health_score": self._calculate_security_health_score(events, incidents),
            "recommendations": self._generate_dashboard_recommendations(events, incidents, alerts),
        }
        
        return dashboard

    # ===== EXPORT FUNCTIONALITY =====

    async def export_security_logs(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[SecurityEventType]] = None,
        threat_levels: Optional[List[ThreatLevel]] = None,
        organization_id: Optional[int] = None,
    ) -> str:
        """Export security logs in specified format."""
        # Build query
        query = select(SecurityEvent)
        
        if start_date:
            query = query.where(SecurityEvent.created_at >= start_date)
        if end_date:
            query = query.where(SecurityEvent.created_at <= end_date)
        if event_types:
            query = query.where(SecurityEvent.event_type.in_(event_types))
        if threat_levels:
            query = query.where(SecurityEvent.threat_level.in_(threat_levels))
        if organization_id:
            query = query.where(SecurityEvent.organization_id == organization_id)
        
        result = await self.db.execute(query.order_by(desc(SecurityEvent.created_at)))
        events = result.scalars().all()
        
        if format == "json":
            return self._export_as_json(events)
        elif format == "csv":
            return self._export_as_csv(events)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    # ===== PRIVATE HELPER METHODS =====

    def _calculate_risk_score(self, event_type: SecurityEventType, threat_level: ThreatLevel) -> int:
        """Calculate risk score for an event."""
        base_scores = {
            ThreatLevel.LOW: 10,
            ThreatLevel.MEDIUM: 30,
            ThreatLevel.HIGH: 70,
            ThreatLevel.CRITICAL: 100,
        }
        
        event_multipliers = {
            SecurityEventType.LOGIN_FAILURE: 1.0,
            SecurityEventType.LOGIN_MULTIPLE_FAILURES: 1.5,
            SecurityEventType.PRIVILEGE_ESCALATION: 2.0,
            SecurityEventType.UNAUTHORIZED_ACCESS: 2.5,
            SecurityEventType.DATA_DELETION: 3.0,
            SecurityEventType.BULK_DATA_ACCESS: 2.0,
            SecurityEventType.SUSPICIOUS_IP: 1.5,
            SecurityEventType.AFTER_HOURS_ACCESS: 1.2,
            SecurityEventType.MALWARE_DETECTED: 3.0,
            SecurityEventType.VULNERABILITY_DETECTED: 2.5,
        }
        
        base_score = base_scores.get(threat_level, 10)
        multiplier = event_multipliers.get(event_type, 1.0)
        
        return min(int(base_score * multiplier), 100)

    def _generate_recommended_actions(self, event_type: SecurityEventType, threat_level: ThreatLevel) -> List[str]:
        """Generate recommended actions for an event."""
        actions = []
        
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            actions.append("Immediate investigation required")
            actions.append("Notify security team")
        
        if event_type == SecurityEventType.LOGIN_MULTIPLE_FAILURES:
            actions.extend([
                "Consider temporary account lockout",
                "Verify user identity",
                "Check for brute force attacks",
            ])
        elif event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            actions.extend([
                "Review user permissions",
                "Audit privilege change authorization",
                "Monitor user activity closely",
            ])
        elif event_type == SecurityEventType.SUSPICIOUS_IP:
            actions.extend([
                "Block suspicious IP if confirmed malicious",
                "Check geolocation and known threat databases",
                "Monitor for additional activity from same IP",
            ])
        elif event_type == SecurityEventType.DATA_DELETION:
            actions.extend([
                "Verify data backup integrity",
                "Check deletion authorization",
                "Investigate potential data loss",
            ])
        
        return actions

    async def _analyze_activity_for_security_events(
        self,
        action: str,
        resource_type: str,
        user: User,
        changes: Dict[str, Any],
        ip_address: Optional[str],
        user_agent: Optional[str],
        session_id: Optional[str],
        api_endpoint: Optional[str],
    ) -> None:
        """Analyze user activity for potential security events."""
        # Check for privilege escalation
        if action in ["create", "update"] and resource_type in ["role", "permission", "user_role"]:
            await self.log_security_event(
                event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                title=f"Privilege change detected: {action} {resource_type}",
                description=f"User {user.id} performed {action} on {resource_type}",
                user_id=user.id,
                organization_id=user.organization_id,
                threat_level=ThreatLevel.MEDIUM,
                details={
                    "action": action,
                    "resource_type": resource_type,
                    "changes": changes,
                },
                source_ip=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                api_endpoint=api_endpoint,
            )
        
        # Check for bulk data access
        if action == "read" and "bulk" in str(changes).lower():
            await self.log_security_event(
                event_type=SecurityEventType.BULK_DATA_ACCESS,
                title="Bulk data access detected",
                description=f"User {user.id} accessed large amount of {resource_type} data",
                user_id=user.id,
                organization_id=user.organization_id,
                threat_level=ThreatLevel.MEDIUM,
                details={
                    "action": action,
                    "resource_type": resource_type,
                    "changes": changes,
                },
                source_ip=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                api_endpoint=api_endpoint,
            )
        
        # Check for data deletion
        if action == "delete":
            threat_level = ThreatLevel.HIGH if resource_type in ["user", "organization", "audit_log"] else ThreatLevel.MEDIUM
            await self.log_security_event(
                event_type=SecurityEventType.DATA_DELETION,
                title=f"Data deletion: {resource_type}",
                description=f"User {user.id} deleted {resource_type} data",
                user_id=user.id,
                organization_id=user.organization_id,
                threat_level=threat_level,
                details={
                    "action": action,
                    "resource_type": resource_type,
                    "changes": changes,
                },
                source_ip=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                api_endpoint=api_endpoint,
            )

    async def _process_automatic_response(self, event: SecurityEvent) -> None:
        """Process automatic responses for security events."""
        if event.threat_level == ThreatLevel.CRITICAL:
            # Create incident for critical events
            await self.create_security_incident(
                title=f"Critical Security Event: {event.title}",
                description=f"Automatically created incident for critical event: {event.description}",
                severity=ThreatLevel.CRITICAL,
                category="automated_response",
                organization_id=event.organization_id,
                related_events=[event.id],
                affected_users=[event.user_id] if event.user_id else [],
            )

    async def _notify_alert_subscribers(self, event: SecurityEvent) -> None:
        """Notify alert subscribers of new security events."""
        for subscriber in self.alert_subscribers:
            try:
                await subscriber(event)
            except Exception as e:
                # Log error but don't interrupt processing
                print(f"Error notifying subscriber: {e}")

    def subscribe_to_alerts(self, callback: callable) -> None:
        """Subscribe to security alert notifications."""
        self.alert_subscribers.append(callback)

    async def _deliver_alert(self, alert: SecurityAlert) -> None:
        """Deliver security alert through specified methods."""
        alert.delivered_at = datetime.utcnow()
        await self._async_commit()

    async def _analyze_threat_patterns(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Analyze threat patterns in security events."""
        if not events:
            return {"total_events": 0, "threat_score": 0}
        
        threat_scores = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.HIGH: 7,
            ThreatLevel.CRITICAL: 10,
        }
        
        total_score = sum(threat_scores.get(event.threat_level, 0) for event in events)
        avg_score = total_score / len(events) if events else 0
        
        return {
            "total_events": len(events),
            "threat_score": total_score,
            "average_threat_score": avg_score,
            "critical_events": len([e for e in events if e.threat_level == ThreatLevel.CRITICAL]),
            "high_risk_users": len(set(e.user_id for e in events if e.user_id and e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL])),
        }

    async def _detect_behavioral_patterns(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Detect suspicious behavioral patterns."""
        patterns = {
            "repeated_failures": [],
            "privilege_escalations": [],
            "suspicious_ips": [],
            "after_hours_activity": [],
        }
        
        # Group events by user and analyze
        user_events = {}
        for event in events:
            if event.user_id:
                if event.user_id not in user_events:
                    user_events[event.user_id] = []
                user_events[event.user_id].append(event)
        
        for user_id, user_events_list in user_events.items():
            failed_logins = [e for e in user_events_list if e.event_type == SecurityEventType.LOGIN_FAILURE]
            if len(failed_logins) >= 3:
                patterns["repeated_failures"].append({
                    "user_id": user_id,
                    "failure_count": len(failed_logins),
                    "last_failure": max(e.created_at for e in failed_logins).isoformat(),
                })
        
        return patterns

    def _generate_security_recommendations(self, events: List[SecurityEvent]) -> List[str]:
        """Generate security recommendations based on events."""
        recommendations = []
        
        if any(e.threat_level == ThreatLevel.CRITICAL for e in events):
            recommendations.append("Critical threats detected - immediate response required")
        
        failed_logins = [e for e in events if e.event_type == SecurityEventType.LOGIN_FAILURE]
        if len(failed_logins) > 10:
            recommendations.append("High number of failed logins - consider implementing rate limiting")
        
        suspicious_ips = set(e.source_ip for e in events if e.source_ip and e.event_type == SecurityEventType.SUSPICIOUS_IP)
        if suspicious_ips:
            recommendations.append(f"Block {len(suspicious_ips)} suspicious IP addresses")
        
        return recommendations

    def _calculate_user_risk_score(self, events: List[SecurityEvent], audits: List[AuditLog]) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a user."""
        if not events and not audits:
            return {"total_score": 0, "risk_level": "low"}
        
        score = 0
        
        # Score based on security events
        for event in events:
            if event.threat_level == ThreatLevel.CRITICAL:
                score += 50
            elif event.threat_level == ThreatLevel.HIGH:
                score += 25
            elif event.threat_level == ThreatLevel.MEDIUM:
                score += 10
            else:
                score += 2
        
        # Additional scoring based on activity volume
        if len(audits) > 1000:  # Very high activity
            score += 10
        elif len(audits) > 500:  # High activity
            score += 5
        
        # Determine risk level
        if score >= 100:
            risk_level = "critical"
        elif score >= 50:
            risk_level = "high"
        elif score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "total_score": min(score, 100),
            "risk_level": risk_level,
            "event_count": len(events),
            "audit_count": len(audits),
        }

    async def _detect_user_anomalies(self, user_id: int, events: List[SecurityEvent], audits: List[AuditLog]) -> List[Dict[str, Any]]:
        """Detect behavioral anomalies for a user."""
        anomalies = []
        
        # Check for unusual login times
        login_events = [e for e in events if e.event_type in [SecurityEventType.LOGIN_SUCCESS, SecurityEventType.LOGIN_FAILURE]]
        if login_events:
            login_hours = [e.created_at.hour for e in login_events]
            unusual_hours = [h for h in login_hours if h < 6 or h > 22]  # Before 6 AM or after 10 PM
            if len(unusual_hours) > len(login_hours) * 0.3:  # More than 30% unusual hours
                anomalies.append({
                    "type": "unusual_login_times",
                    "description": "User frequently logs in during unusual hours",
                    "evidence": {"unusual_hour_percentage": len(unusual_hours) / len(login_hours)},
                })
        
        # Check for failed login spikes
        failed_logins = [e for e in events if e.event_type == SecurityEventType.LOGIN_FAILURE]
        if len(failed_logins) > 5:
            anomalies.append({
                "type": "excessive_failed_logins",
                "description": f"User has {len(failed_logins)} failed login attempts",
                "evidence": {"failed_login_count": len(failed_logins)},
            })
        
        return anomalies

    def _analyze_access_patterns(self, events: List[SecurityEvent], audits: List[AuditLog]) -> Dict[str, Any]:
        """Analyze user access patterns."""
        patterns = {
            "login_frequency": len([e for e in events if e.event_type == SecurityEventType.LOGIN_SUCCESS]),
            "data_access_frequency": len([a for a in audits if a.action == "read"]),
            "data_modification_frequency": len([a for a in audits if a.action in ["create", "update", "delete"]]),
            "unique_resources_accessed": len(set(a.resource_type for a in audits)),
            "peak_activity_hours": self._calculate_peak_hours([e.created_at for e in events] + [a.created_at for a in audits]),
        }
        
        return patterns

    def _calculate_peak_hours(self, timestamps: List[datetime]) -> List[int]:
        """Calculate peak activity hours."""
        if not timestamps:
            return []
        
        hour_counts = {}
        for ts in timestamps:
            hour = ts.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        if not hour_counts:
            return []
        
        max_count = max(hour_counts.values())
        peak_hours = [hour for hour, count in hour_counts.items() if count >= max_count * 0.8]
        
        return sorted(peak_hours)

    def _generate_user_recommendations(self, events: List[SecurityEvent]) -> List[str]:
        """Generate recommendations for a specific user."""
        recommendations = []
        
        failed_logins = [e for e in events if e.event_type == SecurityEventType.LOGIN_FAILURE]
        if len(failed_logins) > 3:
            recommendations.append("Consider enabling two-factor authentication")
            recommendations.append("Review recent login attempts for unauthorized access")
        
        high_risk_events = [e for e in events if e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]
        if high_risk_events:
            recommendations.append("Immediate security review required")
            recommendations.append("Contact security team for incident response")
        
        return recommendations

    def _group_events_by_type(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Group events by type for dashboard display."""
        type_counts = {}
        for event in events:
            event_type = event.event_type.value if event.event_type else "unknown"
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        return type_counts

    def _calculate_security_health_score(self, events: List[SecurityEvent], incidents: List[SecurityIncident]) -> Dict[str, Any]:
        """Calculate overall security health score."""
        base_score = 100
        
        # Deduct points for security events
        for event in events:
            if event.threat_level == ThreatLevel.CRITICAL:
                base_score -= 10
            elif event.threat_level == ThreatLevel.HIGH:
                base_score -= 5
            elif event.threat_level == ThreatLevel.MEDIUM:
                base_score -= 2
            else:
                base_score -= 1
        
        # Deduct points for unresolved incidents
        unresolved_incidents = [i for i in incidents if i.status != SecurityIncidentStatus.RESOLVED]
        base_score -= len(unresolved_incidents) * 5
        
        # Ensure score doesn't go below 0
        final_score = max(base_score, 0)
        
        # Determine health level
        if final_score >= 90:
            health_level = "excellent"
        elif final_score >= 75:
            health_level = "good"
        elif final_score >= 50:
            health_level = "fair"
        elif final_score >= 25:
            health_level = "poor"
        else:
            health_level = "critical"
        
        return {
            "score": final_score,
            "health_level": health_level,
            "total_events": len(events),
            "unresolved_incidents": len(unresolved_incidents),
        }

    def _generate_dashboard_recommendations(self, events: List[SecurityEvent], incidents: List[SecurityIncident], alerts: List[SecurityAlert]) -> List[str]:
        """Generate recommendations for security dashboard."""
        recommendations = []
        
        unacknowledged_alerts = [a for a in alerts if not a.acknowledged]
        if unacknowledged_alerts:
            recommendations.append(f"Acknowledge {len(unacknowledged_alerts)} pending security alerts")
        
        critical_events = [e for e in events if e.threat_level == ThreatLevel.CRITICAL]
        if critical_events:
            recommendations.append(f"Investigate {len(critical_events)} critical security events")
        
        open_incidents = [i for i in incidents if i.status == SecurityIncidentStatus.OPEN]
        if open_incidents:
            recommendations.append(f"Assign and investigate {len(open_incidents)} open security incidents")
        
        return recommendations

    def _event_to_dict(self, event: SecurityEvent) -> Dict[str, Any]:
        """Convert SecurityEvent to dictionary for JSON serialization."""
        return {
            "id": event.id,
            "event_id": event.event_id,
            "event_type": event.event_type.value if event.event_type else None,
            "threat_level": event.threat_level.value if event.threat_level else None,
            "title": event.title,
            "description": event.description,
            "user_id": event.user_id,
            "organization_id": event.organization_id,
            "source_ip": event.source_ip,
            "risk_score": event.risk_score,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    def _incident_to_dict(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Convert SecurityIncident to dictionary for JSON serialization."""
        return {
            "id": incident.id,
            "incident_id": incident.incident_id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity.value if incident.severity else None,
            "status": incident.status.value if incident.status else None,
            "category": incident.category,
            "organization_id": incident.organization_id,
            "assigned_to": incident.assigned_to,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
        }

    def _export_as_json(self, events: List[SecurityEvent]) -> str:
        """Export events as JSON."""
        import json
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_events": len(events),
            "events": [self._event_to_dict(event) for event in events],
        }
        
        return json.dumps(export_data, indent=2)

    def _export_as_csv(self, events: List[SecurityEvent]) -> str:
        """Export events as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            "ID", "Event ID", "Event Type", "Threat Level", "Title", 
            "User ID", "Organization ID", "Source IP", "Risk Score", "Created At"
        ])
        
        # Data rows
        for event in events:
            writer.writerow([
                event.id,
                event.event_id,
                event.event_type.value if event.event_type else "",
                event.threat_level.value if event.threat_level else "",
                event.title,
                event.user_id or "",
                event.organization_id or "",
                event.source_ip or "",
                event.risk_score,
                event.created_at.isoformat() if event.created_at else "",
            ])
        
        return output.getvalue()

    async def _async_commit(self):
        """Handle async commit for AsyncSession."""
        if hasattr(self.db, 'commit'):
            await self.db.commit()
        else:
            self.db.commit()