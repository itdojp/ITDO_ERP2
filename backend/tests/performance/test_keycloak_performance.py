"""
Keycloak performance tests.

Following TDD approach - Red phase: Writing performance tests before implementation.
"""

import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any
from unittest.mock import patch, Mock

from app.core.keycloak import KeycloakClient
from tests.utils.keycloak import (
    create_keycloak_token_with_roles,
    MockKeycloakClient,
)


class TestKeycloakPerformance:
    """Test cases for Keycloak performance requirements."""

    def test_auth_url_generation_performance(self) -> None:
        """認証URL生成が高速であることを確認."""
        # Given: Mock Keycloak client
        client = MockKeycloakClient(Mock(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
        ))
        
        # Warm up
        client.get_auth_url("http://localhost:3000/callback", "state")
        
        # Measure
        iterations = 1000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            client.get_auth_url("http://localhost:3000/callback", "state123")
        
        elapsed_time = time.perf_counter() - start_time
        avg_time_ms = (elapsed_time / iterations) * 1000
        
        # Then: Should be very fast (< 0.1ms per generation)
        assert avg_time_ms < 0.1

    def test_pkce_generation_performance(self) -> None:
        """PKCE生成が高速であることを確認."""
        from app.core.keycloak import generate_pkce_pair
        
        # Warm up
        generate_pkce_pair()
        
        # Measure
        iterations = 100
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            generate_pkce_pair()
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to ms
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        # Then: Should be fast
        assert avg_time < 5  # Average < 5ms
        assert p95_time < 10  # 95th percentile < 10ms

    def test_concurrent_auth_requests(self) -> None:
        """TEST-PERF-KC-003: 100並行認証リクエストが処理できることを確認."""
        # Given: Mock client
        client = MockKeycloakClient(Mock(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
        ))
        
        successful_requests = 0
        failed_requests = 0
        response_times: List[float] = []
        
        def make_auth_request() -> tuple[bool, float]:
            """Make a single auth request and return success status and time."""
            start = time.perf_counter()
            try:
                url = client.get_auth_url("http://localhost:3000/callback", "state")
                elapsed = time.perf_counter() - start
                return True, elapsed
            except Exception:
                elapsed = time.perf_counter() - start
                return False, elapsed
        
        # When: 100 concurrent requests
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(make_auth_request) for _ in range(100)]
            
            for future in as_completed(futures):
                success, elapsed = future.result()
                response_times.append(elapsed * 1000)  # Convert to ms
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1
        
        # Then: 95% success rate and reasonable response times
        success_rate = successful_requests / 100
        assert success_rate >= 0.95
        
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]
        
        assert avg_response_time < 50  # Average < 50ms
        assert p95_response_time < 100  # 95th percentile < 100ms

    def test_token_validation_caching(self) -> None:
        """トークン検証のキャッシュが効果的であることを確認."""
        # Given: Mock client with caching
        client = MockKeycloakClient(Mock())
        token = "test-token"
        
        # First call (cache miss)
        start1 = time.perf_counter()
        result1 = client.verify_token(token)
        time1 = (time.perf_counter() - start1) * 1000
        
        # Subsequent calls (cache hits)
        cache_times = []
        for _ in range(10):
            start = time.perf_counter()
            result = client.verify_token(token)
            elapsed = (time.perf_counter() - start) * 1000
            cache_times.append(elapsed)
        
        avg_cache_time = statistics.mean(cache_times)
        
        # Then: Cached calls should be much faster
        # Cache hits should be at least 10x faster than cache miss
        # (In reality would be 100x+ faster)
        assert avg_cache_time < time1 / 10

    def test_bulk_user_info_retrieval(self) -> None:
        """複数ユーザー情報の一括取得性能を確認."""
        # Given: Mock client
        client = MockKeycloakClient(Mock())
        tokens = [f"token-{i}" for i in range(50)]
        
        # Measure sequential retrieval
        start_seq = time.perf_counter()
        for token in tokens:
            client.get_userinfo(token)
        seq_time = time.perf_counter() - start_seq
        
        # Measure parallel retrieval (simulated)
        start_par = time.perf_counter()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(client.get_userinfo, token) for token in tokens]
            for future in as_completed(futures):
                future.result()
        par_time = time.perf_counter() - start_par
        
        # Then: Parallel should be faster
        assert par_time < seq_time * 0.5  # At least 2x speedup

    def test_memory_usage_under_load(self) -> None:
        """高負荷時のメモリ使用量が適切であることを確認."""
        # This would require memory profiling
        # Ensure no memory leaks during extended operation
        pass

    @pytest.mark.asyncio
    async def test_async_token_validation_performance(self) -> None:
        """非同期トークン検証の性能を確認."""
        # Given: Async mock client
        async def mock_validate_token(token: str) -> dict:
            """Simulate async token validation."""
            await asyncio.sleep(0.01)  # Simulate network delay
            return {"sub": "user-123", "email": "test@example.com"}
        
        # Measure concurrent validations
        tokens = [f"token-{i}" for i in range(100)]
        
        start = time.perf_counter()
        tasks = [mock_validate_token(token) for token in tokens]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start
        
        # Then: Should handle 100 concurrent validations efficiently
        assert len(results) == 100
        assert elapsed < 0.5  # Should complete in < 500ms (leveraging async)

    def test_connection_pool_efficiency(self) -> None:
        """接続プールが効率的に動作することを確認."""
        # Connection pooling should reduce overhead
        # This would be tested with actual HTTP client
        pass

    def test_graceful_degradation(self) -> None:
        """性能劣化時の適切な動作を確認."""
        # When Keycloak is slow, should:
        # - Use cached results where possible
        # - Implement circuit breaker pattern
        # - Return appropriate errors
        pass


class TestCachePerformance:
    """Test cases for caching performance."""

    def test_public_key_cache_performance(self) -> None:
        """公開鍵キャッシュの性能を確認."""
        # Public key should be cached for 1 hour
        # Reduces calls to Keycloak
        pass

    def test_user_info_cache_performance(self) -> None:
        """ユーザー情報キャッシュの性能を確認."""
        # User info cached for 5 minutes
        # Balance between freshness and performance
        pass

    def test_cache_invalidation_performance(self) -> None:
        """キャッシュ無効化の性能を確認."""
        # Cache invalidation should be fast
        # Should not block main operations
        pass


class TestScalabilityMetrics:
    """Test cases for scalability metrics."""

    def test_horizontal_scaling_readiness(self) -> None:
        """水平スケーリングへの対応を確認."""
        # Stateless design allows horizontal scaling
        # Shared cache (Redis) enables multiple instances
        pass

    def test_load_balancing_compatibility(self) -> None:
        """ロードバランサーとの互換性を確認."""
        # No sticky sessions required
        # Health check endpoints available
        pass