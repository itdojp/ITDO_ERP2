"""
CC02 v77.0 Day 22: Performance Testing & Benchmarking Module
Enterprise-grade performance testing framework with comprehensive benchmarking and analysis.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import numpy as np
import psutil

from app.mobile_sdk.core import MobileERPSDK

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Performance test types."""

    LOAD_TEST = "load_test"
    STRESS_TEST = "stress_test"
    SPIKE_TEST = "spike_test"
    VOLUME_TEST = "volume_test"
    ENDURANCE_TEST = "endurance_test"
    SCALABILITY_TEST = "scalability_test"
    BASELINE_TEST = "baseline_test"


class TestStatus(Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MetricType(Enum):
    """Performance metric types."""

    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    NETWORK_IO = "network_io"
    DISK_IO = "disk_io"
    CONCURRENT_USERS = "concurrent_users"


@dataclass
class TestConfiguration:
    """Performance test configuration."""

    test_id: str
    test_type: TestType
    test_name: str
    target_endpoint: str
    concurrent_users: int
    test_duration_seconds: int
    ramp_up_time_seconds: int
    request_rate_per_second: Optional[int] = None
    payload_size_bytes: int = 1024
    headers: Dict[str, str] = field(default_factory=dict)
    custom_parameters: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, float] = field(default_factory=dict)


@dataclass
class TestResult:
    """Individual test request result."""

    timestamp: datetime
    response_time_ms: float
    status_code: int
    error_message: Optional[str] = None
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    success: bool = True


@dataclass
class BenchmarkMetrics:
    """Comprehensive benchmark metrics."""

    test_id: str
    test_type: TestType
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int

    # Response time metrics
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float

    # Throughput metrics
    requests_per_second: float
    bytes_per_second: float

    # Error metrics
    error_rate_percent: float
    timeout_count: int

    # Resource metrics
    avg_cpu_usage_percent: float
    avg_memory_usage_mb: float
    peak_cpu_usage_percent: float
    peak_memory_usage_mb: float

    # Additional metrics
    concurrent_users: int
    test_duration_seconds: float


class PerformanceTestExecutor:
    """Executes performance tests with various patterns."""

    def __init__(self, max_workers: int = 100) -> dict:
        self.max_workers = max_workers
        self.active_tests: Dict[str, TestConfiguration] = {}
        self.test_results: Dict[str, List[TestResult]] = {}
        self.system_metrics: Dict[str, List[Dict[str, float]]] = {}

    async def execute_test(self, config: TestConfiguration) -> BenchmarkMetrics:
        """Execute performance test based on configuration."""
        logger.info(f"Starting {config.test_type.value} test: {config.test_name}")

        self.active_tests[config.test_id] = config
        self.test_results[config.test_id] = []
        self.system_metrics[config.test_id] = []

        start_time = datetime.now()

        try:
            # Start system monitoring
            monitor_task = asyncio.create_task(
                self._monitor_system_resources(config.test_id)
            )

            # Execute test based on type
            if config.test_type == TestType.LOAD_TEST:
                await self._execute_load_test(config)
            elif config.test_type == TestType.STRESS_TEST:
                await self._execute_stress_test(config)
            elif config.test_type == TestType.SPIKE_TEST:
                await self._execute_spike_test(config)
            elif config.test_type == TestType.ENDURANCE_TEST:
                await self._execute_endurance_test(config)
            elif config.test_type == TestType.SCALABILITY_TEST:
                await self._execute_scalability_test(config)
            else:
                await self._execute_basic_test(config)

            # Stop monitoring
            monitor_task.cancel()

            end_time = datetime.now()

            # Calculate metrics
            metrics = self._calculate_benchmark_metrics(config, start_time, end_time)

            # Log results
            logger.info(
                f"Test {config.test_name} completed: "
                f"RPS={metrics.requests_per_second:.1f}, "
                f"Avg RT={metrics.avg_response_time_ms:.1f}ms, "
                f"Error Rate={metrics.error_rate_percent:.2f}%"
            )

            return metrics

        except Exception as e:
            logger.error(f"Test {config.test_name} failed: {e}")
            raise
        finally:
            # Cleanup
            if config.test_id in self.active_tests:
                del self.active_tests[config.test_id]

    async def _execute_load_test(self, config: TestConfiguration) -> dict:
        """Execute load test with sustained load."""
        # Gradual ramp-up
        await self._ramp_up_users(config)

        # Sustained load phase
        await self._sustained_load_phase(config)

    async def _execute_stress_test(self, config: TestConfiguration) -> dict:
        """Execute stress test with increasing load until failure."""
        current_users = config.concurrent_users
        max_users = current_users * 3  # Test up to 3x the target load

        step_duration = config.test_duration_seconds // 5  # 5 steps

        for users in range(current_users, max_users + 1, current_users // 2):
            logger.info(f"Stress test step: {users} concurrent users")

            # Update configuration for this step
            step_config = TestConfiguration(
                test_id=f"{config.test_id}_stress_{users}",
                test_type=config.test_type,
                test_name=f"{config.test_name}_stress_{users}",
                target_endpoint=config.target_endpoint,
                concurrent_users=users,
                test_duration_seconds=step_duration,
                ramp_up_time_seconds=min(
                    config.ramp_up_time_seconds, step_duration // 2
                ),
            )

            await self._execute_concurrent_requests(step_config)

            # Check if system is failing
            recent_results = self.test_results[config.test_id][-100:]
            if recent_results:
                error_rate = sum(1 for r in recent_results if not r.success) / len(
                    recent_results
                )
                if error_rate > 0.5:  # 50% error rate
                    logger.warning(
                        f"High error rate detected at {users} users: {error_rate:.2%}"
                    )
                    break

    async def _execute_spike_test(self, config: TestConfiguration) -> dict:
        """Execute spike test with sudden load increases."""
        baseline_users = max(1, config.concurrent_users // 4)
        spike_users = config.concurrent_users

        # Baseline load
        baseline_config = self._create_test_step_config(config, baseline_users, 30)
        await self._execute_concurrent_requests(baseline_config)

        # Sudden spike
        spike_config = self._create_test_step_config(config, spike_users, 60)
        await self._execute_concurrent_requests(spike_config)

        # Return to baseline
        baseline_config = self._create_test_step_config(config, baseline_users, 30)
        await self._execute_concurrent_requests(baseline_config)

    async def _execute_endurance_test(self, config: TestConfiguration) -> dict:
        """Execute endurance test for extended duration."""
        # Extend duration for endurance testing
        extended_duration = max(config.test_duration_seconds, 3600)  # Minimum 1 hour

        endurance_config = TestConfiguration(
            test_id=config.test_id,
            test_type=config.test_type,
            test_name=config.test_name,
            target_endpoint=config.target_endpoint,
            concurrent_users=config.concurrent_users,
            test_duration_seconds=extended_duration,
            ramp_up_time_seconds=config.ramp_up_time_seconds,
        )

        await self._execute_concurrent_requests(endurance_config)

    async def _execute_scalability_test(self, config: TestConfiguration) -> dict:
        """Execute scalability test with varying user loads."""
        user_steps = [
            config.concurrent_users // 4,
            config.concurrent_users // 2,
            config.concurrent_users,
            config.concurrent_users * 2,
        ]

        step_duration = config.test_duration_seconds // len(user_steps)

        for users in user_steps:
            step_config = self._create_test_step_config(config, users, step_duration)
            await self._execute_concurrent_requests(step_config)

    async def _execute_basic_test(self, config: TestConfiguration) -> dict:
        """Execute basic performance test."""
        await self._execute_concurrent_requests(config)

    def _create_test_step_config(
        self, base_config: TestConfiguration, users: int, duration: int
    ) -> TestConfiguration:
        """Create configuration for test step."""
        return TestConfiguration(
            test_id=f"{base_config.test_id}_step_{users}",
            test_type=base_config.test_type,
            test_name=f"{base_config.test_name}_step_{users}",
            target_endpoint=base_config.target_endpoint,
            concurrent_users=users,
            test_duration_seconds=duration,
            ramp_up_time_seconds=min(base_config.ramp_up_time_seconds, duration // 3),
        )

    async def _ramp_up_users(self, config: TestConfiguration) -> dict:
        """Gradually ramp up concurrent users."""
        if config.ramp_up_time_seconds <= 0:
            return

        step_interval = config.ramp_up_time_seconds / config.concurrent_users

        for user_count in range(1, config.concurrent_users + 1):
            # Start user simulation
            asyncio.create_task(self._simulate_user_session(config, user_count))

            if user_count < config.concurrent_users:
                await asyncio.sleep(step_interval)

    async def _sustained_load_phase(self, config: TestConfiguration) -> dict:
        """Execute sustained load phase."""
        await self._execute_concurrent_requests(config)

    async def _execute_concurrent_requests(self, config: TestConfiguration) -> dict:
        """Execute concurrent requests for specified configuration."""
        tasks = []

        # Calculate request intervals
        if config.request_rate_per_second:
            request_interval = 1.0 / config.request_rate_per_second
        else:
            request_interval = 0.1  # Default 10 RPS per user

        # Create concurrent user tasks
        for user_id in range(config.concurrent_users):
            task = asyncio.create_task(
                self._simulate_user_session(config, user_id, request_interval)
            )
            tasks.append(task)

        # Wait for test duration
        await asyncio.sleep(config.test_duration_seconds)

        # Cancel all tasks
        for task in tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _simulate_user_session(
        self, config: TestConfiguration, user_id: int, request_interval: float = 0.1
    ):
        """Simulate individual user session."""
        session_timeout = aiohttp.ClientTimeout(total=30, connect=10)

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            start_time = time.time()

            while time.time() - start_time < config.test_duration_seconds:
                try:
                    # Make request
                    result = await self._make_request(session, config, user_id)

                    # Store result
                    self.test_results[config.test_id].append(result)

                    # Wait for next request
                    await asyncio.sleep(request_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Record error
                    error_result = TestResult(
                        timestamp=datetime.now(),
                        response_time_ms=0.0,
                        status_code=0,
                        error_message=str(e),
                        success=False,
                    )
                    self.test_results[config.test_id].append(error_result)

    async def _make_request(
        self, session: aiohttp.ClientSession, config: TestConfiguration, user_id: int
    ) -> TestResult:
        """Make HTTP request and measure performance."""
        start_time = time.time()

        try:
            # Prepare request
            headers = config.headers.copy()
            headers["User-Agent"] = f"PerformanceTest-User-{user_id}"

            # Generate payload if needed
            payload = None
            if config.payload_size_bytes > 0:
                payload = "x" * config.payload_size_bytes

            # Make request
            async with session.post(
                config.target_endpoint, data=payload, headers=headers
            ) as response:
                response_body = await response.read()
                response_time = (time.time() - start_time) * 1000

                return TestResult(
                    timestamp=datetime.now(),
                    response_time_ms=response_time,
                    status_code=response.status,
                    request_size_bytes=len(payload) if payload else 0,
                    response_size_bytes=len(response_body),
                    success=200 <= response.status < 400,
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return TestResult(
                timestamp=datetime.now(),
                response_time_ms=response_time,
                status_code=0,
                error_message=str(e),
                success=False,
            )

    async def _monitor_system_resources(self, test_id: str) -> dict:
        """Monitor system resources during test."""
        while True:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_mb": memory.used / (1024 * 1024),
                }

                self.system_metrics[test_id].append(metrics)

                await asyncio.sleep(5)  # Monitor every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(10)

    def _calculate_benchmark_metrics(
        self, config: TestConfiguration, start_time: datetime, end_time: datetime
    ) -> BenchmarkMetrics:
        """Calculate comprehensive benchmark metrics."""
        results = self.test_results.get(config.test_id, [])
        system_metrics = self.system_metrics.get(config.test_id, [])

        if not results:
            raise ValueError("No test results available for metric calculation")

        # Basic counts
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r.success)
        failed_requests = total_requests - successful_requests

        # Response time metrics
        response_times = [r.response_time_ms for r in results if r.success]

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = statistics.median(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50_response_time = p95_response_time = p99_response_time = 0.0

        # Throughput metrics
        test_duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0

        total_bytes = sum(r.response_size_bytes for r in results)
        bytes_per_second = total_bytes / test_duration if test_duration > 0 else 0

        # Error metrics
        error_rate_percent = (
            (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        )
        timeout_count = sum(
            1
            for r in results
            if not r.success and "timeout" in (r.error_message or "").lower()
        )

        # Resource metrics
        if system_metrics:
            cpu_values = [m["cpu_percent"] for m in system_metrics]
            memory_values = [m["memory_mb"] for m in system_metrics]

            avg_cpu_usage = statistics.mean(cpu_values)
            avg_memory_usage = statistics.mean(memory_values)
            peak_cpu_usage = max(cpu_values)
            peak_memory_usage = max(memory_values)
        else:
            avg_cpu_usage = avg_memory_usage = 0.0
            peak_cpu_usage = peak_memory_usage = 0.0

        return BenchmarkMetrics(
            test_id=config.test_id,
            test_type=config.test_type,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=p50_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            requests_per_second=requests_per_second,
            bytes_per_second=bytes_per_second,
            error_rate_percent=error_rate_percent,
            timeout_count=timeout_count,
            avg_cpu_usage_percent=avg_cpu_usage,
            avg_memory_usage_mb=avg_memory_usage,
            peak_cpu_usage_percent=peak_cpu_usage,
            peak_memory_usage_mb=peak_memory_usage,
            concurrent_users=config.concurrent_users,
            test_duration_seconds=test_duration,
        )


class BenchmarkSuite:
    """Comprehensive benchmark suite for performance testing."""

    def __init__(self) -> dict:
        self.executor = PerformanceTestExecutor()
        self.test_suites: Dict[str, List[TestConfiguration]] = {}
        self.benchmark_history: List[BenchmarkMetrics] = []

        # Default test configurations
        self._initialize_default_suites()

    def _initialize_default_suites(self) -> dict:
        """Initialize default benchmark test suites."""
        # API Performance Suite
        api_suite = [
            TestConfiguration(
                test_id="api_load_test",
                test_type=TestType.LOAD_TEST,
                test_name="API Load Test",
                target_endpoint="http://localhost:8000/api/v1/health",
                concurrent_users=50,
                test_duration_seconds=120,
                ramp_up_time_seconds=30,
            ),
            TestConfiguration(
                test_id="api_stress_test",
                test_type=TestType.STRESS_TEST,
                test_name="API Stress Test",
                target_endpoint="http://localhost:8000/api/v1/users",
                concurrent_users=100,
                test_duration_seconds=300,
                ramp_up_time_seconds=60,
            ),
            TestConfiguration(
                test_id="api_spike_test",
                test_type=TestType.SPIKE_TEST,
                test_name="API Spike Test",
                target_endpoint="http://localhost:8000/api/v1/orders",
                concurrent_users=200,
                test_duration_seconds=180,
                ramp_up_time_seconds=10,
            ),
        ]

        self.test_suites["api_performance"] = api_suite

        # Database Performance Suite
        db_suite = [
            TestConfiguration(
                test_id="db_query_load",
                test_type=TestType.LOAD_TEST,
                test_name="Database Query Load Test",
                target_endpoint="http://localhost:8000/api/v1/reports",
                concurrent_users=30,
                test_duration_seconds=300,
                ramp_up_time_seconds=60,
            ),
            TestConfiguration(
                test_id="db_transaction_test",
                test_type=TestType.VOLUME_TEST,
                test_name="Database Transaction Volume Test",
                target_endpoint="http://localhost:8000/api/v1/transactions",
                concurrent_users=20,
                test_duration_seconds=600,
                ramp_up_time_seconds=120,
            ),
        ]

        self.test_suites["database_performance"] = db_suite

        # Endurance Test Suite
        endurance_suite = [
            TestConfiguration(
                test_id="system_endurance",
                test_type=TestType.ENDURANCE_TEST,
                test_name="System Endurance Test",
                target_endpoint="http://localhost:8000/api/v1/status",
                concurrent_users=25,
                test_duration_seconds=3600,  # 1 hour
                ramp_up_time_seconds=300,
            )
        ]

        self.test_suites["endurance"] = endurance_suite

    async def run_benchmark_suite(self, suite_name: str) -> List[BenchmarkMetrics]:
        """Run complete benchmark suite."""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown benchmark suite: {suite_name}")

        logger.info(f"Starting benchmark suite: {suite_name}")

        suite_results = []
        test_configs = self.test_suites[suite_name]

        for config in test_configs:
            try:
                logger.info(f"Running test: {config.test_name}")

                # Execute test
                metrics = await self.executor.execute_test(config)
                suite_results.append(metrics)
                self.benchmark_history.append(metrics)

                # Brief pause between tests
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Test {config.test_name} failed: {e}")
                continue

        logger.info(
            f"Benchmark suite {suite_name} completed with {len(suite_results)} tests"
        )
        return suite_results

    async def run_custom_test(self, config: TestConfiguration) -> BenchmarkMetrics:
        """Run custom performance test."""
        metrics = await self.executor.execute_test(config)
        self.benchmark_history.append(metrics)
        return metrics

    def analyze_performance_trends(
        self, test_type: Optional[TestType] = None
    ) -> Dict[str, Any]:
        """Analyze performance trends across benchmark history."""
        relevant_metrics = self.benchmark_history

        if test_type:
            relevant_metrics = [m for m in relevant_metrics if m.test_type == test_type]

        if not relevant_metrics:
            return {"trend": "no_data"}

        # Sort by start time
        relevant_metrics.sort(key=lambda x: x.start_time)

        # Calculate trends
        response_times = [m.avg_response_time_ms for m in relevant_metrics]
        throughputs = [m.requests_per_second for m in relevant_metrics]
        error_rates = [m.error_rate_percent for m in relevant_metrics]

        analysis = {
            "total_tests": len(relevant_metrics),
            "time_span": {
                "start": relevant_metrics[0].start_time.isoformat(),
                "end": relevant_metrics[-1].start_time.isoformat(),
            },
            "response_time_trend": {
                "avg": statistics.mean(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "trend": "improving"
                if response_times[-1] < response_times[0]
                else "degrading",
            },
            "throughput_trend": {
                "avg": statistics.mean(throughputs),
                "min": min(throughputs),
                "max": max(throughputs),
                "trend": "improving"
                if throughputs[-1] > throughputs[0]
                else "degrading",
            },
            "error_rate_trend": {
                "avg": statistics.mean(error_rates),
                "min": min(error_rates),
                "max": max(error_rates),
                "trend": "improving"
                if error_rates[-1] < error_rates[0]
                else "degrading",
            },
        }

        # Overall performance score
        performance_score = self._calculate_performance_score(relevant_metrics[-1])
        analysis["current_performance_score"] = performance_score

        return analysis

    def _calculate_performance_score(self, metrics: BenchmarkMetrics) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0

        # Response time penalty (target: <200ms)
        if metrics.avg_response_time_ms > 200:
            score -= min((metrics.avg_response_time_ms - 200) / 20, 30)

        # Error rate penalty
        score -= metrics.error_rate_percent * 2

        # Throughput bonus (reward high throughput)
        if metrics.requests_per_second > 100:
            score += min((metrics.requests_per_second - 100) / 50, 10)

        # Resource usage penalty
        if metrics.avg_cpu_usage_percent > 80:
            score -= (metrics.avg_cpu_usage_percent - 80) / 2

        return max(0.0, min(100.0, score))

    def compare_benchmarks(self, test_id1: str, test_id2: str) -> Dict[str, Any]:
        """Compare two benchmark results."""
        metrics1 = next(
            (m for m in self.benchmark_history if m.test_id == test_id1), None
        )
        metrics2 = next(
            (m for m in self.benchmark_history if m.test_id == test_id2), None
        )

        if not metrics1 or not metrics2:
            return {"error": "One or both test results not found"}

        comparison = {
            "test_1": {
                "id": test_id1,
                "name": metrics1.test_type.value,
                "response_time": metrics1.avg_response_time_ms,
                "throughput": metrics1.requests_per_second,
                "error_rate": metrics1.error_rate_percent,
            },
            "test_2": {
                "id": test_id2,
                "name": metrics2.test_type.value,
                "response_time": metrics2.avg_response_time_ms,
                "throughput": metrics2.requests_per_second,
                "error_rate": metrics2.error_rate_percent,
            },
            "improvements": {
                "response_time": (
                    (metrics1.avg_response_time_ms - metrics2.avg_response_time_ms)
                    / metrics1.avg_response_time_ms
                )
                * 100,
                "throughput": (
                    (metrics2.requests_per_second - metrics1.requests_per_second)
                    / metrics1.requests_per_second
                )
                * 100,
                "error_rate": (
                    (metrics1.error_rate_percent - metrics2.error_rate_percent)
                    / max(metrics1.error_rate_percent, 0.1)
                )
                * 100,
            },
        }

        return comparison

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance testing report."""
        if not self.benchmark_history:
            return {"message": "No benchmark data available"}

        recent_tests = self.benchmark_history[-10:]  # Last 10 tests

        # Calculate summary statistics
        avg_response_time = statistics.mean(
            [m.avg_response_time_ms for m in recent_tests]
        )
        avg_throughput = statistics.mean([m.requests_per_second for m in recent_tests])
        avg_error_rate = statistics.mean([m.error_rate_percent for m in recent_tests])

        # Performance categories
        test_types = {}
        for metrics in recent_tests:
            test_type = metrics.test_type.value
            if test_type not in test_types:
                test_types[test_type] = []
            test_types[test_type].append(metrics)

        return {
            "summary": {
                "total_tests_run": len(self.benchmark_history),
                "recent_tests": len(recent_tests),
                "avg_response_time_ms": avg_response_time,
                "avg_throughput_rps": avg_throughput,
                "avg_error_rate_percent": avg_error_rate,
                "overall_performance_score": statistics.mean(
                    [self._calculate_performance_score(m) for m in recent_tests]
                ),
            },
            "test_categories": {
                test_type: {
                    "count": len(metrics_list),
                    "avg_response_time": statistics.mean(
                        [m.avg_response_time_ms for m in metrics_list]
                    ),
                    "avg_throughput": statistics.mean(
                        [m.requests_per_second for m in metrics_list]
                    ),
                    "avg_error_rate": statistics.mean(
                        [m.error_rate_percent for m in metrics_list]
                    ),
                }
                for test_type, metrics_list in test_types.items()
            },
            "trends": self.analyze_performance_trends(),
            "recommendations": self._generate_performance_recommendations(recent_tests),
        }

    def _generate_performance_recommendations(
        self, recent_tests: List[BenchmarkMetrics]
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if not recent_tests:
            return recommendations

        latest_test = recent_tests[-1]

        # Response time recommendations
        if latest_test.avg_response_time_ms > 500:
            recommendations.append(
                "Response time is high - consider optimizing database queries and API endpoints"
            )

        # Throughput recommendations
        if latest_test.requests_per_second < 50:
            recommendations.append(
                "Low throughput detected - consider scaling up server resources or optimizing request handling"
            )

        # Error rate recommendations
        if latest_test.error_rate_percent > 5:
            recommendations.append(
                "High error rate detected - investigate error logs and improve error handling"
            )

        # Resource usage recommendations
        if latest_test.avg_cpu_usage_percent > 85:
            recommendations.append(
                "High CPU usage - consider CPU optimization or horizontal scaling"
            )

        if latest_test.peak_memory_usage_mb > 4096:  # 4GB
            recommendations.append(
                "High memory usage - investigate memory leaks and optimize memory allocation"
            )

        # Trend-based recommendations
        if len(recent_tests) >= 3:
            response_time_trend = [m.avg_response_time_ms for m in recent_tests[-3:]]
            if all(
                response_time_trend[i] < response_time_trend[i + 1]
                for i in range(len(response_time_trend) - 1)
            ):
                recommendations.append(
                    "Response time is consistently increasing - immediate performance investigation needed"
                )

        return recommendations


class PerformanceTestingBenchmarkingSystem:
    """Main performance testing and benchmarking system."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.benchmark_suite = BenchmarkSuite()

        # System metrics
        self.metrics = {
            "total_tests_executed": 0,
            "average_performance_score": 0.0,
            "current_throughput_rps": 0.0,
            "current_response_time_ms": 0.0,
            "system_stability_score": 0.0,
            "last_benchmark_time": None,
        }

    async def start_testing_system(self) -> dict:
        """Start the performance testing and benchmarking system."""
        logger.info("Starting Performance Testing & Benchmarking System")

        # Start background tasks
        tasks = [
            asyncio.create_task(self._run_scheduled_benchmarks()),
            asyncio.create_task(self._monitor_performance_continuously()),
            asyncio.create_task(self._analyze_performance_trends()),
        ]

        await asyncio.gather(*tasks)

    async def _run_scheduled_benchmarks(self) -> dict:
        """Run scheduled benchmark tests."""
        while True:
            try:
                # Run baseline performance test every hour
                logger.info("Running scheduled baseline performance test")

                baseline_config = TestConfiguration(
                    test_id=f"baseline_{int(time.time())}",
                    test_type=TestType.BASELINE_TEST,
                    test_name="Scheduled Baseline Test",
                    target_endpoint="http://localhost:8000/api/v1/health",
                    concurrent_users=10,
                    test_duration_seconds=60,
                    ramp_up_time_seconds=10,
                )

                metrics = await self.benchmark_suite.run_custom_test(baseline_config)

                # Update system metrics
                self.metrics["total_tests_executed"] += 1
                self.metrics["current_throughput_rps"] = metrics.requests_per_second
                self.metrics["current_response_time_ms"] = metrics.avg_response_time_ms
                self.metrics["last_benchmark_time"] = datetime.now().isoformat()

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error in scheduled benchmarks: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes

    async def _monitor_performance_continuously(self) -> dict:
        """Monitor performance metrics continuously."""
        while True:
            try:
                # Calculate current performance scores
                if self.benchmark_suite.benchmark_history:
                    recent_tests = self.benchmark_suite.benchmark_history[-5:]
                    scores = [
                        self.benchmark_suite._calculate_performance_score(m)
                        for m in recent_tests
                    ]
                    self.metrics["average_performance_score"] = statistics.mean(scores)

                    # Calculate stability score based on variance
                    if len(scores) > 1:
                        variance = statistics.variance(scores)
                        stability = max(0, 100 - variance)
                        self.metrics["system_stability_score"] = stability

                await asyncio.sleep(300)  # Monitor every 5 minutes

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(600)

    async def _analyze_performance_trends(self) -> dict:
        """Analyze performance trends and generate alerts."""
        while True:
            try:
                if len(self.benchmark_suite.benchmark_history) >= 3:
                    trends = self.benchmark_suite.analyze_performance_trends()

                    # Check for concerning trends
                    if (
                        trends.get("response_time_trend", {}).get("trend")
                        == "degrading"
                    ):
                        logger.warning(
                            "Performance degradation detected: Response time trending upward"
                        )

                    if trends.get("error_rate_trend", {}).get("avg", 0) > 5:
                        logger.warning(
                            f"High error rate detected: {trends['error_rate_trend']['avg']:.2f}%"
                        )

                await asyncio.sleep(1800)  # Analyze every 30 minutes

            except Exception as e:
                logger.error(f"Error in performance trend analysis: {e}")
                await asyncio.sleep(3600)

    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark across all test suites."""
        logger.info("Starting comprehensive benchmark")

        results = {}

        # Run all benchmark suites
        for suite_name in self.benchmark_suite.test_suites.keys():
            try:
                suite_results = await self.benchmark_suite.run_benchmark_suite(
                    suite_name
                )
                results[suite_name] = suite_results

                # Brief pause between suites
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Failed to run benchmark suite {suite_name}: {e}")
                results[suite_name] = {"error": str(e)}

        # Update metrics
        total_tests = sum(len(v) for v in results.values() if isinstance(v, list))
        self.metrics["total_tests_executed"] += total_tests

        logger.info(f"Comprehensive benchmark completed: {total_tests} tests executed")

        return {
            "comprehensive_results": results,
            "summary": self.benchmark_suite.get_performance_report(),
            "execution_time": datetime.now().isoformat(),
        }

    def get_testing_report(self) -> Dict[str, Any]:
        """Get comprehensive testing and benchmarking report."""
        return {
            "system_metrics": self.metrics,
            "benchmark_report": self.benchmark_suite.get_performance_report(),
            "available_test_suites": list(self.benchmark_suite.test_suites.keys()),
            "recent_tests": [
                {
                    "test_id": m.test_id,
                    "test_type": m.test_type.value,
                    "throughput_rps": m.requests_per_second,
                    "response_time_ms": m.avg_response_time_ms,
                    "error_rate": m.error_rate_percent,
                    "performance_score": self.benchmark_suite._calculate_performance_score(
                        m
                    ),
                }
                for m in self.benchmark_suite.benchmark_history[-10:]
            ],
        }


# Example usage and integration
async def main() -> None:
    """Example usage of the Performance Testing & Benchmarking System."""
    # Initialize with mobile ERP SDK
    sdk = MobileERPSDK()

    # Create testing system
    testing_system = PerformanceTestingBenchmarkingSystem(sdk)

    # Start testing system
    await testing_system.start_testing_system()


if __name__ == "__main__":
    asyncio.run(main())
