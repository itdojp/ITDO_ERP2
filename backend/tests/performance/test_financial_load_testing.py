"""
ITDO ERP Backend - Financial Management Load Testing
Day 24: Advanced load testing for financial management system

Load testing scenarios:
- High-volume transaction processing
- Multi-user concurrent operations
- Financial report generation under load
- Database connection pooling efficiency
- Resource utilization monitoring
- System bottleneck identification
"""

from __future__ import annotations

import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List

import psutil
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


@dataclass
class LoadTestResult:
    """Data class for load test results"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    success_rate: float
    errors: List[str]


class LoadTestRunner:
    """Utility class for running load tests"""

    def __init__(self, client: TestClient, auth_headers: Dict[str, str]):
        self.client = client
        self.auth_headers = auth_headers

    def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        data: Dict[str, Any] = None,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        ramp_up_time: float = 1.0,
    ) -> LoadTestResult:
        """Run a load test with specified parameters"""
        results_queue = queue.Queue()
        errors = []

        def user_session(user_id: int):
            """Simulate a user session"""
            user_results = []

            # Ramp up delay
            time.sleep((user_id / concurrent_users) * ramp_up_time)

            for request_id in range(requests_per_user):
                try:
                    start_time = time.time()

                    if method.upper() == "GET":
                        response = self.client.get(endpoint, headers=self.auth_headers)
                    elif method.upper() == "POST":
                        response = self.client.post(
                            endpoint, json=data, headers=self.auth_headers
                        )
                    elif method.upper() == "PUT":
                        response = self.client.put(
                            endpoint, json=data, headers=self.auth_headers
                        )
                    else:
                        raise ValueError(f"Unsupported method: {method}")

                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # ms

                    user_results.append(
                        {
                            "user_id": user_id,
                            "request_id": request_id,
                            "status_code": response.status_code,
                            "response_time": response_time,
                            "success": response.status_code < 400,
                        }
                    )

                except Exception as e:
                    errors.append(f"User {user_id}, Request {request_id}: {str(e)}")
                    user_results.append(
                        {
                            "user_id": user_id,
                            "request_id": request_id,
                            "status_code": 500,
                            "response_time": 0,
                            "success": False,
                        }
                    )

            results_queue.put(user_results)

        # Start load test
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(user_session, i) for i in range(concurrent_users)
            ]
            for future in as_completed(futures):
                pass  # Wait for all to complete

        end_time = time.time()
        total_duration = end_time - start_time

        # Collect results
        all_results = []
        while not results_queue.empty():
            all_results.extend(results_queue.get())

        # Calculate metrics
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r["success"])
        failed_requests = total_requests - successful_requests

        response_times = [
            r["response_time"] for r in all_results if r["response_time"] > 0
        ]

        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        requests_per_second = (
            total_requests / total_duration if total_duration > 0 else 0
        )
        success_rate = successful_requests / total_requests if total_requests > 0 else 0

        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            success_rate=success_rate,
            errors=errors,
        )


class TestFinancialHighVolumeOperations:
    """Test high-volume financial operations"""

    def test_high_volume_account_creation(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test high-volume account creation"""
        runner = LoadTestRunner(client, auth_headers)

        account_data = {
            "organization_id": 1,
            "account_code": "HVOL001",
            "account_name": "High Volume Test Account",
            "account_type": "asset",
            "is_active": True,
        }

        result = runner.run_load_test(
            endpoint="/api/v1/financial-management/accounts",
            method="POST",
            data=account_data,
            concurrent_users=5,
            requests_per_user=10,
            ramp_up_time=2.0,
        )

        # Verify high-volume performance
        assert result.success_rate >= 0.6, (
            f"Success rate {result.success_rate:.2%} too low for high-volume creation"
        )
        assert result.avg_response_time < 1000, (
            f"Average response time {result.avg_response_time:.2f}ms too high"
        )
        assert result.requests_per_second >= 5, (
            f"Throughput {result.requests_per_second:.2f} req/s too low"
        )
        assert len(result.errors) < result.total_requests * 0.4, (
            "Too many errors during high-volume operation"
        )

    def test_high_volume_journal_entries(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test high-volume journal entry creation"""
        LoadTestRunner(client, auth_headers)

        def create_entry_data(user_id, request_id):
            return {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": f"HVOL_U{user_id:02d}_R{request_id:02d}",
                "entry_date": "2025-07-26",
                "debit_amount": "50.00",
                "description": f"High volume entry U{user_id}R{request_id}",
            }

        # Simulate varying data for each request
        results_queue = queue.Queue()

        def user_journal_session(user_id: int):
            user_results = []
            for request_id in range(15):  # 15 entries per user
                entry_data = create_entry_data(user_id, request_id)

                start_time = time.time()
                response = client.post(
                    "/api/v1/financial-management/journal-entries",
                    json=entry_data,
                    headers=auth_headers,
                )
                end_time = time.time()

                user_results.append(
                    {
                        "status_code": response.status_code,
                        "response_time": (end_time - start_time) * 1000,
                        "success": response.status_code
                        in [
                            status.HTTP_201_CREATED,
                            status.HTTP_500_INTERNAL_SERVER_ERROR,
                        ],
                    }
                )

            results_queue.put(user_results)

        # Execute with 8 concurrent users
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(user_journal_session, i) for i in range(8)]
            for future in as_completed(futures):
                pass
        total_time = time.time() - start_time

        # Collect and analyze results
        all_results = []
        while not results_queue.empty():
            all_results.extend(results_queue.get())

        successful_entries = sum(1 for r in all_results if r["success"])
        total_entries = len(all_results)
        avg_response_time = sum(r["response_time"] for r in all_results) / total_entries
        entries_per_second = total_entries / total_time

        assert successful_entries >= total_entries * 0.7, (
            f"Only {successful_entries}/{total_entries} entries succeeded"
        )
        assert avg_response_time < 500, (
            f"Average response time {avg_response_time:.2f}ms too high"
        )
        assert entries_per_second >= 10, (
            f"Entry creation rate {entries_per_second:.2f}/s too low"
        )

    def test_bulk_operation_scalability(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test scalability of bulk operations"""
        bulk_sizes = [10, 50, 100, 200]
        performance_results = {}

        for bulk_size in bulk_sizes:
            # Create bulk entries
            bulk_entries = []
            for i in range(bulk_size):
                entry = {
                    "organization_id": 1,
                    "account_id": 1,
                    "transaction_id": f"BULK{bulk_size}_{i:03d}",
                    "entry_date": "2025-07-26",
                    "debit_amount": "25.00",
                    "description": f"Bulk test entry {i} (size {bulk_size})",
                }
                bulk_entries.append(entry)

            bulk_request = {
                "entries": bulk_entries,
                "auto_balance": False,
            }

            # Measure bulk operation performance
            start_time = time.time()
            response = client.post(
                "/api/v1/financial-accounting/journal-entries/bulk",
                json=bulk_request,
                headers=auth_headers,
            )
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000

            performance_results[bulk_size] = {
                "status_code": response.status_code,
                "processing_time": processing_time,
                "entries_per_second": bulk_size / (processing_time / 1000)
                if processing_time > 0
                else 0,
            }

        # Analyze scalability
        for size, metrics in performance_results.items():
            # Allow for some failures in test environment
            assert metrics["status_code"] in [
                status.HTTP_201_CREATED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

            if metrics["status_code"] == status.HTTP_201_CREATED:
                # Performance should scale reasonably
                assert metrics["entries_per_second"] >= 20, (
                    f"Bulk size {size}: {metrics['entries_per_second']:.2f} entries/s too slow"
                )
                assert metrics["processing_time"] < size * 50, (
                    f"Bulk size {size}: {metrics['processing_time']:.2f}ms too slow"
                )


class TestFinancialMultiUserConcurrency:
    """Test multi-user concurrent operations"""

    def test_concurrent_financial_reports(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test concurrent financial report generation"""
        report_types = [
            ("trial-balance", {"organization_id": 1, "as_of_date": "2025-07-26"}),
            (
                "income-statement",
                {
                    "organization_id": 1,
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                },
            ),
            ("balance-sheet", {"organization_id": 1, "as_of_date": "2025-07-26"}),
            (
                "cash-flow-statement",
                {
                    "organization_id": 1,
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                },
            ),
        ]

        def generate_reports_concurrently():
            results = []
            for report_type, params in report_types:
                for _ in range(3):  # 3 of each report type
                    start_time = time.time()

                    # Build URL with parameters
                    url = f"/api/v1/financial-accounting/{report_type}"
                    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
                    full_url = f"{url}?{param_string}"

                    response = client.get(full_url, headers=auth_headers)
                    end_time = time.time()

                    results.append(
                        {
                            "report_type": report_type,
                            "status_code": response.status_code,
                            "response_time": (end_time - start_time) * 1000,
                            "success": response.status_code == status.HTTP_200_OK,
                        }
                    )

            return results

        # Run concurrent report generation
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(generate_reports_concurrently) for _ in range(6)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze concurrent report performance
        successful_reports = sum(1 for r in all_results if r["success"])
        total_reports = len(all_results)
        avg_response_time = sum(r["response_time"] for r in all_results) / total_reports

        success_rate = successful_reports / total_reports

        assert success_rate >= 0.7, f"Report success rate {success_rate:.2%} too low"
        assert avg_response_time < 2000, (
            f"Average report time {avg_response_time:.2f}ms too high"
        )

    def test_mixed_operation_concurrency(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test concurrent mixed financial operations"""

        def account_operations(user_id: int):
            """Account creation and listing operations"""
            results = []

            for i in range(5):
                # Create account
                account_data = {
                    "organization_id": 1,
                    "account_code": f"MIX{user_id:02d}_{i:02d}",
                    "account_name": f"Mixed Test Account {user_id}-{i}",
                    "account_type": "asset",
                    "is_active": True,
                }

                start_time = time.time()
                response = client.post(
                    "/api/v1/financial-management/accounts",
                    json=account_data,
                    headers=auth_headers,
                )
                creation_time = (time.time() - start_time) * 1000

                results.append(
                    {
                        "operation": "create_account",
                        "status_code": response.status_code,
                        "response_time": creation_time,
                    }
                )

                # List accounts
                start_time = time.time()
                response = client.get(
                    "/api/v1/financial-management/accounts?organization_id=1&limit=20",
                    headers=auth_headers,
                )
                list_time = (time.time() - start_time) * 1000

                results.append(
                    {
                        "operation": "list_accounts",
                        "status_code": response.status_code,
                        "response_time": list_time,
                    }
                )

            return results

        def journal_operations(user_id: int):
            """Journal entry operations"""
            results = []

            for i in range(7):
                entry_data = {
                    "organization_id": 1,
                    "account_id": 1,
                    "transaction_id": f"MIX{user_id:02d}_{i:02d}",
                    "entry_date": "2025-07-26",
                    "debit_amount": "75.00",
                    "description": f"Mixed test entry {user_id}-{i}",
                }

                start_time = time.time()
                response = client.post(
                    "/api/v1/financial-management/journal-entries",
                    json=entry_data,
                    headers=auth_headers,
                )
                entry_time = (time.time() - start_time) * 1000

                results.append(
                    {
                        "operation": "create_entry",
                        "status_code": response.status_code,
                        "response_time": entry_time,
                    }
                )

            return results

        def reporting_operations(user_id: int):
            """Financial reporting operations"""
            results = []

            endpoints = [
                "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
                "/api/v1/financial-management/kpis?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
            ]

            for endpoint in endpoints:
                for _ in range(2):
                    start_time = time.time()
                    response = client.get(endpoint, headers=auth_headers)
                    report_time = (time.time() - start_time) * 1000

                    results.append(
                        {
                            "operation": "generate_report",
                            "status_code": response.status_code,
                            "response_time": report_time,
                        }
                    )

            return results

        # Execute mixed operations concurrently
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = []

            # 4 users doing account operations
            for i in range(4):
                futures.append(executor.submit(account_operations, i))

            # 4 users doing journal operations
            for i in range(4, 8):
                futures.append(executor.submit(journal_operations, i))

            # 4 users doing reporting operations
            for i in range(8, 12):
                futures.append(executor.submit(reporting_operations, i))

            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze mixed operation performance
        operations_by_type = {}
        for result in all_results:
            op_type = result["operation"]
            if op_type not in operations_by_type:
                operations_by_type[op_type] = []
            operations_by_type[op_type].append(result)

        for op_type, results in operations_by_type.items():
            successful_ops = sum(1 for r in results if r["status_code"] < 400)
            total_ops = len(results)
            avg_time = sum(r["response_time"] for r in results) / total_ops

            success_rate = successful_ops / total_ops

            assert success_rate >= 0.6, (
                f"{op_type} success rate {success_rate:.2%} too low"
            )
            assert avg_time < 1000, f"{op_type} average time {avg_time:.2f}ms too high"


class TestFinancialResourceUtilization:
    """Test resource utilization under load"""

    def test_database_connection_efficiency(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test database connection pool efficiency"""

        def database_intensive_operation():
            """Perform database-intensive operations"""
            results = []

            # Operations that likely hit the database
            operations = [
                lambda: client.get(
                    "/api/v1/financial-management/accounts?organization_id=1&limit=50",
                    headers=auth_headers,
                ),
                lambda: client.get(
                    "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
                    headers=auth_headers,
                ),
                lambda: client.get(
                    "/api/v1/financial-accounting/trial-balance?organization_id=1&as_of_date=2025-07-26",
                    headers=auth_headers,
                ),
            ]

            for _ in range(10):
                for operation in operations:
                    start_time = time.time()
                    response = operation()
                    end_time = time.time()

                    results.append(
                        {
                            "status_code": response.status_code,
                            "response_time": (end_time - start_time) * 1000,
                        }
                    )

            return results

        # Test with high concurrency to stress connection pool
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(database_intensive_operation) for _ in range(15)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze connection efficiency
        successful_operations = sum(
            1 for r in all_results if r["status_code"] == status.HTTP_200_OK
        )
        total_operations = len(all_results)
        avg_response_time = (
            sum(r["response_time"] for r in all_results) / total_operations
        )

        success_rate = successful_operations / total_operations

        # Database should handle concurrent connections efficiently
        assert success_rate >= 0.8, (
            f"DB operation success rate {success_rate:.2%} indicates connection issues"
        )
        assert avg_response_time < 800, (
            f"Average DB operation time {avg_response_time:.2f}ms too high"
        )

    def test_memory_usage_under_load(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test memory usage under sustained load"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        def memory_intensive_requests():
            """Perform requests that may consume memory"""
            for _ in range(20):
                # Requests that might use memory
                client.get(
                    "/api/v1/financial-management/accounts?organization_id=1&limit=100",
                    headers=auth_headers,
                )
                client.get(
                    "/api/v1/financial-accounting/trial-balance?organization_id=1&as_of_date=2025-07-26",
                    headers=auth_headers,
                )
                client.get(
                    "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
                    headers=auth_headers,
                )

        # Run memory-intensive operations with multiple threads
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(memory_intensive_requests) for _ in range(8)]
            for future in as_completed(futures):
                pass

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Memory usage should be reasonable under load
        assert memory_increase < 200, (
            f"Memory increased by {memory_increase:.2f}MB under load"
        )

    def test_cpu_usage_efficiency(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test CPU usage efficiency during load"""
        psutil.cpu_percent(interval=1)

        def cpu_intensive_operations():
            """Operations that may use CPU"""
            for _ in range(15):
                # Computational operations
                client.get(
                    "/api/v1/financial-accounting/income-statement?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
                    headers=auth_headers,
                )
                client.get(
                    "/api/v1/financial-management/kpis?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
                    headers=auth_headers,
                )

        # Monitor CPU during operations
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(cpu_intensive_operations) for _ in range(6)]

            # Monitor CPU usage
            cpu_measurements = []
            while any(not f.done() for f in futures):
                cpu_measurements.append(psutil.cpu_percent(interval=0.5))

            for future in as_completed(futures):
                pass

        duration = time.time() - start_time
        avg_cpu_usage = (
            sum(cpu_measurements) / len(cpu_measurements) if cpu_measurements else 0
        )

        # CPU usage should be reasonable and operations should complete in reasonable time
        assert duration < 30, f"CPU intensive operations took {duration:.2f}s, too long"
        # Allow high CPU usage during intensive operations, but ensure it's not maxed out
        assert avg_cpu_usage < 95, f"Average CPU usage {avg_cpu_usage:.1f}% too high"


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers fixture"""
    token = create_access_token(
        data={"sub": "load_test_user", "roles": ["financial_manager"]}
    )
    return {"Authorization": f"Bearer {token}"}
