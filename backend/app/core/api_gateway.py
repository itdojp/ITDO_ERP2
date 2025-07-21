"""API Gateway implementation with Kong/Envoy-like features."""

import time
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, Response, HTTPException, status
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
import httpx

from app.core.monitoring import monitor_performance
from app.core.microservices import service_manager


class RoutingStrategy(str, Enum):
    """API Gateway routing strategies."""
    PATH_BASED = "path_based"
    HOST_BASED = "host_based"
    HEADER_BASED = "header_based"
    WEIGHTED = "weighted"


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RouteConfig:
    """Route configuration for API Gateway."""
    path_pattern: str
    service_name: str
    target_path: Optional[str] = None
    methods: List[str] = None
    headers: Dict[str, str] = None
    rate_limit: Optional[int] = None
    auth_required: bool = True
    timeout: int = 30
    retries: int = 3
    circuit_breaker: bool = True
    cache_ttl: Optional[int] = None
    weight: int = 100  # For weighted routing
    
    def __post_init__(self):
        if self.methods is None:
            self.methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if self.headers is None:
            self.headers = {}


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    key_pattern: str  # e.g., "user:{user_id}", "ip:{ip}", "global"
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_size: Optional[int] = None
    
    def get_cache_key(self, identifier: str) -> str:
        """Get cache key for rate limiting."""
        return f"rate_limit:{self.key_pattern.format(**{self.key_pattern.split(':')[1][1:-1]: identifier})}"


class RateLimiter:
    """Rate limiter implementation for API Gateway."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.request_counts: Dict[str, Dict[str, Any]] = {}
    
    async def is_allowed(
        self,
        rule: RateLimitRule,
        identifier: str,
        request_count: int = 1
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed based on rate limit."""
        cache_key = rule.get_cache_key(identifier)
        current_time = datetime.utcnow()
        
        if cache_key not in self.request_counts:
            self.request_counts[cache_key] = {
                "requests": [],
                "last_reset": current_time
            }
        
        data = self.request_counts[cache_key]
        
        if rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window_check(rule, data, current_time, request_count)
        elif rule.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window_check(rule, data, current_time, request_count)
        elif rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket_check(rule, data, current_time, request_count)
        
        return False, {"error": "Unknown rate limit strategy"}
    
    async def _sliding_window_check(
        self,
        rule: RateLimitRule,
        data: Dict[str, Any],
        current_time: datetime,
        request_count: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Sliding window rate limit check."""
        requests = data["requests"]
        
        # Remove old requests
        minute_ago = current_time - timedelta(minutes=1)
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(days=1)
        
        # Filter requests within time windows
        recent_requests = [r for r in requests if r > minute_ago]
        hourly_requests = [r for r in requests if r > hour_ago]
        daily_requests = [r for r in requests if r > day_ago]
        
        # Check limits
        if len(recent_requests) >= rule.requests_per_minute:
            return False, {
                "error": "Rate limit exceeded (per minute)",
                "retry_after": 60 - (current_time - recent_requests[0]).seconds
            }
        
        if len(hourly_requests) >= rule.requests_per_hour:
            return False, {
                "error": "Rate limit exceeded (per hour)",
                "retry_after": 3600 - (current_time - hourly_requests[0]).seconds
            }
        
        if len(daily_requests) >= rule.requests_per_day:
            return False, {
                "error": "Rate limit exceeded (per day)",
                "retry_after": 86400 - (current_time - daily_requests[0]).seconds
            }
        
        # Add current request
        requests.append(current_time)
        data["requests"] = daily_requests + [current_time]  # Keep only relevant requests
        
        return True, {
            "remaining_minute": rule.requests_per_minute - len(recent_requests) - 1,
            "remaining_hour": rule.requests_per_hour - len(hourly_requests) - 1,
            "remaining_day": rule.requests_per_day - len(daily_requests) - 1
        }
    
    async def _fixed_window_check(
        self,
        rule: RateLimitRule,
        data: Dict[str, Any],
        current_time: datetime,
        request_count: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Fixed window rate limit check."""
        # Reset counter if window has passed
        if (current_time - data["last_reset"]).total_seconds() >= 60:
            data["requests"] = []
            data["last_reset"] = current_time
        
        current_requests = len(data["requests"])
        
        if current_requests >= rule.requests_per_minute:
            seconds_until_reset = 60 - (current_time - data["last_reset"]).seconds
            return False, {
                "error": "Rate limit exceeded",
                "retry_after": seconds_until_reset
            }
        
        data["requests"].append(current_time)
        
        return True, {
            "remaining": rule.requests_per_minute - current_requests - 1,
            "reset_time": data["last_reset"] + timedelta(minutes=1)
        }
    
    async def _token_bucket_check(
        self,
        rule: RateLimitRule,
        data: Dict[str, Any],
        current_time: datetime,
        request_count: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Token bucket rate limit check."""
        if "tokens" not in data:
            data["tokens"] = rule.burst_size or rule.requests_per_minute
            data["last_refill"] = current_time
        
        # Refill tokens
        time_passed = (current_time - data["last_refill"]).total_seconds()
        tokens_to_add = int(time_passed * (rule.requests_per_minute / 60))
        
        data["tokens"] = min(
            rule.burst_size or rule.requests_per_minute,
            data["tokens"] + tokens_to_add
        )
        data["last_refill"] = current_time
        
        # Check if enough tokens
        if data["tokens"] < request_count:
            return False, {
                "error": "Rate limit exceeded (token bucket)",
                "tokens_remaining": data["tokens"]
            }
        
        # Consume tokens
        data["tokens"] -= request_count
        
        return True, {
            "tokens_remaining": data["tokens"]
        }


class RequestTransformer:
    """Transform requests before forwarding to services."""
    
    @staticmethod
    async def add_headers(request: Request, headers: Dict[str, str]) -> Dict[str, str]:
        """Add headers to request."""
        request_headers = dict(request.headers)
        request_headers.update(headers)
        return request_headers
    
    @staticmethod
    async def remove_headers(request: Request, headers: List[str]) -> Dict[str, str]:
        """Remove headers from request."""
        request_headers = dict(request.headers)
        for header in headers:
            request_headers.pop(header.lower(), None)
        return request_headers
    
    @staticmethod
    async def transform_path(request_path: str, route_config: RouteConfig) -> str:
        """Transform request path."""
        if route_config.target_path:
            # Replace the matched pattern with target path
            return route_config.target_path
        return request_path
    
    @staticmethod
    async def add_correlation_id(request: Request) -> str:
        """Add correlation ID to request."""
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = hashlib.md5(
                f"{time.time()}:{request.client.host if request.client else 'unknown'}".encode()
            ).hexdigest()
        return correlation_id


class ResponseTransformer:
    """Transform responses before returning to client."""
    
    @staticmethod
    async def add_headers(response: Response, headers: Dict[str, str]) -> None:
        """Add headers to response."""
        for key, value in headers.items():
            response.headers[key] = value
    
    @staticmethod
    async def remove_headers(response: Response, headers: List[str]) -> None:
        """Remove headers from response."""
        for header in headers:
            response.headers.pop(header, None)
    
    @staticmethod
    async def add_security_headers(response: Response) -> None:
        """Add security headers to response."""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'"
        }
        
        for key, value in security_headers.items():
            response.headers[key] = value


class APIGateway:
    """API Gateway with routing, rate limiting, and transformations."""
    
    def __init__(self):
        """Initialize API Gateway."""
        self.routes: Dict[str, RouteConfig] = {}
        self.rate_limits: Dict[str, RateLimitRule] = {}
        self.rate_limiter = RateLimiter()
        self.request_transformer = RequestTransformer()
        self.response_transformer = ResponseTransformer()
        self.http_client = httpx.AsyncClient()
        
        # Middleware functions
        self.pre_request_hooks: List[Callable] = []
        self.post_response_hooks: List[Callable] = []
    
    def add_route(self, route_config: RouteConfig) -> None:
        """Add a route to the gateway."""
        self.routes[route_config.path_pattern] = route_config
    
    def add_rate_limit(self, pattern: str, rule: RateLimitRule) -> None:
        """Add rate limiting rule."""
        self.rate_limits[pattern] = rule
    
    def add_pre_request_hook(self, hook: Callable) -> None:
        """Add pre-request middleware hook."""
        self.pre_request_hooks.append(hook)
    
    def add_post_response_hook(self, hook: Callable) -> None:
        """Add post-response middleware hook."""
        self.post_response_hooks.append(hook)
    
    @monitor_performance("gateway.process_request")
    async def process_request(self, request: Request) -> Response:
        """Process incoming request through the gateway."""
        start_time = time.time()
        
        try:
            # Find matching route
            route_config = await self._find_matching_route(request)
            if not route_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Route not found"
                )
            
            # Check rate limits
            await self._check_rate_limits(request, route_config)
            
            # Execute pre-request hooks
            for hook in self.pre_request_hooks:
                await hook(request, route_config)
            
            # Transform request
            transformed_request = await self._transform_request(request, route_config)
            
            # Forward to service
            response = await self._forward_to_service(transformed_request, route_config)
            
            # Transform response
            await self._transform_response(response, route_config)
            
            # Execute post-response hooks
            for hook in self.post_response_hooks:
                await hook(request, response, route_config)
            
            # Add gateway headers
            response.headers["X-Gateway-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
            response.headers["X-Gateway-Version"] = "1.0.0"
            
            return response
        
        except HTTPException:
            raise
        except Exception as e:
            # Log error and return 500
            print(f"Gateway error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal gateway error", "message": str(e)}
            )
    
    async def _find_matching_route(self, request: Request) -> Optional[RouteConfig]:
        """Find matching route configuration."""
        request_path = request.url.path
        request_method = request.method
        
        for pattern, config in self.routes.items():
            if self._path_matches(request_path, pattern) and request_method in config.methods:
                return config
        
        return None
    
    def _path_matches(self, request_path: str, pattern: str) -> bool:
        """Check if request path matches route pattern."""
        # Simple pattern matching - in production, use more sophisticated routing
        if pattern.endswith("/*"):
            return request_path.startswith(pattern[:-2])
        elif "{" in pattern and "}" in pattern:
            # Path parameter matching
            pattern_parts = pattern.split("/")
            request_parts = request_path.split("/")
            
            if len(pattern_parts) != len(request_parts):
                return False
            
            for pattern_part, request_part in zip(pattern_parts, request_parts):
                if pattern_part.startswith("{") and pattern_part.endswith("}"):
                    continue  # Path parameter matches anything
                elif pattern_part != request_part:
                    return False
            
            return True
        else:
            return request_path == pattern
    
    async def _check_rate_limits(self, request: Request, route_config: RouteConfig) -> None:
        """Check rate limits for request."""
        # Check route-specific rate limit
        if route_config.rate_limit:
            user_id = getattr(request.state, "user_id", None)
            client_ip = request.client.host if request.client else "unknown"
            
            identifier = user_id if user_id else client_ip
            
            # Create temporary rate limit rule
            rule = RateLimitRule(
                key_pattern="route:{identifier}",
                requests_per_minute=route_config.rate_limit,
                requests_per_hour=route_config.rate_limit * 60,
                requests_per_day=route_config.rate_limit * 60 * 24
            )
            
            allowed, info = await self.rate_limiter.is_allowed(rule, identifier)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=info.get("error", "Rate limit exceeded"),
                    headers={"Retry-After": str(info.get("retry_after", 60))}
                )
        
        # Check global rate limits
        for pattern, rule in self.rate_limits.items():
            if self._path_matches(request.url.path, pattern):
                user_id = getattr(request.state, "user_id", None)
                client_ip = request.client.host if request.client else "unknown"
                
                identifier = user_id if user_id else client_ip
                
                allowed, info = await self.rate_limiter.is_allowed(rule, identifier)
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=info.get("error", "Rate limit exceeded"),
                        headers={"Retry-After": str(info.get("retry_after", 60))}
                    )
    
    async def _transform_request(self, request: Request, route_config: RouteConfig) -> Dict[str, Any]:
        """Transform request before forwarding."""
        # Add correlation ID
        correlation_id = await self.request_transformer.add_correlation_id(request)
        
        # Transform headers
        headers = await self.request_transformer.add_headers(request, {
            "X-Correlation-ID": correlation_id,
            "X-Gateway-Source": "api-gateway",
            **route_config.headers
        })
        
        # Transform path
        target_path = await self.request_transformer.transform_path(
            request.url.path, route_config
        )
        
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        return {
            "method": request.method,
            "path": target_path,
            "headers": headers,
            "params": dict(request.query_params),
            "body": body,
            "correlation_id": correlation_id
        }
    
    async def _forward_to_service(
        self,
        transformed_request: Dict[str, Any],
        route_config: RouteConfig
    ) -> Response:
        """Forward request to target service."""
        try:
            # Use service discovery to call the service
            endpoint = transformed_request["path"]
            
            response_data = await service_manager.call_service(
                service_name=route_config.service_name,
                endpoint=endpoint,
                method=transformed_request["method"],
                data=transformed_request.get("body"),
                headers=transformed_request["headers"],
                timeout=route_config.timeout
            )
            
            return JSONResponse(content=response_data)
        
        except HTTPException as e:
            # Forward HTTP exceptions from services
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )
        except Exception as e:
            # Handle service communication errors
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service unavailable",
                    "service": route_config.service_name,
                    "message": str(e)
                }
            )
    
    async def _transform_response(self, response: Response, route_config: RouteConfig) -> None:
        """Transform response before returning."""
        # Add security headers
        await self.response_transformer.add_security_headers(response)
        
        # Add gateway information
        await self.response_transformer.add_headers(response, {
            "X-Service-Name": route_config.service_name,
            "X-Gateway-Route": route_config.path_pattern
        })
    
    async def get_gateway_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "routes_configured": len(self.routes),
            "rate_limits_configured": len(self.rate_limits),
            "active_rate_limits": len(self.rate_limiter.request_counts),
            "pre_request_hooks": len(self.pre_request_hooks),
            "post_response_hooks": len(self.post_response_hooks),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()


# Default gateway configuration
def setup_default_routes(gateway: APIGateway) -> None:
    """Setup default routes for the gateway."""
    
    # User service routes
    gateway.add_route(RouteConfig(
        path_pattern="/api/v1/users/*",
        service_name="user-service",
        target_path="/users",
        rate_limit=100,
        timeout=10
    ))
    
    # Auth service routes
    gateway.add_route(RouteConfig(
        path_pattern="/api/v1/auth/*",
        service_name="auth-service",
        target_path="/auth",
        auth_required=False,  # Auth endpoints don't require auth
        rate_limit=50,
        timeout=5
    ))
    
    # Organization service routes
    gateway.add_route(RouteConfig(
        path_pattern="/api/v1/organizations/*",
        service_name="organization-service",
        target_path="/organizations",
        rate_limit=200,
        timeout=15
    ))
    
    # Notification service routes
    gateway.add_route(RouteConfig(
        path_pattern="/api/v1/notifications/*",
        service_name="notification-service",
        target_path="/notifications",
        rate_limit=300,
        timeout=30
    ))
    
    # Audit service routes
    gateway.add_route(RouteConfig(
        path_pattern="/api/v1/comprehensive-audit/*",
        service_name="audit-service",
        target_path="/audit",
        rate_limit=500,
        timeout=20
    ))


def setup_default_rate_limits(gateway: APIGateway) -> None:
    """Setup default rate limiting rules."""
    
    # Global rate limits
    gateway.add_rate_limit("/api/v1/*", RateLimitRule(
        key_pattern="global:{ip}",
        requests_per_minute=1000,
        requests_per_hour=10000,
        requests_per_day=100000,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ))
    
    # Auth endpoints - stricter limits
    gateway.add_rate_limit("/api/v1/auth/login", RateLimitRule(
        key_pattern="auth_login:{ip}",
        requests_per_minute=5,
        requests_per_hour=20,
        requests_per_day=100,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ))
    
    # User registration - very strict
    gateway.add_rate_limit("/api/v1/auth/register", RateLimitRule(
        key_pattern="auth_register:{ip}",
        requests_per_minute=2,
        requests_per_hour=5,
        requests_per_day=10,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ))


# Global gateway instance
api_gateway = APIGateway()

# Setup default configuration
setup_default_routes(api_gateway)
setup_default_rate_limits(api_gateway)


# Health check for API Gateway
async def check_api_gateway_health() -> Dict[str, Any]:
    """Check API Gateway health."""
    stats = await api_gateway.get_gateway_stats()
    stats["status"] = "healthy"
    return stats