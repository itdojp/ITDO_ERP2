"""Database performance optimization utilities and monitoring."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Union

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from app.core.monitoring import monitor_performance

logger = logging.getLogger(__name__)


class QueryProfiler:
    """Query profiler for monitoring database performance."""

    def __init__(self):
        """Initialize query profiler."""
        self.slow_queries: List[Dict[str, Any]] = []
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.slow_query_threshold = 0.1  # 100ms
        self.enabled = True

    def log_query(self, query: str, duration: float, params: Optional[Dict] = None) -> None:
        """Log query execution details."""
        if not self.enabled:
            return

        # Normalize query for statistics
        normalized_query = self._normalize_query(query)
        
        # Update statistics
        if normalized_query not in self.query_stats:
            self.query_stats[normalized_query] = {
                'count': 0,
                'total_duration': 0.0,
                'max_duration': 0.0,
                'min_duration': float('inf'),
                'avg_duration': 0.0,
                'last_execution': None
            }
        
        stats = self.query_stats[normalized_query]
        stats['count'] += 1
        stats['total_duration'] += duration
        stats['max_duration'] = max(stats['max_duration'], duration)
        stats['min_duration'] = min(stats['min_duration'], duration)
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['last_execution'] = time.time()

        # Log slow queries
        if duration > self.slow_query_threshold:
            slow_query = {
                'query': query,
                'normalized_query': normalized_query,
                'duration': duration,
                'params': params,
                'timestamp': time.time()
            }
            self.slow_queries.append(slow_query)
            
            # Keep only last 100 slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries.pop(0)
            
            logger.warning(f"Slow query detected ({duration:.3f}s): {query[:200]}...")

    def _normalize_query(self, query: str) -> str:
        """Normalize query for statistics grouping."""
        # Remove parameter values and normalize whitespace
        import re
        normalized = re.sub(r'\$\d+|\?', '?', query)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip().lower()

    def get_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent slow queries."""
        return sorted(
            self.slow_queries[-limit:], 
            key=lambda x: x['duration'], 
            reverse=True
        )

    def get_query_statistics(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """Get top queries by various metrics."""
        stats_list = []
        for query, stats in self.query_stats.items():
            stats_list.append({
                'query': query,
                **stats
            })
        
        # Sort by total duration (most expensive queries first)
        return sorted(
            stats_list, 
            key=lambda x: x['total_duration'], 
            reverse=True
        )[:top_n]

    def reset_statistics(self) -> None:
        """Reset query statistics."""
        self.slow_queries.clear()
        self.query_stats.clear()
        logger.info("Query profiler statistics reset")


# Global query profiler instance
query_profiler = QueryProfiler()


def setup_query_profiling(engine: Engine) -> None:
    """Setup query profiling for SQLAlchemy engine."""
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query start time."""
        context._query_start_time = time.time()
        context._query_statement = statement
        context._query_parameters = parameters

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query completion and profile."""
        if hasattr(context, '_query_start_time'):
            duration = time.time() - context._query_start_time
            query_profiler.log_query(
                query=statement,
                duration=duration,
                params=parameters
            )


class DatabaseOptimizer:
    """Database optimization utilities."""

    @staticmethod
    def optimize_connection_pool(engine: Engine) -> None:
        """Optimize database connection pool settings."""
        if isinstance(engine.pool, QueuePool):
            # Optimize pool settings for performance
            engine.pool._pool_size = 20
            engine.pool._max_overflow = 30
            engine.pool._pre_ping = True
            logger.info("Database connection pool optimized")

    @staticmethod
    async def warm_up_connections(engine, count: int = 5) -> None:
        """Warm up database connections."""
        tasks = []
        for _ in range(count):
            tasks.append(DatabaseOptimizer._create_test_connection(engine))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Warmed up {count} database connections")

    @staticmethod
    async def _create_test_connection(engine):
        """Create a test connection to warm up the pool."""
        async with AsyncSession(engine) as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar()

    @staticmethod
    def get_connection_pool_status(engine: Engine) -> Dict[str, Any]:
        """Get connection pool status information."""
        if hasattr(engine, 'pool'):
            pool = engine.pool
            return {
                'pool_size': getattr(pool, '_pool_size', 'N/A'),
                'checked_in': getattr(pool, 'checkedin', 'N/A'),
                'checked_out': getattr(pool, 'checkedout', 'N/A'),
                'overflow': getattr(pool, 'overflow', 'N/A'),
                'invalid': getattr(pool, 'invalidated', 'N/A'),
            }
        return {'status': 'No pool information available'}


class QueryOptimizer:
    """Query optimization utilities."""

    @staticmethod
    def analyze_index_usage(db: Session, table_name: str) -> Dict[str, Any]:
        """Analyze index usage for a table (PostgreSQL specific)."""
        query = text("""
            SELECT 
                indexname,
                idx_scan as scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes 
            WHERE relname = :table_name
            ORDER BY idx_scan DESC
        """)
        
        result = db.execute(query, {'table_name': table_name})
        indexes = []
        for row in result:
            indexes.append({
                'index_name': row[0],
                'scans': row[1] or 0,
                'tuples_read': row[2] or 0,
                'tuples_fetched': row[3] or 0
            })
        
        return {
            'table_name': table_name,
            'indexes': indexes
        }

    @staticmethod
    def get_table_sizes(db: Session) -> List[Dict[str, Any]]:
        """Get table sizes (PostgreSQL specific)."""
        query = text("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(tablename::text)) as size,
                pg_total_relation_size(tablename::text) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(tablename::text) DESC
        """)
        
        result = db.execute(query)
        tables = []
        for row in result:
            tables.append({
                'table_name': row[0],
                'size': row[1],
                'size_bytes': row[2]
            })
        
        return tables

    @staticmethod
    def suggest_indexes(slow_queries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Suggest indexes based on slow queries."""
        suggestions = []
        
        for query_info in slow_queries:
            query = query_info['query'].lower()
            
            # Simple heuristics for index suggestions
            if 'where' in query and 'order by' in query:
                suggestions.append({
                    'query': query_info['query'][:100] + '...',
                    'suggestion': 'Consider composite index on WHERE and ORDER BY columns',
                    'priority': 'high' if query_info['duration'] > 1.0 else 'medium'
                })
            elif 'join' in query:
                suggestions.append({
                    'query': query_info['query'][:100] + '...',
                    'suggestion': 'Consider indexes on JOIN columns',
                    'priority': 'medium'
                })
        
        return suggestions


# Context managers for database monitoring
@contextmanager
def monitor_db_query(operation_name: str):
    """Context manager for monitoring database queries."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(f"DB operation '{operation_name}' took {duration:.3f}s")


@asynccontextmanager
async def monitor_async_db_query(operation_name: str):
    """Async context manager for monitoring database queries."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(f"Async DB operation '{operation_name}' took {duration:.3f}s")


# Decorators for query monitoring
def monitor_query(operation_name: Optional[str] = None):
    """Decorator for monitoring database query performance."""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with monitor_async_db_query(name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with monitor_db_query(name):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


# Database health check
async def check_database_health(db: Union[Session, AsyncSession]) -> Dict[str, Any]:
    """Check database health and performance metrics."""
    health_info = {
        'status': 'healthy',
        'query_profiler': {
            'enabled': query_profiler.enabled,
            'slow_queries_count': len(query_profiler.slow_queries),
            'total_queries_tracked': len(query_profiler.query_stats)
        },
        'performance_metrics': {}
    }
    
    try:
        # Test basic connectivity
        if hasattr(db, 'execute'):  # AsyncSession
            start_time = time.time()
            result = await db.execute(text("SELECT 1"))
            response_time = time.time() - start_time
        else:  # Session
            start_time = time.time()
            result = db.execute(text("SELECT 1"))
            response_time = time.time() - start_time
        
        health_info['performance_metrics']['response_time'] = response_time
        health_info['performance_metrics']['connectivity'] = 'ok'
        
        # Get recent slow queries summary
        slow_queries = query_profiler.get_slow_queries(10)
        if slow_queries:
            health_info['performance_metrics']['recent_slow_queries'] = len(slow_queries)
            health_info['performance_metrics']['slowest_query_duration'] = max(
                q['duration'] for q in slow_queries
            )
        
    except Exception as e:
        health_info['status'] = 'unhealthy'
        health_info['error'] = str(e)
    
    return health_info


# Performance analysis utilities
class PerformanceAnalyzer:
    """Database performance analysis utilities."""
    
    @staticmethod
    def generate_performance_report() -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        slow_queries = query_profiler.get_slow_queries()
        query_stats = query_profiler.get_query_statistics()
        
        report = {
            'timestamp': time.time(),
            'summary': {
                'total_queries_tracked': len(query_profiler.query_stats),
                'slow_queries_count': len(slow_queries),
                'avg_slow_query_duration': sum(q['duration'] for q in slow_queries) / len(slow_queries) if slow_queries else 0,
                'slowest_query_duration': max((q['duration'] for q in slow_queries), default=0)
            },
            'top_slow_queries': slow_queries[:10],
            'top_expensive_queries': query_stats[:10],
            'index_suggestions': QueryOptimizer.suggest_indexes(slow_queries[:20])
        }
        
        return report
    
    @staticmethod
    def export_performance_data(format: str = 'json') -> str:
        """Export performance data in specified format."""
        report = PerformanceAnalyzer.generate_performance_report()
        
        if format.lower() == 'json':
            import json
            return json.dumps(report, indent=2, default=str)
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write slow queries
            writer.writerow(['Query', 'Duration', 'Timestamp'])
            for query in report['top_slow_queries']:
                writer.writerow([
                    query['query'][:100],
                    query['duration'],
                    query['timestamp']
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# Initialize database optimization
def initialize_database_optimization(engine: Engine) -> None:
    """Initialize database optimization features."""
    logger.info("Initializing database optimization...")
    
    # Setup query profiling
    setup_query_profiling(engine)
    
    # Optimize connection pool
    DatabaseOptimizer.optimize_connection_pool(engine)
    
    logger.info("Database optimization initialized")