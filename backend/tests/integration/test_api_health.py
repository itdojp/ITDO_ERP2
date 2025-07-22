import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

class TestAPIPerformance:
    """Test API performance and health under load."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient):
        """Test API can handle concurrent requests."""
        async def make_request():
            response = await client.get("/api/v1/health")
            return response.status_code, response.elapsed.total_seconds()

        # 100 concurrent requests
        tasks = [make_request() for _ in range(100)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # All requests should succeed
        status_codes = [r[0] for r in results]
        assert all(code == 200 for code in status_codes)

        # Average response time should be under 100ms
        response_times = [r[1] for r in results]
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.1

        # Total time for 100 requests should be under 2 seconds
        assert total_time < 2.0

    @pytest.mark.asyncio
    async def test_database_connection_pool(self, client: AsyncClient, db_session: AsyncSession):
        """Test database connection pooling."""
        async def query_database():
            result = await db_session.execute("SELECT 1")
            return result.scalar()

        # 50 concurrent database queries
        tasks = [query_database() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        assert all(r == 1 for r in results)

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client: AsyncClient):
        """Test health endpoint response time."""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.elapsed.total_seconds() < 0.05  # Under 50ms

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, client: AsyncClient):
        """Test memory usage remains stable under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make 1000 requests
        for _ in range(1000):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / initial_memory
        
        # Memory should not increase by more than 10%
        assert memory_increase < 0.1