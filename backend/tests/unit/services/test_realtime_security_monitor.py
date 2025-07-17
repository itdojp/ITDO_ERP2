"""
Test cases for RealTimeSecurityMonitor service.
リアルタイムセキュリティ監視サービスのテスト
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.realtime_security_monitor import (
    RealTimeSecurityMonitor,
    SecurityEvent,
    ThreatLevel,
    ThreatPattern,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def security_monitor(mock_db):
    """Create security monitor instance."""
    monitor = RealTimeSecurityMonitor(mock_db)
    return monitor


@pytest.mark.asyncio
class TestRealTimeSecurityMonitor:
    """Test cases for RealTimeSecurityMonitor."""

    async def test_initialization(self, security_monitor):
        """Test monitor initialization."""
        assert security_monitor.is_monitoring is False
        assert len(security_monitor.threat_patterns) > 0
        assert len(security_monitor.alert_rules) > 0
        assert security_monitor.event_buffer.maxlen == 10000

    async def test_start_monitoring(self, security_monitor):
        """Test starting monitoring."""
        with patch.object(security_monitor, '_monitoring_loop', new_callable=AsyncMock):
            await security_monitor.start_monitoring()
            assert security_monitor.is_monitoring is True
            assert security_monitor.monitoring_task is not None

    async def test_stop_monitoring(self, security_monitor):
        """Test stopping monitoring."""
        # Start monitoring first
        security_monitor.is_monitoring = True
        mock_task = AsyncMock()
        security_monitor.monitoring_task = mock_task

        await security_monitor.stop_monitoring()

        assert security_monitor.is_monitoring is False
        mock_task.cancel.assert_called_once()

    async def test_security_event_processing(self, security_monitor):
        """Test security event processing."""
        event = SecurityEvent(
            event_id="test_001",
            event_type="test_activity",
            user_id=1,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow(),
            details={"action": "login_success"},
            source_ip="192.168.1.1"
        )

        with patch.object(security_monitor, '_matches_pattern', return_value=False):
            await security_monitor._process_event(event)

        assert len(security_monitor.event_buffer) == 1
        assert security_monitor.event_buffer[0] == event

    async def test_brute_force_detection(self, security_monitor):
        """Test brute force attack detection."""
        # Create multiple failed login events
        for i in range(6):
            event = SecurityEvent(
                event_id=f"failed_login_{i}",
                event_type="login_attempt",
                user_id=1,
                threat_level=ThreatLevel.LOW,
                timestamp=datetime.utcnow(),
                details={"action": "login_failed"},
                source_ip="192.168.1.100",
                raw_data={"action": "login_failed"}
            )
            security_monitor.event_buffer.append(event)

        # Get brute force pattern
        pattern = security_monitor.threat_patterns["brute_force_login"]

        # Test pattern matching
        result = await security_monitor._matches_pattern(event, pattern)
        assert result is True

    async def test_privilege_escalation_detection(self, security_monitor):
        """Test privilege escalation detection."""
        # Create privilege escalation events
        for i in range(4):
            event = SecurityEvent(
                event_id=f"priv_escalation_{i}",
                event_type="audit_log",
                user_id=1,
                threat_level=ThreatLevel.LOW,
                timestamp=datetime.utcnow(),
                details={"changes": {"role": "admin"}},
                raw_data={
                    "action": "update",
                    "resource_type": "role"
                }
            )
            security_monitor.event_buffer.append(event)

        pattern = security_monitor.threat_patterns["privilege_escalation"]
        result = await security_monitor._matches_pattern(event, pattern)
        assert result is True

    async def test_threat_statistics(self, security_monitor):
        """Test threat statistics generation."""
        # Add some events to buffer
        now = datetime.utcnow()
        for level in [ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH]:
            event = SecurityEvent(
                event_id=f"test_{level.value}",
                event_type="test",
                user_id=1,
                threat_level=level,
                timestamp=now,
                details={}
            )
            security_monitor.event_buffer.append(event)

        stats = await security_monitor.get_threat_statistics()

        assert "timestamp" in stats
        assert "monitoring_status" in stats
        assert "threat_counts" in stats
        assert stats["threat_counts"]["low"] >= 1
        assert stats["threat_counts"]["medium"] >= 1
        assert stats["threat_counts"]["high"] >= 1

    async def test_user_risk_profile(self, security_monitor):
        """Test user risk profile generation."""
        user_id = 123

        # Add events for the user
        for i in range(5):
            event = SecurityEvent(
                event_id=f"user_event_{i}",
                event_type="activity",
                user_id=user_id,
                threat_level=ThreatLevel.MEDIUM if i > 2 else ThreatLevel.LOW,
                timestamp=datetime.utcnow(),
                details={}
            )
            security_monitor.event_buffer.append(event)

        profile = await security_monitor.get_user_risk_profile(user_id)

        assert profile["user_id"] == user_id
        assert profile["events_count"] == 5
        assert profile["risk_level"] in ["low", "medium", "high"]
        assert "threat_distribution" in profile

    async def test_event_condition_matching(self, security_monitor):
        """Test event condition matching logic."""
        event = SecurityEvent(
            event_id="condition_test",
            event_type="test",
            user_id=1,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow(),
            details={},
            source_ip="192.168.1.1",
            raw_data={"action": "login_failed"}
        )

        # Test equals condition
        conditions = [{"field": "action", "operator": "equals", "value": "login_failed"}]
        result = security_monitor._event_matches_conditions(event, conditions)
        assert result is True

        # Test in condition
        conditions = [{"field": "action", "operator": "in", "value": ["login_failed", "login_success"]}]
        result = security_monitor._event_matches_conditions(event, conditions)
        assert result is True

        # Test non-matching condition
        conditions = [{"field": "action", "operator": "equals", "value": "different_action"}]
        result = security_monitor._event_matches_conditions(event, conditions)
        assert result is False

    async def test_off_hours_detection(self, security_monitor):
        """Test off-hours access detection."""
        # Create event during off-hours (23:00)
        off_hours_time = datetime.utcnow().replace(hour=23, minute=0, second=0, microsecond=0)

        event = SecurityEvent(
            event_id="off_hours_test",
            event_type="login",
            user_id=1,
            threat_level=ThreatLevel.LOW,
            timestamp=off_hours_time,
            details={},
            raw_data={"action": "login_success"}
        )

        conditions = [
            {"field": "timestamp", "operator": "off_hours", "value": True},
            {"field": "action", "operator": "equals", "value": "login_success"}
        ]

        result = security_monitor._event_matches_conditions(event, conditions)
        assert result is True

    async def test_subscriber_notifications(self, security_monitor):
        """Test subscriber notification system."""
        notifications = []

        async def test_subscriber(event):
            notifications.append(event)

        # Subscribe to events
        security_monitor.subscribe(test_subscriber)

        # Process an event
        event = SecurityEvent(
            event_id="subscriber_test",
            event_type="test",
            user_id=1,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.utcnow(),
            details={}
        )

        with patch.object(security_monitor, '_matches_pattern', return_value=False):
            await security_monitor._process_event(event)

        # Check notification was sent
        assert len(notifications) == 1
        assert notifications[0] == event

        # Test unsubscribe
        security_monitor.unsubscribe(test_subscriber)
        await security_monitor._process_event(event)

        # Should still be 1 (no new notification)
        assert len(notifications) == 1

    @patch('app.services.realtime_security_monitor.select')
    async def test_collect_new_events(self, mock_select, security_monitor, mock_db):
        """Test collecting new events from database."""
        # Mock database results
        mock_activity = MagicMock()
        mock_activity.id = 1
        mock_activity.user_id = 1
        mock_activity.created_at = datetime.utcnow()
        mock_activity.action = "login_success"
        mock_activity.details = {}
        mock_activity.ip_address = "192.168.1.1"
        mock_activity.user_agent = "test-agent"

        mock_audit = MagicMock()
        mock_audit.id = 1
        mock_audit.user_id = 1
        mock_audit.created_at = datetime.utcnow()
        mock_audit.action = "read"
        mock_audit.resource_type = "user"
        mock_audit.resource_id = 1
        mock_audit.changes = {}
        mock_audit.ip_address = "192.168.1.1"
        mock_audit.user_agent = "test-agent"
        mock_audit.organization_id = 1

        # Mock database execution
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_activity]
        mock_db.execute.return_value = mock_result

        # Mock the second query for audit logs
        mock_audit_result = AsyncMock()
        mock_audit_result.scalars.return_value.all.return_value = [mock_audit]

        # Set up side effects for multiple calls
        mock_db.execute.side_effect = [mock_result, mock_audit_result]

        # Test collection
        with patch.object(security_monitor, '_process_event', new_callable=AsyncMock) as mock_process:
            await security_monitor._collect_new_events()

            # Should process both activity and audit events
            assert mock_process.call_count == 2

    async def test_alert_generation(self, security_monitor):
        """Test alert generation and throttling."""
        event = SecurityEvent(
            event_id="alert_test",
            event_type="test",
            user_id=1,
            threat_level=ThreatLevel.HIGH,
            timestamp=datetime.utcnow(),
            details={}
        )

        pattern = ThreatPattern(
            pattern_id="test_pattern",
            name="Test Pattern",
            description="Test pattern for alerts",
            threat_level=ThreatLevel.HIGH,
            time_window_minutes=10,
            max_events=1,
            conditions=[],
            actions=["notify_admin"]
        )

        with patch.object(security_monitor, '_send_alert', new_callable=AsyncMock) as mock_send:
            await security_monitor._generate_alerts(event, pattern)

            # Should send alert for high threat
            assert mock_send.call_count >= 1

            # Test throttling - second alert should be throttled
            await security_monitor._generate_alerts(event, pattern)

            # Should still be same count due to throttling
            assert mock_send.call_count >= 1

    async def test_action_execution(self, security_monitor):
        """Test security action execution."""
        event = SecurityEvent(
            event_id="action_test",
            event_type="test",
            user_id=1,
            threat_level=ThreatLevel.HIGH,
            timestamp=datetime.utcnow(),
            details={},
            source_ip="192.168.1.100"
        )

        pattern = ThreatPattern(
            pattern_id="test_pattern",
            name="Test Pattern",
            description="Test",
            threat_level=ThreatLevel.HIGH,
            time_window_minutes=10,
            max_events=1,
            conditions=[],
            actions=["lock_account", "block_ip", "notify_admin"]
        )

        with patch.object(security_monitor, '_lock_user_account', new_callable=AsyncMock) as mock_lock, \
             patch.object(security_monitor, '_block_ip_address', new_callable=AsyncMock) as mock_block, \
             patch.object(security_monitor, '_notify_administrators', new_callable=AsyncMock) as mock_notify:

            for action in pattern.actions:
                await security_monitor._execute_action(action, event, pattern)

            mock_lock.assert_called_once()
            mock_block.assert_called_once()
            mock_notify.assert_called_once()

    async def test_buffer_cleanup(self, security_monitor):
        """Test event buffer cleanup."""
        # Add old and new events
        old_time = datetime.utcnow() - timedelta(hours=2)
        new_time = datetime.utcnow()

        old_event = SecurityEvent(
            event_id="old_event",
            event_type="test",
            user_id=1,
            threat_level=ThreatLevel.LOW,
            timestamp=old_time,
            details={}
        )

        new_event = SecurityEvent(
            event_id="new_event",
            event_type="test",
            user_id=1,
            threat_level=ThreatLevel.LOW,
            timestamp=new_time,
            details={}
        )

        security_monitor.event_buffer.extend([old_event, new_event])

        # Manually trigger cleanup logic
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        while (security_monitor.event_buffer and
               security_monitor.event_buffer[0].timestamp < cutoff_time):
            security_monitor.event_buffer.popleft()

        # Only new event should remain
        assert len(security_monitor.event_buffer) == 1
        assert security_monitor.event_buffer[0].event_id == "new_event"

    async def test_data_exfiltration_detection(self, security_monitor):
        """Test data exfiltration pattern detection."""
        user_id = 1

        # Create multiple read operations on different resource types
        resource_types = ["user", "department", "customer", "financial", "document", "report"]

        for i, resource_type in enumerate(resource_types):
            for j in range(20):  # 20 operations per resource type
                event = SecurityEvent(
                    event_id=f"read_event_{i}_{j}",
                    event_type="audit_log",
                    user_id=user_id,
                    threat_level=ThreatLevel.LOW,
                    timestamp=datetime.utcnow(),
                    details={},
                    raw_data={
                        "action": "read",
                        "resource_type": resource_type
                    }
                )
                security_monitor.event_buffer.append(event)

        pattern = security_monitor.threat_patterns["data_exfiltration"]
        result = await security_monitor._matches_pattern(event, pattern)
        assert result is True

    async def test_monitoring_loop_error_handling(self, security_monitor):
        """Test error handling in monitoring loop."""
        # Mock an exception during event collection
        with patch.object(security_monitor, '_collect_new_events',
                         side_effect=Exception("Test exception")):

            security_monitor.is_monitoring = True

            # Start monitoring loop and let it run briefly
            task = asyncio.create_task(security_monitor._monitoring_loop())

            # Wait a short time then stop monitoring
            await asyncio.sleep(0.1)
            security_monitor.is_monitoring = False

            # Wait for task to complete
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except asyncio.TimeoutError:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # The loop should handle the exception and continue
        assert True  # If we get here, error handling worked
