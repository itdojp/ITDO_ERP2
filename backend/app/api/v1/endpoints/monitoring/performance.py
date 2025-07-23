"""Performance monitoring API endpoints."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import List

import psutil
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.schemas.monitoring.performance import (
    PerformanceMetric,
    PerformanceSummary,
    ResourceUsage,
    SystemHealth,
)

router = APIRouter()

# In-memory metrics storage (in production, use time-series DB)
performance_metrics: List[PerformanceMetric] = []
resource_metrics: List[ResourceUsage] = []


@router.post("/metrics")
async def record_performance_metric(
    metric: PerformanceMetric,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> dict:
    """Record a performance metric (admin only)."""
    # Store metric
    performance_metrics.append(metric)

    # Keep only last 24 hours of metrics
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    performance_metrics[:] = [
        m for m in performance_metrics if m.timestamp > cutoff_time
    ]

    return {"status": "recorded", "total_metrics": len(performance_metrics)}


@router.get("/summary", response_model=List[PerformanceSummary])
async def get_performance_summary(
    hours: int = Query(1, ge=1, le=24),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[PerformanceSummary]:
    """Get performance summary for all endpoints."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    recent_metrics = [m for m in performance_metrics if m.timestamp > cutoff_time]

    # Group by endpoint and method
    endpoint_metrics = {}
    for metric in recent_metrics:
        key = f"{metric.method} {metric.endpoint}"
        if key not in endpoint_metrics:
            endpoint_metrics[key] = []
        endpoint_metrics[key].append(metric)

    summaries = []
    for key, metrics in endpoint_metrics.items():
        method, endpoint = key.split(" ", 1)

        response_times = [m.response_time_ms for m in metrics]
        response_times.sort()

        errors = sum(1 for m in metrics if m.status_code >= 400)
        total = len(metrics)

        # Calculate percentiles
        def percentile(data, p):
            if not data:
                return 0
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] * (1 - c) + data[f + 1] * c
            return data[f]

        time_range = (
            max(m.timestamp for m in metrics) - min(m.timestamp for m in metrics)
        ).total_seconds()
        rps = total / time_range if time_range > 0 else 0

        summary = PerformanceSummary(
            endpoint=endpoint,
            method=method,
            total_requests=total,
            avg_response_time_ms=sum(response_times) / total if total > 0 else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            p50_response_time_ms=percentile(response_times, 0.5),
            p90_response_time_ms=percentile(response_times, 0.9),
            p95_response_time_ms=percentile(response_times, 0.95),
            p99_response_time_ms=percentile(response_times, 0.99),
            error_rate=errors / total if total > 0 else 0,
            requests_per_second=rps,
            time_period={
                "start": min(m.timestamp for m in metrics),
                "end": max(m.timestamp for m in metrics),
            },
        )
        summaries.append(summary)

    return summaries


@router.get("/health", response_model=SystemHealth)
async def get_system_health(db: AsyncSession = Depends(deps.get_db)) -> SystemHealth:
    """Get current system health status."""
    # CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Database pool status
    db_pool = db.bind.pool  # type: ignore
    db_pool_size = db_pool.size()
    db_pool_available = db_pool.size() - db_pool.checked_out()

    # Redis connection check
    redis_connected = True  # Simplified for now
    try:
        # In a real implementation, check Redis connection here
        pass
    except Exception:
        redis_connected = False

    # Determine overall status
    status = "healthy"
    if cpu_percent > 80 or memory.percent > 80:
        status = "degraded"
    if cpu_percent > 95 or memory.percent > 95 or not redis_connected:
        status = "unhealthy"

    # Individual health checks
    checks = {
        "database": {
            "status": "healthy" if db_pool_available > 0 else "unhealthy",
            "pool_size": db_pool_size,
            "available_connections": db_pool_available,
        },
        "redis": {
            "status": "healthy" if redis_connected else "unhealthy",
            "connected": redis_connected,
        },
        "disk": {
            "status": "healthy" if disk.percent < 90 else "degraded",
            "usage_percent": disk.percent,
        },
    }

    # Calculate uptime
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    return SystemHealth(
        status=status,
        uptime_seconds=uptime_seconds,
        cpu_usage_percent=cpu_percent,
        memory_usage_percent=memory.percent,
        disk_usage_percent=disk.percent,
        active_connections=len(psutil.net_connections()),
        database_pool_size=db_pool_size,
        database_pool_available=db_pool_available,
        redis_connected=redis_connected,
        checks=checks,
    )


@router.get("/resources", response_model=List[ResourceUsage])
async def get_resource_usage(
    hours: int = Query(1, ge=1, le=24),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[ResourceUsage]:
    """Get resource usage history."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    recent_usage = [m for m in resource_metrics if m.timestamp > cutoff_time]
    return recent_usage


@router.post("/resources/collect")
async def collect_resource_metrics(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> dict:
    """Collect current resource metrics (admin only)."""
    # Collect metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk_io = psutil.disk_io_counters()
    net_io = psutil.net_io_counters()

    metric = ResourceUsage(
        timestamp=datetime.utcnow(),
        cpu_percent=cpu_percent,
        memory_mb=memory.used / 1024 / 1024,
        disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
        disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
        network_in_mb=net_io.bytes_recv / 1024 / 1024 if net_io else 0,
        network_out_mb=net_io.bytes_sent / 1024 / 1024 if net_io else 0,
        active_requests=len(
            [
                m
                for m in performance_metrics
                if (datetime.utcnow() - m.timestamp).total_seconds() < 60
            ]
        ),
        queued_requests=0,  # Would need actual queue monitoring
    )

    resource_metrics.append(metric)

    # Keep only last 24 hours
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    resource_metrics[:] = [m for m in resource_metrics if m.timestamp > cutoff_time]

    return {"status": "collected", "total_metrics": len(resource_metrics)}
