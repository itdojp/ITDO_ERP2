<<<<<<< HEAD
"""Unit tests for security audit service."""
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security.audit_log import SecurityAuditLog
from app.schemas.security.audit_log import (
    SecurityAuditLogCreate,
    SecurityAuditLogFilter,
    SecurityEventType,
    SecuritySeverity,
)
from app.services.security.audit_service import SecurityAuditService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=AsyncSession)


@pytest.fixture
def audit_service(mock_db):
    """Create audit service instance."""
    return SecurityAuditService(mock_db)


@pytest.fixture
def sample_audit_log():
    """Create sample audit log."""
    return SecurityAuditLog(
        id=uuid4(),
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.INFO,
        user_id=str(uuid4()),
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        event_data={"test": "data"},
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_log_event_success(audit_service, mock_db):
    """Test successful event logging."""
    # Arrange
    event_data = SecurityAuditLogCreate(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.INFO,
        user_id=str(uuid4()),
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        event_data={"test": "data"},
    )
    
    mock_audit_log = Mock(spec=SecurityAuditLog)
    mock_audit_log.id = uuid4()
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Act
    result = await audit_service.log_event(event_data)

    # Assert
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_get_logs_with_filter(audit_service, mock_db, sample_audit_log):
    """Test getting logs with filter."""
    # Arrange
    filter_data = SecurityAuditLogFilter(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.INFO,
        limit=10,
        offset=0,
    )
    
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all = AsyncMock(return_value=[sample_audit_log])
    
    mock_db.query.return_value = mock_query

    # Act
    result = await audit_service.get_logs(filter_data)

    # Assert
    assert result == [sample_audit_log]
    mock_query.filter.assert_called()
    mock_query.order_by.assert_called_once()


@pytest.mark.asyncio
async def test_get_metrics(audit_service, mock_db):
    """Test getting security metrics."""
    # Arrange
    mock_result = Mock()
    mock_result.scalar.return_value = 100
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await audit_service.get_metrics()

    # Assert
    assert result is not None
    assert hasattr(result, 'total_events')
    mock_db.execute.assert_called()


@pytest.mark.asyncio
async def test_detect_anomalies(audit_service, mock_db):
    """Test anomaly detection."""
    # Arrange
    user_id = str(uuid4())
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all = AsyncMock(return_value=[])
    
    mock_db.query.return_value = mock_query

    # Act
    result = await audit_service.detect_anomalies(user_id)

    # Assert
    assert isinstance(result, list)
    mock_query.filter.assert_called()


@pytest.mark.asyncio
async def test_log_event_with_database_error(audit_service, mock_db):
    """Test event logging with database error."""
    # Arrange
    event_data = SecurityAuditLogCreate(
        event_type=SecurityEventType.LOGIN_FAILED,
        severity=SecuritySeverity.WARNING,
        user_id=str(uuid4()),
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        event_data={"error": "Invalid credentials"},
    )
    
    mock_db.add = Mock()
    mock_db.commit = AsyncMock(side_effect=Exception("Database error"))
    mock_db.rollback = AsyncMock()

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await audit_service.log_event(event_data)
    
    mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_logs_by_user(audit_service, mock_db, sample_audit_log):
    """Test getting logs for specific user."""
    # Arrange
    user_id = str(uuid4())
    filter_data = SecurityAuditLogFilter(
        user_id=user_id,
        limit=50,
        offset=0,
    )
    
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all = AsyncMock(return_value=[sample_audit_log])
    
    mock_db.query.return_value = mock_query

    # Act
    result = await audit_service.get_logs(filter_data)

    # Assert
    assert result == [sample_audit_log]
    mock_query.filter.assert_called()


@pytest.mark.asyncio
async def test_security_event_types():
    """Test security event type enum values."""
    assert SecurityEventType.LOGIN_SUCCESS == "login_success"
    assert SecurityEventType.LOGIN_FAILED == "login_failed"
    assert SecurityEventType.LOGOUT == "logout"
    assert SecurityEventType.PASSWORD_CHANGE == "password_change"
    assert SecurityEventType.PERMISSION_DENIED == "permission_denied"


@pytest.mark.asyncio
async def test_security_severity_levels():
    """Test security severity level enum values."""
    assert SecuritySeverity.INFO == "INFO"
    assert SecuritySeverity.WARNING == "WARNING"
    assert SecuritySeverity.ERROR == "ERROR"
    assert SecuritySeverity.CRITICAL == "CRITICAL"


@pytest.mark.asyncio
async def test_audit_log_filter_validation():
    """Test audit log filter validation."""
    # Valid filter
    filter_data = SecurityAuditLogFilter(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.INFO,
        start_date=datetime.now(),
        limit=100,
        offset=0,
    )
    
    assert filter_data.event_type == SecurityEventType.LOGIN_SUCCESS
    assert filter_data.severity == SecuritySeverity.INFO
    assert filter_data.limit == 100
=======
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
>>>>>>> ccb1e068def1ad909fc530c57afb662159a9b79c
