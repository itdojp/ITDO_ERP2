"""
CC02 v77.0 Day 22: Server Resource Optimization & Load Balancing Module
Enterprise-grade server resource optimization with intelligent load balancing and auto-scaling.
"""

from __future__ import annotations

import asyncio
import logging
import multiprocessing
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from app.mobile_sdk.core import MobileERPSDK

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """System resource types."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


class LoadBalancerAlgorithm(Enum):
    """Load balancing algorithms."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESOURCE_BASED = "resource_based"


class ServerStatus(Enum):
    """Server status states."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    FAILING = "failing"
    OFFLINE = "offline"


class OptimizationAction(Enum):
    """Resource optimization actions."""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    REBALANCE = "rebalance"
    THROTTLE = "throttle"
    CACHE_EVICT = "cache_evict"
    PROCESS_RESTART = "process_restart"
    MIGRATE_WORKLOAD = "migrate_workload"


@dataclass
class SystemResourceMetrics:
    """System resource usage metrics."""

    cpu_percent: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    disk_usage_percent: float
    load_average: Tuple[float, float, float]
    process_count: int
    thread_count: int
    file_descriptor_count: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServerNode:
    """Server node configuration."""

    node_id: str
    hostname: str
    ip_address: str
    port: int
    weight: int
    max_connections: int
    current_connections: int
    cpu_cores: int
    memory_gb: int
    status: ServerStatus
    last_health_check: datetime
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    resource_metrics: Optional[SystemResourceMetrics] = None


@dataclass
class LoadBalancerMetrics:
    """Load balancer performance metrics."""

    total_requests: int
    requests_per_second: float
    average_response_time: float
    error_rate: float
    active_connections: int
    bytes_transferred: int
    server_distribution: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)


class SystemResourceMonitor:
    """Monitors system resource usage and performance."""

    def __init__(self, sampling_interval: float = 1.0) -> dict:
        self.sampling_interval = sampling_interval
        self.metrics_history: List[SystemResourceMetrics] = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "load_average_threshold": multiprocessing.cpu_count() * 1.5,
        }
        self.is_monitoring = False

    async def start_monitoring(self) -> dict:
        """Start continuous resource monitoring."""
        self.is_monitoring = True

        while self.is_monitoring:
            try:
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)

                # Keep only last 1000 measurements
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)

                # Check for resource alerts
                await self._check_resource_alerts(metrics)

                await asyncio.sleep(self.sampling_interval)

            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(5)

    async def stop_monitoring(self) -> dict:
        """Stop resource monitoring."""
        self.is_monitoring = False

    async def _collect_system_metrics(self) -> SystemResourceMetrics:
        """Collect current system resource metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk metrics
        disk_usage = psutil.disk_usage("/")
        disk_usage_percent = disk_usage.percent

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0.0
        disk_io_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0.0

        # Network I/O
        network_io = psutil.net_io_counters()
        network_io_sent_mb = (
            network_io.bytes_sent / (1024 * 1024) if network_io else 0.0
        )
        network_io_recv_mb = (
            network_io.bytes_recv / (1024 * 1024) if network_io else 0.0
        )

        # Process metrics
        process_count = len(psutil.pids())

        # Thread count estimation
        thread_count = 0
        try:
            for proc in psutil.process_iter(["num_threads"]):
                thread_count += proc.info.get("num_threads", 0)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # File descriptor count (Linux/Unix only)
        fd_count = 0
        try:
            if hasattr(psutil, "Process"):
                current_process = psutil.Process()
                fd_count = (
                    current_process.num_fds()
                    if hasattr(current_process, "num_fds")
                    else 0
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        return SystemResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_sent_mb=network_io_sent_mb,
            network_io_recv_mb=network_io_recv_mb,
            disk_usage_percent=disk_usage_percent,
            load_average=load_avg,
            process_count=process_count,
            thread_count=thread_count,
            file_descriptor_count=fd_count,
        )

    async def _check_resource_alerts(self, metrics: SystemResourceMetrics) -> dict:
        """Check for resource threshold violations."""
        alerts = []

        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")

        if metrics.disk_usage_percent > self.alert_thresholds["disk_usage_percent"]:
            alerts.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")

        if metrics.load_average[0] > self.alert_thresholds["load_average_threshold"]:
            alerts.append(f"High load average: {metrics.load_average[0]:.2f}")

        if alerts:
            logger.warning(f"Resource alerts: {', '.join(alerts)}")

    def get_resource_trends(self, minutes: int = 10) -> Dict[str, Any]:
        """Get resource usage trends."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff]

        if len(recent_metrics) < 2:
            return {"trend": "insufficient_data"}

        # Calculate trends
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]

        cpu_trend = "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
        memory_trend = (
            "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
        )

        return {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "cpu_avg": np.mean(cpu_values),
            "memory_avg": np.mean(memory_values),
            "samples": len(recent_metrics),
            "stability_score": self._calculate_stability_score(recent_metrics),
        }

    def _calculate_stability_score(self, metrics: List[SystemResourceMetrics]) -> float:
        """Calculate system stability score."""
        if len(metrics) < 5:
            return 1.0

        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_percent for m in metrics]

        # Lower variance = higher stability
        cpu_variance = np.var(cpu_values)
        memory_variance = np.var(memory_values)

        # Normalize to 0-1 scale (lower variance = higher score)
        cpu_stability = max(0, 1.0 - (cpu_variance / 1000))
        memory_stability = max(0, 1.0 - (memory_variance / 1000))

        return (cpu_stability + memory_stability) / 2


class IntelligentLoadBalancer:
    """Intelligent load balancer with multiple algorithms and health checking."""

    def __init__(
        self,
        algorithm: LoadBalancerAlgorithm = LoadBalancerAlgorithm.LEAST_RESPONSE_TIME,
    ):
        self.algorithm = algorithm
        self.servers: Dict[str, ServerNode] = {}
        self.request_count = 0
        self.last_server_index = 0
        self.metrics = LoadBalancerMetrics(
            total_requests=0,
            requests_per_second=0.0,
            average_response_time=0.0,
            error_rate=0.0,
            active_connections=0,
            bytes_transferred=0,
            server_distribution={},
        )

        # Performance tracking
        self.response_times: List[float] = []
        self.error_count = 0
        self.start_time = datetime.now()

    def add_server(self, server: ServerNode) -> dict:
        """Add server to load balancer pool."""
        self.servers[server.node_id] = server
        self.metrics.server_distribution[server.node_id] = 0
        logger.info(f"Added server {server.node_id} ({server.hostname}:{server.port})")

    def remove_server(self, node_id: str) -> dict:
        """Remove server from load balancer pool."""
        if node_id in self.servers:
            del self.servers[node_id]
            if node_id in self.metrics.server_distribution:
                del self.metrics.server_distribution[node_id]
            logger.info(f"Removed server {node_id}")

    async def select_server(
        self, request_context: Dict[str, Any] = None
    ) -> Optional[ServerNode]:
        """Select optimal server based on configured algorithm."""
        healthy_servers = [
            s for s in self.servers.values() if s.status == ServerStatus.HEALTHY
        ]

        if not healthy_servers:
            logger.error("No healthy servers available")
            return None

        if self.algorithm == LoadBalancerAlgorithm.ROUND_ROBIN:
            return self._round_robin_selection(healthy_servers)
        elif self.algorithm == LoadBalancerAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_servers)
        elif self.algorithm == LoadBalancerAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(healthy_servers)
        elif self.algorithm == LoadBalancerAlgorithm.LEAST_RESPONSE_TIME:
            return self._least_response_time_selection(healthy_servers)
        elif self.algorithm == LoadBalancerAlgorithm.RESOURCE_BASED:
            return self._resource_based_selection(healthy_servers)
        elif self.algorithm == LoadBalancerAlgorithm.IP_HASH:
            return self._ip_hash_selection(healthy_servers, request_context)
        else:
            return healthy_servers[0] if healthy_servers else None

    def _round_robin_selection(self, servers: List[ServerNode]) -> ServerNode:
        """Round-robin server selection."""
        server = servers[self.last_server_index % len(servers)]
        self.last_server_index += 1
        return server

    def _least_connections_selection(self, servers: List[ServerNode]) -> ServerNode:
        """Select server with least active connections."""
        return min(servers, key=lambda s: s.current_connections)

    def _weighted_round_robin_selection(self, servers: List[ServerNode]) -> ServerNode:
        """Weighted round-robin based on server weights."""
        total_weight = sum(s.weight for s in servers)
        if total_weight == 0:
            return self._round_robin_selection(servers)

        # Simple weighted selection
        target = self.request_count % total_weight
        cumulative_weight = 0

        for server in servers:
            cumulative_weight += server.weight
            if target < cumulative_weight:
                return server

        return servers[0]

    def _least_response_time_selection(self, servers: List[ServerNode]) -> ServerNode:
        """Select server with lowest response time."""
        return min(servers, key=lambda s: s.response_time_ms)

    def _resource_based_selection(self, servers: List[ServerNode]) -> ServerNode:
        """Select server based on resource utilization."""

        def resource_score(server: ServerNode) -> float:
            if not server.resource_metrics:
                return 100.0  # High score = less preferred

            metrics = server.resource_metrics
            # Combine CPU, memory, and connection load
            cpu_load = metrics.cpu_percent
            memory_load = metrics.memory_percent
            connection_load = (
                server.current_connections / server.max_connections
            ) * 100

            return (cpu_load + memory_load + connection_load) / 3

        return min(servers, key=resource_score)

    def _ip_hash_selection(
        self, servers: List[ServerNode], request_context: Dict[str, Any]
    ) -> ServerNode:
        """Select server based on client IP hash."""
        client_ip = (
            request_context.get("client_ip", "127.0.0.1")
            if request_context
            else "127.0.0.1"
        )
        hash_value = hash(client_ip) % len(servers)
        return servers[hash_value]

    async def record_request(
        self,
        server_node_id: str,
        response_time: float,
        success: bool,
        bytes_transferred: int = 0,
    ):
        """Record request metrics for load balancer optimization."""
        self.request_count += 1
        self.response_times.append(response_time)

        if server_node_id in self.metrics.server_distribution:
            self.metrics.server_distribution[server_node_id] += 1

        if not success:
            self.error_count += 1

        # Update server metrics
        if server_node_id in self.servers:
            server = self.servers[server_node_id]
            server.response_time_ms = (
                server.response_time_ms + response_time
            ) / 2  # Moving average

        # Update load balancer metrics
        self.metrics.total_requests = self.request_count
        self.metrics.bytes_transferred += bytes_transferred

        # Calculate rates
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        if elapsed_time > 0:
            self.metrics.requests_per_second = self.request_count / elapsed_time
            self.metrics.error_rate = self.error_count / self.request_count

        if self.response_times:
            self.metrics.average_response_time = np.mean(
                self.response_times[-100:]
            )  # Last 100 requests

    async def health_check_servers(self) -> dict:
        """Perform health checks on all servers."""
        for server in self.servers.values():
            try:
                # Simulate health check (would be actual HTTP request in production)
                start_time = time.time()

                # Mock health check - in real implementation would ping server
                await asyncio.sleep(0.01)  # Simulate network delay

                response_time = (time.time() - start_time) * 1000

                # Update server health
                server.last_health_check = datetime.now()
                server.response_time_ms = response_time

                # Determine server status based on response time and resource usage
                if response_time > 5000:  # 5 seconds
                    server.status = ServerStatus.FAILING
                elif response_time > 1000:  # 1 second
                    server.status = ServerStatus.DEGRADED
                elif (
                    server.resource_metrics and server.resource_metrics.cpu_percent > 90
                ):
                    server.status = ServerStatus.OVERLOADED
                else:
                    server.status = ServerStatus.HEALTHY

            except Exception as e:
                logger.error(f"Health check failed for server {server.node_id}: {e}")
                server.status = ServerStatus.OFFLINE

    def get_load_distribution(self) -> Dict[str, float]:
        """Get current load distribution across servers."""
        total_requests = sum(self.metrics.server_distribution.values())
        if total_requests == 0:
            return {}

        distribution = {}
        for server_id, count in self.metrics.server_distribution.items():
            distribution[server_id] = (count / total_requests) * 100

        return distribution


class AutoScalingManager:
    """Manages automatic scaling of server resources."""

    def __init__(self, resource_monitor: SystemResourceMonitor) -> dict:
        self.resource_monitor = resource_monitor
        self.scaling_rules = {
            "cpu_scale_up_threshold": 80.0,
            "cpu_scale_down_threshold": 30.0,
            "memory_scale_up_threshold": 85.0,
            "memory_scale_down_threshold": 40.0,
            "scale_up_cooldown": 300,  # 5 minutes
            "scale_down_cooldown": 600,  # 10 minutes
        }

        self.last_scale_action = datetime.min
        self.scaling_history: List[Dict[str, Any]] = []
        self.predictor = ResourceUsagePredictor()

    async def evaluate_scaling_needs(self) -> List[OptimizationAction]:
        """Evaluate if scaling actions are needed."""
        if not self.resource_monitor.metrics_history:
            return []

        current_metrics = self.resource_monitor.metrics_history[-1]
        actions = []

        # Check cooldown period
        time_since_last_action = (
            datetime.now() - self.last_scale_action
        ).total_seconds()

        # CPU-based scaling
        if current_metrics.cpu_percent > self.scaling_rules["cpu_scale_up_threshold"]:
            if time_since_last_action > self.scaling_rules["scale_up_cooldown"]:
                actions.append(OptimizationAction.SCALE_UP)
                logger.info(
                    f"CPU scale-up triggered: {current_metrics.cpu_percent:.1f}%"
                )

        elif (
            current_metrics.cpu_percent < self.scaling_rules["cpu_scale_down_threshold"]
        ):
            if time_since_last_action > self.scaling_rules["scale_down_cooldown"]:
                actions.append(OptimizationAction.SCALE_DOWN)
                logger.info(
                    f"CPU scale-down triggered: {current_metrics.cpu_percent:.1f}%"
                )

        # Memory-based scaling
        if (
            current_metrics.memory_percent
            > self.scaling_rules["memory_scale_up_threshold"]
        ):
            if OptimizationAction.SCALE_UP not in actions:
                if time_since_last_action > self.scaling_rules["scale_up_cooldown"]:
                    actions.append(OptimizationAction.SCALE_UP)
                    logger.info(
                        f"Memory scale-up triggered: {current_metrics.memory_percent:.1f}%"
                    )

        # Predictive scaling
        predicted_usage = await self.predictor.predict_resource_usage(
            self.resource_monitor.metrics_history
        )
        if predicted_usage and predicted_usage["cpu_percent"] > 90:
            if OptimizationAction.SCALE_UP not in actions:
                actions.append(OptimizationAction.SCALE_UP)
                logger.info("Predictive scale-up triggered")

        return actions

    async def execute_scaling_action(self, action: OptimizationAction) -> bool:
        """Execute scaling action."""
        try:
            if action == OptimizationAction.SCALE_UP:
                success = await self._scale_up()
            elif action == OptimizationAction.SCALE_DOWN:
                success = await self._scale_down()
            else:
                success = await self._execute_other_action(action)

            if success:
                self.last_scale_action = datetime.now()
                self.scaling_history.append(
                    {
                        "action": action.value,
                        "timestamp": datetime.now(),
                        "success": success,
                    }
                )

            return success

        except Exception as e:
            logger.error(f"Failed to execute scaling action {action}: {e}")
            return False

    async def _scale_up(self) -> bool:
        """Scale up resources."""
        logger.info("Executing scale-up action")
        # In production, this would trigger actual scaling
        # For now, just simulate the action
        await asyncio.sleep(0.1)
        return True

    async def _scale_down(self) -> bool:
        """Scale down resources."""
        logger.info("Executing scale-down action")
        # In production, this would trigger actual scaling
        await asyncio.sleep(0.1)
        return True

    async def _execute_other_action(self, action: OptimizationAction) -> bool:
        """Execute other optimization actions."""
        logger.info(f"Executing optimization action: {action.value}")

        if action == OptimizationAction.REBALANCE:
            # Rebalance workload across servers
            return True
        elif action == OptimizationAction.THROTTLE:
            # Throttle incoming requests
            return True
        elif action == OptimizationAction.CACHE_EVICT:
            # Evict cache entries to free memory
            return True
        elif action == OptimizationAction.PROCESS_RESTART:
            # Restart problematic processes
            return True

        return False


class ResourceUsagePredictor:
    """Predicts future resource usage using machine learning."""

    def __init__(self) -> dict:
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_window = 10  # Number of previous metrics to use as features

    async def predict_resource_usage(
        self, metrics_history: List[SystemResourceMetrics]
    ) -> Optional[Dict[str, float]]:
        """Predict resource usage for next time period."""
        if len(metrics_history) < self.feature_window * 2:
            return None

        # Train model if not already trained
        if not self.is_trained:
            await self._train_model(metrics_history)

        if not self.is_trained:
            return None

        # Prepare features from recent metrics
        recent_metrics = metrics_history[-self.feature_window :]
        features = self._extract_features(recent_metrics)

        if features is None:
            return None

        # Make prediction
        try:
            features_scaled = self.scaler.transform([features])
            prediction = self.model.predict(features_scaled)

            return {
                "cpu_percent": max(0, min(100, prediction[0])),
                "memory_percent": max(
                    0, min(100, prediction[1] if len(prediction) > 1 else 50)
                ),
                "confidence": 0.8,  # Placeholder confidence score
            }

        except Exception as e:
            logger.error(f"Error making resource prediction: {e}")
            return None

    async def _train_model(self, metrics_history: List[SystemResourceMetrics]) -> dict:
        """Train the prediction model."""
        if len(metrics_history) < self.feature_window * 3:
            return

        features = []
        targets = []

        # Create training data using sliding window
        for i in range(self.feature_window, len(metrics_history)):
            window_metrics = metrics_history[i - self.feature_window : i]
            feature_vector = self._extract_features(window_metrics)

            if feature_vector is not None:
                target_metrics = metrics_history[i]
                features.append(feature_vector)
                targets.append(
                    [target_metrics.cpu_percent, target_metrics.memory_percent]
                )

        if len(features) < 10:  # Need minimum training data
            return

        try:
            X = np.array(features)
            y = np.array(targets)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True

            logger.info(
                f"Resource prediction model trained with {len(features)} samples"
            )

        except Exception as e:
            logger.error(f"Error training resource prediction model: {e}")

    def _extract_features(
        self, metrics: List[SystemResourceMetrics]
    ) -> Optional[List[float]]:
        """Extract feature vector from metrics window."""
        if len(metrics) < self.feature_window:
            return None

        features = []

        # Statistical features for each metric type
        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_percent for m in metrics]
        load_values = [m.load_average[0] for m in metrics]

        # Add statistical features
        features.extend(
            [
                np.mean(cpu_values),
                np.std(cpu_values),
                np.max(cpu_values),
                np.min(cpu_values),
                np.mean(memory_values),
                np.std(memory_values),
                np.max(memory_values),
                np.min(memory_values),
                np.mean(load_values),
                np.std(load_values),
            ]
        )

        # Add trend features
        if len(cpu_values) > 1:
            cpu_trend = cpu_values[-1] - cpu_values[0]
            memory_trend = memory_values[-1] - memory_values[0]
            features.extend([cpu_trend, memory_trend])
        else:
            features.extend([0.0, 0.0])

        # Add time-based features
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()
        features.extend([current_hour / 24.0, current_day / 7.0])

        return features


class ServerResourceOptimizationSystem:
    """Main server resource optimization and load balancing system."""

    def __init__(self, sdk: MobileERPSDK) -> dict:
        self.sdk = sdk
        self.resource_monitor = SystemResourceMonitor()
        self.load_balancer = IntelligentLoadBalancer()
        self.auto_scaler = AutoScalingManager(self.resource_monitor)

        # System metrics
        self.metrics = {
            "system_efficiency_score": 0.0,
            "load_balance_efficiency": 0.0,
            "resource_utilization": 0.0,
            "scaling_actions_count": 0,
            "server_health_score": 0.0,
            "total_requests_handled": 0,
        }

        # Initialize with sample servers
        self._initialize_sample_servers()

    def _initialize_sample_servers(self) -> dict:
        """Initialize with sample server configuration."""
        sample_servers = [
            ServerNode(
                node_id="server-1",
                hostname="app-server-1",
                ip_address="192.168.1.10",
                port=8000,
                weight=100,
                max_connections=1000,
                current_connections=0,
                cpu_cores=8,
                memory_gb=16,
                status=ServerStatus.HEALTHY,
                last_health_check=datetime.now(),
            ),
            ServerNode(
                node_id="server-2",
                hostname="app-server-2",
                ip_address="192.168.1.11",
                port=8000,
                weight=150,
                max_connections=1500,
                current_connections=0,
                cpu_cores=12,
                memory_gb=32,
                status=ServerStatus.HEALTHY,
                last_health_check=datetime.now(),
            ),
            ServerNode(
                node_id="server-3",
                hostname="app-server-3",
                ip_address="192.168.1.12",
                port=8000,
                weight=80,
                max_connections=800,
                current_connections=0,
                cpu_cores=4,
                memory_gb=8,
                status=ServerStatus.HEALTHY,
                last_health_check=datetime.now(),
            ),
        ]

        for server in sample_servers:
            self.load_balancer.add_server(server)

    async def start_optimization_system(self) -> dict:
        """Start the server resource optimization system."""
        logger.info("Starting Server Resource Optimization & Load Balancing System")

        # Start background optimization tasks
        tasks = [
            asyncio.create_task(self.resource_monitor.start_monitoring()),
            asyncio.create_task(self._optimize_resources_continuously()),
            asyncio.create_task(self._manage_load_balancing()),
            asyncio.create_task(self._monitor_server_health()),
            asyncio.create_task(self._evaluate_auto_scaling()),
        ]

        await asyncio.gather(*tasks)

    async def _optimize_resources_continuously(self) -> dict:
        """Continuously optimize system resources."""
        while True:
            try:
                # Get current resource trends
                trends = self.resource_monitor.get_resource_trends()

                if trends.get("trend") != "insufficient_data":
                    # Calculate system efficiency score
                    stability_score = trends.get("stability_score", 0.5)
                    cpu_efficiency = max(0, 100 - trends.get("cpu_avg", 50)) / 100
                    memory_efficiency = max(0, 100 - trends.get("memory_avg", 50)) / 100

                    self.metrics["system_efficiency_score"] = (
                        (stability_score + cpu_efficiency + memory_efficiency) / 3 * 100
                    )

                    self.metrics["resource_utilization"] = (
                        trends.get("cpu_avg", 0) + trends.get("memory_avg", 0)
                    ) / 2

                await asyncio.sleep(30)  # Optimize every 30 seconds

            except Exception as e:
                logger.error(f"Error in resource optimization: {e}")
                await asyncio.sleep(60)

    async def _manage_load_balancing(self) -> dict:
        """Manage load balancing optimization."""
        while True:
            try:
                # Perform health checks
                await self.load_balancer.health_check_servers()

                # Calculate load balance efficiency
                distribution = self.load_balancer.get_load_distribution()
                if distribution:
                    # Ideal distribution would be equal across all servers
                    ideal_percentage = 100 / len(distribution)
                    variance = np.var(list(distribution.values()))

                    # Lower variance = better balance
                    efficiency = max(0, 100 - (variance / ideal_percentage) * 10)
                    self.metrics["load_balance_efficiency"] = efficiency

                # Update total requests handled
                self.metrics["total_requests_handled"] = (
                    self.load_balancer.metrics.total_requests
                )

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in load balancing management: {e}")
                await asyncio.sleep(120)

    async def _monitor_server_health(self) -> dict:
        """Monitor overall server health."""
        while True:
            try:
                healthy_servers = sum(
                    1
                    for s in self.load_balancer.servers.values()
                    if s.status == ServerStatus.HEALTHY
                )
                total_servers = len(self.load_balancer.servers)

                if total_servers > 0:
                    self.metrics["server_health_score"] = (
                        healthy_servers / total_servers
                    ) * 100

                # Log health status
                if healthy_servers < total_servers:
                    logger.warning(
                        f"Server health: {healthy_servers}/{total_servers} healthy"
                    )

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in server health monitoring: {e}")
                await asyncio.sleep(60)

    async def _evaluate_auto_scaling(self) -> dict:
        """Evaluate and execute auto-scaling decisions."""
        while True:
            try:
                # Evaluate scaling needs
                scaling_actions = await self.auto_scaler.evaluate_scaling_needs()

                # Execute scaling actions
                for action in scaling_actions:
                    success = await self.auto_scaler.execute_scaling_action(action)
                    if success:
                        self.metrics["scaling_actions_count"] += 1
                        logger.info(
                            f"Successfully executed scaling action: {action.value}"
                        )

                await asyncio.sleep(60)  # Evaluate every minute

            except Exception as e:
                logger.error(f"Error in auto-scaling evaluation: {e}")
                await asyncio.sleep(120)

    async def handle_request(self, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming request with load balancing."""
        try:
            # Select optimal server
            server = await self.load_balancer.select_server(request_context)

            if not server:
                return {
                    "error": "No healthy servers available",
                    "status": "service_unavailable",
                }

            # Simulate request processing
            start_time = time.time()

            # Update server connection count
            server.current_connections += 1

            # Simulate processing time
            processing_time = np.random.normal(100, 20)  # 100ms average
            await asyncio.sleep(processing_time / 1000)

            # Calculate response time
            response_time = (time.time() - start_time) * 1000

            # Update server connection count
            server.current_connections = max(0, server.current_connections - 1)

            # Record request metrics
            success = response_time < 5000  # Consider successful if < 5 seconds
            await self.load_balancer.record_request(
                server.node_id,
                response_time,
                success,
                bytes_transferred=1024,  # Sample response size
            )

            return {
                "server_id": server.node_id,
                "response_time_ms": response_time,
                "status": "success" if success else "timeout",
                "load_balancer_algorithm": self.load_balancer.algorithm.value,
            }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {"error": str(e), "status": "error"}

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report."""
        return {
            "system_metrics": self.metrics,
            "resource_trends": self.resource_monitor.get_resource_trends(),
            "load_balancer_metrics": {
                "algorithm": self.load_balancer.algorithm.value,
                "total_requests": self.load_balancer.metrics.total_requests,
                "average_response_time": self.load_balancer.metrics.average_response_time,
                "error_rate": self.load_balancer.metrics.error_rate,
                "server_distribution": self.load_balancer.get_load_distribution(),
            },
            "server_status": {
                server.node_id: {
                    "status": server.status.value,
                    "response_time": server.response_time_ms,
                    "connections": server.current_connections,
                    "max_connections": server.max_connections,
                    "utilization": (server.current_connections / server.max_connections)
                    * 100,
                }
                for server in self.load_balancer.servers.values()
            },
            "scaling_history": self.auto_scaler.scaling_history[
                -10:
            ],  # Last 10 scaling actions
            "optimization_recommendations": self._generate_optimization_recommendations(),
        }

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Check system efficiency
        if self.metrics["system_efficiency_score"] < 70:
            recommendations.append(
                "Consider optimizing resource allocation - system efficiency is low"
            )

        # Check load balance
        if self.metrics["load_balance_efficiency"] < 80:
            recommendations.append(
                "Review load balancing algorithm - distribution is uneven"
            )

        # Check server health
        if self.metrics["server_health_score"] < 100:
            recommendations.append(
                "Address unhealthy servers to improve overall system reliability"
            )

        # Check resource utilization
        if self.metrics["resource_utilization"] > 85:
            recommendations.append("Consider scaling up - resource utilization is high")
        elif self.metrics["resource_utilization"] < 30:
            recommendations.append(
                "Consider scaling down - resource utilization is low"
            )

        return recommendations

    async def cleanup(self) -> dict:
        """Clean up system resources."""
        await self.resource_monitor.stop_monitoring()


# Example usage and integration
async def main() -> None:
    """Example usage of the Server Resource Optimization System."""
    # Initialize with mobile ERP SDK
    sdk = MobileERPSDK()

    # Create optimization system
    server_optimizer = ServerResourceOptimizationSystem(sdk)

    # Start optimization system
    await server_optimizer.start_optimization_system()


if __name__ == "__main__":
    asyncio.run(main())
