"""Mobile SDK Performance Optimization & Benchmarking - CC02 v72.0 Day 17."""

from __future__ import annotations

import asyncio
import gc
import json
import resource
import statistics
import time
import tracemalloc
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Tuple

import psutil

from .mobile_sdk_core import MobileERPSDK


class MetricType(str, Enum):
    """Performance metric types."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    STORAGE = "storage"
    BATTERY = "battery"


class BenchmarkLevel(str, Enum):
    """Benchmark complexity levels."""

    MICRO = "micro"  # Individual function calls
    COMPONENT = "component"  # SDK module performance
    INTEGRATION = "integration"  # End-to-end scenarios
    LOAD = "load"  # High load scenarios


@dataclass
class PerformanceMetric:
    """Performance metric data point."""

    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any]
    tags: List[str]


@dataclass
class BenchmarkResult:
    """Benchmark execution result."""

    benchmark_id: str
    benchmark_name: str
    level: BenchmarkLevel
    start_time: datetime
    end_time: datetime
    duration_ms: float

    metrics: Dict[str, List[PerformanceMetric]]
    statistics: Dict[str, Dict[str, float]]
    passed: bool
    thresholds: Dict[str, float]
    violations: List[str]

    system_info: Dict[str, Any]
    configuration: Dict[str, Any]


class PerformanceMonitor:
    """Real-time performance monitoring."""

    def __init__(self, sample_interval: float = 1.0, history_size: int = 1000) -> dict:
        self.sample_interval = sample_interval
        self.history_size = history_size

        # Performance data storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.active_monitors: Dict[str, asyncio.Task] = {}

        # System monitoring
        self.process = psutil.Process()
        self.start_time = time.time()

        # Memory tracking
        self.memory_snapshots: List[Tuple[float, Dict[str, Any]]] = []
        self.peak_memory_usage = 0

        # Network tracking
        self.network_requests: List[Dict[str, Any]] = []
        self.total_bytes_sent = 0
        self.total_bytes_received = 0

    async def start_monitoring(self, metrics: List[MetricType]) -> None:
        """Start monitoring specified metrics."""
        for metric_type in metrics:
            if metric_type.value not in self.active_monitors:
                monitor_task = asyncio.create_task(self._monitor_metric(metric_type))
                self.active_monitors[metric_type.value] = monitor_task

    async def stop_monitoring(self) -> None:
        """Stop all active monitoring."""
        for task in self.active_monitors.values():
            task.cancel()

        # Wait for tasks to complete
        if self.active_monitors:
            await asyncio.gather(*self.active_monitors.values(), return_exceptions=True)

        self.active_monitors.clear()

    async def _monitor_metric(self, metric_type: MetricType) -> None:
        """Monitor specific metric type continuously."""
        try:
            while True:
                timestamp = datetime.now()

                if metric_type == MetricType.MEMORY:
                    memory_info = self.process.memory_info()
                    memory_percent = self.process.memory_percent()

                    metric = PerformanceMetric(
                        name="memory_usage",
                        metric_type=MetricType.MEMORY,
                        value=memory_info.rss,
                        unit="bytes",
                        timestamp=timestamp,
                        context={
                            "rss": memory_info.rss,
                            "vms": memory_info.vms,
                            "percent": memory_percent,
                        },
                        tags=["system", "memory"],
                    )

                    # Track peak memory usage
                    self.peak_memory_usage = max(
                        self.peak_memory_usage, memory_info.rss
                    )

                elif metric_type == MetricType.CPU:
                    cpu_percent = self.process.cpu_percent()
                    cpu_times = self.process.cpu_times()

                    metric = PerformanceMetric(
                        name="cpu_usage",
                        metric_type=MetricType.CPU,
                        value=cpu_percent,
                        unit="percent",
                        timestamp=timestamp,
                        context={
                            "percent": cpu_percent,
                            "user_time": cpu_times.user,
                            "system_time": cpu_times.system,
                        },
                        tags=["system", "cpu"],
                    )

                elif metric_type == MetricType.NETWORK:
                    # Network I/O monitoring would be implemented here
                    # For now, we'll track connection counts
                    connections = len(self.process.connections())

                    metric = PerformanceMetric(
                        name="network_connections",
                        metric_type=MetricType.NETWORK,
                        value=connections,
                        unit="count",
                        timestamp=timestamp,
                        context={"active_connections": connections},
                        tags=["system", "network"],
                    )

                else:
                    # Skip unsupported metrics
                    continue

                self.metrics[metric_type.value].append(metric)
                await asyncio.sleep(self.sample_interval)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Performance Monitor] Error monitoring {metric_type}: {e}")

    def record_network_request(
        self,
        method: str,
        url: str,
        bytes_sent: int,
        bytes_received: int,
        duration_ms: float,
        status_code: int,
    ) -> None:
        """Record network request metrics."""
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "url": url,
            "bytes_sent": bytes_sent,
            "bytes_received": bytes_received,
            "duration_ms": duration_ms,
            "status_code": status_code,
        }

        self.network_requests.append(request_data)
        self.total_bytes_sent += bytes_sent
        self.total_bytes_received += bytes_received

    def take_memory_snapshot(self, label: str) -> Dict[str, Any]:
        """Take memory snapshot with label."""
        memory_info = self.process.memory_info()
        snapshot = {
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "rss": memory_info.rss,
            "vms": memory_info.vms,
            "percent": self.process.memory_percent(),
        }

        self.memory_snapshots.append((time.time(), snapshot))
        return snapshot

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        current_time = time.time()
        uptime = current_time - self.start_time

        # Calculate averages for recent metrics
        recent_metrics = {}
        for metric_type, metric_list in self.metrics.items():
            if metric_list:
                recent_values = [
                    m.value for m in list(metric_list)[-10:]
                ]  # Last 10 samples
                recent_metrics[metric_type] = {
                    "current": recent_values[-1] if recent_values else 0,
                    "average": statistics.mean(recent_values) if recent_values else 0,
                    "min": min(recent_values) if recent_values else 0,
                    "max": max(recent_values) if recent_values else 0,
                }

        return {
            "uptime_seconds": uptime,
            "peak_memory_bytes": self.peak_memory_usage,
            "total_network_requests": len(self.network_requests),
            "total_bytes_sent": self.total_bytes_sent,
            "total_bytes_received": self.total_bytes_received,
            "metrics": recent_metrics,
            "snapshots_count": len(self.memory_snapshots),
        }


class PerformanceOptimizer:
    """Performance optimization utilities."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.optimizations_applied: List[str] = []
        self.performance_hints: List[Dict[str, Any]] = []

    async def analyze_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics and provide recommendations."""
        analysis = {
            "overall_score": 0,
            "recommendations": [],
            "optimizations": [],
            "warnings": [],
        }

        # Memory analysis
        if "memory" in metrics.get("metrics", {}):
            memory_data = metrics["metrics"]["memory"]
            peak_memory_mb = metrics["peak_memory_bytes"] / (1024 * 1024)

            if peak_memory_mb > 500:  # 500MB threshold
                analysis["warnings"].append(
                    {
                        "type": "high_memory_usage",
                        "message": f"Peak memory usage is high: {peak_memory_mb:.1f}MB",
                        "recommendation": "Consider implementing memory optimization strategies",
                    }
                )
                analysis["optimizations"].append("memory_optimization")

            if memory_data["max"] - memory_data["min"] > memory_data["average"] * 0.5:
                analysis["recommendations"].append(
                    {
                        "type": "memory_volatility",
                        "message": "Memory usage is highly variable",
                        "action": "Implement memory pooling or caching strategies",
                    }
                )

        # Network analysis
        network_requests = metrics.get("total_network_requests", 0)
        if network_requests > 0:
            avg_request_size = metrics.get("total_bytes_sent", 0) / network_requests

            if avg_request_size > 10 * 1024:  # 10KB threshold
                analysis["recommendations"].append(
                    {
                        "type": "large_requests",
                        "message": f"Average request size is large: {avg_request_size / 1024:.1f}KB",
                        "action": "Consider request payload compression or pagination",
                    }
                )

        # CPU analysis (if available)
        if "cpu" in metrics.get("metrics", {}):
            cpu_data = metrics["metrics"]["cpu"]
            if cpu_data["average"] > 80:  # 80% threshold
                analysis["warnings"].append(
                    {
                        "type": "high_cpu_usage",
                        "message": f"Average CPU usage is high: {cpu_data['average']:.1f}%",
                        "recommendation": "Profile CPU-intensive operations",
                    }
                )

        # Calculate overall score
        score = 100
        score -= len(analysis["warnings"]) * 20
        score -= len(analysis["recommendations"]) * 10
        analysis["overall_score"] = max(0, score)

        return analysis

    async def apply_optimization(self, optimization_type: str) -> bool:
        """Apply specific optimization."""
        try:
            if optimization_type == "memory_optimization":
                await self._apply_memory_optimization()
            elif optimization_type == "network_optimization":
                await self._apply_network_optimization()
            elif optimization_type == "cache_optimization":
                await self._apply_cache_optimization()
            else:
                return False

            self.optimizations_applied.append(optimization_type)
            return True

        except Exception as e:
            print(f"[Performance Optimizer] Failed to apply {optimization_type}: {e}")
            return False

    async def _apply_memory_optimization(self) -> None:
        """Apply memory optimization strategies."""
        # Force garbage collection
        gc.collect()

        # Clear caches if available
        if hasattr(self.sdk.http_client, "cache"):
            await self.sdk.http_client.cache.clear()

        # Set smaller cache sizes
        if hasattr(self.sdk.http_client, "cache"):
            self.sdk.http_client.cache.default_ttl = min(
                self.sdk.http_client.cache.default_ttl,
                60,  # 1 minute max
            )

    async def _apply_network_optimization(self) -> None:
        """Apply network optimization strategies."""
        # Enable request compression if not already enabled
        if hasattr(self.sdk.config, "compression_enabled"):
            self.sdk.config.compression_enabled = True

        # Reduce timeout for faster failures
        self.sdk.config.timeout_seconds = min(self.sdk.config.timeout_seconds, 15)

        # Enable more aggressive caching
        self.sdk.config.cache_enabled = True
        self.sdk.config.cache_ttl_seconds = max(self.sdk.config.cache_ttl_seconds, 300)

    async def _apply_cache_optimization(self) -> None:
        """Apply cache optimization strategies."""
        if hasattr(self.sdk.http_client, "cache"):
            # Increase cache size for better hit rates
            # Implementation would depend on cache structure
            pass


class BenchmarkSuite:
    """Comprehensive benchmarking suite."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.monitor = PerformanceMonitor()
        self.optimizer = PerformanceOptimizer(sdk)
        self.results: List[BenchmarkResult] = []

        # Benchmark thresholds
        self.thresholds = {
            "authentication_latency_ms": 2000,
            "api_call_latency_ms": 1000,
            "sync_throughput_records_per_sec": 100,
            "memory_usage_mb": 200,
            "cpu_usage_percent": 50,
        }

    @asynccontextmanager
    async def benchmark_context(
        self, benchmark_id: str, benchmark_name: str, level: BenchmarkLevel
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Context manager for benchmark execution."""
        start_time = datetime.now()

        # Start performance monitoring
        await self.monitor.start_monitoring(
            [MetricType.MEMORY, MetricType.CPU, MetricType.NETWORK]
        )

        # Enable memory tracing
        tracemalloc.start()

        # Take initial memory snapshot
        self.monitor.take_memory_snapshot(f"{benchmark_id}_start")

        context = {
            "benchmark_id": benchmark_id,
            "start_time": start_time,
            "metrics": [],
            "violations": [],
        }

        try:
            yield context

        finally:
            # Take final memory snapshot
            self.monitor.take_memory_snapshot(f"{benchmark_id}_end")

            # Stop memory tracing
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Stop monitoring
            await self.monitor.stop_monitoring()

            # Calculate results
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Collect system info
            system_info = {
                "python_version": f"{resource.struct_time}",
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "platform": "mobile_sdk",
            }

            # Process metrics and check thresholds
            violations = []
            statistics_data = {}

            # Check latency thresholds
            if duration_ms > self.thresholds.get(
                f"{benchmark_id}_latency_ms", float("inf")
            ):
                violations.append(f"Latency exceeded threshold: {duration_ms:.1f}ms")

            # Check memory thresholds
            memory_usage_mb = peak / (1024 * 1024)
            if memory_usage_mb > self.thresholds.get("memory_usage_mb", float("inf")):
                violations.append(
                    f"Memory usage exceeded threshold: {memory_usage_mb:.1f}MB"
                )

            # Create benchmark result
            result = BenchmarkResult(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                level=level,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                metrics={
                    "memory": [
                        PerformanceMetric(
                            name="peak_memory",
                            metric_type=MetricType.MEMORY,
                            value=peak,
                            unit="bytes",
                            timestamp=end_time,
                            context={"current": current, "peak": peak},
                            tags=["benchmark", "memory"],
                        )
                    ]
                },
                statistics=statistics_data,
                passed=len(violations) == 0,
                thresholds=self.thresholds,
                violations=violations,
                system_info=system_info,
                configuration=self.sdk.config.dict()
                if hasattr(self.sdk.config, "dict")
                else {},
            )

            self.results.append(result)

    async def benchmark_authentication(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark authentication performance."""
        async with self.benchmark_context(
            "authentication", "Authentication Performance", BenchmarkLevel.COMPONENT
        ) as ctx:
            auth_times = []

            for i in range(iterations):
                start = time.time()

                try:
                    # Test credential authentication
                    await self.sdk.authenticate(
                        username="benchmark_user", password="benchmark_password"
                    )

                    # Logout to reset state
                    await self.sdk.logout()

                    auth_time = (time.time() - start) * 1000
                    auth_times.append(auth_time)

                except Exception as e:
                    print(f"[Benchmark] Authentication failed in iteration {i}: {e}")
                    continue

            if auth_times:
                ctx["metrics"].extend(
                    [
                        PerformanceMetric(
                            name="auth_latency_avg",
                            metric_type=MetricType.LATENCY,
                            value=statistics.mean(auth_times),
                            unit="ms",
                            timestamp=datetime.now(),
                            context={
                                "min": min(auth_times),
                                "max": max(auth_times),
                                "median": statistics.median(auth_times),
                                "iterations": len(auth_times),
                            },
                            tags=["authentication", "latency"],
                        )
                    ]
                )

        return self.results[-1]

    async def benchmark_api_calls(self, iterations: int = 200) -> BenchmarkResult:
        """Benchmark API call performance."""
        async with self.benchmark_context(
            "api_calls", "API Call Performance", BenchmarkLevel.COMPONENT
        ) as ctx:
            # Authenticate first
            await self.sdk.authenticate("benchmark_user", "benchmark_password")

            api_times = []
            endpoints = [
                "auth/profile",
                "organization/settings",
                "data/sync/status",
                "analytics/summary",
            ]

            for i in range(iterations):
                endpoint = endpoints[i % len(endpoints)]
                start = time.time()

                try:
                    response = await self.sdk.http_client.get(endpoint)
                    api_time = (time.time() - start) * 1000
                    api_times.append(api_time)

                    # Record network request
                    self.monitor.record_network_request(
                        method="GET",
                        url=endpoint,
                        bytes_sent=100,  # Estimated
                        bytes_received=len(str(response)),
                        duration_ms=api_time,
                        status_code=response.get("status", 200),
                    )

                except Exception as e:
                    print(f"[Benchmark] API call failed in iteration {i}: {e}")
                    continue

            if api_times:
                throughput = len(api_times) / (
                    sum(api_times) / 1000
                )  # Requests per second

                ctx["metrics"].extend(
                    [
                        PerformanceMetric(
                            name="api_latency_avg",
                            metric_type=MetricType.LATENCY,
                            value=statistics.mean(api_times),
                            unit="ms",
                            timestamp=datetime.now(),
                            context={
                                "min": min(api_times),
                                "max": max(api_times),
                                "median": statistics.median(api_times),
                                "p95": sorted(api_times)[int(len(api_times) * 0.95)],
                                "iterations": len(api_times),
                            },
                            tags=["api", "latency"],
                        ),
                        PerformanceMetric(
                            name="api_throughput",
                            metric_type=MetricType.THROUGHPUT,
                            value=throughput,
                            unit="requests/sec",
                            timestamp=datetime.now(),
                            context={"total_requests": len(api_times)},
                            tags=["api", "throughput"],
                        ),
                    ]
                )

        return self.results[-1]

    async def benchmark_data_sync(self, record_count: int = 1000) -> BenchmarkResult:
        """Benchmark data synchronization performance."""
        async with self.benchmark_context(
            "data_sync", "Data Synchronization Performance", BenchmarkLevel.INTEGRATION
        ) as ctx:
            # Authenticate first
            await self.sdk.authenticate("benchmark_user", "benchmark_password")

            # Get sync module
            sync_module = self.sdk.get_module("sync")
            if not sync_module:
                print("[Benchmark] Sync module not available")
                return self.results[-1]

            try:
                start = time.time()

                # Initiate sync
                sync_session = await sync_module.sync_now(
                    entity_types=["users", "projects", "tasks"], force_full_sync=True
                )

                # Wait for sync completion (simplified)
                await asyncio.sleep(
                    5
                )  # In real implementation, would wait for actual completion

                sync_time = (time.time() - start) * 1000
                throughput = record_count / (sync_time / 1000)  # Records per second

                ctx["metrics"].extend(
                    [
                        PerformanceMetric(
                            name="sync_duration",
                            metric_type=MetricType.LATENCY,
                            value=sync_time,
                            unit="ms",
                            timestamp=datetime.now(),
                            context={
                                "record_count": record_count,
                                "session_id": sync_session.session_id
                                if hasattr(sync_session, "session_id")
                                else "unknown",
                            },
                            tags=["sync", "latency"],
                        ),
                        PerformanceMetric(
                            name="sync_throughput",
                            metric_type=MetricType.THROUGHPUT,
                            value=throughput,
                            unit="records/sec",
                            timestamp=datetime.now(),
                            context={"record_count": record_count},
                            tags=["sync", "throughput"],
                        ),
                    ]
                )

            except Exception as e:
                print(f"[Benchmark] Data sync failed: {e}")

        return self.results[-1]

    async def benchmark_memory_usage(self, operations: int = 1000) -> BenchmarkResult:
        """Benchmark memory usage patterns."""
        async with self.benchmark_context(
            "memory_usage", "Memory Usage Patterns", BenchmarkLevel.LOAD
        ) as ctx:
            # Authenticate first
            await self.sdk.authenticate("benchmark_user", "benchmark_password")

            memory_readings = []

            for i in range(operations):
                # Perform various SDK operations
                if i % 10 == 0:
                    # API calls
                    try:
                        await self.sdk.http_client.get("auth/profile")
                    except:
                        pass

                if i % 50 == 0:
                    # Cache operations
                    if hasattr(self.sdk.http_client, "cache"):
                        await self.sdk.http_client.cache.set(
                            f"test_key_{i}", {"data": "test"}
                        )

                if i % 100 == 0:
                    # Take memory reading
                    memory_info = psutil.Process().memory_info()
                    memory_readings.append(memory_info.rss)

                # Small delay to allow monitoring
                if i % 100 == 0:
                    await asyncio.sleep(0.01)

            if memory_readings:
                memory_growth = memory_readings[-1] - memory_readings[0]

                ctx["metrics"].append(
                    PerformanceMetric(
                        name="memory_growth",
                        metric_type=MetricType.MEMORY,
                        value=memory_growth,
                        unit="bytes",
                        timestamp=datetime.now(),
                        context={
                            "initial": memory_readings[0],
                            "final": memory_readings[-1],
                            "peak": max(memory_readings),
                            "operations": operations,
                        },
                        tags=["memory", "growth"],
                    )
                )

        return self.results[-1]

    async def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Run complete benchmark suite."""
        print("[Benchmark] Starting full benchmark suite...")

        suite_start = datetime.now()

        # Run all benchmarks
        await self.benchmark_authentication(50)
        await self.benchmark_api_calls(100)
        await self.benchmark_data_sync(500)
        await self.benchmark_memory_usage(500)

        suite_end = datetime.now()
        suite_duration = (suite_end - suite_start).total_seconds()

        # Analyze overall performance
        performance_metrics = self.monitor.get_current_metrics()
        analysis = await self.optimizer.analyze_performance(performance_metrics)

        # Generate summary report
        summary = {
            "suite_duration_seconds": suite_duration,
            "total_benchmarks": len(self.results),
            "benchmarks_passed": len([r for r in self.results if r.passed]),
            "benchmarks_failed": len([r for r in self.results if not r.passed]),
            "overall_performance_score": analysis["overall_score"],
            "recommendations": analysis["recommendations"],
            "warnings": analysis["warnings"],
            "system_metrics": performance_metrics,
            "benchmark_results": [
                {
                    "id": result.benchmark_id,
                    "name": result.benchmark_name,
                    "passed": result.passed,
                    "duration_ms": result.duration_ms,
                    "violations": result.violations,
                }
                for result in self.results
            ],
            "generated_at": datetime.now().isoformat(),
        }

        print(f"[Benchmark] Suite completed in {suite_duration:.1f}s")
        print(f"[Benchmark] Performance Score: {analysis['overall_score']}/100")

        return summary

    def export_results(self, filepath: str) -> None:
        """Export benchmark results to JSON file."""
        export_data = {
            "benchmark_suite_version": "1.0.0",
            "export_timestamp": datetime.now().isoformat(),
            "thresholds": self.thresholds,
            "results": [
                {
                    "benchmark_id": result.benchmark_id,
                    "benchmark_name": result.benchmark_name,
                    "level": result.level.value,
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "duration_ms": result.duration_ms,
                    "passed": result.passed,
                    "violations": result.violations,
                    "metrics": {
                        metric_type: [
                            {
                                "name": metric.name,
                                "value": metric.value,
                                "unit": metric.unit,
                                "timestamp": metric.timestamp.isoformat(),
                                "context": metric.context,
                                "tags": metric.tags,
                            }
                            for metric in metrics
                        ]
                        for metric_type, metrics in result.metrics.items()
                    },
                    "system_info": result.system_info,
                }
                for result in self.results
            ],
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)


class PerformanceProfiler:
    """Advanced performance profiling utilities."""

    def __init__(self) -> dict:
        self.active_profiles: Dict[str, Any] = {}
        self.call_stack: List[Dict[str, Any]] = []

    @asynccontextmanager
    async def profile_async_function(
        self, function_name: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Profile async function execution."""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss

        profile_data = {
            "function_name": function_name,
            "start_time": start_time,
            "call_depth": len(self.call_stack),
        }

        self.call_stack.append(profile_data)

        try:
            yield profile_data
        finally:
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss

            profile_data.update(
                {
                    "end_time": end_time,
                    "duration_ms": (end_time - start_time) * 1000,
                    "memory_delta": end_memory - start_memory,
                }
            )

            self.call_stack.pop()

    def get_profiling_summary(self) -> Dict[str, Any]:
        """Get profiling summary."""
        return {
            "active_profiles": len(self.active_profiles),
            "call_stack_depth": len(self.call_stack),
            "current_calls": [call["function_name"] for call in self.call_stack],
        }
