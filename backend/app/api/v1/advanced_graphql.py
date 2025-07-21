"""Advanced GraphQL features API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.graphql.advanced.federation import (
    federation_registry,
    check_graphql_federation_health
)
from app.graphql.advanced.middleware import (
    performance_middleware,
    security_middleware,
    caching_middleware,
    rate_limit_middleware,
    audit_middleware,
    check_graphql_middleware_health
)
from app.graphql.advanced.subscriptions import (
    subscription_manager,
    SubscriptionEventType,
    check_graphql_subscriptions_health
)
from app.graphql.advanced.validation import (
    standard_validator,
    strict_validator,
    enterprise_validator,
    ValidationLevel,
    check_graphql_validation_health
)
from app.graphql.advanced.analytics import (
    graphql_analytics,
    QueryExecution,
    QueryType,
    check_graphql_analytics_health
)
from app.graphql.advanced.caching import (
    query_cache_manager,
    check_graphql_caching_health
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class AdvancedGraphQLHealthResponse(BaseModel):
    """Advanced GraphQL system health response."""
    status: str
    federation: Dict[str, Any]
    middleware: Dict[str, Any]
    subscriptions: Dict[str, Any]
    validation: Dict[str, Any]
    analytics: Dict[str, Any]
    caching: Dict[str, Any]
    last_updated: str


class FederationStatusResponse(BaseModel):
    """Federation status response."""
    overall_status: str
    subgraphs: Dict[str, Any]
    composition_info: Dict[str, Any]


class MiddlewareStatsResponse(BaseModel):
    """Middleware statistics response."""
    performance: Dict[str, Any]
    security: Dict[str, Any]
    caching: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    audit: Dict[str, Any]


class ValidationRequest(BaseModel):
    """Query validation request."""
    query: str = Field(..., max_length=50000)
    variables: Optional[Dict[str, Any]] = None
    validation_level: ValidationLevel = ValidationLevel.STANDARD


class ValidationResponse(BaseModel):
    """Query validation response."""
    is_valid: bool
    allow_execution: bool
    complexity_analysis: Dict[str, Any]
    validation_errors: List[str]
    validation_warnings: List[str]
    execution_recommendations: List[str]
    estimated_cost: float


class AnalyticsRequest(BaseModel):
    """Analytics request parameters."""
    hours: int = Field(24, ge=1, le=168)  # 1 hour to 1 week
    include_details: bool = False


class AnalyticsResponse(BaseModel):
    """Analytics response."""
    performance_metrics: Dict[str, Any]
    usage_analytics: Dict[str, Any]
    security_analytics: Dict[str, Any]
    insights: List[str]
    generated_at: str


class CacheInvalidationRequest(BaseModel):
    """Cache invalidation request."""
    invalidation_type: str = Field(..., regex="^(dependency|tags|pattern|user|organization|all)$")
    target: Optional[str] = None
    tags: Optional[List[str]] = None


class SubscriptionEventRequest(BaseModel):
    """Subscription event publishing request."""
    event_type: SubscriptionEventType
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


# Health check endpoint
@router.get("/health", response_model=AdvancedGraphQLHealthResponse)
async def advanced_graphql_health_check():
    """Check advanced GraphQL system health."""
    try:
        federation_health = await check_graphql_federation_health()
        middleware_health = await check_graphql_middleware_health()
        subscriptions_health = await check_graphql_subscriptions_health()
        validation_health = await check_graphql_validation_health()
        analytics_health = await check_graphql_analytics_health()
        caching_health = await check_graphql_caching_health()
        
        # Determine overall status
        components_status = [
            federation_health["status"],
            middleware_health["status"],
            subscriptions_health["status"],
            validation_health["status"],
            analytics_health["status"],
            caching_health["status"]
        ]
        
        if all(status == "healthy" for status in components_status):
            overall_status = "healthy"
        elif any(status in ["unhealthy", "critical"] for status in components_status):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        return AdvancedGraphQLHealthResponse(
            status=overall_status,
            federation=federation_health,
            middleware=middleware_health,
            subscriptions=subscriptions_health,
            validation=validation_health,
            analytics=analytics_health,
            caching=caching_health,
            last_updated=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Advanced GraphQL health check failed: {str(e)}"
        )


# Federation endpoints
@router.get("/federation/status", response_model=FederationStatusResponse)
async def get_federation_status(
    current_user: User = Depends(get_current_user)
):
    """Get GraphQL federation status."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        federation_status = federation_registry.get_federation_status()
        health_status = await federation_registry.health_check_all_subgraphs()
        
        return FederationStatusResponse(
            overall_status=federation_status["overall_status"],
            subgraphs=federation_status["subgraph_metrics"],
            composition_info={
                "schema_cached": federation_status["schema_cached"],
                "last_composition": federation_status["last_composition"],
                "federation_version": federation_status["federation_version"]
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get federation status: {str(e)}"
        )


@router.post("/federation/compose-schema")
async def compose_federated_schema(
    current_user: User = Depends(get_current_user)
):
    """Trigger federated schema composition."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        schema = await federation_registry.compose_federated_schema()
        
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to compose schema - no healthy subgraphs"
            )
        
        return {
            "message": "Schema composition successful",
            "composed_at": datetime.utcnow().isoformat(),
            "schema_size": len(schema),
            "subgraph_count": len(federation_registry.subgraphs)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema composition failed: {str(e)}"
        )


# Middleware endpoints
@router.get("/middleware/stats", response_model=MiddlewareStatsResponse)
async def get_middleware_stats(
    current_user: User = Depends(get_current_user)
):
    """Get middleware statistics."""
    try:
        return MiddlewareStatsResponse(
            performance=performance_middleware.get_performance_summary(),
            security=security_middleware.get_security_summary(),
            caching=caching_middleware.get_cache_summary(),
            rate_limiting=rate_limit_middleware.get_rate_limit_summary(),
            audit=audit_middleware.get_audit_summary()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get middleware stats: {str(e)}"
        )


@router.post("/middleware/security/violations")
async def get_security_violations(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get recent security violations."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        violations = list(security_middleware.violations)[-limit:]
        
        violation_list = []
        for violation in violations:
            violation_list.append({
                "id": violation.id,
                "violation_type": violation.violation_type,
                "severity": violation.severity,
                "ip_address": violation.ip_address,
                "user_id": violation.user_id,
                "timestamp": violation.timestamp.isoformat(),
                "blocked": violation.blocked,
                "details": violation.details
            })
        
        return {
            "violations": violation_list,
            "total_count": len(violation_list),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security violations: {str(e)}"
        )


# Validation endpoints
@router.post("/validation/validate", response_model=ValidationResponse)
async def validate_query(
    validation_request: ValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """Validate GraphQL query."""
    try:
        # Select validator based on level
        if validation_request.validation_level == ValidationLevel.STRICT:
            validator = strict_validator
        elif validation_request.validation_level == ValidationLevel.ENTERPRISE:
            validator = enterprise_validator
        else:
            validator = standard_validator
        
        # Prepare user context
        user_context = {
            "user_id": str(current_user.id),
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None,
            "role": "admin" if current_user.is_superuser else "user",
            "is_authenticated": True
        }
        
        # Validate query
        result = validator.validate_query(
            validation_request.query,
            validation_request.variables,
            user_context
        )
        
        return ValidationResponse(
            is_valid=result.is_valid,
            allow_execution=result.allow_execution,
            complexity_analysis={
                "total_score": result.complexity_analysis.total_score,
                "depth": result.complexity_analysis.depth,
                "field_count": result.complexity_analysis.field_count,
                "estimated_execution_time_ms": result.complexity_analysis.estimated_execution_time_ms,
                "memory_estimate_mb": result.complexity_analysis.memory_estimate_mb,
                "risk_level": result.complexity_analysis.risk_level,
                "violations": result.complexity_analysis.violations
            },
            validation_errors=result.validation_errors,
            validation_warnings=result.validation_warnings,
            execution_recommendations=result.execution_recommendations,
            estimated_cost=result.estimated_cost
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query validation failed: {str(e)}"
        )


@router.get("/validation/summary")
async def get_validation_summary(
    current_user: User = Depends(get_current_user)
):
    """Get validation system summary."""
    try:
        return {
            "standard": standard_validator.get_validation_summary(),
            "strict": strict_validator.get_validation_summary(),
            "enterprise": enterprise_validator.get_validation_summary()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation summary: {str(e)}"
        )


# Analytics endpoints
@router.post("/analytics/report", response_model=AnalyticsResponse)
async def get_analytics_report(
    analytics_request: AnalyticsRequest,
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics report."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        analytics_data = graphql_analytics.get_comprehensive_analytics(analytics_request.hours)
        
        response_data = {
            "performance_metrics": analytics_data["performance_metrics"],
            "usage_analytics": analytics_data["usage_analytics"],
            "security_analytics": analytics_data["security_analytics"],
            "insights": analytics_data["insights"],
            "generated_at": analytics_data["generated_at"]
        }
        
        if analytics_request.include_details:
            response_data.update({
                "anomalies": analytics_data["anomalies"],
                "alerts": analytics_data["alerts"],
                "realtime_metrics": analytics_data["realtime_metrics"]
            })
        
        return AnalyticsResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics report: {str(e)}"
        )


@router.get("/analytics/export")
async def export_analytics_data(
    format_type: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user)
):
    """Export analytics data."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        exported_data = graphql_analytics.export_analytics_data(format_type)
        
        return {
            "format": format_type,
            "data": exported_data,
            "exported_at": datetime.utcnow().isoformat(),
            "size_bytes": len(exported_data.encode())
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics data: {str(e)}"
        )


# Caching endpoints
@router.get("/cache/status")
async def get_cache_status(
    current_user: User = Depends(get_current_user)
):
    """Get cache system status."""
    try:
        return query_cache_manager.get_comprehensive_status()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache status: {str(e)}"
        )


@router.post("/cache/invalidate")
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
        invalidated_count = 0
        
        if invalidation_request.invalidation_type == "all":
            invalidated_count = query_cache_manager.cache.clear()
        elif invalidation_request.invalidation_type == "dependency":
            if not invalidation_request.target:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target dependency required"
                )
            invalidated_count = query_cache_manager.cache.invalidate_by_dependency(
                invalidation_request.target
            )
        elif invalidation_request.invalidation_type == "pattern":
            if not invalidation_request.target:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target pattern required"
                )
            invalidated_count = query_cache_manager.cache.invalidate_by_pattern(
                invalidation_request.target
            )
        elif invalidation_request.invalidation_type == "tags":
            if not invalidation_request.tags:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tags required"
                )
            invalidated_count = query_cache_manager.cache.invalidate_by_tags(
                set(invalidation_request.tags)
            )
        elif invalidation_request.invalidation_type == "user":
            if not invalidation_request.target:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID required"
                )
            invalidated_count = query_cache_manager.invalidate_user_data(
                invalidation_request.target
            )
        elif invalidation_request.invalidation_type == "organization":
            if not invalidation_request.target:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization ID required"
                )
            invalidated_count = query_cache_manager.invalidate_organization_data(
                invalidation_request.target
            )
        
        return {
            "message": f"Cache invalidation successful",
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


# Subscription endpoints
@router.get("/subscriptions/status")
async def get_subscriptions_status(
    current_user: User = Depends(get_current_user)
):
    """Get subscriptions system status."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        metrics = subscription_manager.get_subscription_metrics()
        
        return {
            "metrics": {
                "total_connections": metrics.total_connections,
                "active_connections": metrics.active_connections,
                "events_published_24h": metrics.events_published_24h,
                "events_delivered_24h": metrics.events_delivered_24h,
                "average_delivery_time_ms": metrics.average_delivery_time_ms,
                "error_rate_percentage": metrics.error_rate_percentage,
                "connection_duration_avg_minutes": metrics.connection_duration_avg_minutes,
                "popular_event_types": metrics.popular_event_types
            },
            "background_tasks": len(subscription_manager.background_tasks),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscriptions status: {str(e)}"
        )


@router.post("/subscriptions/publish-event")
async def publish_subscription_event(
    event_request: SubscriptionEventRequest,
    current_user: User = Depends(get_current_user)
):
    """Publish subscription event."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        event_id = await subscription_manager.publish_event(
            event_request.event_type,
            event_request.payload,
            source="admin_api",
            metadata=event_request.metadata
        )
        
        return {
            "message": "Event published successfully",
            "event_id": event_id,
            "event_type": event_request.event_type.value,
            "published_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish event: {str(e)}"
        )


@router.post("/subscriptions/broadcast-alert")
async def broadcast_system_alert(
    message: str = Query(..., max_length=500),
    severity: str = Query("info", regex="^(info|warning|error|critical)$"),
    current_user: User = Depends(get_current_user)
):
    """Broadcast system-wide alert."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        alert_id = await subscription_manager.broadcast_system_alert(
            message,
            severity,
            {"admin_user": str(current_user.id)}
        )
        
        return {
            "message": "System alert broadcasted successfully",
            "alert_id": alert_id,
            "severity": severity,
            "broadcasted_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast alert: {str(e)}"
        )


# System information endpoints
@router.get("/system/capabilities")
async def get_system_capabilities():
    """Get advanced GraphQL system capabilities."""
    return {
        "federation": {
            "enabled": True,
            "version": "2.0",
            "subgraph_support": True,
            "schema_composition": True
        },
        "middleware": {
            "performance_monitoring": True,
            "security_protection": True,
            "intelligent_caching": True,
            "rate_limiting": True,
            "audit_logging": True
        },
        "subscriptions": {
            "real_time_events": True,
            "connection_management": True,
            "event_filtering": True,
            "delivery_guarantees": True
        },
        "validation": {
            "complexity_analysis": True,
            "custom_rules": True,
            "multiple_levels": True,
            "cost_estimation": True
        },
        "analytics": {
            "performance_tracking": True,
            "usage_analytics": True,
            "security_monitoring": True,
            "anomaly_detection": True,
            "data_export": True
        },
        "caching": {
            "intelligent_caching": True,
            "dependency_tracking": True,
            "tag_based_invalidation": True,
            "smart_eviction": True
        }
    }