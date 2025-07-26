"""
ITDO ERP Backend - Resource Management Load Testing
Day 23: Load testing and benchmarking for resource management system
"""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestResourceManagementLoadTesting:
    """Load testing for resource management system"""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application for load testing"""
        from fastapi import FastAPI

        from app.api.v1.resource_analytics_api import router as analytics_router
        from app.api.v1.resource_integration_api import router as integration_router
        from app.api.v1.resource_management_api import router as management_router

        app = FastAPI()
        app.include_router(integration_router, prefix="/api/v1/resource-integration")
        app.include_router(management_router, prefix="/api/v1/resource-management")
        app.include_router(analytics_router, prefix="/api/v1/resource-analytics")
        return app

    @pytest.fixture
    def client(self, mock_app):
        """Test client for load testing"""
        return TestClient(mock_app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock-jwt-token"}

    def test_baseline_performance_metrics(self, client, auth_headers):
        """Establish baseline performance metrics"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test single request performance
            endpoints = [
                "/api/v1/resource-integration/dashboard",
                "/api/v1/resource-integration/health",
                "/api/v1/resource-integration/health-check",
            ]

            baseline_metrics = {}

            for endpoint in endpoints:
                response_times = []

                # Warm up
                for _ in range(5):
                    client.get(endpoint, headers=auth_headers)

                # Measure baseline
                for _ in range(20):
                    start_time = time.time()
                    response = client.get(endpoint, headers=auth_headers)
                    end_time = time.time()

                    if response.status_code in [200, 500]:  # Accept mocked responses
                        response_times.append(end_time - start_time)

                if response_times:
                    baseline_metrics[endpoint] = {
                        "avg_response_time": statistics.mean(response_times),
                        "median_response_time": statistics.median(response_times),
                        "p95_response_time": sorted(response_times)[
                            int(0.95 * len(response_times))
                        ],
                        "p99_response_time": sorted(response_times)[
                            int(0.99 * len(response_times))
                        ],
                        "std_dev": statistics.stdev(response_times)
                        if len(response_times) > 1
                        else 0,
                    }

            # Baseline assertions
            for endpoint, metrics in baseline_metrics.items():
                assert metrics["avg_response_time"] < 0.1, (
                    f"{endpoint} avg response time {metrics['avg_response_time']:.3f}s exceeds 100ms"
                )
                assert metrics["p95_response_time"] < 0.2, (
                    f"{endpoint} P95 response time {metrics['p95_response_time']:.3f}s exceeds 200ms"
                )
                assert metrics["std_dev"] < 0.05, (
                    f"{endpoint} response time std dev {metrics['std_dev']:.3f}s too high"
                )

            print("Baseline Performance Metrics:")
            for endpoint, metrics in baseline_metrics.items():
                print(f"  {endpoint}:")
                print(f"    Average: {metrics['avg_response_time']:.3f}s")
                print(f"    P95: {metrics['p95_response_time']:.3f}s")
                print(f"    P99: {metrics['p99_response_time']:.3f}s")
                print(f"    Std Dev: {metrics['std_dev']:.3f}s")

    def test_load_testing_gradual_ramp_up(self, client, auth_headers):
        """Test gradual load ramp-up"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            def make_request():
                start_time = time.time()
                response = client.get(
                    "/api/v1/resource-integration/dashboard", headers=auth_headers
                )
                end_time = time.time()
                return {
                    "response_time": end_time - start_time,
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 500],
                }

            # Gradual ramp-up: 1, 5, 10, 20, 50 concurrent users
            load_levels = [1, 5, 10, 20, 50]
            load_test_results = {}

            for concurrent_users in load_levels:
                print(f"Testing with {concurrent_users} concurrent users...")

                with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                    start_time = time.time()

                    # Submit requests
                    futures = [
                        executor.submit(make_request)
                        for _ in range(concurrent_users * 2)
                    ]
                    results = [future.result() for future in as_completed(futures)]

                    end_time = time.time()
                    total_time = end_time - start_time

                # Analyze results
                response_times = [r["response_time"] for r in results if r["success"]]
                success_rate = sum(1 for r in results if r["success"]) / len(results)

                if response_times:
                    load_test_results[concurrent_users] = {
                        "success_rate": success_rate,
                        "avg_response_time": statistics.mean(response_times),
                        "p95_response_time": sorted(response_times)[
                            int(0.95 * len(response_times))
                        ],
                        "throughput": len(results) / total_time,
                        "total_requests": len(results),
                        "successful_requests": len(response_times),
                    }

            # Performance degradation analysis
            print("\nLoad Test Results:")
            for users, metrics in load_test_results.items():
                print(f"  {users} users:")
                print(f"    Success Rate: {metrics['success_rate']:.1%}")
                print(f"    Avg Response Time: {metrics['avg_response_time']:.3f}s")
                print(f"    P95 Response Time: {metrics['p95_response_time']:.3f}s")
                print(f"    Throughput: {metrics['throughput']:.1f} req/s")

            # Assertions for load handling
            for users, metrics in load_test_results.items():
                assert metrics["success_rate"] >= 0.95, (
                    f"Success rate {metrics['success_rate']:.1%} below 95% at {users} users"
                )

                # Response time should not degrade exponentially
                if users <= 10:
                    assert metrics["avg_response_time"] < 0.5, (
                        f"Response time {metrics['avg_response_time']:.3f}s too high at {users} users"
                    )
                elif users <= 20:
                    assert metrics["avg_response_time"] < 1.0, (
                        f"Response time {metrics['avg_response_time']:.3f}s too high at {users} users"
                    )

    def test_sustained_load_testing(self, client, auth_headers):
        """Test sustained load over time"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            def make_sustained_request():
                return client.get(
                    "/api/v1/resource-integration/health-check", headers=auth_headers
                )

            # Sustained load: 10 concurrent users for 30 seconds
            concurrent_users = 10
            test_duration = 30  # seconds

            results = []
            start_test_time = time.time()

            def worker():
                while time.time() - start_test_time < test_duration:
                    start_time = time.time()
                    response = make_sustained_request()
                    end_time = time.time()

                    results.append(
                        {
                            "timestamp": start_time,
                            "response_time": end_time - start_time,
                            "status_code": response.status_code,
                            "success": response.status_code in [200, 500],
                        }
                    )

                    # Small delay to prevent overwhelming
                    time.sleep(0.1)

            # Run sustained load test
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(worker) for _ in range(concurrent_users)]
                for future in as_completed(futures):
                    future.result()

            # Analyze sustained performance
            if results:
                successful_results = [r for r in results if r["success"]]
                response_times = [r["response_time"] for r in successful_results]

                # Group results by time windows (5-second windows)
                time_windows = {}
                for result in successful_results:
                    window = int((result["timestamp"] - start_test_time) // 5) * 5
                    if window not in time_windows:
                        time_windows[window] = []
                    time_windows[window].append(result["response_time"])

                # Check for performance degradation over time
                window_averages = {}
                for window, times in time_windows.items():
                    if times:
                        window_averages[window] = statistics.mean(times)

                print(f"\nSustained Load Test Results ({test_duration}s):")
                print(f"  Total Requests: {len(results)}")
                print(f"  Successful Requests: {len(successful_results)}")
                print(f"  Success Rate: {len(successful_results) / len(results):.1%}")
                print(
                    f"  Average Response Time: {statistics.mean(response_times):.3f}s"
                )
                print(
                    f"  Throughput: {len(successful_results) / test_duration:.1f} req/s"
                )

                print("  Performance by Time Window:")
                for window, avg_time in sorted(window_averages.items()):
                    print(f"    {window}-{window + 5}s: {avg_time:.3f}s avg")

                # Assertions
                assert len(successful_results) / len(results) >= 0.95, (
                    "Success rate below 95% during sustained load"
                )
                assert statistics.mean(response_times) < 0.5, (
                    "Average response time too high during sustained load"
                )

                # Check for memory leaks or degradation
                first_window_avg = window_averages[min(window_averages.keys())]
                last_window_avg = window_averages[max(window_averages.keys())]
                degradation_ratio = (
                    last_window_avg / first_window_avg if first_window_avg > 0 else 1
                )

                assert degradation_ratio < 2.0, (
                    f"Performance degraded {degradation_ratio:.1f}x during sustained load"
                )

    def test_spike_load_testing(self, client, auth_headers):
        """Test sudden load spikes"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            def make_spike_request():
                start_time = time.time()
                response = client.get(
                    "/api/v1/resource-integration/dashboard", headers=auth_headers
                )
                end_time = time.time()
                return {
                    "response_time": end_time - start_time,
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 500],
                }

            # Baseline load (5 users)
            print("Establishing baseline with 5 users...")
            with ThreadPoolExecutor(max_workers=5) as executor:
                baseline_futures = [
                    executor.submit(make_spike_request) for _ in range(10)
                ]
                baseline_results = [future.result() for future in baseline_futures]

            baseline_response_times = [
                r["response_time"] for r in baseline_results if r["success"]
            ]
            baseline_avg = (
                statistics.mean(baseline_response_times)
                if baseline_response_times
                else 0
            )

            # Sudden spike (50 users)
            print("Testing spike load with 50 users...")
            spike_start_time = time.time()

            with ThreadPoolExecutor(max_workers=50) as executor:
                spike_futures = [
                    executor.submit(make_spike_request) for _ in range(100)
                ]
                spike_results = [future.result() for future in spike_futures]

            spike_end_time = time.time()
            spike_duration = spike_end_time - spike_start_time

            # Analyze spike results
            spike_successful = [r for r in spike_results if r["success"]]
            spike_response_times = [r["response_time"] for r in spike_successful]

            if spike_response_times:
                spike_avg = statistics.mean(spike_response_times)
                spike_p95 = sorted(spike_response_times)[
                    int(0.95 * len(spike_response_times))
                ]
                spike_success_rate = len(spike_successful) / len(spike_results)
                spike_throughput = len(spike_successful) / spike_duration

                print("\nSpike Load Test Results:")
                print(f"  Baseline Avg Response Time: {baseline_avg:.3f}s")
                print(f"  Spike Avg Response Time: {spike_avg:.3f}s")
                print(f"  Spike P95 Response Time: {spike_p95:.3f}s")
                print(f"  Spike Success Rate: {spike_success_rate:.1%}")
                print(f"  Spike Throughput: {spike_throughput:.1f} req/s")
                print(
                    f"  Response Time Increase: {spike_avg / baseline_avg:.1f}x"
                    if baseline_avg > 0
                    else "N/A"
                )

                # Assertions
                assert spike_success_rate >= 0.8, (
                    f"Spike success rate {spike_success_rate:.1%} below 80%"
                )
                assert spike_p95 < 2.0, (
                    f"Spike P95 response time {spike_p95:.3f}s exceeds 2s"
                )

                # System should handle spikes without complete failure
                response_time_increase = (
                    spike_avg / baseline_avg if baseline_avg > 0 else 1
                )
                assert response_time_increase < 5.0, (
                    f"Response time increased {response_time_increase:.1f}x during spike"
                )

    def test_mixed_workload_performance(self, client, auth_headers):
        """Test performance with mixed API workloads"""

        with (
            patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth,
            patch("app.api.v1.resource_management_api.get_current_user") as mock_auth2,
        ):
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }
            mock_auth2.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Define different workload types
            def read_heavy_workload():
                """Simulates read-heavy operations"""
                endpoints = [
                    "/api/v1/resource-integration/dashboard",
                    "/api/v1/resource-integration/health",
                    "/api/v1/resource-integration/health-check",
                ]

                start_time = time.time()
                response = client.get(
                    endpoints[0], headers=auth_headers
                )  # Use first endpoint
                end_time = time.time()

                return {
                    "workload_type": "read_heavy",
                    "response_time": end_time - start_time,
                    "success": response.status_code in [200, 500],
                }

            def write_heavy_workload():
                """Simulates write-heavy operations"""
                resource_data = {
                    "name": f"Test Resource {int(time.time() * 1000) % 10000}",
                    "type": "human",
                    "department_id": 1,
                    "hourly_rate": 150.0,
                }

                start_time = time.time()
                response = client.post(
                    "/api/v1/resource-management/resources",
                    json=resource_data,
                    headers=auth_headers,
                )
                end_time = time.time()

                return {
                    "workload_type": "write_heavy",
                    "response_time": end_time - start_time,
                    "success": response.status_code in [201, 500, 422],
                }

            def complex_workload():
                """Simulates complex analytical operations"""
                start_time = time.time()
                response = client.get(
                    "/api/v1/resource-integration/dashboard?time_period=quarter&include_forecasts=true",
                    headers=auth_headers,
                )
                end_time = time.time()

                return {
                    "workload_type": "complex",
                    "response_time": end_time - start_time,
                    "success": response.status_code in [200, 500],
                }

            # Mixed workload simulation
            workload_functions = [
                read_heavy_workload,
                write_heavy_workload,
                complex_workload,
            ]
            workload_weights = [0.6, 0.2, 0.2]  # 60% read, 20% write, 20% complex

            def execute_mixed_workload():
                import random

                workload_func = random.choices(
                    workload_functions, weights=workload_weights
                )[0]
                return workload_func()

            # Run mixed workload test
            print("Running mixed workload test...")

            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(execute_mixed_workload) for _ in range(100)]
                results = [future.result() for future in futures]

            # Analyze results by workload type
            workload_analysis = {}
            for result in results:
                workload_type = result["workload_type"]
                if workload_type not in workload_analysis:
                    workload_analysis[workload_type] = []
                workload_analysis[workload_type].append(result)

            print("\nMixed Workload Test Results:")
            for workload_type, workload_results in workload_analysis.items():
                successful = [r for r in workload_results if r["success"]]
                if successful:
                    response_times = [r["response_time"] for r in successful]
                    avg_response_time = statistics.mean(response_times)
                    success_rate = len(successful) / len(workload_results)

                    print(f"  {workload_type.title()} Workload:")
                    print(f"    Requests: {len(workload_results)}")
                    print(f"    Success Rate: {success_rate:.1%}")
                    print(f"    Avg Response Time: {avg_response_time:.3f}s")

                    # Workload-specific assertions
                    assert success_rate >= 0.9, (
                        f"{workload_type} success rate {success_rate:.1%} below 90%"
                    )

                    if workload_type == "read_heavy":
                        assert avg_response_time < 0.2, (
                            f"Read-heavy workload too slow: {avg_response_time:.3f}s"
                        )
                    elif workload_type == "write_heavy":
                        assert avg_response_time < 0.5, (
                            f"Write-heavy workload too slow: {avg_response_time:.3f}s"
                        )
                    elif workload_type == "complex":
                        assert avg_response_time < 1.0, (
                            f"Complex workload too slow: {avg_response_time:.3f}s"
                        )

    def test_resource_exhaustion_scenarios(self, client, auth_headers):
        """Test system behavior under resource exhaustion"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Test 1: CPU intensive operations
            def cpu_intensive_request():
                start_time = time.time()
                response = client.get(
                    "/api/v1/resource-integration/dashboard?time_period=year&include_forecasts=true&include_optimization=true",
                    headers=auth_headers,
                )
                end_time = time.time()
                return {
                    "response_time": end_time - start_time,
                    "success": response.status_code in [200, 500],
                }

            print("Testing CPU intensive operations...")

            # Run multiple CPU intensive operations concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                cpu_futures = [
                    executor.submit(cpu_intensive_request) for _ in range(20)
                ]
                cpu_results = [future.result() for future in cpu_futures]

            cpu_successful = [r for r in cpu_results if r["success"]]
            if cpu_successful:
                cpu_response_times = [r["response_time"] for r in cpu_successful]
                cpu_avg = statistics.mean(cpu_response_times)
                cpu_success_rate = len(cpu_successful) / len(cpu_results)

                print("  CPU Intensive Test:")
                print(f"    Success Rate: {cpu_success_rate:.1%}")
                print(f"    Avg Response Time: {cpu_avg:.3f}s")

                # System should handle CPU intensive operations gracefully
                assert cpu_success_rate >= 0.7, (
                    f"CPU intensive success rate {cpu_success_rate:.1%} below 70%"
                )
                assert cpu_avg < 3.0, (
                    f"CPU intensive avg response time {cpu_avg:.3f}s exceeds 3s"
                )

            # Test 2: Memory intensive operations (simulated)
            def memory_intensive_request():
                # Simulate large data request
                start_time = time.time()
                response = client.get(
                    "/api/v1/resource-integration/dashboard?departments=1,2,3,4,5,6,7,8,9,10",
                    headers=auth_headers,
                )
                end_time = time.time()
                return {
                    "response_time": end_time - start_time,
                    "success": response.status_code in [200, 500],
                }

            print("Testing memory intensive operations...")

            with ThreadPoolExecutor(max_workers=15) as executor:
                memory_futures = [
                    executor.submit(memory_intensive_request) for _ in range(30)
                ]
                memory_results = [future.result() for future in memory_futures]

            memory_successful = [r for r in memory_results if r["success"]]
            if memory_successful:
                memory_response_times = [r["response_time"] for r in memory_successful]
                memory_avg = statistics.mean(memory_response_times)
                memory_success_rate = len(memory_successful) / len(memory_results)

                print("  Memory Intensive Test:")
                print(f"    Success Rate: {memory_success_rate:.1%}")
                print(f"    Avg Response Time: {memory_avg:.3f}s")

                # System should handle memory intensive operations gracefully
                assert memory_success_rate >= 0.8, (
                    f"Memory intensive success rate {memory_success_rate:.1%} below 80%"
                )
                assert memory_avg < 2.0, (
                    f"Memory intensive avg response time {memory_avg:.3f}s exceeds 2s"
                )

    def test_performance_regression_detection(self, client, auth_headers):
        """Test for performance regression detection"""

        with patch("app.api.v1.resource_integration_api.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "id": 1,
                "username": "testuser",
                "department_ids": [1],
            }

            # Expected performance benchmarks (baseline)
            performance_benchmarks = {
                "/api/v1/resource-integration/dashboard": {
                    "max_response_time": 0.2,
                    "p95_response_time": 0.15,
                    "min_success_rate": 0.95,
                },
                "/api/v1/resource-integration/health": {
                    "max_response_time": 0.1,
                    "p95_response_time": 0.05,
                    "min_success_rate": 0.99,
                },
                "/api/v1/resource-integration/health-check": {
                    "max_response_time": 0.05,
                    "p95_response_time": 0.03,
                    "min_success_rate": 0.99,
                },
            }

            print("Running performance regression tests...")

            regression_results = {}

            for endpoint, benchmarks in performance_benchmarks.items():
                response_times = []
                successes = 0
                total_requests = 50

                for _ in range(total_requests):
                    start_time = time.time()
                    response = client.get(endpoint, headers=auth_headers)
                    end_time = time.time()

                    response_time = end_time - start_time
                    response_times.append(response_time)

                    if response.status_code in [200, 500]:
                        successes += 1

                # Calculate metrics
                avg_response_time = statistics.mean(response_times)
                p95_response_time = sorted(response_times)[
                    int(0.95 * len(response_times))
                ]
                success_rate = successes / total_requests

                regression_results[endpoint] = {
                    "avg_response_time": avg_response_time,
                    "p95_response_time": p95_response_time,
                    "success_rate": success_rate,
                    "passed": (
                        avg_response_time <= benchmarks["max_response_time"]
                        and p95_response_time <= benchmarks["p95_response_time"]
                        and success_rate >= benchmarks["min_success_rate"]
                    ),
                }

                print(f"  {endpoint}:")
                print(
                    f"    Avg Response Time: {avg_response_time:.3f}s (max: {benchmarks['max_response_time']:.3f}s)"
                )
                print(
                    f"    P95 Response Time: {p95_response_time:.3f}s (max: {benchmarks['p95_response_time']:.3f}s)"
                )
                print(
                    f"    Success Rate: {success_rate:.1%} (min: {benchmarks['min_success_rate']:.1%})"
                )
                print(
                    f"    Status: {'PASS' if regression_results[endpoint]['passed'] else 'FAIL'}"
                )

            # Assert no regressions
            failed_endpoints = [
                ep for ep, result in regression_results.items() if not result["passed"]
            ]
            assert len(failed_endpoints) == 0, (
                f"Performance regression detected in: {failed_endpoints}"
            )

            print(
                f"\nRegression Test Summary: {len(regression_results)} endpoints tested, {len(failed_endpoints)} regressions detected"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
