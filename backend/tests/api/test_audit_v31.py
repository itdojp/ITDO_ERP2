"""
Tests for Audit Log System API - CC02 v31.0 Phase 2

Comprehensive test suite for audit log management including:
- System-wide Activity Tracking
- Compliance & Regulatory Auditing
- Security Event Monitoring
- Data Change Tracking
- User Action Logging
- Performance Monitoring
- Risk Assessment & Alerting
- Forensic Analysis Support
- Real-time Monitoring
- Automated Compliance Reporting

Tests 8 main endpoint groups with 80+ individual endpoints
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.audit_v31 import router
from app.main import app
from app.models.audit_extended import (
    AuditLogEntry,
    AuditRule,
    AuditAlert,
    AuditReport,
    AuditSession,
    AuditCompliance,
    AuditMetrics,
    AuditEventType,
    AuditSeverity,
    AuditStatus,
    ComplianceFramework,
)


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_audit_service():
    """Mock audit service fixture."""
    return Mock()


@pytest.fixture
def sample_audit_log_entry():
    """Sample audit log entry for testing."""
    return AuditLogEntry(
        id="entry-123",
        organization_id="org-123",
        event_type=AuditEventType.LOGIN,
        event_category="authentication",
        event_name="User Login",
        event_description="User successfully logged in",
        user_id="user-123",
        actor_type="user",
        actor_name="John Doe",
        resource_type="user_session",
        resource_id="session-123",
        action_performed="login",
        outcome="success",
        severity=AuditSeverity.LOW,
        old_values={},
        new_values={"session_created": True},
        change_details={"login_method": "password"},
        event_data={"user_agent": "Mozilla/5.0"},
        session_id="sess-123",
        correlation_id="corr-123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        source_system="web_app",
        compliance_frameworks=["sox", "gdpr"],
        risk_score=10,
        tags=["authentication", "login"],
        status=AuditStatus.ACTIVE,
        event_timestamp=datetime.now(),
        created_at=datetime.now()
    )


@pytest.fixture
def sample_audit_rule():
    """Sample audit rule for testing."""
    return AuditRule(
        id="rule-123",
        organization_id="org-123",
        name="Failed Login Attempts",
        description="Detect multiple failed login attempts",
        rule_type="threshold",
        conditions={
            "event_type": "login_failed",
            "threshold": 5,
            "time_window": 300
        },
        event_filters={"outcome": "failure"},
        threshold_config={"max_attempts": 5, "window_seconds": 300},
        actions=["log", "alert", "email"],
        alert_severity=AuditSeverity.HIGH,
        compliance_frameworks=["sox", "iso27001"],
        regulatory_requirements=["access_control"],
        is_active=True,
        priority=80,
        evaluation_frequency="real_time",
        trigger_count=15,
        last_triggered=datetime.now() - timedelta(hours=1),
        false_positive_count=2,
        created_at=datetime.now(),
        created_by="user-123"
    )


@pytest.fixture
def sample_audit_alert():
    """Sample audit alert for testing."""
    return AuditAlert(
        id="alert-123",
        organization_id="org-123",
        rule_id="rule-123",
        alert_type="threshold_exceeded",
        title="Multiple Failed Login Attempts Detected",
        description="User attempted to login 5 times with incorrect credentials",
        severity=AuditSeverity.HIGH,
        triggering_event_ids=["entry-1", "entry-2", "entry-3"],
        event_count=5,
        alert_data={"user_id": "user-456", "ip_address": "192.168.1.100"},
        risk_assessment={"risk_level": "high", "confidence": 0.9},
        recommended_actions=["lock_account", "investigate"],
        status="open",
        assigned_to="admin-123",
        priority=80,
        escalation_level=0,
        escalated_to=[],
        compliance_impact="security_breach",
        regulatory_notification_required=True,
        notification_sent=False,
        first_occurrence=datetime.now() - timedelta(minutes=10),
        last_occurrence=datetime.now(),
        created_at=datetime.now()
    )


@pytest.fixture
def sample_audit_report():
    """Sample audit report for testing."""
    return AuditReport(
        id="report-123",
        organization_id="org-123",
        report_name="Monthly Security Report",
        report_type="security",
        description="Monthly security assessment report",
        period_start=date.today() - timedelta(days=30),
        period_end=date.today(),
        report_filters={"severity": ["high", "critical"]},
        report_config={"include_trends": True},
        compliance_framework=ComplianceFramework.SOX,
        regulatory_requirements=["access_control", "data_protection"],
        executive_summary="Security posture remains strong",
        findings=[{"type": "security_gap", "description": "Weak password policy"}],
        recommendations=[{"action": "enforce_strong_passwords", "priority": "high"}],
        metrics={"total_events": 1000, "security_events": 50},
        total_events=1000,
        critical_events=5,
        violations=3,
        compliance_score=Decimal("95.5"),
        file_path="/reports/security_report_123.pdf",
        file_format="pdf",
        file_size=2048000,
        generated_by="admin-123",
        generation_status="completed",
        generation_progress=100,
        recipients=["admin@company.com"],
        retention_period_days=2555,
        is_archived=False,
        created_at=datetime.now(),
        completed_at=datetime.now()
    )


@pytest.fixture
def sample_audit_session():
    """Sample audit session for testing."""
    return AuditSession(
        id="session-123",
        organization_id="org-123",
        user_id="user-123",
        session_token="token-abc123",
        session_type="web",
        authentication_method="password",
        mfa_verified=True,
        authentication_factors=["password", "totp"],
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        device_fingerprint="fp-123",
        geolocation={"country": "US", "city": "New York"},
        is_active=True,
        last_activity=datetime.now(),
        inactivity_duration=0,
        suspicious_activity_count=0,
        failed_action_count=0,
        risk_score=25,
        actions_performed=50,
        data_accessed=["users", "reports"],
        permissions_used=["read", "export"],
        started_at=datetime.now() - timedelta(hours=2),
        created_at=datetime.now() - timedelta(hours=2)
    )


# =============================================================================
# Audit Log Entry Management Tests
# =============================================================================

class TestAuditLogEntryManagement:
    """Test audit log entry management endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_create_audit_log_entry_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful audit log entry creation."""
        mock_service = Mock()
        mock_service.create_audit_log_entry = AsyncMock(return_value=sample_audit_log_entry)
        mock_get_service.return_value = mock_service

        entry_data = {
            "organization_id": "org-123",
            "event_type": "login",
            "event_category": "authentication",
            "event_name": "User Login",
            "event_description": "User successfully logged in",
            "user_id": "user-123",
            "actor_type": "user",
            "resource_type": "user_session",
            "action_performed": "login",
            "outcome": "success",
            "severity": "low"
        }

        response = client.post("/logs", json=entry_data)
        assert response.status_code == 200
        data = response.json()
        assert data["event_name"] == "User Login"
        assert data["event_type"] == "login"
        mock_service.create_audit_log_entry.assert_called_once()

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_create_audit_log_entry_failure(self, mock_get_service, client):
        """Test audit log entry creation failure."""
        mock_service = Mock()
        mock_service.create_audit_log_entry = AsyncMock(side_effect=Exception("Creation failed"))
        mock_get_service.return_value = mock_service

        entry_data = {
            "organization_id": "org-123",
            "event_type": "login",
            "event_category": "authentication",
            "event_name": "User Login"
        }

        response = client.post("/logs", json=entry_data)
        assert response.status_code == 400
        assert "Failed to create audit log entry" in response.json()["detail"]

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_bulk_create_audit_entries_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful bulk audit entries creation."""
        mock_service = Mock()
        mock_service.bulk_create_audit_entries = AsyncMock(return_value=[sample_audit_log_entry])
        mock_get_service.return_value = mock_service

        bulk_data = {
            "entries": [
                {
                    "organization_id": "org-123",
                    "event_type": "login",
                    "event_category": "authentication",
                    "event_name": "User Login"
                }
            ]
        }

        response = client.post("/logs/bulk", json=bulk_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["event_name"] == "User Login"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_search_audit_logs_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful audit logs search."""
        mock_service = Mock()
        mock_service.search_audit_logs = AsyncMock(return_value=([sample_audit_log_entry], 1))
        mock_get_service.return_value = mock_service

        search_request = {
            "organization_id": "org-123",
            "event_type": "login",
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "page": 1,
            "per_page": 50
        }

        response = client.post("/logs/search", json=search_request)
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["entries"]) == 1
        assert data["entries"][0]["event_name"] == "User Login"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_audit_log_entry_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful audit log entry retrieval."""
        mock_service = Mock()
        mock_service.get_audit_log_entry = AsyncMock(return_value=sample_audit_log_entry)
        mock_get_service.return_value = mock_service

        response = client.get("/logs/entry-123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "entry-123"
        assert data["event_name"] == "User Login"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_audit_log_entry_not_found(self, mock_get_service, client):
        """Test audit log entry not found."""
        mock_service = Mock()
        mock_service.get_audit_log_entry = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = client.get("/logs/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_update_audit_log_status_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful audit log status update."""
        mock_service = Mock()
        mock_service.update_audit_log_status = AsyncMock(return_value=sample_audit_log_entry)
        mock_get_service.return_value = mock_service

        response = client.put("/logs/entry-123/status?status=acknowledged&acknowledged_by=user-123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "entry-123"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_recent_audit_logs_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful recent audit logs retrieval."""
        mock_service = Mock()
        mock_service.search_audit_logs = AsyncMock(return_value=([sample_audit_log_entry], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/logs/recent?organization_id=org-123&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["entries"]) == 1

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_user_audit_logs_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful user audit logs retrieval."""
        mock_service = Mock()
        mock_service.search_audit_logs = AsyncMock(return_value=([sample_audit_log_entry], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/logs/user/user-123?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_resource_audit_logs_success(self, mock_get_service, client, sample_audit_log_entry):
        """Test successful resource audit logs retrieval."""
        mock_service = Mock()
        mock_service.search_audit_logs = AsyncMock(return_value=([sample_audit_log_entry], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/logs/resource/user_session/session-123?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_audit_log_statistics_success(self, mock_get_service, client):
        """Test successful audit log statistics retrieval."""
        mock_service = Mock()
        mock_service.search_audit_logs = AsyncMock(return_value=([], 1000))
        mock_get_service.return_value = mock_service

        response = client.get("/logs/statistics?organization_id=org-123&period_days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 1000
        assert data["period_days"] == 30


# =============================================================================
# Audit Rules Management Tests
# =============================================================================

class TestAuditRulesManagement:
    """Test audit rules management endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_create_audit_rule_success(self, mock_get_service, client, sample_audit_rule):
        """Test successful audit rule creation."""
        mock_service = Mock()
        mock_service.create_audit_rule = AsyncMock(return_value=sample_audit_rule)
        mock_get_service.return_value = mock_service

        rule_data = {
            "organization_id": "org-123",
            "name": "Failed Login Attempts",
            "description": "Detect multiple failed login attempts",
            "rule_type": "threshold",
            "conditions": {
                "event_type": "login_failed",
                "threshold": 5
            },
            "actions": ["log", "alert"],
            "alert_severity": "high",
            "created_by": "user-123"
        }

        response = client.post("/rules", json=rule_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Failed Login Attempts"
        assert data["rule_type"] == "threshold"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_list_audit_rules_success(self, mock_get_service, client, sample_audit_rule):
        """Test successful audit rules listing."""
        mock_service = Mock()
        mock_service.list_audit_rules = AsyncMock(return_value=([sample_audit_rule], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/rules?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["rules"]) == 1
        assert data["rules"][0]["name"] == "Failed Login Attempts"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_test_audit_rule_success(self, mock_get_service, client):
        """Test successful audit rule testing."""
        mock_service = Mock()
        mock_service.test_audit_rule = AsyncMock(return_value={
            "success": True,
            "triggered": True,
            "matched_conditions": ["event_type", "threshold"],
            "alert_would_generate": True
        })
        mock_get_service.return_value = mock_service

        test_data = {
            "test_data": {
                "event_type": "login_failed",
                "user_id": "user-123",
                "failure_count": 6
            }
        }

        response = client.post("/rules/rule-123/test", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["triggered"] is True

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_validate_rule_conditions_success(self, mock_get_service, client):
        """Test successful rule conditions validation."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        conditions = {
            "event_type": "security_violation",
            "severity": "high"
        }

        response = client.post("/rules/validate", json=conditions)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


# =============================================================================
# Audit Alerts Management Tests
# =============================================================================

class TestAuditAlertsManagement:
    """Test audit alerts management endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_create_audit_alert_success(self, mock_get_service, client, sample_audit_alert):
        """Test successful audit alert creation."""
        mock_service = Mock()
        mock_service.create_audit_alert = AsyncMock(return_value=sample_audit_alert)
        mock_get_service.return_value = mock_service

        alert_data = {
            "organization_id": "org-123",
            "rule_id": "rule-123",
            "alert_type": "threshold_exceeded",
            "title": "Multiple Failed Login Attempts",
            "severity": "high",
            "triggering_event_ids": ["entry-1", "entry-2"]
        }

        response = client.post("/alerts", json=alert_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Multiple Failed Login Attempts Detected"
        assert data["severity"] == "high"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_list_audit_alerts_success(self, mock_get_service, client, sample_audit_alert):
        """Test successful audit alerts listing."""
        mock_service = Mock()
        mock_service.list_audit_alerts = AsyncMock(return_value=([sample_audit_alert], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/alerts?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["title"] == "Multiple Failed Login Attempts Detected"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_resolve_alert_success(self, mock_get_service, client, sample_audit_alert):
        """Test successful alert resolution."""
        mock_service = Mock()
        mock_service.resolve_alert = AsyncMock(return_value=sample_audit_alert)
        mock_get_service.return_value = mock_service

        resolution_data = {
            "resolved_by": "admin-123",
            "resolution_notes": "False positive - legitimate user"
        }

        response = client.post("/alerts/alert-123/resolve", json=resolution_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "alert-123"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_active_alerts_success(self, mock_get_service, client, sample_audit_alert):
        """Test successful active alerts retrieval."""
        mock_service = Mock()
        mock_service.list_audit_alerts = AsyncMock(return_value=([sample_audit_alert], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/alerts/active?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_my_alerts_success(self, mock_get_service, client, sample_audit_alert):
        """Test successful user alerts retrieval."""
        mock_service = Mock()
        mock_service.list_audit_alerts = AsyncMock(return_value=([sample_audit_alert], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/alerts/my-alerts?user_id=admin-123&organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_alerts_summary_success(self, mock_get_service, client):
        """Test successful alerts summary retrieval."""
        mock_service = Mock()
        mock_service.list_audit_alerts = AsyncMock(return_value=([], 5))
        mock_get_service.return_value = mock_service

        response = client.get("/alerts/summary?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["active_alerts"] == 5
        assert data["organization_id"] == "org-123"


# =============================================================================
# Audit Reports Management Tests
# =============================================================================

class TestAuditReportsManagement:
    """Test audit reports management endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_generate_audit_report_success(self, mock_get_service, client, sample_audit_report):
        """Test successful audit report generation."""
        mock_service = Mock()
        mock_service.generate_audit_report = AsyncMock(return_value=sample_audit_report)
        mock_get_service.return_value = mock_service

        report_data = {
            "organization_id": "org-123",
            "report_name": "Monthly Security Report",
            "report_type": "security",
            "period_start": str(date.today() - timedelta(days=30)),
            "period_end": str(date.today()),
            "file_format": "pdf",
            "generated_by": "admin-123"
        }

        response = client.post("/reports", json=report_data)
        assert response.status_code == 200
        data = response.json()
        assert data["report_name"] == "Monthly Security Report"
        assert data["report_type"] == "security"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_list_audit_reports_success(self, mock_get_service, client, sample_audit_report):
        """Test successful audit reports listing."""
        mock_service = Mock()
        mock_service.list_audit_reports = AsyncMock(return_value=([sample_audit_report], 1))
        mock_get_service.return_value = mock_service

        response = client.get("/reports?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["reports"]) == 1
        assert data["reports"][0]["report_name"] == "Monthly Security Report"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_report_templates_success(self, mock_get_service, client):
        """Test successful report templates retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/reports/templates?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0


# =============================================================================
# Session Tracking Tests
# =============================================================================

class TestSessionTracking:
    """Test session tracking endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_create_audit_session_success(self, mock_get_service, client, sample_audit_session):
        """Test successful audit session creation."""
        mock_service = Mock()
        mock_service.create_audit_session = AsyncMock(return_value=sample_audit_session)
        mock_get_service.return_value = mock_service

        session_data = {
            "organization_id": "org-123",
            "user_id": "user-123",
            "session_token": "token-abc123",
            "session_type": "web",
            "authentication_method": "password",
            "ip_address": "192.168.1.1"
        }

        response = client.post("/sessions", json=session_data)
        assert response.status_code == 200
        data = response.json()
        assert data["session_token"] == "token-abc123"
        assert data["session_type"] == "web"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_update_session_activity_success(self, mock_get_service, client, sample_audit_session):
        """Test successful session activity update."""
        mock_service = Mock()
        mock_service.update_session_activity = AsyncMock(return_value=sample_audit_session)
        mock_get_service.return_value = mock_service

        response = client.put("/sessions/token-abc123/activity")
        assert response.status_code == 200
        data = response.json()
        assert data["session_token"] == "token-abc123"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_terminate_session_success(self, mock_get_service, client, sample_audit_session):
        """Test successful session termination."""
        mock_service = Mock()
        sample_audit_session.is_active = False
        sample_audit_session.ended_at = datetime.now()
        mock_service.terminate_session = AsyncMock(return_value=sample_audit_session)
        mock_get_service.return_value = mock_service

        response = client.post("/sessions/token-abc123/terminate?reason=user_logout")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_active_sessions_success(self, mock_get_service, client):
        """Test successful active sessions retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/sessions/active?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert "active_sessions" in data

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_session_statistics_success(self, mock_get_service, client):
        """Test successful session statistics retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/sessions/statistics?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "active_sessions" in data


# =============================================================================
# Compliance Management Tests
# =============================================================================

class TestComplianceManagement:
    """Test compliance management endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_create_compliance_assessment_success(self, mock_get_service, client):
        """Test successful compliance assessment creation."""
        mock_service = Mock()
        mock_assessment = Mock()
        mock_assessment.__dict__ = {
            "id": "assessment-123",
            "organization_id": "org-123",
            "framework": "sox",
            "requirement_name": "Access Control",
            "compliance_status": "compliant",
            "created_at": datetime.now()
        }
        mock_service.create_compliance_assessment = AsyncMock(return_value=mock_assessment)
        mock_get_service.return_value = mock_service

        assessment_data = {
            "organization_id": "org-123",
            "framework": "sox",
            "requirement_id": "AC-001",
            "requirement_name": "Access Control",
            "assessment_period_start": str(date.today() - timedelta(days=30)),
            "assessment_period_end": str(date.today()),
            "compliance_status": "compliant"
        }

        response = client.post("/compliance/assessments", json=assessment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["framework"] == "sox"
        assert data["requirement_name"] == "Access Control"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_compliance_dashboard_success(self, mock_get_service, client):
        """Test successful compliance dashboard retrieval."""
        mock_service = Mock()
        mock_service.get_compliance_dashboard = AsyncMock(return_value={
            "overall_compliance_rate": 95.5,
            "total_assessments": 100,
            "compliant_assessments": 95,
            "framework_statistics": {},
            "overdue_assessments": 5,
            "last_updated": datetime.now().isoformat()
        })
        mock_get_service.return_value = mock_service

        response = client.get("/compliance/dashboard?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_compliance_rate"] == 95.5
        assert data["total_assessments"] == 100

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_compliance_frameworks_success(self, mock_get_service, client):
        """Test successful compliance frameworks retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/compliance/frameworks")
        assert response.status_code == 200
        data = response.json()
        assert "frameworks" in data
        assert len(data["frameworks"]) > 0
        
        # Check that SOX framework is included
        sox_framework = next((f for f in data["frameworks"] if f["code"] == "sox"), None)
        assert sox_framework is not None
        assert sox_framework["name"] == "Sarbanes-Oxley Act"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_compliance_gaps_success(self, mock_get_service, client):
        """Test successful compliance gaps retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/compliance/gaps?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert "gaps" in data
        assert "total_gaps" in data


# =============================================================================
# Analytics and Dashboards Tests
# =============================================================================

class TestAnalyticsDashboards:
    """Test analytics and dashboards endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_security_dashboard_success(self, mock_get_service, client):
        """Test successful security dashboard retrieval."""
        mock_service = Mock()
        mock_service.get_security_dashboard = AsyncMock(return_value={
            "security_events_week": 25,
            "active_alerts": 5,
            "high_risk_sessions": 2,
            "failed_logins_24h": 10,
            "security_score": 85,
            "last_updated": datetime.now().isoformat()
        })
        mock_get_service.return_value = mock_service

        response = client.get("/analytics/security-dashboard?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["security_events_week"] == 25
        assert data["security_score"] == 85

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_generate_audit_metrics_success(self, mock_get_service, client):
        """Test successful audit metrics generation."""
        mock_service = Mock()
        mock_metrics = Mock()
        mock_metrics.__dict__ = {
            "organization_id": "org-123",
            "period_start": datetime.now() - timedelta(days=7),
            "period_end": datetime.now(),
            "period_type": "daily",
            "total_events": 1000,
            "events_by_type": {"login": 500, "logout": 300},
            "events_by_severity": {"low": 800, "medium": 150, "high": 50},
            "failed_events": 25,
            "total_alerts": 10,
            "alerts_by_severity": {"high": 5, "medium": 3, "low": 2},
            "active_users": 50,
            "calculated_at": datetime.now()
        }
        mock_service.generate_audit_metrics = AsyncMock(return_value=mock_metrics)
        mock_get_service.return_value = mock_service

        period_start = (datetime.now() - timedelta(days=7)).isoformat()
        period_end = datetime.now().isoformat()

        response = client.post(f"/analytics/metrics?organization_id=org-123&period_start={period_start}&period_end={period_end}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 1000
        assert data["total_alerts"] == 10

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_audit_trends_success(self, mock_get_service, client):
        """Test successful audit trends retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/analytics/trends?organization_id=org-123&metric_type=events")
        assert response.status_code == 200
        data = response.json()
        assert "trend_data" in data
        assert data["metric_type"] == "events"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_risk_assessment_success(self, mock_get_service, client):
        """Test successful risk assessment retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/analytics/risk-assessment?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert "overall_risk_score" in data
        assert "risk_categories" in data


# =============================================================================
# Data Export and Archival Tests
# =============================================================================

class TestDataExportArchival:
    """Test data export and archival endpoints."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_export_audit_data_success(self, mock_get_service, client):
        """Test successful audit data export."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        export_request = {
            "organization_id": "org-123",
            "export_type": "audit_logs",
            "format": "csv",
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat()
        }

        response = client.post("/export", json=export_request)
        assert response.status_code == 200
        data = response.json()
        assert data["export_id"] == "exp-123"
        assert data["status"] == "completed"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_get_export_status_success(self, mock_get_service, client):
        """Test successful export status retrieval."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        response = client.get("/export/exp-123/status")
        assert response.status_code == 200
        data = response.json()
        assert data["export_id"] == "exp-123"
        assert data["status"] == "completed"

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_execute_retention_policy_success(self, mock_get_service, client):
        """Test successful retention policy execution."""
        mock_service = Mock()
        mock_service.execute_retention_policy = AsyncMock(return_value={
            "success": True,
            "records_processed": 1000,
            "records_archived": 800,
            "records_deleted": 200
        })
        mock_get_service.return_value = mock_service

        response = client.post("/retention/execute/policy-123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["records_processed"] == 1000

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_create_archive_success(self, mock_get_service, client):
        """Test successful archive creation."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        archive_criteria = {
            "older_than_days": 365,
            "event_types": ["login", "logout"]
        }

        response = client.post(f"/archive/create?organization_id=org-123&archive_criteria={archive_criteria}")
        assert response.status_code == 200
        data = response.json()
        assert "archive_id" in data
        assert data["status"] == "creating"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_service_error_handling(self, mock_get_service, client):
        """Test service error handling."""
        mock_service = Mock()
        mock_service.get_audit_log_entry = AsyncMock(side_effect=Exception("Service error"))
        mock_get_service.return_value = mock_service

        response = client.get("/logs/entry-123")
        assert response.status_code == 400
        assert "Failed to get audit log entry" in response.json()["detail"]

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_not_found_error_handling(self, mock_get_service, client):
        """Test not found error handling."""
        mock_service = Mock()
        mock_service.update_session_activity = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        response = client.put("/sessions/nonexistent/activity")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_validation_error_handling(self, client):
        """Test validation error handling."""
        # Test with missing required fields
        response = client.post("/logs", json={})
        assert response.status_code == 422  # Unprocessable Entity

    def test_query_parameter_validation(self, client):
        """Test query parameter validation."""
        # Test with invalid page number
        response = client.get("/logs/recent?organization_id=org-123&limit=0")
        assert response.status_code == 422  # Unprocessable Entity


# =============================================================================
# Integration Tests
# =============================================================================

class TestAuditIntegration:
    """Test audit system integration scenarios."""

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_complete_audit_workflow(self, mock_get_service, client, sample_audit_log_entry, sample_audit_alert):
        """Test complete audit workflow from entry to alert."""
        mock_service = Mock()
        
        # Mock sequential operations
        mock_service.create_audit_log_entry = AsyncMock(return_value=sample_audit_log_entry)
        mock_service.list_audit_alerts = AsyncMock(return_value=([sample_audit_alert], 1))
        mock_service.resolve_alert = AsyncMock(return_value=sample_audit_alert)
        
        mock_get_service.return_value = mock_service

        # 1. Create audit log entry
        entry_data = {
            "organization_id": "org-123",
            "event_type": "login_failed",
            "event_category": "authentication",
            "event_name": "Failed Login Attempt",
            "severity": "high"
        }
        
        response = client.post("/logs", json=entry_data)
        assert response.status_code == 200

        # 2. Check for alerts
        response = client.get("/alerts/active?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

        # 3. Resolve alert
        resolution_data = {
            "resolved_by": "admin-123",
            "resolution_notes": "Investigated and resolved"
        }
        
        response = client.post("/alerts/alert-123/resolve", json=resolution_data)
        assert response.status_code == 200

    @patch('app.api.v1.audit_v31.get_audit_service')
    def test_compliance_assessment_workflow(self, mock_get_service, client):
        """Test compliance assessment workflow."""
        mock_service = Mock()
        
        # Mock assessment creation
        mock_assessment = Mock()
        mock_assessment.__dict__ = {
            "id": "assessment-123",
            "framework": "sox",
            "compliance_status": "compliant",
            "created_at": datetime.now()
        }
        mock_service.create_compliance_assessment = AsyncMock(return_value=mock_assessment)
        
        # Mock dashboard data
        mock_service.get_compliance_dashboard = AsyncMock(return_value={
            "overall_compliance_rate": 95.0,
            "total_assessments": 1,
            "compliant_assessments": 1,
            "framework_statistics": {},
            "overdue_assessments": 0,
            "last_updated": datetime.now().isoformat()
        })
        
        mock_get_service.return_value = mock_service

        # Create assessment
        assessment_data = {
            "organization_id": "org-123",
            "framework": "sox",
            "requirement_id": "AC-001",
            "requirement_name": "Access Control",
            "assessment_period_start": str(date.today() - timedelta(days=30)),
            "assessment_period_end": str(date.today()),
            "compliance_status": "compliant"
        }
        
        response = client.post("/compliance/assessments", json=assessment_data)
        assert response.status_code == 200

        # Check dashboard
        response = client.get("/compliance/dashboard?organization_id=org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_compliance_rate"] == 95.0


if __name__ == "__main__":
    pytest.main([__file__])