"""Microservices management API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.microservices import (
    service_manager,
    ServiceStatus,
    CircuitBreakerState,
    CircuitBreakerConfig,
    check_microservices_health,
)
from app.core.api_gateway import (
    api_gateway,
    RouteConfig,
    RateLimitRule,
    RateLimitStrategy,
    check_api_gateway_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class ServiceInstanceResponse(BaseModel):
    """Service instance response schema."""
    service_id: str
    service_name: str
    host: str
    port: int
    version: str
    health_check_url: str
    status: ServiceStatus
    address: str
    metadata: Dict[str, Any]
    tags: List[str]
    last_heartbeat: Optional[datetime]
    registration_time: datetime

    class Config:
        from_attributes = True


class ServiceRegistrationRequest(BaseModel):
    """Service registration request schema."""
    service_name: str = Field(..., max_length=100)
    host: str = Field(..., max_length=255)
    port: int = Field(..., ge=1, le=65535)
    version: str = Field("1.0.0", max_length=50)
    health_check_url: str = Field("/health", max_length=255)
    metadata: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []


class ServiceHealthResponse(BaseModel):
    """Service health response schema."""
    service_name: str
    total_instances: int
    healthy_instances: int
    instances: List[ServiceInstanceResponse]


class CircuitBreakerResponse(BaseModel):
    """Circuit breaker status response."""
    name: str
    state: CircuitBreakerState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    last_request_time: Optional[datetime]

    class Config:
        from_attributes = True


class SystemStatusResponse(BaseModel):
    """System status response schema."""
    timestamp: datetime
    current_service: Optional[ServiceInstanceResponse]
    registered_services: List[ServiceInstanceResponse]
    circuit_breakers: List[CircuitBreakerResponse]
    health_checker_running: bool


class RouteConfigRequest(BaseModel):
    """Route configuration request schema."""
    path_pattern: str = Field(..., max_length=255)
    service_name: str = Field(..., max_length=100)
    target_path: Optional[str] = Field(None, max_length=255)
    methods: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    headers: Optional[Dict[str, str]] = {}
    rate_limit: Optional[int] = Field(None, ge=1)
    auth_required: bool = True
    timeout: int = Field(30, ge=1, le=300)
    retries: int = Field(3, ge=0, le=10)
    circuit_breaker: bool = True
    cache_ttl: Optional[int] = Field(None, ge=0)
    weight: int = Field(100, ge=1, le=1000)


class RateLimitRuleRequest(BaseModel):
    """Rate limit rule request schema."""
    pattern: str = Field(..., max_length=255)
    key_pattern: str = Field(..., max_length=100)
    requests_per_minute: int = Field(..., ge=1)
    requests_per_hour: int = Field(..., ge=1)
    requests_per_day: int = Field(..., ge=1)
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_size: Optional[int] = Field(None, ge=1)


class GatewayStatsResponse(BaseModel):
    """Gateway statistics response."""
    routes_configured: int
    rate_limits_configured: int
    active_rate_limits: int
    pre_request_hooks: int
    post_response_hooks: int
    timestamp: datetime
    status: str


# Service Discovery endpoints
@router.post("/services/register", response_model=ServiceInstanceResponse)
async def register_service(
    registration: ServiceRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register a service instance."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    service_instance = await service_manager.register_current_service(
        service_name=registration.service_name,
        host=registration.host,
        port=registration.port,
        version=registration.version,
        health_check_url=registration.health_check_url,
        metadata=registration.metadata,
        tags=registration.tags
    )
    
    return ServiceInstanceResponse(**service_instance.to_dict())


@router.delete("/services/{service_id}")
async def deregister_service(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deregister a service instance."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    success = await service_manager.registry.deregister_service(service_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return {"message": f"Service {service_id} deregistered successfully"}


@router.get("/services", response_model=List[ServiceInstanceResponse])
async def list_services(
    service_name: Optional[str] = Query(None),
    status_filter: Optional[ServiceStatus] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List all registered services."""
    if hasattr(service_manager.registry, 'get_all_services'):
        services = await service_manager.registry.get_all_services()
    else:
        # For registries that don't support listing all services
        services = []
    
    # Apply filters
    filtered_services = services
    
    if service_name:
        filtered_services = [s for s in filtered_services if s.service_name == service_name]
    
    if status_filter:
        filtered_services = [s for s in filtered_services if s.status == status_filter]
    
    return [ServiceInstanceResponse(**service.to_dict()) for service in filtered_services]


@router.get("/services/{service_name}/instances", response_model=List[ServiceInstanceResponse])
async def discover_service_instances(
    service_name: str,
    current_user: User = Depends(get_current_user)
):
    """Discover instances of a specific service."""
    instances = await service_manager.registry.discover_services(service_name)
    return [ServiceInstanceResponse(**instance.to_dict()) for instance in instances]


@router.get("/services/{service_id}", response_model=ServiceInstanceResponse)
async def get_service(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific service instance."""
    service = await service_manager.registry.get_service(service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return ServiceInstanceResponse(**service.to_dict())


@router.put("/services/{service_id}/health")
async def update_service_health(
    service_id: str,
    health_status: ServiceStatus,
    current_user: User = Depends(get_current_user)
):
    """Update service health status."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    success = await service_manager.registry.update_health(service_id, health_status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return {"message": f"Service {service_id} health updated to {health_status}"}


@router.post("/services/{service_id}/heartbeat")
async def send_heartbeat(
    service_id: str,
    current_user: User = Depends(get_current_user)
):
    """Send heartbeat for service."""
    success = await service_manager.registry.heartbeat(service_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return {"message": f"Heartbeat sent for service {service_id}"}


# Service Health endpoints
@router.get("/services/{service_name}/health", response_model=ServiceHealthResponse)
async def get_service_health(
    service_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get health status of all instances of a service."""
    health_info = await service_manager.get_service_health(service_name)
    
    return ServiceHealthResponse(
        service_name=health_info["service_name"],
        total_instances=health_info["total_instances"],
        healthy_instances=health_info["healthy_instances"],
        instances=[
            ServiceInstanceResponse(**instance) 
            for instance in health_info["instances"]
        ]
    )


# Circuit Breaker endpoints
@router.get("/circuit-breakers", response_model=List[CircuitBreakerResponse])
async def get_circuit_breaker_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all circuit breakers."""
    circuit_breakers = await service_manager.discovery.get_circuit_breaker_status()
    
    return [
        CircuitBreakerResponse(
            name=cb["name"],
            state=CircuitBreakerState(cb["state"]),
            failure_count=cb["failure_count"],
            success_count=cb["success_count"],
            last_failure_time=datetime.fromisoformat(cb["last_failure_time"]) if cb["last_failure_time"] else None,
            last_request_time=datetime.fromisoformat(cb["last_request_time"]) if cb["last_request_time"] else None
        )
        for cb in circuit_breakers
    ]


# System Status endpoints
@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """Get overall system status."""
    status_info = await service_manager.get_system_status()
    
    return SystemStatusResponse(
        timestamp=datetime.fromisoformat(status_info["timestamp"]),
        current_service=ServiceInstanceResponse(**status_info["current_service"]) if status_info["current_service"] else None,
        registered_services=[
            ServiceInstanceResponse(**service) 
            for service in status_info["registered_services"]
        ],
        circuit_breakers=[
            CircuitBreakerResponse(
                name=cb["name"],
                state=CircuitBreakerState(cb["state"]),
                failure_count=cb["failure_count"],
                success_count=cb["success_count"],
                last_failure_time=datetime.fromisoformat(cb["last_failure_time"]) if cb["last_failure_time"] else None,
                last_request_time=datetime.fromisoformat(cb["last_request_time"]) if cb["last_request_time"] else None
            )
            for cb in status_info["circuit_breakers"]
        ],
        health_checker_running=status_info["health_checker_running"]
    )


# API Gateway Management endpoints
@router.post("/gateway/routes")
async def add_gateway_route(
    route_config: RouteConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a route to the API Gateway."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    config = RouteConfig(
        path_pattern=route_config.path_pattern,
        service_name=route_config.service_name,
        target_path=route_config.target_path,
        methods=route_config.methods,
        headers=route_config.headers,
        rate_limit=route_config.rate_limit,
        auth_required=route_config.auth_required,
        timeout=route_config.timeout,
        retries=route_config.retries,
        circuit_breaker=route_config.circuit_breaker,
        cache_ttl=route_config.cache_ttl,
        weight=route_config.weight
    )
    
    api_gateway.add_route(config)
    
    return {
        "message": f"Route {route_config.path_pattern} -> {route_config.service_name} added successfully"
    }


@router.post("/gateway/rate-limits")
async def add_rate_limit_rule(
    rate_limit: RateLimitRuleRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a rate limiting rule to the API Gateway."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    rule = RateLimitRule(
        key_pattern=rate_limit.key_pattern,
        requests_per_minute=rate_limit.requests_per_minute,
        requests_per_hour=rate_limit.requests_per_hour,
        requests_per_day=rate_limit.requests_per_day,
        strategy=rate_limit.strategy,
        burst_size=rate_limit.burst_size
    )
    
    api_gateway.add_rate_limit(rate_limit.pattern, rule)
    
    return {
        "message": f"Rate limit rule for {rate_limit.pattern} added successfully"
    }


@router.get("/gateway/stats", response_model=GatewayStatsResponse)
async def get_gateway_stats(
    current_user: User = Depends(get_current_user)
):
    """Get API Gateway statistics."""
    stats = await api_gateway.get_gateway_stats()
    
    return GatewayStatsResponse(
        **stats,
        status="healthy"
    )


@router.get("/gateway/routes")
async def list_gateway_routes(
    current_user: User = Depends(get_current_user)
):
    """List all configured gateway routes."""
    routes = []
    for pattern, config in api_gateway.routes.items():
        routes.append({
            "path_pattern": pattern,
            "service_name": config.service_name,
            "target_path": config.target_path,
            "methods": config.methods,
            "rate_limit": config.rate_limit,
            "auth_required": config.auth_required,
            "timeout": config.timeout,
            "circuit_breaker": config.circuit_breaker
        })
    
    return {
        "routes": routes,
        "total_count": len(routes)
    }


@router.get("/gateway/rate-limits")
async def list_rate_limits(
    current_user: User = Depends(get_current_user)
):
    """List all configured rate limiting rules."""
    rate_limits = []
    for pattern, rule in api_gateway.rate_limits.items():
        rate_limits.append({
            "pattern": pattern,
            "key_pattern": rule.key_pattern,
            "requests_per_minute": rule.requests_per_minute,
            "requests_per_hour": rule.requests_per_hour,
            "requests_per_day": rule.requests_per_day,
            "strategy": rule.strategy,
            "burst_size": rule.burst_size
        })
    
    return {
        "rate_limits": rate_limits,
        "total_count": len(rate_limits)
    }


# Service Communication endpoints
@router.post("/services/{service_name}/call")
async def call_service(
    service_name: str,
    endpoint: str = Query(...),
    method: str = Query("GET"),
    current_user: User = Depends(get_current_user)
):
    """Call another service through service discovery."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        result = await service_manager.call_service(
            service_name=service_name,
            endpoint=endpoint,
            method=method
        )
        
        return {
            "service_name": service_name,
            "endpoint": endpoint,
            "method": method,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service call failed: {str(e)}"
        )


# Health check endpoints
@router.get("/health/microservices")
async def microservices_health():
    """Check microservices infrastructure health."""
    health_info = await check_microservices_health()
    
    if not health_info.get("health_checker_running", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health checker not running"
        )
    
    return health_info


@router.get("/health/gateway")
async def gateway_health():
    """Check API Gateway health."""
    health_info = await check_api_gateway_health()
    
    return health_info


@router.get("/health/overall")
async def overall_health():
    """Check overall microservices system health."""
    microservices_health_info = await check_microservices_health()
    gateway_health_info = await check_api_gateway_health()
    
    overall_status = "healthy"
    if (not microservices_health_info.get("health_checker_running", False) or
        gateway_health_info.get("status") != "healthy"):
        overall_status = "degraded"
    
    return {
        "overall_status": overall_status,
        "microservices": microservices_health_info,
        "gateway": gateway_health_info,
        "timestamp": datetime.utcnow().isoformat()
    }