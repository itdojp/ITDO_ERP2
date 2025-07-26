"""
ITDO ERP Backend - Financial Performance Optimizer
Day 27: Performance optimization utilities for financial operations

This module provides:
- Database query optimization for financial operations
- Caching strategies for financial data
- Performance monitoring and metrics
- Memory management for large datasets
- Async operation optimization
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.types import OrganizationId

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Redis client for caching (mock implementation for demonstration)
try:
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
except Exception:
    redis_client = None
    logger.warning("Redis not available, caching disabled")


class PerformanceMonitor:
    """Performance monitoring utility for financial operations"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}

    def start_timer(self, operation_name: str) -> None:
        """Start timing an operation"""
        self.start_times[operation_name] = time.time()

    def end_timer(self, operation_name: str) -> float:
        """End timing an operation and record the duration"""
        if operation_name not in self.start_times:
            logger.warning(f"No start time found for operation: {operation_name}")
            return 0.0

        duration = time.time() - self.start_times[operation_name]

        if operation_name not in self.metrics:
            self.metrics[operation_name] = []

        self.metrics[operation_name].append(duration)
        del self.start_times[operation_name]

        logger.debug(
            f"Operation '{operation_name}' completed in {duration:.4f} seconds"
        )
        return duration

    def get_average_duration(self, operation_name: str) -> float:
        """Get average duration for an operation"""
        if operation_name not in self.metrics or not self.metrics[operation_name]:
            return 0.0

        return sum(self.metrics[operation_name]) / len(self.metrics[operation_name])

    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get comprehensive metrics summary"""
        summary = {}

        for operation, durations in self.metrics.items():
            if durations:
                summary[operation] = {
                    "count": len(durations),
                    "total_time": sum(durations),
                    "average_time": sum(durations) / len(durations),
                    "min_time": min(durations),
                    "max_time": max(durations),
                }

        return summary

    @asynccontextmanager
    async def measure_async(self, operation_name: str):
        """Context manager for measuring async operations"""
        self.start_timer(operation_name)
        try:
            yield
        finally:
            self.end_timer(operation_name)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def cache_result(expire_seconds: int = 300, key_prefix: str = "financial") -> Callable:
    """Decorator for caching function results"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not redis_client:
                # If Redis is not available, execute function directly
                return await func(*args, **kwargs)

            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            try:
                # Try to get cached result
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return eval(
                        cached_result
                    )  # Note: In production, use proper serialization
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            # Execute function and cache result
            result = await func(*args, **kwargs)

            try:
                redis_client.setex(cache_key, expire_seconds, str(result))
                logger.debug(f"Cached result for {func.__name__}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result

        return wrapper

    return decorator


def performance_monitor_decorator(operation_name: Optional[str] = None) -> Callable:
    """Decorator for automatically monitoring function performance"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            async with performance_monitor.measure_async(op_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


class DatabaseOptimizer:
    """Database optimization utilities for financial operations"""

    @staticmethod
    async def optimize_connection_pool(engine) -> None:
        """Optimize database connection pool settings"""
        # Configure connection pool for financial operations
        engine.pool._recycle = 3600  # Recycle connections every hour
        engine.pool._pool_size = 20  # Increase pool size for concurrent operations
        engine.pool._max_overflow = 30  # Allow overflow connections

        logger.info("Database connection pool optimized for financial operations")

    @staticmethod
    async def create_financial_indexes(db: AsyncSession) -> None:
        """Create optimized indexes for financial queries"""
        indexes = [
            # Journal entries indexes
            "CREATE INDEX IF NOT EXISTS idx_journal_entries_org_date ON journal_entries(organization_id, entry_date)",
            "CREATE INDEX IF NOT EXISTS idx_journal_entries_account_date ON journal_entries(account_id, entry_date)",
            # Financial forecasts indexes
            "CREATE INDEX IF NOT EXISTS idx_financial_forecasts_org_active ON financial_forecasts(organization_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_financial_forecasts_created ON financial_forecasts(created_at DESC)",
            # Risk assessments indexes
            "CREATE INDEX IF NOT EXISTS idx_risk_assessments_org_active ON risk_assessments(organization_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_risk_assessments_date ON risk_assessments(assessment_date DESC)",
            # Cash flow predictions indexes
            "CREATE INDEX IF NOT EXISTS idx_cashflow_predictions_org_active ON cash_flow_predictions(organization_id, is_active)",
            # Exchange rates indexes
            "CREATE INDEX IF NOT EXISTS idx_exchange_rates_date_active ON exchange_rates(rate_date DESC, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_exchange_rates_currencies ON exchange_rates(base_currency_id, target_currency_id)",
        ]

        for index_sql in indexes:
            try:
                await db.execute(text(index_sql))
                logger.debug(f"Created index: {index_sql.split()[-1]}")
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")

        await db.commit()
        logger.info("Financial database indexes optimized")

    @staticmethod
    async def analyze_query_performance(db: AsyncSession, query: str) -> Dict[str, Any]:
        """Analyze query performance and provide optimization suggestions"""
        try:
            # Execute EXPLAIN ANALYZE for the query
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            result = await db.execute(text(explain_query))
            explain_result = result.fetchone()

            if explain_result:
                return {
                    "query": query,
                    "execution_plan": explain_result[0],
                    "analysis_timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {"error": str(e)}


class MemoryManager:
    """Memory management utilities for large financial datasets"""

    @staticmethod
    def chunk_data(data: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
        """Split large datasets into manageable chunks"""
        return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]

    @staticmethod
    async def process_large_dataset(
        data: List[Any],
        processor_func: Callable,
        chunk_size: int = 1000,
        max_concurrent: int = 5,
    ) -> List[Any]:
        """Process large datasets with memory optimization"""
        chunks = MemoryManager.chunk_data(data, chunk_size)
        results = []

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_chunk(chunk):
            async with semaphore:
                return await processor_func(chunk)

        # Process chunks concurrently with controlled concurrency
        tasks = [process_chunk(chunk) for chunk in chunks]
        chunk_results = await asyncio.gather(*tasks)

        # Flatten results
        for chunk_result in chunk_results:
            if isinstance(chunk_result, list):
                results.extend(chunk_result)
            else:
                results.append(chunk_result)

        return results

    @staticmethod
    def optimize_decimal_operations(
        values: List[Union[float, Decimal]],
    ) -> List[Decimal]:
        """Optimize decimal operations for financial calculations"""
        # Convert to Decimal with appropriate precision
        return [Decimal(str(value)).quantize(Decimal("0.01")) for value in values]


class CacheManager:
    """Advanced caching strategies for financial data"""

    def __init__(self):
        self.local_cache: Dict[str, Dict[str, Any]] = {}

    def set_cache(
        self,
        key: str,
        value: Any,
        expire_at: Optional[datetime] = None,
        cache_type: str = "redis",
    ) -> None:
        """Set cache value with expiration"""
        if cache_type == "redis" and redis_client:
            try:
                if expire_at:
                    ttl = int((expire_at - datetime.now()).total_seconds())
                    redis_client.setex(key, ttl, str(value))
                else:
                    redis_client.set(key, str(value))
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
                self._set_local_cache(key, value, expire_at)
        else:
            self._set_local_cache(key, value, expire_at)

    def get_cache(self, key: str, cache_type: str = "redis") -> Optional[Any]:
        """Get cache value"""
        if cache_type == "redis" and redis_client:
            try:
                cached_value = redis_client.get(key)
                if cached_value:
                    return eval(
                        cached_value
                    )  # Note: Use proper serialization in production
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
                return self._get_local_cache(key)
        else:
            return self._get_local_cache(key)

    def _set_local_cache(
        self, key: str, value: Any, expire_at: Optional[datetime]
    ) -> None:
        """Set local cache value"""
        self.local_cache[key] = {
            "value": value,
            "expire_at": expire_at,
            "created_at": datetime.now(),
        }

    def _get_local_cache(self, key: str) -> Optional[Any]:
        """Get local cache value"""
        if key not in self.local_cache:
            return None

        cache_entry = self.local_cache[key]

        # Check expiration
        if cache_entry["expire_at"] and datetime.now() > cache_entry["expire_at"]:
            del self.local_cache[key]
            return None

        return cache_entry["value"]

    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching a pattern"""
        if redis_client:
            try:
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis pattern invalidation failed: {e}")

        # Also invalidate local cache
        keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.local_cache[key]

    def clear_all(self) -> None:
        """Clear all cache"""
        if redis_client:
            try:
                redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis flush failed: {e}")

        self.local_cache.clear()


class AsyncOperationOptimizer:
    """Optimization utilities for async financial operations"""

    @staticmethod
    async def batch_database_operations(
        db: AsyncSession,
        operations: List[Callable],
        batch_size: int = 100,
    ) -> List[Any]:
        """Batch database operations for better performance"""
        results = []

        for i in range(0, len(operations), batch_size):
            batch = operations[i : i + batch_size]

            # Execute batch operations
            batch_results = await asyncio.gather(
                *[op() for op in batch], return_exceptions=True
            )

            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch operation failed: {result}")
                else:
                    results.append(result)

            # Commit batch
            try:
                await db.commit()
            except Exception as e:
                logger.error(f"Batch commit failed: {e}")
                await db.rollback()

        return results

    @staticmethod
    async def parallel_financial_calculations(
        calculations: List[Callable],
        max_workers: int = 10,
    ) -> List[Any]:
        """Execute financial calculations in parallel"""
        semaphore = asyncio.Semaphore(max_workers)

        async def execute_with_semaphore(calc):
            async with semaphore:
                return await calc()

        tasks = [execute_with_semaphore(calc) for calc in calculations]
        return await asyncio.gather(*tasks, return_exceptions=True)


# Global cache manager instance
cache_manager = CacheManager()


def get_financial_cache_key(
    operation: str, organization_id: OrganizationId, **params
) -> str:
    """Generate standardized cache key for financial operations"""
    param_string = "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
    return f"financial:{operation}:{organization_id}:{param_string}"


async def warm_up_financial_caches(organization_id: OrganizationId) -> None:
    """Pre-warm caches for common financial operations"""
    logger.info(f"Warming up financial caches for organization {organization_id}")

    # Common cache keys to warm up
    cache_operations = [
        "basic_financial_metrics",
        "module_metrics",
        "risk_assessment",
        "currency_data",
        "performance_kpis",
    ]

    for operation in cache_operations:
        cache_key = get_financial_cache_key(operation, organization_id)

        # Set placeholder cache entries to avoid cold cache misses
        cache_manager.set_cache(
            cache_key,
            {"status": "warming", "timestamp": datetime.now().isoformat()},
            datetime.now() + timedelta(minutes=5),
        )

    logger.info("Financial cache warm-up completed")


class FinancialQueryOptimizer:
    """Specialized query optimization for financial operations"""

    @staticmethod
    def optimize_date_range_query(start_date: datetime, end_date: datetime) -> str:
        """Optimize date range queries for financial data"""
        # Use proper indexing strategy for date ranges
        return f"entry_date >= '{start_date.isoformat()}' AND entry_date <= '{end_date.isoformat()}'"

    @staticmethod
    def build_optimized_financial_query(
        base_query: str,
        organization_id: OrganizationId,
        date_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        """Build optimized financial query with proper indexing"""
        query_parts = [base_query]

        # Add organization filter (should use index)
        query_parts.append(f"WHERE organization_id = '{organization_id}'")

        # Add date filter if provided
        if date_filter:
            query_parts.append(f"AND {date_filter}")

        # Add limit for large datasets
        if limit:
            query_parts.append(f"LIMIT {limit}")

        return " ".join(query_parts)


# Export optimization utilities
__all__ = [
    "PerformanceMonitor",
    "DatabaseOptimizer",
    "MemoryManager",
    "CacheManager",
    "AsyncOperationOptimizer",
    "FinancialQueryOptimizer",
    "performance_monitor",
    "cache_manager",
    "cache_result",
    "performance_monitor_decorator",
    "get_financial_cache_key",
    "warm_up_financial_caches",
]
