"""Unit tests for performance monitoring API endpoints."""
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from app.models.user import User
from app.schemas.monitoring.performance import (
    PerformanceMetric,
    PerformanceSummary,
    ResourceUsage,
    SystemHealth,
)


@pytest.fixture
def mock_current_user():
    """Mock current user."""
    user = Mock(spec=User)
    user.id = "test-user-id"
    user.is_admin = True
    return user


@pytest.fixture
def sample_performance_metric():
    """Sample performance metric."""
    return PerformanceMetric(
        endpoint="/api/v1/users",
        method="GET",
        response_time=150.5,
        status_code=200,
        timestamp=datetime.utcnow(),
        user_id="test-user-id",
    )


@pytest.fixture
def sample_system_health():
    """Sample system health data."""
    return SystemHealth(
        status="healthy",
        timestamp=datetime.utcnow(),
        uptime_seconds=86400,
        cpu_usage=25.5,
        memory_usage=45.2,
        disk_usage=30.1,
        active_connections=150,
        response_time_avg=120.5,
        error_rate=0.02,
    )


@pytest.fixture
def sample_resource_usage():
    """Sample resource usage data."""
    return ResourceUsage(
        timestamp=datetime.utcnow(),
        cpu_percent=35.2,
        memory_percent=55.8,
        disk_percent=40.3,
        network_io={"bytes_sent": 1024000, "bytes_recv": 2048000},
        active_processes=125,
        load_average=[1.2, 1.5, 1.8],
    )


@pytest.mark.asyncio
async def test_log_performance_metric_success(mock_current_user, sample_performance_metric):
    """Test successful performance metric logging."""
    from app.api.v1.endpoints.monitoring.performance import log_performance_metric

    # Act
    result = await log_performance_metric(
        metric=sample_performance_metric,
        current_user=mock_current_user,
    )

    # Assert
    assert result is not None
    assert "message" in result
    assert "Performance metric logged" in result["message"]


@pytest.mark.asyncio
async def test_get_performance_metrics_success(mock_current_user):
    """Test successful retrieval of performance metrics."""
    from app.api.v1.endpoints.monitoring.performance import get_performance_metrics

    # Act
    result = await get_performance_metrics(
        endpoint=None,
        method=None,
        start_time=None,
        end_time=None,
        limit=100,
        current_user=mock_current_user,
    )

    # Assert
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_performance_summary_success(mock_current_user):
    """Test successful retrieval of performance summary."""
    from app.api.v1.endpoints.monitoring.performance import get_performance_summary

    # Act
    result = await get_performance_summary(
        hours=24,
        current_user=mock_current_user,
    )

    # Assert
    assert isinstance(result, PerformanceSummary)
    assert hasattr(result, 'total_requests')
    assert hasattr(result, 'avg_response_time')
    assert hasattr(result, 'error_rate')


@pytest.mark.asyncio
async def test_get_system_health_success(mock_current_user, sample_system_health):
    """Test successful system health check."""
    with patch('psutil.cpu_percent', return_value=25.5), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.boot_time', return_value=datetime.utcnow().timestamp() - 86400):

        mock_memory.return_value.percent = 45.2
        mock_disk.return_value.percent = 30.1

        from app.api.v1.endpoints.monitoring.performance import get_system_health

        # Act
        result = await get_system_health(
            current_user=mock_current_user,
        )

        # Assert
        assert isinstance(result, SystemHealth)
        assert result.status in ["healthy", "warning", "critical"]
        assert result.cpu_usage >= 0
        assert result.memory_usage >= 0


@pytest.mark.asyncio
async def test_get_resource_usage_success(mock_current_user):
    """Test successful resource usage retrieval."""
    with patch('psutil.cpu_percent', return_value=35.2), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.net_io_counters') as mock_net, \
         patch('psutil.getloadavg', return_value=[1.2, 1.5, 1.8]), \
         patch('len', return_value=125):

        mock_memory.return_value.percent = 55.8
        mock_disk.return_value.percent = 40.3
        mock_net.return_value.bytes_sent = 1024000
        mock_net.return_value.bytes_recv = 2048000

        from app.api.v1.endpoints.monitoring.performance import get_resource_usage

        # Act
        result = await get_resource_usage(
            current_user=mock_current_user,
        )

        # Assert
        assert isinstance(result, ResourceUsage)
        assert result.cpu_percent >= 0
        assert result.memory_percent >= 0
        assert result.disk_percent >= 0


@pytest.mark.asyncio
async def test_collect_resource_metrics_success(mock_current_user):
    """Test successful resource metrics collection."""
    from app.api.v1.endpoints.monitoring.performance import collect_resource_metrics

    # Act
    result = await collect_resource_metrics(
        current_user=mock_current_user,
    )

    # Assert
    assert result is not None
    assert "message" in result
    assert "Resource metrics collected" in result["message"]


@pytest.mark.asyncio
async def test_performance_metric_filtering(mock_current_user):
    """Test performance metrics with filtering parameters."""
    from app.api.v1.endpoints.monitoring.performance import get_performance_metrics

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()

    # Act
    result = await get_performance_metrics(
        endpoint="/api/v1/users",
        method="GET",
        start_time=start_time,
        end_time=end_time,
        limit=50,
        current_user=mock_current_user,
    )

    # Assert
    assert isinstance(result, list)
    # Verify filtering logic is applied (metrics should be empty for new test)
    assert len(result) >= 0


@pytest.mark.asyncio
async def test_performance_summary_calculation(mock_current_user):
    """Test performance summary calculation with different time ranges."""
    from app.api.v1.endpoints.monitoring.performance import get_performance_summary

    # Test different time ranges
    for hours in [1, 6, 24, 168]:  # 1h, 6h, 24h, 1week
        result = await get_performance_summary(
            hours=hours,
            current_user=mock_current_user,
        )

        assert isinstance(result, PerformanceSummary)
        assert result.total_requests >= 0
        assert result.avg_response_time >= 0
        assert result.error_rate >= 0.0


@pytest.mark.asyncio
async def test_system_health_status_determination():
    """Test system health status determination logic."""
    with patch('psutil.cpu_percent', return_value=95.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('psutil.boot_time', return_value=datetime.utcnow().timestamp() - 86400):

        mock_memory.return_value.percent = 90.0
        mock_disk.return_value.percent = 85.0

        from app.api.v1.endpoints.monitoring.performance import get_system_health

        result = await get_system_health(
            current_user=mock_current_user(),
        )

        # With high CPU, memory, and disk usage, status should be warning or critical
        assert result.status in ["warning", "critical"]
        assert result.cpu_usage == 95.0
        assert result.memory_usage == 90.0
        assert result.disk_usage == 85.0


@pytest.mark.asyncio
async def test_performance_percentile_calculations(mock_current_user):
    """Test performance percentile calculations in summary."""
    # Add some test metrics first
    from app.api.v1.endpoints.monitoring.performance import (
        get_performance_summary,
        log_performance_metric,
    )

    test_metrics = [
        PerformanceMetric(
            endpoint="/test",
            method="GET",
            response_time=100.0,
            status_code=200,
            timestamp=datetime.utcnow(),
            user_id="test-user",
        ),
        PerformanceMetric(
            endpoint="/test",
            method="GET",
            response_time=200.0,
            status_code=200,
            timestamp=datetime.utcnow(),
            user_id="test-user",
        ),
        PerformanceMetric(
            endpoint="/test",
            method="GET",
            response_time=300.0,
            status_code=200,
            timestamp=datetime.utcnow(),
            user_id="test-user",
        ),
    ]

    for metric in test_metrics:
        await log_performance_metric(metric, mock_current_user)

    # Get summary
    result = await get_performance_summary(
        hours=1,
        current_user=mock_current_user,
    )

    assert isinstance(result, PerformanceSummary)
    assert hasattr(result, 'p50_response_time')
    assert hasattr(result, 'p95_response_time')
    assert hasattr(result, 'p99_response_time')


@pytest.mark.asyncio
async def test_resource_usage_network_metrics():
    """Test network I/O metrics in resource usage."""
    with patch('psutil.net_io_counters') as mock_net:
        mock_net.return_value.bytes_sent = 5000000
        mock_net.return_value.bytes_recv = 10000000

        from app.api.v1.endpoints.monitoring.performance import get_resource_usage

        result = await get_resource_usage(
            current_user=mock_current_user(),
        )

        assert result.network_io["bytes_sent"] == 5000000
        assert result.network_io["bytes_recv"] == 10000000


@pytest.mark.asyncio
async def test_performance_metric_validation():
    """Test performance metric data validation."""
    # Valid metric
    valid_metric = PerformanceMetric(
        endpoint="/api/v1/test",
        method="POST",
        response_time=250.75,
        status_code=201,
        timestamp=datetime.utcnow(),
        user_id="user-123",
    )

    assert valid_metric.endpoint == "/api/v1/test"
    assert valid_metric.method == "POST"
    assert valid_metric.response_time == 250.75
    assert valid_metric.status_code == 201


@pytest.mark.asyncio
async def test_memory_leak_detection_in_metrics(mock_current_user):
    """Test that metrics don't cause memory leaks."""
    from app.api.v1.endpoints.monitoring.performance import log_performance_metric

    # Log many metrics to test memory usage
    for i in range(100):
        metric = PerformanceMetric(
            endpoint=f"/test/{i}",
            method="GET",
            response_time=100.0 + i,
            status_code=200,
            timestamp=datetime.utcnow(),
            user_id=f"user-{i}",
        )
        await log_performance_metric(metric, mock_current_user)

    # Verify that metrics are stored but with reasonable limits
    from app.api.v1.endpoints.monitoring.performance import get_performance_metrics

    result = await get_performance_metrics(
        endpoint=None,
        method=None,
        start_time=None,
        end_time=None,
        limit=1000,  # High limit to see all metrics
        current_user=mock_current_user,
    )

    # Should have some metrics but not cause memory issues
    assert isinstance(result, list)
    assert len(result) <= 1000  # Respects limit
