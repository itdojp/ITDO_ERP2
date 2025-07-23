"""Performance monitoring schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PerformanceMetric(BaseModel):
    """Individual performance metric."""

    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    timestamp: datetime
    user_id: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    error: Optional[str] = None


class PerformanceSummary(BaseModel):
    """Performance summary for an endpoint."""

    endpoint: str
    method: str
    total_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p90_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    requests_per_second: float
    time_period: Dict[str, datetime]


class SystemHealth(BaseModel):
    """System health status."""

    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    uptime_seconds: float
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    database_pool_size: int
    database_pool_available: int
    redis_connected: bool
    checks: Dict[str, Dict[str, Any]]


class ResourceUsage(BaseModel):
    """Resource usage over time."""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_in_mb: float
    network_out_mb: float
    active_requests: int
    queued_requests: int
