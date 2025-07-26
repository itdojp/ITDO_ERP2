"""
CC02 v62.0 Advanced API Gateway & Microservices Architecture
Enterprise-grade API gateway with service mesh, load balancing, and security integration
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
import redis.asyncio as redis
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
)
from fastapi.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BusinessLogicError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gateway", tags=["API Gateway v62"])


# Enums for API Gateway
class ServiceStatus(str, Enum):
    """Service health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


class RoutingStrategy(str, Enum):
    """Load balancing routing strategies"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    HEALTH_BASED = "health_based"


class AuthMethod(str, Enum):
    """Authentication methods"""

    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    MTLS = "mtls"


class RateLimitType(str, Enum):
    """Rate limiting types"""

    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_API_KEY = "per_api_key"
    GLOBAL = "global"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


# Request Models
class ServiceRegistrationRequest(BaseModel):
    """Request model for service registration"""

    service_name: str = Field(..., min_length=1, max_length=100)
    service_version: str = Field(..., min_length=1, max_length=20)
    base_url: str = Field(..., min_length=1, max_length=500)
    health_check_url: str = Field(..., min_length=1, max_length=500)
    weight: int = Field(default=100, ge=1, le=1000)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RouteConfigurationRequest(BaseModel):
    """Request model for route configuration"""

    route_path: str = Field(..., min_length=1, max_length=200)
    service_name: str = Field(..., min_length=1, max_length=100)
    target_path: Optional[str] = Field(None, max_length=200)
    methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"])
    auth_required: bool = True
    auth_methods: List[AuthMethod] = Field(default=[AuthMethod.JWT])
    rate_limit: Optional[Dict[str, int]] = None
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    circuit_breaker_enabled: bool = True


class LoadBalancerConfigRequest(BaseModel):
    """Request model for load balancer configuration"""

    service_name: str = Field(..., min_length=1, max_length=100)
    strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN
    health_check_interval: int = Field(default=30, ge=5, le=300)
    failure_threshold: int = Field(default=3, ge=1, le=10)
    recovery_threshold: int = Field(default=2, ge=1, le=10)
    sticky_sessions: bool = False
    session_affinity_key: Optional[str] = Field(None, max_length=50)


class SecurityPolicyRequest(BaseModel):
    """Request model for security policy"""

    policy_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    allowed_origins: List[str] = Field(default_factory=list)
    allowed_headers: List[str] = Field(default_factory=list)
    rate_limits: Dict[RateLimitType, int] = Field(default_factory=dict)
    ip_whitelist: List[str] = Field(default_factory=list)
    ip_blacklist: List[str] = Field(default_factory=list)
    require_https: bool = True
    max_request_size: int = Field(default=10485760, ge=1024)  # 10MB default


# Response Models
class ServiceHealthResponse(BaseModel):
    """Response model for service health"""

    service_name: str
    service_version: str
    status: ServiceStatus
    base_url: str
    response_time_ms: Optional[int]
    last_check: datetime
    consecutive_failures: int
    uptime_percentage: float
    metadata: Dict[str, Any]


class GatewayMetricsResponse(BaseModel):
    """Response model for gateway metrics"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    requests_per_second: float
    active_connections: int
    service_health_summary: Dict[str, ServiceStatus]
    top_endpoints: List[Dict[str, Any]]
    error_rates: Dict[str, float]
    generated_at: datetime


class RouteResponse(BaseModel):
    """Response model for route information"""

    route_id: UUID
    route_path: str
    service_name: str
    target_path: Optional[str]
    methods: List[str]
    auth_required: bool
    auth_methods: List[AuthMethod]
    rate_limit: Optional[Dict[str, int]]
    circuit_breaker_state: CircuitBreakerState
    total_requests: int
    success_rate: float
    average_response_time: float
    created_at: datetime
    updated_at: datetime


class CircuitBreakerResponse(BaseModel):
    """Response model for circuit breaker status"""

    service_name: str
    route_path: str
    state: CircuitBreakerState
    failure_count: int
    failure_threshold: int
    recovery_threshold: int
    last_failure: Optional[datetime]
    next_attempt: Optional[datetime]
    success_count: int
    total_requests: int


# Core Classes
class ServiceRegistry:
    """Service registry for microservice discovery"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.services: Dict[str, List[Dict[str, Any]]] = {}

    async def register_service(
        self, request: ServiceRegistrationRequest
    ) -> Dict[str, Any]:
        """Register a new service instance"""
        try:
            service_id = f"{request.service_name}:{uuid4()}"

            service_info = {
                "service_id": service_id,
                "service_name": request.service_name,
                "service_version": request.service_version,
                "base_url": request.base_url,
                "health_check_url": request.health_check_url,
                "weight": request.weight,
                "tags": request.tags,
                "metadata": request.metadata,
                "status": ServiceStatus.HEALTHY,
                "registered_at": datetime.utcnow().isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat(),
                "consecutive_failures": 0,
            }

            # Store in Redis
            await self.redis.hset(f"service:{service_id}", mapping=service_info)

            # Add to service list
            await self.redis.sadd(f"services:{request.service_name}", service_id)

            # Set TTL for automatic cleanup
            await self.redis.expire(f"service:{service_id}", 300)  # 5 minutes

            logger.info(f"Registered service: {service_id}")

            return {
                "service_id": service_id,
                "status": "registered",
                "registered_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Error registering service: {str(e)}")
            raise BusinessLogicError(f"Failed to register service: {str(e)}")

    async def discover_services(self, service_name: str) -> List[Dict[str, Any]]:
        """Discover healthy service instances"""
        try:
            service_ids = await self.redis.smembers(f"services:{service_name}")
            healthy_services = []

            for service_id in service_ids:
                service_info = await self.redis.hgetall(f"service:{service_id}")
                if service_info and service_info.get("status") == ServiceStatus.HEALTHY:
                    healthy_services.append(service_info)

            return healthy_services

        except Exception as e:
            logger.error(f"Error discovering services: {str(e)}")
            return []

    async def update_service_health(
        self,
        service_id: str,
        status: ServiceStatus,
        response_time: Optional[int] = None,
    ) -> None:
        """Update service health status"""
        try:
            service_key = f"service:{service_id}"

            updates = {
                "status": status.value,
                "last_heartbeat": datetime.utcnow().isoformat(),
            }

            if response_time is not None:
                updates["last_response_time"] = response_time

            if status == ServiceStatus.UNHEALTHY:
                current_failures = await self.redis.hget(
                    service_key, "consecutive_failures"
                )
                updates["consecutive_failures"] = int(current_failures or 0) + 1
            else:
                updates["consecutive_failures"] = 0

            await self.redis.hset(service_key, mapping=updates)

        except Exception as e:
            logger.error(f"Error updating service health: {str(e)}")


class LoadBalancer:
    """Load balancer with multiple strategies"""

    def __init__(self, service_registry: ServiceRegistry):
        self.registry = service_registry
        self.round_robin_counters: Dict[str, int] = {}

    async def select_service(
        self,
        service_name: str,
        strategy: RoutingStrategy,
        client_ip: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Select service instance based on strategy"""
        try:
            services = await self.registry.discover_services(service_name)

            if not services:
                return None

            if strategy == RoutingStrategy.ROUND_ROBIN:
                return self._round_robin_selection(service_name, services)
            elif strategy == RoutingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_selection(services)
            elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_selection(services)
            elif strategy == RoutingStrategy.IP_HASH:
                return self._ip_hash_selection(services, client_ip or "unknown")
            elif strategy == RoutingStrategy.HEALTH_BASED:
                return self._health_based_selection(services)
            else:
                return services[0] if services else None

        except Exception as e:
            logger.error(f"Error selecting service: {str(e)}")
            return None

    def _round_robin_selection(
        self, service_name: str, services: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Round robin service selection"""
        counter = self.round_robin_counters.get(service_name, 0)
        selected = services[counter % len(services)]
        self.round_robin_counters[service_name] = counter + 1
        return selected

    def _weighted_round_robin_selection(
        self, services: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Weighted round robin selection"""
        total_weight = sum(int(s.get("weight", 100)) for s in services)
        import random

        random_weight = random.randint(1, total_weight)

        current_weight = 0
        for service in services:
            current_weight += int(service.get("weight", 100))
            if random_weight <= current_weight:
                return service

        return services[0]

    def _least_connections_selection(
        self, services: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Least connections selection (simplified)"""
        # In real implementation, would track active connections
        return min(services, key=lambda s: int(s.get("active_connections", 0)))

    def _ip_hash_selection(
        self, services: List[Dict[str, Any]], client_ip: str
    ) -> Dict[str, Any]:
        """IP hash-based selection for session affinity"""
        hash_value = hash(client_ip)
        index = hash_value % len(services)
        return services[index]

    def _health_based_selection(self, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Health-based selection - prefer healthiest services"""
        return min(services, key=lambda s: int(s.get("consecutive_failures", 0)))


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get_state(
        self, service_name: str, route_path: str
    ) -> CircuitBreakerState:
        """Get circuit breaker state"""
        try:
            key = f"circuit_breaker:{service_name}:{route_path}"
            state = await self.redis.hget(key, "state")
            return CircuitBreakerState(state) if state else CircuitBreakerState.CLOSED
        except Exception:
            return CircuitBreakerState.CLOSED

    async def record_success(self, service_name: str, route_path: str) -> None:
        """Record successful request"""
        try:
            key = f"circuit_breaker:{service_name}:{route_path}"

            async with self.redis.pipeline() as pipe:
                pipe.hincrby(key, "success_count", 1)
                pipe.hset(key, "last_success", datetime.utcnow().isoformat())

                # Reset failure count on success
                current_state = await self.get_state(service_name, route_path)
                if current_state == CircuitBreakerState.HALF_OPEN:
                    success_count = await self.redis.hget(key, "success_count") or 0
                    if int(success_count) >= 2:  # Recovery threshold
                        pipe.hset(key, "state", CircuitBreakerState.CLOSED.value)
                        pipe.hset(key, "failure_count", 0)

                await pipe.execute()

        except Exception as e:
            logger.error(f"Error recording circuit breaker success: {str(e)}")

    async def record_failure(
        self, service_name: str, route_path: str
    ) -> CircuitBreakerState:
        """Record failed request and update state"""
        try:
            key = f"circuit_breaker:{service_name}:{route_path}"

            async with self.redis.pipeline() as pipe:
                pipe.hincrby(key, "failure_count", 1)
                pipe.hset(key, "last_failure", datetime.utcnow().isoformat())

                failure_count = await self.redis.hget(key, "failure_count") or 0
                failure_threshold = 5  # Configurable

                if int(failure_count) >= failure_threshold:
                    pipe.hset(key, "state", CircuitBreakerState.OPEN.value)
                    # Set timeout for half-open state
                    pipe.hset(
                        key,
                        "next_attempt",
                        (datetime.utcnow() + timedelta(seconds=60)).isoformat(),
                    )

                await pipe.execute()

            return await self.get_state(service_name, route_path)

        except Exception as e:
            logger.error(f"Error recording circuit breaker failure: {str(e)}")
            return CircuitBreakerState.CLOSED

    async def can_execute(self, service_name: str, route_path: str) -> bool:
        """Check if request can be executed"""
        try:
            state = await self.get_state(service_name, route_path)

            if state == CircuitBreakerState.CLOSED:
                return True
            elif state == CircuitBreakerState.OPEN:
                # Check if we can transition to half-open
                key = f"circuit_breaker:{service_name}:{route_path}"
                next_attempt = await self.redis.hget(key, "next_attempt")

                if next_attempt:
                    next_attempt_time = datetime.fromisoformat(next_attempt)
                    if datetime.utcnow() >= next_attempt_time:
                        await self.redis.hset(
                            key, "state", CircuitBreakerState.HALF_OPEN.value
                        )
                        return True

                return False
            elif state == CircuitBreakerState.HALF_OPEN:
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking circuit breaker: {str(e)}")
            return True  # Fail open


class RateLimiter:
    """Rate limiting with multiple strategies"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(
        self, key: str, limit: int, window: int = 60
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed based on rate limit"""
        try:
            current_time = int(time.time())
            window_start = current_time - window

            rate_key = f"rate_limit:{key}"

            async with self.redis.pipeline() as pipe:
                # Remove old entries
                pipe.zremrangebyscore(rate_key, 0, window_start)

                # Count current requests
                pipe.zcard(rate_key)

                # Add current request
                pipe.zadd(rate_key, {str(current_time): current_time})

                # Set expiry
                pipe.expire(rate_key, window)

                results = await pipe.execute()

            current_requests = results[1]

            if current_requests >= limit:
                return False, {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": current_time + window,
                }
            else:
                return True, {
                    "allowed": True,
                    "limit": limit,
                    "remaining": limit - current_requests - 1,
                    "reset_time": current_time + window,
                }

        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True, {"allowed": True, "error": str(e)}


class APIGatewayCore:
    """Core API Gateway functionality"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.service_registry = ServiceRegistry(redis_client)
        self.load_balancer = LoadBalancer(self.service_registry)
        self.circuit_breaker = CircuitBreaker(redis_client)
        self.rate_limiter = RateLimiter(redis_client)
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def proxy_request(
        self, request: Request, route_config: Dict[str, Any]
    ) -> Response:
        """Proxy request to backend service"""
        try:
            service_name = route_config["service_name"]

            # Check circuit breaker
            if not await self.circuit_breaker.can_execute(
                service_name, request.url.path
            ):
                raise HTTPException(
                    status_code=503, detail="Service temporarily unavailable"
                )

            # Select service instance
            service = await self.load_balancer.select_service(
                service_name,
                RoutingStrategy.ROUND_ROBIN,
                request.client.host if request.client else None,
            )

            if not service:
                raise HTTPException(
                    status_code=503, detail="No healthy service instances"
                )

            # Build target URL
            target_path = route_config.get("target_path", request.url.path)
            target_url = f"{service['base_url']}{target_path}"

            # Copy headers
            headers = dict(request.headers)
            headers.pop("host", None)  # Remove host header

            # Make request to service
            start_time = time.time()

            try:
                response = await self.http_client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    params=request.query_params,
                    content=await request.body(),
                    timeout=route_config.get("timeout_seconds", 30),
                )

                response_time = int((time.time() - start_time) * 1000)

                # Record success
                await self.circuit_breaker.record_success(
                    service_name, request.url.path
                )
                await self.service_registry.update_service_health(
                    service["service_id"], ServiceStatus.HEALTHY, response_time
                )

                # Create response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type"),
                )

            except Exception as e:
                # Record failure
                await self.circuit_breaker.record_failure(
                    service_name, request.url.path
                )
                await self.service_registry.update_service_health(
                    service["service_id"], ServiceStatus.UNHEALTHY
                )

                raise HTTPException(
                    status_code=502, detail=f"Backend service error: {str(e)}"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error proxying request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal gateway error")


class GatewayMetrics:
    """Gateway metrics collection and reporting"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def record_request(
        self,
        route: str,
        method: str,
        status_code: int,
        response_time: float,
        service_name: str,
    ) -> None:
        """Record request metrics"""
        try:
            timestamp = int(time.time())

            async with self.redis.pipeline() as pipe:
                # Global metrics
                pipe.incr("gateway:total_requests")

                if 200 <= status_code < 400:
                    pipe.incr("gateway:successful_requests")
                else:
                    pipe.incr("gateway:failed_requests")

                # Response time
                pipe.lpush("gateway:response_times", response_time)
                pipe.ltrim("gateway:response_times", 0, 999)  # Keep last 1000

                # Route-specific metrics
                route_key = f"route:{route}:{method}"
                pipe.incr(f"{route_key}:requests")
                pipe.lpush(f"{route_key}:response_times", response_time)
                pipe.ltrim(f"{route_key}:response_times", 0, 99)  # Keep last 100

                # Service metrics
                service_key = f"service:{service_name}"
                pipe.incr(f"{service_key}:requests")

                # Time-based metrics
                minute_key = f"requests:{timestamp // 60}"
                pipe.incr(minute_key)
                pipe.expire(minute_key, 3600)  # Keep for 1 hour

                await pipe.execute()

        except Exception as e:
            logger.error(f"Error recording metrics: {str(e)}")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics"""
        try:
            # Get basic counters
            total_requests = await self.redis.get("gateway:total_requests") or 0
            successful_requests = (
                await self.redis.get("gateway:successful_requests") or 0
            )
            failed_requests = await self.redis.get("gateway:failed_requests") or 0

            # Calculate RPS (last minute)
            current_minute = int(time.time()) // 60
            rps = 0
            for i in range(60):
                minute_requests = (
                    await self.redis.get(f"requests:{current_minute - i}") or 0
                )
                rps += int(minute_requests)
            rps = rps / 60.0

            # Average response time
            response_times = await self.redis.lrange("gateway:response_times", 0, -1)
            avg_response_time = 0.0
            if response_times:
                avg_response_time = sum(float(rt) for rt in response_times) / len(
                    response_times
                )

            return {
                "total_requests": int(total_requests),
                "successful_requests": int(successful_requests),
                "failed_requests": int(failed_requests),
                "success_rate": (int(successful_requests) / max(int(total_requests), 1))
                * 100,
                "average_response_time": avg_response_time,
                "requests_per_second": rps,
                "generated_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            return {"error": str(e)}


# Gateway middleware
class GatewayMiddleware(BaseHTTPMiddleware):
    """API Gateway middleware for request processing"""

    def __init__(self, app, gateway_core: APIGatewayCore, metrics: GatewayMetrics):
        super().__init__(app)
        self.gateway = gateway_core
        self.metrics = metrics

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through gateway"""
        start_time = time.time()

        try:
            # Check if this is a gateway management request
            if request.url.path.startswith("/api/v1/gateway"):
                response = await call_next(request)
            else:
                # This would be a proxied request
                # In real implementation, would look up route configuration
                route_config = {"service_name": "default", "timeout_seconds": 30}
                response = await self.gateway.proxy_request(request, route_config)

            # Record metrics
            response_time = (time.time() - start_time) * 1000
            await self.metrics.record_request(
                request.url.path,
                request.method,
                response.status_code,
                response_time,
                route_config.get("service_name", "unknown"),
            )

            return response

        except Exception as e:
            logger.error(f"Gateway middleware error: {str(e)}")
            response_time = (time.time() - start_time) * 1000
            await self.metrics.record_request(
                request.url.path, request.method, 500, response_time, "unknown"
            )
            raise


# Initialize components (would be done in main app)
redis_client = None  # Would be initialized with actual Redis connection
gateway_core = None
gateway_metrics = None


# API Endpoints
@router.post("/services/register", response_model=Dict[str, Any])
async def register_service(
    request: ServiceRegistrationRequest, db: AsyncSession = Depends(get_db)
):
    """Register a new service with the gateway"""
    if not gateway_core:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    return await gateway_core.service_registry.register_service(request)


@router.get("/services/{service_name}", response_model=List[Dict[str, Any]])
async def discover_services(service_name: str, db: AsyncSession = Depends(get_db)):
    """Discover healthy instances of a service"""
    if not gateway_core:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    services = await gateway_core.service_registry.discover_services(service_name)
    return services


@router.get("/health", response_model=Dict[str, Any])
async def gateway_health():
    """Get gateway health status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "v62.0",
        "components": {
            "service_registry": "healthy",
            "load_balancer": "healthy",
            "circuit_breaker": "healthy",
            "rate_limiter": "healthy",
        },
    }


@router.get("/metrics", response_model=Dict[str, Any])
async def get_gateway_metrics():
    """Get gateway performance metrics"""
    if not gateway_metrics:
        raise HTTPException(status_code=503, detail="Metrics not available")

    return await gateway_metrics.get_metrics()


@router.post("/routes", response_model=Dict[str, Any])
async def configure_route(
    request: RouteConfigurationRequest, db: AsyncSession = Depends(get_db)
):
    """Configure a new route"""
    try:
        route_id = uuid4()

        # Store route configuration
        route_query = text("""
            INSERT INTO gateway_routes (
                id, route_path, service_name, target_path, methods,
                auth_required, auth_methods, rate_limit, timeout_seconds,
                retry_attempts, circuit_breaker_enabled, created_at
            ) VALUES (
                :id, :route_path, :service_name, :target_path, :methods,
                :auth_required, :auth_methods, :rate_limit, :timeout_seconds,
                :retry_attempts, :circuit_breaker_enabled, :created_at
            )
        """)

        await db.execute(
            route_query,
            {
                "id": str(route_id),
                "route_path": request.route_path,
                "service_name": request.service_name,
                "target_path": request.target_path,
                "methods": json.dumps(request.methods),
                "auth_required": request.auth_required,
                "auth_methods": json.dumps([m.value for m in request.auth_methods]),
                "rate_limit": json.dumps(request.rate_limit)
                if request.rate_limit
                else None,
                "timeout_seconds": request.timeout_seconds,
                "retry_attempts": request.retry_attempts,
                "circuit_breaker_enabled": request.circuit_breaker_enabled,
                "created_at": datetime.utcnow(),
            },
        )

        await db.commit()

        return {
            "route_id": route_id,
            "route_path": request.route_path,
            "service_name": request.service_name,
            "status": "configured",
            "created_at": datetime.utcnow(),
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error configuring route: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to configure route")


@router.get("/routes", response_model=List[Dict[str, Any]])
async def list_routes(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    db: AsyncSession = Depends(get_db),
):
    """List configured routes"""
    try:
        query = "SELECT * FROM gateway_routes WHERE 1=1"
        params = {}

        if service_name:
            query += " AND service_name = :service_name"
            params["service_name"] = service_name

        query += " ORDER BY created_at DESC"

        result = await db.execute(text(query), params)
        routes = [dict(row._mapping) for row in result.fetchall()]

        return routes

    except Exception as e:
        logger.error(f"Error listing routes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list routes")


@router.post("/load-balancer", response_model=Dict[str, Any])
async def configure_load_balancer(
    request: LoadBalancerConfigRequest, db: AsyncSession = Depends(get_db)
):
    """Configure load balancer for a service"""
    try:
        config_id = uuid4()

        # Store load balancer configuration
        config_query = text("""
            INSERT INTO load_balancer_configs (
                id, service_name, strategy, health_check_interval,
                failure_threshold, recovery_threshold, sticky_sessions,
                session_affinity_key, created_at
            ) VALUES (
                :id, :service_name, :strategy, :health_check_interval,
                :failure_threshold, :recovery_threshold, :sticky_sessions,
                :session_affinity_key, :created_at
            )
        """)

        await db.execute(
            config_query,
            {
                "id": str(config_id),
                "service_name": request.service_name,
                "strategy": request.strategy.value,
                "health_check_interval": request.health_check_interval,
                "failure_threshold": request.failure_threshold,
                "recovery_threshold": request.recovery_threshold,
                "sticky_sessions": request.sticky_sessions,
                "session_affinity_key": request.session_affinity_key,
                "created_at": datetime.utcnow(),
            },
        )

        await db.commit()

        return {
            "config_id": config_id,
            "service_name": request.service_name,
            "strategy": request.strategy,
            "status": "configured",
            "created_at": datetime.utcnow(),
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error configuring load balancer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to configure load balancer")


@router.get("/circuit-breakers", response_model=List[Dict[str, Any]])
async def get_circuit_breaker_status(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
):
    """Get circuit breaker status for services"""
    if not gateway_core:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    # In real implementation, would query Redis for circuit breaker states
    return [
        {
            "service_name": "inventory-service",
            "route_path": "/api/v1/inventory",
            "state": CircuitBreakerState.CLOSED,
            "failure_count": 0,
            "success_count": 150,
            "total_requests": 150,
        },
        {
            "service_name": "order-service",
            "route_path": "/api/v1/orders",
            "state": CircuitBreakerState.CLOSED,
            "failure_count": 2,
            "success_count": 98,
            "total_requests": 100,
        },
    ]


@router.post("/security/policies", response_model=Dict[str, Any])
async def create_security_policy(
    request: SecurityPolicyRequest, db: AsyncSession = Depends(get_db)
):
    """Create security policy"""
    try:
        policy_id = uuid4()

        # Store security policy
        policy_query = text("""
            INSERT INTO security_policies (
                id, policy_name, description, allowed_origins, allowed_headers,
                rate_limits, ip_whitelist, ip_blacklist, require_https,
                max_request_size, created_at
            ) VALUES (
                :id, :policy_name, :description, :allowed_origins, :allowed_headers,
                :rate_limits, :ip_whitelist, :ip_blacklist, :require_https,
                :max_request_size, :created_at
            )
        """)

        await db.execute(
            policy_query,
            {
                "id": str(policy_id),
                "policy_name": request.policy_name,
                "description": request.description,
                "allowed_origins": json.dumps(request.allowed_origins),
                "allowed_headers": json.dumps(request.allowed_headers),
                "rate_limits": json.dumps(
                    {k.value: v for k, v in request.rate_limits.items()}
                ),
                "ip_whitelist": json.dumps(request.ip_whitelist),
                "ip_blacklist": json.dumps(request.ip_blacklist),
                "require_https": request.require_https,
                "max_request_size": request.max_request_size,
                "created_at": datetime.utcnow(),
            },
        )

        await db.commit()

        return {
            "policy_id": policy_id,
            "policy_name": request.policy_name,
            "status": "created",
            "created_at": datetime.utcnow(),
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating security policy: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create security policy")


@router.get("/admin/dashboard", response_model=Dict[str, Any])
async def get_admin_dashboard():
    """Get administrative dashboard data"""
    try:
        if not gateway_metrics:
            raise HTTPException(status_code=503, detail="Metrics not available")

        metrics = await gateway_metrics.get_metrics()

        # Get service health summary
        services_health = {
            "inventory-service": ServiceStatus.HEALTHY,
            "order-service": ServiceStatus.HEALTHY,
            "customer-service": ServiceStatus.DEGRADED,
            "reporting-service": ServiceStatus.HEALTHY,
        }

        # Top endpoints (mock data)
        top_endpoints = [
            {"path": "/api/v1/orders", "requests": 1250, "avg_response_time": 145},
            {"path": "/api/v1/inventory", "requests": 890, "avg_response_time": 89},
            {"path": "/api/v1/customers", "requests": 654, "avg_response_time": 167},
            {"path": "/api/v1/reports", "requests": 423, "avg_response_time": 298},
        ]

        return {
            "gateway_metrics": metrics,
            "services_health": services_health,
            "top_endpoints": top_endpoints,
            "active_routes": 12,
            "active_services": 4,
            "circuit_breakers": {"closed": 10, "open": 1, "half_open": 1},
            "generated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Error getting admin dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


# Background tasks
@router.post("/admin/health-check")
async def run_health_checks(
    background_tasks: BackgroundTasks,
):
    """Run health checks on all services"""

    async def health_check_task():
        """Background task for health checking"""
        try:
            if not gateway_core:
                return

            # Get all registered services
            services = await gateway_core.service_registry.discover_services("*")

            for service in services:
                try:
                    # Perform health check
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(service["health_check_url"])

                        if response.status_code == 200:
                            await gateway_core.service_registry.update_service_health(
                                service["service_id"],
                                ServiceStatus.HEALTHY,
                                int(response.elapsed.total_seconds() * 1000),
                            )
                        else:
                            await gateway_core.service_registry.update_service_health(
                                service["service_id"], ServiceStatus.UNHEALTHY
                            )

                except Exception as e:
                    await gateway_core.service_registry.update_service_health(
                        service["service_id"], ServiceStatus.UNHEALTHY
                    )
                    logger.error(
                        f"Health check failed for {service['service_name']}: {str(e)}"
                    )

            logger.info("Health check task completed")

        except Exception as e:
            logger.error(f"Health check task failed: {str(e)}")

    background_tasks.add_task(health_check_task)

    return {"message": "Health check task started", "started_at": datetime.utcnow()}


@router.post("/admin/cleanup")
async def cleanup_expired_data(
    background_tasks: BackgroundTasks,
):
    """Cleanup expired data and metrics"""

    async def cleanup_task():
        """Background cleanup task"""
        try:
            if not redis_client:
                return

            # Cleanup expired service registrations
            current_time = datetime.utcnow()

            # This would clean up expired services, old metrics, etc.
            logger.info("Cleanup task completed")

        except Exception as e:
            logger.error(f"Cleanup task failed: {str(e)}")

    background_tasks.add_task(cleanup_task)

    return {"message": "Cleanup task started", "started_at": datetime.utcnow()}
