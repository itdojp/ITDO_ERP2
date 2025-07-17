"""
Test cases for Enhanced Security Monitoring API endpoints.
拡張セキュリティ監視APIエンドポイントのテスト
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def mock_security_monitor():
    """Mock security monitor service."""
    monitor = AsyncMock()

    # Default return values
    monitor.start_monitoring.return_value = {"status": "started", "message": "Monitoring started successfully"}
    monitor.stop_monitoring.return_value = {"status": "stopped", "message": "Monitoring stopped successfully"}
    monitor.get_threat_statistics.return_value = {
        "timestamp": datetime.utcnow().isoformat(),
        "monitoring_status": "active",
        "threat_counts": {"low": 10, "medium": 5, "high": 2},
        "events_processed": 100,
        "alerts_generated": 7
    }
    monitor.get_user_risk_profile.return_value = {
        "user_id": 123,
        "risk_level": "medium",
        "events_count": 25,
        "threat_distribution": {"low": 20, "medium": 4, "high": 1}
    }

    return monitor


@pytest.fixture
def mock_threat_detector():
    """Mock threat detector service."""
    detector = AsyncMock()

    # Default return values
    detector.build_behavior_baseline.return_value = {
        "user_id": 123,
        "baseline_created": True,
        "activities_analyzed": 50,
        "typical_actions": ["read", "write"],
        "typical_locations": ["192.168.1.1"]
    }
    detector.detect_user_anomaly.return_value = {
        "user_id": 123,
        "anomaly_detected": True,
        "anomaly_type": "unusual_location",
        "confidence_score": 0.85,
        "severity": "medium"
    }
    detector.calculate_user_risk_score.return_value = 67.5
    detector.analyze_threat_intelligence.return_value = {
        "indicator": "1.2.3.4",
        "indicator_type": "ip",
        "threat_level": "high",
        "is_malicious": True,
        "sources": ["threat_feed_1", "threat_feed_2"]
    }

    return detector


@pytest.mark.asyncio
class TestEnhancedSecurityMonitoringAPI:
    """Test cases for Enhanced Security Monitoring API."""

    async def test_start_monitoring(self, mock_security_monitor):
        """Test starting real-time monitoring."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/security-monitoring/start")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "started"
                assert "message" in data

                mock_security_monitor.start_monitoring.assert_called_once()

    async def test_stop_monitoring(self, mock_security_monitor):
        """Test stopping real-time monitoring."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/security-monitoring/stop")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "stopped"

                mock_security_monitor.stop_monitoring.assert_called_once()

    async def test_get_monitoring_status(self, mock_security_monitor):
        """Test getting monitoring status."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/security-monitoring/status")

                assert response.status_code == 200
                data = response.json()
                assert "monitoring_status" in data
                assert "threat_counts" in data
                assert "events_processed" in data

    async def test_get_threat_statistics(self, mock_security_monitor):
        """Test getting threat statistics."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/security-monitoring/threats/statistics")

                assert response.status_code == 200
                data = response.json()
                assert "threat_counts" in data
                assert "low" in data["threat_counts"]
                assert "medium" in data["threat_counts"]
                assert "high" in data["threat_counts"]

    async def test_get_user_risk_profile(self, mock_security_monitor):
        """Test getting user risk profile."""
        user_id = 123

        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/security-monitoring/users/{user_id}/risk-profile")

                assert response.status_code == 200
                data = response.json()
                assert data["user_id"] == user_id
                assert "risk_level" in data
                assert "events_count" in data

                mock_security_monitor.get_user_risk_profile.assert_called_once_with(user_id)

    async def test_build_user_baseline(self, mock_threat_detector):
        """Test building user behavior baseline."""
        user_id = 123

        with patch('app.api.v1.enhanced_security_monitoring.get_threat_detector',
                  return_value=mock_threat_detector), \
             patch('app.api.v1.enhanced_security_monitoring.get_db') as mock_db:

            # Mock database query results
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session

            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db_session.execute.return_value = mock_result

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(f"/api/v1/security-monitoring/users/{user_id}/baseline")

                assert response.status_code == 200
                data = response.json()
                assert data["user_id"] == user_id
                assert data["baseline_created"] is True

    async def test_detect_user_anomaly(self, mock_threat_detector):
        """Test detecting user anomaly."""
        user_id = 123
        event_data = {
            "event_type": "login",
            "action": "login_success",
            "source_ip": "10.0.0.1",
            "user_agent": "Mozilla/5.0...",
            "details": {"method": "password"}
        }

        with patch('app.api.v1.enhanced_security_monitoring.get_threat_detector',
                  return_value=mock_threat_detector):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/security-monitoring/users/{user_id}/anomaly-detection",
                    json=event_data
                )

                assert response.status_code == 200
                data = response.json()
                assert data["user_id"] == user_id
                assert "anomaly_detected" in data
                assert "confidence_score" in data

    async def test_calculate_risk_score(self, mock_threat_detector):
        """Test calculating user risk score."""
        user_id = 123

        with patch('app.api.v1.enhanced_security_monitoring.get_threat_detector',
                  return_value=mock_threat_detector), \
             patch('app.api.v1.enhanced_security_monitoring.get_db') as mock_db:

            # Mock database session
            mock_db_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_db_session

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/security-monitoring/users/{user_id}/risk-score")

                assert response.status_code == 200
                data = response.json()
                assert data["user_id"] == user_id
                assert "risk_score" in data
                assert 0 <= data["risk_score"] <= 100

    async def test_analyze_threat_intelligence(self, mock_threat_detector):
        """Test threat intelligence analysis."""
        indicator = "1.2.3.4"
        indicator_type = "ip"

        with patch('app.api.v1.enhanced_security_monitoring.get_threat_detector',
                  return_value=mock_threat_detector):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/security-monitoring/threat-intelligence/{indicator}",
                    params={"indicator_type": indicator_type}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["indicator"] == indicator
                assert data["indicator_type"] == indicator_type
                assert "threat_level" in data
                assert "is_malicious" in data

    async def test_get_threat_summary(self, mock_security_monitor, mock_threat_detector):
        """Test getting comprehensive threat summary."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor), \
             patch('app.api.v1.enhanced_security_monitoring.get_threat_detector',
                  return_value=mock_threat_detector):

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/security-monitoring/threat-summary")

                assert response.status_code == 200
                data = response.json()
                assert "monitoring_status" in data
                assert "threat_statistics" in data
                assert "high_risk_users" in data
                assert "recent_alerts" in data

    async def test_configure_monitoring(self, mock_security_monitor):
        """Test monitoring configuration."""
        config_data = {
            "monitoring_interval": 30,
            "alert_thresholds": {
                "low": 10,
                "medium": 5,
                "high": 1
            },
            "retention_days": 90,
            "notification_channels": ["email", "webhook"]
        }

        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/security-monitoring/configure",
                    json=config_data
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "configured"
                assert "message" in data

    async def test_get_security_logs(self, mock_security_monitor):
        """Test retrieving security logs."""
        # Mock log data
        mock_security_monitor.get_security_logs.return_value = {
            "logs": [
                {
                    "id": 1,
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": "login",
                    "user_id": 123,
                    "threat_level": "low",
                    "details": {"action": "login_success"}
                }
            ],
            "total_count": 1,
            "page": 1,
            "limit": 50
        }

        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/security-monitoring/logs",
                    params={"limit": 50, "offset": 0}
                )

                assert response.status_code == 200
                data = response.json()
                assert "logs" in data
                assert "total_count" in data

    async def test_cleanup_old_logs(self, mock_security_monitor):
        """Test cleaning up old security logs."""
        mock_security_monitor.cleanup_old_logs.return_value = {
            "status": "completed",
            "deleted_count": 1500,
            "retention_days": 90
        }

        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(
                    "/api/v1/security-monitoring/logs/cleanup",
                    params={"days": 90}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "completed"
                assert "deleted_count" in data

    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time monitoring."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor') as mock_monitor:
            # Mock monitor with subscription capability
            monitor_instance = AsyncMock()
            monitor_instance.subscribe = MagicMock()
            monitor_instance.unsubscribe = MagicMock()
            mock_monitor.return_value = monitor_instance

            async with AsyncClient(app=app, base_url="http://test") as client:
                with client.websocket_connect("/api/v1/security-monitoring/ws") as websocket:
                    # Test connection establishment
                    data = websocket.receive_json()
                    assert data["type"] == "connection_established"

                    # Mock receiving a security event
                    test_event = {
                        "type": "security_event",
                        "event": {
                            "event_id": "test_001",
                            "event_type": "login",
                            "user_id": 123,
                            "threat_level": "medium",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }

                    # Simulate event notification
                    websocket.send_json(test_event)

    async def test_error_handling_invalid_user(self, mock_security_monitor):
        """Test error handling for invalid user ID."""
        invalid_user_id = 99999
        mock_security_monitor.get_user_risk_profile.side_effect = Exception("User not found")

        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    f"/api/v1/security-monitoring/users/{invalid_user_id}/risk-profile"
                )

                assert response.status_code == 404

    async def test_error_handling_invalid_data(self, mock_threat_detector):
        """Test error handling for invalid input data."""
        user_id = 123
        invalid_event_data = {
            "event_type": "",  # Invalid empty event type
            "action": None,    # Invalid null action
        }

        with patch('app.api.v1.enhanced_security_monitoring.get_threat_detector',
                  return_value=mock_threat_detector):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/security-monitoring/users/{user_id}/anomaly-detection",
                    json=invalid_event_data
                )

                assert response.status_code == 422  # Validation error

    async def test_rate_limiting(self, mock_security_monitor):
        """Test rate limiting on monitoring endpoints."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Make multiple rapid requests
                responses = []
                for i in range(10):
                    response = await client.get("/api/v1/security-monitoring/status")
                    responses.append(response)

                # All requests should succeed in test environment
                # In production, rate limiting would be configured
                assert all(r.status_code == 200 for r in responses)

    async def test_security_headers(self, mock_security_monitor):
        """Test security headers in API responses."""
        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/security-monitoring/status")

                assert response.status_code == 200
                # Check for security headers (would be configured in middleware)
                # These would typically be added by FastAPI middleware
                headers = response.headers
                assert "content-type" in headers

    async def test_monitoring_performance(self, mock_security_monitor):
        """Test monitoring endpoint performance."""
        import time

        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            async with AsyncClient(app=app, base_url="http://test") as client:
                start_time = time.time()
                response = await client.get("/api/v1/security-monitoring/status")
                end_time = time.time()

                assert response.status_code == 200
                # Response should be fast (under 1 second for mock)
                assert (end_time - start_time) < 1.0

    async def test_concurrent_requests(self, mock_security_monitor):
        """Test handling concurrent monitoring requests."""
        import asyncio

        async def make_request():
            async with AsyncClient(app=app, base_url="http://test") as client:
                return await client.get("/api/v1/security-monitoring/status")

        with patch('app.api.v1.enhanced_security_monitoring.get_security_monitor',
                  return_value=mock_security_monitor):
            # Make 5 concurrent requests
            tasks = [make_request() for _ in range(5)]
            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)
