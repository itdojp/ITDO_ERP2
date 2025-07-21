"""Advanced GraphQL caching system with intelligent cache management."""

import hashlib
import json
import pickle
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from app.core.monitoring import monitor_performance


class CacheStrategy(str, Enum):
    """Cache invalidation strategies."""
    TIME_BASED = "time_based"
    DEPENDENCY_BASED = "dependency_based"
    MANUAL = "manual"
    SMART_EVICTION = "smart_eviction"


class CacheLevel(str, Enum):
    """Cache storage levels."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"
    CDN = "cdn"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int
    size_bytes: int
    dependencies: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl_seconds <= 0:
            return False  # Never expires
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl_seconds
    
    def should_evict(self, access_threshold: int = 5, age_threshold_hours: int = 24) -> bool:
        """Determine if entry should be evicted."""
        age_hours = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        return (self.access_count < access_threshold and age_hours > age_threshold_hours)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate_percentage: float
    avg_retrieval_time_ms: float
    total_storage_mb: float
    entry_count: int
    eviction_count: int
    invalidation_count: int
    popular_keys: List[Tuple[str, int]]


@dataclass
class CacheConfig:
    """Cache configuration."""
    max_size_mb: int = 100
    default_ttl_seconds: int = 300  # 5 minutes
    max_entries: int = 10000
    cleanup_interval_seconds: int = 60
    strategy: CacheStrategy = CacheStrategy.TIME_BASED
    levels: List[CacheLevel] = field(default_factory=lambda: [CacheLevel.MEMORY])
    enable_compression: bool = True
    enable_encryption: bool = False


class SmartCacheInvalidator:
    """Intelligent cache invalidation based on dependencies."""
    
    def __init__(self):
        """Initialize smart invalidator."""
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.entity_patterns: Dict[str, str] = {
            "user": r"user:(\d+)",
            "organization": r"organization:(\d+)",
            "task": r"task:(\d+)",
            "project": r"project:(\d+)"
        }
    
    def add_dependency(self, cache_key: str, dependency: str) -> None:
        """Add dependency relationship."""
        self.dependency_graph[cache_key].add(dependency)
        self.reverse_dependencies[dependency].add(cache_key)
    
    def remove_dependency(self, cache_key: str, dependency: str) -> None:
        """Remove dependency relationship."""
        if cache_key in self.dependency_graph:
            self.dependency_graph[cache_key].discard(dependency)
        if dependency in self.reverse_dependencies:
            self.reverse_dependencies[dependency].discard(cache_key)
    
    def get_affected_keys(self, changed_entity: str) -> Set[str]:
        """Get all cache keys affected by entity change."""
        affected_keys = set()
        
        # Direct dependencies
        if changed_entity in self.reverse_dependencies:
            affected_keys.update(self.reverse_dependencies[changed_entity])
        
        # Pattern-based matching
        for cache_key, dependencies in self.dependency_graph.items():
            for dep in dependencies:
                if self._matches_entity_pattern(dep, changed_entity):
                    affected_keys.add(cache_key)
        
        return affected_keys
    
    def _matches_entity_pattern(self, dependency: str, changed_entity: str) -> bool:
        """Check if dependency matches changed entity pattern."""
        import re
        
        for entity_type, pattern in self.entity_patterns.items():
            if entity_type in dependency.lower() and entity_type in changed_entity.lower():
                dep_match = re.search(pattern, dependency)
                entity_match = re.search(pattern, changed_entity)
                if dep_match and entity_match:
                    return dep_match.group(1) == entity_match.group(1)
        
        return dependency == changed_entity
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependency graph for insights."""
        # Most connected entities
        entity_connections = defaultdict(int)
        for dependencies in self.dependency_graph.values():
            for dep in dependencies:
                entity_connections[dep] += 1
        
        top_dependencies = sorted(
            entity_connections.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_cache_keys": len(self.dependency_graph),
            "total_dependencies": sum(len(deps) for deps in self.dependency_graph.values()),
            "avg_dependencies_per_key": (
                sum(len(deps) for deps in self.dependency_graph.values()) / 
                len(self.dependency_graph) if self.dependency_graph else 0
            ),
            "most_connected_entities": top_dependencies,
            "orphaned_keys": [
                key for key, deps in self.dependency_graph.items()
                if not deps
            ]
        }


class GraphQLCache:
    """Advanced GraphQL result caching system."""
    
    def __init__(self, config: CacheConfig):
        """Initialize GraphQL cache."""
        self.config = config
        self.cache_store: Dict[str, CacheEntry] = {}
        self.access_history: deque = deque(maxlen=10000)
        self.invalidator = SmartCacheInvalidator()
        self.metrics = CacheMetrics(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate_percentage=0.0,
            avg_retrieval_time_ms=0.0,
            total_storage_mb=0.0,
            entry_count=0,
            eviction_count=0,
            invalidation_count=0,
            popular_keys=[]
        )
        self.retrieval_times: deque = deque(maxlen=1000)
        self.last_cleanup = datetime.utcnow()
    
    @monitor_performance("graphql.cache.get")
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()
        
        self.metrics.total_requests += 1
        
        if key not in self.cache_store:
            self.metrics.cache_misses += 1
            return None
        
        entry = self.cache_store[key]
        
        # Check expiration
        if entry.is_expired():
            del self.cache_store[key]
            self.metrics.cache_misses += 1
            return None
        
        # Update access metadata
        entry.last_accessed = datetime.utcnow()
        entry.access_count += 1
        
        # Record access
        self.access_history.append({
            "key": key,
            "timestamp": datetime.utcnow(),
            "hit": True
        })
        
        self.metrics.cache_hits += 1
        
        # Record retrieval time
        retrieval_time = (time.time() - start_time) * 1000
        self.retrieval_times.append(retrieval_time)
        
        return entry.value
    
    @monitor_performance("graphql.cache.set")
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        dependencies: Optional[Set[str]] = None,
        tags: Optional[Set[str]] = None
    ) -> bool:
        """Set value in cache."""
        try:
            # Calculate size
            serialized_value = self._serialize_value(value)
            size_bytes = len(serialized_value)
            
            # Check cache limits
            if not self._check_cache_limits(size_bytes):
                self._evict_entries()
                if not self._check_cache_limits(size_bytes):
                    return False  # Still can't fit
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=0,
                ttl_seconds=ttl_seconds or self.config.default_ttl_seconds,
                size_bytes=size_bytes,
                dependencies=dependencies or set(),
                tags=tags or set()
            )
            
            # Store entry
            self.cache_store[key] = entry
            
            # Update dependencies
            for dep in entry.dependencies:
                self.invalidator.add_dependency(key, dep)
            
            # Update metrics
            self._update_storage_metrics()
            
            return True
        
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self.cache_store:
            entry = self.cache_store[key]
            
            # Remove dependencies
            for dep in entry.dependencies:
                self.invalidator.remove_dependency(key, dep)
            
            del self.cache_store[key]
            self._update_storage_metrics()
            return True
        
        return False
    
    def invalidate_by_dependency(self, dependency: str) -> int:
        """Invalidate cache entries by dependency."""
        affected_keys = self.invalidator.get_affected_keys(dependency)
        
        invalidated_count = 0
        for key in affected_keys:
            if self.delete(key):
                invalidated_count += 1
        
        self.metrics.invalidation_count += invalidated_count
        return invalidated_count
    
    def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate cache entries by tags."""
        keys_to_invalidate = []
        
        for key, entry in self.cache_store.items():
            if entry.tags.intersection(tags):
                keys_to_invalidate.append(key)
        
        invalidated_count = 0
        for key in keys_to_invalidate:
            if self.delete(key):
                invalidated_count += 1
        
        self.metrics.invalidation_count += invalidated_count
        return invalidated_count
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries by key pattern."""
        import re
        
        keys_to_invalidate = []
        compiled_pattern = re.compile(pattern)
        
        for key in self.cache_store:
            if compiled_pattern.search(key):
                keys_to_invalidate.append(key)
        
        invalidated_count = 0
        for key in keys_to_invalidate:
            if self.delete(key):
                invalidated_count += 1
        
        self.metrics.invalidation_count += invalidated_count
        return invalidated_count
    
    def clear(self) -> int:
        """Clear all cache entries."""
        count = len(self.cache_store)
        self.cache_store.clear()
        self.invalidator.dependency_graph.clear()
        self.invalidator.reverse_dependencies.clear()
        self._update_storage_metrics()
        return count
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        expired_keys = []
        
        for key, entry in self.cache_store.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        cleaned_count = 0
        for key in expired_keys:
            if self.delete(key):
                cleaned_count += 1
        
        self.last_cleanup = datetime.utcnow()
        return cleaned_count
    
    def _check_cache_limits(self, additional_size_bytes: int = 0) -> bool:
        """Check if adding entry would exceed cache limits."""
        current_size_mb = self._calculate_total_size_mb()
        additional_size_mb = additional_size_bytes / (1024 * 1024)
        
        if (current_size_mb + additional_size_mb) > self.config.max_size_mb:
            return False
        
        if len(self.cache_store) >= self.config.max_entries:
            return False
        
        return True
    
    def _evict_entries(self) -> int:
        """Evict entries using smart eviction strategy."""
        if self.config.strategy == CacheStrategy.SMART_EVICTION:
            return self._smart_eviction()
        else:
            return self._lru_eviction()
    
    def _smart_eviction(self) -> int:
        """Smart eviction based on access patterns and aging."""
        candidates = []
        
        for key, entry in self.cache_store.items():
            # Calculate eviction score
            age_hours = (datetime.utcnow() - entry.created_at).total_seconds() / 3600
            access_frequency = entry.access_count / max(age_hours, 1)
            last_access_hours = (datetime.utcnow() - entry.last_accessed).total_seconds() / 3600
            
            # Lower score = higher eviction priority
            score = access_frequency / (1 + last_access_hours + age_hours)
            
            candidates.append((key, score, entry.size_bytes))
        
        # Sort by score (ascending) and evict until we have space
        candidates.sort(key=lambda x: x[1])
        
        evicted_count = 0
        target_evict_count = max(1, len(self.cache_store) // 10)  # Evict 10%
        
        for key, score, size in candidates[:target_evict_count]:
            if self.delete(key):
                evicted_count += 1
        
        self.metrics.eviction_count += evicted_count
        return evicted_count
    
    def _lru_eviction(self) -> int:
        """Least Recently Used eviction."""
        if not self.cache_store:
            return 0
        
        # Find least recently used entry
        lru_key = min(
            self.cache_store.keys(),
            key=lambda k: self.cache_store[k].last_accessed
        )
        
        if self.delete(lru_key):
            self.metrics.eviction_count += 1
            return 1
        
        return 0
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for size calculation."""
        if self.config.enable_compression:
            # Would use compression in production
            return pickle.dumps(value)
        else:
            return pickle.dumps(value)
    
    def _calculate_total_size_mb(self) -> float:
        """Calculate total cache size in MB."""
        total_bytes = sum(entry.size_bytes for entry in self.cache_store.values())
        return total_bytes / (1024 * 1024)
    
    def _update_storage_metrics(self) -> None:
        """Update storage-related metrics."""
        self.metrics.total_storage_mb = self._calculate_total_size_mb()
        self.metrics.entry_count = len(self.cache_store)
        
        # Update hit rate
        total_requests = self.metrics.cache_hits + self.metrics.cache_misses
        if total_requests > 0:
            self.metrics.hit_rate_percentage = (self.metrics.cache_hits / total_requests) * 100
        
        # Update average retrieval time
        if self.retrieval_times:
            self.metrics.avg_retrieval_time_ms = sum(self.retrieval_times) / len(self.retrieval_times)
        
        # Update popular keys
        key_access_counts = defaultdict(int)
        for access in self.access_history:
            if access["hit"]:
                key_access_counts[access["key"]] += 1
        
        self.metrics.popular_keys = sorted(
            key_access_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    
    def get_cache_analytics(self) -> Dict[str, Any]:
        """Get comprehensive cache analytics."""
        # Cleanup if needed
        if (datetime.utcnow() - self.last_cleanup).total_seconds() > self.config.cleanup_interval_seconds:
            expired_count = self.cleanup_expired()
        else:
            expired_count = 0
        
        # Dependency analysis
        dependency_analysis = self.invalidator.analyze_dependencies()
        
        # Entry age distribution
        now = datetime.utcnow()
        age_distribution = {"0-1h": 0, "1-6h": 0, "6-24h": 0, "1d+": 0}
        
        for entry in self.cache_store.values():
            age_hours = (now - entry.created_at).total_seconds() / 3600
            if age_hours < 1:
                age_distribution["0-1h"] += 1
            elif age_hours < 6:
                age_distribution["1-6h"] += 1
            elif age_hours < 24:
                age_distribution["6-24h"] += 1
            else:
                age_distribution["1d+"] += 1
        
        return {
            "performance_metrics": {
                "total_requests": self.metrics.total_requests,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "hit_rate_percentage": round(self.metrics.hit_rate_percentage, 2),
                "avg_retrieval_time_ms": round(self.metrics.avg_retrieval_time_ms, 3),
                "eviction_count": self.metrics.eviction_count,
                "invalidation_count": self.metrics.invalidation_count
            },
            "storage_metrics": {
                "total_storage_mb": round(self.metrics.total_storage_mb, 2),
                "entry_count": self.metrics.entry_count,
                "max_size_mb": self.config.max_size_mb,
                "max_entries": self.config.max_entries,
                "utilization_percentage": round(
                    (self.metrics.total_storage_mb / self.config.max_size_mb) * 100, 2
                )
            },
            "popular_keys": self.metrics.popular_keys,
            "age_distribution": age_distribution,
            "dependency_analysis": dependency_analysis,
            "config": {
                "strategy": self.config.strategy.value,
                "default_ttl_seconds": self.config.default_ttl_seconds,
                "cleanup_interval_seconds": self.config.cleanup_interval_seconds,
                "compression_enabled": self.config.enable_compression
            },
            "last_cleanup": self.last_cleanup.isoformat(),
            "expired_entries_cleaned": expired_count
        }


class QueryCacheManager:
    """High-level GraphQL query cache management."""
    
    def __init__(self):
        """Initialize query cache manager."""
        self.cache_config = CacheConfig(
            max_size_mb=200,
            default_ttl_seconds=300,
            max_entries=5000,
            strategy=CacheStrategy.SMART_EVICTION
        )
        self.cache = GraphQLCache(self.cache_config)
        self.query_signatures: Dict[str, str] = {}
    
    def generate_cache_key(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for query."""
        # Normalize query (remove whitespace, comments)
        normalized_query = self._normalize_query(query)
        
        # Include variables in key
        variables_str = json.dumps(variables or {}, sort_keys=True)
        
        # Include user context if relevant
        context_str = ""
        if user_context:
            # Only include relevant context that affects query results
            relevant_context = {
                "user_id": user_context.get("user_id"),
                "organization_id": user_context.get("organization_id"),
                "role": user_context.get("role")
            }
            context_str = json.dumps(relevant_context, sort_keys=True)
        
        # Generate hash
        cache_data = f"{normalized_query}|{variables_str}|{context_str}"
        return hashlib.sha256(cache_data.encode()).hexdigest()[:16]
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent caching."""
        import re
        
        # Remove comments
        query = re.sub(r'#.*$', '', query, flags=re.MULTILINE)
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Remove operation name for caching purposes
        query = re.sub(r'(query|mutation|subscription)\s+\w+', r'\1', query)
        
        return query.strip()
    
    def extract_dependencies(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Set[str]:
        """Extract dependencies from GraphQL query."""
        dependencies = set()
        
        # Simple dependency extraction based on common patterns
        # In production, this would use proper GraphQL parsing
        
        # User dependencies
        if "user" in query.lower():
            if variables and "userId" in variables:
                dependencies.add(f"user:{variables['userId']}")
            elif variables and "id" in variables:
                dependencies.add(f"user:{variables['id']}")
            else:
                dependencies.add("user:*")
        
        # Organization dependencies
        if "organization" in query.lower():
            if variables and "organizationId" in variables:
                dependencies.add(f"organization:{variables['organizationId']}")
            else:
                dependencies.add("organization:*")
        
        # Task dependencies
        if "task" in query.lower():
            if variables and "taskId" in variables:
                dependencies.add(f"task:{variables['taskId']}")
            else:
                dependencies.add("task:*")
        
        return dependencies
    
    def extract_tags(self, query: str) -> Set[str]:
        """Extract cache tags from query."""
        tags = set()
        
        query_lower = query.lower()
        
        if "query" in query_lower:
            tags.add("query")
        if "mutation" in query_lower:
            tags.add("mutation")
        if "user" in query_lower:
            tags.add("user_data")
        if "organization" in query_lower:
            tags.add("organization_data")
        if "task" in query_lower:
            tags.add("task_data")
        if "analytics" in query_lower or "report" in query_lower:
            tags.add("analytics")
        
        return tags
    
    @monitor_performance("graphql.cache.query_get")
    def get_cached_result(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Get cached query result."""
        cache_key = self.generate_cache_key(query, variables, user_context)
        return self.cache.get(cache_key)
    
    @monitor_performance("graphql.cache.query_set")
    def cache_query_result(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        result: Any = None,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Cache query result."""
        cache_key = self.generate_cache_key(query, variables, user_context)
        dependencies = self.extract_dependencies(query, variables)
        tags = self.extract_tags(query)
        
        return self.cache.set(
            cache_key,
            result,
            ttl_seconds,
            dependencies,
            tags
        )
    
    def invalidate_user_data(self, user_id: str) -> int:
        """Invalidate all cache entries for a user."""
        return self.cache.invalidate_by_dependency(f"user:{user_id}")
    
    def invalidate_organization_data(self, organization_id: str) -> int:
        """Invalidate all cache entries for an organization."""
        return self.cache.invalidate_by_dependency(f"organization:{organization_id}")
    
    def invalidate_mutations(self) -> int:
        """Invalidate all mutation-related cache entries."""
        return self.cache.invalidate_by_tags({"mutation"})
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive cache status."""
        analytics = self.cache.get_cache_analytics()
        
        return {
            "cache_status": "healthy" if analytics["performance_metrics"]["hit_rate_percentage"] > 50 else "degraded",
            "analytics": analytics,
            "query_signatures_count": len(self.query_signatures)
        }


# Global cache manager instance
query_cache_manager = QueryCacheManager()


# Health check for caching system
async def check_graphql_caching_health() -> Dict[str, Any]:
    """Check GraphQL caching system health."""
    status = query_cache_manager.get_comprehensive_status()
    
    return {
        "status": status["cache_status"],
        "cache_metrics": status["analytics"]["performance_metrics"],
        "storage_metrics": status["analytics"]["storage_metrics"],
        "configuration": status["analytics"]["config"]
    }