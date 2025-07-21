"""Multi-tenant performance optimization engine."""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from weakref import WeakSet

from app.core.monitoring import monitor_performance


class OptimizationStrategy(str, Enum):
    """Performance optimization strategies."""
    RESOURCE_POOLING = "resource_pooling"
    QUERY_OPTIMIZATION = "query_optimization"
    CACHE_PARTITIONING = "cache_partitioning"
    CONNECTION_POOLING = "connection_pooling"
    LOAD_BALANCING = "load_balancing"
    ADAPTIVE_SCALING = "adaptive_scaling"


class ResourceType(str, Enum):
    """Resource types for optimization."""
    DATABASE_CONNECTION = "database_connection"
    MEMORY_POOL = "memory_pool"
    CPU_THREAD = "cpu_thread"
    CACHE_SEGMENT = "cache_segment"
    FILE_HANDLE = "file_handle"
    NETWORK_CONNECTION = "network_connection"


@dataclass
class TenantMetrics:
    """Performance metrics for a tenant."""
    tenant_id: str
    request_count: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    resource_usage: Dict[ResourceType, float] = field(default_factory=dict)
    peak_concurrent_users: int = 0
    data_volume: int = 0
    query_complexity_score: float = 0.0
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def update_metrics(self, response_time: float, error: bool = False) -> None:
        """Update tenant metrics with new request data."""
        self.request_count += 1
        
        # Update average response time
        if self.request_count == 1:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (
                (self.avg_response_time * (self.request_count - 1) + response_time) / 
                self.request_count
            )
        
        # Update error rate
        if error:
            error_count = int(self.error_rate * (self.request_count - 1)) + 1
            self.error_rate = error_count / self.request_count
        else:
            error_count = int(self.error_rate * (self.request_count - 1))
            self.error_rate = error_count / self.request_count
        
        self.last_activity = datetime.utcnow()


@dataclass
class ResourcePool:
    """Resource pool for multi-tenant optimization."""
    resource_type: ResourceType
    total_capacity: int
    allocated_resources: Dict[str, int] = field(default_factory=dict)  # tenant_id -> count
    reserved_capacity: int = 0
    utilization_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def available_capacity(self) -> int:
        """Get available resource capacity."""
        used = sum(self.allocated_resources.values()) + self.reserved_capacity
        return max(0, self.total_capacity - used)
    
    @property
    def utilization_rate(self) -> float:
        """Get current utilization rate."""
        used = sum(self.allocated_resources.values())
        return (used / self.total_capacity) * 100 if self.total_capacity > 0 else 0.0
    
    def allocate(self, tenant_id: str, amount: int) -> bool:
        """Allocate resources to tenant."""
        if amount <= self.available_capacity:
            self.allocated_resources[tenant_id] = self.allocated_resources.get(tenant_id, 0) + amount
            self.utilization_history.append((datetime.utcnow(), self.utilization_rate))
            return True
        return False
    
    def deallocate(self, tenant_id: str, amount: int) -> int:
        """Deallocate resources from tenant."""
        current = self.allocated_resources.get(tenant_id, 0)
        actual_amount = min(amount, current)
        
        if actual_amount > 0:
            self.allocated_resources[tenant_id] = current - actual_amount
            if self.allocated_resources[tenant_id] == 0:
                del self.allocated_resources[tenant_id]
            
            self.utilization_history.append((datetime.utcnow(), self.utilization_rate))
        
        return actual_amount


class QueryOptimizer:
    """Multi-tenant query optimization engine."""
    
    def __init__(self):
        """Initialize query optimizer."""
        self.tenant_query_patterns: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.optimization_cache: Dict[str, str] = {}
        self.index_recommendations: Dict[str, Set[str]] = defaultdict(set)
    
    @monitor_performance("query_optimizer.analyze")
    async def analyze_query(self, tenant_id: str, query: str) -> Dict[str, Any]:
        """Analyze query for optimization opportunities."""
        query_hash = str(hash(query))
        
        # Track query patterns
        self.tenant_query_patterns[tenant_id][query_hash] += 1
        
        # Basic query analysis
        analysis = {
            "query_hash": query_hash,
            "complexity_score": self._calculate_complexity(query),
            "optimization_suggestions": [],
            "estimated_cost": self._estimate_cost(query),
            "tenant_specific_optimizations": []
        }
        
        # Check for common patterns
        if "SELECT *" in query.upper():
            analysis["optimization_suggestions"].append("Avoid SELECT * - specify required columns")
        
        if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
            analysis["optimization_suggestions"].append("Consider adding LIMIT to ORDER BY queries")
        
        if query.upper().count("JOIN") > 3:
            analysis["optimization_suggestions"].append("Complex joins detected - consider query restructuring")
        
        # Tenant-specific optimizations
        tenant_patterns = self.tenant_query_patterns[tenant_id]
        if len(tenant_patterns) > 10:
            most_common = max(tenant_patterns.items(), key=lambda x: x[1])
            if most_common[1] > 100:  # Frequently executed query
                analysis["tenant_specific_optimizations"].append("Frequent query - consider materialized view")
        
        return analysis
    
    def _calculate_complexity(self, query: str) -> float:
        """Calculate query complexity score."""
        query_upper = query.upper()
        
        # Base complexity factors
        complexity = 1.0
        complexity += query_upper.count("JOIN") * 2
        complexity += query_upper.count("SUBQUERY") * 3
        complexity += query_upper.count("ORDER BY") * 1.5
        complexity += query_upper.count("GROUP BY") * 1.5
        complexity += query_upper.count("HAVING") * 2
        complexity += query_upper.count("UNION") * 2
        
        return min(complexity, 10.0)  # Cap at 10
    
    def _estimate_cost(self, query: str) -> int:
        """Estimate query execution cost."""
        # Simplified cost estimation
        base_cost = 100
        query_upper = query.upper()
        
        # Add cost for complex operations
        cost = base_cost
        cost += query_upper.count("JOIN") * 500
        cost += query_upper.count("SUBQUERY") * 1000
        cost += query_upper.count("ORDER BY") * 200
        cost += query_upper.count("GROUP BY") * 300
        
        return cost


class ConnectionPoolManager:
    """Multi-tenant database connection pool manager."""
    
    def __init__(self, max_connections: int = 100):
        """Initialize connection pool manager."""
        self.max_connections = max_connections
        self.tenant_pools: Dict[str, ResourcePool] = {}
        self.global_pool = ResourcePool(ResourceType.DATABASE_CONNECTION, max_connections)
        self.connection_weights: Dict[str, float] = defaultdict(lambda: 1.0)
    
    async def allocate_connections(self, tenant_id: str, requested: int) -> int:
        """Allocate database connections for tenant."""
        # Calculate tenant priority based on metrics
        weight = self.connection_weights[tenant_id]
        
        # Adjust allocation based on tenant weight
        adjusted_request = max(1, int(requested * weight))
        
        # Try to allocate from global pool
        allocated = 0
        if self.global_pool.allocate(tenant_id, adjusted_request):
            allocated = adjusted_request
        else:
            # Allocate what's available
            available = self.global_pool.available_capacity
            if available > 0 and self.global_pool.allocate(tenant_id, available):
                allocated = available
        
        return allocated
    
    async def deallocate_connections(self, tenant_id: str, count: int) -> int:
        """Deallocate database connections for tenant."""
        return self.global_pool.deallocate(tenant_id, count)
    
    def update_tenant_weight(self, tenant_id: str, metrics: TenantMetrics) -> None:
        """Update tenant connection weight based on performance metrics."""
        # Higher priority for tenants with better performance
        base_weight = 1.0
        
        # Adjust based on error rate (lower error rate = higher weight)
        if metrics.error_rate < 0.01:
            base_weight += 0.5
        elif metrics.error_rate > 0.05:
            base_weight -= 0.3
        
        # Adjust based on response time (faster = higher weight)
        if metrics.avg_response_time < 100:
            base_weight += 0.3
        elif metrics.avg_response_time > 1000:
            base_weight -= 0.2
        
        # Adjust based on request volume (more active = slightly higher weight)
        if metrics.request_count > 1000:
            base_weight += 0.2
        
        self.connection_weights[tenant_id] = max(0.1, min(2.0, base_weight))


class TenantLoadBalancer:
    """Load balancer for multi-tenant requests."""
    
    def __init__(self):
        """Initialize load balancer."""
        self.tenant_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.processing_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.circuit_breakers: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    async def route_request(self, tenant_id: str, request_data: Dict[str, Any]) -> str:
        """Route request to optimal processing queue."""
        # Check circuit breaker
        if self._is_circuit_open(tenant_id):
            return "circuit_breaker_open"
        
        # Add to tenant queue
        self.tenant_queues[tenant_id].append({
            "request_data": request_data,
            "timestamp": datetime.utcnow(),
            "priority": self._calculate_priority(tenant_id, request_data)
        })
        
        return "queued"
    
    def _calculate_priority(self, tenant_id: str, request_data: Dict[str, Any]) -> int:
        """Calculate request priority."""
        base_priority = 5
        
        # Adjust based on tenant performance history
        avg_processing_time = self._get_avg_processing_time(tenant_id)
        if avg_processing_time < 100:
            base_priority += 2
        elif avg_processing_time > 1000:
            base_priority -= 2
        
        # Adjust based on request type
        if request_data.get("type") == "read":
            base_priority += 1
        elif request_data.get("type") == "write":
            base_priority -= 1
        
        return max(1, min(10, base_priority))
    
    def _is_circuit_open(self, tenant_id: str) -> bool:
        """Check if circuit breaker is open for tenant."""
        cb = self.circuit_breakers[tenant_id]
        if not cb:
            return False
        
        failure_rate = cb.get("failure_rate", 0.0)
        last_failure = cb.get("last_failure")
        
        # Open circuit if failure rate > 50% and recent failures
        if failure_rate > 0.5 and last_failure:
            time_since_failure = (datetime.utcnow() - last_failure).total_seconds()
            return time_since_failure < 300  # 5 minute cooldown
        
        return False
    
    def _get_avg_processing_time(self, tenant_id: str) -> float:
        """Get average processing time for tenant."""
        times = self.processing_times[tenant_id]
        return sum(times) / len(times) if times else 500.0


class MultiTenantPerformanceManager:
    """Main multi-tenant performance optimization manager."""
    
    def __init__(self):
        """Initialize performance manager."""
        self.tenant_metrics: Dict[str, TenantMetrics] = {}
        self.resource_pools: Dict[ResourceType, ResourcePool] = {}
        self.query_optimizer = QueryOptimizer()
        self.connection_manager = ConnectionPoolManager()
        self.load_balancer = TenantLoadBalancer()
        self.optimization_recommendations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        self._initialize_resource_pools()
    
    def _initialize_resource_pools(self) -> None:
        """Initialize resource pools."""
        pool_configs = {
            ResourceType.DATABASE_CONNECTION: 100,
            ResourceType.MEMORY_POOL: 1000,  # MB
            ResourceType.CPU_THREAD: 50,
            ResourceType.CACHE_SEGMENT: 200,
            ResourceType.FILE_HANDLE: 500,
            ResourceType.NETWORK_CONNECTION: 150
        }
        
        for resource_type, capacity in pool_configs.items():
            self.resource_pools[resource_type] = ResourcePool(resource_type, capacity)
    
    @monitor_performance("performance_manager.track_request")
    async def track_request(
        self,
        tenant_id: str,
        request_type: str,
        response_time: float,
        error: bool = False,
        resource_usage: Optional[Dict[ResourceType, float]] = None
    ) -> None:
        """Track request performance for tenant."""
        if tenant_id not in self.tenant_metrics:
            self.tenant_metrics[tenant_id] = TenantMetrics(tenant_id)
        
        metrics = self.tenant_metrics[tenant_id]
        metrics.update_metrics(response_time, error)
        
        if resource_usage:
            for resource_type, usage in resource_usage.items():
                metrics.resource_usage[resource_type] = usage
        
        # Update connection weights
        self.connection_manager.update_tenant_weight(tenant_id, metrics)
        
        # Generate recommendations if needed
        await self._generate_recommendations(tenant_id)
    
    @monitor_performance("performance_manager.optimize_query")
    async def optimize_query(self, tenant_id: str, query: str) -> Dict[str, Any]:
        """Optimize query for tenant."""
        analysis = await self.query_optimizer.analyze_query(tenant_id, query)
        
        # Update tenant query complexity metrics
        if tenant_id in self.tenant_metrics:
            metrics = self.tenant_metrics[tenant_id]
            complexity = analysis["complexity_score"]
            
            if metrics.query_complexity_score == 0:
                metrics.query_complexity_score = complexity
            else:
                # Running average
                metrics.query_complexity_score = (
                    (metrics.query_complexity_score * 0.9) + (complexity * 0.1)
                )
        
        return analysis
    
    async def allocate_resources(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        amount: int
    ) -> bool:
        """Allocate resources to tenant."""
        if resource_type in self.resource_pools:
            pool = self.resource_pools[resource_type]
            return pool.allocate(tenant_id, amount)
        return False
    
    async def deallocate_resources(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        amount: int
    ) -> int:
        """Deallocate resources from tenant."""
        if resource_type in self.resource_pools:
            pool = self.resource_pools[resource_type]
            return pool.deallocate(tenant_id, amount)
        return 0
    
    async def get_tenant_metrics(self, tenant_id: str) -> Optional[TenantMetrics]:
        """Get metrics for tenant."""
        return self.tenant_metrics.get(tenant_id)
    
    async def get_optimization_recommendations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get optimization recommendations for tenant."""
        return self.optimization_recommendations.get(tenant_id, [])
    
    async def _generate_recommendations(self, tenant_id: str) -> None:
        """Generate optimization recommendations for tenant."""
        metrics = self.tenant_metrics[tenant_id]
        recommendations = []
        
        # High response time recommendation
        if metrics.avg_response_time > 1000:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "message": "High average response time detected",
                "suggestion": "Consider query optimization or resource scaling",
                "metric": "avg_response_time",
                "value": metrics.avg_response_time
            })
        
        # High error rate recommendation
        if metrics.error_rate > 0.05:
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "message": "High error rate detected",
                "suggestion": "Review application logic and error handling",
                "metric": "error_rate",
                "value": metrics.error_rate
            })
        
        # Resource utilization recommendations
        for resource_type, pool in self.resource_pools.items():
            tenant_usage = pool.allocated_resources.get(tenant_id, 0)
            if tenant_usage > 0:
                utilization = (tenant_usage / pool.total_capacity) * 100
                
                if utilization > 80:
                    recommendations.append({
                        "type": "resource",
                        "priority": "medium",
                        "message": f"High {resource_type.value} utilization",
                        "suggestion": "Consider resource optimization or scaling",
                        "metric": f"{resource_type.value}_utilization",
                        "value": utilization
                    })
        
        # Query complexity recommendation
        if metrics.query_complexity_score > 7:
            recommendations.append({
                "type": "query",
                "priority": "medium", 
                "message": "High query complexity detected",
                "suggestion": "Review and optimize complex queries",
                "metric": "query_complexity_score",
                "value": metrics.query_complexity_score
            })
        
        # Update recommendations
        self.optimization_recommendations[tenant_id] = recommendations[-10:]  # Keep last 10
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get system performance overview."""
        total_tenants = len(self.tenant_metrics)
        active_tenants = sum(
            1 for metrics in self.tenant_metrics.values()
            if (datetime.utcnow() - metrics.last_activity).total_seconds() < 3600
        )
        
        # Resource utilization summary
        resource_summary = {}
        for resource_type, pool in self.resource_pools.items():
            resource_summary[resource_type.value] = {
                "total_capacity": pool.total_capacity,
                "allocated": sum(pool.allocated_resources.values()),
                "utilization_rate": pool.utilization_rate,
                "active_tenants": len(pool.allocated_resources)
            }
        
        # Performance metrics summary
        if self.tenant_metrics:
            avg_response_time = sum(m.avg_response_time for m in self.tenant_metrics.values()) / total_tenants
            avg_error_rate = sum(m.error_rate for m in self.tenant_metrics.values()) / total_tenants
            total_requests = sum(m.request_count for m in self.tenant_metrics.values())
        else:
            avg_response_time = 0
            avg_error_rate = 0
            total_requests = 0
        
        return {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "resource_utilization": resource_summary,
            "performance_metrics": {
                "avg_response_time": avg_response_time,
                "avg_error_rate": avg_error_rate,
                "total_requests": total_requests
            },
            "optimization_strategies_active": len(OptimizationStrategy),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global performance manager instance
performance_manager = MultiTenantPerformanceManager()


# Performance monitoring decorator for tenant operations
def tenant_performance_monitor(tenant_id_param: str = "tenant_id"):
    """Decorator to monitor tenant performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            tenant_id = kwargs.get(tenant_id_param) or (args[0] if args else "unknown")
            start_time = time.time()
            error = False
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = True
                raise
            finally:
                response_time = (time.time() - start_time) * 1000
                await performance_manager.track_request(
                    tenant_id=str(tenant_id),
                    request_type=func.__name__,
                    response_time=response_time,
                    error=error
                )
        
        def sync_wrapper(*args, **kwargs):
            tenant_id = kwargs.get(tenant_id_param) or (args[0] if args else "unknown")
            start_time = time.time()
            error = False
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = True
                raise
            finally:
                response_time = (time.time() - start_time) * 1000
                # For sync functions, we can't easily call async track_request
                # In production, you'd want to use a background task or queue
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Health check for multi-tenant performance
async def check_multi_tenant_performance_health() -> Dict[str, Any]:
    """Check multi-tenant performance system health."""
    overview = await performance_manager.get_system_overview()
    
    # Determine health status
    health_status = "healthy"
    
    # Check resource utilization
    for resource_info in overview["resource_utilization"].values():
        if resource_info["utilization_rate"] > 90:
            health_status = "degraded"
            break
    
    # Check performance metrics
    perf_metrics = overview["performance_metrics"]
    if perf_metrics["avg_response_time"] > 2000 or perf_metrics["avg_error_rate"] > 0.1:
        health_status = "degraded"
    
    return {
        "status": health_status,
        "system_overview": overview,
        "query_optimizer_patterns": len(performance_manager.query_optimizer.tenant_query_patterns),
        "connection_pools": len(performance_manager.connection_manager.tenant_pools),
        "load_balancer_queues": len(performance_manager.load_balancer.tenant_queues)
    }