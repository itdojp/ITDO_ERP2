"""Cache manager for Redis integration."""

import json
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class CacheManager:
    """Redis cache manager for caching operations."""

    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize cache manager."""
        self.redis_client = redis_client
        self._is_connected = False

    async def connect(self) -> None:
        """Connect to Redis if not already connected."""
        if not self.redis_client and not self._is_connected:
            self.redis_client = await redis.from_url(  # type: ignore
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            self._is_connected = True

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client and self._is_connected:
            await self.redis_client.close()
            self._is_connected = False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value and isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
        except Exception:
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """Set value in cache with optional expiration."""
        if not self.redis_client:
            return False

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)

            if expire:
                await self.redis_client.setex(key, expire, value)
            else:
                await self.redis_client.set(key, value)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            return bool(result > 0)
        except Exception:
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.redis_client:
            return 0

        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return int(await self.redis_client.delete(*keys))
            return 0
        except Exception:
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False

        try:
            return bool(await self.redis_client.exists(key) > 0)
        except Exception:
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if not self.redis_client:
            return False

        try:
            return bool(await self.redis_client.expire(key, seconds))
        except Exception:
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        if not self.redis_client:
            return -1

        try:
            return int(await self.redis_client.ttl(key))
        except Exception:
            return -1

    async def flush_all(self) -> bool:
        """Flush all keys from cache (use with caution)."""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.flushall()
            return True
        except Exception:
            return False

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        if not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False


# Global cache manager instance
cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global cache_manager

    if not cache_manager:
        cache_manager = CacheManager()
        await cache_manager.connect()

    return cache_manager


async def close_cache_manager() -> None:
    """Close global cache manager."""
    global cache_manager

    if cache_manager:
        await cache_manager.disconnect()
        cache_manager = None
