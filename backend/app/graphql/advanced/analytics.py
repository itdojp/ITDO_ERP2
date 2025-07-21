"""Advanced GraphQL analytics and monitoring system."""

import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.core.monitoring import monitor_performance


class QueryType(str, Enum):
    """GraphQL operation types."""
    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"
    INTROSPECTION = "introspection"


class AnalyticsMetric(str, Enum):
    """Analytics metric types."""
    EXECUTION_TIME = "execution_time"
    COMPLEXITY_SCORE = "complexity_score"
    ERROR_RATE = "error_rate"
    USAGE_FREQUENCY = "usage_frequency"
    CACHE_HIT_RATE = "cache_hit_rate"
    RESOLVER_PERFORMANCE = "resolver_performance"


@dataclass
class QueryExecution:
    """Query execution record for analytics."""
    id: str
    query_hash: str
    query_type: QueryType
    operation_name: Optional[str]
    complexity_score: int
    execution_time_ms: float
    error: Optional[str]
    user_id: Optional[str]
    ip_address: str
    timestamp: datetime
    field_count: int
    depth: int
    cache_hit: bool = False
    resolver_count: int = 0
    variables_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class PerformanceMetrics:
    """Performance metrics aggregation."""
    total_executions: int
    avg_execution_time_ms: float
    p95_execution_time_ms: float
    p99_execution_time_ms: float
    avg_complexity_score: float
    error_rate_percentage: float
    cache_hit_rate_percentage: float
    queries_per_minute: float
    unique_operations: int
    slowest_operations: List[Tuple[str, float]]  # (operation_name, avg_time)


@dataclass
class UsageAnalytics:
    """Usage analytics aggregation."""
    popular_operations: Dict[str, int]
    popular_fields: Dict[str, int]
    user_activity: Dict[str, int]
    hourly_distribution: Dict[int, int]
    error_patterns: Dict[str, int]
    complexity_distribution: Dict[str, int]  # low, medium, high, critical


@dataclass
class SecurityAnalytics:
    """Security-focused analytics."""
    suspicious_queries: List[QueryExecution]
    blocked_queries: int
    rate_limited_ips: Set[str]
    introspection_attempts: int
    high_complexity_queries: int
    repeated_failures: Dict[str, int]  # ip -> failure count


class QueryAnalyzer:
    """Advanced query pattern analysis."""
    
    def __init__(self):
        """Initialize query analyzer."""
        self.execution_history: deque = deque(maxlen=50000)
        self.query_patterns: Dict[str, Dict[str, Any]] = {}
        self.field_usage: defaultdict = defaultdict(int)
        self.operation_registry: Dict[str, Dict[str, Any]] = {}
        self.performance_baselines: Dict[str, float] = {}
    
    @monitor_performance("graphql.analytics.record_execution")
    def record_execution(self, execution: QueryExecution) -> None:
        """Record query execution for analysis."""
        self.execution_history.append(execution)
        
        # Update query patterns
        self._update_query_patterns(execution)
        
        # Update field usage
        self._update_field_usage(execution)
        
        # Update operation registry
        self._update_operation_registry(execution)
        
        # Update performance baselines
        self._update_performance_baselines(execution)
    
    def _update_query_patterns(self, execution: QueryExecution) -> None:
        """Update query pattern statistics."""
        pattern_key = f"{execution.query_type}_{execution.complexity_score//100}"
        
        if pattern_key not in self.query_patterns:
            self.query_patterns[pattern_key] = {
                "count": 0,
                "avg_execution_time": 0.0,
                "avg_complexity": 0.0,
                "error_count": 0,
                "last_seen": execution.timestamp
            }
        
        pattern = self.query_patterns[pattern_key]
        pattern["count"] += 1
        pattern["avg_execution_time"] = (
            (pattern["avg_execution_time"] * (pattern["count"] - 1) + execution.execution_time_ms) /
            pattern["count"]
        )
        pattern["avg_complexity"] = (
            (pattern["avg_complexity"] * (pattern["count"] - 1) + execution.complexity_score) /
            pattern["count"]
        )
        if execution.error:
            pattern["error_count"] += 1
        pattern["last_seen"] = execution.timestamp
    
    def _update_field_usage(self, execution: QueryExecution) -> None:
        """Update field usage statistics."""
        # This would parse the actual query in production
        # For now, we'll simulate based on field count
        estimated_fields = ["user", "organization", "task", "profile", "settings"]
        for field in estimated_fields[:execution.field_count]:
            self.field_usage[field] += 1
    
    def _update_operation_registry(self, execution: QueryExecution) -> None:
        """Update operation registry."""
        if execution.operation_name:
            if execution.operation_name not in self.operation_registry:
                self.operation_registry[execution.operation_name] = {
                    "count": 0,
                    "total_time": 0.0,
                    "error_count": 0,
                    "avg_complexity": 0.0,
                    "first_seen": execution.timestamp,
                    "last_seen": execution.timestamp
                }
            
            op = self.operation_registry[execution.operation_name]
            op["count"] += 1
            op["total_time"] += execution.execution_time_ms
            if execution.error:
                op["error_count"] += 1
            op["avg_complexity"] = (
                (op["avg_complexity"] * (op["count"] - 1) + execution.complexity_score) /
                op["count"]
            )
            op["last_seen"] = execution.timestamp
    
    def _update_performance_baselines(self, execution: QueryExecution) -> None:
        """Update performance baselines for operations."""
        if execution.operation_name and not execution.error:
            baseline_key = f"{execution.operation_name}_{execution.complexity_score//50}"
            
            if baseline_key not in self.performance_baselines:
                self.performance_baselines[baseline_key] = execution.execution_time_ms
            else:
                # Exponential moving average
                self.performance_baselines[baseline_key] = (
                    0.9 * self.performance_baselines[baseline_key] +
                    0.1 * execution.execution_time_ms
                )
    
    def analyze_performance_trends(self, hours: int = 24) -> PerformanceMetrics:
        """Analyze performance trends over time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_executions = [
            ex for ex in self.execution_history
            if ex.timestamp > cutoff_time
        ]
        
        if not recent_executions:
            return PerformanceMetrics(
                total_executions=0,
                avg_execution_time_ms=0.0,
                p95_execution_time_ms=0.0,
                p99_execution_time_ms=0.0,
                avg_complexity_score=0.0,
                error_rate_percentage=0.0,
                cache_hit_rate_percentage=0.0,
                queries_per_minute=0.0,
                unique_operations=0,
                slowest_operations=[]
            )
        
        # Calculate metrics
        execution_times = [ex.execution_time_ms for ex in recent_executions]
        execution_times.sort()
        
        total_executions = len(recent_executions)
        avg_execution_time = sum(execution_times) / total_executions
        p95_execution_time = execution_times[int(0.95 * total_executions)] if total_executions > 0 else 0
        p99_execution_time = execution_times[int(0.99 * total_executions)] if total_executions > 0 else 0
        
        avg_complexity = sum(ex.complexity_score for ex in recent_executions) / total_executions
        error_count = sum(1 for ex in recent_executions if ex.error)
        error_rate = (error_count / total_executions * 100) if total_executions > 0 else 0
        
        cache_hits = sum(1 for ex in recent_executions if ex.cache_hit)
        cache_hit_rate = (cache_hits / total_executions * 100) if total_executions > 0 else 0
        
        time_span_minutes = hours * 60
        queries_per_minute = total_executions / time_span_minutes if time_span_minutes > 0 else 0
        
        unique_operations = len(set(ex.operation_name for ex in recent_executions if ex.operation_name))
        
        # Calculate slowest operations
        operation_times = defaultdict(list)
        for ex in recent_executions:
            if ex.operation_name:
                operation_times[ex.operation_name].append(ex.execution_time_ms)
        
        slowest_operations = []
        for op_name, times in operation_times.items():
            avg_time = sum(times) / len(times)
            slowest_operations.append((op_name, avg_time))
        
        slowest_operations.sort(key=lambda x: x[1], reverse=True)
        slowest_operations = slowest_operations[:10]  # Top 10
        
        return PerformanceMetrics(
            total_executions=total_executions,
            avg_execution_time_ms=round(avg_execution_time, 2),
            p95_execution_time_ms=round(p95_execution_time, 2),
            p99_execution_time_ms=round(p99_execution_time, 2),
            avg_complexity_score=round(avg_complexity, 2),
            error_rate_percentage=round(error_rate, 2),
            cache_hit_rate_percentage=round(cache_hit_rate, 2),
            queries_per_minute=round(queries_per_minute, 2),
            unique_operations=unique_operations,
            slowest_operations=slowest_operations
        )
    
    def analyze_usage_patterns(self, hours: int = 24) -> UsageAnalytics:
        """Analyze usage patterns over time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_executions = [
            ex for ex in self.execution_history
            if ex.timestamp > cutoff_time
        ]
        
        # Popular operations
        operation_counts = defaultdict(int)
        for ex in recent_executions:
            if ex.operation_name:
                operation_counts[ex.operation_name] += 1
        
        # Field usage (simplified)
        field_counts = dict(self.field_usage)
        
        # User activity
        user_activity = defaultdict(int)
        for ex in recent_executions:
            if ex.user_id:
                user_activity[ex.user_id] += 1
        
        # Hourly distribution
        hourly_distribution = defaultdict(int)
        for ex in recent_executions:
            hour = ex.timestamp.hour
            hourly_distribution[hour] += 1
        
        # Error patterns
        error_patterns = defaultdict(int)
        for ex in recent_executions:
            if ex.error:
                # Categorize error types
                error_type = "unknown"
                if "permission" in ex.error.lower():
                    error_type = "permission_denied"
                elif "not found" in ex.error.lower():
                    error_type = "not_found"
                elif "validation" in ex.error.lower():
                    error_type = "validation_error"
                elif "timeout" in ex.error.lower():
                    error_type = "timeout"
                
                error_patterns[error_type] += 1
        
        # Complexity distribution
        complexity_distribution = defaultdict(int)
        for ex in recent_executions:
            if ex.complexity_score < 100:
                complexity_distribution["low"] += 1
            elif ex.complexity_score < 300:
                complexity_distribution["medium"] += 1
            elif ex.complexity_score < 600:
                complexity_distribution["high"] += 1
            else:
                complexity_distribution["critical"] += 1
        
        return UsageAnalytics(
            popular_operations=dict(operation_counts),
            popular_fields=field_counts,
            user_activity=dict(user_activity),
            hourly_distribution=dict(hourly_distribution),
            error_patterns=dict(error_patterns),
            complexity_distribution=dict(complexity_distribution)
        )
    
    def analyze_security_patterns(self, hours: int = 24) -> SecurityAnalytics:
        """Analyze security-related patterns."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_executions = [
            ex for ex in self.execution_history
            if ex.timestamp > cutoff_time
        ]
        
        # Identify suspicious queries
        suspicious_queries = []
        for ex in recent_executions:
            # High complexity queries
            if ex.complexity_score > 800:
                suspicious_queries.append(ex)
            # Queries with errors (potential probing)
            elif ex.error and "permission" not in ex.error.lower():
                suspicious_queries.append(ex)
            # Rapid successive queries from same IP
            # (Would need more sophisticated analysis in production)
        
        # Count blocked queries
        blocked_queries = len([ex for ex in recent_executions if ex.error and "blocked" in ex.error.lower()])
        
        # Rate limited IPs
        rate_limited_ips = set()
        for ex in recent_executions:
            if ex.error and "rate limit" in ex.error.lower():
                rate_limited_ips.add(ex.ip_address)
        
        # Introspection attempts
        introspection_attempts = len([
            ex for ex in recent_executions
            if ex.query_type == QueryType.INTROSPECTION
        ])
        
        # High complexity queries
        high_complexity_queries = len([
            ex for ex in recent_executions
            if ex.complexity_score > 500
        ])
        
        # Repeated failures by IP
        failure_counts = defaultdict(int)
        for ex in recent_executions:
            if ex.error:
                failure_counts[ex.ip_address] += 1
        
        return SecurityAnalytics(
            suspicious_queries=suspicious_queries[:20],  # Limit to 20 most recent
            blocked_queries=blocked_queries,
            rate_limited_ips=rate_limited_ips,
            introspection_attempts=introspection_attempts,
            high_complexity_queries=high_complexity_queries,
            repeated_failures=dict(failure_counts)
        )
    
    def detect_anomalies(self, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """Detect performance anomalies."""
        anomalies = []
        
        # Check recent executions against baselines
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        recent_executions = [
            ex for ex in self.execution_history
            if ex.timestamp > recent_time
        ]
        
        for execution in recent_executions:
            if execution.operation_name:
                baseline_key = f"{execution.operation_name}_{execution.complexity_score//50}"
                baseline = self.performance_baselines.get(baseline_key)
                
                if baseline and execution.execution_time_ms > baseline * threshold_multiplier:
                    anomalies.append({
                        "type": "performance_anomaly",
                        "operation": execution.operation_name,
                        "execution_time": execution.execution_time_ms,
                        "baseline": baseline,
                        "deviation_factor": execution.execution_time_ms / baseline,
                        "timestamp": execution.timestamp.isoformat(),
                        "query_hash": execution.query_hash
                    })
        
        return anomalies
    
    def generate_insights(self) -> List[str]:
        """Generate actionable insights from analytics."""
        insights = []
        
        # Performance insights
        performance = self.analyze_performance_trends(24)
        if performance.avg_execution_time_ms > 1000:
            insights.append("Average query execution time is over 1 second - consider optimization")
        
        if performance.error_rate_percentage > 5:
            insights.append(f"Error rate is {performance.error_rate_percentage}% - investigate common failures")
        
        if performance.cache_hit_rate_percentage < 50:
            insights.append("Cache hit rate is low - review caching strategy")
        
        # Usage insights
        usage = self.analyze_usage_patterns(24)
        popular_ops = sorted(usage.popular_operations.items(), key=lambda x: x[1], reverse=True)
        if popular_ops:
            top_operation = popular_ops[0]
            insights.append(f"Most popular operation is '{top_operation[0]}' with {top_operation[1]} executions")
        
        # Security insights
        security = self.analyze_security_patterns(24)
        if security.blocked_queries > 10:
            insights.append(f"{security.blocked_queries} queries were blocked - review security rules")
        
        if len(security.rate_limited_ips) > 5:
            insights.append(f"{len(security.rate_limited_ips)} IPs were rate limited - check for abuse")
        
        # Anomaly insights
        anomalies = self.detect_anomalies()
        if anomalies:
            insights.append(f"Detected {len(anomalies)} performance anomalies in the last 30 minutes")
        
        return insights


class GraphQLAnalytics:
    """Main GraphQL analytics system."""
    
    def __init__(self):
        """Initialize analytics system."""
        self.query_analyzer = QueryAnalyzer()
        self.realtime_metrics: Dict[str, Any] = defaultdict(int)
        self.alert_thresholds = {
            "error_rate": 10.0,  # 10%
            "avg_execution_time": 2000.0,  # 2 seconds
            "complexity_score": 800,
            "queries_per_minute": 500
        }
        self.analytics_history: deque = deque(maxlen=1000)
    
    @monitor_performance("graphql.analytics.process_execution")
    def process_execution(self, execution: QueryExecution) -> None:
        """Process query execution for analytics."""
        # Record in query analyzer
        self.query_analyzer.record_execution(execution)
        
        # Update realtime metrics
        self.realtime_metrics["total_queries"] += 1
        self.realtime_metrics["total_execution_time"] += execution.execution_time_ms
        
        if execution.error:
            self.realtime_metrics["error_count"] += 1
        
        if execution.cache_hit:
            self.realtime_metrics["cache_hits"] += 1
        
        # Check for alerts
        self._check_alert_conditions(execution)
    
    def _check_alert_conditions(self, execution: QueryExecution) -> None:
        """Check if execution triggers any alerts."""
        alerts = []
        
        # High execution time
        if execution.execution_time_ms > self.alert_thresholds["avg_execution_time"]:
            alerts.append({
                "type": "high_execution_time",
                "value": execution.execution_time_ms,
                "threshold": self.alert_thresholds["avg_execution_time"],
                "operation": execution.operation_name
            })
        
        # High complexity
        if execution.complexity_score > self.alert_thresholds["complexity_score"]:
            alerts.append({
                "type": "high_complexity",
                "value": execution.complexity_score,
                "threshold": self.alert_thresholds["complexity_score"],
                "operation": execution.operation_name
            })
        
        # Store alerts
        for alert in alerts:
            alert["timestamp"] = execution.timestamp.isoformat()
            alert["execution_id"] = execution.id
            self.analytics_history.append(alert)
    
    def get_comprehensive_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive analytics report."""
        performance = self.query_analyzer.analyze_performance_trends(hours)
        usage = self.query_analyzer.analyze_usage_patterns(hours)
        security = self.query_analyzer.analyze_security_patterns(hours)
        anomalies = self.query_analyzer.detect_anomalies()
        insights = self.query_analyzer.generate_insights()
        
        # Recent alerts
        recent_alerts = [
            alert for alert in self.analytics_history
            if datetime.fromisoformat(alert["timestamp"]) > datetime.utcnow() - timedelta(hours=hours)
        ]
        
        return {
            "performance_metrics": {
                "total_executions": performance.total_executions,
                "avg_execution_time_ms": performance.avg_execution_time_ms,
                "p95_execution_time_ms": performance.p95_execution_time_ms,
                "p99_execution_time_ms": performance.p99_execution_time_ms,
                "avg_complexity_score": performance.avg_complexity_score,
                "error_rate_percentage": performance.error_rate_percentage,
                "cache_hit_rate_percentage": performance.cache_hit_rate_percentage,
                "queries_per_minute": performance.queries_per_minute,
                "unique_operations": performance.unique_operations,
                "slowest_operations": performance.slowest_operations
            },
            "usage_analytics": {
                "popular_operations": usage.popular_operations,
                "popular_fields": usage.popular_fields,
                "user_activity_count": len(usage.user_activity),
                "hourly_distribution": usage.hourly_distribution,
                "error_patterns": usage.error_patterns,
                "complexity_distribution": usage.complexity_distribution
            },
            "security_analytics": {
                "suspicious_queries_count": len(security.suspicious_queries),
                "blocked_queries": security.blocked_queries,
                "rate_limited_ips_count": len(security.rate_limited_ips),
                "introspection_attempts": security.introspection_attempts,
                "high_complexity_queries": security.high_complexity_queries,
                "repeated_failures_count": len(security.repeated_failures)
            },
            "anomalies": anomalies,
            "insights": insights,
            "alerts": recent_alerts,
            "realtime_metrics": dict(self.realtime_metrics),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def export_analytics_data(self, format_type: str = "json") -> str:
        """Export analytics data in specified format."""
        data = self.get_comprehensive_analytics(168)  # 7 days
        
        if format_type == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_type == "csv":
            # Simplified CSV export (would be more comprehensive in production)
            lines = ["timestamp,operation,execution_time,complexity,error"]
            for execution in self.query_analyzer.execution_history:
                lines.append(f"{execution.timestamp},{execution.operation_name or 'unknown'},"
                           f"{execution.execution_time_ms},{execution.complexity_score},"
                           f"{execution.error or ''}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Global analytics instance
graphql_analytics = GraphQLAnalytics()


# Health check for analytics system
async def check_graphql_analytics_health() -> Dict[str, Any]:
    """Check GraphQL analytics system health."""
    analytics_data = graphql_analytics.get_comprehensive_analytics(1)  # Last hour
    
    # Determine health status
    health_status = "healthy"
    performance_metrics = analytics_data["performance_metrics"]
    
    if performance_metrics["error_rate_percentage"] > 15:
        health_status = "degraded"
    if performance_metrics["avg_execution_time_ms"] > 3000:
        health_status = "warning"
    
    return {
        "status": health_status,
        "analytics_summary": {
            "total_executions_1h": performance_metrics["total_executions"],
            "avg_execution_time_ms": performance_metrics["avg_execution_time_ms"],
            "error_rate_percentage": performance_metrics["error_rate_percentage"],
            "cache_hit_rate_percentage": performance_metrics["cache_hit_rate_percentage"],
            "unique_operations": performance_metrics["unique_operations"],
            "insights_count": len(analytics_data["insights"]),
            "anomalies_count": len(analytics_data["anomalies"]),
            "alerts_count": len(analytics_data["alerts"])
        },
        "data_retention": {
            "execution_history_size": len(graphql_analytics.query_analyzer.execution_history),
            "max_execution_history": graphql_analytics.query_analyzer.execution_history.maxlen,
            "analytics_history_size": len(graphql_analytics.analytics_history)
        }
    }