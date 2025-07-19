"""Cache service implementation for Redis-based caching layer.

This module provides a comprehensive caching solution with:
- Redis-based storage
- Cache invalidation strategies
- Cache warming functionality
- Statistics tracking
- Decorator for easy integration
"""

import functools
import json
import logging
import pickle
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

import redis
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# Type variable for generic decorator support
T = TypeVar("T")


class CacheKeyBuilder:
    """Helper class for building consistent cache keys."""

    @staticmethod
    def build_key(*args: Union[str, int], prefix: str = "cache") -> str:
        """Build a cache key from components."""
        key_parts = [str(prefix)]
        key_parts.extend(str(arg) for arg in args)
        return ":".join(key_parts)

    @staticmethod
    def build_pattern(prefix: str, pattern: str = "*") -> str:
        """Build a pattern for key matching."""
        return f"{prefix}:{pattern}"


class CacheStatistics:
    """Cache statistics tracking."""

    def __init__(self, redis_client: redis.Redis):
        """Initialize statistics tracking."""
        self.redis_client = redis_client
        self.stats_key = "cache:stats"

    def increment_hits(self, cache_key: str) -> None:
        """Increment cache hit counter."""
        self._increment_stat("hits")
        self._increment_stat(f"key_hits:{cache_key}")

    def increment_misses(self, cache_key: str) -> None:
        """Increment cache miss counter."""
        self._increment_stat("misses")
        self._increment_stat(f"key_misses:{cache_key}")

    def increment_sets(self, cache_key: str) -> None:
        """Increment cache set counter."""
        self._increment_stat("sets")
        self._increment_stat(f"key_sets:{cache_key}")

    def increment_deletes(self, cache_key: str) -> None:
        """Increment cache delete counter."""
        self._increment_stat("deletes")
        self._increment_stat(f"key_deletes:{cache_key}")

    def _increment_stat(self, stat_name: str) -> None:
        """Increment a statistic counter."""
        try:
            self.redis_client.hincrby(self.stats_key, stat_name, 1)
        except Exception as e:
            logger.warning(f"Failed to update cache statistics: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = self.redis_client.hgetall(self.stats_key) if hasattr(self.redis_client, 'hgetall') else {}
            if not isinstance(stats, dict):
                stats = {}

            # Convert byte strings to proper types
            processed_stats = {}
            for key, value in stats.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if isinstance(value, bytes):
                    value = value.decode('utf-8')

                # Convert numeric values
                try:
                    processed_stats[key] = int(value)
                except ValueError:
                    processed_stats[key] = value

            # Calculate derived statistics
            hits = processed_stats.get("hits", 0)
            misses = processed_stats.get("misses", 0)
            total_requests = hits + misses

            processed_stats["total_requests"] = total_requests
            processed_stats["hit_rate"] = (
                int(hits / total_requests * 100) if total_requests > 0 else 0
            )
            processed_stats["miss_rate"] = (
                int(misses / total_requests * 100) if total_requests > 0 else 0
            )

            return processed_stats
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {}

    def reset_statistics(self) -> None:
        """Reset all cache statistics."""
        try:
            self.redis_client.delete(self.stats_key)
            logger.info("Cache statistics reset")
        except Exception as e:
            logger.error(f"Failed to reset cache statistics: {e}")


class CacheService:
    """Redis-based caching service with advanced features."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache service."""
        self.redis_client = self._get_redis_client(redis_url)
        self.key_builder = CacheKeyBuilder()
        self.statistics = (
            CacheStatistics(self.redis_client) if self.redis_client else None
        )
        self.default_ttl = getattr(settings, "CACHE_DEFAULT_TTL", 3600)

    def _get_redis_client(
        self, redis_url: Optional[str] = None
    ) -> Optional[redis.Redis]:
        """Get Redis client connection."""
        try:
            if redis_url:
                client = redis.from_url(redis_url, decode_responses=True)  # type: ignore[no-untyped-call]
            else:
                client = redis.Redis(
                    host=getattr(settings, "REDIS_HOST", "localhost"),
                    port=getattr(settings, "REDIS_PORT", 6379),
                    db=getattr(settings, "REDIS_CACHE_DB", 1),
                    decode_responses=True,
                )

            # Test connection
            client.ping()
            logger.info("Redis cache connection established")
            return client  # type: ignore[no-any-return]
        except Exception as e:
            logger.warning(f"Redis cache connection failed: {e}")
            return None

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if not self.redis_client:
            return default

        try:
            value = cast(str, self.redis_client.get(key))
            if value is not None:
                if self.statistics:
                    self.statistics.increment_hits(key)

                # Try to deserialize JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        return pickle.loads(cast(str, value).encode('latin-1'))
                    except Exception:
                        return value
            else:
                if self.statistics:
                    self.statistics.increment_misses(key)
                return default

        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            if self.statistics:
                self.statistics.increment_misses(key)
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize_json: bool = True
    ) -> bool:
        """Set value in cache with optional TTL."""
        if not self.redis_client:
            return False

        try:
            # Serialize the value
            if serialize_json:
                try:
                    serialized_value = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    # Fall back to pickle for complex objects
                    serialized_value = pickle.dumps(value).decode('latin-1')
                    serialize_json = False
            else:
                if isinstance(value, (dict, list)):
                    serialized_value = pickle.dumps(value).decode('latin-1')
                else:
                    serialized_value = str(value)

            # Set with TTL
            cache_ttl = ttl or self.default_ttl
            success = self.redis_client.setex(key, cache_ttl, serialized_value)

            if success and self.statistics:
                self.statistics.increment_sets(key)

            return bool(success)

        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False

        try:
            result = self.redis_client.delete(key)
            if result and self.statistics:
                self.statistics.increment_deletes(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = cast(int, self.redis_client.delete(*cast(list[str], keys)))
                if self.statistics:
                    for key in cast(list[str], keys):
                        self.statistics.increment_deletes(key)
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"Failed to delete cache pattern {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key existence {key}: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        if not self.redis_client:
            return -1

        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key {key}: {e}")
            return -1

    def invalidate_pattern(self, prefix: str) -> int:
        """Invalidate all cache keys with a given prefix."""
        pattern = self.key_builder.build_pattern(prefix)
        return self.delete_pattern(pattern)

    def warm_cache(self, warming_functions: List[Callable]) -> Dict[str, Any]:
        """Warm cache with predefined data."""
        results = {"success": 0, "failed": 0, "errors": []}

        for func in warming_functions:
            try:
                func()
                results["success"] += 1
                logger.info(f"Cache warming function {func.__name__} completed")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{func.__name__}: {str(e)}")
                logger.error(f"Cache warming function {func.__name__} failed: {e}")

        return results

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information and statistics."""
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            stats = self.statistics.get_statistics() if self.statistics else {}

            return {
                "status": "connected",
                "redis_info": {
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                },
                "cache_statistics": stats,
                "default_ttl": self.default_ttl,
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {"status": "error", "error": str(e)}

    def flush_all(self) -> bool:
        """Flush all cache data (use with caution)."""
        if not self.redis_client:
            return False

        try:
            self.redis_client.flushdb()
            logger.warning("Cache flushed - all data cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to flush cache: {e}")
            return False


# Cache decorators for easy integration

def cached(
    key_prefix: str = "cache",
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None,
) -> Callable:
    """Decorator to cache function results.

    Args:
        key_prefix: Prefix for cache keys
        ttl: Time to live in seconds
        key_builder: Custom function to build cache key from function args
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache_service()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key building
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = cache.key_builder.build_key(*key_parts, prefix=key_prefix)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


def cache_invalidate(key_prefix: str) -> Callable:
    """Decorator to invalidate cache with given prefix after function execution."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = func(*args, **kwargs)

            cache = get_cache_service()
            cache.invalidate_pattern(key_prefix)

            return result
        return wrapper
    return decorator


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def initialize_cache_service(redis_url: Optional[str] = None) -> CacheService:
    """Initialize cache service with custom configuration."""
    global _cache_service
    _cache_service = CacheService(redis_url)
    return _cache_service


# Cache warming functions examples

def warm_user_cache(db: Session) -> None:
    """Example cache warming function for user data."""
    cache = get_cache_service()

    # This is a placeholder - implement actual warming logic
    from app.models.user import User

    try:
        # Example: Cache active user count
        active_users = db.query(User).filter(User.is_active).count()
        cache.set("stats:active_users", active_users, ttl=3600)

        # Example: Cache recent users
        recent_users = (
            db.query(User)
            .filter(User.is_active)
            .order_by(User.created_at.desc())
            .limit(100)
            .all()
        )

        user_data = [
            {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
            }
            for user in recent_users
        ]
        cache.set("users:recent", user_data, ttl=1800)

        logger.info("User cache warmed successfully")

    except Exception as e:
        logger.error(f"Failed to warm user cache: {e}")
        raise


def warm_organization_cache(db: Session) -> None:
    """Example cache warming function for organization data."""
    cache = get_cache_service()

    try:
        from app.models.organization import Organization

        # Cache organization count
        org_count = db.query(Organization).filter(Organization.is_active).count()
        cache.set("stats:active_organizations", org_count, ttl=3600)

        logger.info("Organization cache warmed successfully")

    except Exception as e:
        logger.error(f"Failed to warm organization cache: {e}")
        raise


# Export main components
__all__ = [
    "CacheService",
    "CacheKeyBuilder",
    "CacheStatistics",
    "cached",
    "cache_invalidate",
    "get_cache_service",
    "initialize_cache_service",
    "warm_user_cache",
    "warm_organization_cache",
]

