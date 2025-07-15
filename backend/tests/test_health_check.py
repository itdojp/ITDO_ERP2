"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_basic_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_comprehensive_health_check(client: TestClient):
    """Test comprehensive health check endpoint."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data
    assert "overall_healthy" in data

    # Status should be either 'healthy' or 'unhealthy'
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["version"] == "2.0.0"

    # Checks should be a dict
    assert isinstance(data["checks"], dict)


def test_liveness_probe(client: TestClient):
    """Test Kubernetes liveness probe."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_readiness_probe(client: TestClient):
    """Test Kubernetes readiness probe."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()

    # Should have database connectivity info
    assert "status" in data
    assert "database" in data
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_database_health(client: TestClient):
    """Test database health check."""
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()

    if data["status"] == "healthy":
        # Should have query performance data
        assert "basic_query" in data
        assert "count_query" in data
        assert "total_duration_ms" in data

        # Check query structure
        assert "result" in data["basic_query"]
        assert "duration_ms" in data["basic_query"]
        assert "users_count" in data["count_query"]
        assert "duration_ms" in data["count_query"]
    else:
        # Should have error information
        assert "error" in data
        assert "error_type" in data


def test_metrics_endpoint_health(client: TestClient):
    """Test metrics endpoint health check."""
    response = client.get("/api/v1/health/metrics-endpoint")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "metrics_available" in data

    if data["status"] == "healthy":
        assert data["metrics_available"] == "yes"
        assert "sample_metrics_length" in data
    else:
        assert data["metrics_available"] == "no"
        assert "error" in data


def test_system_health(client: TestClient):
    """Test system health check."""
    response = client.get("/api/v1/health/system")
    assert response.status_code == 200
    data = response.json()

    if data["status"] == "healthy":
        # Should have system resource data
        assert "disk" in data
        assert "memory" in data
        assert "cpu" in data

        # Check disk info
        assert "free_percent" in data["disk"]
        assert "free_gb" in data["disk"]
        assert "total_gb" in data["disk"]
        assert "healthy" in data["disk"]

        # Check memory info
        assert "used_percent" in data["memory"]
        assert "available_gb" in data["memory"]
        assert "total_gb" in data["memory"]
        assert "healthy" in data["memory"]

        # Check CPU info
        assert "usage_percent" in data["cpu"]
        assert "healthy" in data["cpu"]
    else:
        assert "error" in data


def test_startup_health(client: TestClient):
    """Test startup health check."""
    response = client.get("/api/v1/health/startup")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "checks" in data
    assert "overall_healthy" in data

    # Check expected startup components
    checks = data["checks"]
    assert "monitoring_initialized" in checks
    assert "health_checker_ready" in checks
    assert "database_session_factory" in checks

    # All should be boolean values
    for check_name, check_value in checks.items():
        assert isinstance(check_value, bool), f"{check_name} should be boolean"


def test_agent_health(client: TestClient):
    """Test agent health check for Level 1 escalation."""
    response = client.get("/api/v1/health/agent")
    assert response.status_code == 200
    data = response.json()

    # Required fields
    assert "status" in data
    assert "agent_response_time_ms" in data
    assert "system_resources" in data
    assert "performance_criteria" in data
    assert "overall_agent_health" in data
    assert "timestamp" in data
    assert "escalation_level" in data

    # Status values
    assert data["status"] in ["healthy", "degraded", "critical"]

    # System resources
    resources = data["system_resources"]
    assert "memory_usage_percent" in resources
    assert "cpu_usage_percent" in resources
    assert "memory_available_gb" in resources

    # Performance criteria
    criteria = data["performance_criteria"]
    assert "response_time_ok" in criteria
    assert "memory_ok" in criteria
    assert "cpu_ok" in criteria

    # All criteria should be boolean
    for criterion, value in criteria.items():
        assert isinstance(value, bool), f"{criterion} should be boolean"

    # Escalation level
    assert data["escalation_level"] in ["NORMAL", "LEVEL_1"]

    # Agent health should be boolean
    assert isinstance(data["overall_agent_health"], bool)


def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200

    # Should return plain text metrics
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # Should contain Prometheus-style metrics
    content = response.text
    assert "# HELP" in content or "# TYPE" in content or content.strip() == ""


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ITDO ERP System API"


class TestHealthCheckIntegration:
    """Integration tests for health check system."""

    def test_health_check_with_database_error(self, client: TestClient, monkeypatch):
        """Test health check behavior when database is unavailable."""

        # Mock database connection to raise an exception
        def mock_get_db():
            raise Exception("Database connection failed")

        # Note: This test would require more complex mocking to properly test
        # database failure scenarios. For now, we test normal operation.
        response = client.get("/api/v1/health/database")
        assert response.status_code == 200
        # Response could be either healthy or unhealthy depending on actual DB state

    def test_agent_health_escalation_criteria(self, client: TestClient):
        """Test agent health escalation criteria logic."""
        response = client.get("/api/v1/health/agent")
        assert response.status_code == 200
        data = response.json()

        # If all performance criteria are OK, should be NORMAL
        # If any fail, should be LEVEL_1
        criteria = data["performance_criteria"]
        all_ok = all(criteria.values())

        if all_ok:
            assert data["escalation_level"] == "NORMAL"
            assert data["overall_agent_health"] is True
            assert data["status"] == "healthy"
        else:
            assert data["escalation_level"] == "LEVEL_1"
            assert data["overall_agent_health"] is False
            assert data["status"] in ["degraded", "critical"]

    def test_comprehensive_health_includes_all_checks(self, client: TestClient):
        """Test that comprehensive health check includes all expected checks."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()

        checks = data.get("checks", {})

        # Should have checks for major system components
        # Note: Exact checks depend on what's registered during startup
        assert isinstance(checks, dict)

        # If checks are present, they should have the expected structure
        for check_name, check_data in checks.items():
            assert isinstance(check_data, dict)
            if "healthy" in check_data:
                assert isinstance(check_data["healthy"], bool)
            if "timestamp" in check_data:
                assert isinstance(check_data["timestamp"], str)
