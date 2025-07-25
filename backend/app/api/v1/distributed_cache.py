"""Distributed Cache Management API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.distributed_cache import (
    distributed_cache,
    CacheBackend,
    CacheStrategy,
    check_distributed_cache_health
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class CacheSetRequest(BaseModel):
    """Cache set request."""
    key: str = Field(..., max_length=500)
    value: Any
    ttl_seconds: int = Field(3600, ge=1, le=86400)  # Max 24 hours
    tags: Set[str] = Field(default_factory=set)
    dependencies: Set[str] = Field(default_factory=set)


class CacheGetResponse(BaseModel):
    """Cache get response."""
    key: str
    value: Any
    found: bool
    source: str  # local, distributed, etc.


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    hit_rate_percentage: float
    memory_utilization_percentage: float
    avg_response_time_ms: float
    total_requests: int
    cache_hits: int
    cache_misses: int
    evictions: int
    total_nodes: int
    active_nodes: int


class CacheHealthResponse(BaseModel):
    """Cache health response."""
    status: str
    statistics: CacheStatsResponse
    nodes: Dict[str, int]
    configuration: Dict[str, str]
    local_cache: Dict[str, Any]


class CacheInvalidationRequest(BaseModel):
    """Cache invalidation request."""
    invalidation_type: str = Field(..., regex="^(key|tags|pattern|dependencies)$")
    target: Optional[str] = None
    tags: Optional[Set[str]] = None


class CacheWarmingRequest(BaseModel):
    """Cache warming request."""
    patterns: List[str] = Field(..., max_items=20)


# Cache operation endpoints
@router.get("/cache/{key}")
async def get_cache_value(
    key: str,
    current_user: User = Depends(get_current_user)
):
    """Get value from distributed cache."""
    try:
        value = await distributed_cache.get(key)
        
        return CacheGetResponse(
            key=key,
            value=value,
            found=value is not None,
            source="distributed"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache value: {str(e)}"
        )


@router.post("/cache")
async def set_cache_value(
    cache_request: CacheSetRequest,
    current_user: User = Depends(get_current_user)
):
    """Set value in distributed cache."""
    try:
        success = await distributed_cache.set(
            key=cache_request.key,
            value=cache_request.value,
            ttl_seconds=cache_request.ttl_seconds,
            tags=cache_request.tags,
            dependencies=cache_request.dependencies
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set cache value"
            )
        
        return {
            "message": "Cache value set successfully",
            "key": cache_request.key,
            "ttl_seconds": cache_request.ttl_seconds,
            "set_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set cache value: {str(e)}"
        )


@router.delete("/cache/{key}")
async def delete_cache_value(
    key: str,
    current_user: User = Depends(get_current_user)
):
    """Delete value from distributed cache."""
    try:
        success = await distributed_cache.delete(key)
        
        return {
            "message": "Cache value deleted" if success else "Cache key not found",
            "key": key,
            "deleted": success,
            "deleted_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cache value: {str(e)}"
        )


@router.post("/cache/invalidate")
async def invalidate_cache(
    invalidation_request: CacheInvalidationRequest,
    current_user: User = Depends(get_current_user)
):
    """Invalidate cache entries based on criteria."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        invalidated_count = 0
        
        if invalidation_request.invalidation_type == "key":
            if not invalidation_request.target:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target key required for key invalidation"
                )
            success = await distributed_cache.delete(invalidation_request.target)
            invalidated_count = 1 if success else 0
        
        elif invalidation_request.invalidation_type == "tags":
            if not invalidation_request.tags:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tags required for tag-based invalidation"
                )
            invalidated_count = await distributed_cache.invalidate_by_tags(
                invalidation_request.tags
            )
        
        elif invalidation_request.invalidation_type == "pattern":
            if not invalidation_request.target:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pattern required for pattern-based invalidation"
                )
            invalidated_count = await distributed_cache.invalidate_by_pattern(
                invalidation_request.target
            )
        
        elif invalidation_request.invalidation_type == "dependencies":
            if not invalidation_request.target:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Dependency key required for dependency invalidation"
                )
            invalidated_count = await distributed_cache.invalidate_dependencies(
                invalidation_request.target
            )
        
        return {
            "message": f"Cache invalidation completed",
            "invalidation_type": invalidation_request.invalidation_type,
            "invalidated_count": invalidated_count,
            "invalidated_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache invalidation failed: {str(e)}"
        )


@router.post("/cache/warm")
async def warm_cache(
    warming_request: CacheWarmingRequest,
    current_user: User = Depends(get_current_user)
):
    """Warm cache with data matching patterns."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        warmed_count = await distributed_cache.warm_cache(warming_request.patterns)
        
        return {
            "message": "Cache warming completed",
            "patterns": warming_request.patterns,
            "warmed_count": warmed_count,
            "warmed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache warming failed: {str(e)}"
        )


@router.post("/cache/preload")
async def preload_critical_cache(
    current_user: User = Depends(get_current_user)
):
    """Preload critical application data into cache."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        preloaded_count = await distributed_cache.preload_critical_data()
        
        return {
            "message": "Critical data preloading completed",
            "preloaded_count": preloaded_count,
            "preloaded_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache preloading failed: {str(e)}"
        )


# Monitoring and management endpoints
@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get cache performance statistics."""
    try:
        health_info = await distributed_cache.health_check()
        stats = health_info["statistics"]
        nodes = health_info["nodes"]
        
        return CacheStatsResponse(
            hit_rate_percentage=stats["hit_rate_percentage"],
            memory_utilization_percentage=stats["memory_utilization_percentage"],
            avg_response_time_ms=stats["avg_response_time_ms"],
            total_requests=stats["total_requests"],
            cache_hits=stats["cache_hits"],
            cache_misses=stats["cache_misses"],
            evictions=stats["evictions"],
            total_nodes=nodes["total"],
            active_nodes=nodes["active"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.get("/cache/performance")
async def get_cache_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get detailed cache performance metrics."""
    try:
        metrics = await distributed_cache.get_performance_metrics()
        
        return {
            "performance_metrics": metrics,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/cache/nodes")
async def get_cache_nodes_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all cache nodes."""
    try:
        metrics = await distributed_cache.get_performance_metrics()
        node_status = metrics["node_status"]
        
        return {
            "nodes": node_status,
            "summary": {
                "total_nodes": len(node_status),
                "active_nodes": len([n for n in node_status.values() if n["active"]]),
                "total_memory_mb": sum(n["memory_limit_mb"] for n in node_status.values()),
                "used_memory_mb": sum(n["memory_used_mb"] for n in node_status.values())
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node status: {str(e)}"
        )


# Configuration endpoints
@router.get("/cache/config")
async def get_cache_configuration(
    current_user: User = Depends(get_current_user)
):
    """Get cache system configuration."""
    try:
        health_info = await distributed_cache.health_check()
        config = health_info["configuration"]
        
        return {
            "configuration": config,
            "capabilities": {
                "backends": [backend.value for backend in CacheBackend],
                "strategies": [strategy.value for strategy in CacheStrategy],
                "replication": True,
                "consistent_hashing": True,
                "dependency_tracking": True,
                "tag_based_invalidation": True,
                "cache_warming": True,
                "performance_monitoring": True
            },
            "limits": {
                "max_key_length": 500,
                "max_ttl_seconds": 86400,
                "max_warming_patterns": 20,
                "local_cache_limit_mb": distributed_cache.local_cache_size_mb
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache configuration: {str(e)}"
        )


# Health check endpoint
@router.get("/cache/health", response_model=CacheHealthResponse)
async def cache_health_check():
    """Check distributed cache system health."""
    try:
        health_info = await check_distributed_cache_health()
        stats = health_info["statistics"]
        
        return CacheHealthResponse(
            status=health_info["status"],
            statistics=CacheStatsResponse(
                hit_rate_percentage=stats["hit_rate_percentage"],
                memory_utilization_percentage=stats["memory_utilization_percentage"],
                avg_response_time_ms=stats["avg_response_time_ms"],
                total_requests=stats["total_requests"],
                cache_hits=stats["cache_hits"],
                cache_misses=stats["cache_misses"],
                evictions=stats["evictions"],
                total_nodes=health_info["nodes"]["total"],
                active_nodes=health_info["nodes"]["active"]
            ),
            nodes=health_info["nodes"],
            configuration=health_info["configuration"],
            local_cache=health_info["local_cache"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cache health check failed: {str(e)}"
        )


# Administrative endpoints
@router.post("/cache/clear")
async def clear_all_cache(
    confirm: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Clear all cache entries (DANGEROUS)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm cache clearing with confirm=true parameter"
        )
    
    try:
        # Clear local cache
        initial_count = len(distributed_cache.local_cache)
        distributed_cache.local_cache.clear()
        
        # Reset stats
        distributed_cache.stats.evictions += initial_count
        
        return {
            "message": "All cache entries cleared",
            "cleared_count": initial_count,
            "cleared_at": datetime.utcnow().isoformat(),
            "warning": "This action cleared all cached data"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.post("/cache/optimize")
async def optimize_cache(
    current_user: User = Depends(get_current_user)
):
    """Optimize cache performance by evicting stale entries."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        # Perform cache optimization
        evicted_count = await distributed_cache._evict_local_entries()
        
        return {
            "message": "Cache optimization completed",
            "evicted_count": evicted_count,
            "optimized_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache optimization failed: {str(e)}"
        )