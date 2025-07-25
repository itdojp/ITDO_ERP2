"""
CC02 v55.0 Performance Optimizer
Advanced Performance Monitoring and Optimization System
Day 6 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union, Set, Tuple, Callable
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import asyncio
import time
import psutil
import json
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import statistics
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import QueuePool

from app.core.database import get_db
from app.core.exceptions import PerformanceError, OptimizationError
from app.models.performance import (
    PerformanceMetric, OptimizationRule, CacheEntry, QueryProfile,
    ResourceMonitor, PerformanceAlert, SystemHealth
)
from app.services.audit_service import AuditService

class MetricType(str, Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    DATABASE_CONNECTIONS = "database_connections"
    API_RESPONSE_TIME = "api_response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    QUEUE_SIZE = "queue_size"

class OptimizationType(str, Enum):
    QUERY_OPTIMIZATION = "query_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    INDEX_OPTIMIZATION = "index_optimization"
    CONNECTION_POOLING = "connection_pooling"
    MEMORY_OPTIMIZATION = "memory_optimization"
    ASYNC_OPTIMIZATION = "async_optimization"
    BATCH_PROCESSING = "batch_processing"
    COMPRESSION = "compression"

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class CacheStrategy(str, Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    metrics: Dict[MetricType, float]
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation"""
    id: UUID
    optimization_type: OptimizationType
    priority: int
    description: str
    estimated_improvement: float
    implementation_cost: int
    affected_components: List[str]
    recommended_actions: List[str]
    created_at: datetime

@dataclass
class QueryAnalysis:
    """SQL query analysis result"""
    query_hash: str
    query_text: str
    execution_count: int
    total_execution_time: float
    average_execution_time: float
    max_execution_time: float
    rows_affected: int
    tables_accessed: List[str]
    indexes_used: List[str]
    optimization_opportunities: List[str]

class BaseOptimizer(ABC):
    """Base class for performance optimizers"""
    
    def __init__(self, optimizer_id: str):
        self.optimizer_id = optimizer_id
        self.enabled = True
    
    @abstractmethod
    async def analyze(self, metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze metrics and generate recommendations"""
        pass
    
    @abstractmethod
    async def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply optimization recommendation"""
        pass

class QueryOptimizer(BaseOptimizer):
    """SQL query performance optimizer"""
    
    def __init__(self):
        super().__init__("query_optimizer")
        self.query_profiles: Dict[str, QueryAnalysis] = {}
        self.slow_query_threshold = 1.0  # seconds
    
    async def analyze(self, metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze query performance"""
        recommendations = []
        
        # Analyze slow queries
        slow_queries = [
            profile for profile in self.query_profiles.values()
            if profile.average_execution_time > self.slow_query_threshold
        ]
        
        for query in slow_queries:
            # Check for missing indexes
            if not query.indexes_used and len(query.tables_accessed) > 0:
                recommendations.append(OptimizationRecommendation(
                    id=uuid4(),
                    optimization_type=OptimizationType.INDEX_OPTIMIZATION,
                    priority=8,
                    description=f"Add indexes to improve query performance: {query.query_hash[:10]}...",
                    estimated_improvement=query.average_execution_time * 0.7,
                    implementation_cost=3,
                    affected_components=query.tables_accessed,
                    recommended_actions=[
                        f"CREATE INDEX ON {table} (column)" for table in query.tables_accessed
                    ],
                    created_at=datetime.utcnow()
                ))
            
            # Check for inefficient queries
            if query.rows_affected > 10000 and query.average_execution_time > 2.0:
                recommendations.append(OptimizationRecommendation(
                    id=uuid4(),
                    optimization_type=OptimizationType.QUERY_OPTIMIZATION,
                    priority=9,
                    description=f"Optimize query structure: {query.query_hash[:10]}...",
                    estimated_improvement=query.average_execution_time * 0.5,
                    implementation_cost=5,
                    affected_components=query.tables_accessed,
                    recommended_actions=[
                        "Add WHERE clauses to limit result set",
                        "Consider query rewriting",
                        "Use LIMIT for pagination"
                    ],
                    created_at=datetime.utcnow()
                ))
        
        return recommendations
    
    async def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply query optimization"""
        try:
            if recommendation.optimization_type == OptimizationType.INDEX_OPTIMIZATION:
                # In production, would execute CREATE INDEX statements
                logging.info(f"Would create indexes: {recommendation.recommended_actions}")
                return True
            elif recommendation.optimization_type == OptimizationType.QUERY_OPTIMIZATION:
                # In production, would apply query rewrites
                logging.info(f"Would optimize queries: {recommendation.recommended_actions}")
                return True
            
            return False
        except Exception as e:
            logging.error(f"Failed to apply query optimization: {e}")
            return False
    
    async def profile_query(
        self,
        query_text: str,
        execution_time: float,
        rows_affected: int,
        session: AsyncSession
    ):
        """Profile a query execution"""
        query_hash = str(hash(query_text))
        
        if query_hash in self.query_profiles:
            profile = self.query_profiles[query_hash]
            profile.execution_count += 1
            profile.total_execution_time += execution_time
            profile.average_execution_time = profile.total_execution_time / profile.execution_count
            profile.max_execution_time = max(profile.max_execution_time, execution_time)
            profile.rows_affected += rows_affected
        else:
            # Analyze query structure
            tables_accessed = self._extract_tables(query_text)
            indexes_used = await self._get_query_indexes(query_text, session)
            optimization_opportunities = self._identify_optimizations(query_text)
            
            self.query_profiles[query_hash] = QueryAnalysis(
                query_hash=query_hash,
                query_text=query_text,
                execution_count=1,
                total_execution_time=execution_time,
                average_execution_time=execution_time,
                max_execution_time=execution_time,
                rows_affected=rows_affected,
                tables_accessed=tables_accessed,
                indexes_used=indexes_used,
                optimization_opportunities=optimization_opportunities
            )
    
    def _extract_tables(self, query_text: str) -> List[str]:
        """Extract table names from query"""
        # Simplified table extraction
        import re
        tables = []
        
        # Match FROM clauses
        from_matches = re.findall(r'FROM\s+(\w+)', query_text, re.IGNORECASE)
        tables.extend(from_matches)
        
        # Match JOIN clauses
        join_matches = re.findall(r'JOIN\s+(\w+)', query_text, re.IGNORECASE)
        tables.extend(join_matches)
        
        return list(set(tables))
    
    async def _get_query_indexes(self, query_text: str, session: AsyncSession) -> List[str]:
        """Get indexes used by query"""
        # In production, would use EXPLAIN ANALYZE
        # For now, return empty list
        return []
    
    def _identify_optimizations(self, query_text: str) -> List[str]:
        """Identify optimization opportunities"""
        opportunities = []
        
        if "SELECT *" in query_text.upper():
            opportunities.append("Avoid SELECT * - specify needed columns")
        
        if "ORDER BY" in query_text.upper() and "LIMIT" not in query_text.upper():
            opportunities.append("Consider adding LIMIT to ORDER BY queries")
        
        if query_text.upper().count("JOIN") > 3:
            opportunities.append("Complex joins - consider query restructuring")
        
        return opportunities

class CacheOptimizer(BaseOptimizer):
    """Cache performance optimizer"""
    
    def __init__(self):
        super().__init__("cache_optimizer")
        self.cache_stats: Dict[str, Dict[str, Any]] = {}
        self.cache_strategies: Dict[str, CacheStrategy] = {}
    
    async def analyze(self, metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze cache performance"""
        recommendations = []
        
        cache_hit_rate = metrics.metrics.get(MetricType.CACHE_HIT_RATE, 100.0)
        
        if cache_hit_rate < 80.0:
            recommendations.append(OptimizationRecommendation(
                id=uuid4(),
                optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                priority=7,
                description=f"Cache hit rate is low: {cache_hit_rate:.1f}%",
                estimated_improvement=20.0,  # 20% response time improvement
                implementation_cost=2,
                affected_components=["cache_layer"],
                recommended_actions=[
                    "Increase cache size",
                    "Optimize cache key strategy",
                    "Implement cache warming",
                    "Review cache TTL settings"
                ],
                created_at=datetime.utcnow()
            ))
        
        # Analyze cache strategies
        for cache_name, stats in self.cache_stats.items():
            hit_rate = stats.get('hit_rate', 0)
            eviction_rate = stats.get('eviction_rate', 0)
            
            if hit_rate < 70.0 and eviction_rate > 20.0:
                recommendations.append(OptimizationRecommendation(
                    id=uuid4(),
                    optimization_type=OptimizationType.CACHE_OPTIMIZATION,
                    priority=6,
                    description=f"Cache {cache_name} has high eviction rate",
                    estimated_improvement=15.0,
                    implementation_cost=3,
                    affected_components=[cache_name],
                    recommended_actions=[
                        "Increase cache memory allocation",
                        "Implement LFU eviction strategy",
                        "Optimize cache key distribution"
                    ],
                    created_at=datetime.utcnow()
                ))
        
        return recommendations
    
    async def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply cache optimization"""
        try:
            if recommendation.optimization_type == OptimizationType.CACHE_OPTIMIZATION:
                # Apply cache optimizations
                for component in recommendation.affected_components:
                    if component == "cache_layer":
                        # Optimize global cache settings
                        await self._optimize_cache_settings()
                    else:
                        # Optimize specific cache
                        await self._optimize_cache(component)
                return True
            
            return False
        except Exception as e:
            logging.error(f"Failed to apply cache optimization: {e}")
            return False
    
    async def _optimize_cache_settings(self):
        """Optimize cache settings"""
        logging.info("Optimizing cache settings")
        # In production, would adjust cache configuration
    
    async def _optimize_cache(self, cache_name: str):
        """Optimize specific cache"""
        logging.info(f"Optimizing cache: {cache_name}")
        # In production, would adjust cache-specific settings

class MemoryOptimizer(BaseOptimizer):
    """Memory usage optimizer"""
    
    def __init__(self):
        super().__init__("memory_optimizer")
        self.memory_threshold = 80.0  # 80% memory usage threshold
    
    async def analyze(self, metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze memory usage"""
        recommendations = []
        
        memory_usage = metrics.metrics.get(MetricType.MEMORY_USAGE, 0.0)
        
        if memory_usage > self.memory_threshold:
            recommendations.append(OptimizationRecommendation(
                id=uuid4(),
                optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                priority=8,
                description=f"High memory usage: {memory_usage:.1f}%",
                estimated_improvement=memory_usage - 70.0,  # Target 70% usage
                implementation_cost=4,
                affected_components=["application"],
                recommended_actions=[
                    "Implement object pooling",
                    "Optimize data structures",
                    "Add memory profiling",
                    "Implement garbage collection tuning"
                ],
                created_at=datetime.utcnow()
            ))
        
        return recommendations
    
    async def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply memory optimization"""
        try:
            if recommendation.optimization_type == OptimizationType.MEMORY_OPTIMIZATION:
                # Apply memory optimizations
                await self._optimize_memory_usage()
                return True
            
            return False
        except Exception as e:
            logging.error(f"Failed to apply memory optimization: {e}")
            return False
    
    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        logging.info("Optimizing memory usage")
        # In production, would implement memory optimizations

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.monitoring_interval = 10  # seconds
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect system performance metrics"""
        
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_rate = disk_io.read_bytes if disk_io else 0
        disk_write_rate = disk_io.write_bytes if disk_io else 0
        
        # Network I/O
        network_io = psutil.net_io_counters()
        network_read_rate = network_io.bytes_recv if network_io else 0
        network_write_rate = network_io.bytes_sent if network_io else 0
        
        metrics = PerformanceMetrics(
            timestamp=datetime.utcnow(),
            metrics={
                MetricType.CPU_USAGE: cpu_usage,
                MetricType.MEMORY_USAGE: memory_usage,
                MetricType.DISK_IO: disk_read_rate + disk_write_rate,
                MetricType.NETWORK_IO: network_read_rate + network_write_rate,
            },
            labels={
                "host": "localhost",
                "service": "itdo_erp"
            }
        )
        
        # Store in history
        self.metrics_history.append(metrics)
        
        # Limit history size
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
        
        return metrics
    
    def get_metrics_summary(self, period_minutes: int = 60) -> Dict[str, Any]:
        """Get metrics summary for specified period"""
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=period_minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        summary = {}
        
        for metric_type in MetricType:
            values = [
                m.metrics.get(metric_type, 0)
                for m in recent_metrics
                if metric_type in m.metrics
            ]
            
            if values:
                summary[metric_type.value] = {
                    'current': values[-1],
                    'average': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'median': statistics.median(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0
                }
        
        return summary

class AlertManager:
    """Performance alert management"""
    
    def __init__(self):
        self.alert_rules: Dict[str, Dict[str, Any]] = {
            'high_cpu': {
                'metric': MetricType.CPU_USAGE,
                'threshold': 90.0,
                'operator': '>',
                'severity': AlertSeverity.WARNING,
                'duration': 300  # 5 minutes
            },
            'high_memory': {
                'metric': MetricType.MEMORY_USAGE,
                'threshold': 85.0,
                'operator': '>',
                'severity': AlertSeverity.WARNING,
                'duration': 300
            },
            'slow_response': {
                'metric': MetricType.API_RESPONSE_TIME,
                'threshold': 2000.0,  # 2 seconds
                'operator': '>',
                'severity': AlertSeverity.CRITICAL,
                'duration': 60
            },
            'high_error_rate': {
                'metric': MetricType.ERROR_RATE,
                'threshold': 5.0,  # 5%
                'operator': '>',
                'severity': AlertSeverity.CRITICAL,
                'duration': 120
            }
        }
        self.active_alerts: Dict[str, datetime] = {}
    
    async def evaluate_alerts(self, metrics: PerformanceMetrics) -> List[Dict[str, Any]]:
        """Evaluate alert conditions"""
        
        alerts = []
        current_time = datetime.utcnow()
        
        for rule_name, rule in self.alert_rules.items():
            metric_type = rule['metric']
            threshold = rule['threshold']
            operator = rule['operator']
            severity = rule['severity']
            duration = rule['duration']
            
            current_value = metrics.metrics.get(metric_type, 0)
            
            # Check if condition is met
            condition_met = False
            if operator == '>':
                condition_met = current_value > threshold
            elif operator == '<':
                condition_met = current_value < threshold
            elif operator == '>=':
                condition_met = current_value >= threshold
            elif operator == '<=':
                condition_met = current_value <= threshold
            
            if condition_met:
                if rule_name not in self.active_alerts:
                    # Start tracking this alert
                    self.active_alerts[rule_name] = current_time
                else:
                    # Check if duration threshold is met
                    alert_duration = (current_time - self.active_alerts[rule_name]).total_seconds()
                    if alert_duration >= duration:
                        alerts.append({
                            'rule_name': rule_name,
                            'metric': metric_type.value,
                            'current_value': current_value,
                            'threshold': threshold,
                            'severity': severity.value,
                            'duration': alert_duration,
                            'message': f"{metric_type.value} is {current_value} (threshold: {threshold})",
                            'triggered_at': self.active_alerts[rule_name].isoformat()
                        })
            else:
                # Clear alert if condition is no longer met
                if rule_name in self.active_alerts:
                    del self.active_alerts[rule_name]
        
        return alerts

class PerformanceOptimizer:
    """Main performance optimization engine"""
    
    def __init__(self):
        self.optimizers: List[BaseOptimizer] = [
            QueryOptimizer(),
            CacheOptimizer(),
            MemoryOptimizer()
        ]
        self.system_monitor = SystemMonitor()
        self.alert_manager = AlertManager()
        self.audit_service = AuditService()
        self.optimization_history: List[OptimizationRecommendation] = []
        self.applied_optimizations: Set[UUID] = set()
    
    async def start_monitoring(self):
        """Start performance monitoring loop"""
        while True:
            try:
                # Collect metrics
                metrics = await self.system_monitor.collect_metrics()
                
                # Evaluate alerts
                alerts = await self.alert_manager.evaluate_alerts(metrics)
                
                if alerts:
                    await self._handle_alerts(alerts)
                
                # Generate optimization recommendations
                await self._generate_recommendations(metrics)
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.system_monitor.monitoring_interval)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _handle_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle performance alerts"""
        for alert in alerts:
            await self.audit_service.log_event(
                event_type="performance_alert",
                entity_type="system",
                entity_id=None,
                details=alert
            )
            
            logging.warning(f"Performance alert: {alert['message']}")
    
    async def _generate_recommendations(self, metrics: PerformanceMetrics):
        """Generate optimization recommendations"""
        
        all_recommendations = []
        
        for optimizer in self.optimizers:
            if optimizer.enabled:
                try:
                    recommendations = await optimizer.analyze(metrics)
                    all_recommendations.extend(recommendations)
                except Exception as e:
                    logging.error(f"Error in optimizer {optimizer.optimizer_id}: {e}")
        
        # Store new recommendations
        for recommendation in all_recommendations:
            if recommendation.id not in [r.id for r in self.optimization_history]:
                self.optimization_history.append(recommendation)
                
                await self.audit_service.log_event(
                    event_type="optimization_recommendation",
                    entity_type="performance",
                    entity_id=recommendation.id,
                    details={
                        'optimization_type': recommendation.optimization_type.value,
                        'priority': recommendation.priority,
                        'description': recommendation.description,
                        'estimated_improvement': recommendation.estimated_improvement
                    }
                )
    
    async def get_recommendations(
        self,
        optimization_type: Optional[OptimizationType] = None,
        min_priority: int = 0,
        limit: int = 50
    ) -> List[OptimizationRecommendation]:
        """Get optimization recommendations"""
        
        recommendations = self.optimization_history
        
        # Filter by optimization type
        if optimization_type:
            recommendations = [
                r for r in recommendations
                if r.optimization_type == optimization_type
            ]
        
        # Filter by priority
        recommendations = [
            r for r in recommendations
            if r.priority >= min_priority
        ]
        
        # Sort by priority and creation time
        recommendations.sort(
            key=lambda r: (-r.priority, r.created_at),
            reverse=False
        )
        
        return recommendations[:limit]
    
    async def apply_recommendation(self, recommendation_id: UUID) -> bool:
        """Apply optimization recommendation"""
        
        if recommendation_id in self.applied_optimizations:
            return True  # Already applied
        
        # Find recommendation
        recommendation = next(
            (r for r in self.optimization_history if r.id == recommendation_id),
            None
        )
        
        if not recommendation:
            return False
        
        # Find appropriate optimizer
        optimizer = next(
            (o for o in self.optimizers 
             if o.optimizer_id == recommendation.optimization_type.value.replace('_', '_optimizer')),
            None
        )
        
        if not optimizer:
            return False
        
        try:
            success = await optimizer.apply_optimization(recommendation)
            
            if success:
                self.applied_optimizations.add(recommendation_id)
                
                await self.audit_service.log_event(
                    event_type="optimization_applied",
                    entity_type="performance",
                    entity_id=recommendation_id,
                    details={
                        'optimization_type': recommendation.optimization_type.value,
                        'description': recommendation.description,
                        'estimated_improvement': recommendation.estimated_improvement
                    }
                )
            
            return success
            
        except Exception as e:
            logging.error(f"Error applying optimization {recommendation_id}: {e}")
            return False
    
    async def get_performance_summary(
        self,
        period_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get performance summary"""
        
        metrics_summary = self.system_monitor.get_metrics_summary(period_minutes)
        
        # Get active alerts
        active_alerts = [
            {
                'rule_name': rule_name,
                'active_since': start_time.isoformat(),
                'duration': (datetime.utcnow() - start_time).total_seconds()
            }
            for rule_name, start_time in self.alert_manager.active_alerts.items()
        ]
        
        # Get recent recommendations
        recent_recommendations = [
            {
                'id': str(r.id),
                'type': r.optimization_type.value,
                'priority': r.priority,
                'description': r.description,
                'estimated_improvement': r.estimated_improvement,
                'applied': r.id in self.applied_optimizations
            }
            for r in self.optimization_history[-10:]  # Last 10 recommendations
        ]
        
        return {
            'period_minutes': period_minutes,
            'metrics': metrics_summary,
            'active_alerts': active_alerts,
            'recent_recommendations': recent_recommendations,
            'total_recommendations': len(self.optimization_history),
            'applied_optimizations': len(self.applied_optimizations),
            'optimizers_status': [
                {
                    'id': optimizer.optimizer_id,
                    'enabled': optimizer.enabled
                }
                for optimizer in self.optimizers
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
    
    async def benchmark_operation(
        self,
        operation_name: str,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Benchmark an operation"""
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = await operation_func(*args, **kwargs) if asyncio.iscoroutinefunction(operation_func) else operation_func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        benchmark_result = {
            'operation_name': operation_name,
            'success': success,
            'execution_time': execution_time,
            'memory_delta': memory_delta,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log benchmark result
        await self.audit_service.log_event(
            event_type="operation_benchmark",
            entity_type="performance",
            entity_id=None,
            details=benchmark_result
        )
        
        return benchmark_result

# Singleton instance
performance_optimizer = PerformanceOptimizer()

# Helper functions
async def start_performance_monitoring():
    """Start performance monitoring"""
    await performance_optimizer.start_monitoring()

async def get_performance_metrics(period_minutes: int = 60) -> Dict[str, Any]:
    """Get performance metrics"""
    return await performance_optimizer.get_performance_summary(period_minutes)

async def get_optimization_recommendations(
    optimization_type: Optional[OptimizationType] = None,
    min_priority: int = 0
) -> List[OptimizationRecommendation]:
    """Get optimization recommendations"""
    return await performance_optimizer.get_recommendations(optimization_type, min_priority)

async def apply_optimization(recommendation_id: UUID) -> bool:
    """Apply optimization recommendation"""
    return await performance_optimizer.apply_recommendation(recommendation_id)

async def benchmark_operation(operation_name: str, operation_func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Benchmark operation performance"""
    return await performance_optimizer.benchmark_operation(operation_name, operation_func, *args, **kwargs)