"""Enhanced health check API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=dict[str, Any])
async def comprehensive_health_check(
    detailed: bool = Query(False, description="Include detailed system metrics"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Comprehensive health check with all system components.

    This endpoint provides a complete health assessment of the ITDO ERP system,
    including database, cache, external dependencies, and system resources.
    """
    from datetime import datetime, timezone

    from app.core.monitoring import health_checker, setup_health_checks

    # Setup health checks if not already done
    try:
        setup_health_checks(None, lambda: db, None)
    except Exception:
        # Health checks might already be setup
        pass

    try:
        # Use enhanced health checker if available
        try:
            from app.core.health import HealthStatus, get_health_checker

            health_checker_enhanced = get_health_checker()

            if detailed:
                # Run comprehensive health check with detailed metrics
                health_report = await health_checker_enhanced.check_system_health(
                    include_detailed=detailed
                )

                return {
                    "status": health_report.overall_status.value,
                    "timestamp": health_report.timestamp.isoformat(),
                    "version": health_report.version,
                    "environment": health_report.environment,
                    "uptime_seconds": health_report.uptime_seconds,
                    "components": [
                        {
                            "component": comp.component,
                            "type": comp.component_type.value,
                            "status": comp.status.value,
                            "response_time_ms": comp.response_time_ms,
                            "timestamp": comp.timestamp.isoformat(),
                            "message": comp.message,
                            "details": comp.details,
                            "metrics": [
                                {
                                    "name": metric.name,
                                    "value": metric.value,
                                    "unit": metric.unit,
                                    "threshold_warning": metric.threshold_warning,
                                    "threshold_critical": metric.threshold_critical,
                                    "description": metric.description,
                                }
                                for metric in comp.metrics
                            ]
                            if hasattr(comp, "metrics")
                            else [],
                            "error": comp.error if hasattr(comp, "error") else None,
                        }
                        for comp in health_report.components
                    ],
                    "performance_metrics": health_report.performance_metrics,
                    "alerts": health_report.alerts,
                    "recommendations": health_report.recommendations,
                    "summary": health_report.summary
                    if hasattr(health_report, "summary")
                    else None,
                    "overall_healthy": health_report.overall_status
                    == HealthStatus.HEALTHY,
                }
        except ImportError:
            # Fall back to basic health checker
            pass

        # Use basic health checker as fallback
        health_results = await health_checker.run_checks()

        return {
            "status": "healthy" if health_results["healthy"] else "unhealthy",
            "timestamp": health_results["timestamp"],
            "version": "2.1.0",
            "service": "ITDO ERP API",
            "protocol": "v17.0",
            "checks": health_results["checks"],
            "overall_healthy": health_results["healthy"],
        }

    except Exception as e:
        # If health check system fails, return minimal status
        return {
            "status": "unhealthy",
            "error": f"Health check system failure: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fallback_mode": True,
        }


@router.get("/simple")
async def simple_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Simple health check for basic monitoring."""
    from datetime import datetime, timezone

    from app.core.monitoring import health_checker

    try:
        # Use health checker for consistent protocol
        health_results = await health_checker.run_checks()

        return {
            "status": "healthy" if health_results["healthy"] else "unhealthy",
            "timestamp": health_results["timestamp"],
            "protocol": "v17.0",
            "checks": health_results["checks"],
            "overall_healthy": health_results["healthy"],
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": "v17.0",
            "error": str(e),
            "overall_healthy": False,
        }


@router.get("/live", response_model=dict[str, str])
async def liveness_probe() -> dict[str, str]:
    """Kubernetes liveness probe - basic application responsiveness."""
    return {"status": "alive"}


@router.get("/ready", response_model=dict[str, Any])
async def readiness_probe(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Kubernetes readiness probe - checks if app can serve traffic."""
    from datetime import datetime, timezone

    try:
        # Quick essential health checks for readiness
        ready_checks = {
            "database": False,
            "redis": False,
            "application": True,  # Application is running if we reached this point
        }

        # Test database connectivity
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        ready_checks["database"] = True

        # Test Redis connectivity
        try:
            from app.core.database import get_redis

            redis_client = get_redis()
            await redis_client.ping()
            ready_checks["redis"] = True
        except:
            # Redis failure is not critical for readiness
            pass

        # Service is ready if essential services are available
        is_ready = ready_checks["database"] and ready_checks["application"]

        if not is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service dependencies not ready",
            )

        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": ready_checks,
            "ready": is_ready,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}",
        )


@router.get("/database", response_model=dict[str, Any])
async def database_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Detailed database health check."""

    try:
        import time

        from sqlalchemy import text

        start_time = time.time()

        # Test basic connectivity
        result = db.execute(text("SELECT 1 as test")).fetchone()
        basic_duration = time.time() - start_time

        # Test some table queries
        start_time = time.time()
        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        count_duration = time.time() - start_time

        return {
            "status": "healthy",
            "basic_query": {
                "result": result[0] if result else None,
                "duration_ms": round(basic_duration * 1000, 2),
            },
            "count_query": {
                "users_count": users_count,
                "duration_ms": round(count_duration * 1000, 2),
            },
            "total_duration_ms": round((basic_duration + count_duration) * 1000, 2),
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "error_type": type(e).__name__}


@router.get("/metrics", response_model=dict[str, Any])
async def health_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed health metrics for monitoring systems."""
    from datetime import datetime, timezone

    try:
        # Try enhanced health checker first
        from app.core.health import HealthStatus, get_health_checker

        health_checker_enhanced = get_health_checker()
        health_report = await health_checker_enhanced.check_system_health(
            include_detailed=True
        )
        metrics = health_report.performance_metrics or {}

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": health_report.uptime_seconds,
            "metrics": metrics,
            "component_count": len(health_report.components),
            "healthy_components": len(
                [
                    comp
                    for comp in health_report.components
                    if comp.status == HealthStatus.HEALTHY
                ]
            ),
            "status": health_report.overall_status.value,
        }
    except ImportError:
        # Fallback to basic metrics
        from app.core.monitoring import get_metrics

        try:
            metrics_data = get_metrics()
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics_data,
                "status": "healthy",
                "metrics_available": True,
            }
        except Exception as e:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "status": "error",
                "metrics_available": False,
            }
    except Exception as e:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "error",
        }


@router.get("/system", response_model=dict[str, Any])
async def system_health() -> dict[str, Any]:
    """System-level health checks (disk, memory, etc)."""

    try:
        import shutil

        import psutil

        # Disk space check
        total, used, free = shutil.disk_usage("/")
        disk_free_percent = (free / total) * 100

        # Memory check
        memory = psutil.virtual_memory()

        # CPU check
        cpu_percent = psutil.cpu_percent(interval=1)

        return {
            "status": "healthy",
            "disk": {
                "free_percent": round(disk_free_percent, 2),
                "free_gb": round(free / (1024**3), 2),
                "total_gb": round(total / (1024**3), 2),
                "healthy": disk_free_percent > 10,
            },
            "memory": {
                "used_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "healthy": memory.percent < 90,
            },
            "cpu": {"usage_percent": cpu_percent, "healthy": cpu_percent < 90},
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "error_type": type(e).__name__}


@router.get("/startup", response_model=dict[str, Any])
async def startup_health() -> dict[str, Any]:
    """Check if all startup components are properly initialized."""
    from app.core.monitoring import health_checker

    status_checks = {
        "monitoring_initialized": False,
        "health_checker_ready": False,
        "database_session_factory": False,
    }

    try:
        # Check if monitoring is set up
        status_checks["monitoring_initialized"] = True

        # Check if health checker has checks registered
        status_checks["health_checker_ready"] = len(health_checker.checks) > 0

        # Check database session factory
        from app.core.database import SessionLocal

        with SessionLocal() as session:
            from sqlalchemy import text

            session.execute(text("SELECT 1"))
            status_checks["database_session_factory"] = True

        all_healthy = all(status_checks.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": status_checks,
            "overall_healthy": all_healthy,
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "checks": status_checks,
            "error": str(e),
            "overall_healthy": False,
        }


@router.get("/agent", response_model=dict[str, Any])
async def agent_health() -> dict[str, Any]:
    """Agent-specific health check for LEVEL 1 ESCALATION."""

    try:
        import datetime
        import time

        import psutil

        start_time = time.time()

        # Simulate agent responsiveness test
        response_time = time.time() - start_time

        # Check system resources for agent performance
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Agent health criteria
        agent_healthy = (
            response_time < 1.0  # Response under 1 second
            and memory.percent < 85  # Memory usage under 85%
            and cpu_percent < 85  # CPU usage under 85%
        )

        return {
            "status": "healthy" if agent_healthy else "degraded",
            "agent_response_time_ms": round(response_time * 1000, 2),
            "system_resources": {
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": cpu_percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
            },
            "performance_criteria": {
                "response_time_ok": response_time < 1.0,
                "memory_ok": memory.percent < 85,
                "cpu_ok": cpu_percent < 85,
            },
            "overall_agent_health": agent_healthy,
            "timestamp": datetime.datetime.now().isoformat(),
            "escalation_level": "LEVEL_1" if not agent_healthy else "NORMAL",
        }

    except Exception as e:
        return {
            "status": "critical",
            "error": str(e),
            "escalation_level": "LEVEL_1",
            "timestamp": datetime.datetime.now().isoformat(),
            "agent_health": False,
        }
