"""Integration tests for health endpoints"""

import asyncio
import time

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_basic(self, client: AsyncClient):
        """Test basic health endpoint functionality."""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client: AsyncClient):
        """Test health endpoint response time."""
        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Under 100ms

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint functionality."""
        response = await client.get("/metrics")

        # Should return Prometheus metrics format
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client: AsyncClient):
        """Test health endpoint under concurrent load."""

        async def single_health_check():
            response = await client.get("/health")
            return response.status_code == 200

        # Run 50 concurrent health checks
        tasks = [single_health_check() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)

    @pytest.mark.asyncio
    async def test_health_endpoint_detailed(self, client: AsyncClient):
        """Test detailed health endpoint."""
        response = await client.get("/health/detailed")

        if response.status_code == 200:
            data = response.json()
            # Should include database, redis, etc. status
            assert "database" in data or "components" in data

    @pytest.mark.asyncio
    async def test_readiness_probe(self, client: AsyncClient):
        """Test Kubernetes readiness probe."""
        response = await client.get("/ready")

        # Should be available for K8s readiness checks
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_liveness_probe(self, client: AsyncClient):
        """Test Kubernetes liveness probe."""
        response = await client.get("/health")

        # Should always respond for liveness checks
        assert response.status_code == 200
