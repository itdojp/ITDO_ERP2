"""
CC02 v77.0 Day 22 - Enterprise Integrated Performance Optimization Platform
Advanced Performance Monitoring & Analytics

Comprehensive performance monitoring with real-time analytics, predictive optimization,
and intelligent resource management for enterprise-scale ERP systems.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Import from our existing mobile SDK
from app.mobile.mobile_erp_sdk import MobileERPSDK


class MetricType(Enum):
    """Performance metric types."""

    SYSTEM = "system"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    USER_EXPERIENCE = "user_experience"
    BUSINESS = "business"
    SECURITY = "security"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AggregationType(Enum):
    """Metric aggregation types."""

    SUM = "sum"
    AVERAGE = "average"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"
    STANDARD_DEVIATION = "stddev"


class TimeWindow(Enum):
    """Time window for aggregation."""

    MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1mo"


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""

    metric_id: str
    name: str
    type: MetricType
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    source: str
    category: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""

    alert_id: str
    metric_name: str
    severity: AlertSeverity
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    source: str
    tags: Dict[str, str]
    acknowledged: bool = False
    resolved: bool = False
    escalated: bool = False
    related_metrics: List[str] = field(default_factory=list)


@dataclass
class PerformanceBaseline:
    """Performance baseline for anomaly detection."""

    metric_name: str
    baseline_type: str  # static, dynamic, ml_based
    mean_value: float
    std_deviation: float
    min_value: float
    max_value: float
    percentiles: Dict[str, float]
    sample_count: int
    last_updated: datetime
    confidence_interval: Tuple[float, float]
    seasonal_patterns: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceProfile:
    """Performance profile for system/component."""

    profile_id: str
    name: str
    description: str
    component_type: str
    baseline_metrics: Dict[str, PerformanceBaseline]
    sla_targets: Dict[str, float]
    capacity_limits: Dict[str, float]
    optimization_suggestions: List[str]
    last_analyzed: datetime
    health_score: float


class MetricCollector:
    """Real-time metric collection and aggregation."""

    def __init__(self) -> dict:
        self.collectors: Dict[str, callable] = {}
        self.metric_buffer: deque = deque(maxlen=100000)
        self.collection_interval = 30  # seconds
        self.aggregators: Dict[str, MetricAggregator] = {}
        self.running = False

        # Initialize built-in collectors
        self._initialize_collectors()

    def _initialize_collectors(self) -> None:
        """Initialize built-in metric collectors."""
        self.collectors.update(
            {
                "system_cpu": self._collect_cpu_metrics,
                "system_memory": self._collect_memory_metrics,
                "system_disk": self._collect_disk_metrics,
                "system_network": self._collect_network_metrics,
                "database_performance": self._collect_database_metrics,
                "application_performance": self._collect_application_metrics,
                "user_experience": self._collect_user_experience_metrics,
            }
        )

    async def start_collection(self) -> None:
        """Start metric collection."""
        self.running = True
        collection_tasks = []

        for collector_name, collector_func in self.collectors.items():
            task = asyncio.create_task(
                self._run_collector(collector_name, collector_func)
            )
            collection_tasks.append(task)

        # Start aggregation task
        aggregation_task = asyncio.create_task(self._run_aggregation())
        collection_tasks.append(aggregation_task)

        logging.info("Performance metric collection started")

        try:
            await asyncio.gather(*collection_tasks)
        except Exception as e:
            logging.error(f"Metric collection error: {e}")
        finally:
            self.running = False

    async def stop_collection(self) -> None:
        """Stop metric collection."""
        self.running = False
        logging.info("Performance metric collection stopped")

    async def _run_collector(self, name: str, collector_func: callable) -> None:
        """Run individual metric collector."""
        while self.running:
            try:
                metrics = await collector_func()
                for metric in metrics:
                    await self._buffer_metric(metric)

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logging.error(f"Error in collector {name}: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _buffer_metric(self, metric: PerformanceMetric) -> None:
        """Buffer metric for processing."""
        self.metric_buffer.append(metric)

    async def _run_aggregation(self) -> None:
        """Run metric aggregation process."""
        while self.running:
            try:
                # Process buffered metrics
                metrics_to_process = list(self.metric_buffer)
                self.metric_buffer.clear()

                # Group metrics by type and aggregate
                grouped_metrics = self._group_metrics(metrics_to_process)

                for metric_group, metrics in grouped_metrics.items():
                    if metric_group not in self.aggregators:
                        self.aggregators[metric_group] = MetricAggregator(metric_group)

                    await self.aggregators[metric_group].process_metrics(metrics)

                await asyncio.sleep(60)  # Aggregate every minute

            except Exception as e:
                logging.error(f"Aggregation error: {e}")
                await asyncio.sleep(60)

    def _group_metrics(
        self, metrics: List[PerformanceMetric]
    ) -> Dict[str, List[PerformanceMetric]]:
        """Group metrics by name for aggregation."""
        grouped = defaultdict(list)
        for metric in metrics:
            grouped[metric.name].extend(
                [metric] if isinstance(metric, PerformanceMetric) else []
            )
        return dict(grouped)

    # Built-in metric collectors
    async def _collect_cpu_metrics(self) -> List[PerformanceMetric]:
        """Collect CPU performance metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)

        timestamp = datetime.now()

        metrics = [
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="cpu_utilization",
                type=MetricType.SYSTEM,
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp,
                tags={"component": "cpu", "host": "localhost"},
                source="system_monitor",
                category="system_performance",
                threshold_warning=70.0,
                threshold_critical=90.0,
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="cpu_load_1m",
                type=MetricType.SYSTEM,
                value=load_avg[0],
                unit="load",
                timestamp=timestamp,
                tags={"component": "cpu", "host": "localhost", "period": "1m"},
                source="system_monitor",
                category="system_performance",
                threshold_warning=float(cpu_count * 0.7),
                threshold_critical=float(cpu_count * 0.9),
            ),
        ]

        return metrics

    async def _collect_memory_metrics(self) -> List[PerformanceMetric]:
        """Collect memory performance metrics."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        timestamp = datetime.now()

        metrics = [
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="memory_utilization",
                type=MetricType.SYSTEM,
                value=memory.percent,
                unit="percent",
                timestamp=timestamp,
                tags={"component": "memory", "host": "localhost"},
                source="system_monitor",
                category="system_performance",
                threshold_warning=80.0,
                threshold_critical=95.0,
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="memory_available",
                type=MetricType.SYSTEM,
                value=memory.available / (1024**3),  # GB
                unit="GB",
                timestamp=timestamp,
                tags={"component": "memory", "host": "localhost"},
                source="system_monitor",
                category="system_performance",
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="swap_utilization",
                type=MetricType.SYSTEM,
                value=swap.percent,
                unit="percent",
                timestamp=timestamp,
                tags={"component": "swap", "host": "localhost"},
                source="system_monitor",
                category="system_performance",
                threshold_warning=50.0,
                threshold_critical=80.0,
            ),
        ]

        return metrics

    async def _collect_disk_metrics(self) -> List[PerformanceMetric]:
        """Collect disk performance metrics."""
        disk_usage = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()

        timestamp = datetime.now()

        metrics = [
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="disk_utilization",
                type=MetricType.SYSTEM,
                value=(disk_usage.used / disk_usage.total) * 100,
                unit="percent",
                timestamp=timestamp,
                tags={"component": "disk", "host": "localhost", "mount": "/"},
                source="system_monitor",
                category="system_performance",
                threshold_warning=80.0,
                threshold_critical=95.0,
            )
        ]

        if disk_io:
            metrics.extend(
                [
                    PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        name="disk_read_ops",
                        type=MetricType.SYSTEM,
                        value=disk_io.read_count,
                        unit="ops",
                        timestamp=timestamp,
                        tags={
                            "component": "disk",
                            "host": "localhost",
                            "operation": "read",
                        },
                        source="system_monitor",
                        category="system_performance",
                    ),
                    PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        name="disk_write_ops",
                        type=MetricType.SYSTEM,
                        value=disk_io.write_count,
                        unit="ops",
                        timestamp=timestamp,
                        tags={
                            "component": "disk",
                            "host": "localhost",
                            "operation": "write",
                        },
                        source="system_monitor",
                        category="system_performance",
                    ),
                ]
            )

        return metrics

    async def _collect_network_metrics(self) -> List[PerformanceMetric]:
        """Collect network performance metrics."""
        network_io = psutil.net_io_counters()

        timestamp = datetime.now()

        metrics = []

        if network_io:
            metrics.extend(
                [
                    PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        name="network_bytes_sent",
                        type=MetricType.NETWORK,
                        value=network_io.bytes_sent,
                        unit="bytes",
                        timestamp=timestamp,
                        tags={
                            "component": "network",
                            "host": "localhost",
                            "direction": "out",
                        },
                        source="system_monitor",
                        category="network_performance",
                    ),
                    PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        name="network_bytes_recv",
                        type=MetricType.NETWORK,
                        value=network_io.bytes_recv,
                        unit="bytes",
                        timestamp=timestamp,
                        tags={
                            "component": "network",
                            "host": "localhost",
                            "direction": "in",
                        },
                        source="system_monitor",
                        category="network_performance",
                    ),
                    PerformanceMetric(
                        metric_id=str(uuid.uuid4()),
                        name="network_packets_sent",
                        type=MetricType.NETWORK,
                        value=network_io.packets_sent,
                        unit="packets",
                        timestamp=timestamp,
                        tags={
                            "component": "network",
                            "host": "localhost",
                            "direction": "out",
                        },
                        source="system_monitor",
                        category="network_performance",
                    ),
                ]
            )

        return metrics

    async def _collect_database_metrics(self) -> List[PerformanceMetric]:
        """Collect database performance metrics."""
        # Simulated database metrics - in production, integrate with actual DB monitoring
        timestamp = datetime.now()

        metrics = [
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="db_query_response_time",
                type=MetricType.DATABASE,
                value=np.random.normal(50, 15),  # Simulated response time
                unit="ms",
                timestamp=timestamp,
                tags={"component": "database", "db": "postgresql", "host": "localhost"},
                source="db_monitor",
                category="database_performance",
                threshold_warning=100.0,
                threshold_critical=200.0,
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="db_active_connections",
                type=MetricType.DATABASE,
                value=np.random.randint(10, 50),  # Simulated connections
                unit="connections",
                timestamp=timestamp,
                tags={"component": "database", "db": "postgresql", "host": "localhost"},
                source="db_monitor",
                category="database_performance",
                threshold_warning=80.0,
                threshold_critical=95.0,
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="db_transactions_per_second",
                type=MetricType.DATABASE,
                value=np.random.normal(100, 20),  # Simulated TPS
                unit="tps",
                timestamp=timestamp,
                tags={"component": "database", "db": "postgresql", "host": "localhost"},
                source="db_monitor",
                category="database_performance",
            ),
        ]

        return metrics

    async def _collect_application_metrics(self) -> List[PerformanceMetric]:
        """Collect application performance metrics."""
        # Simulated application metrics
        timestamp = datetime.now()

        metrics = [
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="api_response_time",
                type=MetricType.APPLICATION,
                value=np.random.normal(100, 30),  # Simulated API response time
                unit="ms",
                timestamp=timestamp,
                tags={"component": "api", "endpoint": "/api/v1", "host": "localhost"},
                source="app_monitor",
                category="application_performance",
                threshold_warning=200.0,
                threshold_critical=500.0,
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="api_requests_per_second",
                type=MetricType.APPLICATION,
                value=np.random.normal(50, 10),  # Simulated RPS
                unit="rps",
                timestamp=timestamp,
                tags={"component": "api", "endpoint": "/api/v1", "host": "localhost"},
                source="app_monitor",
                category="application_performance",
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="error_rate",
                type=MetricType.APPLICATION,
                value=np.random.normal(0.5, 0.2),  # Simulated error rate
                unit="percent",
                timestamp=timestamp,
                tags={"component": "api", "endpoint": "/api/v1", "host": "localhost"},
                source="app_monitor",
                category="application_performance",
                threshold_warning=2.0,
                threshold_critical=5.0,
            ),
        ]

        return metrics

    async def _collect_user_experience_metrics(self) -> List[PerformanceMetric]:
        """Collect user experience metrics."""
        # Simulated UX metrics
        timestamp = datetime.now()

        metrics = [
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="page_load_time",
                type=MetricType.USER_EXPERIENCE,
                value=np.random.normal(2.5, 0.8),  # Simulated page load time
                unit="seconds",
                timestamp=timestamp,
                tags={
                    "component": "frontend",
                    "page": "dashboard",
                    "browser": "chrome",
                },
                source="ux_monitor",
                category="user_experience",
                threshold_warning=3.0,
                threshold_critical=5.0,
            ),
            PerformanceMetric(
                metric_id=str(uuid.uuid4()),
                name="user_satisfaction_score",
                type=MetricType.USER_EXPERIENCE,
                value=np.random.normal(4.2, 0.5),  # Simulated satisfaction score
                unit="score",
                timestamp=timestamp,
                tags={"component": "frontend", "feature": "overall"},
                source="ux_monitor",
                category="user_experience",
                threshold_warning=3.0,
                threshold_critical=2.5,
            ),
        ]

        return metrics

    def add_custom_collector(self, name: str, collector_func: callable) -> None:
        """Add custom metric collector."""
        self.collectors[name] = collector_func

    def remove_collector(self, name: str) -> bool:
        """Remove metric collector."""
        if name in self.collectors:
            del self.collectors[name]
            return True
        return False


class MetricAggregator:
    """Metric aggregation and time-series processing."""

    def __init__(self, metric_name: str) -> dict:
        self.metric_name = metric_name
        self.raw_metrics: deque = deque(maxlen=10000)
        self.aggregated_data: Dict[TimeWindow, deque] = {
            window: deque(maxlen=1000) for window in TimeWindow
        }
        self.last_aggregation: Dict[TimeWindow, datetime] = {}

    async def process_metrics(self, metrics: List[PerformanceMetric]) -> None:
        """Process and aggregate incoming metrics."""
        # Store raw metrics
        self.raw_metrics.extend(metrics)

        # Trigger aggregation for different time windows
        for time_window in TimeWindow:
            await self._aggregate_metrics(time_window)

    async def _aggregate_metrics(self, time_window: TimeWindow) -> None:
        """Aggregate metrics for specific time window."""
        window_seconds = self._get_window_seconds(time_window)
        now = datetime.now()

        # Check if aggregation is needed
        last_agg = self.last_aggregation.get(
            time_window, now - timedelta(seconds=window_seconds * 2)
        )
        if (now - last_agg).total_seconds() < window_seconds:
            return

        # Get metrics within the time window
        window_start = now - timedelta(seconds=window_seconds)
        window_metrics = [m for m in self.raw_metrics if m.timestamp >= window_start]

        if not window_metrics:
            return

        # Calculate aggregations
        values = [m.value for m in window_metrics]

        aggregated_point = {
            "timestamp": now,
            "count": len(values),
            "sum": sum(values),
            "average": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0,
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99),
        }

        # Store aggregated data
        self.aggregated_data[time_window].append(aggregated_point)
        self.last_aggregation[time_window] = now

    def _get_window_seconds(self, time_window: TimeWindow) -> int:
        """Get window size in seconds."""
        window_mapping = {
            TimeWindow.MINUTE: 60,
            TimeWindow.FIVE_MINUTES: 300,
            TimeWindow.FIFTEEN_MINUTES: 900,
            TimeWindow.HOUR: 3600,
            TimeWindow.DAY: 86400,
            TimeWindow.WEEK: 604800,
            TimeWindow.MONTH: 2592000,
        }
        return window_mapping.get(time_window, 60)

    def get_aggregated_data(
        self,
        time_window: TimeWindow,
        aggregation_type: AggregationType,
        count: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get aggregated data for specific time window and aggregation type."""
        data = list(self.aggregated_data[time_window])[-count:]

        result = []
        for point in data:
            result.append(
                {
                    "timestamp": point["timestamp"],
                    "value": point[
                        aggregation_type.value.replace("p95", "p95").replace(
                            "p99", "p99"
                        )
                    ],
                }
            )

        return result


class AnomalyDetector:
    """Machine learning-based anomaly detection."""

    def __init__(self) -> dict:
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.models: Dict[str, Dict[str, Any]] = {}
        self.is_trained = False

    async def train_models(self, training_data: Dict[str, List[float]]) -> None:
        """Train anomaly detection models for different metrics."""
        for metric_name, data in training_data.items():
            if len(data) < 100:  # Need sufficient data for training
                continue

            # Prepare features (value, time-based features)
            features = self._prepare_features(data)

            # Scale features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)

            # Train isolation forest
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(scaled_features)

            # Store model and scaler
            self.models[metric_name] = {
                "model": model,
                "scaler": scaler,
                "baseline_stats": {
                    "mean": np.mean(data),
                    "std": np.std(data),
                    "min": np.min(data),
                    "max": np.max(data),
                    "p95": np.percentile(data, 95),
                    "p99": np.percentile(data, 99),
                },
            }

        self.is_trained = True
        logging.info(f"Anomaly detection models trained for {len(self.models)} metrics")

    def _prepare_features(self, data: List[float]) -> np.ndarray:
        """Prepare features for anomaly detection."""
        features = []

        for i, value in enumerate(data):
            feature_vector = [
                value,
                i % 24,  # Hour of day feature
                i % 7,  # Day of week feature
                i,  # Time trend feature
            ]
            features.append(feature_vector)

        return np.array(features)

    async def detect_anomalies(
        self, metric_name: str, recent_values: List[float]
    ) -> Dict[str, Any]:
        """Detect anomalies in recent metric values."""
        if metric_name not in self.models or not recent_values:
            return {
                "is_anomaly": False,
                "confidence": 0.0,
                "reason": "No model or data",
            }

        model_data = self.models[metric_name]
        model = model_data["model"]
        scaler = model_data["scaler"]
        baseline_stats = model_data["baseline_stats"]

        # Prepare features for recent values
        features = self._prepare_features(recent_values)
        scaled_features = scaler.transform(features)

        # Predict anomalies
        anomaly_predictions = model.predict(scaled_features)
        anomaly_scores = model.decision_function(scaled_features)

        # Check for anomalies (isolation forest returns -1 for anomalies)
        anomalies_detected = np.any(anomaly_predictions == -1)

        # Calculate confidence and additional metrics
        latest_value = recent_values[-1]
        z_score = abs(
            (latest_value - baseline_stats["mean"]) / max(baseline_stats["std"], 0.001)
        )

        # Statistical anomaly checks
        statistical_anomaly = (
            latest_value > baseline_stats["p99"]
            or latest_value < baseline_stats["min"]
            or z_score > 3.0
        )

        # Combine ML and statistical detection
        is_anomaly = anomalies_detected or statistical_anomaly

        # Calculate confidence
        confidence = min(abs(anomaly_scores[-1]) if len(anomaly_scores) > 0 else 0, 1.0)
        if statistical_anomaly:
            confidence = max(
                confidence, z_score / 5.0
            )  # Boost confidence for statistical anomalies

        # Determine reason
        reasons = []
        if anomalies_detected:
            reasons.append("ML_model_detection")
        if z_score > 3.0:
            reasons.append(f"High_z_score_{z_score:.2f}")
        if latest_value > baseline_stats["p99"]:
            reasons.append("Above_99th_percentile")

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "latest_value": latest_value,
            "baseline_mean": baseline_stats["mean"],
            "z_score": z_score,
            "reasons": reasons,
            "anomaly_score": anomaly_scores[-1] if len(anomaly_scores) > 0 else 0,
        }


class AlertManager:
    """Performance alert management and notification."""

    def __init__(self) -> dict:
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.notification_channels: List[callable] = []
        self.escalation_rules: Dict[str, Dict[str, Any]] = {}

        # Load default alert rules
        self._load_default_alert_rules()

    def _load_default_alert_rules(self) -> None:
        """Load default alerting rules."""
        self.alert_rules = {
            "cpu_utilization_high": {
                "metric_name": "cpu_utilization",
                "condition": "greater_than",
                "warning_threshold": 70.0,
                "critical_threshold": 90.0,
                "duration": 300,  # seconds
                "severity": AlertSeverity.HIGH,
            },
            "memory_utilization_high": {
                "metric_name": "memory_utilization",
                "condition": "greater_than",
                "warning_threshold": 80.0,
                "critical_threshold": 95.0,
                "duration": 300,
                "severity": AlertSeverity.HIGH,
            },
            "api_response_time_high": {
                "metric_name": "api_response_time",
                "condition": "greater_than",
                "warning_threshold": 200.0,
                "critical_threshold": 500.0,
                "duration": 180,
                "severity": AlertSeverity.MEDIUM,
            },
            "error_rate_high": {
                "metric_name": "error_rate",
                "condition": "greater_than",
                "warning_threshold": 2.0,
                "critical_threshold": 5.0,
                "duration": 120,
                "severity": AlertSeverity.HIGH,
            },
        }

    async def evaluate_metrics(
        self, metrics: List[PerformanceMetric]
    ) -> List[PerformanceAlert]:
        """Evaluate metrics against alert rules."""
        new_alerts = []

        for metric in metrics:
            # Check against alert rules
            triggered_rules = await self._check_alert_rules(metric)

            for rule_name, rule_data in triggered_rules.items():
                alert = await self._create_alert(metric, rule_name, rule_data)

                # Check if alert already exists
                alert_key = f"{metric.name}_{rule_name}"

                if alert_key not in self.active_alerts:
                    self.active_alerts[alert_key] = alert
                    new_alerts.append(alert)

                    # Send notifications
                    await self._send_notifications(alert)
                else:
                    # Update existing alert
                    existing_alert = self.active_alerts[alert_key]
                    existing_alert.current_value = metric.value
                    existing_alert.timestamp = metric.timestamp

        return new_alerts

    async def _check_alert_rules(
        self, metric: PerformanceMetric
    ) -> Dict[str, Dict[str, Any]]:
        """Check metric against alert rules."""
        triggered_rules = {}

        for rule_name, rule in self.alert_rules.items():
            if rule["metric_name"] != metric.name:
                continue

            # Check thresholds
            if metric.threshold_warning and metric.value > metric.threshold_warning:
                triggered_rules[f"{rule_name}_warning"] = {
                    **rule,
                    "threshold_value": metric.threshold_warning,
                    "severity": AlertSeverity.MEDIUM,
                }

            if metric.threshold_critical and metric.value > metric.threshold_critical:
                triggered_rules[f"{rule_name}_critical"] = {
                    **rule,
                    "threshold_value": metric.threshold_critical,
                    "severity": AlertSeverity.CRITICAL,
                }

        return triggered_rules

    async def _create_alert(
        self, metric: PerformanceMetric, rule_name: str, rule_data: Dict[str, Any]
    ) -> PerformanceAlert:
        """Create performance alert."""
        alert_id = str(uuid.uuid4())

        alert = PerformanceAlert(
            alert_id=alert_id,
            metric_name=metric.name,
            severity=rule_data["severity"],
            current_value=metric.value,
            threshold_value=rule_data["threshold_value"],
            message=f"{metric.name} is {metric.value}{metric.unit}, exceeding threshold of {rule_data['threshold_value']}{metric.unit}",
            timestamp=metric.timestamp,
            source=metric.source,
            tags=metric.tags,
        )

        return alert

    async def _send_notifications(self, alert: PerformanceAlert) -> None:
        """Send alert notifications."""
        for notification_func in self.notification_channels:
            try:
                await notification_func(alert)
            except Exception as e:
                logging.error(f"Notification error: {e}")

    def add_notification_channel(self, notification_func: callable) -> None:
        """Add notification channel."""
        self.notification_channels.append(notification_func)

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge alert."""
        for alert in self.active_alerts.values():
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve alert."""
        for alert_key, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.resolved = True
                # Remove from active alerts
                del self.active_alerts[alert_key]
                return True
        return False

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[PerformanceAlert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)


class PerformanceAnalyzer:
    """Advanced performance analysis and insights."""

    def __init__(self) -> dict:
        self.trend_analyzer = TrendAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.capacity_planner = CapacityPlanner()
        self.optimization_engine = OptimizationEngine()

    async def analyze_performance_trends(
        self, metric_data: Dict[str, List[Dict[str, Any]]], time_range: timedelta
    ) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        trends = {}

        for metric_name, data_points in metric_data.items():
            if len(data_points) < 10:  # Need sufficient data
                continue

            trend_analysis = await self.trend_analyzer.analyze_trend(data_points)
            trends[metric_name] = trend_analysis

        # Generate insights
        insights = await self._generate_trend_insights(trends)

        return {
            "trends": trends,
            "insights": insights,
            "analysis_period": time_range,
            "analyzed_metrics": len(trends),
        }

    async def _generate_trend_insights(self, trends: Dict[str, Any]) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []

        for metric_name, trend_data in trends.items():
            if trend_data.get("trend_direction") == "increasing":
                if trend_data.get("rate_of_change", 0) > 0.1:
                    insights.append(
                        f"⚠️ {metric_name} showing rapid increase - investigate potential issues"
                    )
                else:
                    insights.append(
                        f"📈 {metric_name} trending upward - monitor capacity requirements"
                    )

            elif trend_data.get("trend_direction") == "decreasing":
                if metric_name in ["error_rate", "response_time"]:
                    insights.append(
                        f"✅ {metric_name} improving - positive performance trend"
                    )
                else:
                    insights.append(
                        f"📉 {metric_name} declining - may indicate reduced utilization"
                    )

            if trend_data.get("volatility", 0) > 0.3:
                insights.append(
                    f"🔄 {metric_name} showing high volatility - check for periodic issues"
                )

        return insights

    async def detect_performance_correlations(
        self, metric_data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Detect correlations between different performance metrics."""
        correlations = await self.correlation_analyzer.find_correlations(metric_data)

        # Identify strong correlations
        strong_correlations = [
            corr for corr in correlations if abs(corr["correlation_coefficient"]) > 0.7
        ]

        # Generate correlation insights
        insights = []
        for corr in strong_correlations:
            if corr["correlation_coefficient"] > 0.7:
                insights.append(
                    f"Strong positive correlation between {corr['metric1']} and {corr['metric2']} "
                    f"(r={corr['correlation_coefficient']:.2f})"
                )
            elif corr["correlation_coefficient"] < -0.7:
                insights.append(
                    f"Strong negative correlation between {corr['metric1']} and {corr['metric2']} "
                    f"(r={corr['correlation_coefficient']:.2f})"
                )

        return {
            "all_correlations": correlations,
            "strong_correlations": strong_correlations,
            "insights": insights,
        }

    async def generate_optimization_recommendations(
        self, performance_data: Dict[str, Any]
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        return await self.optimization_engine.generate_recommendations(performance_data)


class TrendAnalyzer:
    """Time series trend analysis."""

    async def analyze_trend(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trend in time series data."""
        if len(data_points) < 2:
            return {"trend_direction": "insufficient_data"}

        # Extract values and timestamps
        values = [point["value"] for point in data_points]
        [point["timestamp"] for point in data_points]

        # Calculate trend direction
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = np.mean(first_half)
        second_avg = np.mean(second_half)

        if second_avg > first_avg * 1.05:
            trend_direction = "increasing"
        elif second_avg < first_avg * 0.95:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"

        # Calculate rate of change
        rate_of_change = (second_avg - first_avg) / first_avg if first_avg != 0 else 0

        # Calculate volatility (coefficient of variation)
        volatility = np.std(values) / np.mean(values) if np.mean(values) != 0 else 0

        # Calculate linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        return {
            "trend_direction": trend_direction,
            "rate_of_change": rate_of_change,
            "volatility": volatility,
            "slope": slope,
            "first_half_avg": first_avg,
            "second_half_avg": second_avg,
            "overall_avg": np.mean(values),
            "min_value": np.min(values),
            "max_value": np.max(values),
        }


class CorrelationAnalyzer:
    """Metric correlation analysis."""

    async def find_correlations(
        self, metric_data: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        """Find correlations between metrics."""
        correlations = []
        metric_names = list(metric_data.keys())

        for i, metric1 in enumerate(metric_names):
            for j, metric2 in enumerate(metric_names[i + 1 :], i + 1):
                data1 = metric_data[metric1]
                data2 = metric_data[metric2]

                # Ensure equal length
                min_length = min(len(data1), len(data2))
                if min_length < 10:  # Need sufficient data points
                    continue

                data1 = data1[:min_length]
                data2 = data2[:min_length]

                # Calculate correlation coefficient
                correlation_coeff = np.corrcoef(data1, data2)[0, 1]

                if not np.isnan(correlation_coeff):
                    correlations.append(
                        {
                            "metric1": metric1,
                            "metric2": metric2,
                            "correlation_coefficient": correlation_coeff,
                            "strength": self._classify_correlation_strength(
                                abs(correlation_coeff)
                            ),
                        }
                    )

        return sorted(
            correlations, key=lambda x: abs(x["correlation_coefficient"]), reverse=True
        )

    def _classify_correlation_strength(self, abs_correlation: float) -> str:
        """Classify correlation strength."""
        if abs_correlation >= 0.9:
            return "very_strong"
        elif abs_correlation >= 0.7:
            return "strong"
        elif abs_correlation >= 0.5:
            return "moderate"
        elif abs_correlation >= 0.3:
            return "weak"
        else:
            return "very_weak"


class CapacityPlanner:
    """Capacity planning and forecasting."""

    def __init__(self) -> dict:
        self.forecasting_model = RandomForestRegressor(
            n_estimators=100, random_state=42
        )
        self.is_trained = False

    async def forecast_capacity_needs(
        self, historical_data: Dict[str, List[float]], forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Forecast capacity needs based on historical data."""
        forecasts = {}

        for metric_name, data in historical_data.items():
            if len(data) < 50:  # Need sufficient historical data
                continue

            forecast = await self._forecast_metric(data, forecast_days)
            forecasts[metric_name] = forecast

        # Generate capacity recommendations
        recommendations = await self._generate_capacity_recommendations(forecasts)

        return {
            "forecasts": forecasts,
            "recommendations": recommendations,
            "forecast_horizon_days": forecast_days,
        }

    async def _forecast_metric(
        self, data: List[float], forecast_days: int
    ) -> Dict[str, Any]:
        """Forecast individual metric."""
        # Prepare features (simple time-based features)
        X = np.array([[i, i % 7, i % 24] for i in range(len(data))])
        y = np.array(data)

        # Train model
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)

        # Generate forecasts
        future_X = np.array(
            [
                [len(data) + i, (len(data) + i) % 7, (len(data) + i) % 24]
                for i in range(forecast_days * 24)  # Hourly forecasts
            ]
        )

        forecasted_values = model.predict(future_X)

        # Calculate confidence intervals (simplified)
        confidence_interval = np.std(y) * 1.96  # 95% confidence

        return {
            "forecasted_values": forecasted_values.tolist(),
            "confidence_interval": confidence_interval,
            "trend": "increasing"
            if forecasted_values[-1] > forecasted_values[0]
            else "stable",
            "peak_forecast": np.max(forecasted_values),
            "average_forecast": np.mean(forecasted_values),
        }

    async def _generate_capacity_recommendations(
        self, forecasts: Dict[str, Any]
    ) -> List[str]:
        """Generate capacity planning recommendations."""
        recommendations = []

        for metric_name, forecast_data in forecasts.items():
            peak_forecast = forecast_data["peak_forecast"]
            forecast_data["average_forecast"]

            if "cpu" in metric_name.lower() and peak_forecast > 80:
                recommendations.append(
                    f"Consider CPU scaling: {metric_name} forecasted to reach {peak_forecast:.1f}%"
                )

            if "memory" in metric_name.lower() and peak_forecast > 85:
                recommendations.append(
                    f"Consider memory expansion: {metric_name} forecasted to reach {peak_forecast:.1f}%"
                )

            if "disk" in metric_name.lower() and peak_forecast > 90:
                recommendations.append(
                    f"Disk capacity planning needed: {metric_name} forecasted to reach {peak_forecast:.1f}%"
                )

        return recommendations


class OptimizationEngine:
    """Performance optimization recommendation engine."""

    async def generate_recommendations(
        self, performance_data: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []

        # Analyze current performance metrics
        if "cpu_utilization" in performance_data:
            cpu_data = performance_data["cpu_utilization"]
            if isinstance(cpu_data, dict) and cpu_data.get("current_value", 0) > 80:
                recommendations.append(
                    "🔧 High CPU usage detected - consider process optimization or scaling"
                )

        if "memory_utilization" in performance_data:
            memory_data = performance_data["memory_utilization"]
            if (
                isinstance(memory_data, dict)
                and memory_data.get("current_value", 0) > 85
            ):
                recommendations.append(
                    "🔧 Memory pressure detected - optimize memory usage or add capacity"
                )

        if "api_response_time" in performance_data:
            api_data = performance_data["api_response_time"]
            if isinstance(api_data, dict) and api_data.get("current_value", 0) > 200:
                recommendations.append(
                    "🔧 API response time high - implement caching or optimize queries"
                )

        if "error_rate" in performance_data:
            error_data = performance_data["error_rate"]
            if isinstance(error_data, dict) and error_data.get("current_value", 0) > 2:
                recommendations.append(
                    "🔧 Error rate elevated - investigate and fix underlying issues"
                )

        # Generic optimization recommendations
        recommendations.extend(
            [
                "📊 Enable application performance monitoring (APM) for detailed insights",
                "🔄 Implement automated scaling based on performance metrics",
                "💾 Configure intelligent caching strategies",
                "🗄️ Optimize database queries and indexing",
                "📈 Set up performance baselines and SLA monitoring",
            ]
        )

        return recommendations[:10]  # Limit to top 10 recommendations


class AdvancedPerformanceMonitoringSystem:
    """Main advanced performance monitoring system."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.metric_collector = MetricCollector()
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager()
        self.performance_analyzer = PerformanceAnalyzer()

        # Configure notification channels
        self._configure_notifications()

        # System state
        self.monitoring_active = False
        self.last_analysis = datetime.now()

        # Metrics storage
        self.metrics_storage: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )

        # Performance profiles
        self.performance_profiles: Dict[str, PerformanceProfile] = {}

    def _configure_notifications(self) -> None:
        """Configure alert notification channels."""
        self.alert_manager.add_notification_channel(self._log_notification)
        self.alert_manager.add_notification_channel(self._email_notification)

    async def start_monitoring(self) -> None:
        """Start comprehensive performance monitoring."""
        self.monitoring_active = True

        # Start metric collection
        collection_task = asyncio.create_task(self.metric_collector.start_collection())

        # Start anomaly detection
        anomaly_task = asyncio.create_task(self._run_anomaly_detection())

        # Start performance analysis
        analysis_task = asyncio.create_task(self._run_performance_analysis())

        logging.info("Advanced performance monitoring started")

        try:
            await asyncio.gather(collection_task, anomaly_task, analysis_task)
        except Exception as e:
            logging.error(f"Performance monitoring error: {e}")
        finally:
            self.monitoring_active = False

    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring_active = False
        await self.metric_collector.stop_collection()
        logging.info("Advanced performance monitoring stopped")

    async def _run_anomaly_detection(self) -> None:
        """Run anomaly detection process."""
        # Initial training with historical data
        await self._train_anomaly_models()

        while self.monitoring_active:
            try:
                # Check for anomalies in recent metrics
                for metric_name, metric_data in self.metrics_storage.items():
                    if len(metric_data) < 10:
                        continue

                    recent_values = [m.value for m in list(metric_data)[-20:]]
                    anomaly_result = await self.anomaly_detector.detect_anomalies(
                        metric_name, recent_values
                    )

                    if anomaly_result["is_anomaly"]:
                        await self._handle_anomaly_detection(
                            metric_name, anomaly_result
                        )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logging.error(f"Anomaly detection error: {e}")
                await asyncio.sleep(60)

    async def _train_anomaly_models(self) -> None:
        """Train anomaly detection models with historical data."""
        # Generate sample training data (in production, use actual historical data)
        training_data = {}

        for metric_name in [
            "cpu_utilization",
            "memory_utilization",
            "api_response_time",
            "error_rate",
        ]:
            # Generate realistic sample data
            if "utilization" in metric_name:
                data = np.random.normal(50, 15, 1000).clip(0, 100).tolist()
            elif "response_time" in metric_name:
                data = np.random.lognormal(4, 0.5, 1000).tolist()
            else:
                data = np.random.exponential(1, 1000).tolist()

            training_data[metric_name] = data

        await self.anomaly_detector.train_models(training_data)

    async def _handle_anomaly_detection(
        self, metric_name: str, anomaly_result: Dict[str, Any]
    ) -> None:
        """Handle detected anomaly."""
        # Create anomaly alert
        alert = PerformanceAlert(
            alert_id=str(uuid.uuid4()),
            metric_name=metric_name,
            severity=AlertSeverity.HIGH
            if anomaly_result["confidence"] > 0.8
            else AlertSeverity.MEDIUM,
            current_value=anomaly_result["latest_value"],
            threshold_value=anomaly_result["baseline_mean"],
            message=f"Anomaly detected in {metric_name}: {anomaly_result['reasons']}",
            timestamp=datetime.now(),
            source="anomaly_detector",
            tags={"anomaly_confidence": str(anomaly_result["confidence"])},
        )

        # Send notifications
        await self.alert_manager._send_notifications(alert)

    async def _run_performance_analysis(self) -> None:
        """Run periodic performance analysis."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes

                # Collect recent metrics data
                analysis_data = {}
                for metric_name, metrics in self.metrics_storage.items():
                    if len(metrics) > 0:
                        recent_metrics = list(metrics)[-100:]  # Last 100 data points
                        analysis_data[metric_name] = [
                            {"timestamp": m.timestamp, "value": m.value}
                            for m in recent_metrics
                        ]

                if analysis_data:
                    # Perform trend analysis
                    trend_analysis = (
                        await self.performance_analyzer.analyze_performance_trends(
                            analysis_data, timedelta(minutes=30)
                        )
                    )

                    # Generate optimization recommendations
                    current_performance = {
                        metric_name: {
                            "current_value": metrics[-1].value if metrics else 0
                        }
                        for metric_name, metrics in self.metrics_storage.items()
                    }

                    await (
                        self.performance_analyzer.generate_optimization_recommendations(
                            current_performance
                        )
                    )

                    # Store analysis results
                    self.last_analysis = datetime.now()
                    logging.info(
                        f"Performance analysis completed: {len(trend_analysis['insights'])} insights generated"
                    )

            except Exception as e:
                logging.error(f"Performance analysis error: {e}")

    async def _log_notification(self, alert: PerformanceAlert) -> None:
        """Log alert notification."""
        logging.warning(
            f"Performance Alert: {alert.message} (Severity: {alert.severity.value})"
        )

    async def _email_notification(self, alert: PerformanceAlert) -> None:
        """Email alert notification (mock)."""
        # In production, integrate with actual email service
        logging.info(f"Email notification sent for alert: {alert.alert_id}")

    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard."""
        current_metrics = {}
        for metric_name, metrics in self.metrics_storage.items():
            if metrics:
                latest_metric = metrics[-1]
                current_metrics[metric_name] = {
                    "current_value": latest_metric.value,
                    "unit": latest_metric.unit,
                    "timestamp": latest_metric.timestamp.isoformat(),
                    "threshold_warning": latest_metric.threshold_warning,
                    "threshold_critical": latest_metric.threshold_critical,
                }

        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()

        # Get system overview
        system_health = await self._calculate_system_health()

        return {
            "dashboard_generated": datetime.now().isoformat(),
            "monitoring_status": "active" if self.monitoring_active else "inactive",
            "system_health": system_health,
            "current_metrics": current_metrics,
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "metric_name": alert.metric_name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in active_alerts[:10]  # Top 10 alerts
            ],
            "alert_summary": {
                "total_alerts": len(active_alerts),
                "critical_alerts": len(
                    [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
                ),
                "high_alerts": len(
                    [a for a in active_alerts if a.severity == AlertSeverity.HIGH]
                ),
            },
            "anomaly_detection": {
                "models_trained": self.anomaly_detector.is_trained,
                "metrics_monitored": len(self.anomaly_detector.models),
            },
        }

    async def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        health_scores = []
        component_health = {}

        for metric_name, metrics in self.metrics_storage.items():
            if not metrics:
                continue

            latest_metric = metrics[-1]

            # Calculate health score based on thresholds
            if latest_metric.threshold_critical:
                if latest_metric.value >= latest_metric.threshold_critical:
                    score = 0.0  # Critical
                elif (
                    latest_metric.threshold_warning
                    and latest_metric.value >= latest_metric.threshold_warning
                ):
                    score = 0.5  # Warning
                else:
                    score = 1.0  # Good
            else:
                score = 0.8  # Default for metrics without thresholds

            health_scores.append(score)
            component_health[metric_name] = {
                "score": score,
                "status": "critical"
                if score == 0.0
                else "warning"
                if score == 0.5
                else "healthy",
            }

        overall_health = np.mean(health_scores) if health_scores else 0.8

        return {
            "overall_score": overall_health,
            "status": "critical"
            if overall_health < 0.3
            else "warning"
            if overall_health < 0.7
            else "healthy",
            "component_health": component_health,
            "last_updated": datetime.now().isoformat(),
        }

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        dashboard = await self.get_performance_dashboard()

        return {
            "report_generated": datetime.now().isoformat(),
            "report_period": "last_24_hours",
            "executive_summary": {
                "system_health": dashboard["system_health"]["status"],
                "health_score": dashboard["system_health"]["overall_score"],
                "total_alerts": dashboard["alert_summary"]["total_alerts"],
                "critical_issues": dashboard["alert_summary"]["critical_alerts"],
            },
            "performance_metrics": dashboard["current_metrics"],
            "alert_analysis": dashboard["alert_summary"],
            "recommendations": await self.performance_analyzer.generate_optimization_recommendations(
                dashboard["current_metrics"]
            ),
        }


# Usage example and testing
async def main() -> None:
    """Example usage of the Advanced Performance Monitoring System."""
    # Initialize SDK (mock)
    sdk = MobileERPSDK()

    # Initialize performance monitoring system
    monitoring_system = AdvancedPerformanceMonitoringSystem(sdk)

    # Start monitoring (run for a short time for demo)
    monitoring_task = asyncio.create_task(monitoring_system.start_monitoring())

    # Let it run for a bit to collect some data
    await asyncio.sleep(10)

    # Get performance dashboard
    dashboard = await monitoring_system.get_performance_dashboard()
    print("Performance Dashboard:")
    print(f"System Health: {dashboard['system_health']['status']}")
    print(f"Health Score: {dashboard['system_health']['overall_score']:.2f}")
    print(f"Active Alerts: {dashboard['alert_summary']['total_alerts']}")
    print(f"Monitored Metrics: {len(dashboard['current_metrics'])}")

    # Generate performance report
    report = await monitoring_system.generate_performance_report()
    print("\nPerformance Report:")
    print(f"Executive Summary: {report['executive_summary']}")
    print(f"Recommendations: {len(report['recommendations'])} generated")

    # Stop monitoring
    await monitoring_system.stop_monitoring()
    monitoring_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
