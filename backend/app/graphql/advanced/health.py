"""Comprehensive health check for advanced GraphQL features."""

from datetime import datetime
from typing import Any, Dict

from app.core.monitoring import monitor_performance
from .federation import check_graphql_federation_health
from .middleware import check_graphql_middleware_health
from .subscriptions import check_graphql_subscriptions_health
from .validation import check_graphql_validation_health
from .analytics import check_graphql_analytics_health
from .caching import check_graphql_caching_health


@monitor_performance("graphql.advanced.health_check")
async def check_advanced_graphql_health() -> Dict[str, Any]:
    """Comprehensive health check for all advanced GraphQL features."""
    health_checks = {}
    
    try:
        # Federation health
        health_checks["federation"] = await check_graphql_federation_health()
    except Exception as e:
        health_checks["federation"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        # Middleware health
        health_checks["middleware"] = await check_graphql_middleware_health()
    except Exception as e:
        health_checks["middleware"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        # Subscriptions health
        health_checks["subscriptions"] = await check_graphql_subscriptions_health()
    except Exception as e:
        health_checks["subscriptions"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        # Validation health
        health_checks["validation"] = await check_graphql_validation_health()
    except Exception as e:
        health_checks["validation"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        # Analytics health
        health_checks["analytics"] = await check_graphql_analytics_health()
    except Exception as e:
        health_checks["analytics"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        # Caching health
        health_checks["caching"] = await check_graphql_caching_health()
    except Exception as e:
        health_checks["caching"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Determine overall status
    statuses = [
        check.get("status", "error") 
        for check in health_checks.values()
    ]
    
    if all(status == "healthy" for status in statuses):
        overall_status = "healthy"
    elif any(status in ["error", "critical"] for status in statuses):
        overall_status = "unhealthy"
    elif any(status == "degraded" for status in statuses):
        overall_status = "degraded"
    else:
        overall_status = "warning"
    
    # Component summary
    component_summary = {
        component: check.get("status", "error")
        for component, check in health_checks.items()
    }
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": health_checks,
        "summary": {
            "overall_status": overall_status,
            "total_components": len(health_checks),
            "healthy_components": len([s for s in statuses if s == "healthy"]),
            "degraded_components": len([s for s in statuses if s == "degraded"]),
            "unhealthy_components": len([s for s in statuses if s in ["error", "critical"]]),
            "component_status": component_summary
        },
        "capabilities": {
            "federation": {
                "enabled": True,
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
                "event_filtering": True
            },
            "validation": {
                "complexity_analysis": True,
                "custom_rules": True,
                "multiple_levels": True
            },
            "analytics": {
                "performance_tracking": True,
                "usage_analytics": True,
                "security_monitoring": True,
                "anomaly_detection": True
            },
            "caching": {
                "intelligent_caching": True,
                "dependency_tracking": True,
                "smart_eviction": True
            }
        }
    }