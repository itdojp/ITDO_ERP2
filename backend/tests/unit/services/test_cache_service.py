"""Tests for cache service."""

import json
import pickle
import time
from unittest.mock import MagicMock, patch

import pytest
import redis

from app.services.cache import (
    CacheKeyBuilder,
    CacheService,
    CacheStatistics,
    cache_invalidate,
    cached,
    get_cache_service,
    initialize_cache_service,
)


class TestCacheKeyBuilder:
    """Test cases for CacheKeyBuilder."""

    def test_build_key_simple(self) -> None:
        """Test simple key building."""
        key = CacheKeyBuilder.build_key("user", 123)
        assert key == "cache:user:123"

    def test_build_key_with_prefix(self) -> None:
        """Test key building with custom prefix."""
        key = CacheKeyBuilder.build_key("user", 123, prefix="session")
        assert key == "session:user:123"

    def test_build_key_multiple_args(self) -> None:
        """Test key building with multiple arguments."""
        key = CacheKeyBuilder.build_key("user", 123, "profile", "preferences")
        assert key == "cache:user:123:profile:preferences"

    def test_build_pattern(self) -> None:
        """Test pattern building."""
        pattern = CacheKeyBuilder.build_pattern("user")
        assert pattern == "user:*"

    def test_build_pattern_custom(self) -> None:
        """Test pattern building with custom pattern."""
        pattern = CacheKeyBuilder.build_pattern("user", "123*")
        assert pattern == "user:123*"


class TestCacheStatistics:
    """Test cases for CacheStatistics."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create mock Redis client."""
        return MagicMock()

    @pytest.fixture
    def stats(self, mock_redis: MagicMock) -> CacheStatistics:
        """Create CacheStatistics instance."""
        return CacheStatistics(mock_redis)

    def test_increment_hits(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test incrementing hit counter."""
        stats.increment_hits("test_key")

        mock_redis.hincrby.assert_any_call("cache:stats", "hits", 1)
        mock_redis.hincrby.assert_any_call("cache:stats", "key_hits:test_key", 1)

    def test_increment_misses(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test incrementing miss counter."""
        stats.increment_misses("test_key")

        mock_redis.hincrby.assert_any_call("cache:stats", "misses", 1)
        mock_redis.hincrby.assert_any_call("cache:stats", "key_misses:test_key", 1)

    def test_increment_sets(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test incrementing set counter."""
        stats.increment_sets("test_key")

        mock_redis.hincrby.assert_any_call("cache:stats", "sets", 1)
        mock_redis.hincrby.assert_any_call("cache:stats", "key_sets:test_key", 1)

    def test_increment_deletes(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test incrementing delete counter."""
        stats.increment_deletes("test_key")

        mock_redis.hincrby.assert_any_call("cache:stats", "deletes", 1)
        mock_redis.hincrby.assert_any_call("cache:stats", "key_deletes:test_key", 1)

    def test_get_statistics(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test getting statistics."""
        mock_redis.hgetall.return_value = {
            "hits": "100",
            "misses": "20",
            "sets": "90",
            "deletes": "10",
        }

        result = stats.get_statistics()

        assert result["hits"] == 100
        assert result["misses"] == 20
        assert result["total_requests"] == 120
        assert result["hit_rate"] == 100 / 120 * 100  # hits/total * 100
        assert result["miss_rate"] == 20 / 120 * 100  # misses/total * 100

    def test_get_statistics_empty(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test getting statistics when empty."""
        mock_redis.hgetall.return_value = {}

        result = stats.get_statistics()

        assert result["total_requests"] == 0
        assert result["hit_rate"] == 0
        assert result["miss_rate"] == 0

    def test_get_statistics_error(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test getting statistics with error."""
        mock_redis.hgetall.side_effect = redis.RedisError("Connection failed")

        result = stats.get_statistics()

        assert result == {}

    def test_reset_statistics(
        self, stats: CacheStatistics, mock_redis: MagicMock
    ) -> None:
        """Test resetting statistics."""
        stats.reset_statistics()

        mock_redis.delete.assert_called_once_with("cache:stats")


class TestCacheService:
    """Test cases for CacheService."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create mock Redis client."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        return mock_client

    @pytest.fixture
    def cache_service(self, mock_redis: MagicMock) -> CacheService:
        """Create CacheService instance with mocked Redis."""
        with patch("app.services.cache.redis.Redis", return_value=mock_redis):
            service = CacheService()
        return service

    def test_init_success(self, mock_redis: MagicMock) -> None:
        """Test successful initialization."""
        with patch("app.services.cache.redis.Redis", return_value=mock_redis):
            service = CacheService()
            assert service.redis_client is not None
            assert service.statistics is not None

    def test_init_redis_failure(self) -> None:
        """Test initialization with Redis connection failure."""
        with patch("app.services.cache.redis.Redis") as mock_redis_class:
            mock_redis_class.side_effect = redis.RedisError("Connection failed")
            service = CacheService()
            assert service.redis_client is None
            assert service.statistics is None

    def test_get_existing_json(self, cache_service: CacheService) -> None:
        """Test getting existing JSON value from cache."""
        test_data = {"key": "value", "number": 123}
        cache_service.redis_client.get.return_value = json.dumps(test_data)

        result = cache_service.get("test_key")

        assert result == test_data
        cache_service.redis_client.get.assert_called_once_with("test_key")

    def test_get_existing_pickle(self, cache_service: CacheService) -> None:
        """Test getting existing pickled value from cache."""
        test_data = {"complex": "simple_object"}  # Simple data for pickling
        pickled_data = pickle.dumps(test_data).decode("latin-1")
        cache_service.redis_client.get.return_value = pickled_data

        result = cache_service.get("test_key")

        # Should return the unpickled data
        assert result == test_data

    def test_get_nonexistent(self, cache_service: CacheService) -> None:
        """Test getting non-existent key."""
        cache_service.redis_client.get.return_value = None

        result = cache_service.get("test_key", default="default_value")

        assert result == "default_value"

    def test_get_no_redis(self) -> None:
        """Test getting value when Redis is not available."""
        service = CacheService()  # No Redis connection
        result = service.get("test_key", default="default")
        assert result == "default"

    def test_set_json_success(self, cache_service: CacheService) -> None:
        """Test setting JSON value in cache."""
        test_data = {"key": "value", "number": 123}
        cache_service.redis_client.setex.return_value = True

        result = cache_service.set("test_key", test_data, ttl=300)

        assert result is True
        cache_service.redis_client.setex.assert_called_once_with(
            "test_key", 300, json.dumps(test_data, default=str)
        )

    def test_set_pickle_fallback(self, cache_service: CacheService) -> None:
        """Test setting value with pickle fallback."""
        # Create an object that can't be JSON serialized
        test_data = object()
        cache_service.redis_client.setex.return_value = True

        result = cache_service.set("test_key", test_data, ttl=300)

        assert result is True
        # Should use pickle when JSON fails
        cache_service.redis_client.setex.assert_called_once()

    def test_set_no_redis(self) -> None:
        """Test setting value when Redis is not available."""
        service = CacheService()  # No Redis connection
        result = service.set("test_key", "value")
        assert result is False

    def test_delete_success(self, cache_service: CacheService) -> None:
        """Test deleting key from cache."""
        cache_service.redis_client.delete.return_value = 1

        result = cache_service.delete("test_key")

        assert result is True
        cache_service.redis_client.delete.assert_called_once_with("test_key")

    def test_delete_nonexistent(self, cache_service: CacheService) -> None:
        """Test deleting non-existent key."""
        cache_service.redis_client.delete.return_value = 0

        result = cache_service.delete("test_key")

        assert result is False

    def test_delete_pattern(self, cache_service: CacheService) -> None:
        """Test deleting keys by pattern."""
        cache_service.redis_client.keys.return_value = ["key1", "key2", "key3"]
        cache_service.redis_client.delete.return_value = 3

        result = cache_service.delete_pattern("test:*")

        assert result == 3
        cache_service.redis_client.keys.assert_called_once_with("test:*")
        cache_service.redis_client.delete.assert_called_once_with(
            "key1", "key2", "key3"
        )

    def test_exists_true(self, cache_service: CacheService) -> None:
        """Test checking if key exists (exists)."""
        cache_service.redis_client.exists.return_value = 1

        result = cache_service.exists("test_key")

        assert result is True

    def test_exists_false(self, cache_service: CacheService) -> None:
        """Test checking if key exists (doesn't exist)."""
        cache_service.redis_client.exists.return_value = 0

        result = cache_service.exists("test_key")

        assert result is False

    def test_expire(self, cache_service: CacheService) -> None:
        """Test setting expiration for key."""
        cache_service.redis_client.expire.return_value = True

        result = cache_service.expire("test_key", 300)

        assert result is True
        cache_service.redis_client.expire.assert_called_once_with("test_key", 300)

    def test_ttl(self, cache_service: CacheService) -> None:
        """Test getting TTL for key."""
        cache_service.redis_client.ttl.return_value = 300

        result = cache_service.ttl("test_key")

        assert result == 300

    def test_invalidate_pattern(self, cache_service: CacheService) -> None:
        """Test invalidating cache by pattern."""
        cache_service.redis_client.keys.return_value = ["user:1", "user:2"]
        cache_service.redis_client.delete.return_value = 2

        result = cache_service.invalidate_pattern("user")

        assert result == 2
        cache_service.redis_client.keys.assert_called_once_with("user:*")

    def test_warm_cache_success(self, cache_service: CacheService) -> None:
        """Test cache warming with successful functions."""

        def warm_func1():
            cache_service.set("warm1", "value1")

        def warm_func2():
            cache_service.set("warm2", "value2")

        result = cache_service.warm_cache([warm_func1, warm_func2])

        assert result["success"] == 2
        assert result["failed"] == 0
        assert result["errors"] == []

    def test_warm_cache_with_errors(self, cache_service: CacheService) -> None:
        """Test cache warming with some failing functions."""

        def warm_func_success():
            cache_service.set("warm1", "value1")

        def warm_func_error():
            raise ValueError("Test error")

        result = cache_service.warm_cache([warm_func_success, warm_func_error])

        assert result["success"] == 1
        assert result["failed"] == 1
        assert len(result["errors"]) == 1
        assert "warm_func_error: Test error" in result["errors"][0]

    def test_get_cache_info(self, cache_service: CacheService) -> None:
        """Test getting cache information."""
        cache_service.redis_client.info.return_value = {
            "used_memory_human": "1.5M",
            "connected_clients": 10,
            "keyspace_hits": 1000,
            "keyspace_misses": 100,
        }

        result = cache_service.get_cache_info()

        assert result["status"] == "connected"
        assert result["redis_info"]["used_memory"] == "1.5M"
        assert result["redis_info"]["connected_clients"] == 10

    def test_flush_all(self, cache_service: CacheService) -> None:
        """Test flushing all cache data."""
        result = cache_service.flush_all()

        assert result is True
        cache_service.redis_client.flushdb.assert_called_once()


class TestCacheDecorators:
    """Test cases for cache decorators."""

    @pytest.fixture
    def mock_cache_service(self) -> MagicMock:
        """Create mock cache service."""
        mock_service = MagicMock()
        mock_service.key_builder.build_key.return_value = "cache:test:key"
        return mock_service

    def test_cached_decorator_cache_hit(self, mock_cache_service: MagicMock) -> None:
        """Test cached decorator with cache hit."""
        mock_cache_service.get.return_value = "cached_result"

        with patch(
            "app.services.cache.get_cache_service", return_value=mock_cache_service
        ):

            @cached(key_prefix="test")
            def test_function(arg1: str, arg2: int) -> str:
                return f"result_{arg1}_{arg2}"

            result = test_function("hello", 123)

        assert result == "cached_result"
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_not_called()

    def test_cached_decorator_cache_miss(self, mock_cache_service: MagicMock) -> None:
        """Test cached decorator with cache miss."""
        mock_cache_service.get.return_value = None

        with patch(
            "app.services.cache.get_cache_service", return_value=mock_cache_service
        ):

            @cached(key_prefix="test", ttl=300)
            def test_function(arg1: str, arg2: int) -> str:
                return f"result_{arg1}_{arg2}"

            result = test_function("hello", 123)

        assert result == "result_hello_123"
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once_with(
            "cache:test:key", "result_hello_123", ttl=300
        )

    def test_cache_invalidate_decorator(self, mock_cache_service: MagicMock) -> None:
        """Test cache invalidate decorator."""
        with patch(
            "app.services.cache.get_cache_service", return_value=mock_cache_service
        ):

            @cache_invalidate(key_prefix="test")
            def test_function() -> str:
                return "result"

            result = test_function()

        assert result == "result"
        mock_cache_service.invalidate_pattern.assert_called_once_with("test")


class TestCacheServiceSingleton:
    """Test cases for cache service singleton functions."""

    def test_get_cache_service(self) -> None:
        """Test getting cache service instance."""
        # Reset global instance
        import app.services.cache

        app.services.cache._cache_service = None

        service1 = get_cache_service()
        service2 = get_cache_service()

        assert service1 is service2  # Should be the same instance

    def test_initialize_cache_service(self) -> None:
        """Test initializing cache service with custom config."""
        with patch("app.services.cache.CacheService") as mock_service_class:
            mock_instance = MagicMock()
            mock_service_class.return_value = mock_instance

            result = initialize_cache_service("redis://localhost:6379/2")

            assert result is mock_instance
            mock_service_class.assert_called_once_with("redis://localhost:6379/2")


class TestCachePerformance:
    """Performance tests for cache service."""

    @pytest.fixture
    def cache_service_no_redis(self) -> CacheService:
        """Create cache service without Redis for performance testing."""
        return CacheService()

    def test_cache_operations_without_redis(
        self, cache_service_no_redis: CacheService
    ) -> None:
        """Test that cache operations are fast when Redis is not available."""
        start_time = time.time()

        # Perform multiple operations
        for i in range(100):
            cache_service_no_redis.get(f"key_{i}")
            cache_service_no_redis.set(f"key_{i}", f"value_{i}")
            cache_service_no_redis.delete(f"key_{i}")

        end_time = time.time()
        duration = end_time - start_time

        # Should be very fast since no actual Redis operations
        assert duration < 0.1  # Less than 100ms for 300 operations

    def test_key_building_performance(self) -> None:
        """Test key building performance."""
        builder = CacheKeyBuilder()
        start_time = time.time()

        # Build many keys
        for i in range(1000):
            builder.build_key("user", i, "profile", "data")

        end_time = time.time()
        duration = end_time - start_time

        # Should be very fast
        assert duration < 0.1  # Less than 100ms for 1000 key builds
