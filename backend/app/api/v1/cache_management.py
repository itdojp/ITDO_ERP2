"""Cache management API endpoints for advanced multi-level caching."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.advanced_cache import (
    advanced_cache,
    CacheLevel,
    CacheStrategy,
    InvalidationStrategy,
    check_advanced_cache_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class CacheEntryRequest(BaseModel):
    """Cache entry creation request."""
    key: str = Field(..., max_length=255)
    value: Any
    ttl: Optional[int] = Field(None, ge=1, le=86400)
    tags: Optional[Set[str]] = set()
    dependencies: Optional[Set[str]] = set()
    levels: Optional[List[CacheLevel]] = None


class CacheKeyRequest(BaseModel):
    """Cache key request."""
    key: str = Field(..., max_length=255)
    levels: Optional[List[CacheLevel]] = None


class CacheInvalidationRequest(BaseModel):
    """Cache invalidation request."""
    strategy: InvalidationStrategy
    target: str = Field(..., max_length=255)  # key, tag, or pattern
    levels: Optional[List[CacheLevel]] = None


class CacheWarmingRequest(BaseModel):
    """Cache warming request."""
    strategy_name: str = Field(..., max_length=100)
    force: bool = False


class CacheAnalyticsResponse(BaseModel):
    """Cache analytics response."""
    level: str
    hits: int
    misses: int
    hit_rate: float
    size_bytes: int
    avg_access_time_ms: float
    evictions: int


class CacheOverallAnalyticsResponse(BaseModel):
    """Overall cache analytics response."""
    total_hits: int
    total_misses: int
    overall_hit_rate: float
    total_size_bytes: int
    enabled_levels: List[str]
    level_analytics: List[CacheAnalyticsResponse]


class CacheHealthResponse(BaseModel):
    """Cache health response."""
    status: str
    warming_strategies: int
    invalidation_tags: int
    dependency_graph_size: int
    analytics: CacheOverallAnalyticsResponse


# Cache operations endpoints
@router.get("/entries/{key}")
async def get_cache_entry(
    key: str,
    levels: Optional[List[CacheLevel]] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get value from cache."""
    try:
        value = await advanced_cache.get(key, levels)
        
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cache entry not found"
            )
        
        return {
            "key": key,
            "value": value,
            "retrieved_at": datetime.utcnow().isoformat(),
            "levels_searched": [level.value for level in (levels or advanced_cache.enabled_levels)]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache entry: {str(e)}"
        )


@router.post("/entries")
async def set_cache_entry(
    entry_request: CacheEntryRequest,
    current_user: User = Depends(get_current_user)
):
    """Set value in cache."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await advanced_cache.set(
            key=entry_request.key,
            value=entry_request.value,
            ttl=entry_request.ttl,
            tags=entry_request.tags,
            dependencies=entry_request.dependencies,
            levels=entry_request.levels
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set cache entry"
            )
        
        return {
            "message": f"Cache entry set successfully",
            "key": entry_request.key,
            "ttl": entry_request.ttl,
            "levels": [level.value for level in (entry_request.levels or advanced_cache.enabled_levels)],
            "set_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set cache entry: {str(e)}"
        )


@router.delete("/entries/{key}")
async def delete_cache_entry(
    key: str,
    levels: Optional[List[CacheLevel]] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Delete value from cache."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await advanced_cache.delete(key, levels)
        
        return {
            "message": f"Cache entry {'deleted' if success else 'not found'}",
            "key": key,
            "levels": [level.value for level in (levels or advanced_cache.enabled_levels)],
            "deleted_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cache entry: {str(e)}"
        )


# Cache invalidation endpoints
@router.post("/invalidate")
async def invalidate_cache(
    invalidation_request: CacheInvalidationRequest,
    current_user: User = Depends(get_current_user)
):
    """Invalidate cache entries."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        invalidated_keys = set()
        
        if invalidation_request.strategy == InvalidationStrategy.EVENT_BASED:
            # Invalidate by tag
            invalidated_keys = await advanced_cache.invalidate_by_tag(invalidation_request.target)
        
        elif invalidation_request.strategy == InvalidationStrategy.DEPENDENCY_BASED:
            # Invalidate by dependency
            invalidated_keys = await advanced_cache.invalidate_by_dependency(invalidation_request.target)
        
        elif invalidation_request.strategy == InvalidationStrategy.MANUAL:
            # Manual invalidation by key
            success = await advanced_cache.delete(invalidation_request.target, invalidation_request.levels)
            if success:
                invalidated_keys.add(invalidation_request.target)
        
        return {
            "message": f"Cache invalidation completed",
            "strategy": invalidation_request.strategy,
            "target": invalidation_request.target,
            "invalidated_keys": list(invalidated_keys),
            "invalidated_count": len(invalidated_keys),
            "invalidated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache invalidation failed: {str(e)}"
        )


@router.post("/invalidate/tag/{tag}")
async def invalidate_by_tag(
    tag: str,
    current_user: User = Depends(get_current_user)
):
    """Invalidate all cache entries with specific tag."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        invalidated_keys = await advanced_cache.invalidate_by_tag(tag)
        
        return {
            "message": f"Cache entries with tag '{tag}' invalidated",
            "tag": tag,
            "invalidated_keys": list(invalidated_keys),
            "invalidated_count": len(invalidated_keys),
            "invalidated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tag-based invalidation failed: {str(e)}"
        )


@router.post("/invalidate/dependency/{dependency_key}")
async def invalidate_by_dependency(
    dependency_key: str,
    current_user: User = Depends(get_current_user)
):
    """Invalidate cache entries dependent on specific key."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        invalidated_keys = await advanced_cache.invalidate_by_dependency(dependency_key)
        
        return {
            "message": f"Cache entries dependent on '{dependency_key}' invalidated",
            "dependency_key": dependency_key,
            "invalidated_keys": list(invalidated_keys),
            "invalidated_count": len(invalidated_keys),
            "invalidated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependency-based invalidation failed: {str(e)}"
        )


# Cache warming endpoints
@router.post("/warm")
async def warm_cache(
    warming_request: CacheWarmingRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute cache warming strategy."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await advanced_cache.warm_cache(warming_request.strategy_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cache warming strategy '{warming_request.strategy_name}' not found or failed"
            )
        
        return {
            "message": f"Cache warming completed successfully",
            "strategy": warming_request.strategy_name,
            "warmed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache warming failed: {str(e)}"
        )


@router.get("/warming/strategies")
async def list_warming_strategies(
    current_user: User = Depends(get_current_user)
):
    """List available cache warming strategies."""
    strategies = list(advanced_cache.warming_manager.warming_strategies.keys())
    
    return {
        "strategies": strategies,
        "total_count": len(strategies),
        "warming_in_progress": list(advanced_cache.warming_manager.warming_in_progress)
    }


# Cache analytics endpoints
@router.get("/analytics", response_model=CacheOverallAnalyticsResponse)
async def get_cache_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive cache analytics."""
    try:
        analytics_data = await advanced_cache.get_analytics()
        
        # Convert level analytics
        level_analytics = []
        for level, data in analytics_data.items():
            if level != "overall":
                level_analytics.append(CacheAnalyticsResponse(
                    level=level,
                    hits=data["hits"],
                    misses=data["misses"],
                    hit_rate=data["hit_rate"],
                    size_bytes=data["size_bytes"],
                    avg_access_time_ms=data["avg_access_time_ms"],
                    evictions=data["evictions"]
                ))
        
        overall_data = analytics_data.get("overall", {})
        
        return CacheOverallAnalyticsResponse(
            total_hits=overall_data.get("total_hits", 0),
            total_misses=overall_data.get("total_misses", 0),
            overall_hit_rate=overall_data.get("overall_hit_rate", 0.0),
            total_size_bytes=overall_data.get("total_size_bytes", 0),
            enabled_levels=overall_data.get("enabled_levels", []),
            level_analytics=level_analytics
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache analytics: {str(e)}"
        )


@router.get("/analytics/{level}")
async def get_level_analytics(
    level: CacheLevel,
    current_user: User = Depends(get_current_user)
):
    """Get analytics for specific cache level."""
    try:
        analytics_data = await advanced_cache.get_analytics()
        
        level_data = analytics_data.get(level.value)
        if not level_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analytics not found for cache level: {level.value}"
            )
        
        return {
            "level": level.value,
            "analytics": level_data,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve level analytics: {str(e)}"
        )


# Cache configuration endpoints
@router.get("/config")
async def get_cache_config(
    current_user: User = Depends(get_current_user)
):
    """Get current cache configuration."""
    config_data = {
        "enabled_levels": [level.value for level in advanced_cache.enabled_levels],
        "available_levels": [level.value for level in CacheLevel],
        "warming_strategies": list(advanced_cache.warming_manager.warming_strategies.keys()),
        "invalidation_manager": {
            "tag_subscriptions_count": len(advanced_cache.invalidation_manager.tag_subscriptions),
            "dependency_graph_size": len(advanced_cache.invalidation_manager.dependency_graph),
            "invalidation_callbacks": len(advanced_cache.invalidation_manager.invalidation_callbacks)
        }
    }
    
    return config_data


@router.put("/config/levels")
async def update_cache_levels(
    levels: List[CacheLevel],
    current_user: User = Depends(get_current_user)
):
    """Update enabled cache levels."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        # Validate levels
        available_levels = set(CacheLevel)
        for level in levels:
            if level not in available_levels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid cache level: {level}"
                )
        
        # Update enabled levels
        advanced_cache.enabled_levels = levels
        
        return {
            "message": "Cache levels updated successfully",
            "enabled_levels": [level.value for level in levels],
            "updated_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cache levels: {str(e)}"
        )


# Cache operations endpoints
@router.post("/clear")
async def clear_cache(
    levels: Optional[List[CacheLevel]] = Query(None),
    confirm: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Clear cache entries from specified levels."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cache clear operation requires confirmation (confirm=true)"
        )
    
    try:
        target_levels = levels or advanced_cache.enabled_levels
        cleared_levels = []
        
        for level in target_levels:
            if level in advanced_cache.layers:
                success = await advanced_cache.layers[level].clear()
                if success:
                    cleared_levels.append(level.value)
                    # Reset analytics for cleared level
                    advanced_cache.analytics[level] = advanced_cache.analytics[level].__class__()
        
        return {
            "message": "Cache cleared successfully",
            "cleared_levels": cleared_levels,
            "cleared_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/size")
async def get_cache_size(
    levels: Optional[List[CacheLevel]] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get cache size information."""
    try:
        target_levels = levels or advanced_cache.enabled_levels
        size_info = {}
        
        for level in target_levels:
            if level in advanced_cache.layers:
                entry_count = await advanced_cache.layers[level].size()
                analytics = advanced_cache.analytics[level]
                
                size_info[level.value] = {
                    "entry_count": entry_count,
                    "size_bytes": analytics.size_bytes,
                    "size_mb": round(analytics.size_bytes / (1024 * 1024), 2)
                }
        
        total_entries = sum(info["entry_count"] for info in size_info.values())
        total_bytes = sum(info["size_bytes"] for info in size_info.values())
        
        return {
            "levels": size_info,
            "totals": {
                "total_entries": total_entries,
                "total_size_bytes": total_bytes,
                "total_size_mb": round(total_bytes / (1024 * 1024), 2)
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache size: {str(e)}"
        )


# Health check endpoint
@router.get("/health", response_model=CacheHealthResponse)
async def cache_health_check():
    """Check cache system health."""
    try:
        health_info = await check_advanced_cache_health()
        
        # Convert analytics to response format
        analytics_data = health_info["analytics"]
        level_analytics = []
        
        for level, data in analytics_data.items():
            if level != "overall":
                level_analytics.append(CacheAnalyticsResponse(
                    level=level,
                    hits=data["hits"],
                    misses=data["misses"],
                    hit_rate=data["hit_rate"],
                    size_bytes=data["size_bytes"],
                    avg_access_time_ms=data["avg_access_time_ms"],
                    evictions=data["evictions"]
                ))
        
        overall_data = analytics_data.get("overall", {})
        
        analytics_response = CacheOverallAnalyticsResponse(
            total_hits=overall_data.get("total_hits", 0),
            total_misses=overall_data.get("total_misses", 0),
            overall_hit_rate=overall_data.get("overall_hit_rate", 0.0),
            total_size_bytes=overall_data.get("total_size_bytes", 0),
            enabled_levels=overall_data.get("enabled_levels", []),
            level_analytics=level_analytics
        )
        
        return CacheHealthResponse(
            status=health_info["status"],
            warming_strategies=health_info["warming_strategies"],
            invalidation_tags=health_info["invalidation_tags"],
            dependency_graph_size=health_info["dependency_graph_size"],
            analytics=analytics_response
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cache health check failed: {str(e)}"
        )