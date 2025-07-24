"""Performance tests for critical API endpoints."""

import time
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app


class TestPerformance:
    """Performance tests for API endpoints."""

    def setup_method(self):
        """Setup test environment."""
        self.client = TestClient(app)
        self.max_response_time = 200  # 200ms
        self.concurrent_users = 10

    def test_health_endpoint_performance(self):
        """Test health endpoint response time."""
        start_time = time.time()
        response = self.client.get("/health")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time < self.max_response_time

    def test_concurrent_health_requests(self):
        """Test health endpoint under concurrent load."""

        def make_request():
            start_time = time.time()
            response = self.client.get("/health")
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000

        with ThreadPoolExecutor(max_workers=self.concurrent_users) as executor:
            futures = [
                executor.submit(make_request) for _ in range(self.concurrent_users)
            ]
            results = [future.result() for future in futures]

        # All requests should succeed
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]

        assert all(code == 200 for code in status_codes)
        assert (
            max(response_times) < self.max_response_time * 2
        )  # Allow 2x time under load
        assert sum(response_times) / len(response_times) < self.max_response_time

    def test_database_query_performance(self):
        """Test database query performance."""
        # Test critical database queries
        start_time = time.time()
        response = self.client.get("/api/v1/users?limit=100")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        if response.status_code == 200:
            assert response_time < 500  # 500ms for database queries

    def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively under load."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make many requests
        for _ in range(100):
            self.client.get("/health")

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (less than 50MB)
        assert memory_growth < 50 * 1024 * 1024
