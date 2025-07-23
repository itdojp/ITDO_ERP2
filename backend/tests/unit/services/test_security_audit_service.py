"""Tests for security audit service."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.security.audit_log import (
    SecurityAuditLogCreate,
    SecurityAuditLogFilter,
    SecurityEventType,
    SecuritySeverity,
)
from app.services.security.audit_service import SecurityAuditService


@pytest.mark.asyncio
class TestSecurityAuditService:
    """Test security audit service."""

    async def test_log_event(self):
        """Test logging a security event."""
        db = AsyncMock()
        service = SecurityAuditService(db)

        event_data = SecurityAuditLogCreate(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecuritySeverity.INFO,
            user_id=uuid4(),
            ip_address="192.168.1.1",
            action="User login",
            result="SUCCESS"
        )

        # Mock the database operations
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await service.log_event(event_data)

        assert db.add.called
        assert db.commit.called
        assert db.refresh.called

    async def test_get_logs_with_filters(self):
        """Test getting logs with filters."""
        db = AsyncMock()
        service = SecurityAuditService(db)

        filters = SecurityAuditLogFilter(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecuritySeverity.WARNING,
            start_date=datetime.utcnow() - timedelta(days=1)
        )

        # Mock execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        logs = await service.get_logs(filters)

        assert db.execute.called
        assert isinstance(logs, list)

    async def test_get_metrics(self):
        """Test getting security metrics."""
        db = AsyncMock()
        service = SecurityAuditService(db)

        # Mock all the count queries
        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar.return_value = 10

        mock_group_result = MagicMock()
        mock_group_result.__iter__ = lambda self: iter([
            MagicMock(event_type='login_success', count=5),
            MagicMock(event_type='login_failure', count=3)
        ])

        # Set up different return values for different queries
        db.execute = AsyncMock(side_effect=[
            mock_scalar_result,  # total events
            mock_group_result,   # events by type
            mock_group_result,   # events by severity
            mock_scalar_result,  # failed logins
            mock_scalar_result,  # suspicious activities
            mock_scalar_result,  # blocked requests
            mock_scalar_result   # unique users
        ])

        metrics = await service.get_metrics()

        assert metrics.total_events == 10
        assert isinstance(metrics.events_by_type, dict)
        assert isinstance(metrics.events_by_severity, dict)

    async def test_detect_anomalies(self):
        """Test anomaly detection."""
        db = AsyncMock()
        service = SecurityAuditService(db)

        user_id = uuid4()

        # Mock count result for recent failures
        mock_failures_result = MagicMock()
        mock_failures_result.scalar.return_value = 6  # High failure count

        # Mock unusual activities
        mock_activities_result = MagicMock()
        mock_activities = [
            MagicMock(severity='CRITICAL'),
            MagicMock(severity='ERROR')
        ]
        mock_activities_result.scalars.return_value.all.return_value = mock_activities

        db.execute = AsyncMock(side_effect=[
            mock_failures_result,
            mock_activities_result
        ])

        anomalies = await service.detect_anomalies(user_id)

        assert anomalies['high_failure_rate'] is True
        assert anomalies['recent_failures'] == 6
        assert anomalies['requires_attention'] is True
