"""Unit tests for security audit service."""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.security.audit_service import SecurityAuditService
from app.models.security.audit_log import SecurityAuditLog
from app.schemas.security.audit_log import (
    SecurityAuditLogCreate,
    SecurityEventType,
    SecuritySeverity,
    SecurityAuditLogFilter,
)


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