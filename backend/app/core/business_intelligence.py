"""Advanced Business Intelligence & Analytics Engine."""

import asyncio
import json
import math
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from app.core.monitoring import monitor_performance


class MetricType(str, Enum):
    """Types of business metrics."""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CUSTOM = "custom"


class AggregationMethod(str, Enum):
    """Data aggregation methods."""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    STDDEV = "stddev"


class ChartType(str, Enum):
    """Chart types for visualizations."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TABLE = "table"
    KPI = "kpi"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricDefinition:
    """Business metric definition."""
    id: str
    name: str
    description: str
    metric_type: MetricType
    source_table: str
    source_column: str
    aggregation_method: AggregationMethod
    filters: Dict[str, Any] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)
    time_dimension: str = "created_at"
    custom_formula: Optional[str] = None
    unit: str = ""
    target_value: Optional[float] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    id: str
    title: str
    chart_type: ChartType
    metric_ids: List[str]
    position: Dict[str, int]  # x, y, width, height
    filters: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 300  # seconds
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class Dashboard:
    """Business intelligence dashboard."""
    id: str
    name: str
    description: str
    widgets: List[DashboardWidget] = field(default_factory=list)
    shared_filters: Dict[str, Any] = field(default_factory=dict)
    owner_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class AlertRule:
    """Alert rule configuration."""
    id: str
    name: str
    description: str
    metric_id: str
    condition: str  # e.g., "value > 100", "change_percent > 10"
    severity: AlertSeverity
    notification_channels: List[str] = field(default_factory=list)
    cooldown_minutes: int = 60
    enabled: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class AlertEvent:
    """Alert event instance."""
    id: str
    rule_id: str
    metric_id: str
    severity: AlertSeverity
    message: str
    current_value: float
    threshold_value: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


class DataProcessor:
    """Data processing engine for BI analytics."""
    
    def __init__(self):
        """Initialize data processor."""
        self.data_cache: Dict[str, Dict[str, Any]] = {}
        self.processing_history: deque = deque(maxlen=1000)
    
    @monitor_performance("bi.data_processor.compute_metric")
    async def compute_metric(
        self,
        metric: MetricDefinition,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compute metric value for specified time range."""
        cache_key = f"{metric.id}_{start_date.isoformat()}_{end_date.isoformat()}_{tenant_id}"
        
        # Check cache first
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # Simulate data retrieval and processing
        await asyncio.sleep(0.1)  # Simulate database query
        
        # Generate sample data based on metric type
        data_points = self._generate_sample_data(metric, start_date, end_date)
        
        # Apply aggregation
        result = await self._apply_aggregation(data_points, metric.aggregation_method)
        
        # Calculate additional statistics
        stats = self._calculate_statistics(data_points)
        
        computed_result = {
            "metric_id": metric.id,
            "value": result,
            "data_points": data_points,
            "statistics": stats,
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "computed_at": datetime.utcnow().isoformat(),
            "unit": metric.unit
        }
        
        # Cache result
        self.data_cache[cache_key] = computed_result
        
        # Record processing
        self.processing_history.append({
            "metric_id": metric.id,
            "processing_time": 0.1,
            "data_points_count": len(data_points),
            "timestamp": datetime.utcnow()
        })
        
        return computed_result
    
    def _generate_sample_data(
        self,
        metric: MetricDefinition,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate sample data for demonstration."""
        data_points = []
        current_date = start_date
        
        # Generate daily data points
        while current_date <= end_date:
            base_value = 100
            
            # Add variation based on metric type
            if metric.metric_type == MetricType.FINANCIAL:
                variation = np.random.normal(0, 20)
                value = max(0, base_value + variation)
            elif metric.metric_type == MetricType.OPERATIONAL:
                variation = np.random.normal(0, 10)
                value = max(0, base_value + variation)
            elif metric.metric_type == MetricType.CUSTOMER:
                variation = np.random.poisson(10)
                value = base_value + variation
            else:
                variation = np.random.uniform(-15, 15)
                value = max(0, base_value + variation)
            
            data_points.append({
                "date": current_date.isoformat(),
                "value": round(value, 2),
                "metric_type": metric.metric_type.value
            })
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _apply_aggregation(
        self,
        data_points: List[Dict[str, Any]],
        method: AggregationMethod
    ) -> float:
        """Apply aggregation method to data points."""
        if not data_points:
            return 0.0
        
        values = [point["value"] for point in data_points]
        
        if method == AggregationMethod.SUM:
            return sum(values)
        elif method == AggregationMethod.AVERAGE:
            return statistics.mean(values)
        elif method == AggregationMethod.COUNT:
            return len(values)
        elif method == AggregationMethod.MIN:
            return min(values)
        elif method == AggregationMethod.MAX:
            return max(values)
        elif method == AggregationMethod.MEDIAN:
            return statistics.median(values)
        elif method == AggregationMethod.STDDEV:
            return statistics.stdev(values) if len(values) > 1 else 0.0
        else:
            return statistics.mean(values)
    
    def _calculate_statistics(self, data_points: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate additional statistics for data points."""
        if not data_points:
            return {}
        
        values = [point["value"] for point in data_points]
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "coefficient_of_variation": (statistics.stdev(values) / statistics.mean(values)) * 100 if len(values) > 1 and statistics.mean(values) != 0 else 0.0
        }


class AlertProcessor:
    """Alert processing engine."""
    
    def __init__(self):
        """Initialize alert processor."""
        self.active_alerts: Dict[str, AlertEvent] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.cooldown_tracker: Dict[str, datetime] = {}
    
    @monitor_performance("bi.alert_processor.evaluate")
    async def evaluate_alert_rules(
        self,
        rules: List[AlertRule],
        metric_values: Dict[str, float]
    ) -> List[AlertEvent]:
        """Evaluate alert rules against current metric values."""
        triggered_alerts = []
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if self._is_in_cooldown(rule.id):
                continue
            
            metric_value = metric_values.get(rule.metric_id)
            if metric_value is None:
                continue
            
            # Evaluate condition
            if await self._evaluate_condition(rule.condition, metric_value):
                alert = AlertEvent(
                    id=str(uuid4()),
                    rule_id=rule.id,
                    metric_id=rule.metric_id,
                    severity=rule.severity,
                    message=f"Alert triggered for {rule.name}: {rule.condition}",
                    current_value=metric_value,
                    threshold_value=self._extract_threshold(rule.condition)
                )
                
                triggered_alerts.append(alert)
                self.active_alerts[alert.id] = alert
                self.alert_history.append(alert)
                self.cooldown_tracker[rule.id] = datetime.utcnow()
        
        return triggered_alerts
    
    async def _evaluate_condition(self, condition: str, value: float) -> bool:
        """Evaluate alert condition."""
        try:
            # Simple condition evaluation - in production, use a more robust parser
            condition = condition.replace("value", str(value))
            return eval(condition)
        except:
            return False
    
    def _extract_threshold(self, condition: str) -> float:
        """Extract threshold value from condition string."""
        try:
            # Simple extraction - in production, use proper parsing
            import re
            numbers = re.findall(r'[\d.]+', condition)
            return float(numbers[0]) if numbers else 0.0
        except:
            return 0.0
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if alert rule is in cooldown period."""
        last_trigger = self.cooldown_tracker.get(rule_id)
        if not last_trigger:
            return False
        
        # Default cooldown of 60 minutes
        cooldown_delta = timedelta(minutes=60)
        return datetime.utcnow() - last_trigger < cooldown_delta


class ForecastingEngine:
    """Time series forecasting engine."""
    
    def __init__(self):
        """Initialize forecasting engine."""
        self.models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
    
    @monitor_performance("bi.forecasting.predict")
    async def generate_forecast(
        self,
        metric_data: List[Dict[str, Any]],
        forecast_periods: int = 30
    ) -> Dict[str, Any]:
        """Generate forecast for metric data."""
        if len(metric_data) < 10:
            return {"error": "Insufficient data for forecasting"}
        
        # Prepare data
        dates = [datetime.fromisoformat(d["date"]) for d in metric_data]
        values = [d["value"] for d in metric_data]
        
        # Convert dates to numerical values for regression
        base_date = min(dates)
        x_values = [(d - base_date).days for d in dates]
        
        # Reshape for sklearn
        X = np.array(x_values).reshape(-1, 1)
        y = np.array(values)
        
        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate predictions
        last_x = max(x_values)
        future_x = np.array([last_x + i + 1 for i in range(forecast_periods)]).reshape(-1, 1)
        predictions = model.predict(future_x)
        
        # Calculate confidence intervals (simplified)
        residuals = y - model.predict(X)
        std_error = np.std(residuals)
        
        forecast_points = []
        for i, pred in enumerate(predictions):
            future_date = base_date + timedelta(days=last_x + i + 1)
            
            forecast_points.append({
                "date": future_date.isoformat(),
                "predicted_value": round(pred, 2),
                "lower_bound": round(pred - 1.96 * std_error, 2),
                "upper_bound": round(pred + 1.96 * std_error, 2)
            })
        
        # Calculate forecast metrics
        r_squared = model.score(X, y)
        mape = np.mean(np.abs((y - model.predict(X)) / y)) * 100
        
        return {
            "forecast_points": forecast_points,
            "model_metrics": {
                "r_squared": round(r_squared, 4),
                "mape": round(mape, 2),
                "std_error": round(std_error, 2)
            },
            "trend": "increasing" if model.coef_[0] > 0 else "decreasing",
            "confidence": "high" if r_squared > 0.8 else "medium" if r_squared > 0.5 else "low"
        }


class BusinessIntelligenceEngine:
    """Main Business Intelligence engine."""
    
    def __init__(self):
        """Initialize BI engine."""
        self.metrics: Dict[str, MetricDefinition] = {}
        self.dashboards: Dict[str, Dashboard] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.data_processor = DataProcessor()
        self.alert_processor = AlertProcessor()
        self.forecasting_engine = ForecastingEngine()
        self.insights_cache: Dict[str, Dict[str, Any]] = {}
    
    # Metric Management
    async def register_metric(self, metric: MetricDefinition) -> str:
        """Register a new business metric."""
        self.metrics[metric.id] = metric
        return metric.id
    
    async def get_metric(self, metric_id: str) -> Optional[MetricDefinition]:
        """Get metric definition by ID."""
        return self.metrics.get(metric_id)
    
    async def list_metrics(self, metric_type: Optional[MetricType] = None) -> List[MetricDefinition]:
        """List all metrics, optionally filtered by type."""
        metrics = list(self.metrics.values())
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        return metrics
    
    # Dashboard Management
    async def create_dashboard(self, dashboard: Dashboard) -> str:
        """Create a new dashboard."""
        self.dashboards[dashboard.id] = dashboard
        return dashboard.id
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        return self.dashboards.get(dashboard_id)
    
    async def list_dashboards(self) -> List[Dashboard]:
        """List all dashboards."""
        return list(self.dashboards.values())
    
    # Alert Management
    async def create_alert_rule(self, rule: AlertRule) -> str:
        """Create a new alert rule."""
        self.alert_rules[rule.id] = rule
        return rule.id
    
    async def get_alert_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get alert rule by ID."""
        return self.alert_rules.get(rule_id)
    
    # Analytics
    @monitor_performance("bi.compute_analytics")
    async def compute_analytics(
        self,
        metric_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compute analytics for specified metrics."""
        results = {}
        
        for metric_id in metric_ids:
            metric = self.metrics.get(metric_id)
            if not metric:
                continue
            
            result = await self.data_processor.compute_metric(
                metric, start_date, end_date, tenant_id
            )
            results[metric_id] = result
        
        # Generate insights
        insights = await self._generate_insights(results)
        
        return {
            "metrics": results,
            "insights": insights,
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "computed_at": datetime.utcnow().isoformat()
        }
    
    async def generate_dashboard_data(
        self,
        dashboard_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate data for dashboard widgets."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return {"error": "Dashboard not found"}
        
        widget_data = {}
        
        for widget in dashboard.widgets:
            widget_results = await self.compute_analytics(
                widget.metric_ids, start_date, end_date
            )
            widget_data[widget.id] = {
                "widget_config": {
                    "title": widget.title,
                    "chart_type": widget.chart_type.value,
                    "position": widget.position
                },
                "data": widget_results
            }
        
        return {
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.name,
            "widgets": widget_data,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def generate_forecast(
        self,
        metric_id: str,
        forecast_periods: int = 30
    ) -> Dict[str, Any]:
        """Generate forecast for a metric."""
        metric = self.metrics.get(metric_id)
        if not metric:
            return {"error": "Metric not found"}
        
        # Get historical data (last 90 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        historical_data = await self.data_processor.compute_metric(
            metric, start_date, end_date
        )
        
        forecast = await self.forecasting_engine.generate_forecast(
            historical_data["data_points"], forecast_periods
        )
        
        return {
            "metric_id": metric_id,
            "historical_data": historical_data,
            "forecast": forecast,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _generate_insights(self, metric_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate business insights from metric results."""
        insights = []
        
        for metric_id, result in metric_results.items():
            metric = self.metrics.get(metric_id)
            if not metric or not result.get("statistics"):
                continue
            
            stats = result["statistics"]
            
            # Insight: High variability
            if stats.get("coefficient_of_variation", 0) > 30:
                insights.append({
                    "type": "variability",
                    "metric_id": metric_id,
                    "message": f"High variability detected in {metric.name}",
                    "impact": "medium",
                    "recommendation": "Consider investigating causes of variance"
                })
            
            # Insight: Target comparison
            if metric.target_value and "value" in result:
                current_value = result["value"]
                if current_value < metric.target_value * 0.8:
                    insights.append({
                        "type": "target_miss",
                        "metric_id": metric_id,
                        "message": f"{metric.name} is significantly below target",
                        "impact": "high",
                        "recommendation": "Review performance drivers and optimization opportunities"
                    })
                elif current_value > metric.target_value * 1.2:
                    insights.append({
                        "type": "target_exceed",
                        "metric_id": metric_id,
                        "message": f"{metric.name} significantly exceeds target",
                        "impact": "positive",
                        "recommendation": "Analyze success factors for replication"
                    })
        
        return insights
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get BI system health information."""
        return {
            "status": "healthy",
            "metrics_count": len(self.metrics),
            "dashboards_count": len(self.dashboards),
            "alert_rules_count": len(self.alert_rules),
            "active_alerts": len(self.alert_processor.active_alerts),
            "cache_size": len(self.data_processor.data_cache),
            "processing_history": len(self.data_processor.processing_history),
            "last_updated": datetime.utcnow().isoformat()
        }


# Global BI engine instance
bi_engine = BusinessIntelligenceEngine()


# Health check for Business Intelligence
async def check_business_intelligence_health() -> Dict[str, Any]:
    """Check Business Intelligence system health."""
    return await bi_engine.get_system_health()