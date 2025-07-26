"""
CC02 v78.0 Day 23: Enterprise Integrated Deployment & Operations Automation
Module 4: Operations Monitoring & Alert System

Advanced enterprise-grade operations monitoring with intelligent alerting,
predictive anomaly detection, and comprehensive observability platform.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import numpy as np
import psutil
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ..core.mobile_erp_sdk import MobileERPSDK


class AlertSeverity(Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCategory(Enum):
    """Alert categories"""

    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    COMPLIANCE = "compliance"


class NotificationChannel(Enum):
    """Notification delivery channels"""

    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    SMS = "sms"
    PAGERDUTY = "pagerduty"


@dataclass
class Metric:
    """System metric data structure"""

    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    host: str = ""


@dataclass
class Alert:
    """Alert data structure"""

    id: str
    title: str
    description: str
    severity: AlertSeverity
    category: AlertCategory
    timestamp: datetime
    source: str
    metrics: List[Metric] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None


@dataclass
class AlertRule:
    """Alert rule configuration"""

    id: str
    name: str
    condition: str
    threshold: float
    severity: AlertSeverity
    category: AlertCategory
    enabled: bool = True
    evaluation_window: int = 300  # seconds
    cooldown_period: int = 900  # seconds
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class NotificationTarget:
    """Notification target configuration"""

    id: str
    name: str
    channel: NotificationChannel
    config: Dict[str, Any]
    enabled: bool = True
    severity_filter: List[AlertSeverity] = field(default_factory=list)


class MetricsCollector:
    """Advanced metrics collection system"""

    def __init__(self) -> dict:
        self.collectors: Dict[str, Callable] = {}
        self.collection_interval = 30  # seconds
        self.metrics_buffer: List[Metric] = []
        self.running = False

    def register_collector(self, name: str, collector_func: Callable) -> dict:
        """Register custom metrics collector"""
        self.collectors[name] = collector_func

    async def collect_system_metrics(self) -> List[Metric]:
        """Collect system-level metrics"""
        metrics = []
        now = datetime.now()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(
            Metric(
                name="system.cpu.usage_percent",
                value=cpu_percent,
                timestamp=now,
                unit="percent",
            )
        )

        # Memory metrics
        memory = psutil.virtual_memory()
        metrics.append(
            Metric(
                name="system.memory.usage_percent",
                value=memory.percent,
                timestamp=now,
                unit="percent",
            )
        )

        metrics.append(
            Metric(
                name="system.memory.available_bytes",
                value=memory.available,
                timestamp=now,
                unit="bytes",
            )
        )

        # Disk metrics
        disk = psutil.disk_usage("/")
        metrics.append(
            Metric(
                name="system.disk.usage_percent",
                value=(disk.used / disk.total) * 100,
                timestamp=now,
                unit="percent",
            )
        )

        # Network metrics
        network = psutil.net_io_counters()
        metrics.append(
            Metric(
                name="system.network.bytes_sent",
                value=network.bytes_sent,
                timestamp=now,
                unit="bytes",
            )
        )

        metrics.append(
            Metric(
                name="system.network.bytes_recv",
                value=network.bytes_recv,
                timestamp=now,
                unit="bytes",
            )
        )

        return metrics

    async def collect_application_metrics(self) -> List[Metric]:
        """Collect application-level metrics"""
        metrics = []
        now = datetime.now()

        # Process metrics
        current_process = psutil.Process()

        metrics.append(
            Metric(
                name="app.process.cpu_percent",
                value=current_process.cpu_percent(),
                timestamp=now,
                unit="percent",
            )
        )

        memory_info = current_process.memory_info()
        metrics.append(
            Metric(
                name="app.process.memory_rss",
                value=memory_info.rss,
                timestamp=now,
                unit="bytes",
            )
        )

        # File descriptor count
        try:
            fd_count = current_process.num_fds()
            metrics.append(
                Metric(
                    name="app.process.file_descriptors",
                    value=fd_count,
                    timestamp=now,
                    unit="count",
                )
            )
        except AttributeError:
            # Windows doesn't support num_fds
            pass

        return metrics

    async def collect_custom_metrics(self) -> List[Metric]:
        """Collect custom application metrics"""
        metrics = []

        for name, collector in self.collectors.items():
            try:
                custom_metrics = await collector()
                metrics.extend(custom_metrics)
            except Exception as e:
                logging.error(f"Error collecting metrics from {name}: {e}")

        return metrics

    async def start_collection(self) -> dict:
        """Start metrics collection loop"""
        self.running = True

        while self.running:
            try:
                # Collect all metrics
                all_metrics = []
                all_metrics.extend(await self.collect_system_metrics())
                all_metrics.extend(await self.collect_application_metrics())
                all_metrics.extend(await self.collect_custom_metrics())

                # Add to buffer
                self.metrics_buffer.extend(all_metrics)

                # Trim buffer to last hour
                cutoff_time = datetime.now() - timedelta(hours=1)
                self.metrics_buffer = [
                    m for m in self.metrics_buffer if m.timestamp >= cutoff_time
                ]

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logging.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)

    def stop_collection(self) -> dict:
        """Stop metrics collection"""
        self.running = False

    def get_recent_metrics(
        self, metric_name: str, duration_minutes: int = 10
    ) -> List[Metric]:
        """Get recent metrics for a specific metric name"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            m
            for m in self.metrics_buffer
            if m.name == metric_name and m.timestamp >= cutoff_time
        ]


class AnomalyDetector:
    """Machine learning-based anomaly detection"""

    def __init__(self) -> dict:
        self.models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.training_data: Dict[str, List[float]] = {}

    def train_model(self, metric_name: str, values: List[float]) -> dict:
        """Train anomaly detection model for a metric"""
        if len(values) < 10:
            return  # Need minimum data points

        # Prepare data
        data = np.array(values).reshape(-1, 1)

        # Scale data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)

        # Train isolation forest
        model = IsolationForest(
            contamination=0.1,  # 10% anomalies expected
            random_state=42,
        )
        model.fit(scaled_data)

        # Store model and scaler
        self.models[metric_name] = model
        self.scalers[metric_name] = scaler
        self.training_data[metric_name] = values

        logging.info(f"Trained anomaly detection model for {metric_name}")

    def detect_anomaly(self, metric_name: str, value: float) -> bool:
        """Detect if a metric value is anomalous"""
        if metric_name not in self.models:
            return False

        model = self.models[metric_name]
        scaler = self.scalers[metric_name]

        # Scale the value
        scaled_value = scaler.transform([[value]])

        # Predict anomaly (-1 for anomaly, 1 for normal)
        prediction = model.predict(scaled_value)

        return prediction[0] == -1

    def get_anomaly_score(self, metric_name: str, value: float) -> float:
        """Get anomaly score for a metric value"""
        if metric_name not in self.models:
            return 0.0

        model = self.models[metric_name]
        scaler = self.scalers[metric_name]

        # Scale the value
        scaled_value = scaler.transform([[value]])

        # Get anomaly score
        score = model.decision_function(scaled_value)

        return float(score[0])


class AlertManager:
    """Intelligent alert management system"""

    def __init__(self) -> dict:
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.rule_cooldowns: Dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule) -> dict:
        """Add alert rule"""
        self.rules[rule.id] = rule
        logging.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> dict:
        """Remove alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logging.info(f"Removed alert rule: {rule_id}")

    def evaluate_rules(self, metrics: List[Metric]) -> List[Alert]:
        """Evaluate alert rules against current metrics"""
        new_alerts = []
        now = datetime.now()

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.id in self.rule_cooldowns:
                if now < self.rule_cooldowns[rule.id]:
                    continue

            # Get relevant metrics
            relevant_metrics = [
                m for m in metrics if self._metric_matches_rule(m, rule)
            ]

            if not relevant_metrics:
                continue

            # Evaluate condition
            if self._evaluate_condition(rule, relevant_metrics):
                alert = self._create_alert_from_rule(rule, relevant_metrics)
                new_alerts.append(alert)

                # Set cooldown
                self.rule_cooldowns[rule.id] = now + timedelta(
                    seconds=rule.cooldown_period
                )

        return new_alerts

    def _metric_matches_rule(self, metric: Metric, rule: AlertRule) -> bool:
        """Check if metric matches rule criteria"""
        # Simple implementation - can be extended for complex label matching
        return True

    def _evaluate_condition(self, rule: AlertRule, metrics: List[Metric]) -> bool:
        """Evaluate rule condition against metrics"""
        if not metrics:
            return False

        # Simple threshold-based evaluation
        latest_metric = max(metrics, key=lambda m: m.timestamp)

        if ">" in rule.condition:
            return latest_metric.value > rule.threshold
        elif "<" in rule.condition:
            return latest_metric.value < rule.threshold
        elif "=" in rule.condition:
            return abs(latest_metric.value - rule.threshold) < 0.001

        return False

    def _create_alert_from_rule(self, rule: AlertRule, metrics: List[Metric]) -> Alert:
        """Create alert from rule and metrics"""
        alert_id = f"{rule.id}_{int(datetime.now().timestamp())}"

        return Alert(
            id=alert_id,
            title=rule.name,
            description=f"Alert triggered: {rule.condition}",
            severity=rule.severity,
            category=rule.category,
            timestamp=datetime.now(),
            source=f"rule:{rule.id}",
            metrics=metrics,
            labels=rule.labels.copy(),
        )

    def add_alert(self, alert: Alert) -> dict:
        """Add alert to active alerts"""
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        logging.warning(f"New alert: {alert.title} ({alert.severity.value})")

    def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> dict:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            alert.assigned_to = resolved_by

            del self.active_alerts[alert_id]
            logging.info(f"Resolved alert: {alert.title}")

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)


class NotificationManager:
    """Multi-channel notification system"""

    def __init__(self) -> dict:
        self.targets: Dict[str, NotificationTarget] = {}
        self.notification_history: List[Dict[str, Any]] = []

    def add_target(self, target: NotificationTarget) -> dict:
        """Add notification target"""
        self.targets[target.id] = target
        logging.info(f"Added notification target: {target.name}")

    def remove_target(self, target_id: str) -> dict:
        """Remove notification target"""
        if target_id in self.targets:
            del self.targets[target_id]
            logging.info(f"Removed notification target: {target_id}")

    async def send_alert_notification(self, alert: Alert) -> dict:
        """Send alert notification to all applicable targets"""
        for target in self.targets.values():
            if not target.enabled:
                continue

            # Check severity filter
            if target.severity_filter and alert.severity not in target.severity_filter:
                continue

            try:
                await self._send_notification(target, alert)

                # Record notification
                self.notification_history.append(
                    {
                        "timestamp": datetime.now(),
                        "target": target.name,
                        "alert_id": alert.id,
                        "status": "sent",
                    }
                )

            except Exception as e:
                logging.error(f"Failed to send notification to {target.name}: {e}")

                # Record failure
                self.notification_history.append(
                    {
                        "timestamp": datetime.now(),
                        "target": target.name,
                        "alert_id": alert.id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

    async def _send_notification(self, target: NotificationTarget, alert: Alert) -> dict:
        """Send notification to specific target"""
        if target.channel == NotificationChannel.EMAIL:
            await self._send_email_notification(target, alert)
        elif target.channel == NotificationChannel.SLACK:
            await self._send_slack_notification(target, alert)
        elif target.channel == NotificationChannel.WEBHOOK:
            await self._send_webhook_notification(target, alert)
        # Add more notification channels as needed

    async def _send_email_notification(self, target: NotificationTarget, alert: Alert) -> dict:
        """Send email notification"""
        # Email implementation would go here
        logging.info(f"Email notification sent for alert: {alert.title}")

    async def _send_slack_notification(self, target: NotificationTarget, alert: Alert) -> dict:
        """Send Slack notification"""
        webhook_url = target.config.get("webhook_url")
        if not webhook_url:
            raise ValueError("Slack webhook URL not configured")

        severity_colors = {
            AlertSeverity.CRITICAL: "#FF0000",
            AlertSeverity.HIGH: "#FF8C00",
            AlertSeverity.MEDIUM: "#FFD700",
            AlertSeverity.LOW: "#32CD32",
            AlertSeverity.INFO: "#87CEEB",
        }

        payload = {
            "attachments": [
                {
                    "color": severity_colors.get(alert.severity, "#808080"),
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True,
                        },
                        {
                            "title": "Category",
                            "value": alert.category.value.title(),
                            "short": True,
                        },
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "short": False,
                        },
                    ],
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Slack API error: {response.status}")

    async def _send_webhook_notification(
        self, target: NotificationTarget, alert: Alert
    ):
        """Send webhook notification"""
        webhook_url = target.config.get("url")
        if not webhook_url:
            raise ValueError("Webhook URL not configured")

        payload = {
            "alert": {
                "id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "category": alert.category.value,
                "timestamp": alert.timestamp.isoformat(),
                "source": alert.source,
                "labels": alert.labels,
            }
        }

        headers = target.config.get("headers", {})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url, json=payload, headers=headers
            ) as response:
                if response.status not in [200, 201, 202]:
                    raise Exception(f"Webhook error: {response.status}")


class DashboardManager:
    """Real-time monitoring dashboard"""

    def __init__(self) -> dict:
        self.widgets: Dict[str, Dict[str, Any]] = {}
        self.dashboards: Dict[str, Dict[str, Any]] = {}

    def create_dashboard(self, dashboard_id: str, title: str, description: str = "") -> dict:
        """Create monitoring dashboard"""
        self.dashboards[dashboard_id] = {
            "id": dashboard_id,
            "title": title,
            "description": description,
            "widgets": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def add_widget(self, dashboard_id: str, widget_config: Dict[str, Any]) -> dict:
        """Add widget to dashboard"""
        if dashboard_id not in self.dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")

        widget_id = f"widget_{len(self.dashboards[dashboard_id]['widgets'])}"
        widget_config["id"] = widget_id

        self.dashboards[dashboard_id]["widgets"].append(widget_config)
        self.dashboards[dashboard_id]["updated_at"] = datetime.now()

    def get_dashboard_data(
        self, dashboard_id: str, metrics: List[Metric]
    ) -> Dict[str, Any]:
        """Get dashboard data with current metrics"""
        if dashboard_id not in self.dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")

        dashboard = self.dashboards[dashboard_id].copy()

        # Populate widget data
        for widget in dashboard["widgets"]:
            widget_type = widget.get("type", "metric")

            if widget_type == "metric":
                metric_name = widget.get("metric")
                recent_metrics = [m for m in metrics if m.name == metric_name]

                if recent_metrics:
                    latest = max(recent_metrics, key=lambda m: m.timestamp)
                    widget["current_value"] = latest.value
                    widget["timestamp"] = latest.timestamp

            elif widget_type == "chart":
                metric_name = widget.get("metric")
                chart_metrics = [m for m in metrics if m.name == metric_name]

                widget["data_points"] = [
                    {"timestamp": m.timestamp.isoformat(), "value": m.value}
                    for m in sorted(chart_metrics, key=lambda m: m.timestamp)
                ]

        return dashboard


class OperationsMonitoringSystem:
    """Main operations monitoring and alerting system"""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.metrics_collector = MetricsCollector()
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager()
        self.notification_manager = NotificationManager()
        self.dashboard_manager = DashboardManager()

        # System configuration
        self.monitoring_enabled = True
        self.anomaly_detection_enabled = True
        self.auto_resolution_enabled = True

        # Collection interval
        self.metrics_collection_interval = 30  # seconds

        # Initialize default alert rules
        self._initialize_default_rules()

        # Initialize default dashboards
        self._initialize_default_dashboards()

        logging.info("Operations monitoring system initialized")

    def _initialize_default_rules(self) -> dict:
        """Initialize default alert rules"""

        # CPU usage alert
        cpu_rule = AlertRule(
            id="cpu_high",
            name="High CPU Usage",
            condition="cpu_percent > threshold",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            category=AlertCategory.PERFORMANCE,
            evaluation_window=300,
            cooldown_period=900,
        )
        self.alert_manager.add_rule(cpu_rule)

        # Memory usage alert
        memory_rule = AlertRule(
            id="memory_high",
            name="High Memory Usage",
            condition="memory_percent > threshold",
            threshold=85.0,
            severity=AlertSeverity.HIGH,
            category=AlertCategory.PERFORMANCE,
            evaluation_window=300,
            cooldown_period=900,
        )
        self.alert_manager.add_rule(memory_rule)

        # Disk usage alert
        disk_rule = AlertRule(
            id="disk_high",
            name="High Disk Usage",
            condition="disk_percent > threshold",
            threshold=90.0,
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.INFRASTRUCTURE,
            evaluation_window=600,
            cooldown_period=1800,
        )
        self.alert_manager.add_rule(disk_rule)

    def _initialize_default_dashboards(self) -> dict:
        """Initialize default monitoring dashboards"""

        # System overview dashboard
        self.dashboard_manager.create_dashboard(
            "system_overview",
            "System Overview",
            "Real-time system metrics and performance indicators",
        )

        # Add widgets to system overview
        widgets = [
            {
                "type": "metric",
                "title": "CPU Usage",
                "metric": "system.cpu.usage_percent",
                "unit": "%",
                "thresholds": {"warning": 70, "critical": 85},
            },
            {
                "type": "metric",
                "title": "Memory Usage",
                "metric": "system.memory.usage_percent",
                "unit": "%",
                "thresholds": {"warning": 75, "critical": 90},
            },
            {
                "type": "chart",
                "title": "CPU Usage Over Time",
                "metric": "system.cpu.usage_percent",
                "chart_type": "line",
                "time_range": "1h",
            },
            {
                "type": "chart",
                "title": "Memory Usage Over Time",
                "metric": "system.memory.usage_percent",
                "chart_type": "line",
                "time_range": "1h",
            },
        ]

        for widget in widgets:
            self.dashboard_manager.add_widget("system_overview", widget)

    async def start_monitoring(self) -> dict:
        """Start the monitoring system"""
        if not self.monitoring_enabled:
            logging.info("Monitoring is disabled")
            return

        logging.info("Starting operations monitoring system")

        # Start metrics collection
        collection_task = asyncio.create_task(self.metrics_collector.start_collection())

        # Start alert evaluation loop
        alert_task = asyncio.create_task(self._alert_evaluation_loop())

        # Start anomaly detection training
        if self.anomaly_detection_enabled:
            anomaly_task = asyncio.create_task(self._anomaly_detection_loop())
            await asyncio.gather(collection_task, alert_task, anomaly_task)
        else:
            await asyncio.gather(collection_task, alert_task)

    async def _alert_evaluation_loop(self) -> dict:
        """Main alert evaluation loop"""
        while self.monitoring_enabled:
            try:
                # Get recent metrics
                recent_metrics = []
                for metric_name in [
                    "system.cpu.usage_percent",
                    "system.memory.usage_percent",
                    "system.disk.usage_percent",
                ]:
                    recent_metrics.extend(
                        self.metrics_collector.get_recent_metrics(metric_name, 5)
                    )

                # Evaluate alert rules
                new_alerts = self.alert_manager.evaluate_rules(recent_metrics)

                # Process new alerts
                for alert in new_alerts:
                    self.alert_manager.add_alert(alert)
                    await self.notification_manager.send_alert_notification(alert)

                # Check for auto-resolution
                if self.auto_resolution_enabled:
                    await self._check_auto_resolution(recent_metrics)

                await asyncio.sleep(60)  # Evaluate every minute

            except Exception as e:
                logging.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(60)

    async def _anomaly_detection_loop(self) -> dict:
        """Anomaly detection training and evaluation loop"""
        while self.monitoring_enabled:
            try:
                # Train models on historical data
                for metric_name in [
                    "system.cpu.usage_percent",
                    "system.memory.usage_percent",
                ]:
                    recent_metrics = self.metrics_collector.get_recent_metrics(
                        metric_name, 60
                    )

                    if len(recent_metrics) >= 20:
                        values = [m.value for m in recent_metrics]
                        self.anomaly_detector.train_model(metric_name, values)

                # Detect anomalies in recent metrics
                for metric_name in [
                    "system.cpu.usage_percent",
                    "system.memory.usage_percent",
                ]:
                    recent_metrics = self.metrics_collector.get_recent_metrics(
                        metric_name, 5
                    )

                    for metric in recent_metrics:
                        if self.anomaly_detector.detect_anomaly(
                            metric_name, metric.value
                        ):
                            # Create anomaly alert
                            anomaly_alert = Alert(
                                id=f"anomaly_{metric_name}_{int(metric.timestamp.timestamp())}",
                                title=f"Anomaly Detected: {metric_name}",
                                description=f"Anomalous value detected: {metric.value}",
                                severity=AlertSeverity.MEDIUM,
                                category=AlertCategory.PERFORMANCE,
                                timestamp=metric.timestamp,
                                source="anomaly_detection",
                                metrics=[metric],
                            )

                            self.alert_manager.add_alert(anomaly_alert)
                            await self.notification_manager.send_alert_notification(
                                anomaly_alert
                            )

                await asyncio.sleep(300)  # Train every 5 minutes

            except Exception as e:
                logging.error(f"Error in anomaly detection loop: {e}")
                await asyncio.sleep(300)

    async def _check_auto_resolution(self, metrics: List[Metric]) -> dict:
        """Check for automatic alert resolution"""
        active_alerts = self.alert_manager.get_active_alerts()

        for alert in active_alerts:
            if alert.category == AlertCategory.PERFORMANCE:
                # Check if performance metrics have returned to normal
                relevant_metrics = [
                    m for m in metrics if any(am.name == m.name for am in alert.metrics)
                ]

                if relevant_metrics:
                    latest_metric = max(relevant_metrics, key=lambda m: m.timestamp)

                    # Simple auto-resolution logic
                    if (
                        alert.severity == AlertSeverity.HIGH
                        and latest_metric.value < 70.0
                    ):  # Below warning threshold
                        self.alert_manager.resolve_alert(alert.id, "auto_resolution")

    def add_custom_metric_collector(self, name: str, collector_func: Callable) -> dict:
        """Add custom metrics collector"""
        self.metrics_collector.register_collector(name, collector_func)

    def add_alert_rule(self, rule: AlertRule) -> dict:
        """Add custom alert rule"""
        self.alert_manager.add_rule(rule)

    def add_notification_target(self, target: NotificationTarget) -> dict:
        """Add notification target"""
        self.notification_manager.add_target(target)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        recent_metrics = []

        # Get recent metrics for all key indicators
        for metric_name in [
            "system.cpu.usage_percent",
            "system.memory.usage_percent",
            "system.disk.usage_percent",
        ]:
            recent_metrics.extend(
                self.metrics_collector.get_recent_metrics(metric_name, 10)
            )

        active_alerts = self.alert_manager.get_active_alerts()

        # Calculate system health score
        health_score = self._calculate_health_score(recent_metrics, active_alerts)

        return {
            "timestamp": datetime.now(),
            "health_score": health_score,
            "monitoring_enabled": self.monitoring_enabled,
            "active_alerts": len(active_alerts),
            "critical_alerts": len(
                [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
            ),
            "metrics_collected": len(recent_metrics),
            "anomaly_detection_enabled": self.anomaly_detection_enabled,
            "notification_targets": len(self.notification_manager.targets),
            "alert_rules": len(self.alert_manager.rules),
        }

    def _calculate_health_score(
        self, metrics: List[Metric], alerts: List[Alert]
    ) -> float:
        """Calculate overall system health score (0-100)"""
        base_score = 100.0

        # Deduct points for active alerts
        for alert in alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                base_score -= 20
            elif alert.severity == AlertSeverity.HIGH:
                base_score -= 10
            elif alert.severity == AlertSeverity.MEDIUM:
                base_score -= 5

        # Deduct points for high resource usage
        cpu_metrics = [m for m in metrics if m.name == "system.cpu.usage_percent"]
        if cpu_metrics:
            latest_cpu = max(cpu_metrics, key=lambda m: m.timestamp)
            if latest_cpu.value > 80:
                base_score -= (latest_cpu.value - 80) * 0.5

        memory_metrics = [m for m in metrics if m.name == "system.memory.usage_percent"]
        if memory_metrics:
            latest_memory = max(memory_metrics, key=lambda m: m.timestamp)
            if latest_memory.value > 80:
                base_score -= (latest_memory.value - 80) * 0.5

        return max(0.0, min(100.0, base_score))

    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data"""
        recent_metrics = []

        # Get metrics for dashboard
        for metric_name in [
            "system.cpu.usage_percent",
            "system.memory.usage_percent",
            "system.disk.usage_percent",
        ]:
            recent_metrics.extend(
                self.metrics_collector.get_recent_metrics(metric_name, 60)
            )

        return self.dashboard_manager.get_dashboard_data(dashboard_id, recent_metrics)

    async def stop_monitoring(self) -> dict:
        """Stop the monitoring system"""
        self.monitoring_enabled = False
        self.metrics_collector.stop_collection()
        logging.info("Operations monitoring system stopped")


# Example usage and testing
async def main() -> None:
    """Example usage of the operations monitoring system"""

    # Initialize SDK (mock)
    class MockMobileERPSDK:
        pass

    sdk = MockMobileERPSDK()

    # Create monitoring system
    monitoring_system = OperationsMonitoringSystem(sdk)

    # Add Slack notification target
    slack_target = NotificationTarget(
        id="slack_alerts",
        name="Slack Alerts",
        channel=NotificationChannel.SLACK,
        config={"webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"},
        severity_filter=[AlertSeverity.CRITICAL, AlertSeverity.HIGH],
    )
    monitoring_system.add_notification_target(slack_target)

    # Add custom alert rule
    custom_rule = AlertRule(
        id="app_response_time",
        name="High Application Response Time",
        condition="response_time > threshold",
        threshold=2000.0,  # 2 seconds
        severity=AlertSeverity.HIGH,
        category=AlertCategory.PERFORMANCE,
        evaluation_window=180,
        cooldown_period=600,
    )
    monitoring_system.add_alert_rule(custom_rule)

    # Start monitoring
    print("Starting operations monitoring system...")

    # Run for demonstration (in real usage, this would run continuously)
    monitoring_task = asyncio.create_task(monitoring_system.start_monitoring())

    # Let it run for a few seconds
    await asyncio.sleep(10)

    # Get system status
    status = monitoring_system.get_system_status()
    print(f"System Status: {json.dumps(status, indent=2, default=str)}")

    # Get dashboard data
    dashboard_data = monitoring_system.get_dashboard_data("system_overview")
    print(f"Dashboard Data: {json.dumps(dashboard_data, indent=2, default=str)}")

    # Stop monitoring
    await monitoring_system.stop_monitoring()
    monitoring_task.cancel()

    print("Operations monitoring demonstration completed")


if __name__ == "__main__":
    asyncio.run(main())
