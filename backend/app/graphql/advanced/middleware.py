"""Advanced GraphQL middleware for security, performance, and monitoring."""

import asyncio
import hashlib
import json
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.types import Info

from app.core.monitoring import monitor_performance


class MiddlewareLevel(str, Enum):
    """Middleware execution levels."""
    REQUEST = "request"
    QUERY = "query"
    FIELD = "field"
    RESPONSE = "response"


@dataclass
class MiddlewareConfig:
    """Middleware configuration."""
    enabled: bool = True
    level: MiddlewareLevel = MiddlewareLevel.QUERY
    priority: int = 100  # Lower number = higher priority
    skip_introspection: bool = True


@dataclass
class SecurityViolation:
    """Security violation record."""
    id: str
    violation_type: str
    severity: int  # 1-10
    query: str
    variables: Dict[str, Any]
    ip_address: str
    user_id: Optional[str]
    timestamp: datetime
    blocked: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """Performance tracking metric."""
    query_hash: str
    execution_time_ms: float
    complexity_score: int
    depth: int
    field_count: int
    resolver_count: int
    cache_hits: int
    cache_misses: int
    timestamp: datetime


class PerformanceMiddleware(SchemaExtension):
    """Performance monitoring and optimization middleware."""
    
    def __init__(self):
        """Initialize performance middleware."""
        self.config = MiddlewareConfig(level=MiddlewareLevel.QUERY)
        self.metrics: deque = deque(maxlen=10000)
        self.slow_queries: Dict[str, PerformanceMetric] = {}
        self.query_cache: Dict[str, Any] = {}
        self.resolver_timings: Dict[str, List[float]] = defaultdict(list)
    
    @monitor_performance("graphql.middleware.performance")
    async def on_operation(self):
        """Track operation performance."""
        start_time = time.time()
        
        # Extract query information
        query = str(self.execution_context.query)
        variables = self.execution_context.variable_values or {}
        
        # Calculate query hash for caching
        query_hash = hashlib.md5(
            (query + json.dumps(variables, sort_keys=True)).encode()
        ).hexdigest()
        
        # Track complexity and depth
        complexity_score = self._calculate_complexity(query)
        depth = self._calculate_depth(query)
        field_count = self._count_fields(query)
        
        try:
            # Execute the operation
            yield
        finally:
            # Record performance metrics
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            metric = PerformanceMetric(
                query_hash=query_hash,
                execution_time_ms=execution_time,
                complexity_score=complexity_score,
                depth=depth,
                field_count=field_count,
                resolver_count=0,  # Would be populated by resolver tracking
                cache_hits=0,
                cache_misses=0,
                timestamp=datetime.utcnow()
            )
            
            self.metrics.append(metric)
            
            # Track slow queries (>1000ms)
            if execution_time > 1000:
                self.slow_queries[query_hash] = metric
    
    def _calculate_complexity(self, query: str) -> int:
        """Calculate query complexity score."""
        # Simplified complexity calculation
        complexity = 0
        complexity += query.count('{') * 10  # Nesting
        complexity += query.count('(') * 5   # Arguments
        complexity += len(query.split()) * 1  # Fields
        return complexity
    
    def _calculate_depth(self, query: str) -> int:
        """Calculate query depth."""
        max_depth = 0
        current_depth = 0
        
        for char in query:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1
        
        return max_depth
    
    def _count_fields(self, query: str) -> int:
        """Count number of fields in query."""
        # Simplified field counting
        return len([line for line in query.split('\n') 
                   if line.strip() and not line.strip().startswith('#')])
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance monitoring summary."""
        if not self.metrics:
            return {"message": "No metrics available"}
        
        recent_metrics = list(self.metrics)[-100:]  # Last 100 queries
        
        avg_execution_time = sum(m.execution_time_ms for m in recent_metrics) / len(recent_metrics)
        avg_complexity = sum(m.complexity_score for m in recent_metrics) / len(recent_metrics)
        
        return {
            "total_queries": len(self.metrics),
            "avg_execution_time_ms": avg_execution_time,
            "avg_complexity_score": avg_complexity,
            "slow_queries_count": len(self.slow_queries),
            "cache_size": len(self.query_cache),
            "last_updated": datetime.utcnow().isoformat()
        }


class SecurityMiddleware(SchemaExtension):
    """Security monitoring and protection middleware."""
    
    def __init__(self):
        """Initialize security middleware."""
        self.config = MiddlewareConfig(level=MiddlewareLevel.REQUEST)
        self.violations: deque = deque(maxlen=5000)
        self.blocked_queries: Set[str] = set()
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self.max_requests_per_minute = 100
        self.max_query_depth = 15
        self.max_query_complexity = 1000
        self.suspicious_patterns = [
            r'__schema',
            r'__type',
            r'introspection',
            r'union.*{.*}',
            r'fragment.*on.*{.*}'
        ]
    
    @monitor_performance("graphql.middleware.security")
    async def on_operation(self):
        """Perform security checks on operation."""
        query = str(self.execution_context.query)
        variables = self.execution_context.variable_values or {}
        
        # Get client information
        request = getattr(self.execution_context.context, 'request', None)
        ip_address = "127.0.0.1"
        user_id = None
        
        if request:
            ip_address = request.client.host if request.client else "127.0.0.1"
            user = getattr(self.execution_context.context, 'current_user', None)
            user_id = str(user.id) if user else None
        
        # Check rate limiting
        if not self._check_rate_limit(ip_address):
            violation = self._create_violation(
                "rate_limit_exceeded",
                8,
                query,
                variables,
                ip_address,
                user_id,
                {"requests_per_minute": self.max_requests_per_minute}
            )
            self.violations.append(violation)
            raise PermissionError("Rate limit exceeded")
        
        # Check query depth
        depth = self._calculate_depth(query)
        if depth > self.max_query_depth:
            violation = self._create_violation(
                "query_depth_exceeded",
                7,
                query,
                variables,
                ip_address,
                user_id,
                {"depth": depth, "max_depth": self.max_query_depth}
            )
            self.violations.append(violation)
            raise ValueError(f"Query depth {depth} exceeds maximum {self.max_query_depth}")
        
        # Check query complexity
        complexity = self._calculate_complexity(query)
        if complexity > self.max_query_complexity:
            violation = self._create_violation(
                "query_complexity_exceeded",
                6,
                query,
                variables,
                ip_address,
                user_id,
                {"complexity": complexity, "max_complexity": self.max_query_complexity}
            )
            self.violations.append(violation)
            raise ValueError(f"Query complexity {complexity} exceeds maximum {self.max_query_complexity}")
        
        # Check for suspicious patterns
        self._check_suspicious_patterns(query, variables, ip_address, user_id)
        
        # Execute the operation
        yield
    
    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP address exceeds rate limit."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.rate_limits[ip_address] = [
            req_time for req_time in self.rate_limits[ip_address]
            if req_time > minute_ago
        ]
        
        # Add current request
        self.rate_limits[ip_address].append(now)
        
        # Check limit
        return len(self.rate_limits[ip_address]) <= self.max_requests_per_minute
    
    def _calculate_depth(self, query: str) -> int:
        """Calculate query depth."""
        max_depth = 0
        current_depth = 0
        
        for char in query:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1
        
        return max_depth
    
    def _calculate_complexity(self, query: str) -> int:
        """Calculate query complexity."""
        complexity = 0
        complexity += query.count('{') * 15
        complexity += query.count('(') * 10
        complexity += query.count('[') * 20  # Arrays are expensive
        complexity += len(query.split()) * 2
        return complexity
    
    def _check_suspicious_patterns(
        self,
        query: str,
        variables: Dict[str, Any],
        ip_address: str,
        user_id: Optional[str]
    ) -> None:
        """Check for suspicious query patterns."""
        import re
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                violation = self._create_violation(
                    "suspicious_pattern",
                    5,
                    query,
                    variables,
                    ip_address,
                    user_id,
                    {"pattern": pattern}
                )
                self.violations.append(violation)
                # Don't block, just log
                break
    
    def _create_violation(
        self,
        violation_type: str,
        severity: int,
        query: str,
        variables: Dict[str, Any],
        ip_address: str,
        user_id: Optional[str],
        details: Dict[str, Any]
    ) -> SecurityViolation:
        """Create security violation record."""
        return SecurityViolation(
            id=str(uuid.uuid4()),
            violation_type=violation_type,
            severity=severity,
            query=query,
            variables=variables,
            ip_address=ip_address,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            blocked=severity >= 7,
            details=details
        )
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security monitoring summary."""
        recent_violations = [
            v for v in self.violations
            if v.timestamp > datetime.utcnow() - timedelta(hours=24)
        ]
        
        violation_types = defaultdict(int)
        for violation in recent_violations:
            violation_types[violation.violation_type] += 1
        
        return {
            "total_violations": len(self.violations),
            "recent_violations_24h": len(recent_violations),
            "blocked_queries": len(self.blocked_queries),
            "violation_types": dict(violation_types),
            "rate_limited_ips": len(self.rate_limits),
            "max_query_depth": self.max_query_depth,
            "max_query_complexity": self.max_query_complexity,
            "last_updated": datetime.utcnow().isoformat()
        }


class CachingMiddleware(SchemaExtension):
    """Intelligent query result caching middleware."""
    
    def __init__(self):
        """Initialize caching middleware."""
        self.config = MiddlewareConfig(level=MiddlewareLevel.QUERY)
        self.cache: Dict[str, Any] = {}
        self.cache_metadata: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = defaultdict(int)
        self.default_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
    
    @monitor_performance("graphql.middleware.caching")
    async def on_operation(self):
        """Handle query caching."""
        query = str(self.execution_context.query)
        variables = self.execution_context.variable_values or {}
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, variables)
        
        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            self.cache_stats["hits"] += 1
            # Return cached result (would need to modify execution context)
            return
        
        self.cache_stats["misses"] += 1
        
        # Execute operation
        result = yield
        
        # Cache result if cacheable
        if self._is_cacheable(query):
            self._cache_result(cache_key, result)
        
        return result
    
    def _generate_cache_key(self, query: str, variables: Dict[str, Any]) -> str:
        """Generate cache key for query and variables."""
        normalized_query = self._normalize_query(query)
        cache_data = {
            "query": normalized_query,
            "variables": variables
        }
        return hashlib.md5(
            json.dumps(cache_data, sort_keys=True).encode()
        ).hexdigest()
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent caching."""
        # Remove comments and extra whitespace
        lines = []
        for line in query.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
        return ' '.join(lines)
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if valid."""
        if cache_key not in self.cache:
            return None
        
        metadata = self.cache_metadata.get(cache_key, {})
        ttl = metadata.get("ttl", self.default_ttl)
        cached_at = metadata.get("cached_at")
        
        if cached_at and (datetime.utcnow() - cached_at).total_seconds() > ttl:
            # Cache expired
            del self.cache[cache_key]
            del self.cache_metadata[cache_key]
            return None
        
        return self.cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache query result."""
        # Implement cache size limit
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest cache entry
            oldest_key = min(
                self.cache_metadata.keys(),
                key=lambda k: self.cache_metadata[k].get("cached_at", datetime.min)
            )
            del self.cache[oldest_key]
            del self.cache_metadata[oldest_key]
        
        self.cache[cache_key] = result
        self.cache_metadata[cache_key] = {
            "cached_at": datetime.utcnow(),
            "ttl": self.default_ttl,
            "size": len(str(result))
        }
    
    def _is_cacheable(self, query: str) -> bool:
        """Determine if query result should be cached."""
        # Don't cache mutations or subscriptions
        query_lower = query.lower()
        if 'mutation' in query_lower or 'subscription' in query_lower:
            return False
        
        # Don't cache introspection queries
        if '__schema' in query or '__type' in query:
            return False
        
        return True
    
    def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching pattern."""
        if pattern is None:
            # Clear all cache
            count = len(self.cache)
            self.cache.clear()
            self.cache_metadata.clear()
            return count
        
        # Pattern-based invalidation (simplified)
        keys_to_remove = []
        for key in self.cache:
            if pattern in str(self.cache[key]):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            del self.cache_metadata[key]
        
        return len(keys_to_remove)
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get caching statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        cache_size_bytes = sum(
            metadata.get("size", 0)
            for metadata in self.cache_metadata.values()
        )
        
        return {
            "cache_entries": len(self.cache),
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "hit_rate_percentage": hit_rate,
            "cache_size_bytes": cache_size_bytes,
            "max_cache_size": self.max_cache_size,
            "default_ttl_seconds": self.default_ttl,
            "last_updated": datetime.utcnow().isoformat()
        }


class RateLimitMiddleware(SchemaExtension):
    """Advanced rate limiting middleware."""
    
    def __init__(self):
        """Initialize rate limiting middleware."""
        self.config = MiddlewareConfig(level=MiddlewareLevel.REQUEST)
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.complexity_limits: Dict[str, int] = {
            "anonymous": 100,
            "user": 500,
            "premium": 1000,
            "admin": 5000
        }
        self.rate_limits: Dict[str, int] = {
            "anonymous": 10,
            "user": 100,
            "premium": 500,
            "admin": 1000
        }
    
    @monitor_performance("graphql.middleware.rate_limit")
    async def on_operation(self):
        """Apply rate limiting."""
        # Get user tier
        user_tier = self._get_user_tier()
        
        # Check rate limit
        if not self._check_rate_limit(user_tier):
            raise PermissionError(f"Rate limit exceeded for {user_tier} tier")
        
        # Check complexity limit
        query = str(self.execution_context.query)
        complexity = self._calculate_complexity(query)
        
        if complexity > self.complexity_limits[user_tier]:
            raise ValueError(
                f"Query complexity {complexity} exceeds limit {self.complexity_limits[user_tier]} for {user_tier} tier"
            )
        
        # Record request
        self._record_request(user_tier)
        
        yield
    
    def _get_user_tier(self) -> str:
        """Determine user tier for rate limiting."""
        user = getattr(self.execution_context.context, 'current_user', None)
        
        if not user:
            return "anonymous"
        elif user.is_superuser:
            return "admin"
        elif hasattr(user, 'subscription_tier'):
            return user.subscription_tier
        else:
            return "user"
    
    def _check_rate_limit(self, user_tier: str) -> bool:
        """Check if user tier exceeds rate limit."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        requests = self.request_counts[user_tier]
        while requests and requests[0] < minute_ago:
            requests.popleft()
        
        # Check limit
        return len(requests) < self.rate_limits[user_tier]
    
    def _record_request(self, user_tier: str) -> None:
        """Record a request for rate limiting."""
        self.request_counts[user_tier].append(datetime.utcnow())
    
    def _calculate_complexity(self, query: str) -> int:
        """Calculate query complexity for rate limiting."""
        complexity = 0
        complexity += query.count('{') * 10
        complexity += query.count('(') * 5
        complexity += query.count('[') * 15
        return complexity
    
    def get_rate_limit_summary(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        current_usage = {}
        for tier, requests in self.request_counts.items():
            minute_ago = datetime.utcnow() - timedelta(minutes=1)
            recent_requests = sum(1 for req_time in requests if req_time > minute_ago)
            current_usage[tier] = {
                "requests_last_minute": recent_requests,
                "limit": self.rate_limits[tier],
                "utilization_percentage": (recent_requests / self.rate_limits[tier] * 100) if self.rate_limits[tier] > 0 else 0
            }
        
        return {
            "rate_limits": self.rate_limits,
            "complexity_limits": self.complexity_limits,
            "current_usage": current_usage,
            "last_updated": datetime.utcnow().isoformat()
        }


class AuditMiddleware(SchemaExtension):
    """Comprehensive audit logging middleware."""
    
    def __init__(self):
        """Initialize audit middleware."""
        self.config = MiddlewareConfig(level=MiddlewareLevel.QUERY)
        self.audit_logs: deque = deque(maxlen=10000)
        self.sensitive_fields = {
            "password", "token", "secret", "key", "credential"
        }
    
    @monitor_performance("graphql.middleware.audit")
    async def on_operation(self):
        """Log operation for audit purposes."""
        start_time = datetime.utcnow()
        
        # Extract operation details
        query = str(self.execution_context.query)
        variables = self.execution_context.variable_values or {}
        operation_name = getattr(self.execution_context, 'operation_name', None)
        
        # Get user context
        user = getattr(self.execution_context.context, 'current_user', None)
        request = getattr(self.execution_context.context, 'request', None)
        
        # Sanitize sensitive data
        sanitized_variables = self._sanitize_variables(variables)
        
        audit_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": start_time,
            "operation_name": operation_name,
            "query": query,
            "variables": sanitized_variables,
            "user_id": str(user.id) if user else None,
            "user_email": user.email if user else None,
            "ip_address": request.client.host if request and request.client else "127.0.0.1",
            "user_agent": dict(request.headers).get("user-agent") if request else None,
            "status": "started"
        }
        
        try:
            # Execute operation
            result = yield
            
            # Log successful completion
            end_time = datetime.utcnow()
            audit_entry.update({
                "status": "completed",
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
                "completed_at": end_time
            })
            
            return result
        
        except Exception as e:
            # Log error
            end_time = datetime.utcnow()
            audit_entry.update({
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
                "completed_at": end_time
            })
            raise
        
        finally:
            # Store audit log
            self.audit_logs.append(audit_entry)
    
    def _sanitize_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from variables."""
        sanitized = {}
        
        for key, value in variables.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_variables(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_variables(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get audit logging summary."""
        recent_logs = [
            log for log in self.audit_logs
            if log["timestamp"] > datetime.utcnow() - timedelta(hours=24)
        ]
        
        status_counts = defaultdict(int)
        error_types = defaultdict(int)
        
        for log in recent_logs:
            status_counts[log["status"]] += 1
            if log["status"] == "failed":
                error_types[log.get("error_type", "Unknown")] += 1
        
        return {
            "total_operations": len(self.audit_logs),
            "operations_24h": len(recent_logs),
            "status_distribution": dict(status_counts),
            "error_types": dict(error_types),
            "retention_limit": self.audit_logs.maxlen,
            "last_updated": datetime.utcnow().isoformat()
        }


# Global middleware instances
performance_middleware = PerformanceMiddleware()
security_middleware = SecurityMiddleware()
caching_middleware = CachingMiddleware()
rate_limit_middleware = RateLimitMiddleware()
audit_middleware = AuditMiddleware()


# Health check for middleware system
async def check_graphql_middleware_health() -> Dict[str, Any]:
    """Check GraphQL middleware system health."""
    return {
        "status": "healthy",
        "performance": performance_middleware.get_performance_summary(),
        "security": security_middleware.get_security_summary(),
        "caching": caching_middleware.get_cache_summary(),
        "rate_limiting": rate_limit_middleware.get_rate_limit_summary(),
        "audit": audit_middleware.get_audit_summary()
    }