"""
Tests for CC02 v62.0 Advanced API Gateway & Microservices Architecture
Comprehensive test suite for service registry, load balancing, circuit breaker, and security
"""

import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import redis.asyncio as redis

from app.api.v1.api_gateway_v62 import (
    APIGatewayCore,
    AuthMethod,
    CircuitBreaker,
    CircuitBreakerState,
    GatewayMetrics,
    LoadBalancer,
    LoadBalancerConfigRequest,
    RateLimiter,
    RateLimitType,
    RouteConfigurationRequest,
    RoutingStrategy,
    SecurityPolicyRequest,
    ServiceRegistrationRequest,
    ServiceRegistry,
    ServiceStatus,
)
from app.core.exceptions import BusinessLogicError
from app.models.user import User


# Test Fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock(spec=redis.Redis)
    redis_mock.hset = AsyncMock()
    redis_mock.hget = AsyncMock()
    redis_mock.hgetall = AsyncMock()
    redis_mock.sadd = AsyncMock()
    redis_mock.smembers = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.incr = AsyncMock()
    redis_mock.lpush = AsyncMock()
    redis_mock.ltrim = AsyncMock()
    redis_mock.lrange = AsyncMock()
    redis_mock.get = AsyncMock()
    redis_mock.zadd = AsyncMock()
    redis_mock.zcard = AsyncMock()
    redis_mock.zremrangebyscore = AsyncMock()
    redis_mock.pipeline = MagicMock()
    redis_mock.hincrby = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id=uuid4(),
        email="test.user@example.com",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def service_registry(mock_redis):
    """Create service registry with mocked Redis"""
    return ServiceRegistry(mock_redis)


@pytest.fixture
def load_balancer(service_registry):
    """Create load balancer with service registry"""
    return LoadBalancer(service_registry)


@pytest.fixture
def circuit_breaker(mock_redis):
    """Create circuit breaker with mocked Redis"""
    return CircuitBreaker(mock_redis)


@pytest.fixture
def rate_limiter(mock_redis):
    """Create rate limiter with mocked Redis"""
    return RateLimiter(mock_redis)


@pytest.fixture
def gateway_core(mock_redis):
    """Create API gateway core with mocked dependencies"""
    return APIGatewayCore(mock_redis)


@pytest.fixture
def gateway_metrics(mock_redis):
    """Create gateway metrics with mocked Redis"""
    return GatewayMetrics(mock_redis)


# Unit Tests for ServiceRegistry
class TestServiceRegistry:
    @pytest.mark.asyncio
    async def test_register_service_success(self, service_registry, mock_redis):
        """Test successful service registration"""

        request = ServiceRegistrationRequest(
            service_name="inventory-service",
            service_version="1.0.0",
            base_url="http://inventory:8000",
            health_check_url="http://inventory:8000/health",
            weight=100,
            tags=["inventory", "core"],
            metadata={"region": "us-east-1"},
        )

        # Execute service registration
        result = await service_registry.register_service(request)

        # Assertions
        assert "service_id" in result
        assert result["status"] == "registered"
        assert "registered_at" in result
        assert result["service_id"].startswith("inventory-service:")

        # Verify Redis calls
        mock_redis.hset.assert_called()
        mock_redis.sadd.assert_called()
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_register_service_failure(self, service_registry, mock_redis):
        """Test service registration failure"""

        # Mock Redis error
        mock_redis.hset.side_effect = Exception("Redis connection error")

        request = ServiceRegistrationRequest(
            service_name="test-service",
            service_version="1.0.0",
            base_url="http://test:8000",
            health_check_url="http://test:8000/health",
        )

        # Execute service registration - should raise BusinessLogicError
        with pytest.raises(BusinessLogicError, match="Failed to register service"):
            await service_registry.register_service(request)

    @pytest.mark.asyncio
    async def test_discover_services_success(self, service_registry, mock_redis):
        """Test successful service discovery"""

        # Mock Redis responses
        service_ids = [b"inventory-service:123", b"inventory-service:456"]
        mock_redis.smembers.return_value = service_ids

        # Mock service info
        healthy_service = {
            "service_id": "inventory-service:123",
            "service_name": "inventory-service",
            "base_url": "http://inventory1:8000",
            "status": ServiceStatus.HEALTHY.value,
            "weight": "100",
        }

        unhealthy_service = {
            "service_id": "inventory-service:456",
            "service_name": "inventory-service",
            "base_url": "http://inventory2:8000",
            "status": ServiceStatus.UNHEALTHY.value,
            "weight": "100",
        }

        def mock_hgetall_side_effect(key):
            if key == "service:inventory-service:123":
                return healthy_service
            elif key == "service:inventory-service:456":
                return unhealthy_service
            return {}

        mock_redis.hgetall.side_effect = mock_hgetall_side_effect

        # Execute service discovery
        services = await service_registry.discover_services("inventory-service")

        # Assertions - should only return healthy services
        assert len(services) == 1
        assert services[0]["service_id"] == "inventory-service:123"
        assert services[0]["status"] == ServiceStatus.HEALTHY.value

    @pytest.mark.asyncio
    async def test_discover_services_empty(self, service_registry, mock_redis):
        """Test service discovery with no services"""

        # Mock empty Redis response
        mock_redis.smembers.return_value = []

        # Execute service discovery
        services = await service_registry.discover_services("nonexistent-service")

        # Assertions
        assert len(services) == 0

    @pytest.mark.asyncio
    async def test_update_service_health_healthy(self, service_registry, mock_redis):
        """Test updating service health to healthy"""

        service_id = "inventory-service:123"
        response_time = 150

        # Execute health update
        await service_registry.update_service_health(
            service_id, ServiceStatus.HEALTHY, response_time
        )

        # Verify Redis calls
        mock_redis.hset.assert_called()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == f"service:{service_id}"
        assert call_args[1]["mapping"]["status"] == ServiceStatus.HEALTHY.value
        assert call_args[1]["mapping"]["last_response_time"] == response_time
        assert call_args[1]["mapping"]["consecutive_failures"] == 0

    @pytest.mark.asyncio
    async def test_update_service_health_unhealthy(self, service_registry, mock_redis):
        """Test updating service health to unhealthy"""

        service_id = "inventory-service:123"

        # Mock current failure count
        mock_redis.hget.return_value = "2"

        # Execute health update
        await service_registry.update_service_health(
            service_id, ServiceStatus.UNHEALTHY
        )

        # Verify Redis calls
        mock_redis.hset.assert_called()
        call_args = mock_redis.hset.call_args
        assert call_args[1]["mapping"]["status"] == ServiceStatus.UNHEALTHY.value
        assert call_args[1]["mapping"]["consecutive_failures"] == 3  # 2 + 1


# Unit Tests for LoadBalancer
class TestLoadBalancer:
    @pytest.mark.asyncio
    async def test_select_service_round_robin(self, load_balancer):
        """Test round robin service selection"""

        services = [
            {"service_id": "svc1", "base_url": "http://svc1:8000"},
            {"service_id": "svc2", "base_url": "http://svc2:8000"},
            {"service_id": "svc3", "base_url": "http://svc3:8000"},
        ]

        # Mock service discovery
        with patch.object(load_balancer.registry, "discover_services") as mock_discover:
            mock_discover.return_value = services

            # Test multiple selections
            selected1 = await load_balancer.select_service(
                "test-service", RoutingStrategy.ROUND_ROBIN
            )
            selected2 = await load_balancer.select_service(
                "test-service", RoutingStrategy.ROUND_ROBIN
            )
            selected3 = await load_balancer.select_service(
                "test-service", RoutingStrategy.ROUND_ROBIN
            )
            selected4 = await load_balancer.select_service(
                "test-service", RoutingStrategy.ROUND_ROBIN
            )

            # Assertions - should cycle through services
            assert selected1["service_id"] == "svc1"
            assert selected2["service_id"] == "svc2"
            assert selected3["service_id"] == "svc3"
            assert selected4["service_id"] == "svc1"  # Back to first

    @pytest.mark.asyncio
    async def test_select_service_no_services(self, load_balancer):
        """Test service selection with no available services"""

        # Mock empty service discovery
        with patch.object(load_balancer.registry, "discover_services") as mock_discover:
            mock_discover.return_value = []

            # Execute service selection
            selected = await load_balancer.select_service(
                "nonexistent-service", RoutingStrategy.ROUND_ROBIN
            )

            # Assertions
            assert selected is None

    @pytest.mark.asyncio
    async def test_select_service_weighted_round_robin(self, load_balancer):
        """Test weighted round robin selection"""

        services = [
            {"service_id": "svc1", "weight": "300"},  # Higher weight
            {"service_id": "svc2", "weight": "100"},  # Lower weight
        ]

        with patch.object(load_balancer.registry, "discover_services") as mock_discover:
            mock_discover.return_value = services

            # Test weighted selection (simplified - would need multiple iterations to verify)
            selected = await load_balancer.select_service(
                "test-service", RoutingStrategy.WEIGHTED_ROUND_ROBIN
            )

            # Should select one of the services
            assert selected["service_id"] in ["svc1", "svc2"]

    @pytest.mark.asyncio
    async def test_select_service_ip_hash(self, load_balancer):
        """Test IP hash-based selection"""

        services = [
            {"service_id": "svc1", "base_url": "http://svc1:8000"},
            {"service_id": "svc2", "base_url": "http://svc2:8000"},
        ]

        with patch.object(load_balancer.registry, "discover_services") as mock_discover:
            mock_discover.return_value = services

            # Test IP hash selection with same IP should return same service
            client_ip = "192.168.1.100"

            selected1 = await load_balancer.select_service(
                "test-service", RoutingStrategy.IP_HASH, client_ip
            )
            selected2 = await load_balancer.select_service(
                "test-service", RoutingStrategy.IP_HASH, client_ip
            )

            # Same IP should get same service
            assert selected1["service_id"] == selected2["service_id"]

    def test_least_connections_selection(self, load_balancer):
        """Test least connections selection"""

        services = [
            {"service_id": "svc1", "active_connections": "5"},
            {"service_id": "svc2", "active_connections": "2"},
            {"service_id": "svc3", "active_connections": "8"},
        ]

        # Execute least connections selection
        selected = load_balancer._least_connections_selection(services)

        # Should select service with least connections
        assert selected["service_id"] == "svc2"

    def test_health_based_selection(self, load_balancer):
        """Test health-based selection"""

        services = [
            {"service_id": "svc1", "consecutive_failures": "3"},
            {"service_id": "svc2", "consecutive_failures": "0"},
            {"service_id": "svc3", "consecutive_failures": "1"},
        ]

        # Execute health-based selection
        selected = load_balancer._health_based_selection(services)

        # Should select healthiest service (least failures)
        assert selected["service_id"] == "svc2"


# Unit Tests for CircuitBreaker
class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_get_state_closed(self, circuit_breaker, mock_redis):
        """Test getting circuit breaker state - closed"""

        # Mock Redis response
        mock_redis.hget.return_value = CircuitBreakerState.CLOSED.value

        # Execute state check
        state = await circuit_breaker.get_state("test-service", "/api/test")

        # Assertions
        assert state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_get_state_default(self, circuit_breaker, mock_redis):
        """Test getting circuit breaker state - default when none exists"""

        # Mock Redis response - no state
        mock_redis.hget.return_value = None

        # Execute state check
        state = await circuit_breaker.get_state("test-service", "/api/test")

        # Assertions - should default to closed
        assert state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_record_success(self, circuit_breaker, mock_redis):
        """Test recording successful request"""

        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        # Mock current state
        with patch.object(circuit_breaker, "get_state") as mock_get_state:
            mock_get_state.return_value = CircuitBreakerState.HALF_OPEN
            mock_redis.hget.return_value = "2"  # Success count

            # Execute success recording
            await circuit_breaker.record_success("test-service", "/api/test")

            # Verify pipeline operations
            mock_pipeline.hincrby.assert_called()
            mock_pipeline.hset.assert_called()
            mock_pipeline.execute.assert_called()

    @pytest.mark.asyncio
    async def test_record_failure(self, circuit_breaker, mock_redis):
        """Test recording failed request"""

        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        # Mock failure count reaching threshold
        mock_redis.hget.return_value = "4"  # One below threshold

        # Execute failure recording
        await circuit_breaker.record_failure("test-service", "/api/test")

        # Verify pipeline operations
        mock_pipeline.hincrby.assert_called()
        mock_pipeline.hset.assert_called()
        mock_pipeline.execute.assert_called()

    @pytest.mark.asyncio
    async def test_can_execute_closed(self, circuit_breaker):
        """Test can execute when circuit is closed"""

        with patch.object(circuit_breaker, "get_state") as mock_get_state:
            mock_get_state.return_value = CircuitBreakerState.CLOSED

            # Execute can execute check
            can_execute = await circuit_breaker.can_execute("test-service", "/api/test")

            # Should allow execution
            assert can_execute

    @pytest.mark.asyncio
    async def test_can_execute_open_before_timeout(self, circuit_breaker, mock_redis):
        """Test can execute when circuit is open before timeout"""

        with patch.object(circuit_breaker, "get_state") as mock_get_state:
            mock_get_state.return_value = CircuitBreakerState.OPEN

            # Mock next attempt time in future
            future_time = datetime.utcnow() + timedelta(seconds=30)
            mock_redis.hget.return_value = future_time.isoformat()

            # Execute can execute check
            can_execute = await circuit_breaker.can_execute("test-service", "/api/test")

            # Should not allow execution
            assert not can_execute

    @pytest.mark.asyncio
    async def test_can_execute_open_after_timeout(self, circuit_breaker, mock_redis):
        """Test can execute when circuit is open after timeout"""

        with patch.object(circuit_breaker, "get_state") as mock_get_state:
            mock_get_state.return_value = CircuitBreakerState.OPEN

            # Mock next attempt time in past
            past_time = datetime.utcnow() - timedelta(seconds=30)
            mock_redis.hget.return_value = past_time.isoformat()

            # Execute can execute check
            can_execute = await circuit_breaker.can_execute("test-service", "/api/test")

            # Should allow execution and transition to half-open
            assert can_execute
            mock_redis.hset.assert_called()


# Unit Tests for RateLimiter
class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_is_allowed_under_limit(self, rate_limiter, mock_redis):
        """Test rate limiting when under limit"""

        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        # Mock current request count under limit
        mock_pipeline.execute.return_value = [None, 5, None, None]  # 5 requests

        # Execute rate limit check
        allowed, info = await rate_limiter.is_allowed("test-key", limit=10, window=60)

        # Assertions
        assert allowed
        assert info["allowed"]
        assert info["limit"] == 10
        assert info["remaining"] == 4  # 10 - 5 - 1

    @pytest.mark.asyncio
    async def test_is_allowed_over_limit(self, rate_limiter, mock_redis):
        """Test rate limiting when over limit"""

        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        # Mock current request count at limit
        mock_pipeline.execute.return_value = [None, 10, None, None]  # At limit

        # Execute rate limit check
        allowed, info = await rate_limiter.is_allowed("test-key", limit=10, window=60)

        # Assertions
        assert not allowed
        assert not info["allowed"]
        assert info["remaining"] == 0

    @pytest.mark.asyncio
    async def test_is_allowed_redis_error(self, rate_limiter, mock_redis):
        """Test rate limiting with Redis error"""

        # Mock Redis error
        mock_redis.pipeline.side_effect = Exception("Redis connection error")

        # Execute rate limit check
        allowed, info = await rate_limiter.is_allowed("test-key", limit=10, window=60)

        # Should fail open
        assert allowed
        assert "error" in info


# Unit Tests for APIGatewayCore
class TestAPIGatewayCore:
    @pytest.mark.asyncio
    async def test_proxy_request_success(self, gateway_core, mock_redis):
        """Test successful request proxying"""

        # Mock request
        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {"Authorization": "Bearer token"}
        mock_request.query_params = {"param": "value"}
        mock_request.body = AsyncMock(return_value=b"")
        mock_request.client.host = "192.168.1.100"

        # Mock route config
        route_config = {
            "service_name": "test-service",
            "target_path": "/api/test",
            "timeout_seconds": 30,
        }

        # Mock service selection
        mock_service = {
            "service_id": "test-service:123",
            "base_url": "http://backend:8000",
        }

        # Mock HTTP response
        mock_http_response = MagicMock()
        mock_http_response.content = b'{"result": "success"}'
        mock_http_response.status_code = 200
        mock_http_response.headers = {"content-type": "application/json"}
        mock_http_response.elapsed.total_seconds.return_value = 0.150

        with (
            patch.object(
                gateway_core.circuit_breaker, "can_execute"
            ) as mock_can_execute,
            patch.object(gateway_core.load_balancer, "select_service") as mock_select,
            patch.object(gateway_core.http_client, "request") as mock_http_request,
            patch.object(
                gateway_core.circuit_breaker, "record_success"
            ) as mock_record_success,
            patch.object(
                gateway_core.service_registry, "update_service_health"
            ) as mock_update_health,
        ):
            mock_can_execute.return_value = True
            mock_select.return_value = mock_service
            mock_http_request.return_value = mock_http_response

            # Execute request proxying
            response = await gateway_core.proxy_request(mock_request, route_config)

            # Assertions
            assert response.status_code == 200
            assert response.body == b'{"result": "success"}'

            # Verify backend calls
            mock_can_execute.assert_called_once()
            mock_select.assert_called_once()
            mock_http_request.assert_called_once()
            mock_record_success.assert_called_once()
            mock_update_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_proxy_request_circuit_breaker_open(self, gateway_core):
        """Test request proxying when circuit breaker is open"""

        mock_request = MagicMock()
        mock_request.url.path = "/api/test"

        route_config = {"service_name": "test-service"}

        # Mock circuit breaker blocking request
        with patch.object(
            gateway_core.circuit_breaker, "can_execute"
        ) as mock_can_execute:
            mock_can_execute.return_value = False

            # Execute request proxying - should raise HTTPException
            with pytest.raises(Exception):  # HTTPException
                await gateway_core.proxy_request(mock_request, route_config)

    @pytest.mark.asyncio
    async def test_proxy_request_no_healthy_services(self, gateway_core):
        """Test request proxying with no healthy services"""

        mock_request = MagicMock()
        mock_request.url.path = "/api/test"

        route_config = {"service_name": "test-service"}

        with (
            patch.object(
                gateway_core.circuit_breaker, "can_execute"
            ) as mock_can_execute,
            patch.object(gateway_core.load_balancer, "select_service") as mock_select,
        ):
            mock_can_execute.return_value = True
            mock_select.return_value = None  # No services available

            # Execute request proxying - should raise HTTPException
            with pytest.raises(Exception):  # HTTPException
                await gateway_core.proxy_request(mock_request, route_config)

    @pytest.mark.asyncio
    async def test_proxy_request_backend_error(self, gateway_core):
        """Test request proxying with backend error"""

        mock_request = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}
        mock_request.body = AsyncMock(return_value=b"")
        mock_request.client.host = "192.168.1.100"

        route_config = {"service_name": "test-service", "timeout_seconds": 30}

        mock_service = {
            "service_id": "test-service:123",
            "base_url": "http://backend:8000",
        }

        with (
            patch.object(
                gateway_core.circuit_breaker, "can_execute"
            ) as mock_can_execute,
            patch.object(gateway_core.load_balancer, "select_service") as mock_select,
            patch.object(gateway_core.http_client, "request") as mock_http_request,
            patch.object(
                gateway_core.circuit_breaker, "record_failure"
            ) as mock_record_failure,
            patch.object(
                gateway_core.service_registry, "update_service_health"
            ) as mock_update_health,
        ):
            mock_can_execute.return_value = True
            mock_select.return_value = mock_service
            mock_http_request.side_effect = Exception("Connection timeout")

            # Execute request proxying - should raise HTTPException
            with pytest.raises(Exception):  # HTTPException
                await gateway_core.proxy_request(mock_request, route_config)

            # Verify failure recording
            mock_record_failure.assert_called_once()
            mock_update_health.assert_called_once()


# Unit Tests for GatewayMetrics
class TestGatewayMetrics:
    @pytest.mark.asyncio
    async def test_record_request(self, gateway_metrics, mock_redis):
        """Test recording request metrics"""

        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        # Execute request recording
        await gateway_metrics.record_request(
            route="/api/test",
            method="GET",
            status_code=200,
            response_time=150.5,
            service_name="test-service",
        )

        # Verify pipeline operations
        mock_pipeline.incr.assert_called()
        mock_pipeline.lpush.assert_called()
        mock_pipeline.ltrim.assert_called()
        mock_pipeline.expire.assert_called()
        mock_pipeline.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_metrics(self, gateway_metrics, mock_redis):
        """Test getting gateway metrics"""

        # Mock Redis responses
        mock_redis.get.side_effect = lambda key: {
            "gateway:total_requests": "1000",
            "gateway:successful_requests": "950",
            "gateway:failed_requests": "50",
        }.get(key, "0")

        # Mock response times
        mock_redis.lrange.return_value = ["150", "200", "175", "120", "300"]

        # Execute metrics retrieval
        metrics = await gateway_metrics.get_metrics()

        # Assertions
        assert metrics["total_requests"] == 1000
        assert metrics["successful_requests"] == 950
        assert metrics["failed_requests"] == 50
        assert metrics["success_rate"] == 95.0
        assert metrics["average_response_time"] == 189.0  # Average of response times
        assert "requests_per_second" in metrics
        assert "generated_at" in metrics

    @pytest.mark.asyncio
    async def test_get_metrics_error(self, gateway_metrics, mock_redis):
        """Test getting metrics with Redis error"""

        # Mock Redis error
        mock_redis.get.side_effect = Exception("Redis connection error")

        # Execute metrics retrieval
        metrics = await gateway_metrics.get_metrics()

        # Should return error info
        assert "error" in metrics


# Unit Tests for Request Models
class TestRequestModels:
    def test_service_registration_request_validation(self):
        """Test service registration request validation"""

        # Valid request
        valid_request = ServiceRegistrationRequest(
            service_name="inventory-service",
            service_version="1.2.0",
            base_url="https://inventory.company.com:8443",
            health_check_url="https://inventory.company.com:8443/health",
            weight=150,
            tags=["inventory", "core", "v1"],
            metadata={"region": "us-west-2", "datacenter": "dc1"},
        )

        assert valid_request.service_name == "inventory-service"
        assert valid_request.weight == 150
        assert len(valid_request.tags) == 3
        assert valid_request.metadata["region"] == "us-west-2"

        # Test weight validation
        with pytest.raises(ValueError):
            ServiceRegistrationRequest(
                service_name="test-service",
                service_version="1.0.0",
                base_url="http://test:8000",
                health_check_url="http://test:8000/health",
                weight=1500,  # Invalid: too high
            )

    def test_route_configuration_request_validation(self):
        """Test route configuration request validation"""

        # Valid request
        valid_request = RouteConfigurationRequest(
            route_path="/api/v1/inventory/*",
            service_name="inventory-service",
            target_path="/internal/inventory",
            methods=["GET", "POST", "PUT"],
            auth_required=True,
            auth_methods=[AuthMethod.JWT, AuthMethod.API_KEY],
            rate_limit={"per_user": 100, "per_minute": 1000},
            timeout_seconds=45,
            retry_attempts=5,
            circuit_breaker_enabled=True,
        )

        assert valid_request.route_path == "/api/v1/inventory/*"
        assert valid_request.service_name == "inventory-service"
        assert len(valid_request.methods) == 3
        assert len(valid_request.auth_methods) == 2
        assert valid_request.timeout_seconds == 45

        # Test timeout validation
        with pytest.raises(ValueError):
            RouteConfigurationRequest(
                route_path="/api/test",
                service_name="test-service",
                timeout_seconds=500,  # Invalid: too high
            )

        # Test retry attempts validation
        with pytest.raises(ValueError):
            RouteConfigurationRequest(
                route_path="/api/test",
                service_name="test-service",
                retry_attempts=15,  # Invalid: too high
            )

    def test_load_balancer_config_request_validation(self):
        """Test load balancer configuration request validation"""

        # Valid request
        valid_request = LoadBalancerConfigRequest(
            service_name="order-service",
            strategy=RoutingStrategy.WEIGHTED_ROUND_ROBIN,
            health_check_interval=60,
            failure_threshold=5,
            recovery_threshold=3,
            sticky_sessions=True,
            session_affinity_key="user_id",
        )

        assert valid_request.service_name == "order-service"
        assert valid_request.strategy == RoutingStrategy.WEIGHTED_ROUND_ROBIN
        assert valid_request.health_check_interval == 60
        assert valid_request.sticky_sessions

        # Test health check interval validation
        with pytest.raises(ValueError):
            LoadBalancerConfigRequest(
                service_name="test-service",
                health_check_interval=2,  # Invalid: too low
            )

        # Test threshold validation
        with pytest.raises(ValueError):
            LoadBalancerConfigRequest(
                service_name="test-service",
                failure_threshold=15,  # Invalid: too high
            )

    def test_security_policy_request_validation(self):
        """Test security policy request validation"""

        # Valid request
        valid_request = SecurityPolicyRequest(
            policy_name="Production API Policy",
            description="Security policy for production API gateway",
            allowed_origins=["https://app.company.com", "https://admin.company.com"],
            allowed_headers=["Authorization", "Content-Type", "X-API-Key"],
            rate_limits={
                RateLimitType.PER_USER: 1000,
                RateLimitType.PER_IP: 5000,
                RateLimitType.GLOBAL: 100000,
            },
            ip_whitelist=["10.0.0.0/8", "192.168.0.0/16"],
            ip_blacklist=["192.168.1.100"],
            require_https=True,
            max_request_size=52428800,  # 50MB
        )

        assert valid_request.policy_name == "Production API Policy"
        assert len(valid_request.allowed_origins) == 2
        assert len(valid_request.rate_limits) == 3
        assert valid_request.require_https
        assert valid_request.max_request_size == 52428800

        # Test max request size validation
        with pytest.raises(ValueError):
            SecurityPolicyRequest(
                policy_name="Test Policy",
                max_request_size=500,  # Invalid: too small
            )


# Unit Tests for Enums
class TestEnums:
    def test_service_status_enum_values(self):
        """Test service status enum values"""

        assert ServiceStatus.HEALTHY == "healthy"
        assert ServiceStatus.DEGRADED == "degraded"
        assert ServiceStatus.UNHEALTHY == "unhealthy"
        assert ServiceStatus.MAINTENANCE == "maintenance"

    def test_routing_strategy_enum_values(self):
        """Test routing strategy enum values"""

        assert RoutingStrategy.ROUND_ROBIN == "round_robin"
        assert RoutingStrategy.WEIGHTED_ROUND_ROBIN == "weighted_round_robin"
        assert RoutingStrategy.LEAST_CONNECTIONS == "least_connections"
        assert RoutingStrategy.IP_HASH == "ip_hash"
        assert RoutingStrategy.HEALTH_BASED == "health_based"

    def test_auth_method_enum_values(self):
        """Test authentication method enum values"""

        assert AuthMethod.JWT == "jwt"
        assert AuthMethod.API_KEY == "api_key"
        assert AuthMethod.OAUTH2 == "oauth2"
        assert AuthMethod.BASIC == "basic"
        assert AuthMethod.MTLS == "mtls"

    def test_rate_limit_type_enum_values(self):
        """Test rate limit type enum values"""

        assert RateLimitType.PER_IP == "per_ip"
        assert RateLimitType.PER_USER == "per_user"
        assert RateLimitType.PER_API_KEY == "per_api_key"
        assert RateLimitType.GLOBAL == "global"

    def test_circuit_breaker_state_enum_values(self):
        """Test circuit breaker state enum values"""

        assert CircuitBreakerState.CLOSED == "closed"
        assert CircuitBreakerState.OPEN == "open"
        assert CircuitBreakerState.HALF_OPEN == "half_open"


# Integration Tests
class TestGatewayIntegration:
    @pytest.mark.asyncio
    async def test_complete_service_lifecycle(self, service_registry, mock_redis):
        """Test complete service registration and discovery lifecycle"""

        # Step 1: Register service
        registration_request = ServiceRegistrationRequest(
            service_name="payment-service",
            service_version="2.0.0",
            base_url="http://payment:8000",
            health_check_url="http://payment:8000/health",
            weight=200,
        )

        registration_result = await service_registry.register_service(
            registration_request
        )
        service_id = registration_result["service_id"]

        assert service_id.startswith("payment-service:")

        # Step 2: Update health status
        await service_registry.update_service_health(
            service_id, ServiceStatus.HEALTHY, 120
        )

        # Step 3: Discover services
        # Mock the discovery to return our registered service
        mock_redis.smembers.return_value = [service_id.encode()]
        mock_redis.hgetall.return_value = {
            "service_id": service_id,
            "service_name": "payment-service",
            "base_url": "http://payment:8000",
            "status": ServiceStatus.HEALTHY.value,
            "weight": "200",
        }

        discovered_services = await service_registry.discover_services(
            "payment-service"
        )

        assert len(discovered_services) == 1
        assert discovered_services[0]["service_id"] == service_id
        assert discovered_services[0]["status"] == ServiceStatus.HEALTHY.value

    @pytest.mark.asyncio
    async def test_load_balancing_with_circuit_breaker(self, gateway_core, mock_redis):
        """Test load balancing integration with circuit breaker"""

        # Mock services
        services = [
            {"service_id": "svc1", "base_url": "http://svc1:8000"},
            {"service_id": "svc2", "base_url": "http://svc2:8000"},
        ]

        # Mock service discovery
        with (
            patch.object(
                gateway_core.service_registry, "discover_services"
            ) as mock_discover,
            patch.object(
                gateway_core.circuit_breaker, "can_execute"
            ) as mock_can_execute,
        ):
            mock_discover.return_value = services
            mock_can_execute.return_value = True

            # Test service selection
            selected_service = await gateway_core.load_balancer.select_service(
                "test-service", RoutingStrategy.ROUND_ROBIN
            )

            assert selected_service is not None
            assert selected_service["service_id"] in ["svc1", "svc2"]

            # Verify circuit breaker integration
            can_execute = await gateway_core.circuit_breaker.can_execute(
                "test-service", "/api/test"
            )
            assert can_execute

    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, gateway_core, mock_redis):
        """Test rate limiting integration"""

        # Mock pipeline for rate limiting
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        # Test rate limiting under limit
        mock_pipeline.execute.return_value = [None, 5, None, None]  # 5 requests

        allowed, info = await gateway_core.rate_limiter.is_allowed(
            "user:123", limit=10, window=60
        )

        assert allowed
        assert info["remaining"] == 4

        # Test rate limiting over limit
        mock_pipeline.execute.return_value = [None, 10, None, None]  # At limit

        allowed, info = await gateway_core.rate_limiter.is_allowed(
            "user:123", limit=10, window=60
        )

        assert not allowed
        assert info["remaining"] == 0


# Performance Tests
class TestGatewayPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_service_registrations(self, service_registry, mock_redis):
        """Test concurrent service registrations"""

        # Create multiple registration requests
        requests = []
        for i in range(10):
            requests.append(
                ServiceRegistrationRequest(
                    service_name=f"test-service-{i}",
                    service_version="1.0.0",
                    base_url=f"http://test{i}:8000",
                    health_check_url=f"http://test{i}:8000/health",
                )
            )

        # Execute concurrent registrations
        import asyncio

        start_time = time.time()

        results = await asyncio.gather(
            *[service_registry.register_service(req) for req in requests],
            return_exceptions=True,
        )

        execution_time = time.time() - start_time

        # Verify results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 10
        assert execution_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_high_frequency_rate_limiting(self, rate_limiter, mock_redis):
        """Test rate limiting under high frequency requests"""

        # Mock pipeline for consistent responses
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        # Simulate many requests from same key
        request_count = 100
        allowed_count = 0

        for i in range(request_count):
            # Mock current request count
            mock_pipeline.execute.return_value = [None, i, None, None]

            allowed, info = await rate_limiter.is_allowed(
                "test-key", limit=50, window=60
            )
            if allowed:
                allowed_count += 1

        # Should allow up to limit
        assert allowed_count <= 50

    @pytest.mark.asyncio
    async def test_load_balancer_distribution(self, load_balancer):
        """Test load balancer distribution fairness"""

        services = [
            {"service_id": f"svc{i}", "base_url": f"http://svc{i}:8000"}
            for i in range(5)
        ]

        # Mock service discovery
        with patch.object(load_balancer.registry, "discover_services") as mock_discover:
            mock_discover.return_value = services

            # Test distribution over many requests
            selections = {}
            for _ in range(100):
                selected = await load_balancer.select_service(
                    "test-service", RoutingStrategy.ROUND_ROBIN
                )
                service_id = selected["service_id"]
                selections[service_id] = selections.get(service_id, 0) + 1

            # Verify relatively even distribution
            assert len(selections) == 5
            for count in selections.values():
                assert 15 <= count <= 25  # Should be around 20 each with some variance


if __name__ == "__main__":
    pytest.main([__file__])
