"""Unit tests for security audit API endpoints."""
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.schemas.security.audit_log import (
    SecurityAuditLogCreate,
    SecurityAuditLogResponse,
    SecurityEventType,
    SecurityMetrics,
    SecuritySeverity,
)


@pytest.fixture
def mock_current_user():
    """Mock current user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.is_admin = True
    return user


@pytest.fixture
def mock_current_user_non_admin():
    """Mock non-admin current user."""
    user = Mock(spec=User)
    user.id = str(uuid4())
    user.is_admin = False
    return user


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    return Mock()


@pytest.fixture
def sample_audit_log_response():
    """Sample audit log response."""
    return SecurityAuditLogResponse(
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
async def test_log_security_event_success(mock_current_user, mock_audit_service):
    """Test successful security event logging."""
    # Arrange
    event_data = SecurityAuditLogCreate(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.INFO,
        user_id=str(uuid4()),
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        event_data={"test": "data"},
    )

    mock_audit_service.log_event = AsyncMock(return_value=Mock(id=uuid4()))

    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service_class.return_value = mock_audit_service

        from app.api.v1.endpoints.security.audit import log_security_event

        # Act
        result = await log_security_event(
            event_data=event_data,
            current_user=mock_current_user,
            db=Mock()
        )

        # Assert
        assert result is not None
        mock_audit_service.log_event.assert_called_once_with(event_data)


@pytest.mark.asyncio
async def test_log_security_event_non_admin_forbidden(mock_current_user_non_admin):
    """Test security event logging forbidden for non-admin users."""
    # Arrange
    event_data = SecurityAuditLogCreate(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.INFO,
        user_id=str(uuid4()),
        ip_address="192.168.1.1",
        user_agent="Test Browser",
        event_data={"test": "data"},
    )

    from app.api.v1.endpoints.security.audit import log_security_event

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await log_security_event(
            event_data=event_data,
            current_user=mock_current_user_non_admin,
            db=Mock()
        )

    assert exc_info.value.status_code == 403
    assert "Admin access required" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_security_logs_success(mock_current_user, mock_audit_service, sample_audit_log_response):
    """Test successful retrieval of security logs."""
    # Arrange
    mock_audit_service.get_logs = AsyncMock(return_value=[sample_audit_log_response])

    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service_class.return_value = mock_audit_service

        from app.api.v1.endpoints.security.audit import get_security_logs

        # Act
        result = await get_security_logs(
            event_type=None,
            severity=None,
            user_id=None,
            start_date=None,
            end_date=None,
            limit=50,
            offset=0,
            current_user=mock_current_user,
            db=Mock()
        )

        # Assert
        assert result == [sample_audit_log_response]
        mock_audit_service.get_logs.assert_called_once()


@pytest.mark.asyncio
async def test_get_security_metrics_success(mock_current_user, mock_audit_service):
    """Test successful retrieval of security metrics."""
    # Arrange
    mock_metrics = SecurityMetrics(
        total_events=1000,
        events_by_type={"login_success": 800, "login_failed": 200},
        events_by_severity={"INFO": 800, "WARNING": 150, "ERROR": 50},
        recent_anomalies=5,
        top_users_by_events=[],
        events_by_hour=[],
    )
    mock_audit_service.get_metrics = AsyncMock(return_value=mock_metrics)

    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service_class.return_value = mock_audit_service

        from app.api.v1.endpoints.security.audit import get_security_metrics

        # Act
        result = await get_security_metrics(
            current_user=mock_current_user,
            db=Mock()
        )

        # Assert
        assert result == mock_metrics
        mock_audit_service.get_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_detect_user_anomalies_success(mock_current_user, mock_audit_service):
    """Test successful user anomaly detection."""
    # Arrange
    user_id = str(uuid4())
    mock_anomalies = [
        {"type": "unusual_login_time", "severity": "medium", "details": "Login at 3 AM"}
    ]
    mock_audit_service.detect_anomalies = AsyncMock(return_value=mock_anomalies)

    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service_class.return_value = mock_audit_service

        from app.api.v1.endpoints.security.audit import detect_user_anomalies

        # Act
        result = await detect_user_anomalies(
            user_id=user_id,
            current_user=mock_current_user,
            db=Mock()
        )

        # Assert
        assert result == mock_anomalies
        mock_audit_service.detect_anomalies.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_my_security_logs_success(mock_current_user, mock_audit_service, sample_audit_log_response):
    """Test successful retrieval of user's own security logs."""
    # Arrange
    mock_audit_service.get_logs = AsyncMock(return_value=[sample_audit_log_response])

    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service_class.return_value = mock_audit_service

        from app.api.v1.endpoints.security.audit import get_my_security_logs

        # Act
        result = await get_my_security_logs(
            limit=50,
            offset=0,
            current_user=mock_current_user,
            db=Mock()
        )

        # Assert
        assert result == [sample_audit_log_response]
        mock_audit_service.get_logs.assert_called_once()


@pytest.mark.asyncio
async def test_get_security_logs_with_filters(mock_current_user, mock_audit_service):
    """Test security logs retrieval with various filters."""
    # Arrange
    mock_audit_service.get_logs = AsyncMock(return_value=[])

    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service_class.return_value = mock_audit_service

        from app.api.v1.endpoints.security.audit import get_security_logs

        # Act
        await get_security_logs(
            event_type=SecurityEventType.LOGIN_FAILED,
            severity=SecuritySeverity.WARNING,
            user_id=str(uuid4()),
            start_date=datetime.now(),
            end_date=datetime.now(),
            limit=100,
            offset=10,
            current_user=mock_current_user,
            db=Mock()
        )

        # Assert
        mock_audit_service.get_logs.assert_called_once()
        call_args = mock_audit_service.get_logs.call_args[0][0]
        assert hasattr(call_args, 'event_type')
        assert hasattr(call_args, 'severity')
        assert hasattr(call_args, 'user_id')
        assert call_args.limit == 100
        assert call_args.offset == 10


@pytest.mark.asyncio
async def test_audit_service_exception_handling(mock_current_user, mock_audit_service):
    """Test proper exception handling from audit service."""
    # Arrange
    mock_audit_service.get_logs = AsyncMock(side_effect=Exception("Database error"))

    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service_class.return_value = mock_audit_service

        from app.api.v1.endpoints.security.audit import get_security_logs

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await get_security_logs(
                event_type=None,
                severity=None,
                user_id=None,
                start_date=None,
                end_date=None,
                limit=50,
                offset=0,
                current_user=mock_current_user,
                db=Mock()
            )


@pytest.mark.asyncio
async def test_security_audit_log_validation():
    """Test security audit log data validation."""
    # Valid log data
    valid_log = SecurityAuditLogCreate(
        event_type=SecurityEventType.LOGIN_SUCCESS,
        severity=SecuritySeverity.INFO,
        user_id=str(uuid4()),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        event_data={"source": "web"},
    )

    assert valid_log.event_type == SecurityEventType.LOGIN_SUCCESS
    assert valid_log.severity == SecuritySeverity.INFO
    assert valid_log.ip_address == "192.168.1.1"


@pytest.mark.asyncio
async def test_pagination_parameters():
    """Test pagination parameter validation."""
    from app.api.v1.endpoints.security.audit import get_security_logs

    # Test with valid pagination
    with patch('app.api.v1.endpoints.security.audit.SecurityAuditService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_logs = AsyncMock(return_value=[])
        mock_service_class.return_value = mock_service

        await get_security_logs(
            event_type=None,
            severity=None,
            user_id=None,
            start_date=None,
            end_date=None,
            limit=100,
            offset=0,
            current_user=mock_current_user(),
            db=Mock()
        )

        # Verify pagination parameters are passed correctly
        call_args = mock_service.get_logs.call_args[0][0]
        assert call_args.limit == 100
        assert call_args.offset == 0
