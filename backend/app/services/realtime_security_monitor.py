"""
Real-time Security Monitoring Service for Issue #46 Enhancement.
リアルタイムセキュリティ監視サービス（Issue #46 拡張）
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.user import User
from app.models.user_activity_log import UserActivityLog


class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SLACK = "slack"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_id: str
    event_type: str
    user_id: int
    threat_level: ThreatLevel
    timestamp: datetime
    details: Dict
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    organization_id: Optional[int] = None
    raw_data: Optional[Dict] = None


@dataclass
class ThreatPattern:
    """Threat detection pattern definition."""
    pattern_id: str
    name: str
    description: str
    threat_level: ThreatLevel
    time_window_minutes: int
    max_events: int
    conditions: List[Dict]
    actions: List[str] = field(default_factory=list)


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    threat_levels: List[ThreatLevel]
    channels: List[AlertChannel]
    recipients: List[str]
    throttle_minutes: int = 5
    is_active: bool = True
    conditions: Dict = field(default_factory=dict)


class RealTimeSecurityMonitor:
    """Real-time security monitoring and threat detection service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_buffer: deque = deque(maxlen=10000)
        self.threat_patterns: Dict[str, ThreatPattern] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_history: Dict[str, datetime] = {}
        self.subscribers: List[Callable] = []
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None

        # Initialize built-in threat patterns
        self._initialize_threat_patterns()
        self._initialize_alert_rules()

    def _initialize_threat_patterns(self):
        """Initialize built-in threat detection patterns."""

        # Brute force login pattern
        self.threat_patterns["brute_force_login"] = ThreatPattern(
            pattern_id="brute_force_login",
            name="Brute Force Login Attack",
            description="Multiple failed login attempts from same IP",
            threat_level=ThreatLevel.HIGH,
            time_window_minutes=10,
            max_events=5,
            conditions=[
                {"field": "action", "operator": "equals", "value": "login_failed"},
                {"field": "source_ip", "operator": "group_by", "value": True}
            ],
            actions=["lock_account", "block_ip", "notify_admin"]
        )

        # Privilege escalation pattern
        self.threat_patterns["privilege_escalation"] = ThreatPattern(
            pattern_id="privilege_escalation",
            name="Privilege Escalation Attempt",
            description="Rapid privilege changes for a user",
            threat_level=ThreatLevel.CRITICAL,
            time_window_minutes=60,
            max_events=3,
            conditions=[
                {"field": "resource_type", "operator": "in", "value": ["role", "permission"]},
                {"field": "action", "operator": "in", "value": ["create", "update"]},
                {"field": "user_id", "operator": "group_by", "value": True}
            ],
            actions=["freeze_account", "notify_security", "require_approval"]
        )

        # Data exfiltration pattern
        self.threat_patterns["data_exfiltration"] = ThreatPattern(
            pattern_id="data_exfiltration",
            name="Potential Data Exfiltration",
            description="Unusual data access patterns",
            threat_level=ThreatLevel.HIGH,
            time_window_minutes=30,
            max_events=100,
            conditions=[
                {"field": "action", "operator": "equals", "value": "read"},
                {"field": "user_id", "operator": "group_by", "value": True},
                {"field": "resource_type", "operator": "diverse", "value": 5}
            ],
            actions=["monitor_user", "limit_access", "notify_admin"]
        )

        # Suspicious IP pattern
        self.threat_patterns["suspicious_ip"] = ThreatPattern(
            pattern_id="suspicious_ip",
            name="Suspicious IP Activity",
            description="Activity from known malicious IPs",
            threat_level=ThreatLevel.MEDIUM,
            time_window_minutes=5,
            max_events=1,
            conditions=[
                {"field": "source_ip", "operator": "in_blacklist", "value": True}
            ],
            actions=["block_ip", "notify_security"]
        )

        # Off-hours access pattern
        self.threat_patterns["off_hours_access"] = ThreatPattern(
            pattern_id="off_hours_access",
            name="Off-Hours Access",
            description="Access during non-business hours",
            threat_level=ThreatLevel.MEDIUM,
            time_window_minutes=1,
            max_events=1,
            conditions=[
                {"field": "timestamp", "operator": "off_hours", "value": True},
                {"field": "action", "operator": "equals", "value": "login_success"}
            ],
            actions=["log_suspicious", "notify_manager"]
        )

    def _initialize_alert_rules(self):
        """Initialize default alert rules."""

        # Critical threats - immediate notification
        self.alert_rules["critical_threats"] = AlertRule(
            rule_id="critical_threats",
            name="Critical Security Threats",
            threat_levels=[ThreatLevel.CRITICAL],
            channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.WEBHOOK],
            recipients=["security@company.com", "admin@company.com"],
            throttle_minutes=0  # No throttling for critical threats
        )

        # High threats - urgent notification
        self.alert_rules["high_threats"] = AlertRule(
            rule_id="high_threats",
            name="High Security Threats",
            threat_levels=[ThreatLevel.HIGH],
            channels=[AlertChannel.EMAIL, AlertChannel.IN_APP],
            recipients=["security@company.com"],
            throttle_minutes=5
        )

        # Medium threats - regular monitoring
        self.alert_rules["medium_threats"] = AlertRule(
            rule_id="medium_threats",
            name="Medium Security Threats",
            threat_levels=[ThreatLevel.MEDIUM],
            channels=[AlertChannel.IN_APP],
            recipients=["security@company.com"],
            throttle_minutes=30
        )

    async def start_monitoring(self):
        """Start real-time security monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        # Start background tasks
        asyncio.create_task(self._process_event_buffer())
        asyncio.create_task(self._cleanup_old_events())

    async def stop_monitoring(self):
        """Stop real-time security monitoring."""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Query for new security events
                await self._collect_new_events()
                await asyncio.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                # Log error but continue monitoring
                print(f"Monitoring error: {e}")
                await asyncio.sleep(10)

    async def _collect_new_events(self):
        """Collect new security events from the database."""
        # Get recent activity logs
        cutoff_time = datetime.utcnow() - timedelta(minutes=1)

        # Query recent user activity
        activity_query = select(UserActivityLog).where(
            UserActivityLog.created_at >= cutoff_time
        ).order_by(desc(UserActivityLog.created_at))

        activity_result = await self.db.execute(activity_query)
        activities = activity_result.scalars().all()

        # Query recent audit logs
        audit_query = select(AuditLog).where(
            AuditLog.created_at >= cutoff_time
        ).order_by(desc(AuditLog.created_at))

        audit_result = await self.db.execute(audit_query)
        audits = audit_result.scalars().all()

        # Convert to security events
        for activity in activities:
            event = SecurityEvent(
                event_id=f"activity_{activity.id}",
                event_type="user_activity",
                user_id=activity.user_id,
                threat_level=ThreatLevel.LOW,
                timestamp=activity.created_at,
                details=activity.details or {},
                source_ip=activity.ip_address,
                user_agent=activity.user_agent,
                raw_data={"action": activity.action}
            )
            await self._process_event(event)

        for audit in audits:
            event = SecurityEvent(
                event_id=f"audit_{audit.id}",
                event_type="audit_log",
                user_id=audit.user_id,
                threat_level=ThreatLevel.LOW,
                timestamp=audit.created_at,
                details=audit.changes or {},
                source_ip=audit.ip_address,
                user_agent=audit.user_agent,
                organization_id=audit.organization_id,
                raw_data={
                    "action": audit.action,
                    "resource_type": audit.resource_type,
                    "resource_id": audit.resource_id
                }
            )
            await self._process_event(event)

    async def _process_event(self, event: SecurityEvent):
        """Process a single security event."""
        self.event_buffer.append(event)

        # Check against threat patterns
        for pattern in self.threat_patterns.values():
            if await self._matches_pattern(event, pattern):
                await self._handle_threat_detection(event, pattern)

        # Notify subscribers
        for subscriber in self.subscribers:
            try:
                await subscriber(event)
            except Exception as e:
                print(f"Subscriber error: {e}")

    async def _matches_pattern(self, event: SecurityEvent, pattern: ThreatPattern) -> bool:
        """Check if event matches a threat pattern."""
        # Get recent events within the pattern's time window
        time_window = datetime.utcnow() - timedelta(minutes=pattern.time_window_minutes)
        recent_events = [e for e in self.event_buffer if e.timestamp >= time_window]

        # Apply pattern conditions
        matching_events = []
        for e in recent_events:
            if self._event_matches_conditions(e, pattern.conditions):
                matching_events.append(e)

        # Group by user_id or source_ip as specified in conditions
        groups = defaultdict(list)
        group_by_field = None

        for condition in pattern.conditions:
            if condition.get("operator") == "group_by" and condition.get("value"):
                group_by_field = condition["field"]
                break

        if group_by_field:
            for e in matching_events:
                key = getattr(e, group_by_field, None) or e.raw_data.get(group_by_field)
                if key:
                    groups[key].append(e)

            # Check if any group exceeds the threshold
            for group_events in groups.values():
                if len(group_events) >= pattern.max_events:
                    return True
        else:
            # Simple count threshold
            return len(matching_events) >= pattern.max_events

        return False

    def _event_matches_conditions(self, event: SecurityEvent, conditions: List[Dict]) -> bool:
        """Check if event matches all conditions."""
        for condition in conditions:
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]

            # Get field value from event
            if field in ["user_id", "threat_level", "timestamp", "source_ip", "user_agent", "organization_id"]:
                field_value = getattr(event, field, None)
            else:
                field_value = event.raw_data.get(field)

            # Apply operator
            if operator == "equals" and field_value != value:
                return False
            elif operator == "in" and field_value not in value:
                return False
            elif operator == "group_by":
                continue  # Handled separately
            elif operator == "diverse":
                # Check for diverse resource types (for data exfiltration)
                continue  # Handled in pattern matching
            elif operator == "in_blacklist":
                # Check IP blacklist (would need external IP reputation service)
                continue  # Placeholder
            elif operator == "off_hours":
                # Check if timestamp is outside business hours
                if field_value and isinstance(field_value, datetime):
                    hour = field_value.hour
                    if not (9 <= hour <= 17):  # Outside 9 AM - 5 PM
                        continue
                    else:
                        return False

        return True

    async def _handle_threat_detection(self, event: SecurityEvent, pattern: ThreatPattern):
        """Handle detected threat."""
        # Update event threat level
        event.threat_level = pattern.threat_level

        # Execute pattern actions
        for action in pattern.actions:
            await self._execute_action(action, event, pattern)

        # Generate alerts
        await self._generate_alerts(event, pattern)

    async def _execute_action(self, action: str, event: SecurityEvent, pattern: ThreatPattern):
        """Execute security action."""
        if action == "lock_account":
            await self._lock_user_account(event.user_id)
        elif action == "block_ip":
            await self._block_ip_address(event.source_ip)
        elif action == "notify_admin":
            await self._notify_administrators(event, pattern)
        elif action == "freeze_account":
            await self._freeze_user_account(event.user_id)
        elif action == "require_approval":
            await self._require_approval(event.user_id)
        elif action == "monitor_user":
            await self._add_user_to_monitoring(event.user_id)
        elif action == "limit_access":
            await self._limit_user_access(event.user_id)
        elif action == "log_suspicious":
            await self._log_suspicious_activity(event, pattern)

    async def _lock_user_account(self, user_id: int):
        """Lock user account."""
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if user:
            user.locked_until = datetime.utcnow() + timedelta(hours=1)
            await self.db.commit()

    async def _block_ip_address(self, ip_address: str):
        """Block IP address (placeholder for firewall integration)."""
        # This would integrate with firewall/security appliance
        print(f"Blocking IP address: {ip_address}")

    async def _notify_administrators(self, event: SecurityEvent, pattern: ThreatPattern):
        """Notify system administrators."""
        # This would send notifications through configured channels
        print(f"Admin notification: {pattern.name} detected for user {event.user_id}")

    async def _freeze_user_account(self, user_id: int):
        """Freeze user account (stronger than lock)."""
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if user:
            user.is_active = False
            await self.db.commit()

    async def _require_approval(self, user_id: int):
        """Require approval for user actions."""
        # This would set a flag requiring approval for sensitive actions
        print(f"Requiring approval for user {user_id}")

    async def _add_user_to_monitoring(self, user_id: int):
        """Add user to enhanced monitoring."""
        # This would add user to a monitoring list
        print(f"Adding user {user_id} to enhanced monitoring")

    async def _limit_user_access(self, user_id: int):
        """Limit user access permissions."""
        # This would temporarily reduce user permissions
        print(f"Limiting access for user {user_id}")

    async def _log_suspicious_activity(self, event: SecurityEvent, pattern: ThreatPattern):
        """Log suspicious activity."""
        # This would create a detailed log entry
        print(f"Logging suspicious activity: {pattern.name} for user {event.user_id}")

    async def _generate_alerts(self, event: SecurityEvent, pattern: ThreatPattern):
        """Generate alerts based on rules."""
        for rule in self.alert_rules.values():
            if not rule.is_active:
                continue

            if event.threat_level not in rule.threat_levels:
                continue

            # Check throttling
            alert_key = f"{rule.rule_id}_{event.user_id}_{pattern.pattern_id}"
            last_alert = self.alert_history.get(alert_key)
            if last_alert and datetime.utcnow() - last_alert < timedelta(minutes=rule.throttle_minutes):
                continue

            # Send alert
            await self._send_alert(rule, event, pattern)
            self.alert_history[alert_key] = datetime.utcnow()

    async def _send_alert(self, rule: AlertRule, event: SecurityEvent, pattern: ThreatPattern):
        """Send alert through configured channels."""
        alert_data = {
            "rule_id": rule.rule_id,
            "pattern_id": pattern.pattern_id,
            "pattern_name": pattern.name,
            "threat_level": event.threat_level.value,
            "user_id": event.user_id,
            "timestamp": event.timestamp.isoformat(),
            "details": event.details
        }

        for channel in rule.channels:
            if channel == AlertChannel.EMAIL:
                await self._send_email_alert(rule.recipients, alert_data)
            elif channel == AlertChannel.SMS:
                await self._send_sms_alert(rule.recipients, alert_data)
            elif channel == AlertChannel.WEBHOOK:
                await self._send_webhook_alert(alert_data)
            elif channel == AlertChannel.IN_APP:
                await self._send_in_app_alert(rule.recipients, alert_data)
            elif channel == AlertChannel.SLACK:
                await self._send_slack_alert(alert_data)

    async def _send_email_alert(self, recipients: List[str], alert_data: Dict):
        """Send email alert."""
        # This would integrate with email service
        print(f"Email alert sent to {recipients}: {alert_data['pattern_name']}")

    async def _send_sms_alert(self, recipients: List[str], alert_data: Dict):
        """Send SMS alert."""
        # This would integrate with SMS service
        print(f"SMS alert sent to {recipients}: {alert_data['pattern_name']}")

    async def _send_webhook_alert(self, alert_data: Dict):
        """Send webhook alert."""
        # This would send HTTP POST to configured webhook
        print(f"Webhook alert sent: {alert_data['pattern_name']}")

    async def _send_in_app_alert(self, recipients: List[str], alert_data: Dict):
        """Send in-app alert."""
        # This would create notifications in the application
        print(f"In-app alert sent to {recipients}: {alert_data['pattern_name']}")

    async def _send_slack_alert(self, alert_data: Dict):
        """Send Slack alert."""
        # This would send message to Slack channel
        print(f"Slack alert sent: {alert_data['pattern_name']}")

    async def _process_event_buffer(self):
        """Process events in buffer for analytics."""
        while self.is_monitoring:
            try:
                if len(self.event_buffer) > 0:
                    # Process buffered events for analytics
                    await self._analyze_event_patterns()
                await asyncio.sleep(30)  # Process every 30 seconds
            except Exception as e:
                print(f"Buffer processing error: {e}")
                await asyncio.sleep(60)

    async def _analyze_event_patterns(self):
        """Analyze event patterns for insights."""
        # This would perform advanced analytics on event patterns
        # Such as identifying new threat patterns, user behavior analysis, etc.
        pass

    async def _cleanup_old_events(self):
        """Clean up old events from buffer."""
        while self.is_monitoring:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                # Remove events older than 1 hour
                while self.event_buffer and self.event_buffer[0].timestamp < cutoff_time:
                    self.event_buffer.popleft()
                await asyncio.sleep(300)  # Clean up every 5 minutes
            except Exception as e:
                print(f"Cleanup error: {e}")
                await asyncio.sleep(600)

    def subscribe(self, callback: Callable):
        """Subscribe to security events."""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from security events."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def get_threat_statistics(self) -> Dict:
        """Get real-time threat statistics."""
        current_time = datetime.utcnow()
        last_hour = current_time - timedelta(hours=1)

        # Count events by threat level
        threat_counts = {level.value: 0 for level in ThreatLevel}
        pattern_counts = {}

        for event in self.event_buffer:
            if event.timestamp >= last_hour:
                threat_counts[event.threat_level.value] += 1

        # Count pattern detections
        for pattern_id, pattern in self.threat_patterns.items():
            pattern_counts[pattern_id] = sum(
                1 for event in self.event_buffer
                if event.timestamp >= last_hour and event.threat_level == pattern.threat_level
            )

        return {
            "timestamp": current_time.isoformat(),
            "monitoring_status": self.is_monitoring,
            "buffer_size": len(self.event_buffer),
            "threat_counts": threat_counts,
            "pattern_counts": pattern_counts,
            "active_patterns": len(self.threat_patterns),
            "active_rules": len([r for r in self.alert_rules.values() if r.is_active])
        }

    async def get_user_risk_profile(self, user_id: int) -> Dict:
        """Get detailed risk profile for a user."""
        user_events = [e for e in self.event_buffer if e.user_id == user_id]

        if not user_events:
            return {
                "user_id": user_id,
                "risk_level": "low",
                "events_count": 0,
                "last_activity": None
            }

        # Calculate risk metrics
        high_risk_events = [e for e in user_events if e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]
        recent_events = [e for e in user_events if e.timestamp >= datetime.utcnow() - timedelta(hours=1)]

        risk_level = "low"
        if len(high_risk_events) > 0:
            risk_level = "high"
        elif len(recent_events) > 10:
            risk_level = "medium"

        return {
            "user_id": user_id,
            "risk_level": risk_level,
            "events_count": len(user_events),
            "high_risk_events": len(high_risk_events),
            "recent_events": len(recent_events),
            "last_activity": max(e.timestamp for e in user_events).isoformat(),
            "threat_distribution": {
                level.value: len([e for e in user_events if e.threat_level == level])
                for level in ThreatLevel
            }
        }
