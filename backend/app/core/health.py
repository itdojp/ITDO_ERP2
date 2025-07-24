"""
Comprehensive Health Check System for ITDO ERP
Provides detailed health monitoring for all system components
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
import psutil
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_db, get_redis


class HealthStatus(str, Enum):
    """Health check status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """System component types"""

    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"
    APPLICATION = "application"
    DEPENDENCY = "dependency"


@dataclass
class HealthMetric:
    """Individual health metric"""

    name: str
    value: Union[str, int, float, bool]
    unit: Optional[str] = None
    threshold_warning: Optional[Union[int, float]] = None
    threshold_critical: Optional[Union[int, float]] = None
    description: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Result of a single health check"""

    component: str
    component_type: ComponentType
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: List[HealthMetric] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class SystemHealthReport:
    """Complete system health report"""

    overall_status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    version: str
    environment: str
    components: List[HealthCheckResult]
    summary: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """Comprehensive health checking service"""

    def __init__(self) -> dict:
        self.settings = get_settings()
        self.start_time = time.time()
        self.version = getattr(self.settings, "APP_VERSION", "1.0.0")
        self.environment = getattr(self.settings, "ENVIRONMENT", "development")

    async def check_system_health(
        self, include_detailed: bool = False
    ) -> SystemHealthReport:
        """
        Perform comprehensive system health check

        Args:
            include_detailed: Include detailed metrics and diagnostics

        Returns:
            SystemHealthReport: Complete health assessment
        """
        start_time = time.time()
        components = []

        # Core infrastructure checks
        try:
            components.append(await self._check_database())
        except Exception as e:
            components.append(
                HealthCheckResult(
                    component="database",
                    component_type=ComponentType.DATABASE,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    timestamp=datetime.now(timezone.utc),
                    error=str(e),
                )
            )

        try:
            components.append(await self._check_redis())
        except Exception as e:
            components.append(
                HealthCheckResult(
                    component="redis",
                    component_type=ComponentType.CACHE,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    timestamp=datetime.now(timezone.utc),
                    error=str(e),
                )
            )

        # System resource checks
        if include_detailed:
            components.extend(
                [
                    await self._check_memory(),
                    await self._check_cpu(),
                    await self._check_disk(),
                    await self._check_network(),
                ]
            )

        # External dependency checks
        try:
            components.append(await self._check_external_dependencies())
        except Exception as e:
            components.append(
                HealthCheckResult(
                    component="external_dependencies",
                    component_type=ComponentType.DEPENDENCY,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=0,
                    timestamp=datetime.now(timezone.utc),
                    error=str(e),
                )
            )

        # Application-specific checks
        components.append(await self._check_application_health())

        # Calculate overall status
        overall_status = self._calculate_overall_status(components)

        # Generate summary
        summary = self._generate_summary(components)

        total_time = (time.time() - start_time) * 1000

        return SystemHealthReport(
            overall_status=overall_status,
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=time.time() - self.start_time,
            version=self.version,
            environment=self.environment,
            components=components,
            summary={
                **summary,
                "total_check_time_ms": round(total_time, 2),
                "checks_performed": len(components),
            },
        )

    async def _check_database(self) -> HealthCheckResult:
        """Check PostgreSQL database health"""
        start_time = time.time()

        try:
            # Get database session
            db_gen = get_db()
            db = next(db_gen)

            # Basic connectivity test
            result = db.execute(
                text("SELECT 1 as test, version() as version")
            ).fetchone()

            # Connection pool stats
            pool_info = {}
            if hasattr(db.bind.pool, "status"):
                pool = db.bind.pool
                pool_info = {
                    "pool_size": getattr(pool, "size", 0),
                    "checked_in": getattr(pool, "checkedin", 0),
                    "checked_out": getattr(pool, "checkedout", 0),
                    "invalid": getattr(pool, "invalid", 0),
                }

            # Performance test - simple query
            perf_start = time.time()
            db.execute(
                text("SELECT COUNT(*) FROM information_schema.tables")
            ).fetchone()
            query_time_ms = (time.time() - perf_start) * 1000

            response_time_ms = (time.time() - start_time) * 1000

            # Determine status based on response time
            if response_time_ms > 1000:  # > 1 second
                status = HealthStatus.DEGRADED
                message = "Database responding slowly"
            elif response_time_ms > 500:  # > 500ms
                status = HealthStatus.DEGRADED
                message = "Database response time elevated"
            else:
                status = HealthStatus.HEALTHY
                message = "Database operating normally"

            db.close()

            return HealthCheckResult(
                component="database",
                component_type=ComponentType.DATABASE,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "version": str(result[1]) if result else "unknown",
                    "connection_pool": pool_info,
                    "query_performance_ms": round(query_time_ms, 2),
                },
                metrics=[
                    HealthMetric(
                        name="response_time",
                        value=round(response_time_ms, 2),
                        unit="ms",
                        threshold_warning=500,
                        threshold_critical=1000,
                        description="Database query response time",
                    )
                ],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="database",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="Database connection failed",
                error=str(e),
            )

    async def _check_redis(self) -> HealthCheckResult:
        """Check Redis cache health"""
        start_time = time.time()

        try:
            redis_client = get_redis()

            # Basic connectivity
            await redis_client.ping()

            # Performance test
            test_key = "healthcheck:test"
            perf_start = time.time()
            await redis_client.set(test_key, "test_value", ex=60)
            value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            cache_operation_ms = (time.time() - perf_start) * 1000

            # Get Redis info
            info = await redis_client.info()
            memory_info = await redis_client.info("memory")

            response_time_ms = (time.time() - start_time) * 1000

            # Determine status
            if response_time_ms > 100:
                status = HealthStatus.DEGRADED
                message = "Redis responding slowly"
            elif value != b"test_value":
                status = HealthStatus.DEGRADED
                message = "Redis data consistency issue"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis operating normally"

            return HealthCheckResult(
                component="redis",
                component_type=ComponentType.CACHE,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": memory_info.get("used_memory_human"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                    "cache_operation_ms": round(cache_operation_ms, 2),
                },
                metrics=[
                    HealthMetric(
                        name="response_time",
                        value=round(response_time_ms, 2),
                        unit="ms",
                        threshold_warning=50,
                        threshold_critical=100,
                        description="Redis operation response time",
                    ),
                    HealthMetric(
                        name="memory_usage",
                        value=memory_info.get("used_memory", 0),
                        unit="bytes",
                        description="Redis memory usage",
                    ),
                ],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="redis",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="Redis connection failed",
                error=str(e),
            )

    async def _check_memory(self) -> HealthCheckResult:
        """Check system memory usage"""
        start_time = time.time()

        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Determine status based on memory usage
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical memory usage"
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                message = "High memory usage"
            else:
                status = HealthStatus.HEALTHY
                message = "Memory usage normal"

            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="memory",
                component_type=ComponentType.MEMORY,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "swap_total_gb": round(swap.total / (1024**3), 2),
                    "swap_used_gb": round(swap.used / (1024**3), 2),
                },
                metrics=[
                    HealthMetric(
                        name="memory_usage_percent",
                        value=memory.percent,
                        unit="%",
                        threshold_warning=80,
                        threshold_critical=90,
                        description="System memory usage percentage",
                    ),
                    HealthMetric(
                        name="swap_usage_percent",
                        value=swap.percent,
                        unit="%",
                        threshold_warning=50,
                        threshold_critical=80,
                        description="Swap memory usage percentage",
                    ),
                ],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="memory",
                component_type=ComponentType.MEMORY,
                status=HealthStatus.UNKNOWN,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="Memory check failed",
                error=str(e),
            )

    async def _check_cpu(self) -> HealthCheckResult:
        """Check CPU usage and load"""
        start_time = time.time()

        try:
            # Get CPU usage over a short interval
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            load_avg = (
                psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
            )

            # Determine status
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical CPU usage"
            elif cpu_percent > 80:
                status = HealthStatus.DEGRADED
                message = "High CPU usage"
            else:
                status = HealthStatus.HEALTHY
                message = "CPU usage normal"

            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="cpu",
                component_type=ComponentType.CPU,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "cpu_count": cpu_count,
                    "load_avg_1min": round(load_avg[0], 2),
                    "load_avg_5min": round(load_avg[1], 2),
                    "load_avg_15min": round(load_avg[2], 2),
                },
                metrics=[
                    HealthMetric(
                        name="cpu_usage_percent",
                        value=cpu_percent,
                        unit="%",
                        threshold_warning=80,
                        threshold_critical=90,
                        description="CPU usage percentage",
                    ),
                    HealthMetric(
                        name="load_average_1min",
                        value=load_avg[0],
                        unit="load",
                        threshold_warning=cpu_count * 0.8,
                        threshold_critical=cpu_count * 1.0,
                        description="1-minute load average",
                    ),
                ],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="cpu",
                component_type=ComponentType.CPU,
                status=HealthStatus.UNKNOWN,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="CPU check failed",
                error=str(e),
            )

    async def _check_disk(self) -> HealthCheckResult:
        """Check disk space and I/O"""
        start_time = time.time()

        try:
            disk_usage = psutil.disk_usage("/")
            disk_io = psutil.disk_io_counters()

            usage_percent = (disk_usage.used / disk_usage.total) * 100

            # Determine status based on disk usage
            if usage_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = "Critical disk space"
            elif usage_percent > 85:
                status = HealthStatus.DEGRADED
                message = "Low disk space"
            else:
                status = HealthStatus.HEALTHY
                message = "Disk space normal"

            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="disk",
                component_type=ComponentType.DISK,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                },
                metrics=[
                    HealthMetric(
                        name="disk_usage_percent",
                        value=round(usage_percent, 1),
                        unit="%",
                        threshold_warning=85,
                        threshold_critical=95,
                        description="Disk space usage percentage",
                    )
                ],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="disk",
                component_type=ComponentType.DISK,
                status=HealthStatus.UNKNOWN,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="Disk check failed",
                error=str(e),
            )

    async def _check_network(self) -> HealthCheckResult:
        """Check network connectivity"""
        start_time = time.time()

        try:
            # Test external connectivity
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    response = await client.get("https://httpbin.org/get")
                    external_connectivity = response.status_code == 200
                except:
                    external_connectivity = False

            # Get network I/O stats
            net_io = psutil.net_io_counters()

            if not external_connectivity:
                status = HealthStatus.DEGRADED
                message = "External connectivity limited"
            else:
                status = HealthStatus.HEALTHY
                message = "Network connectivity normal"

            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="network",
                component_type=ComponentType.NETWORK,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "external_connectivity": external_connectivity,
                    "bytes_sent": net_io.bytes_sent if net_io else 0,
                    "bytes_recv": net_io.bytes_recv if net_io else 0,
                    "packets_sent": net_io.packets_sent if net_io else 0,
                    "packets_recv": net_io.packets_recv if net_io else 0,
                },
                metrics=[
                    HealthMetric(
                        name="external_connectivity",
                        value=external_connectivity,
                        description="External internet connectivity status",
                    )
                ],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="network",
                component_type=ComponentType.NETWORK,
                status=HealthStatus.UNKNOWN,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="Network check failed",
                error=str(e),
            )

    async def _check_external_dependencies(self) -> HealthCheckResult:
        """Check external service dependencies"""
        start_time = time.time()

        try:
            dependencies_status = []

            # Test Keycloak if configured
            if hasattr(self.settings, "KEYCLOAK_URL") and self.settings.KEYCLOAK_URL:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(
                            f"{self.settings.KEYCLOAK_URL}/auth/realms/master"
                        )
                        keycloak_ok = response.status_code == 200
                        dependencies_status.append(("keycloak", keycloak_ok))
                except:
                    dependencies_status.append(("keycloak", False))

            # Add other external dependencies here
            # Example: payment gateway, email service, etc.

            failed_dependencies = [
                name for name, status in dependencies_status if not status
            ]

            if failed_dependencies:
                status = HealthStatus.DEGRADED
                message = (
                    f"Some dependencies unavailable: {', '.join(failed_dependencies)}"
                )
            elif not dependencies_status:
                status = HealthStatus.HEALTHY
                message = "No external dependencies configured"
            else:
                status = HealthStatus.HEALTHY
                message = "All dependencies available"

            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="external_dependencies",
                component_type=ComponentType.DEPENDENCY,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "dependencies": dict(dependencies_status),
                    "total_dependencies": len(dependencies_status),
                    "failed_dependencies": failed_dependencies,
                },
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="external_dependencies",
                component_type=ComponentType.DEPENDENCY,
                status=HealthStatus.UNKNOWN,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="Dependencies check failed",
                error=str(e),
            )

    async def _check_application_health(self) -> HealthCheckResult:
        """Check application-specific health metrics"""
        start_time = time.time()

        try:
            # Check feature flags service
            feature_flags_ok = True
            try:
                from app.core.feature_flags import get_feature_flag_service

                ff_service = get_feature_flag_service()
                await ff_service.list_flags()  # Simple test call
            except:
                feature_flags_ok = False

            # Add other application-specific checks
            app_checks = {
                "feature_flags": feature_flags_ok,
                "startup_complete": True,  # Could check if all initialization is done
            }

            failed_checks = [name for name, status in app_checks.items() if not status]

            if failed_checks:
                status = HealthStatus.DEGRADED
                message = f"Application issues: {', '.join(failed_checks)}"
            else:
                status = HealthStatus.HEALTHY
                message = "Application running normally"

            response_time_ms = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="application",
                component_type=ComponentType.APPLICATION,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message=message,
                details={
                    "checks": app_checks,
                    "uptime_seconds": time.time() - self.start_time,
                    "version": self.version,
                    "environment": self.environment,
                },
                metrics=[
                    HealthMetric(
                        name="uptime_seconds",
                        value=round(time.time() - self.start_time, 1),
                        unit="seconds",
                        description="Application uptime",
                    )
                ],
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="application",
                component_type=ComponentType.APPLICATION,
                status=HealthStatus.UNKNOWN,
                response_time_ms=round(response_time_ms, 2),
                timestamp=datetime.now(timezone.utc),
                message="Application health check failed",
                error=str(e),
            )

    def _calculate_overall_status(
        self, components: List[HealthCheckResult]
    ) -> HealthStatus:
        """Calculate overall system status from component statuses"""
        if not components:
            return HealthStatus.UNKNOWN

        # Count status types
        status_counts = {status: 0 for status in HealthStatus}
        for component in components:
            status_counts[component.status] += 1

        # Determine overall status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.UNKNOWN] > 0:
            return HealthStatus.DEGRADED  # Treat unknown as degraded
        else:
            return HealthStatus.HEALTHY

    def _generate_summary(self, components: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate health check summary statistics"""
        if not components:
            return {}

        status_counts = {status.value: 0 for status in HealthStatus}
        total_response_time = 0
        component_types = {}

        for component in components:
            status_counts[component.status.value] += 1
            total_response_time += component.response_time_ms

            comp_type = component.component_type.value
            if comp_type not in component_types:
                component_types[comp_type] = []
            component_types[comp_type].append(component.status.value)

        return {
            "status_distribution": status_counts,
            "average_response_time_ms": round(total_response_time / len(components), 2),
            "component_types": component_types,
            "critical_issues": [
                c.component for c in components if c.status == HealthStatus.UNHEALTHY
            ],
            "warnings": [
                c.component for c in components if c.status == HealthStatus.DEGRADED
            ],
        }


# Singleton instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get or create health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
