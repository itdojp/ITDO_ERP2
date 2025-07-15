# ITDO ERP Phase 4/5 Advanced Foundation Implementation Specifications

## 📋 Executive Summary

This document provides comprehensive implementation specifications for ITDO ERP Phase 4/5, focusing on **Performance Excellence**, **Enterprise Security**, and **API Standardization**. Based on advanced foundation research, these specifications will transform the platform into an enterprise-grade solution.

## 🎯 Implementation Overview

| Phase | Focus Area | Timeline | Priority | Impact |
|-------|------------|----------|----------|--------|
| **Phase 4** | Performance & Security Foundation | 2-3 months | High | 🔥 Critical |
| **Phase 5** | API Excellence & Advanced Features | 1-2 months | Medium | ⚡ Enhancement |

---

## 🚀 Phase 4: Performance & Security Foundation

### 4.1 Performance Optimization Architecture

#### 4.1.1 Asynchronous FastAPI Implementation

**Target**: 50%+ response time improvement

```python
# Implementation Structure
backend/
├── app/
│   ├── core/
│   │   ├── async_database.py      # AsyncSession implementation
│   │   ├── cache_manager.py       # Redis caching layer
│   │   └── performance_monitor.py # Real-time performance tracking
│   ├── api/
│   │   └── v1/
│   │       ├── async_users.py     # Async user endpoints
│   │       ├── async_tasks.py     # Async task management
│   │       └── async_auth.py      # Async authentication
│   └── services/
│       ├── async_user_service.py  # Async business logic
│       └── cache_service.py       # Centralized caching
```

**Implementation Timeline**: Week 1-4

**Key Components**:

1. **AsyncSession Integration**
   ```python
   # app/core/async_database.py
   from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
   
   class AsyncDatabaseManager:
       def __init__(self):
           self.async_engine = create_async_engine(
               DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
               pool_size=20,
               max_overflow=30,
               pool_pre_ping=True,
               pool_recycle=3600,
               echo=False
           )
       
       async def get_async_session(self) -> AsyncSession:
           async with AsyncSession(self.async_engine) as session:
               yield session
   ```

2. **Redis Caching Layer**
   ```python
   # app/core/cache_manager.py
   import redis.asyncio as redis
   from typing import Any, Optional
   import json
   import pickle
   
   class CacheManager:
       def __init__(self, redis_url: str):
           self.redis = redis.from_url(redis_url)
       
       async def get_cached_response(self, key: str) -> Optional[Any]:
           cached = await self.redis.get(key)
           return pickle.loads(cached) if cached else None
       
       async def cache_response(self, key: str, data: Any, ttl: int = 300):
           await self.redis.setex(key, ttl, pickle.dumps(data))
       
       async def invalidate_pattern(self, pattern: str):
           keys = await self.redis.keys(pattern)
           if keys:
               await self.redis.delete(*keys)
   ```

3. **Performance Monitoring**
   ```python
   # app/core/performance_monitor.py
   import time
   from contextlib import asynccontextmanager
   
   class PerformanceMonitor:
       @asynccontextmanager
       async def track_execution(self, operation_name: str):
           start_time = time.time()
           try:
               yield
           finally:
               execution_time = time.time() - start_time
               await self.record_metric(operation_name, execution_time)
   ```

#### 4.1.2 Database Query Optimization

**Target**: 60%+ query performance improvement

**Implementation Tasks**:

1. **Index Strategy**
   ```sql
   -- High-priority indexes
   CREATE INDEX CONCURRENTLY idx_task_project_status ON tasks(project_id, status);
   CREATE INDEX CONCURRENTLY idx_task_assignee_status ON tasks(assignee_id, status);
   CREATE INDEX CONCURRENTLY idx_user_organization_active ON user_organizations(user_id, organization_id, is_active);
   CREATE INDEX CONCURRENTLY idx_audit_log_timestamp ON audit_logs(timestamp);
   
   -- Composite indexes for complex queries
   CREATE INDEX CONCURRENTLY idx_task_department_visibility 
   ON tasks(department_id, department_visibility) 
   WHERE department_visibility IS NOT NULL;
   ```

2. **Query Optimization Patterns**
   ```python
   # Optimized user search with pagination
   async def search_users_optimized(
       self, 
       search_params: UserSearchParams,
       page: int = 1,
       page_size: int = 20
   ) -> PaginatedResponse[UserResponse]:
       
       # Use window functions for efficient pagination
       query = select(
           User,
           func.count().over().label('total_count')
       ).options(
           selectinload(User.user_roles).selectinload(UserRole.role),
           selectinload(User.user_roles).selectinload(UserRole.organization)
       )
       
       # Apply filters efficiently
       if search_params.search_term:
           query = query.where(
               or_(
                   User.full_name.ilike(f"%{search_params.search_term}%"),
                   User.email.ilike(f"%{search_params.search_term}%")
               )
           )
       
       # Efficient offset-limit with total count
       query = query.offset((page - 1) * page_size).limit(page_size)
       
       result = await session.execute(query)
       return self._build_paginated_response(result, page, page_size)
   ```

#### 4.1.3 Response Caching Strategy

**Target**: 70%+ cache hit rate

```python
# app/decorators/cache_decorator.py
from functools import wraps
import hashlib

def cache_response(ttl: int = 300, vary_by: list = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs, vary_by)
            
            # Try cache first
            cached_result = await cache_manager.get_cached_response(cache_key)
            if cached_result:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.cache_response(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Usage example
@cache_response(ttl=600, vary_by=['user_id', 'organization_id'])
async def get_user_permissions(user_id: int, organization_id: int):
    # Expensive permission calculation
    pass
```

### 4.2 Enterprise Security Enhancement

#### 4.2.1 OAuth2/OIDC Complete Implementation

**Target**: Enterprise-grade authentication

```python
# app/core/oauth2_enhanced.py
from authlib.integrations.fastapi_oauth2 import OAuth2
from authlib.integrations.httpx_oauth2 import AsyncOAuth2Client

class EnhancedOAuth2Manager:
    def __init__(self):
        self.keycloak = OAuth2(
            client_id=settings.KEYCLOAK_CLIENT_ID,
            client_secret=settings.KEYCLOAK_CLIENT_SECRET,
            server_metadata_url=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/.well-known/openid_configuration"
        )
    
    async def validate_token_with_keycloak(self, token: str) -> dict:
        # Token introspection with Keycloak
        introspection_endpoint = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token/introspect"
        
        async with AsyncOAuth2Client() as client:
            response = await client.introspect_token(
                introspection_endpoint,
                token,
                token_type_hint="access_token"
            )
            return response
    
    async def get_user_info(self, token: str) -> dict:
        # UserInfo endpoint
        userinfo_endpoint = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
        
        async with AsyncOAuth2Client(token=token) as client:
            response = await client.get(userinfo_endpoint)
            return response.json()
```

#### 4.2.2 Advanced RBAC with ABAC Elements

**Target**: Dynamic, context-aware authorization

```python
# app/security/abac_engine.py
from typing import Dict, Any
import ast
import operator

class ABACPolicyEngine:
    """Attribute-Based Access Control Policy Engine"""
    
    OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }
    
    async def evaluate_policy(
        self, 
        policy_expression: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate ABAC policy expression
        
        Example policy: "user.department == resource.department AND time.hour >= 9"
        """
        try:
            tree = ast.parse(policy_expression, mode='eval')
            return self._evaluate_node(tree.body, context)
        except Exception as e:
            # Log policy evaluation error
            logger.error(f"Policy evaluation failed: {e}")
            return False
    
    def _evaluate_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        if isinstance(node, ast.BoolOp):
            values = [self._evaluate_node(child, context) for child in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
        
        elif isinstance(node, ast.Compare):
            left = self._evaluate_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._evaluate_node(comparator, context)
                if not self.OPERATORS[type(op)](left, right):
                    return False
                left = right
            return True
        
        elif isinstance(node, ast.Attribute):
            # Handle nested attributes like "user.department"
            return self._get_nested_value(context, node)
        
        elif isinstance(node, ast.Constant):
            return node.value
        
        return None

# Example ABAC policies
ABAC_POLICIES = {
    "task_view": "user.department == task.department OR user.role.level >= 'manager'",
    "salary_access": "user.role.permissions.salary_view == True AND user.department == 'HR'",
    "time_restricted": "time.hour >= 9 AND time.hour <= 17 AND user.location == 'office'"
}
```

#### 4.2.3 Security Audit Automation

```python
# app/security/audit_automation.py
from datetime import datetime, timedelta
from typing import List, Dict

class SecurityAuditAutomation:
    """Automated security auditing and compliance checking"""
    
    async def daily_security_scan(self) -> Dict[str, Any]:
        """Comprehensive daily security audit"""
        audit_results = {
            "timestamp": datetime.utcnow(),
            "findings": [],
            "recommendations": [],
            "severity_scores": {}
        }
        
        # 1. Access anomaly detection
        anomalies = await self._detect_access_anomalies()
        audit_results["findings"].extend(anomalies)
        
        # 2. Dormant account detection
        dormant_accounts = await self._find_dormant_accounts()
        audit_results["findings"].extend(dormant_accounts)
        
        # 3. Privilege escalation analysis
        escalations = await self._analyze_privilege_escalations()
        audit_results["findings"].extend(escalations)
        
        # 4. Session anomaly detection
        session_anomalies = await self._detect_session_anomalies()
        audit_results["findings"].extend(session_anomalies)
        
        return audit_results
    
    async def _detect_access_anomalies(self) -> List[Dict]:
        """Detect unusual access patterns"""
        # AI-based anomaly detection
        query = """
        SELECT user_id, COUNT(*) as access_count, 
               array_agg(DISTINCT ip_address) as ip_addresses,
               array_agg(DISTINCT user_agent) as user_agents
        FROM audit_logs 
        WHERE timestamp >= NOW() - INTERVAL '24 hours'
        AND action = 'login'
        GROUP BY user_id
        HAVING COUNT(*) > 50 OR 
               array_length(array_agg(DISTINCT ip_address), 1) > 5
        """
        
        # Execute query and analyze results
        results = await self.db.execute(query)
        anomalies = []
        
        for row in results:
            anomalies.append({
                "type": "access_anomaly",
                "user_id": row.user_id,
                "severity": "high" if row.access_count > 100 else "medium",
                "details": {
                    "access_count": row.access_count,
                    "unique_ips": len(row.ip_addresses),
                    "unique_agents": len(row.user_agents)
                }
            })
        
        return anomalies
```

### 4.3 Monitoring & Observability Enhancement

#### 4.3.1 Advanced Performance Monitoring

```python
# app/monitoring/performance_tracker.py
from prometheus_client import Counter, Histogram, Gauge
import time
from contextvars import ContextVar

class AdvancedPerformanceMonitor:
    def __init__(self):
        # Prometheus metrics
        self.request_count = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint']
        )
        
        self.active_connections = Gauge(
            'database_connections_active',
            'Active database connections'
        )
        
        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate percentage'
        )
    
    async def track_api_call(self, request, response, duration: float):
        """Track API call metrics"""
        self.request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        self.request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
    
    async def update_system_metrics(self):
        """Update system-level metrics"""
        # Database connection count
        db_stats = await self.get_database_stats()
        self.active_connections.set(db_stats["active_connections"])
        
        # Cache statistics
        cache_stats = await self.get_cache_stats()
        self.cache_hit_rate.set(cache_stats["hit_rate"] * 100)
```

---

## ⚡ Phase 5: API Excellence & Advanced Features

### 5.1 API Standardization Framework

#### 5.1.1 Unified Response Format

```python
# app/schemas/standard_response.py
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

T = TypeVar('T')

class StandardAPIResponse(BaseModel, Generic[T]):
    """Unified API response format for all endpoints"""
    
    success: bool = True
    data: Optional[T] = None
    meta: 'ResponseMetadata'
    error: Optional['ErrorDetails'] = None
    
    class Config:
        arbitrary_types_allowed = True

class ResponseMetadata(BaseModel):
    """Response metadata for tracking and debugging"""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "v1"
    execution_time_ms: Optional[float] = None
    
class ErrorDetails(BaseModel):
    """Standardized error information"""
    
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    field_errors: Optional[List['FieldError']] = None

class FieldError(BaseModel):
    """Field-specific validation error"""
    
    field: str
    message: str
    invalid_value: Any = None

# Implementation in endpoints
@router.get("/users", response_model=StandardAPIResponse[List[UserResponse]])
async def get_users(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
) -> StandardAPIResponse[List[UserResponse]]:
    
    start_time = time.time()
    
    try:
        users = await user_service.get_users_paginated(page, size)
        
        return StandardAPIResponse(
            success=True,
            data=users.items,
            meta=ResponseMetadata(
                request_id=request.state.request_id,
                execution_time_ms=(time.time() - start_time) * 1000,
                pagination=users.pagination_info
            )
        )
    except Exception as e:
        return StandardAPIResponse(
            success=False,
            data=None,
            meta=ResponseMetadata(
                request_id=request.state.request_id,
                execution_time_ms=(time.time() - start_time) * 1000
            ),
            error=ErrorDetails(
                code="USER_FETCH_ERROR",
                message=str(e),
                trace_id=request.state.trace_id
            )
        )
```

#### 5.1.2 Enhanced Error Handling

```python
# app/core/error_registry.py
from enum import Enum
from typing import Dict, Any

class ErrorCode(Enum):
    # Authentication Errors (AUTH)
    AUTH_INVALID_CREDENTIALS = "AUTH001"
    AUTH_TOKEN_EXPIRED = "AUTH002"
    AUTH_TOKEN_INVALID = "AUTH003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH004"
    
    # Validation Errors (VAL)
    VAL_REQUIRED_FIELD_MISSING = "VAL001"
    VAL_INVALID_FORMAT = "VAL002"
    VAL_VALUE_OUT_OF_RANGE = "VAL003"
    
    # Business Logic Errors (BIZ)
    BIZ_USER_ALREADY_EXISTS = "BIZ001"
    BIZ_RESOURCE_NOT_FOUND = "BIZ002"
    BIZ_OPERATION_NOT_ALLOWED = "BIZ003"
    
    # System Errors (SYS)
    SYS_DATABASE_ERROR = "SYS001"
    SYS_EXTERNAL_SERVICE_ERROR = "SYS002"
    SYS_INTERNAL_ERROR = "SYS003"

class ErrorRegistry:
    """Centralized error message registry with internationalization support"""
    
    MESSAGES = {
        "en": {
            ErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid username or password",
            ErrorCode.AUTH_TOKEN_EXPIRED: "Authentication token has expired",
            ErrorCode.VAL_REQUIRED_FIELD_MISSING: "Required field '{field}' is missing",
            # ... more messages
        },
        "ja": {
            ErrorCode.AUTH_INVALID_CREDENTIALS: "ユーザー名またはパスワードが無効です",
            ErrorCode.AUTH_TOKEN_EXPIRED: "認証トークンの有効期限が切れています",
            ErrorCode.VAL_REQUIRED_FIELD_MISSING: "必須フィールド '{field}' が不足しています",
            # ... more messages
        }
    }
    
    @classmethod
    def get_message(cls, code: ErrorCode, language: str = "en", **kwargs) -> str:
        message_template = cls.MESSAGES.get(language, cls.MESSAGES["en"]).get(code)
        if message_template and kwargs:
            return message_template.format(**kwargs)
        return message_template or "Unknown error"

# Enhanced exception classes
class EnhancedAPIException(HTTPException):
    def __init__(
        self,
        error_code: ErrorCode,
        detail: str = None,
        status_code: int = 400,
        headers: Dict[str, Any] = None,
        field_errors: List[FieldError] = None
    ):
        self.error_code = error_code
        self.field_errors = field_errors or []
        
        super().__init__(
            status_code=status_code,
            detail=detail or ErrorRegistry.get_message(error_code),
            headers=headers
        )
```

### 5.2 Advanced API Features

#### 5.2.1 API Rate Limiting and Throttling

```python
# app/middleware/rate_limiting.py
from fastapi import Request, HTTPException
from typing import Dict, Optional
import time
import asyncio
from collections import defaultdict, deque

class AdvancedRateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.request_counts = defaultdict(deque)
        self.blocked_ips = defaultdict(float)
        
    async def check_rate_limit(
        self,
        request: Request,
        rate_limit_config: 'RateLimitConfig'
    ) -> bool:
        """Check if request should be rate limited"""
        
        identifier = await self._get_rate_limit_identifier(request, rate_limit_config)
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if identifier in self.blocked_ips:
            if current_time < self.blocked_ips[identifier]:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(int(self.blocked_ips[identifier] - current_time))}
                )
            else:
                del self.blocked_ips[identifier]
        
        # Clean old requests
        request_times = self.request_counts[identifier]
        cutoff_time = current_time - rate_limit_config.window_seconds
        
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # Check rate limit
        if len(request_times) >= rate_limit_config.max_requests:
            # Block IP for escalation period
            if rate_limit_config.block_duration:
                self.blocked_ips[identifier] = current_time + rate_limit_config.block_duration
            
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {rate_limit_config.max_requests} requests per {rate_limit_config.window_seconds} seconds.",
                headers={
                    "X-RateLimit-Limit": str(rate_limit_config.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(request_times[0] + rate_limit_config.window_seconds))
                }
            )
        
        # Add current request
        request_times.append(current_time)
        
        return True
    
    async def _get_rate_limit_identifier(
        self,
        request: Request,
        config: 'RateLimitConfig'
    ) -> str:
        """Get identifier for rate limiting (IP, user, API key, etc.)"""
        
        if config.by_user and hasattr(request.state, 'user'):
            return f"user:{request.state.user.id}"
        elif config.by_api_key and 'X-API-Key' in request.headers:
            return f"api_key:{request.headers['X-API-Key']}"
        else:
            # Default to IP address
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                return f"ip:{forwarded_for.split(',')[0].strip()}"
            return f"ip:{request.client.host}"

class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    
    max_requests: int = 100
    window_seconds: int = 60
    by_user: bool = False
    by_api_key: bool = False
    block_duration: Optional[int] = None  # Seconds to block after exceeding limit

# Rate limit decorator
def rate_limit(config: RateLimitConfig):
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            await rate_limiter.check_rate_limit(request, config)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage example
@router.get("/users")
@rate_limit(RateLimitConfig(max_requests=50, window_seconds=60, by_user=True))
async def get_users(request: Request):
    # Implementation
    pass
```

#### 5.2.2 API Versioning Strategy

```python
# app/api/versioning.py
from fastapi import Request, HTTPException
from typing import Callable, Any
import re

class APIVersionManager:
    """Advanced API versioning with deprecation support"""
    
    SUPPORTED_VERSIONS = ["v1", "v2"]
    DEFAULT_VERSION = "v1"
    DEPRECATED_VERSIONS = {"v1": "2024-12-31"}  # Deprecation date
    
    @staticmethod
    def extract_version(request: Request) -> str:
        """Extract API version from request"""
        
        # 1. URL path version (preferred)
        path_match = re.match(r'^/api/(v\d+)/', request.url.path)
        if path_match:
            return path_match.group(1)
        
        # 2. Accept header version
        accept_header = request.headers.get('Accept', '')
        version_match = re.search(r'version=(v\d+)', accept_header)
        if version_match:
            return version_match.group(1)
        
        # 3. Custom header
        custom_version = request.headers.get('X-API-Version')
        if custom_version:
            return custom_version
        
        # 4. Default version
        return APIVersionManager.DEFAULT_VERSION
    
    @staticmethod
    def check_version_support(version: str) -> None:
        """Check if version is supported and handle deprecation"""
        
        if version not in APIVersionManager.SUPPORTED_VERSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {version}. Supported versions: {APIVersionManager.SUPPORTED_VERSIONS}"
            )
        
        # Check deprecation
        if version in APIVersionManager.DEPRECATED_VERSIONS:
            deprecation_date = APIVersionManager.DEPRECATED_VERSIONS[version]
            # Add deprecation warning to response headers
            # This would be handled in middleware

def version_aware_endpoint(versions: list[str]):
    """Decorator to mark endpoints as version-aware"""
    def decorator(func: Callable) -> Callable:
        func._supported_versions = versions
        return func
    return decorator

# Usage example
@version_aware_endpoint(["v1", "v2"])
async def get_user_profile(request: Request, user_id: int):
    version = APIVersionManager.extract_version(request)
    APIVersionManager.check_version_support(version)
    
    if version == "v1":
        return await get_user_profile_v1(user_id)
    elif version == "v2":
        return await get_user_profile_v2(user_id)
```

### 5.3 Developer Experience Enhancement

#### 5.3.1 Comprehensive OpenAPI Documentation

```python
# app/docs/openapi_customization.py
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def create_enhanced_openapi_schema(app: FastAPI) -> dict:
    """Create enhanced OpenAPI schema with enterprise features"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="ITDO ERP API",
        version="2.0.0",
        description="""
        # ITDO ERP - Enterprise Resource Planning API
        
        ## Overview
        This API provides comprehensive enterprise resource planning functionality
        with advanced security, performance optimization, and developer-friendly features.
        
        ## Authentication
        This API uses OAuth2 with Bearer tokens. Include your token in the Authorization header:
        ```
        Authorization: Bearer your_access_token
        ```
        
        ## Rate Limiting
        API requests are rate limited to ensure fair usage:
        - Standard: 1000 requests per hour
        - Premium: 5000 requests per hour
        
        ## Versioning
        API versions are specified in the URL path: `/api/v1/` or `/api/v2/`
        
        ## Response Format
        All responses follow a standard format:
        ```json
        {
            "success": true,
            "data": {...},
            "meta": {
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "uuid",
                "version": "v1"
            }
        }
        ```
        """,
        routes=app.routes,
    )
    
    # Add custom components
    openapi_schema["components"]["schemas"]["StandardResponse"] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "object"},
            "meta": {"$ref": "#/components/schemas/ResponseMetadata"},
            "error": {"$ref": "#/components/schemas/ErrorDetails"}
        }
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth",
                    "tokenUrl": f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
                    "scopes": {
                        "openid": "OpenID Connect",
                        "profile": "User profile",
                        "email": "Email address"
                    }
                }
            }
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom extensions
    openapi_schema["x-logo"] = {
        "url": "https://itdo.jp/logo.png",
        "altText": "ITDO ERP Logo"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

## 📊 Implementation Timeline and Resource Planning

### Phase 4 Implementation Schedule (8-12 weeks)

| Week | Focus Area | Deliverables | Resources |
|------|------------|--------------|-----------|
| 1-2 | Async FastAPI Foundation | AsyncSession, Base Infrastructure | 1 Senior Dev |
| 3-4 | Database Optimization | Indexes, Query Optimization | 1 Senior Dev + 1 DBA |
| 5-6 | Caching Implementation | Redis Layer, Cache Strategies | 1 Senior Dev |
| 7-8 | Security Enhancement | OAuth2, ABAC Implementation | 1 Security Specialist |
| 9-10 | Monitoring Implementation | Performance Tracking, Alerting | 1 DevOps Engineer |
| 11-12 | Testing & Optimization | Load Testing, Performance Tuning | Full Team |

### Phase 5 Implementation Schedule (4-6 weeks)

| Week | Focus Area | Deliverables | Resources |
|------|------------|--------------|-----------|
| 1-2 | API Standardization | Response Format, Error Handling | 1 Senior Dev |
| 3-4 | Advanced Features | Rate Limiting, Versioning | 1 Senior Dev |
| 5-6 | Documentation & DX | OpenAPI, Developer Tools | 1 Technical Writer + 1 Dev |

## 🎯 Success Metrics and KPIs

### Performance Metrics
- **API Response Time**: < 100ms (95th percentile)
- **Database Query Performance**: 60%+ improvement
- **Cache Hit Rate**: > 80%
- **Concurrent Users**: 1000+ simultaneous users

### Security Metrics
- **Security Audit Score**: > 95%
- **Vulnerability Count**: 0 critical, < 5 medium
- **Authentication Success Rate**: > 99.9%
- **Anomaly Detection Accuracy**: > 95%

### Developer Experience Metrics
- **API Documentation Completeness**: 100%
- **API Error Rate**: < 1%
- **Developer Onboarding Time**: < 2 hours
- **API Adoption Rate**: 90%+ endpoint coverage

## 🚀 Post-Implementation Benefits

### Immediate Benefits (Month 1)
- 50%+ faster API response times
- Enterprise-grade security implementation
- Standardized API documentation
- Automated security monitoring

### Medium-term Benefits (Months 2-6)
- Scalability for 10,000+ concurrent users
- Zero-downtime deployments
- Advanced analytics and insights
- Comprehensive audit compliance

### Long-term Benefits (6+ Months)
- Platform for advanced AI/ML features
- Multi-tenant SaaS capabilities
- Global enterprise deployment readiness
- Microservices architecture foundation

---

## 📋 Conclusion

This implementation specification provides a comprehensive roadmap for transforming ITDO ERP into an enterprise-grade platform. The phased approach ensures minimal disruption while delivering maximum value through performance optimization, security enhancement, and API excellence.

**Next Steps:**
1. Review and approve specifications
2. Allocate development resources
3. Begin Phase 4 implementation
4. Establish monitoring and progress tracking
5. Plan Phase 5 execution

The successful implementation of these specifications will position ITDO ERP as a leading enterprise solution with world-class performance, security, and developer experience.