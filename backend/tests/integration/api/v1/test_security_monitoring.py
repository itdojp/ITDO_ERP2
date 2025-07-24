"""Security monitoring API integration tests for Issue #46."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User
from app.services.security_monitoring import SecurityMonitoringService, SecurityThreat


class TestSecurityMonitoringAPI:
    """Test security monitoring API endpoints."""

    def test_get_security_dashboard_success(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test security dashboard retrieval."""
        response = client.get(
            "/api/v1/security-monitoring/dashboard",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "threats" in data
        assert "metrics" in data
        assert "monitoring_status" in data

        # Check threat statistics structure
        assert "total" in data["threats"]
        assert "critical" in data["threats"]
        assert "high" in data["threats"]
        assert "medium" in data["threats"]
        assert "low" in data["threats"]
        assert "recent_threats" in data["threats"]

    def test_get_security_dashboard_forbidden(
        self, client: TestClient, user_token_headers: dict
    ):
        """Test security dashboard access denied for regular users."""
        response = client.get(
            "/api/v1/security-monitoring/dashboard",
            headers=user_token_headers,
        )
        assert response.status_code == 403

    def test_get_current_threats_success(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test current threats retrieval."""
        response = client.get(
            "/api/v1/security-monitoring/threats",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "threats" in data
        assert "total_count" in data
        assert "filters_applied" in data

    def test_get_current_threats_with_filters(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        test_user: User,
        db: Session,
    ):
        """Test current threats retrieval with filters."""
        response = client.get(
            f"/api/v1/security-monitoring/threats?user_id={test_user.id}&severity=high",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["filters_applied"]["user_id"] == test_user.id
        assert data["filters_applied"]["severity"] == "high"

    def test_monitor_failed_logins_success(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test failed login monitoring."""
        response = client.get(
            "/api/v1/security-monitoring/failed-logins",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "failed_login_threats" in data
        assert "monitoring_config" in data
        assert "threshold" in data["monitoring_config"]
        assert "time_window" in data["monitoring_config"]

    def test_monitor_bulk_access_success(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test bulk access monitoring."""
        response = client.get(
            "/api/v1/security-monitoring/bulk-access",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "bulk_access_threats" in data
        assert "monitoring_config" in data

    def test_monitor_privilege_escalation_success(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test privilege escalation monitoring."""
        response = client.get(
            "/api/v1/security-monitoring/privilege-escalation",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "privilege_escalation_threats" in data
        assert "monitoring_enabled" in data

    def test_generate_security_report_success(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test security report generation."""
        response = client.get(
            "/api/v1/security-monitoring/reports/security",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "report_period" in data
        assert "summary" in data
        assert "top_activities" in data
        assert "security_insights" in data

    def test_generate_security_report_with_dates(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test security report generation with custom date range."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()

        response = client.get(
            f"/api/v1/security-monitoring/reports/security?start_date={start_date}&end_date={end_date}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["report_period"]["start_date"].startswith(start_date[:10])

    def test_get_monitoring_status_success(
        self, client: TestClient, user_token_headers: dict, db: Session
    ):
        """Test monitoring status retrieval."""
        response = client.get(
            "/api/v1/security-monitoring/status",
            headers=user_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "monitoring_active" in data
        assert "service_status" in data
        assert "features" in data
        assert "thresholds" in data
        assert "timestamp" in data

    def test_test_security_alert_success(
        self, client: TestClient, superuser_token_headers: dict, db: Session
    ):
        """Test security alert testing."""
        response = client.post(
            "/api/v1/security-monitoring/alerts/test",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    def test_test_security_alert_forbidden(
        self, client: TestClient, user_token_headers: dict
    ):
        """Test security alert testing forbidden for regular users."""
        response = client.post(
            "/api/v1/security-monitoring/alerts/test",
            headers=user_token_headers,
        )
        assert response.status_code == 403


class TestSecurityMonitoringService:
    """Test security monitoring service functionality."""

    def test_monitor_failed_logins_detection(self, db: Session, test_user: User):
        """Test failed login threat detection."""
        service = SecurityMonitoringService(db)

        # Create multiple failed login attempts
        for i in range(6):  # Above threshold of 5
            audit_log = AuditLog(
                user_id=test_user.id,
                action="login_failed",
                resource_type="authentication",
                resource_id=0,
                organization_id=test_user.organization_id,
                changes={},
                ip_address="192.168.1.100",
                created_at=datetime.now(timezone.utc) - timedelta(minutes=i),
            )
            db.add(audit_log)
        db.commit()

        # Monitor should detect threat
        threats = service.monitor_failed_logins(test_user.id)
        assert len(threats) > 0
        assert threats[0].threat_type == "brute_force_attack"
        assert threats[0].severity in [SecurityThreat.MEDIUM, SecurityThreat.HIGH]

    def test_monitor_bulk_access_detection(self, db: Session, test_user: User):
        """Test bulk access threat detection."""
        service = SecurityMonitoringService(db)

        # Create bulk access attempts
        for i in range(150):  # Above threshold of 100
            audit_log = AuditLog(
                user_id=test_user.id,
                action="read",
                resource_type="data",
                resource_id=i,
                organization_id=test_user.organization_id,
                changes={},
                created_at=datetime.now(timezone.utc) - timedelta(seconds=i),
            )
            db.add(audit_log)
        db.commit()

        # Monitor should detect threat
        threats = service.monitor_bulk_data_access(test_user.id)
        assert len(threats) > 0
        assert threats[0].threat_type == "bulk_data_access"
        assert threats[0].severity in [SecurityThreat.HIGH, SecurityThreat.CRITICAL]

    def test_monitor_privilege_escalation_detection(self, db: Session, test_user: User):
        """Test privilege escalation threat detection."""
        service = SecurityMonitoringService(db)

        # Create multiple privilege changes
        for action in ["permission_grant", "role_change"]:
            audit_log = AuditLog(
                user_id=test_user.id,
                action=action,
                resource_type="user_permissions",
                resource_id=test_user.id,
                organization_id=test_user.organization_id,
                changes={"new_permission": "admin"},
                created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            db.add(audit_log)
        db.commit()

        # Monitor should detect threat
        threats = service.monitor_privilege_escalation(test_user.id)
        assert len(threats) > 0
        assert threats[0].threat_type == "privilege_escalation"
        assert threats[0].severity == SecurityThreat.HIGH

    def test_monitor_unusual_access_patterns(self, db: Session, test_user: User):
        """Test unusual access pattern detection."""
        service = SecurityMonitoringService(db)

        # Create logins from multiple IPs
        ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.1"]
        for i, ip in enumerate(ips):
            audit_log = AuditLog(
                user_id=test_user.id,
                action="login_success",
                resource_type="authentication",
                resource_id=0,
                organization_id=test_user.organization_id,
                changes={},
                ip_address=ip,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=i * 10),
            )
            db.add(audit_log)
        db.commit()

        # Monitor should detect threat
        threats = service.monitor_unusual_access_patterns(test_user.id)
        assert len(threats) > 0
        assert threats[0].threat_type == "unusual_access_pattern"
        assert threats[0].severity == SecurityThreat.MEDIUM

    def test_get_security_dashboard(self, db: Session, test_user: User):
        """Test security dashboard data generation."""
        service = SecurityMonitoringService(db)

        # Create some audit logs
        audit_log = AuditLog(
            user_id=test_user.id,
            action="login_success",
            resource_type="authentication",
            resource_id=0,
            organization_id=test_user.organization_id,
            changes={},
            created_at=datetime.now(timezone.utc),
        )
        db.add(audit_log)
        db.commit()

        dashboard = service.get_security_dashboard(test_user.organization_id)

        assert "timestamp" in dashboard
        assert "threats" in dashboard
        assert "metrics" in dashboard
        assert "monitoring_status" in dashboard

    def test_generate_security_report(self, db: Session, test_user: User):
        """Test security report generation."""
        service = SecurityMonitoringService(db)

        # Create audit logs
        actions = ["login_success", "login_failed", "read", "export"]
        for action in actions:
            audit_log = AuditLog(
                user_id=test_user.id,
                action=action,
                resource_type="test",
                resource_id=1,
                organization_id=test_user.organization_id,
                changes={},
                created_at=datetime.now(timezone.utc),
            )
            db.add(audit_log)
        db.commit()

        report = service.generate_security_report(
            organization_id=test_user.organization_id,
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
        )

        assert "report_period" in report
        assert "summary" in report
        assert "top_activities" in report
        assert "security_insights" in report
        assert report["summary"]["total_events"] == len(actions)

    @patch("app.services.security_monitoring.AuditLogger.log")
    def test_log_security_event(self, mock_log, db: Session, test_user: User):
        """Test security event logging."""
        service = SecurityMonitoringService(db)

        threat = SecurityThreat(
            threat_type="test_threat",
            severity=SecurityThreat.HIGH,
            description="Test threat description",
            details={"test": "data"},
        )

        service.log_security_event(
            threat=threat,
            user=test_user,
            organization_id=test_user.organization_id,
            ip_address="192.168.1.1",
        )

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[1]["action"] == "security_threat_detected"
        assert call_args[1]["user"] == test_user
