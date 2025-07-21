"""Multi-tenant performance optimization API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.multi_tenant_performance import (
    performance_manager,
    ResourceType,
    OptimizationStrategy,
    check_multi_tenant_performance_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class TenantMetricsResponse(BaseModel):
    """Tenant metrics response schema."""
    tenant_id: str
    request_count: int
    avg_response_time: float
    error_rate: float
    resource_usage: Dict[str, float]
    peak_concurrent_users: int
    data_volume: int
    query_complexity_score: float
    last_activity: datetime

    class Config:
        from_attributes = True


class OptimizationRecommendationResponse(BaseModel):
    """Optimization recommendation response schema."""
    type: str
    priority: str
    message: str
    suggestion: str
    metric: str
    value: float


class ResourceAllocationRequest(BaseModel):
    """Resource allocation request schema."""
    tenant_id: str = Field(..., max_length=100)
    resource_type: ResourceType
    amount: int = Field(..., ge=1)


class QueryOptimizationRequest(BaseModel):
    """Query optimization request schema."""
    tenant_id: str = Field(..., max_length=100)
    query: str = Field(..., max_length=10000)


class QueryAnalysisResponse(BaseModel):
    """Query analysis response schema."""
    query_hash: str
    complexity_score: float
    optimization_suggestions: List[str]
    estimated_cost: int
    tenant_specific_optimizations: List[str]


class ResourcePoolStatus(BaseModel):
    """Resource pool status schema."""
    resource_type: str
    total_capacity: int
    allocated: int
    utilization_rate: float
    active_tenants: int


class SystemOverviewResponse(BaseModel):
    """System overview response schema."""
    total_tenants: int
    active_tenants: int
    resource_utilization: Dict[str, ResourcePoolStatus]
    performance_metrics: Dict[str, float]
    optimization_strategies_active: int
    timestamp: str


class PerformanceHealthResponse(BaseModel):
    """Performance health response schema."""
    status: str
    system_overview: SystemOverviewResponse
    query_optimizer_patterns: int
    connection_pools: int
    load_balancer_queues: int


# Tenant metrics endpoints
@router.get("/tenants/{tenant_id}/metrics", response_model=TenantMetricsResponse)
async def get_tenant_metrics(
    tenant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for a specific tenant."""
    metrics = await performance_manager.get_tenant_metrics(tenant_id)
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for tenant: {tenant_id}"
        )
    
    return TenantMetricsResponse(
        tenant_id=metrics.tenant_id,
        request_count=metrics.request_count,
        avg_response_time=metrics.avg_response_time,
        error_rate=metrics.error_rate,
        resource_usage={rt.value: usage for rt, usage in metrics.resource_usage.items()},
        peak_concurrent_users=metrics.peak_concurrent_users,
        data_volume=metrics.data_volume,
        query_complexity_score=metrics.query_complexity_score,
        last_activity=metrics.last_activity
    )


@router.get("/tenants/{tenant_id}/recommendations", response_model=List[OptimizationRecommendationResponse])
async def get_tenant_recommendations(
    tenant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get optimization recommendations for a specific tenant."""
    recommendations = await performance_manager.get_optimization_recommendations(tenant_id)
    
    return [
        OptimizationRecommendationResponse(**rec)
        for rec in recommendations
    ]


# Resource management endpoints
@router.post("/resources/allocate")
async def allocate_resources(
    allocation_request: ResourceAllocationRequest,
    current_user: User = Depends(get_current_user)
):
    """Allocate resources to a tenant."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        success = await performance_manager.allocate_resources(
            tenant_id=allocation_request.tenant_id,
            resource_type=allocation_request.resource_type,
            amount=allocation_request.amount
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to allocate {allocation_request.amount} {allocation_request.resource_type.value} resources"
            )
        
        return {
            "message": f"Successfully allocated {allocation_request.amount} {allocation_request.resource_type.value} resources",
            "tenant_id": allocation_request.tenant_id,
            "resource_type": allocation_request.resource_type.value,
            "amount": allocation_request.amount,
            "allocated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resource allocation failed: {str(e)}"
        )


@router.post("/resources/deallocate")
async def deallocate_resources(
    allocation_request: ResourceAllocationRequest,
    current_user: User = Depends(get_current_user)
):
    """Deallocate resources from a tenant."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        deallocated = await performance_manager.deallocate_resources(
            tenant_id=allocation_request.tenant_id,
            resource_type=allocation_request.resource_type,
            amount=allocation_request.amount
        )
        
        return {
            "message": f"Successfully deallocated {deallocated} {allocation_request.resource_type.value} resources",
            "tenant_id": allocation_request.tenant_id,
            "resource_type": allocation_request.resource_type.value,
            "requested_amount": allocation_request.amount,
            "actual_deallocated": deallocated,
            "deallocated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resource deallocation failed: {str(e)}"
        )


# Query optimization endpoints
@router.post("/query/optimize", response_model=QueryAnalysisResponse)
async def optimize_query(
    optimization_request: QueryOptimizationRequest,
    current_user: User = Depends(get_current_user)
):
    """Optimize a query for a specific tenant."""
    try:
        analysis = await performance_manager.optimize_query(
            tenant_id=optimization_request.tenant_id,
            query=optimization_request.query
        )
        
        return QueryAnalysisResponse(**analysis)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query optimization failed: {str(e)}"
        )


@router.get("/query/patterns/{tenant_id}")
async def get_tenant_query_patterns(
    tenant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get query patterns for a specific tenant."""
    try:
        patterns = performance_manager.query_optimizer.tenant_query_patterns.get(tenant_id, {})
        
        # Convert to readable format
        pattern_summary = []
        for query_hash, count in patterns.items():
            pattern_summary.append({
                "query_hash": query_hash,
                "execution_count": count,
                "frequency_rank": len([c for c in patterns.values() if c > count]) + 1
            })
        
        # Sort by execution count
        pattern_summary.sort(key=lambda x: x["execution_count"], reverse=True)
        
        return {
            "tenant_id": tenant_id,
            "total_unique_queries": len(patterns),
            "total_executions": sum(patterns.values()),
            "top_patterns": pattern_summary[:20],  # Top 20 patterns
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve query patterns: {str(e)}"
        )


# System overview endpoints
@router.get("/system/overview", response_model=SystemOverviewResponse)
async def get_system_overview(
    current_user: User = Depends(get_current_user)
):
    """Get system performance overview."""
    try:
        overview = await performance_manager.get_system_overview()
        
        # Convert resource utilization to proper format
        resource_util = {}
        for resource_type, info in overview["resource_utilization"].items():
            resource_util[resource_type] = ResourcePoolStatus(
                resource_type=resource_type,
                total_capacity=info["total_capacity"],
                allocated=info["allocated"],
                utilization_rate=info["utilization_rate"],
                active_tenants=info["active_tenants"]
            )
        
        return SystemOverviewResponse(
            total_tenants=overview["total_tenants"],
            active_tenants=overview["active_tenants"],
            resource_utilization=resource_util,
            performance_metrics=overview["performance_metrics"],
            optimization_strategies_active=overview["optimization_strategies_active"],
            timestamp=overview["timestamp"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system overview: {str(e)}"
        )


@router.get("/system/resource-pools")
async def get_resource_pools_status(
    current_user: User = Depends(get_current_user)
):
    """Get detailed status of all resource pools."""
    try:
        pools_status = {}
        
        for resource_type, pool in performance_manager.resource_pools.items():
            pools_status[resource_type.value] = {
                "total_capacity": pool.total_capacity,
                "allocated_resources": dict(pool.allocated_resources),
                "available_capacity": pool.available_capacity,
                "utilization_rate": pool.utilization_rate,
                "reserved_capacity": pool.reserved_capacity,
                "utilization_history": [
                    {"timestamp": ts.isoformat(), "utilization": util}
                    for ts, util in list(pool.utilization_history)[-10:]  # Last 10 entries
                ]
            }
        
        return {
            "resource_pools": pools_status,
            "total_pools": len(pools_status),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resource pools status: {str(e)}"
        )


@router.get("/optimization/strategies")
async def list_optimization_strategies(
    current_user: User = Depends(get_current_user)
):
    """List available optimization strategies."""
    strategies = []
    for strategy in OptimizationStrategy:
        strategies.append({
            "name": strategy.value,
            "description": strategy.value.replace("_", " ").title()
        })
    
    return {
        "strategies": strategies,
        "total_count": len(strategies),
        "available_resource_types": [rt.value for rt in ResourceType]
    }


# Health check endpoint
@router.get("/health", response_model=PerformanceHealthResponse)
async def performance_health_check():
    """Check multi-tenant performance system health."""
    try:
        health_info = await check_multi_tenant_performance_health()
        
        # Convert system overview
        overview_data = health_info["system_overview"]
        resource_util = {}
        for resource_type, info in overview_data["resource_utilization"].items():
            resource_util[resource_type] = ResourcePoolStatus(
                resource_type=resource_type,
                total_capacity=info["total_capacity"],
                allocated=info["allocated"],
                utilization_rate=info["utilization_rate"],
                active_tenants=info["active_tenants"]
            )
        
        system_overview = SystemOverviewResponse(
            total_tenants=overview_data["total_tenants"],
            active_tenants=overview_data["active_tenants"],
            resource_utilization=resource_util,
            performance_metrics=overview_data["performance_metrics"],
            optimization_strategies_active=overview_data["optimization_strategies_active"],
            timestamp=overview_data["timestamp"]
        )
        
        return PerformanceHealthResponse(
            status=health_info["status"],
            system_overview=system_overview,
            query_optimizer_patterns=health_info["query_optimizer_patterns"],
            connection_pools=health_info["connection_pools"],
            load_balancer_queues=health_info["load_balancer_queues"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Performance health check failed: {str(e)}"
        )


# Tenant performance tracking endpoint
@router.post("/tenants/{tenant_id}/track")
async def track_tenant_performance(
    tenant_id: str,
    request_type: str = Query(...),
    response_time: float = Query(..., ge=0),
    error: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Track performance metrics for a tenant request."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        await performance_manager.track_request(
            tenant_id=tenant_id,
            request_type=request_type,
            response_time=response_time,
            error=error
        )
        
        return {
            "message": "Performance metrics tracked successfully",
            "tenant_id": tenant_id,
            "request_type": request_type,
            "response_time": response_time,
            "error": error,
            "tracked_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track performance metrics: {str(e)}"
        )