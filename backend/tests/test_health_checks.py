"""
Health Check System Tests
Comprehensive test suite for health monitoring functionality
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.health import (
    ComponentType,
    HealthChecker,
    HealthCheckResult,
    HealthMetric,
    HealthStatus,
    SystemHealthReport,
)
from app.main import app


class TestHealthChecker:
    """Test suite for HealthChecker class"""

    @pytest.fixture
    def health_checker(self):
        """Health checker instance"""
        return HealthChecker()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = MagicMock(spec=Session)
        session.execute.return_value.fetchone.return_value = (1, "PostgreSQL 15.0")
        session.bind.pool = MagicMock()
        session.bind.pool.size = 5
        session.bind.pool.checkedin = 3
        session.bind.pool.checkedout = 2
        session.bind.pool.invalid = 0
        return session

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.ping.return_value = True
        redis_mock.set.return_value = True
        redis_mock.get.return_value = b"test_value"
        redis_mock.delete.return_value = 1
        redis_mock.info.return_value = {
            "redis_version": "7.0.0",
            "connected_clients": 2,
            "keyspace_hits": 100,
            "keyspace_misses": 5,
        }
        return redis_mock

    @pytest.mark.asyncio
    async def test_check_system_health_basic(self, health_checker):
        """Test basic system health check"""
        with (
            patch.object(health_checker, "_check_database") as mock_db,
            patch.object(health_checker, "_check_redis") as mock_redis,
            patch.object(health_checker, "_check_external_dependencies") as mock_ext,
            patch.object(health_checker, "_check_application_health") as mock_app,
        ):
            # Mock successful health checks
            mock_db.return_value = HealthCheckResult(
                component="database",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                timestamp=datetime.now(timezone.utc),
                message="Database operating normally",
            )

            mock_redis.return_value = HealthCheckResult(
                component="redis",
                component_type=ComponentType.CACHE,
                status=HealthStatus.HEALTHY,
                response_time_ms=10.0,
                timestamp=datetime.now(timezone.utc),
                message="Redis operating normally",
            )

            mock_ext.return_value = HealthCheckResult(
                component="external_dependencies",
                component_type=ComponentType.DEPENDENCY,
                status=HealthStatus.HEALTHY,
                response_time_ms=100.0,
                timestamp=datetime.now(timezone.utc),
                message="All dependencies available",
            )

            mock_app.return_value = HealthCheckResult(
                component="application",
                component_type=ComponentType.APPLICATION,
                status=HealthStatus.HEALTHY,
                response_time_ms=5.0,
                timestamp=datetime.now(timezone.utc),
                message="Application running normally",
            )

            result = await health_checker.check_system_health()

            assert isinstance(result, SystemHealthReport)
            assert result.overall_status == HealthStatus.HEALTHY
            assert len(result.components) >= 4  # At least DB, Redis, deps, app
            assert result.version == health_checker.version
            assert result.environment == health_checker.environment

    @pytest.mark.asyncio
    async def test_check_system_health_with_failures(self, health_checker):
        """Test system health check with some component failures"""
        with (
            patch.object(health_checker, "_check_database") as mock_db,
            patch.object(health_checker, "_check_redis") as mock_redis,
            patch.object(health_checker, "_check_external_dependencies") as mock_ext,
            patch.object(health_checker, "_check_application_health") as mock_app,
        ):
            # Mock database failure
            mock_db.return_value = HealthCheckResult(
                component="database",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                timestamp=datetime.now(timezone.utc),
                message="Database connection failed",
                error="Connection refused",
            )

            # Mock Redis degraded
            mock_redis.return_value = HealthCheckResult(
                component="redis",
                component_type=ComponentType.CACHE,
                status=HealthStatus.DEGRADED,
                response_time_ms=150.0,
                timestamp=datetime.now(timezone.utc),
                message="Redis responding slowly",
            )

            mock_ext.return_value = HealthCheckResult(
                component="external_dependencies",
                component_type=ComponentType.DEPENDENCY,
                status=HealthStatus.HEALTHY,
                response_time_ms=100.0,
                timestamp=datetime.now(timezone.utc),
                message="All dependencies available",
            )

            mock_app.return_value = HealthCheckResult(
                component="application",
                component_type=ComponentType.APPLICATION,
                status=HealthStatus.HEALTHY,
                response_time_ms=5.0,
                timestamp=datetime.now(timezone.utc),
                message="Application running normally",
            )

            result = await health_checker.check_system_health()

            # Overall status should be unhealthy due to database failure
            assert result.overall_status == HealthStatus.UNHEALTHY

            # Should have summary of issues
            assert "database" in result.summary["critical_issues"]
            assert "redis" in result.summary["warnings"]

    @pytest.mark.asyncio
    @patch("app.core.health.get_db")
    async def test_check_database_success(
        self, mock_get_db, health_checker, mock_db_session
    ):
        """Test successful database health check"""
        mock_get_db.return_value.__next__.return_value = mock_db_session

        result = await health_checker._check_database()

        assert result.component == "database"
        assert result.component_type == ComponentType.DATABASE
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0
        assert "Database operating normally" in result.message
        assert "version" in result.details
        assert "connection_pool" in result.details

    @pytest.mark.asyncio
    @patch("app.core.health.get_db")
    async def test_check_database_failure(self, mock_get_db, health_checker):
        """Test database health check with connection failure"""
        mock_get_db.return_value.__next__.side_effect = Exception("Connection refused")

        result = await health_checker._check_database()

        assert result.component == "database"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Connection refused" in result.error
        assert "Database connection failed" in result.message

    @pytest.mark.asyncio
    @patch("app.core.health.get_redis")
    async def test_check_redis_success(
        self, mock_get_redis, health_checker, mock_redis_client
    ):
        """Test successful Redis health check"""
        mock_get_redis.return_value = mock_redis_client

        result = await health_checker._check_redis()

        assert result.component == "redis"
        assert result.component_type == ComponentType.CACHE
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0
        assert "Redis operating normally" in result.message
        assert "redis_version" in result.details

    @pytest.mark.asyncio
    @patch("app.core.health.get_redis")
    async def test_check_redis_failure(self, mock_get_redis, health_checker):
        """Test Redis health check with connection failure"""
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis connection failed")
        mock_get_redis.return_value = mock_redis

        result = await health_checker._check_redis()

        assert result.component == "redis"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Redis connection failed" in result.error

    @pytest.mark.asyncio
    @patch("psutil.virtual_memory")
    async def test_check_memory(self, mock_memory, health_checker):
        """Test memory health check"""
        mock_memory.return_value = MagicMock(
            total=8 * 1024**3,  # 8GB
            available=6 * 1024**3,  # 6GB
            used=2 * 1024**3,  # 2GB
            percent=25.0,
        )

        result = await health_checker._check_memory()

        assert result.component == "memory"
        assert result.component_type == ComponentType.MEMORY
        assert result.status == HealthStatus.HEALTHY
        assert "Memory usage normal" in result.message
        assert len(result.metrics) >= 1

        # Check memory metric
        memory_metric = next(
            m for m in result.metrics if m.name == "memory_usage_percent"
        )
        assert memory_metric.value == 25.0
        assert memory_metric.unit == "%"

    @pytest.mark.asyncio
    @patch("psutil.virtual_memory")
    async def test_check_memory_high_usage(self, mock_memory, health_checker):
        """Test memory health check with high usage"""
        mock_memory.return_value = MagicMock(
            total=8 * 1024**3, available=0.5 * 1024**3, used=7.5 * 1024**3, percent=95.0
        )

        result = await health_checker._check_memory()

        assert result.status == HealthStatus.UNHEALTHY
        assert "Critical memory usage" in result.message

    @pytest.mark.asyncio
    @patch("psutil.cpu_percent")
    @patch("psutil.cpu_count")
    async def test_check_cpu(self, mock_cpu_count, mock_cpu_percent, health_checker):
        """Test CPU health check"""
        mock_cpu_percent.return_value = 45.0
        mock_cpu_count.return_value = 4

        with patch("psutil.getloadavg", return_value=(1.2, 1.5, 1.8)):
            result = await health_checker._check_cpu()

        assert result.component == "cpu"
        assert result.component_type == ComponentType.CPU
        assert result.status == HealthStatus.HEALTHY
        assert "CPU usage normal" in result.message

        # Check CPU metric
        cpu_metric = next(m for m in result.metrics if m.name == "cpu_usage_percent")
        assert cpu_metric.value == 45.0

    @pytest.mark.asyncio
    @patch("psutil.disk_usage")
    async def test_check_disk(self, mock_disk_usage, health_checker):
        """Test disk health check"""
        mock_disk_usage.return_value = MagicMock(
            total=100 * 1024**3,  # 100GB
            used=50 * 1024**3,  # 50GB
            free=50 * 1024**3,  # 50GB
        )

        result = await health_checker._check_disk()

        assert result.component == "disk"
        assert result.component_type == ComponentType.DISK
        assert result.status == HealthStatus.HEALTHY
        assert "Disk space normal" in result.message

        # Check disk metric
        disk_metric = next(m for m in result.metrics if m.name == "disk_usage_percent")
        assert disk_metric.value == 50.0

    def test_calculate_overall_status(self, health_checker):
        """Test overall status calculation logic"""
        # All healthy
        components = [
            HealthCheckResult(
                "db",
                ComponentType.DATABASE,
                HealthStatus.HEALTHY,
                50,
                datetime.now(timezone.utc),
            ),
            HealthCheckResult(
                "redis",
                ComponentType.CACHE,
                HealthStatus.HEALTHY,
                20,
                datetime.now(timezone.utc),
            ),
        ]
        assert (
            health_checker._calculate_overall_status(components) == HealthStatus.HEALTHY
        )

        # One degraded
        components[1].status = HealthStatus.DEGRADED
        assert (
            health_checker._calculate_overall_status(components)
            == HealthStatus.DEGRADED
        )

        # One unhealthy
        components[0].status = HealthStatus.UNHEALTHY
        assert (
            health_checker._calculate_overall_status(components)
            == HealthStatus.UNHEALTHY
        )

        # Empty components
        assert health_checker._calculate_overall_status([]) == HealthStatus.UNKNOWN

    def test_generate_summary(self, health_checker):
        """Test summary generation"""
        components = [
            HealthCheckResult(
                "db",
                ComponentType.DATABASE,
                HealthStatus.HEALTHY,
                50,
                datetime.now(timezone.utc),
            ),
            HealthCheckResult(
                "redis",
                ComponentType.CACHE,
                HealthStatus.DEGRADED,
                150,
                datetime.now(timezone.utc),
            ),
            HealthCheckResult(
                "app",
                ComponentType.APPLICATION,
                HealthStatus.UNHEALTHY,
                0,
                datetime.now(timezone.utc),
            ),
        ]

        summary = health_checker._generate_summary(components)

        assert summary["status_distribution"]["healthy"] == 1
        assert summary["status_distribution"]["degraded"] == 1
        assert summary["status_distribution"]["unhealthy"] == 1
        assert summary["average_response_time_ms"] == 66.67  # (50 + 150 + 0) / 3
        assert "db" not in summary["critical_issues"]
        assert "app" in summary["critical_issues"]
        assert "redis" in summary["warnings"]


class TestHealthCheckAPI:
    """Test health check API endpoints"""

    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)

    def test_liveness_probe(self, client):
        """Test liveness probe endpoint"""
        response = client.get("/api/v1/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @patch("app.core.health.get_health_checker")
    def test_comprehensive_health_check(self, mock_get_checker, client):
        """Test comprehensive health check endpoint"""
        mock_checker = MagicMock()
        mock_report = SystemHealthReport(
            overall_status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=3600,
            version="1.0.0",
            environment="test",
            components=[
                HealthCheckResult(
                    "database",
                    ComponentType.DATABASE,
                    HealthStatus.HEALTHY,
                    50.0,
                    datetime.now(timezone.utc),
                    "Database OK",
                    {"version": "15.0"},
                    [HealthMetric("response_time", 50.0, "ms")],
                )
            ],
            summary={"healthy_components": 1},
        )

        mock_checker.check_system_health = AsyncMock(return_value=mock_report)
        mock_get_checker.return_value = mock_checker

        response = client.get("/api/v1/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["overall_healthy"] is True
        assert len(data["components"]) == 1
        assert data["components"][0]["component"] == "database"

    @patch("app.core.health.get_health_checker")
    def test_comprehensive_health_check_failure(self, mock_get_checker, client):
        """Test comprehensive health check with failure"""
        mock_checker = MagicMock()
        mock_checker.check_system_health = AsyncMock(
            side_effect=Exception("Health check failed")
        )
        mock_checker.version = "1.0.0"
        mock_checker.environment = "test"
        mock_get_checker.return_value = mock_checker

        response = client.get("/api/v1/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["overall_healthy"] is False
        assert data["fallback_mode"] is True
        assert "Health check failed" in data["error"]


class TestHealthCheckIntegration:
    """Integration tests for health check system"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_health_check_workflow(self):
        """Test complete health check workflow"""
        health_checker = HealthChecker()

        # This would typically use real database and Redis connections
        # For integration tests, you'd set up test containers

        with (
            patch("app.core.database.get_db") as mock_get_db,
            patch("app.core.database.get_redis") as mock_get_redis,
        ):
            # Mock successful connections
            mock_session = MagicMock()
            mock_session.execute.return_value.fetchone.return_value = (
                1,
                "PostgreSQL 15.0",
            )
            mock_get_db.return_value.__next__.return_value = mock_session

            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_redis.info.return_value = {"redis_version": "7.0.0"}
            mock_get_redis.return_value = mock_redis

            # Run health check
            report = await health_checker.check_system_health(include_detailed=True)

            assert isinstance(report, SystemHealthReport)
            assert report.overall_status in [
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
            ]
            assert len(report.components) > 0
            assert report.summary is not None

    @pytest.mark.integration
    def test_api_endpoint_integration(self):
        """Test health check API endpoints integration"""
        client = TestClient(app)

        # Test all health endpoints
        endpoints = [
            "/api/v1/health/live",
            "/api/v1/health/ready",
            "/api/v1/health/startup",
            "/api/v1/health/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 500 errors
            assert response.status_code != 500

            # Should return JSON
            assert response.headers.get("content-type") == "application/json"


class TestHealthMetrics:
    """Test health check metrics and monitoring"""

    def test_health_metric_creation(self):
        """Test health metric object creation"""
        metric = HealthMetric(
            name="response_time",
            value=123.45,
            unit="ms",
            threshold_warning=100,
            threshold_critical=200,
            description="API response time",
        )

        assert metric.name == "response_time"
        assert metric.value == 123.45
        assert metric.unit == "ms"
        assert metric.threshold_warning == 100
        assert metric.threshold_critical == 200

    def test_health_check_result_creation(self):
        """Test health check result object creation"""
        timestamp = datetime.now(timezone.utc)
        metrics = [HealthMetric("test_metric", 42, "unit")]

        result = HealthCheckResult(
            component="test_component",
            component_type=ComponentType.DATABASE,
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
            timestamp=timestamp,
            message="Test message",
            details={"key": "value"},
            metrics=metrics,
            error=None,
        )

        assert result.component == "test_component"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms == 50.0
        assert result.timestamp == timestamp
        assert len(result.metrics) == 1
        assert result.metrics[0].name == "test_metric"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
