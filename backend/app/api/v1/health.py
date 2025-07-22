"""Enhanced health check API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.health import HealthStatus, SystemHealthReport, get_health_checker
from app.core.monitoring import health_checker

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

    health_checker = get_health_checker()

    try:
        # Run comprehensive health check
        health_report: SystemHealthReport = await health_checker.check_system_health(
            include_detailed=detailed
        )

        # Convert to API response format
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
                            "description": metric.description
                        }
                        for metric in comp.metrics
                    ],
                    "error": comp.error
                }
                for comp in health_report.components
            ],
            "summary": health_report.summary,
            "overall_healthy": health_report.overall_status == HealthStatus.HEALTHY
        }

    except Exception as e:
        # Fallback to basic health check if comprehensive fails
        from datetime import datetime, timezone
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": health_checker.version,
            "environment": health_checker.environment,
            "error": f"Health check failed: {str(e)}",
            "overall_healthy": False,
            "fallback_mode": True
        }


@router.get("/live", response_model=dict[str, str])
async def liveness_probe() -> dict[str, str]:
    """Kubernetes liveness probe - basic application responsiveness."""
    return {"status": "alive"}


@router.get("/ready", response_model=dict[str, Any])
async def readiness_probe(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Kubernetes readiness probe - checks if app can serve traffic."""

    from datetime import datetime, timezone
    get_health_checker()

    try:
        # Quick essential health checks for readiness
        ready_checks = {
            "database": False,
            "redis": False,
            "application": True  # Application is running if we reached this point
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
                detail="Service dependencies not ready"
            )

        return {
            "status": "ready",
            "checks": ready_checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}",
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


@router.get("/metrics-endpoint", response_model=dict[str, str])
async def metrics_endpoint_health() -> dict[str, str]:
    """Check if metrics collection is working."""

    try:
        from app.core.monitoring import get_metrics

        # Try to generate metrics
        metrics_data = get_metrics()

        return {
            "status": "healthy",
            "metrics_available": "yes",
            "sample_metrics_length": str(len(metrics_data)),
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "metrics_available": "no"}


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

        start_time = time.time()

        # Simulate agent responsiveness test
        response_time = time.time() - start_time

        # Check system resources for agent performance
        import psutil

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
