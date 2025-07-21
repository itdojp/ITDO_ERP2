"""Redis caching implementation for performance optimization."""

import asyncio
import json
import pickle
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from redis import Redis

from app.core.config import settings
from app.core.monitoring import monitor_performance


class CacheManager:
    """Redis cache manager for application-wide caching."""

    def __init__(self):
        """Initialize cache manager."""
        self.redis_url = settings.REDIS_URL
        self.default_ttl = 300  # 5 minutes
        self._async_client: Optional[aioredis.Redis] = None
        self._sync_client: Optional[Redis] = None

    async def get_async_client(self) -> aioredis.Redis:
        """Get async Redis client."""
        if self._async_client is None:
            self._async_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
        return self._async_client

    def get_sync_client(self) -> Redis:
        """Get sync Redis client."""
        if self._sync_client is None:
            self._sync_client = Redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
        return self._sync_client

    @monitor_performance("cache.set")
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        namespace: str = "app"
    ) -> bool:
        """Set a value in cache."""
        try:
            client = await self.get_async_client()
            cache_key = self._build_key(key, namespace)
            serialized_value = self._serialize(value)
            
            if ttl is None:
                ttl = self.default_ttl
            
            result = await client.setex(cache_key, ttl, serialized_value)
            return bool(result)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    @monitor_performance("cache.get")
    async def get(
        self, 
        key: str, 
        namespace: str = "app",
        default: Any = None
    ) -> Any:
        """Get a value from cache."""
        try:
            client = await self.get_async_client()
            cache_key = self._build_key(key, namespace)
            
            cached_value = await client.get(cache_key)
            if cached_value is None:
                return default
            
            return self._deserialize(cached_value)
        except Exception as e:
            print(f"Cache get error: {e}")
            return default

    @monitor_performance("cache.delete")
    async def delete(self, key: str, namespace: str = "app") -> bool:
        """Delete a key from cache."""
        try:
            client = await self.get_async_client()
            cache_key = self._build_key(key, namespace)
            result = await client.delete(cache_key)
            return bool(result)
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    @monitor_performance("cache.exists")
    async def exists(self, key: str, namespace: str = "app") -> bool:
        """Check if key exists in cache."""
        try:
            client = await self.get_async_client()
            cache_key = self._build_key(key, namespace)
            result = await client.exists(cache_key)
            return bool(result)
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    @monitor_performance("cache.clear_namespace")
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        try:
            client = await self.get_async_client()
            pattern = f"{namespace}:*"
            keys = []
            
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear namespace error: {e}")
            return 0

    @monitor_performance("cache.set_many")
    async def set_many(
        self, 
        mapping: Dict[str, Any], 
        ttl: Optional[int] = None,
        namespace: str = "app"
    ) -> bool:
        """Set multiple values in cache."""
        try:
            client = await self.get_async_client()
            
            if ttl is None:
                ttl = self.default_ttl
            
            pipe = client.pipeline()
            for key, value in mapping.items():
                cache_key = self._build_key(key, namespace)
                serialized_value = self._serialize(value)
                pipe.setex(cache_key, ttl, serialized_value)
            
            results = await pipe.execute()
            return all(results)
        except Exception as e:
            print(f"Cache set_many error: {e}")
            return False

    @monitor_performance("cache.get_many")
    async def get_many(
        self, 
        keys: List[str], 
        namespace: str = "app"
    ) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            client = await self.get_async_client()
            cache_keys = [self._build_key(key, namespace) for key in keys]
            
            values = await client.mget(cache_keys)
            result = {}
            
            for i, key in enumerate(keys):
                if values[i] is not None:
                    result[key] = self._deserialize(values[i])
            
            return result
        except Exception as e:
            print(f"Cache get_many error: {e}")
            return {}

    def _build_key(self, key: str, namespace: str) -> str:
        """Build cache key with namespace."""
        return f"{namespace}:{key}"

    def _serialize(self, value: Any) -> str:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value)
        else:
            # Use pickle for complex objects
            return pickle.dumps(value).hex()

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            try:
                # Try pickle
                return pickle.loads(bytes.fromhex(value))
            except (ValueError, pickle.PickleError):
                return value


# Global cache manager instance
cache_manager = CacheManager()


class CacheDecorator:
    """Decorator for caching function results."""

    @staticmethod
    def cached(
        ttl: int = 300,
        namespace: str = "func",
        key_builder: Optional[callable] = None
    ):
        """Cache function results."""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try to get from cache
                cached_result = await cache_manager.get(cache_key, namespace)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await cache_manager.set(cache_key, result, ttl, namespace)
                
                return result
            
            def sync_wrapper(*args, **kwargs):
                # For sync functions, use asyncio.run for cache operations
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try to get from cache
                try:
                    cached_result = asyncio.run(cache_manager.get(cache_key, namespace))
                    if cached_result is not None:
                        return cached_result
                except:
                    pass
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                try:
                    asyncio.run(cache_manager.set(cache_key, result, ttl, namespace))
                except:
                    pass
                
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# Cache utilities for specific use cases
class ModelCache:
    """Model-specific caching utilities."""

    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict]:
        """Get user from cache."""
        return await cache_manager.get(f"user:{user_id}", "users")

    @staticmethod
    async def set_user(user_id: int, user_data: Dict, ttl: int = 600) -> bool:
        """Cache user data."""
        return await cache_manager.set(f"user:{user_id}", user_data, ttl, "users")

    @staticmethod
    async def invalidate_user(user_id: int) -> bool:
        """Invalidate user cache."""
        return await cache_manager.delete(f"user:{user_id}", "users")

    @staticmethod
    async def get_organization(org_id: int) -> Optional[Dict]:
        """Get organization from cache."""
        return await cache_manager.get(f"org:{org_id}", "organizations")

    @staticmethod
    async def set_organization(org_id: int, org_data: Dict, ttl: int = 3600) -> bool:
        """Cache organization data."""
        return await cache_manager.set(f"org:{org_id}", org_data, ttl, "organizations")

    @staticmethod
    async def get_product(product_id: int) -> Optional[Dict]:
        """Get product from cache."""
        return await cache_manager.get(f"product:{product_id}", "products")

    @staticmethod
    async def set_product(product_id: int, product_data: Dict, ttl: int = 1800) -> bool:
        """Cache product data."""
        return await cache_manager.set(f"product:{product_id}", product_data, ttl, "products")


class SessionCache:
    """Session-specific caching utilities."""

    @staticmethod
    async def set_session(session_id: str, session_data: Dict, ttl: int = 3600) -> bool:
        """Cache session data."""
        return await cache_manager.set(f"session:{session_id}", session_data, ttl, "sessions")

    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict]:
        """Get session from cache."""
        return await cache_manager.get(f"session:{session_id}", "sessions")

    @staticmethod
    async def invalidate_session(session_id: str) -> bool:
        """Invalidate session cache."""
        return await cache_manager.delete(f"session:{session_id}", "sessions")


class QueryCache:
    """Query result caching utilities."""

    @staticmethod
    async def get_query_result(query_hash: str) -> Optional[Any]:
        """Get cached query result."""
        return await cache_manager.get(f"query:{query_hash}", "queries")

    @staticmethod
    async def set_query_result(
        query_hash: str, 
        result: Any, 
        ttl: int = 300
    ) -> bool:
        """Cache query result."""
        return await cache_manager.set(f"query:{query_hash}", result, ttl, "queries")

    @staticmethod
    def build_query_hash(query: str, params: Dict) -> str:
        """Build hash for query caching."""
        import hashlib
        query_string = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(query_string.encode()).hexdigest()


# Health check for cache
async def check_cache_health() -> Dict[str, Any]:
    """Check Redis cache health."""
    health_info = {
        "status": "healthy",
        "redis_connection": False,
        "ping_response_time": None,
        "memory_usage": None
    }
    
    try:
        client = await cache_manager.get_async_client()
        
        # Test ping
        start_time = datetime.utcnow()
        pong = await client.ping()
        ping_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        health_info["redis_connection"] = bool(pong)
        health_info["ping_response_time"] = ping_time
        
        # Get memory info
        info = await client.info("memory")
        health_info["memory_usage"] = info.get("used_memory_human", "unknown")
        
    except Exception as e:
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)
    
    return health_info


# Cache warming utilities
async def warm_cache():
    """Warm up cache with frequently accessed data."""
    try:
        # This would be implemented based on specific application needs
        # For example, pre-load frequently accessed users, products, etc.
        
        print("Cache warming started...")
        
        # Example: Pre-load some sample data
        await cache_manager.set("app:status", "running", 3600, "system")
        
        print("Cache warming completed successfully")
        
    except Exception as e:
        print(f"Cache warming failed: {e}")