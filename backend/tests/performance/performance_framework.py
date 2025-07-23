"""Performance testing framework."""
import asyncio
import time
import statistics
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PerformanceResult:
    """Performance test result."""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50: float
    p90: float
    p95: float
    p99: float
    requests_per_second: float
    errors: List[str]


class PerformanceTestFramework:
    """Framework for running performance tests."""

    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.results = []

    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Dict[str, Any] = None,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        ramp_up_time: int = 0
    ) -> PerformanceResult:
        """Run load test on endpoint."""
        print(f"Running load test: {method} {endpoint}")
        print(f"Concurrent users: {concurrent_users}, Requests per user: {requests_per_user}")

        start_time = time.time()
        response_times = []
        errors = []
        successful = 0

        # Headers
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        # Create session
        async with aiohttp.ClientSession() as session:
            # Ramp up
            if ramp_up_time > 0:
                for i in range(concurrent_users):
                    await asyncio.sleep(ramp_up_time / concurrent_users)

            # Run concurrent requests
            tasks = []
            for user in range(concurrent_users):
                for req in range(requests_per_user):
                    task = self._make_request(
                        session, endpoint, method, headers, payload
                    )
                    tasks.append(task)

            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                elif isinstance(result, dict):
                    if result["success"]:
                        successful += 1
                        response_times.append(result["response_time"])
                    else:
                        errors.append(result["error"])

        # Calculate metrics
        total_requests = concurrent_users * requests_per_user
        total_time = time.time() - start_time

        if response_times:
            response_times.sort()
            result = PerformanceResult(
                endpoint=endpoint,
                method=method,
                total_requests=total_requests,
                successful_requests=successful,
                failed_requests=total_requests - successful,
                avg_response_time=statistics.mean(response_times),
                min_response_time=min(response_times),
                max_response_time=max(response_times),
                p50=self._percentile(response_times, 50),
                p90=self._percentile(response_times, 90),
                p95=self._percentile(response_times, 95),
                p99=self._percentile(response_times, 99),
                requests_per_second=total_requests / total_time,
                errors=errors[:10]  # First 10 errors
            )
        else:
            # All requests failed
            result = PerformanceResult(
                endpoint=endpoint,
                method=method,
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=total_requests,
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                p50=0,
                p90=0,
                p95=0,
                p99=0,
                requests_per_second=0,
                errors=errors[:10]
            )

        self.results.append(result)
        return result

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str,
        headers: Dict[str, str],
        payload: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make single request and measure time."""
        url = f"{self.base_url}{endpoint}"
        start = time.time()

        try:
            async with session.request(
                method, url, headers=headers, json=payload, timeout=30
            ) as response:
                await response.text()  # Read response body
                response_time = (time.time() - start) * 1000  # Convert to ms

                if response.status < 400:
                    return {
                        "success": True,
                        "response_time": response_time,
                        "status": response.status
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time": response_time
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": (time.time() - start) * 1000
            }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0

        index = (len(data) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1

        if upper >= len(data):
            return data[lower]

        return data[lower] + (data[upper] - data[lower]) * (index - lower)

    def generate_report(self) -> str:
        """Generate performance test report."""
        report = f"""# Performance Test Report

Generated: {datetime.now().isoformat()}

## Summary

| Endpoint | Method | Total | Success | Failed | Avg (ms) | P95 (ms) | P99 (ms) | RPS |
|----------|--------|-------|---------|--------|----------|----------|----------|-----|
"""

        for result in self.results:
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0

            report += f"| {result.endpoint} | {result.method} | {result.total_requests} | "
            report += f"{result.successful_requests} ({success_rate:.1f}%) | {result.failed_requests} | "
            report += f"{result.avg_response_time:.1f} | {result.p95:.1f} | {result.p99:.1f} | "
            report += f"{result.requests_per_second:.1f} |\n"

        report += "\n## Detailed Results\n\n"

        for result in self.results:
            report += f"### {result.method} {result.endpoint}\n\n"
            report += f"- Response times: min={result.min_response_time:.1f}ms, "
            report += f"max={result.max_response_time:.1f}ms\n"
            report += f"- Percentiles: P50={result.p50:.1f}ms, P90={result.p90:.1f}ms\n"

            if result.errors:
                report += f"- Sample errors:\n"
                for error in result.errors[:5]:
                    report += f"  - {error}\n"

            report += "\n"

        return report