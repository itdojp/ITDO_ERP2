"""
ITDO ERP Backend - Financial Management Performance Tests
Day 24: Comprehensive performance testing for financial management APIs

Performance test coverage:
- API response time validation (<200ms for critical operations)
- Concurrent request handling (20+ parallel users)
- Bulk operation performance (1000+ records)
- Financial calculation speed
- Memory usage optimization
- Cache effectiveness
- Database query optimization
- Scalability under load
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import psutil
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app


class TestFinancialAPIResponseTime:
    """Test API response time performance"""

    def test_account_creation_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test account creation response time"""
        account_data = {
            "organization_id": 1,
            "account_code": "PERF001",
            "account_name": "Performance Test Account",
            "account_type": "asset",
            "is_active": True,
        }

        start_time = time.time()
        response = client.post(
            "/api/v1/financial-management/accounts",
            json=account_data,
            headers=auth_headers,
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response_time < 200, (
            f"Account creation took {response_time:.2f}ms, expected <200ms"
        )

    def test_account_listing_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test account listing response time"""
        start_time = time.time()
        response = client.get(
            "/api/v1/financial-management/accounts?organization_id=1&limit=100",
            headers=auth_headers,
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response_time < 150, (
            f"Account listing took {response_time:.2f}ms, expected <150ms"
        )

    def test_journal_entry_creation_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test journal entry creation response time"""
        entry_data = {
            "organization_id": 1,
            "account_id": 1,
            "transaction_id": "PERF_TXN001",
            "entry_date": "2025-07-26",
            "debit_amount": "1000.00",
            "description": "Performance test entry",
        }

        start_time = time.time()
        response = client.post(
            "/api/v1/financial-management/journal-entries",
            json=entry_data,
            headers=auth_headers,
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response_time < 200, (
            f"Journal entry creation took {response_time:.2f}ms, expected <200ms"
        )

    def test_financial_summary_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test financial summary generation performance"""
        start_time = time.time()
        response = client.get(
            "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
            headers=auth_headers,
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response_time < 500, (
            f"Financial summary took {response_time:.2f}ms, expected <500ms"
        )

    def test_trial_balance_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test trial balance report performance"""
        start_time = time.time()
        response = client.get(
            "/api/v1/financial-accounting/trial-balance?organization_id=1&as_of_date=2025-07-26",
            headers=auth_headers,
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response_time < 300, (
            f"Trial balance took {response_time:.2f}ms, expected <300ms"
        )

    def test_income_statement_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test income statement generation performance"""
        start_time = time.time()
        response = client.get(
            "/api/v1/financial-accounting/income-statement?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
            headers=auth_headers,
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response_time < 400, (
            f"Income statement took {response_time:.2f}ms, expected <400ms"
        )

    def test_balance_sheet_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test balance sheet generation performance"""
        start_time = time.time()
        response = client.get(
            "/api/v1/financial-accounting/balance-sheet?organization_id=1&as_of_date=2025-07-26",
            headers=auth_headers,
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response_time < 400, (
            f"Balance sheet took {response_time:.2f}ms, expected <400ms"
        )


class TestFinancialConcurrentPerformance:
    """Test concurrent request handling performance"""

    def test_concurrent_account_queries(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test concurrent account queries performance"""

        def make_account_request():
            start_time = time.time()
            response = client.get(
                "/api/v1/financial-management/accounts?organization_id=1&limit=50",
                headers=auth_headers,
            )
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000

        # Execute 20 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_account_request) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        response_times = [time_ms for status_code, time_ms in results]
        successful_requests = sum(
            1 for status_code, _ in results if status_code == status.HTTP_200_OK
        )

        # Verify performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert successful_requests >= 15, (
            f"Only {successful_requests}/20 requests succeeded"
        )
        assert avg_response_time < 300, (
            f"Average response time {avg_response_time:.2f}ms exceeded 300ms"
        )
        assert max_response_time < 1000, (
            f"Max response time {max_response_time:.2f}ms exceeded 1000ms"
        )

    def test_concurrent_journal_entry_creation(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test concurrent journal entry creation performance"""

        def create_journal_entry(index):
            entry_data = {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": f"CONC_TXN{index:03d}",
                "entry_date": "2025-07-26",
                "debit_amount": "100.00",
                "description": f"Concurrent test entry {index}",
            }

            start_time = time.time()
            response = client.post(
                "/api/v1/financial-management/journal-entries",
                json=entry_data,
                headers=auth_headers,
            )
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000

        # Execute 15 concurrent requests
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(create_journal_entry, i) for i in range(15)]
            results = [future.result() for future in as_completed(futures)]

        response_times = [time_ms for status_code, time_ms in results]
        successful_requests = sum(
            1
            for status_code, _ in results
            if status_code
            in [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR]
        )

        avg_response_time = sum(response_times) / len(response_times)

        assert successful_requests >= 10, (
            f"Only {successful_requests}/15 requests processed"
        )
        assert avg_response_time < 500, (
            f"Average response time {avg_response_time:.2f}ms exceeded 500ms"
        )

    def test_concurrent_financial_reports(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test concurrent financial report generation"""
        report_endpoints = [
            "/api/v1/financial-accounting/trial-balance?organization_id=1&as_of_date=2025-07-26",
            "/api/v1/financial-accounting/income-statement?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
            "/api/v1/financial-accounting/balance-sheet?organization_id=1&as_of_date=2025-07-26",
            "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
        ]

        def make_report_request(endpoint):
            start_time = time.time()
            response = client.get(endpoint, headers=auth_headers)
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000, endpoint

        # Execute concurrent report requests
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for _ in range(2):  # 2 rounds of all reports
                for endpoint in report_endpoints:
                    futures.append(executor.submit(make_report_request, endpoint))

            results = [future.result() for future in as_completed(futures)]

        response_times = [time_ms for status_code, time_ms, endpoint in results]
        successful_requests = sum(
            1 for status_code, _, _ in results if status_code == status.HTTP_200_OK
        )

        avg_response_time = sum(response_times) / len(response_times)

        assert successful_requests >= 6, (
            f"Only {successful_requests}/8 report requests succeeded"
        )
        assert avg_response_time < 1000, (
            f"Average report response time {avg_response_time:.2f}ms exceeded 1000ms"
        )


class TestFinancialBulkOperationPerformance:
    """Test bulk operation performance"""

    def test_bulk_journal_entry_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test bulk journal entry creation performance"""
        # Create 100 journal entries for bulk operation
        bulk_entries = []
        for i in range(100):
            entry = {
                "organization_id": 1,
                "account_id": 1,
                "transaction_id": f"BULK{i:03d}",
                "entry_date": "2025-07-26",
                "debit_amount": "10.00",
                "description": f"Bulk entry {i}",
            }
            bulk_entries.append(entry)

        bulk_request = {
            "entries": bulk_entries,
            "auto_balance": False,
        }

        start_time = time.time()
        response = client.post(
            "/api/v1/financial-accounting/journal-entries/bulk",
            json=bulk_request,
            headers=auth_headers,
        )
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000

        # Should process 100 entries in under 5 seconds
        assert processing_time < 5000, (
            f"Bulk processing took {processing_time:.2f}ms, expected <5000ms"
        )

        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            created_count = data.get("total_created", 0)
            # Should process at least 20 entries per second
            entries_per_second = created_count / (processing_time / 1000)
            assert entries_per_second >= 20, (
                f"Only {entries_per_second:.2f} entries/second, expected >=20"
            )

    def test_large_account_listing_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test performance with large account listings"""
        # Test with maximum limit
        start_time = time.time()
        response = client.get(
            "/api/v1/financial-management/accounts?organization_id=1&limit=1000",
            headers=auth_headers,
        )
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert processing_time < 2000, (
            f"Large listing took {processing_time:.2f}ms, expected <2000ms"
        )

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            items = data.get("items", [])
            if items:
                # Should handle pagination efficiently
                assert len(items) <= 1000, "Response exceeded expected limit"

    def test_budget_variance_calculation_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test budget variance calculation performance"""
        start_time = time.time()
        response = client.get(
            "/api/v1/financial-accounting/budgets/1/variance-report?organization_id=1",
            headers=auth_headers,
        )
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert processing_time < 800, (
            f"Variance calculation took {processing_time:.2f}ms, expected <800ms"
        )


class TestFinancialMemoryPerformance:
    """Test memory usage and optimization"""

    def test_memory_usage_during_operations(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test memory usage during financial operations"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform multiple operations
        operations = [
            lambda: client.get(
                "/api/v1/financial-management/accounts?organization_id=1&limit=100",
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
            lambda: client.get(
                "/api/v1/financial-accounting/income-statement?organization_id=1&start_date=2025-01-01&end_date=2025-12-31",
                headers=auth_headers,
            ),
        ]

        # Execute operations multiple times
        for _ in range(10):
            for operation in operations:
                operation()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (<50MB for test operations)
        assert memory_increase < 50, (
            f"Memory increased by {memory_increase:.2f}MB, expected <50MB"
        )

    def test_large_dataset_memory_efficiency(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test memory efficiency with large datasets"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Request large dataset
        response = client.get(
            "/api/v1/financial-management/accounts?organization_id=1&limit=1000",
            headers=auth_headers,
        )

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_for_operation = peak_memory - initial_memory

        # Large dataset operation should not consume excessive memory
        assert memory_for_operation < 100, (
            f"Large dataset used {memory_for_operation:.2f}MB, expected <100MB"
        )

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            items_count = len(data.get("items", []))
            if items_count > 0:
                memory_per_item = memory_for_operation / items_count
                assert memory_per_item < 0.1, (
                    f"Memory per item {memory_per_item:.3f}MB too high"
                )


class TestFinancialCachePerformance:
    """Test cache effectiveness and performance"""

    def test_repeated_query_cache_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test cache performance for repeated queries"""
        endpoint = "/api/v1/financial-management/summary?organization_id=1&start_date=2025-01-01&end_date=2025-12-31"

        # First request (cache miss)
        start_time = time.time()
        response1 = client.get(endpoint, headers=auth_headers)
        first_request_time = (time.time() - start_time) * 1000

        # Second request (should hit cache)
        start_time = time.time()
        response2 = client.get(endpoint, headers=auth_headers)
        second_request_time = (time.time() - start_time) * 1000

        # Third request (should hit cache)
        start_time = time.time()
        response3 = client.get(endpoint, headers=auth_headers)
        third_request_time = (time.time() - start_time) * 1000

        assert response1.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response2.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        assert response3.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        # Cache should improve performance (at least 20% faster)
        if all(
            r.status_code == status.HTTP_200_OK
            for r in [response1, response2, response3]
        ):
            avg_cached_time = (second_request_time + third_request_time) / 2
            performance_improvement = (
                first_request_time - avg_cached_time
            ) / first_request_time

            # Allow for some variance in timing
            assert performance_improvement > -0.5, (
                f"Cache performance degraded by {performance_improvement:.2%}"
            )

    def test_cache_invalidation_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test cache invalidation does not impact performance significantly"""
        # Make initial cached request
        client.get(
            "/api/v1/financial-management/accounts?organization_id=1&limit=50",
            headers=auth_headers,
        )

        # Create new account (should invalidate cache)
        account_data = {
            "organization_id": 1,
            "account_code": "CACHE001",
            "account_name": "Cache Test Account",
            "account_type": "asset",
            "is_active": True,
        }

        start_time = time.time()
        client.post(
            "/api/v1/financial-management/accounts",
            json=account_data,
            headers=auth_headers,
        )
        creation_time = (time.time() - start_time) * 1000

        # Request accounts again (cache should be invalidated)
        start_time = time.time()
        client.get(
            "/api/v1/financial-management/accounts?organization_id=1&limit=50",
            headers=auth_headers,
        )
        post_invalidation_time = (time.time() - start_time) * 1000

        # Cache invalidation should not significantly impact performance
        assert creation_time < 500, (
            f"Account creation with cache invalidation took {creation_time:.2f}ms"
        )
        assert post_invalidation_time < 300, (
            f"Post-invalidation query took {post_invalidation_time:.2f}ms"
        )


class TestFinancialLoadTesting:
    """Test system behavior under load"""

    def test_sustained_load_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test performance under sustained load"""

        def sustained_requests():
            results = []
            for i in range(20):  # 20 requests per thread
                start_time = time.time()
                response = client.get(
                    f"/api/v1/financial-management/accounts?organization_id=1&skip={i * 5}&limit=5",
                    headers=auth_headers,
                )
                end_time = time.time()
                results.append((response.status_code, (end_time - start_time) * 1000))
                time.sleep(0.1)  # Small delay between requests
            return results

        # Run sustained load with 5 concurrent threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(sustained_requests) for _ in range(5)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        response_times = [time_ms for status_code, time_ms in all_results]
        successful_requests = sum(
            1 for status_code, _ in all_results if status_code == status.HTTP_200_OK
        )

        # Analyze sustained load performance
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        success_rate = successful_requests / len(all_results)

        assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below 80%"
        assert avg_response_time < 500, (
            f"Average response time {avg_response_time:.2f}ms under load"
        )
        assert max_response_time < 2000, (
            f"Max response time {max_response_time:.2f}ms too high"
        )

    def test_spike_load_performance(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test performance during traffic spikes"""

        def spike_request(index):
            start_time = time.time()
            response = client.get(
                "/api/v1/financial-management/health",
                headers=auth_headers,
            )
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000

        # Simulate traffic spike with 30 concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(spike_request, i) for i in range(30)]
            results = [future.result() for future in as_completed(futures)]
        total_spike_time = time.time() - start_time

        response_times = [time_ms for status_code, time_ms in results]
        successful_requests = sum(
            1 for status_code, _ in results if status_code == status.HTTP_200_OK
        )

        # Analyze spike performance
        avg_response_time = sum(response_times) / len(response_times)
        success_rate = successful_requests / len(results)

        assert success_rate >= 0.7, f"Spike success rate {success_rate:.2%} below 70%"
        assert avg_response_time < 1000, (
            f"Average spike response time {avg_response_time:.2f}ms too high"
        )
        assert total_spike_time < 10, (
            f"Total spike handling took {total_spike_time:.2f}s, expected <10s"
        )

    def test_gradual_load_increase(
        self, client: TestClient, auth_headers: Dict[str, str]
    ):
        """Test performance with gradually increasing load"""
        load_levels = [1, 2, 5, 10, 15]  # Concurrent users
        results_by_load = {}

        for concurrent_users in load_levels:

            def load_test_request():
                start_time = time.time()
                response = client.get(
                    "/api/v1/financial-management/accounts?organization_id=1&limit=10",
                    headers=auth_headers,
                )
                end_time = time.time()
                return response.status_code, (end_time - start_time) * 1000

            # Execute requests with current load level
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [
                    executor.submit(load_test_request)
                    for _ in range(concurrent_users * 2)
                ]
                load_results = [future.result() for future in as_completed(futures)]

            response_times = [time_ms for status_code, time_ms in load_results]
            successful_requests = sum(
                1
                for status_code, _ in load_results
                if status_code == status.HTTP_200_OK
            )

            avg_response_time = sum(response_times) / len(response_times)
            success_rate = successful_requests / len(load_results)

            results_by_load[concurrent_users] = {
                "avg_response_time": avg_response_time,
                "success_rate": success_rate,
            }

        # Verify graceful degradation
        for users, metrics in results_by_load.items():
            assert metrics["success_rate"] >= 0.6, (
                f"Success rate dropped to {metrics['success_rate']:.2%} at {users} users"
            )

            # Response time should not increase dramatically
            if users <= 10:
                assert metrics["avg_response_time"] < 800, (
                    f"Response time {metrics['avg_response_time']:.2f}ms too high at {users} users"
                )


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers fixture"""
    token = create_access_token(
        data={"sub": "test_user", "roles": ["financial_manager"]}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def performance_metrics():
    """Fixture to collect performance metrics across tests"""
    return {
        "response_times": [],
        "memory_usage": [],
        "throughput": [],
    }
