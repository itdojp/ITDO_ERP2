"""
Comprehensive tests for security audit and monitoring functionality.
包括的セキュリティ監査とモニタリング機能のテスト
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import (
    SecurityAlert,
    SecurityEvent,
    SecurityEventType,
    SecurityIncident,
    ThreatLevel,
)
from app.models.user import User
from app.services.enhanced_security_service import EnhancedSecurityService
from app.services.realtime_alert_service import RealtimeAlertService


class TestSecurityEventModels:
    """Test security event models and their functionality."""

    def test_security_event_creation(self, db_session: AsyncSession, test_user: User):
        """Test SecurityEvent model creation and integrity."""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.LOGIN_FAILURE,
            threat_level=ThreatLevel.MEDIUM,
            user_id=test_user.id,
            title="Failed login attempt",
            description="User failed to login with incorrect password",
            details={"attempt_count": 3, "source_ip": "192.168.1.100"},
            source_ip="192.168.1.100",
            risk_score=30,
        )
        
        # Test checksum calculation
        event.checksum = event.calculate_checksum()
        assert event.checksum is not None
        assert len(event.checksum) == 64  # SHA-256 hex length
        
        # Test integrity verification
        assert event.verify_integrity() is True
        
        # Test tampering detection
        original_checksum = event.checksum
        event.details["tampered"] = True
        assert event.verify_integrity() is False
        
        # Restore for further tests
        event.details.pop("tampered")
        event.checksum = original_checksum
        assert event.verify_integrity() is True

    def test_security_incident_creation(self):
        """Test SecurityIncident model creation."""
        incident = SecurityIncident(
            incident_id=str(uuid.uuid4()),
            title="Suspicious login activity",
            description="Multiple failed login attempts from different IPs",
            severity=ThreatLevel.HIGH,
            category="authentication",
            affected_users=[1, 2, 3],
            related_events=[1, 2, 3],
            timeline=[{
                "timestamp": datetime.utcnow().isoformat(),
                "action": "incident_created",
                "description": "Incident created due to suspicious activity",
            }],
        )
        
        assert incident.incident_id is not None
        assert incident.severity == ThreatLevel.HIGH
        assert len(incident.affected_users) == 3
        assert len(incident.timeline) == 1

    def test_security_alert_creation(self):
        """Test SecurityAlert model creation."""
        alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type="authentication_failure",
            severity=ThreatLevel.HIGH,
            title="Multiple Failed Login Attempts",
            message="User account has multiple failed login attempts",
            recipients=[1, 2],
            delivery_methods=["email", "sms", "in_app"],
        )
        
        assert alert.alert_id is not None
        assert alert.severity == ThreatLevel.HIGH
        assert len(alert.recipients) == 2
        assert "email" in alert.delivery_methods


class TestEnhancedSecurityService:
    """Test enhanced security service functionality."""

    @pytest.fixture
    def security_service(self, db_session: AsyncSession):
        """Create security service instance for testing."""
        return EnhancedSecurityService(db_session)

    async def test_log_security_event(
        self, security_service: EnhancedSecurityService, test_user: User
    ):
        """Test logging security events."""
        event = await security_service.log_security_event(
            event_type=SecurityEventType.LOGIN_FAILURE,
            title="Test login failure",
            description="Test failed login event",
            user_id=test_user.id,
            threat_level=ThreatLevel.MEDIUM,
            source_ip="192.168.1.100",
            details={"test": True},
        )
        
        assert event.id is not None
        assert event.event_type == SecurityEventType.LOGIN_FAILURE
        assert event.threat_level == ThreatLevel.MEDIUM
        assert event.user_id == test_user.id
        assert event.checksum is not None
        assert event.verify_integrity()

    async def test_detect_suspicious_activities(
        self, security_service: EnhancedSecurityService, test_user: User
    ):
        """Test suspicious activity detection."""
        # Create multiple test events
        for i in range(5):
            await security_service.log_security_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                title=f"Failed login {i}",
                description=f"Failed login attempt {i}",
                user_id=test_user.id,
                threat_level=ThreatLevel.MEDIUM,
                source_ip="192.168.1.100",
            )
        
        # Detect threats
        threats = await security_service.detect_suspicious_activities(
            time_window_hours=24
        )
        
        assert "detection_time" in threats
        assert "total_events" in threats
        assert threats["total_events"] >= 5
        assert "threat_summary" in threats
        assert "recommendations" in threats

    async def test_user_risk_profile_analysis(
        self, security_service: EnhancedSecurityService, test_user: User
    ):
        """Test user risk profile analysis."""
        # Create test events
        await security_service.log_security_event(
            event_type=SecurityEventType.PRIVILEGE_ESCALATION,
            title="Privilege escalation test",
            description="Test privilege escalation event",
            user_id=test_user.id,
            threat_level=ThreatLevel.HIGH,
        )
        
        # Analyze risk profile
        profile = await security_service.analyze_user_risk_profile(
            user_id=test_user.id, days_back=30
        )
        
        assert profile["user_id"] == test_user.id
        assert "analysis_period" in profile
        assert "event_summary" in profile
        assert "risk_score" in profile
        assert "behavioral_anomalies" in profile
        assert "recommendations" in profile

    async def test_create_security_incident(
        self, security_service: EnhancedSecurityService
    ):
        """Test security incident creation."""
        incident = await security_service.create_security_incident(
            title="Test Security Incident",
            description="This is a test security incident",
            severity=ThreatLevel.HIGH,
            category="test",
            affected_users=[1, 2],
            related_events=[1, 2, 3],
        )
        
        assert incident.id is not None
        assert incident.title == "Test Security Incident"
        assert incident.severity == ThreatLevel.HIGH
        assert len(incident.affected_users) == 2
        assert len(incident.related_events) == 3

    async def test_create_security_alert(
        self, security_service: EnhancedSecurityService, test_user: User
    ):
        """Test security alert creation."""
        alert = await security_service.create_security_alert(
            alert_type="test_alert",
            severity=ThreatLevel.MEDIUM,
            title="Test Alert",
            message="This is a test alert",
            user_id=test_user.id,
            recipients=[test_user.id],
        )
        
        assert alert.id is not None
        assert alert.alert_type == "test_alert"
        assert alert.severity == ThreatLevel.MEDIUM
        assert alert.user_id == test_user.id

    async def test_export_security_logs(
        self, security_service: EnhancedSecurityService, test_user: User
    ):
        """Test security log export functionality."""
        # Create test events
        await security_service.log_security_event(
            event_type=SecurityEventType.DATA_ACCESS,
            title="Data access test",
            description="Test data access event",
            user_id=test_user.id,
            threat_level=ThreatLevel.LOW,
        )
        
        # Test JSON export
        json_export = await security_service.export_security_logs(
            format="json",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
        )
        
        assert json_export is not None
        export_data = json.loads(json_export)
        assert "export_timestamp" in export_data
        assert "events" in export_data
        assert isinstance(export_data["events"], list)
        
        # Test CSV export
        csv_export = await security_service.export_security_logs(
            format="csv",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
        )
        
        assert csv_export is not None
        assert "ID,Event ID,Event Type" in csv_export  # CSV header check


class TestRealtimeAlertService:
    """Test real-time alert service functionality."""

    @pytest.fixture
    def alert_service(self):
        """Create alert service instance for testing."""
        return RealtimeAlertService()

    def test_add_subscriber(self, alert_service: RealtimeAlertService):
        """Test adding alert subscribers."""
        result = alert_service.add_subscriber(
            user_id=1,
            email="test@example.com",
            severity_threshold=ThreatLevel.MEDIUM,
            alert_types=["security_incident", "authentication_failure"],
        )
        
        assert "added successfully" in result
        assert 1 in alert_service.subscribers
        
        subscriber = alert_service.subscribers[1]
        assert subscriber.email == "test@example.com"
        assert subscriber.severity_threshold == ThreatLevel.MEDIUM
        assert "security_incident" in subscriber.alert_types

    def test_update_subscriber_preferences(self, alert_service: RealtimeAlertService):
        """Test updating subscriber preferences."""
        # Add subscriber first
        alert_service.add_subscriber(user_id=1, email="test@example.com")
        
        # Update preferences
        result = alert_service.update_subscriber_preferences(
            user_id=1,
            severity_threshold=ThreatLevel.HIGH,
            phone="+1234567890",
        )
        
        assert "updated" in result
        subscriber = alert_service.subscribers[1]
        assert subscriber.severity_threshold == ThreatLevel.HIGH
        assert subscriber.phone == "+1234567890"

    def test_get_service_statistics(self, alert_service: RealtimeAlertService):
        """Test getting service statistics."""
        # Add some subscribers
        alert_service.add_subscriber(user_id=1)
        alert_service.add_subscriber(user_id=2)
        
        stats = alert_service.get_service_statistics()
        
        assert "is_running" in stats
        assert "total_subscribers" in stats
        assert stats["total_subscribers"] == 2
        assert "active_websocket_connections" in stats
        assert "queued_alerts" in stats

    async def test_send_test_alert(self, alert_service: RealtimeAlertService):
        """Test sending test alerts."""
        # Add subscriber
        alert_service.add_subscriber(user_id=1)
        
        result = await alert_service.send_test_alert(
            user_id=1, severity=ThreatLevel.LOW
        )
        
        assert "Test alert queued" in result

    def test_alert_filtering(self, alert_service: RealtimeAlertService):
        """Test alert filtering based on subscriber preferences."""
        # Add subscriber with specific preferences
        alert_service.add_subscriber(
            user_id=1,
            severity_threshold=ThreatLevel.HIGH,
            alert_types=["security_incident"],
        )
        
        subscriber = alert_service.subscribers[1]
        
        # Test alert that should be received
        high_severity_alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type="security_incident",
            severity=ThreatLevel.HIGH,
            title="High severity alert",
            message="This is a high severity alert",
        )
        
        assert subscriber.should_receive_alert(high_severity_alert) is True
        
        # Test alert that should NOT be received (low severity)
        low_severity_alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type="security_incident",
            severity=ThreatLevel.LOW,
            title="Low severity alert",
            message="This is a low severity alert",
        )
        
        assert subscriber.should_receive_alert(low_severity_alert) is False
        
        # Test alert that should NOT be received (wrong type)
        wrong_type_alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type="data_breach",
            severity=ThreatLevel.HIGH,
            title="Data breach alert",
            message="This is a data breach alert",
        )
        
        assert subscriber.should_receive_alert(wrong_type_alert) is False


class TestSecurityAuditAPI:
    """Test security audit API endpoints."""

    def test_start_monitoring_session(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test starting a security monitoring session."""
        response = client.post(
            "/api/v1/security-audit/start-session",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "active"
        assert "started_at" in data

    def test_log_security_event_api(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test logging security events via API."""
        event_data = {
            "event_type": "login_failure",
            "title": "API Test Login Failure",
            "description": "Test failed login via API",
            "threat_level": "medium",
            "source_ip": "192.168.1.100",
            "details": {"test": True},
        }
        
        response = client.post(
            "/api/v1/security-audit/log-event",
            json=event_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "event_id" in data
        assert data["status"] == "logged"
        assert data["threat_level"] == "medium"

    def test_detect_threats_api(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test threat detection via API."""
        response = client.get(
            "/api/v1/security-audit/detect-threats?time_window_hours=24",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "detection_summary" in data
        assert "generated_at" in data
        assert "detection_scope" in data

    def test_get_security_dashboard(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test getting security dashboard data."""
        response = client.get(
            "/api/v1/security-audit/dashboard?time_range_hours=24",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "summary" in data
        assert "threat_levels" in data
        assert "realtime_monitoring" in data

    def test_create_security_incident_api(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test creating security incidents via API."""
        incident_data = {
            "title": "API Test Incident",
            "description": "Test security incident created via API",
            "severity": "high",
            "category": "test",
            "affected_users": [1, 2],
        }
        
        response = client.post(
            "/api/v1/security-audit/create-incident",
            json=incident_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "incident_id" in data
        assert data["severity"] == "high"
        assert "created_at" in data

    def test_export_security_logs_api(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test exporting security logs via API."""
        # Test JSON export
        response = client.get(
            "/api/v1/security-audit/export-logs?format=json",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
        # Test CSV export
        response = client.get(
            "/api/v1/security-audit/export-logs?format=csv",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_create_security_alert_api(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test creating security alerts via API."""
        alert_data = {
            "alert_type": "test_alert",
            "severity": "medium",
            "title": "API Test Alert",
            "message": "Test alert created via API",
            "delivery_methods": ["email", "in_app"],
        }
        
        response = client.post(
            "/api/v1/security-audit/alerts/create",
            json=alert_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "alert_id" in data
        assert data["status"] == "created"
        assert data["severity"] == "medium"

    def test_alert_subscription_preferences(self, client: TestClient, user_headers: Dict[str, str]):
        """Test managing alert subscription preferences."""
        # Get current preferences
        response = client.get(
            "/api/v1/security-audit/alerts/subscription-preferences",
            headers=user_headers,
        )
        
        assert response.status_code == 200
        
        # Update preferences
        preferences_data = {
            "severity_threshold": "high",
            "alert_types": ["security_incident", "data_breach"],
            "email": "test@example.com",
        }
        
        response = client.put(
            "/api/v1/security-audit/alerts/subscription-preferences",
            json=preferences_data,
            headers=user_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

    def test_send_test_alert_api(self, client: TestClient, user_headers: Dict[str, str]):
        """Test sending test alerts via API."""
        response = client.post(
            "/api/v1/security-audit/alerts/test?severity=low",
            headers=user_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["test_alert_sent"] is True
        assert data["severity"] == "low"

    def test_get_security_statistics(self, client: TestClient, admin_headers: Dict[str, str]):
        """Test getting comprehensive security statistics."""
        response = client.get(
            "/api/v1/security-audit/statistics?days_back=30",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_period" in data
        assert "security_dashboard" in data
        assert "realtime_monitoring" in data
        assert "system_health" in data

    def test_unauthorized_access(self, client: TestClient):
        """Test that unauthorized users cannot access security endpoints."""
        # Test without authentication
        response = client.get("/api/v1/security-audit/dashboard")
        assert response.status_code == 401

    def test_forbidden_access(self, client: TestClient, user_headers: Dict[str, str]):
        """Test that non-admin users cannot access admin-only endpoints."""
        # Regular users should not be able to detect threats
        response = client.get(
            "/api/v1/security-audit/detect-threats",
            headers=user_headers,
        )
        assert response.status_code == 403


class TestSecurityIntegration:
    """Integration tests for the complete security system."""

    async def test_end_to_end_security_workflow(
        self,
        db_session: AsyncSession,
        test_user: User,
        client: TestClient,
        admin_headers: Dict[str, str],
    ):
        """Test complete security workflow from event to alert."""
        security_service = EnhancedSecurityService(db_session)
        alert_service = RealtimeAlertService()
        
        # 1. Start monitoring
        await alert_service.start_service()
        
        # 2. Add subscriber
        alert_service.add_subscriber(
            user_id=test_user.id,
            email="test@example.com",
            severity_threshold=ThreatLevel.MEDIUM,
        )
        
        # 3. Log a high-severity security event
        event = await security_service.log_security_event(
            event_type=SecurityEventType.PRIVILEGE_ESCALATION,
            title="Critical privilege escalation",
            description="Unauthorized privilege escalation detected",
            user_id=test_user.id,
            threat_level=ThreatLevel.CRITICAL,
        )
        
        # 4. Create incident (should be automatic for critical events)
        incidents = await security_service.detect_suspicious_activities(
            time_window_hours=1
        )
        
        # 5. Create alert
        alert = await security_service.create_security_alert(
            alert_type="privilege_escalation",
            severity=ThreatLevel.CRITICAL,
            title="Critical Security Alert",
            message="Privilege escalation detected",
            user_id=test_user.id,
        )
        
        # 6. Queue alert for delivery
        await alert_service.queue_alert(alert)
        
        # Verify the workflow completed successfully
        assert event.id is not None
        assert event.threat_level == ThreatLevel.CRITICAL
        assert alert.id is not None
        assert alert.severity == ThreatLevel.CRITICAL
        
        # Stop monitoring
        await alert_service.stop_service()

    def test_concurrent_event_logging(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test concurrent security event logging."""
        security_service = EnhancedSecurityService(db_session)
        
        async def log_event(i: int):
            return await security_service.log_security_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                title=f"Concurrent test event {i}",
                description=f"Concurrent login failure {i}",
                user_id=test_user.id,
                threat_level=ThreatLevel.LOW,
            )
        
        # Use asyncio to run concurrent event logging
        async def run_concurrent_tests():
            tasks = [log_event(i) for i in range(10)]
            events = await asyncio.gather(*tasks)
            return events
        
        events = asyncio.run(run_concurrent_tests())
        
        # Verify all events were logged successfully
        assert len(events) == 10
        for event in events:
            assert event.id is not None
            assert event.verify_integrity()


# Pytest fixtures for test data
@pytest.fixture
def test_user(db_session: AsyncSession) -> User:
    """Create a test user for security tests."""
    user = User(
        email="security_test@example.com",
        username="security_test_user",
        full_name="Security Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(test_user: User) -> Dict[str, str]:
    """Create admin headers for API testing."""
    # In a real implementation, this would generate a proper JWT token
    return {
        "Authorization": "Bearer admin_test_token",
        "Content-Type": "application/json",
    }


@pytest.fixture
def user_headers(test_user: User) -> Dict[str, str]:
    """Create user headers for API testing."""
    # In a real implementation, this would generate a proper JWT token
    return {
        "Authorization": "Bearer user_test_token",
        "Content-Type": "application/json",
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])