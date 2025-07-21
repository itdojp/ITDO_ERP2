"""Advanced multi-level caching system with warming and invalidation."""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from weakref import WeakSet

from app.core.cache import cache_manager
from app.core.monitoring import monitor_performance


class CacheLevel(str, Enum):
    """Cache levels for multi-level caching."""
    L1_MEMORY = "l1_memory"      # In-process memory cache
    L2_REDIS = "l2_redis"        # Redis distributed cache
    L3_DATABASE = "l3_database"  # Database-level cache
    L4_CDN = "l4_cdn"           # CDN edge cache


class CacheStrategy(str, Enum):
    """Cache strategies."""
    LRU = "lru"                 # Least Recently Used
    LFU = "lfu"                 # Least Frequently Used
    TTL = "ttl"                 # Time To Live
    ADAPTIVE = "adaptive"       # Adaptive based on usage patterns


class InvalidationStrategy(str, Enum):
    """Cache invalidation strategies."""
    TIME_BASED = "time_based"           # TTL expiration
    EVENT_BASED = "event_based"         # Event-driven invalidation
    DEPENDENCY_BASED = "dependency_based"  # Based on data dependencies
    MANUAL = "manual"                   # Manual invalidation
    SMART = "smart"                     # AI-driven invalidation


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    size_bytes: int = 0
    hit_count: int = 0
    source_level: CacheLevel = CacheLevel.L1_MEMORY
    
    def __post_init__(self):
        """Calculate entry size after initialization."""
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if not self.ttl:
            return False
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl
    
    def access(self) -> None:
        """Record cache access."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1
        self.hit_count += 1
    
    def _calculate_size(self) -> int:
        """Calculate approximate size of cache entry."""
        try:
            return len(json.dumps(self.value, default=str).encode('utf-8'))
        except:
            return 1024  # Default size if calculation fails


@dataclass
class CacheConfig:
    """Configuration for cache level."""
    max_size: int = 1000
    ttl_seconds: int = 3600
    strategy: CacheStrategy = CacheStrategy.LRU
    compression: bool = False
    serialization: str = "json"  # json, pickle, msgpack
    auto_refresh: bool = False
    refresh_threshold: float = 0.8  # Refresh when TTL is 80% expired


class CacheLayer(ABC):
    """Abstract cache layer interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get number of entries in cache."""
        pass
    
    @abstractmethod
    async def keys(self) -> List[str]:
        """Get all cache keys."""
        pass


class MemoryCache(CacheLayer):
    """L1 in-memory cache implementation."""
    
    def __init__(self, config: CacheConfig):
        """Initialize memory cache."""
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU
        self.access_frequency: Dict[str, int] = defaultdict(int)  # For LFU
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from memory cache."""
        async with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check expiration
            if entry.is_expired():
                await self._remove_entry(key)
                return None
            
            # Update access statistics
            entry.access()
            self._update_access_order(key)
            
            return entry
    
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in memory cache."""
        async with self._lock:
            # Check if eviction is needed
            if key not in self.cache and len(self.cache) >= self.config.max_size:
                await self._evict_entries()
            
            entry.source_level = CacheLevel.L1_MEMORY
            self.cache[key] = entry
            self._update_access_order(key)
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        async with self._lock:
            return await self._remove_entry(key)
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.access_frequency.clear()
            return True
    
    async def size(self) -> int:
        """Get number of entries in cache."""
        return len(self.cache)
    
    async def keys(self) -> List[str]:
        """Get all cache keys."""
        return list(self.cache.keys())
    
    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU."""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        self.access_frequency[key] += 1
    
    async def _remove_entry(self, key: str) -> bool:
        """Remove entry from cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            if key in self.access_frequency:
                del self.access_frequency[key]
            return True
        return False
    
    async def _evict_entries(self) -> None:
        """Evict entries based on strategy."""
        if self.config.strategy == CacheStrategy.LRU:
            await self._evict_lru()
        elif self.config.strategy == CacheStrategy.LFU:
            await self._evict_lfu()
        elif self.config.strategy == CacheStrategy.TTL:
            await self._evict_expired()
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        while len(self.cache) >= self.config.max_size and self.access_order:
            oldest_key = self.access_order[0]
            await self._remove_entry(oldest_key)
    
    async def _evict_lfu(self) -> None:
        """Evict least frequently used entries."""
        if not self.access_frequency:
            return
        
        # Find key with minimum frequency
        min_freq_key = min(self.access_frequency.items(), key=lambda x: x[1])[0]
        await self._remove_entry(min_freq_key)
    
    async def _evict_expired(self) -> None:
        """Evict expired entries."""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            await self._remove_entry(key)


class RedisCache(CacheLayer):
    """L2 Redis distributed cache implementation."""
    
    def __init__(self, config: CacheConfig):
        """Initialize Redis cache."""
        self.config = config
        self.namespace = "advanced_cache"
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from Redis cache."""
        cache_key = f"{self.namespace}:{key}"
        
        cached_data = await cache_manager.get(cache_key, namespace=self.namespace)
        if not cached_data:
            return None
        
        # Deserialize cache entry
        try:
            entry_data = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
            
            entry = CacheEntry(
                key=entry_data["key"],
                value=entry_data["value"],
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                accessed_at=datetime.fromisoformat(entry_data["accessed_at"]),
                access_count=entry_data.get("access_count", 0),
                ttl=entry_data.get("ttl"),
                tags=set(entry_data.get("tags", [])),
                dependencies=set(entry_data.get("dependencies", [])),
                size_bytes=entry_data.get("size_bytes", 0),
                hit_count=entry_data.get("hit_count", 0),
                source_level=CacheLevel.L2_REDIS
            )
            
            # Check expiration
            if entry.is_expired():
                await self.delete(key)
                return None
            
            entry.access()
            return entry
        
        except Exception as e:
            print(f"Failed to deserialize cache entry: {e}")
            return None
    
    async def set(self, key: str, entry: CacheEntry) -> bool:
        """Set value in Redis cache."""
        cache_key = f"{self.namespace}:{key}"
        
        # Serialize cache entry
        entry_data = {
            "key": entry.key,
            "value": entry.value,
            "created_at": entry.created_at.isoformat(),
            "accessed_at": entry.accessed_at.isoformat(),
            "access_count": entry.access_count,
            "ttl": entry.ttl,
            "tags": list(entry.tags),
            "dependencies": list(entry.dependencies),
            "size_bytes": entry.size_bytes,
            "hit_count": entry.hit_count
        }
        
        entry.source_level = CacheLevel.L2_REDIS
        ttl = entry.ttl or self.config.ttl_seconds
        
        return await cache_manager.set(
            cache_key,
            entry_data,
            ttl=ttl,
            namespace=self.namespace
        )
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        cache_key = f"{self.namespace}:{key}"
        return await cache_manager.delete(cache_key, namespace=self.namespace)
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        result = await cache_manager.clear_namespace(self.namespace)
        return result > 0
    
    async def size(self) -> int:
        """Get number of entries in cache."""
        # This is an approximation as Redis doesn't provide exact count
        return 0
    
    async def keys(self) -> List[str]:
        """Get all cache keys."""
        # This would require SCAN operation in Redis
        return []


class CacheInvalidationManager:
    """Manages cache invalidation strategies."""
    
    def __init__(self):
        """Initialize invalidation manager."""
        self.tag_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # tag -> set of keys
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)   # key -> dependent keys
        self.invalidation_callbacks: List[Callable] = []
    
    def register_dependency(self, key: str, depends_on: str) -> None:
        """Register dependency between cache keys."""
        self.dependency_graph[depends_on].add(key)
    
    def register_tag(self, key: str, tag: str) -> None:
        """Register tag for cache key."""
        self.tag_subscriptions[tag].add(key)
    
    def add_invalidation_callback(self, callback: Callable) -> None:
        """Add callback for invalidation events."""
        self.invalidation_callbacks.append(callback)
    
    async def invalidate_by_key(self, key: str) -> Set[str]:
        """Invalidate cache entry and its dependents."""
        invalidated_keys = {key}
        
        # Find dependent keys
        if key in self.dependency_graph:
            for dependent_key in self.dependency_graph[key]:
                dependent_invalidated = await self.invalidate_by_key(dependent_key)
                invalidated_keys.update(dependent_invalidated)
        
        # Notify callbacks
        for callback in self.invalidation_callbacks:
            try:
                await callback(key, "dependency")
            except Exception as e:
                print(f"Invalidation callback failed: {e}")
        
        return invalidated_keys
    
    async def invalidate_by_tag(self, tag: str) -> Set[str]:
        """Invalidate all cache entries with specific tag."""
        invalidated_keys = set()
        
        if tag in self.tag_subscriptions:
            for key in self.tag_subscriptions[tag].copy():
                key_invalidated = await self.invalidate_by_key(key)
                invalidated_keys.update(key_invalidated)
            
            # Clear tag subscriptions
            del self.tag_subscriptions[tag]
        
        return invalidated_keys
    
    async def invalidate_by_pattern(self, pattern: str) -> Set[str]:
        """Invalidate cache entries matching pattern."""
        invalidated_keys = set()
        
        # This would require pattern matching against all keys
        # Implementation depends on specific cache layers
        
        return invalidated_keys


class CacheWarmingManager:
    """Manages cache warming strategies."""
    
    def __init__(self):
        """Initialize warming manager."""
        self.warming_strategies: Dict[str, Callable] = {}
        self.scheduled_warmings: Dict[str, datetime] = {}
        self.warming_in_progress: Set[str] = set()
    
    def register_warming_strategy(self, name: str, strategy: Callable) -> None:
        """Register cache warming strategy."""
        self.warming_strategies[name] = strategy
    
    async def warm_cache(self, strategy_name: str, force: bool = False) -> bool:
        """Execute cache warming strategy."""
        if strategy_name not in self.warming_strategies:
            return False
        
        if strategy_name in self.warming_in_progress and not force:
            return False
        
        try:
            self.warming_in_progress.add(strategy_name)
            strategy = self.warming_strategies[strategy_name]
            
            await strategy()
            self.scheduled_warmings[strategy_name] = datetime.utcnow()
            
            return True
        
        except Exception as e:
            print(f"Cache warming failed for {strategy_name}: {e}")
            return False
        
        finally:
            self.warming_in_progress.discard(strategy_name)
    
    async def schedule_warming(self, strategy_name: str, interval_minutes: int) -> None:
        """Schedule periodic cache warming."""
        while True:
            await self.warm_cache(strategy_name)
            await asyncio.sleep(interval_minutes * 60)


@dataclass
class CacheAnalytics:
    """Cache performance analytics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    avg_access_time_ms: float = 0.0
    hit_rate: float = 0.0
    
    def update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        total_requests = self.hits + self.misses
        self.hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0


class AdvancedCacheManager:
    """Advanced multi-level cache manager."""
    
    def __init__(self):
        """Initialize advanced cache manager."""
        self.layers: Dict[CacheLevel, CacheLayer] = {}
        self.invalidation_manager = CacheInvalidationManager()
        self.warming_manager = CacheWarmingManager()
        self.analytics: Dict[CacheLevel, CacheAnalytics] = defaultdict(CacheAnalytics)
        self.enabled_levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        # Initialize default cache layers
        self._initialize_default_layers()
        
        # Setup warming strategies
        self._setup_warming_strategies()
    
    def _initialize_default_layers(self) -> None:
        """Initialize default cache layers."""
        # L1 Memory Cache
        l1_config = CacheConfig(
            max_size=1000,
            ttl_seconds=300,
            strategy=CacheStrategy.LRU
        )
        self.layers[CacheLevel.L1_MEMORY] = MemoryCache(l1_config)
        
        # L2 Redis Cache
        l2_config = CacheConfig(
            max_size=10000,
            ttl_seconds=3600,
            strategy=CacheStrategy.TTL
        )
        self.layers[CacheLevel.L2_REDIS] = RedisCache(l2_config)
    
    def _setup_warming_strategies(self) -> None:
        """Setup default cache warming strategies."""
        
        async def warm_popular_data():
            """Warm cache with popular data."""
            # Implementation would depend on business logic
            # For example, preload frequently accessed users, products, etc.
            print("Warming cache with popular data...")
        
        async def warm_user_data():
            """Warm cache with user-specific data."""
            print("Warming cache with user data...")
        
        self.warming_manager.register_warming_strategy("popular_data", warm_popular_data)
        self.warming_manager.register_warming_strategy("user_data", warm_user_data)
    
    @monitor_performance("cache.get")
    async def get(
        self,
        key: str,
        levels: Optional[List[CacheLevel]] = None
    ) -> Optional[Any]:
        """Get value from cache with multi-level fallback."""
        if levels is None:
            levels = self.enabled_levels
        
        start_time = time.time()
        
        for level in levels:
            if level not in self.layers:
                continue
            
            try:
                entry = await self.layers[level].get(key)
                if entry:
                    # Cache hit
                    self.analytics[level].hits += 1
                    
                    # Promote to higher cache levels
                    await self._promote_entry(key, entry, level)
                    
                    # Update analytics
                    access_time = (time.time() - start_time) * 1000
                    self._update_access_time(level, access_time)
                    
                    return entry.value
                else:
                    # Cache miss
                    self.analytics[level].misses += 1
            
            except Exception as e:
                print(f"Cache get error at level {level}: {e}")
                continue
        
        # Update analytics for all levels
        for level in levels:
            if level in self.analytics:
                self.analytics[level].update_hit_rate()
        
        return None
    
    @monitor_performance("cache.set")
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
        levels: Optional[List[CacheLevel]] = None
    ) -> bool:
        """Set value in cache across multiple levels."""
        if levels is None:
            levels = self.enabled_levels
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            ttl=ttl,
            tags=tags or set(),
            dependencies=dependencies or set()
        )
        
        # Register tags and dependencies
        for tag in entry.tags:
            self.invalidation_manager.register_tag(key, tag)
        
        for dep in entry.dependencies:
            self.invalidation_manager.register_dependency(key, dep)
        
        # Set in all specified levels
        success = True
        for level in levels:
            if level not in self.layers:
                continue
            
            try:
                level_success = await self.layers[level].set(key, entry)
                if level_success:
                    self.analytics[level].size_bytes += entry.size_bytes
                success = success and level_success
            
            except Exception as e:
                print(f"Cache set error at level {level}: {e}")
                success = False
        
        return success
    
    async def delete(
        self,
        key: str,
        levels: Optional[List[CacheLevel]] = None
    ) -> bool:
        """Delete value from cache across multiple levels."""
        if levels is None:
            levels = self.enabled_levels
        
        success = True
        for level in levels:
            if level not in self.layers:
                continue
            
            try:
                level_success = await self.layers[level].delete(key)
                success = success and level_success
            
            except Exception as e:
                print(f"Cache delete error at level {level}: {e}")
                success = False
        
        return success
    
    async def invalidate_by_tag(self, tag: str) -> Set[str]:
        """Invalidate all cache entries with specific tag."""
        invalidated_keys = await self.invalidation_manager.invalidate_by_tag(tag)
        
        # Remove from all cache levels
        for key in invalidated_keys:
            await self.delete(key)
        
        return invalidated_keys
    
    async def invalidate_by_dependency(self, dependency_key: str) -> Set[str]:
        """Invalidate cache entries dependent on specific key."""
        return await self.invalidation_manager.invalidate_by_key(dependency_key)
    
    async def warm_cache(self, strategy_name: str) -> bool:
        """Execute cache warming strategy."""
        return await self.warming_manager.warm_cache(strategy_name)
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get cache analytics."""
        analytics_data = {}
        
        for level, analytics in self.analytics.items():
            analytics_data[level.value] = {
                "hits": analytics.hits,
                "misses": analytics.misses,
                "hit_rate": analytics.hit_rate,
                "size_bytes": analytics.size_bytes,
                "avg_access_time_ms": analytics.avg_access_time_ms,
                "evictions": analytics.evictions
            }
        
        # Overall statistics
        total_hits = sum(a.hits for a in self.analytics.values())
        total_misses = sum(a.misses for a in self.analytics.values())
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        analytics_data["overall"] = {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": overall_hit_rate,
            "total_size_bytes": sum(a.size_bytes for a in self.analytics.values()),
            "enabled_levels": [level.value for level in self.enabled_levels]
        }
        
        return analytics_data
    
    async def _promote_entry(
        self,
        key: str,
        entry: CacheEntry,
        current_level: CacheLevel
    ) -> None:
        """Promote cache entry to higher levels."""
        level_priority = {
            CacheLevel.L1_MEMORY: 1,
            CacheLevel.L2_REDIS: 2,
            CacheLevel.L3_DATABASE: 3,
            CacheLevel.L4_CDN: 4
        }
        
        current_priority = level_priority.get(current_level, 999)
        
        for level in self.enabled_levels:
            if level not in self.layers:
                continue
            
            level_priority_val = level_priority.get(level, 999)
            if level_priority_val < current_priority:
                try:
                    await self.layers[level].set(key, entry)
                except Exception as e:
                    print(f"Failed to promote entry to {level}: {e}")
    
    def _update_access_time(self, level: CacheLevel, access_time_ms: float) -> None:
        """Update average access time for cache level."""
        analytics = self.analytics[level]
        total_requests = analytics.hits + analytics.misses
        
        if total_requests > 1:
            # Running average
            analytics.avg_access_time_ms = (
                (analytics.avg_access_time_ms * (total_requests - 1) + access_time_ms) / total_requests
            )
        else:
            analytics.avg_access_time_ms = access_time_ms


# Global advanced cache manager instance
advanced_cache = AdvancedCacheManager()


# Decorator for caching function results
def advanced_cached(
    ttl: Optional[int] = None,
    tags: Optional[Set[str]] = None,
    dependencies: Optional[Set[str]] = None,
    levels: Optional[List[CacheLevel]] = None,
    key_builder: Optional[Callable] = None
):
    """Advanced caching decorator."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode() + str(sorted(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await advanced_cache.get(cache_key, levels)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await advanced_cache.set(
                cache_key,
                result,
                ttl=ttl,
                tags=tags,
                dependencies=dependencies,
                levels=levels
            )
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run async operations in event loop
            import asyncio
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Health check for advanced cache
async def check_advanced_cache_health() -> Dict[str, Any]:
    """Check advanced cache system health."""
    health_info = {
        "status": "healthy",
        "analytics": await advanced_cache.get_analytics(),
        "warming_strategies": len(advanced_cache.warming_manager.warming_strategies),
        "invalidation_tags": len(advanced_cache.invalidation_manager.tag_subscriptions),
        "dependency_graph_size": len(advanced_cache.invalidation_manager.dependency_graph)
    }
    
    return health_info