"""Distributed caching system with Redis clustering and intelligent cache management."""

import asyncio
import hashlib
import json
import pickle
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.core.monitoring import monitor_performance


class CacheBackend(str, Enum):
    """Cache backend types."""

    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    HYBRID = "hybrid"


class CacheStrategy(str, Enum):
    """Cache eviction strategies."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    ADAPTIVE = "adaptive"


class CachePartitionStrategy(str, Enum):
    """Cache partitioning strategies."""

    CONSISTENT_HASH = "consistent_hash"
    RANGE_BASED = "range_based"
    HASH_BASED = "hash_based"
    GEOGRAPHIC = "geographic"


@dataclass
class CacheNode:
    """Cache node in distributed system."""

    id: str
    host: str
    port: int
    weight: float = 1.0
    is_active: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    connection_pool_size: int = 10
    max_memory_mb: int = 1024
    current_memory_mb: float = 0.0
    hit_rate: float = 0.0
    response_time_ms: float = 0.0

    def __post_init__(self) -> dict:
        if not self.id:
            self.id = f"{self.host}:{self.port}"


@dataclass
class CacheEntry:
    """Distributed cache entry with metadata."""

    key: str
    value: Any
    ttl_seconds: int
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size_bytes: int = 0
    node_id: str = ""
    version: int = 1
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds <= 0:
            return False
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl_seconds

    def update_access(self) -> None:
        """Update access metadata."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    memory_used_mb: float = 0.0
    memory_limit_mb: float = 0.0
    avg_response_time_ms: float = 0.0
    node_count: int = 0
    active_nodes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0

    @property
    def memory_utilization(self) -> float:
        """Calculate memory utilization percentage."""
        return (
            (self.memory_used_mb / self.memory_limit_mb * 100)
            if self.memory_limit_mb > 0
            else 0.0
        )


class ConsistentHash:
    """Consistent hashing for distributed cache."""

    def __init__(self, replicas: int = 150) -> dict:
        """Initialize consistent hash ring."""
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        self.nodes: Set[str] = set()

    def _hash(self, key: str) -> int:
        """Generate hash for key."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        """Add node to hash ring."""
        self.nodes.add(node)
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node

        self.sorted_keys = sorted(self.ring.keys())

    def remove_node(self, node: str) -> None:
        """Remove node from hash ring."""
        if node not in self.nodes:
            return

        self.nodes.discard(node)
        keys_to_remove = []

        for hash_value, ring_node in self.ring.items():
            if ring_node == node:
                keys_to_remove.append(hash_value)

        for key in keys_to_remove:
            del self.ring[key]

        self.sorted_keys = sorted(self.ring.keys())

    def get_node(self, key: str) -> Optional[str]:
        """Get node for key using consistent hashing."""
        if not self.ring:
            return None

        hash_value = self._hash(key)

        # Find first node clockwise from hash value
        for ring_key in self.sorted_keys:
            if hash_value <= ring_key:
                return self.ring[ring_key]

        # Wrap around to first node
        return self.ring[self.sorted_keys[0]]

    def get_nodes_for_replication(self, key: str, count: int = 3) -> List[str]:
        """Get multiple nodes for replication."""
        if not self.ring or count <= 0:
            return []

        hash_value = self._hash(key)
        nodes = []
        unique_nodes = set()

        # Start from the primary node
        start_index = 0
        for i, ring_key in enumerate(self.sorted_keys):
            if hash_value <= ring_key:
                start_index = i
                break

        # Collect unique nodes
        for i in range(len(self.sorted_keys)):
            index = (start_index + i) % len(self.sorted_keys)
            node = self.ring[self.sorted_keys[index]]

            if node not in unique_nodes:
                unique_nodes.add(node)
                nodes.append(node)

                if len(nodes) >= count:
                    break

        return nodes


class DistributedCacheManager:
    """Advanced distributed cache management system."""

    def __init__(
        self,
        backend: CacheBackend = CacheBackend.HYBRID,
        strategy: CacheStrategy = CacheStrategy.ADAPTIVE,
        partition_strategy: CachePartitionStrategy = CachePartitionStrategy.CONSISTENT_HASH,
        replication_factor: int = 3,
    ):
        """Initialize distributed cache manager."""
        self.backend = backend
        self.strategy = strategy
        self.partition_strategy = partition_strategy
        self.replication_factor = replication_factor

        # Node management
        self.nodes: Dict[str, CacheNode] = {}
        self.consistent_hash = ConsistentHash()

        # Local cache for hybrid mode
        self.local_cache: Dict[str, CacheEntry] = {}
        self.local_cache_size_mb = 100  # Local cache limit

        # Performance tracking
        self.stats = CacheStats()
        self.performance_history: deque = deque(maxlen=10000)
        self.operation_times: deque = deque(maxlen=1000)

        # Cache warming and preloading
        self.warm_cache_keys: Set[str] = set()
        self.preload_patterns: List[str] = []

        # Invalidation tracking
        self.invalidation_queue: deque = deque()
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)

        # Initialize default local nodes
        self._initialize_default_nodes()

    def _initialize_default_nodes(self) -> None:
        """Initialize default cache nodes."""
        # Add local memory node
        local_node = CacheNode(
            id="local_memory",
            host="localhost",
            port=0,
            weight=1.0,
            max_memory_mb=self.local_cache_size_mb,
        )
        self.add_node(local_node)

        # Add Redis nodes (would be configured from environment)
        redis_nodes = [
            CacheNode(
                id="redis_1",
                host="localhost",
                port=6379,
                weight=2.0,
                max_memory_mb=2048,
            ),
            CacheNode(
                id="redis_2",
                host="localhost",
                port=6380,
                weight=2.0,
                max_memory_mb=2048,
            ),
            CacheNode(
                id="redis_3",
                host="localhost",
                port=6381,
                weight=2.0,
                max_memory_mb=2048,
            ),
        ]

        for node in redis_nodes:
            self.add_node(node)

    def add_node(self, node: CacheNode) -> None:
        """Add cache node to distributed system."""
        self.nodes[node.id] = node
        self.consistent_hash.add_node(node.id)
        self.stats.node_count = len(self.nodes)
        self.stats.active_nodes = len([n for n in self.nodes.values() if n.is_active])

    def remove_node(self, node_id: str) -> bool:
        """Remove cache node from system."""
        if node_id not in self.nodes:
            return False

        # Redistribute data from removed node
        self._redistribute_node_data(node_id)

        del self.nodes[node_id]
        self.consistent_hash.remove_node(node_id)
        self.stats.node_count = len(self.nodes)
        self.stats.active_nodes = len([n for n in self.nodes.values() if n.is_active])

        return True

    def _redistribute_node_data(self, node_id: str) -> None:
        """Redistribute data when node is removed."""
        # In production, this would move data to other nodes
        # For now, we'll simulate by clearing local entries for that node
        keys_to_redistribute = []

        for key, entry in self.local_cache.items():
            if entry.node_id == node_id:
                keys_to_redistribute.append(key)

        for key in keys_to_redistribute:
            # Find new node and move data
            new_node_id = self.consistent_hash.get_node(key)
            if new_node_id and new_node_id != node_id:
                entry = self.local_cache[key]
                entry.node_id = new_node_id
            else:
                # If no suitable node, remove from cache
                del self.local_cache[key]

    @monitor_performance("cache.distributed.get")
    async def get(self, key: str) -> Optional[Any]:
        """Get value from distributed cache."""
        start_time = time.time()
        self.stats.total_requests += 1

        try:
            # Try local cache first in hybrid mode
            if self.backend in [CacheBackend.HYBRID, CacheBackend.MEMORY]:
                if key in self.local_cache:
                    entry = self.local_cache[key]

                    if not entry.is_expired():
                        entry.update_access()
                        self.stats.cache_hits += 1
                        self._record_operation_time(start_time)
                        return entry.value
                    else:
                        # Remove expired entry
                        del self.local_cache[key]

            # Try distributed nodes
            if self.backend in [CacheBackend.HYBRID, CacheBackend.REDIS]:
                nodes = self.consistent_hash.get_nodes_for_replication(
                    key, self.replication_factor
                )

                for node_id in nodes:
                    if node_id in self.nodes and self.nodes[node_id].is_active:
                        value = await self._get_from_node(key, node_id)
                        if value is not None:
                            self.stats.cache_hits += 1
                            self._record_operation_time(start_time)

                            # Cache locally in hybrid mode
                            if self.backend == CacheBackend.HYBRID:
                                await self._store_locally(key, value, 300)  # 5 min TTL

                            return value

            # Cache miss
            self.stats.cache_misses += 1
            self._record_operation_time(start_time)
            return None

        except Exception as e:
            self.stats.cache_misses += 1
            print(f"Cache get error for key {key}: {e}")
            return None

    @monitor_performance("cache.distributed.set")
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
    ) -> bool:
        """Set value in distributed cache."""
        start_time = time.time()

        try:
            serialized_value = self._serialize_value(value)
            size_bytes = len(serialized_value)

            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                size_bytes=size_bytes,
                tags=tags or set(),
                dependencies=dependencies or set(),
            )

            # Store in distributed nodes
            success = False
            if self.backend in [CacheBackend.HYBRID, CacheBackend.REDIS]:
                nodes = self.consistent_hash.get_nodes_for_replication(
                    key, self.replication_factor
                )
                successful_stores = 0

                for node_id in nodes:
                    if node_id in self.nodes and self.nodes[node_id].is_active:
                        if await self._set_in_node(key, entry, node_id):
                            successful_stores += 1

                # Require at least one successful store
                success = successful_stores > 0

            # Store locally
            if self.backend in [CacheBackend.HYBRID, CacheBackend.MEMORY]:
                await self._store_locally(key, value, ttl_seconds, tags, dependencies)
                success = True

            # Update dependency graph
            if dependencies:
                for dep in dependencies:
                    self.dependency_graph[dep].add(key)

            self._record_operation_time(start_time)
            return success

        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from distributed cache."""
        success = False

        # Delete from local cache
        if key in self.local_cache:
            del self.local_cache[key]
            success = True

        # Delete from distributed nodes
        if self.backend in [CacheBackend.HYBRID, CacheBackend.REDIS]:
            nodes = self.consistent_hash.get_nodes_for_replication(
                key, self.replication_factor
            )

            for node_id in nodes:
                if node_id in self.nodes and self.nodes[node_id].is_active:
                    if await self._delete_from_node(key, node_id):
                        success = True

        # Clean up dependency graph
        self._cleanup_dependencies(key)

        return success

    async def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate cache entries by tags."""
        invalidated_count = 0
        keys_to_invalidate = []

        # Find keys with matching tags
        for key, entry in self.local_cache.items():
            if entry.tags.intersection(tags):
                keys_to_invalidate.append(key)

        # Invalidate found keys
        for key in keys_to_invalidate:
            if await self.delete(key):
                invalidated_count += 1

        return invalidated_count

    async def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        import re

        invalidated_count = 0
        keys_to_invalidate = []
        compiled_pattern = re.compile(pattern)

        # Find matching keys
        for key in self.local_cache:
            if compiled_pattern.search(key):
                keys_to_invalidate.append(key)

        # Invalidate found keys
        for key in keys_to_invalidate:
            if await self.delete(key):
                invalidated_count += 1

        return invalidated_count

    async def invalidate_dependencies(self, dependency: str) -> int:
        """Invalidate cache entries dependent on a key."""
        invalidated_count = 0

        if dependency in self.dependency_graph:
            dependent_keys = self.dependency_graph[dependency].copy()

            for key in dependent_keys:
                if await self.delete(key):
                    invalidated_count += 1

        return invalidated_count

    async def warm_cache(self, patterns: List[str]) -> int:
        """Warm cache with data matching patterns."""
        warmed_count = 0

        # This would typically load data from database
        # For now, we'll simulate cache warming
        for pattern in patterns:
            # Simulate loading 10 items per pattern
            for i in range(10):
                key = f"{pattern}:{i}"
                value = {"data": f"warmed_data_{i}", "pattern": pattern}

                if await self.set(key, value, ttl_seconds=3600):
                    warmed_count += 1
                    self.warm_cache_keys.add(key)

        return warmed_count

    async def preload_critical_data(self) -> int:
        """Preload critical application data."""
        preloaded_count = 0

        # Define critical data patterns
        critical_patterns = [
            "user:settings:*",
            "organization:config:*",
            "system:config:*",
            "feature:flags:*",
        ]

        preloaded_count = await self.warm_cache(critical_patterns)

        return preloaded_count

    async def _get_from_node(self, key: str, node_id: str) -> Optional[Any]:
        """Get value from specific cache node."""
        # Simulate node access
        node = self.nodes.get(node_id)
        if not node or not node.is_active:
            return None

        # In production, this would make actual Redis/Memcached calls
        await asyncio.sleep(0.001)  # Simulate network latency

        # For simulation, check if key exists in local cache with this node
        if key in self.local_cache:
            entry = self.local_cache[key]
            if entry.node_id == node_id and not entry.is_expired():
                return entry.value

        return None

    async def _set_in_node(self, key: str, entry: CacheEntry, node_id: str) -> bool:
        """Set value in specific cache node."""
        node = self.nodes.get(node_id)
        if not node or not node.is_active:
            return False

        try:
            # Simulate node storage
            await asyncio.sleep(0.002)  # Simulate network latency

            # Update entry with node info
            entry.node_id = node_id

            # In production, this would make actual Redis/Memcached calls
            # For simulation, store in local cache with node ID
            self.local_cache[key] = entry

            # Update node stats
            node.current_memory_mb += entry.size_bytes / (1024 * 1024)

            return True

        except Exception as e:
            print(f"Error setting key {key} in node {node_id}: {e}")
            return False

    async def _delete_from_node(self, key: str, node_id: str) -> bool:
        """Delete key from specific cache node."""
        node = self.nodes.get(node_id)
        if not node or not node.is_active:
            return False

        try:
            # Simulate node deletion
            await asyncio.sleep(0.001)

            # In production, this would make actual deletion calls
            if key in self.local_cache:
                entry = self.local_cache[key]
                if entry.node_id == node_id:
                    node.current_memory_mb -= entry.size_bytes / (1024 * 1024)
                    del self.local_cache[key]
                    return True

            return False

        except Exception as e:
            print(f"Error deleting key {key} from node {node_id}: {e}")
            return False

    async def _store_locally(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
        tags: Optional[Set[str]] = None,
        dependencies: Optional[Set[str]] = None,
    ) -> None:
        """Store value in local cache."""
        # Check local cache size limit
        if self._get_local_cache_size_mb() > self.local_cache_size_mb:
            await self._evict_local_entries()

        serialized_value = self._serialize_value(value)

        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            size_bytes=len(serialized_value),
            node_id="local_memory",
            tags=tags or set(),
            dependencies=dependencies or set(),
        )

        self.local_cache[key] = entry

    def _get_local_cache_size_mb(self) -> float:
        """Calculate local cache size in MB."""
        total_bytes = sum(entry.size_bytes for entry in self.local_cache.values())
        return total_bytes / (1024 * 1024)

    async def _evict_local_entries(self) -> int:
        """Evict entries from local cache based on strategy."""
        if not self.local_cache:
            return 0

        evicted_count = 0
        target_evict_count = max(1, len(self.local_cache) // 10)  # Evict 10%

        if self.strategy == CacheStrategy.LRU:
            # Sort by last accessed time
            entries = sorted(self.local_cache.items(), key=lambda x: x[1].accessed_at)
        elif self.strategy == CacheStrategy.LFU:
            # Sort by access count
            entries = sorted(self.local_cache.items(), key=lambda x: x[1].access_count)
        elif self.strategy == CacheStrategy.TTL:
            # Sort by creation time (oldest first)
            entries = sorted(self.local_cache.items(), key=lambda x: x[1].created_at)
        else:  # ADAPTIVE
            # Score-based eviction
            entries = []
            for key, entry in self.local_cache.items():
                age_hours = (
                    datetime.utcnow() - entry.created_at
                ).total_seconds() / 3600
                access_frequency = entry.access_count / max(age_hours, 1)
                score = access_frequency / (1 + age_hours)
                entries.append((key, entry, score))

            entries = sorted(entries, key=lambda x: x[2])  # Sort by score
            entries = [(k, e) for k, e, s in entries]  # Remove score

        # Evict entries
        for key, entry in entries[:target_evict_count]:
            del self.local_cache[key]
            evicted_count += 1
            self.stats.evictions += 1

        return evicted_count

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            return pickle.dumps(value)
        except Exception:
            # Fallback to JSON
            return json.dumps(value, default=str).encode()

    def _cleanup_dependencies(self, key: str) -> None:
        """Clean up dependency graph for deleted key."""
        # Remove key from all dependency sets
        for dep_key, dependent_keys in self.dependency_graph.items():
            dependent_keys.discard(key)

        # Remove empty dependency entries
        empty_deps = [k for k, v in self.dependency_graph.items() if not v]
        for k in empty_deps:
            del self.dependency_graph[k]

    def _record_operation_time(self, start_time: float) -> None:
        """Record operation timing."""
        operation_time = (time.time() - start_time) * 1000  # Convert to ms
        self.operation_times.append(operation_time)

        # Update average response time
        if self.operation_times:
            self.stats.avg_response_time_ms = sum(self.operation_times) / len(
                self.operation_times
            )

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        healthy_nodes = 0
        total_memory_mb = 0
        used_memory_mb = 0

        for node in self.nodes.values():
            if node.is_active:
                healthy_nodes += 1
            total_memory_mb += node.max_memory_mb
            used_memory_mb += node.current_memory_mb

        self.stats.active_nodes = healthy_nodes
        self.stats.memory_used_mb = used_memory_mb
        self.stats.memory_limit_mb = total_memory_mb

        # Determine health status
        if healthy_nodes == 0:
            status = "critical"
        elif healthy_nodes < len(self.nodes) * 0.5:
            status = "degraded"
        elif self.stats.memory_utilization > 90:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "statistics": {
                "hit_rate_percentage": round(self.stats.hit_rate, 2),
                "memory_utilization_percentage": round(
                    self.stats.memory_utilization, 2
                ),
                "avg_response_time_ms": round(self.stats.avg_response_time_ms, 3),
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "evictions": self.stats.evictions,
            },
            "nodes": {
                "total": self.stats.node_count,
                "active": self.stats.active_nodes,
                "healthy_percentage": round((healthy_nodes / len(self.nodes) * 100), 2)
                if self.nodes
                else 0,
            },
            "configuration": {
                "backend": self.backend.value,
                "strategy": self.strategy.value,
                "partition_strategy": self.partition_strategy.value,
                "replication_factor": self.replication_factor,
            },
            "local_cache": {
                "entries": len(self.local_cache),
                "size_mb": round(self._get_local_cache_size_mb(), 2),
                "limit_mb": self.local_cache_size_mb,
            },
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        return {
            "cache_performance": {
                "hit_rate_percentage": round(self.stats.hit_rate, 2),
                "miss_rate_percentage": round(100 - self.stats.hit_rate, 2),
                "avg_response_time_ms": round(self.stats.avg_response_time_ms, 3),
                "total_operations": self.stats.total_requests,
                "successful_operations": self.stats.cache_hits,
                "failed_operations": self.stats.cache_misses,
            },
            "memory_usage": {
                "used_mb": round(self.stats.memory_used_mb, 2),
                "limit_mb": self.stats.memory_limit_mb,
                "utilization_percentage": round(self.stats.memory_utilization, 2),
                "local_cache_mb": round(self._get_local_cache_size_mb(), 2),
            },
            "node_status": {
                node_id: {
                    "active": node.is_active,
                    "memory_used_mb": round(node.current_memory_mb, 2),
                    "memory_limit_mb": node.max_memory_mb,
                    "hit_rate": round(node.hit_rate, 2),
                    "response_time_ms": round(node.response_time_ms, 3),
                    "last_heartbeat": node.last_heartbeat.isoformat(),
                }
                for node_id, node in self.nodes.items()
            },
            "cache_distribution": {
                "total_entries": len(self.local_cache),
                "warm_cache_entries": len(self.warm_cache_keys),
                "dependency_mappings": len(self.dependency_graph),
                "evictions_total": self.stats.evictions,
            },
        }


# Global distributed cache manager instance
distributed_cache = DistributedCacheManager(
    backend=CacheBackend.HYBRID,
    strategy=CacheStrategy.ADAPTIVE,
    partition_strategy=CachePartitionStrategy.CONSISTENT_HASH,
    replication_factor=2,
)


# Health check for distributed cache
async def check_distributed_cache_health() -> Dict[str, Any]:
    """Check distributed cache system health."""
    return await distributed_cache.health_check()
