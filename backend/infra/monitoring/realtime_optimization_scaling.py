"""
CC02 v77.0 Day 22 - Enterprise Integrated Performance Optimization Platform
Real-time System Optimization & Scaling

Advanced real-time optimization with intelligent auto-scaling, adaptive resource
management, and predictive performance tuning for enterprise ERP systems.
"""

from __future__ import annotations

import asyncio
import logging
import math
import statistics
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Import from our existing mobile SDK and performance monitoring
from app.mobile.mobile_erp_sdk import MobileERPSDK
from app.performance.advanced_performance_monitoring import (
    MetricType,
    PerformanceMetric,
)


class ScalingDirection(Enum):
    """Scaling direction options."""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    NO_CHANGE = "no_change"


class ResourceType(Enum):
    """Resource types for scaling."""

    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE_CONNECTIONS = "db_connections"
    APPLICATION_INSTANCES = "app_instances"
    WORKER_PROCESSES = "worker_processes"
    CACHE_SIZE = "cache_size"


class OptimizationStrategy(Enum):
    """Optimization strategies."""

    PERFORMANCE_FIRST = "performance_first"
    COST_OPTIMIZED = "cost_optimized"
    BALANCED = "balanced"
    PREDICTIVE = "predictive"
    REACTIVE = "reactive"


class ScalingPolicy(Enum):
    """Auto-scaling policies."""

    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    CUSTOM = "custom"


@dataclass
class ScalingRule:
    """Auto-scaling rule configuration."""

    rule_id: str
    name: str
    resource_type: ResourceType
    metric_name: str
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_action: Dict[str, Any]
    scale_down_action: Dict[str, Any]
    cooldown_period: int  # seconds
    min_instances: int
    max_instances: int
    enabled: bool = True
    last_triggered: Optional[datetime] = None


@dataclass
class ResourceAllocation:
    """Current resource allocation state."""

    resource_type: ResourceType
    current_allocation: float
    min_allocation: float
    max_allocation: float
    utilization: float
    efficiency_score: float
    cost_per_unit: float
    last_updated: datetime


@dataclass
class ScalingAction:
    """Scaling action record."""

    action_id: str
    timestamp: datetime
    resource_type: ResourceType
    direction: ScalingDirection
    previous_allocation: float
    new_allocation: float
    trigger_metric: str
    trigger_value: float
    reason: str
    success: bool
    execution_time: float
    cost_impact: float


@dataclass
class OptimizationRecommendation:
    """System optimization recommendation."""

    recommendation_id: str
    timestamp: datetime
    category: str
    priority: str  # high, medium, low
    title: str
    description: str
    expected_benefit: str
    implementation_effort: str
    estimated_savings: float
    risk_level: str
    actions: List[Dict[str, Any]]
    metrics_to_monitor: List[str]


class ResourceMonitor:
    """Real-time resource monitoring and utilization tracking."""

    def __init__(self):
        self.resource_metrics: Dict[ResourceType, deque] = {
            resource_type: deque(maxlen=1000) for resource_type in ResourceType
        }
        self.utilization_thresholds = {
            ResourceType.CPU: {"warning": 70, "critical": 90},
            ResourceType.MEMORY: {"warning": 80, "critical": 95},
            ResourceType.STORAGE: {"warning": 85, "critical": 95},
            ResourceType.NETWORK: {"warning": 80, "critical": 95},
            ResourceType.DATABASE_CONNECTIONS: {"warning": 80, "critical": 95},
        }
        self.efficiency_calculator = EfficiencyCalculator()

    async def collect_resource_metrics(self) -> Dict[ResourceType, PerformanceMetric]:
        """Collect current resource utilization metrics."""
        metrics = {}
        timestamp = datetime.now()

        # Simulate resource metrics collection
        # In production, integrate with actual monitoring systems

        # CPU metrics
        cpu_utilization = np.random.normal(45, 15)  # Simulated CPU usage
        cpu_metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            name="cpu_utilization",
            type=MetricType.SYSTEM,
            value=max(0, min(100, cpu_utilization)),
            unit="percent",
            timestamp=timestamp,
            tags={"resource_type": "cpu"},
            source="resource_monitor",
            category="resource_utilization",
        )
        metrics[ResourceType.CPU] = cpu_metric
        self.resource_metrics[ResourceType.CPU].append(cpu_metric)

        # Memory metrics
        memory_utilization = np.random.normal(60, 20)
        memory_metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            name="memory_utilization",
            type=MetricType.SYSTEM,
            value=max(0, min(100, memory_utilization)),
            unit="percent",
            timestamp=timestamp,
            tags={"resource_type": "memory"},
            source="resource_monitor",
            category="resource_utilization",
        )
        metrics[ResourceType.MEMORY] = memory_metric
        self.resource_metrics[ResourceType.MEMORY].append(memory_metric)

        # Storage metrics
        storage_utilization = np.random.normal(35, 10)
        storage_metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            name="storage_utilization",
            type=MetricType.SYSTEM,
            value=max(0, min(100, storage_utilization)),
            unit="percent",
            timestamp=timestamp,
            tags={"resource_type": "storage"},
            source="resource_monitor",
            category="resource_utilization",
        )
        metrics[ResourceType.STORAGE] = storage_metric
        self.resource_metrics[ResourceType.STORAGE].append(storage_metric)

        # Application instance metrics
        instance_count = np.random.randint(2, 8)
        instance_metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            name="application_instances",
            type=MetricType.APPLICATION,
            value=instance_count,
            unit="count",
            timestamp=timestamp,
            tags={"resource_type": "instances"},
            source="resource_monitor",
            category="resource_allocation",
        )
        metrics[ResourceType.APPLICATION_INSTANCES] = instance_metric
        self.resource_metrics[ResourceType.APPLICATION_INSTANCES].append(
            instance_metric
        )

        return metrics

    async def calculate_resource_efficiency(self, resource_type: ResourceType) -> float:
        """Calculate efficiency score for a resource type."""
        recent_metrics = list(self.resource_metrics[resource_type])[-10:]
        if not recent_metrics:
            return 0.5  # Default efficiency

        utilizations = [metric.value for metric in recent_metrics]
        return await self.efficiency_calculator.calculate_efficiency(
            utilizations, resource_type
        )

    async def get_resource_trends(
        self, resource_type: ResourceType, window_minutes: int = 30
    ) -> Dict[str, Any]:
        """Get resource utilization trends."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_metrics = [
            metric
            for metric in self.resource_metrics[resource_type]
            if metric.timestamp >= cutoff_time
        ]

        if len(recent_metrics) < 2:
            return {"trend": "insufficient_data"}

        values = [metric.value for metric in recent_metrics]

        # Calculate trend
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)

        trend_direction = (
            "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
        )

        return {
            "trend": trend_direction,
            "slope": slope,
            "current_value": values[-1],
            "average_value": np.mean(values),
            "min_value": np.min(values),
            "max_value": np.max(values),
            "volatility": np.std(values),
            "sample_count": len(values),
        }


class EfficiencyCalculator:
    """Calculate resource efficiency scores."""

    async def calculate_efficiency(
        self, utilizations: List[float], resource_type: ResourceType
    ) -> float:
        """Calculate efficiency score based on utilization patterns."""
        if not utilizations:
            return 0.5

        avg_utilization = np.mean(utilizations)
        utilization_variance = np.var(utilizations)

        # Optimal utilization ranges by resource type
        optimal_ranges = {
            ResourceType.CPU: (60, 80),
            ResourceType.MEMORY: (70, 85),
            ResourceType.STORAGE: (60, 85),
            ResourceType.NETWORK: (40, 70),
            ResourceType.DATABASE_CONNECTIONS: (60, 80),
            ResourceType.APPLICATION_INSTANCES: (70, 90),
            ResourceType.WORKER_PROCESSES: (70, 85),
            ResourceType.CACHE_SIZE: (80, 95),
        }

        optimal_min, optimal_max = optimal_ranges.get(resource_type, (60, 80))

        # Calculate efficiency based on how close to optimal range
        if optimal_min <= avg_utilization <= optimal_max:
            utilization_score = 1.0
        elif avg_utilization < optimal_min:
            # Under-utilized
            utilization_score = avg_utilization / optimal_min
        else:
            # Over-utilized
            utilization_score = max(
                0, 1.0 - (avg_utilization - optimal_max) / (100 - optimal_max)
            )

        # Penalize high variance (inconsistent utilization)
        variance_penalty = min(utilization_variance / 100, 0.3)

        efficiency_score = max(0, utilization_score - variance_penalty)

        return min(efficiency_score, 1.0)


class AutoScaler:
    """Intelligent auto-scaling engine."""

    def __init__(self):
        self.scaling_rules: Dict[str, ScalingRule] = {}
        self.resource_allocations: Dict[ResourceType, ResourceAllocation] = {}
        self.scaling_history: deque = deque(maxlen=1000)
        self.predictor = ScalingPredictor()
        self.policy = ScalingPolicy.MODERATE

        # Initialize default scaling rules
        self._initialize_default_rules()
        self._initialize_resource_allocations()

    def _initialize_default_rules(self) -> None:
        """Initialize default auto-scaling rules."""
        self.scaling_rules = {
            "cpu_scaling": ScalingRule(
                rule_id="cpu_scaling",
                name="CPU Auto-scaling",
                resource_type=ResourceType.CPU,
                metric_name="cpu_utilization",
                scale_up_threshold=80.0,
                scale_down_threshold=30.0,
                scale_up_action={
                    "type": "increase_cpu",
                    "amount": 20,
                    "unit": "percent",
                },
                scale_down_action={
                    "type": "decrease_cpu",
                    "amount": 20,
                    "unit": "percent",
                },
                cooldown_period=300,  # 5 minutes
                min_instances=1,
                max_instances=10,
            ),
            "memory_scaling": ScalingRule(
                rule_id="memory_scaling",
                name="Memory Auto-scaling",
                resource_type=ResourceType.MEMORY,
                metric_name="memory_utilization",
                scale_up_threshold=85.0,
                scale_down_threshold=40.0,
                scale_up_action={
                    "type": "increase_memory",
                    "amount": 25,
                    "unit": "percent",
                },
                scale_down_action={
                    "type": "decrease_memory",
                    "amount": 25,
                    "unit": "percent",
                },
                cooldown_period=600,  # 10 minutes
                min_instances=1,
                max_instances=8,
            ),
            "instance_scaling": ScalingRule(
                rule_id="instance_scaling",
                name="Application Instance Scaling",
                resource_type=ResourceType.APPLICATION_INSTANCES,
                metric_name="cpu_utilization",
                scale_up_threshold=75.0,
                scale_down_threshold=25.0,
                scale_up_action={"type": "add_instance", "amount": 1, "unit": "count"},
                scale_down_action={
                    "type": "remove_instance",
                    "amount": 1,
                    "unit": "count",
                },
                cooldown_period=180,  # 3 minutes
                min_instances=2,
                max_instances=20,
            ),
        }

    def _initialize_resource_allocations(self) -> None:
        """Initialize current resource allocation state."""
        self.resource_allocations = {
            ResourceType.CPU: ResourceAllocation(
                resource_type=ResourceType.CPU,
                current_allocation=4.0,  # 4 cores
                min_allocation=2.0,
                max_allocation=16.0,
                utilization=45.0,
                efficiency_score=0.7,
                cost_per_unit=0.10,  # $0.10 per core-hour
                last_updated=datetime.now(),
            ),
            ResourceType.MEMORY: ResourceAllocation(
                resource_type=ResourceType.MEMORY,
                current_allocation=8.0,  # 8 GB
                min_allocation=4.0,
                max_allocation=64.0,
                utilization=60.0,
                efficiency_score=0.8,
                cost_per_unit=0.02,  # $0.02 per GB-hour
                last_updated=datetime.now(),
            ),
            ResourceType.APPLICATION_INSTANCES: ResourceAllocation(
                resource_type=ResourceType.APPLICATION_INSTANCES,
                current_allocation=3.0,  # 3 instances
                min_allocation=2.0,
                max_allocation=20.0,
                utilization=75.0,
                efficiency_score=0.85,
                cost_per_unit=1.00,  # $1.00 per instance-hour
                last_updated=datetime.now(),
            ),
        }

    async def evaluate_scaling_needs(
        self, current_metrics: Dict[ResourceType, PerformanceMetric]
    ) -> List[ScalingAction]:
        """Evaluate current metrics and determine scaling actions."""
        scaling_actions = []

        for rule_id, rule in self.scaling_rules.items():
            if not rule.enabled:
                continue

            # Check cooldown period
            if (
                rule.last_triggered
                and (datetime.now() - rule.last_triggered).total_seconds()
                < rule.cooldown_period
            ):
                continue

            # Get relevant metric
            resource_metric = current_metrics.get(rule.resource_type)
            if not resource_metric:
                continue

            # Evaluate scaling decision
            scaling_action = await self._evaluate_rule(rule, resource_metric)
            if scaling_action:
                scaling_actions.append(scaling_action)
                rule.last_triggered = datetime.now()

        return scaling_actions

    async def _evaluate_rule(
        self, rule: ScalingRule, metric: PerformanceMetric
    ) -> Optional[ScalingAction]:
        """Evaluate individual scaling rule."""
        current_allocation = self.resource_allocations.get(rule.resource_type)
        if not current_allocation:
            return None

        metric_value = metric.value

        # Determine scaling direction
        scaling_direction = ScalingDirection.NO_CHANGE
        action_config = None

        if metric_value >= rule.scale_up_threshold:
            if (
                current_allocation.current_allocation
                < current_allocation.max_allocation
            ):
                scaling_direction = ScalingDirection.SCALE_UP
                action_config = rule.scale_up_action
        elif metric_value <= rule.scale_down_threshold:
            if (
                current_allocation.current_allocation
                > current_allocation.min_allocation
            ):
                scaling_direction = ScalingDirection.SCALE_DOWN
                action_config = rule.scale_down_action

        if scaling_direction == ScalingDirection.NO_CHANGE:
            return None

        # Calculate new allocation
        new_allocation = await self._calculate_new_allocation(
            current_allocation, action_config, scaling_direction
        )

        # Create scaling action
        action = ScalingAction(
            action_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            resource_type=rule.resource_type,
            direction=scaling_direction,
            previous_allocation=current_allocation.current_allocation,
            new_allocation=new_allocation,
            trigger_metric=rule.metric_name,
            trigger_value=metric_value,
            reason=f"Metric {rule.metric_name} = {metric_value} {'>' if scaling_direction == ScalingDirection.SCALE_UP else '<'} threshold {rule.scale_up_threshold if scaling_direction == ScalingDirection.SCALE_UP else rule.scale_down_threshold}",
            success=False,  # Will be updated after execution
            execution_time=0.0,
            cost_impact=0.0,
        )

        return action

    async def _calculate_new_allocation(
        self,
        current_allocation: ResourceAllocation,
        action_config: Dict[str, Any],
        direction: ScalingDirection,
    ) -> float:
        """Calculate new resource allocation based on action configuration."""
        amount = action_config.get("amount", 1)
        unit = action_config.get("unit", "count")

        if unit == "percent":
            if direction == ScalingDirection.SCALE_UP:
                new_allocation = current_allocation.current_allocation * (
                    1 + amount / 100
                )
            else:
                new_allocation = current_allocation.current_allocation * (
                    1 - amount / 100
                )
        else:  # count or absolute units
            if direction == ScalingDirection.SCALE_UP:
                new_allocation = current_allocation.current_allocation + amount
            else:
                new_allocation = current_allocation.current_allocation - amount

        # Ensure within bounds
        new_allocation = max(
            current_allocation.min_allocation,
            min(current_allocation.max_allocation, new_allocation),
        )

        return new_allocation

    async def execute_scaling_action(self, action: ScalingAction) -> bool:
        """Execute scaling action."""
        start_time = time.time()

        try:
            # Get current allocation
            current_allocation = self.resource_allocations[action.resource_type]

            # Execute scaling based on resource type
            success = await self._execute_resource_scaling(action)

            if success:
                # Update allocation
                old_allocation = current_allocation.current_allocation
                current_allocation.current_allocation = action.new_allocation
                current_allocation.last_updated = datetime.now()

                # Calculate cost impact
                cost_diff = (
                    action.new_allocation - old_allocation
                ) * current_allocation.cost_per_unit
                action.cost_impact = cost_diff

                logging.info(
                    f"Scaling action executed: {action.resource_type.value} from {old_allocation} to {action.new_allocation}"
                )

            action.success = success
            action.execution_time = time.time() - start_time

            # Record action
            self.scaling_history.append(action)

            return success

        except Exception as e:
            logging.error(f"Scaling action failed: {e}")
            action.success = False
            action.execution_time = time.time() - start_time
            return False

    async def _execute_resource_scaling(self, action: ScalingAction) -> bool:
        """Execute the actual resource scaling operation."""
        # In production, integrate with cloud provider APIs or container orchestration

        if action.resource_type == ResourceType.CPU:
            # Scale CPU resources
            logging.info(
                f"Scaling CPU from {action.previous_allocation} to {action.new_allocation} cores"
            )
            return True

        elif action.resource_type == ResourceType.MEMORY:
            # Scale memory resources
            logging.info(
                f"Scaling memory from {action.previous_allocation} to {action.new_allocation} GB"
            )
            return True

        elif action.resource_type == ResourceType.APPLICATION_INSTANCES:
            # Scale application instances
            if action.direction == ScalingDirection.SCALE_UP:
                logging.info(
                    f"Adding application instance (total: {action.new_allocation})"
                )
            else:
                logging.info(
                    f"Removing application instance (total: {action.new_allocation})"
                )
            return True

        else:
            logging.warning(
                f"Scaling not implemented for resource type: {action.resource_type}"
            )
            return False

    async def get_scaling_recommendations(
        self,
        metrics: Dict[ResourceType, PerformanceMetric],
        forecast_data: Optional[Dict[str, Any]] = None,
    ) -> List[OptimizationRecommendation]:
        """Get intelligent scaling recommendations."""
        recommendations = []

        # Analyze current resource efficiency
        for resource_type, allocation in self.resource_allocations.items():
            if allocation.efficiency_score < 0.6:  # Low efficiency threshold
                recommendation = await self._generate_efficiency_recommendation(
                    resource_type, allocation
                )
                if recommendation:
                    recommendations.append(recommendation)

        # Analyze scaling patterns
        pattern_recommendations = await self._analyze_scaling_patterns()
        recommendations.extend(pattern_recommendations)

        # Predictive recommendations based on forecast
        if forecast_data:
            predictive_recommendations = (
                await self._generate_predictive_recommendations(forecast_data)
            )
            recommendations.extend(predictive_recommendations)

        return sorted(recommendations, key=lambda x: x.priority, reverse=True)

    async def _generate_efficiency_recommendation(
        self, resource_type: ResourceType, allocation: ResourceAllocation
    ) -> Optional[OptimizationRecommendation]:
        """Generate recommendation for improving resource efficiency."""
        if allocation.utilization < 30:
            # Under-utilized
            return OptimizationRecommendation(
                recommendation_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                category="resource_optimization",
                priority="medium",
                title=f"Reduce {resource_type.value} allocation",
                description=f"{resource_type.value} is under-utilized ({allocation.utilization:.1f}%). Consider reducing allocation to save costs.",
                expected_benefit="Cost reduction with maintained performance",
                implementation_effort="low",
                estimated_savings=allocation.current_allocation
                * allocation.cost_per_unit
                * 0.3,
                risk_level="low",
                actions=[
                    {
                        "type": "scale_down",
                        "resource": resource_type.value,
                        "amount": 30,
                        "unit": "percent",
                    }
                ],
                metrics_to_monitor=[
                    f"{resource_type.value}_utilization",
                    f"{resource_type.value}_efficiency",
                ],
            )

        elif allocation.utilization > 85:
            # Over-utilized
            return OptimizationRecommendation(
                recommendation_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                category="performance_optimization",
                priority="high",
                title=f"Increase {resource_type.value} allocation",
                description=f"{resource_type.value} is over-utilized ({allocation.utilization:.1f}%). Consider increasing allocation to improve performance.",
                expected_benefit="Improved performance and reduced bottlenecks",
                implementation_effort="low",
                estimated_savings=-allocation.current_allocation
                * allocation.cost_per_unit
                * 0.2,  # Cost increase
                risk_level="low",
                actions=[
                    {
                        "type": "scale_up",
                        "resource": resource_type.value,
                        "amount": 25,
                        "unit": "percent",
                    }
                ],
                metrics_to_monitor=[
                    f"{resource_type.value}_utilization",
                    "response_time",
                    "throughput",
                ],
            )

        return None

    async def _analyze_scaling_patterns(self) -> List[OptimizationRecommendation]:
        """Analyze historical scaling patterns for optimization opportunities."""
        recommendations = []

        # Analyze recent scaling actions
        recent_actions = [
            action
            for action in self.scaling_history
            if action.timestamp > datetime.now() - timedelta(hours=24)
        ]

        if len(recent_actions) > 10:  # Frequent scaling
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    category="scaling_optimization",
                    priority="medium",
                    title="Frequent scaling detected",
                    description="System is scaling frequently, which may indicate suboptimal thresholds or resource allocation.",
                    expected_benefit="Reduced scaling overhead and improved stability",
                    implementation_effort="medium",
                    estimated_savings=100.0,  # Estimated operational savings
                    risk_level="low",
                    actions=[
                        {"type": "review_thresholds", "category": "scaling_rules"},
                        {
                            "type": "implement_predictive_scaling",
                            "category": "optimization",
                        },
                    ],
                    metrics_to_monitor=[
                        "scaling_frequency",
                        "resource_utilization",
                        "performance_stability",
                    ],
                )
            )

        return recommendations

    async def _generate_predictive_recommendations(
        self, forecast_data: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate recommendations based on performance forecasts."""
        recommendations = []

        for metric_name, forecast in forecast_data.items():
            if "cpu" in metric_name.lower() and forecast.get("peak_forecast", 0) > 80:
                recommendations.append(
                    OptimizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        category="predictive_scaling",
                        priority="high",
                        title="Proactive CPU scaling recommended",
                        description=f"CPU utilization is forecasted to reach {forecast['peak_forecast']:.1f}%. Consider proactive scaling.",
                        expected_benefit="Prevent performance degradation during peak demand",
                        implementation_effort="low",
                        estimated_savings=0.0,
                        risk_level="low",
                        actions=[
                            {
                                "type": "proactive_scale_up",
                                "resource": "cpu",
                                "timing": "before_peak",
                                "amount": 20,
                                "unit": "percent",
                            }
                        ],
                        metrics_to_monitor=[
                            "cpu_utilization",
                            "response_time",
                            "user_satisfaction",
                        ],
                    )
                )

        return recommendations


class ScalingPredictor:
    """Predictive scaling based on historical patterns and ML models."""

    def __init__(self):
        self.models: Dict[ResourceType, RandomForestRegressor] = {}
        self.scalers: Dict[ResourceType, StandardScaler] = {}
        self.is_trained = False
        self.training_data: Dict[ResourceType, List[Dict[str, Any]]] = defaultdict(list)

    async def train_prediction_models(
        self, historical_data: Dict[ResourceType, List[Dict[str, Any]]]
    ) -> None:
        """Train prediction models for different resource types."""
        for resource_type, data in historical_data.items():
            if len(data) < 100:  # Need sufficient training data
                continue

            # Prepare features and targets
            features, targets = self._prepare_training_data(data)

            if len(features) < 50:
                continue

            # Scale features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)

            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(scaled_features, targets)

            # Store model and scaler
            self.models[resource_type] = model
            self.scalers[resource_type] = scaler

        self.is_trained = True
        logging.info(
            f"Scaling prediction models trained for {len(self.models)} resource types"
        )

    def _prepare_training_data(
        self, data: List[Dict[str, Any]]
    ) -> Tuple[List[List[float]], List[float]]:
        """Prepare training data for ML models."""
        features = []
        targets = []

        for i, point in enumerate(
            data[:-1]
        ):  # Exclude last point as we can't predict its future
            # Features: current utilization, trend, time-based features
            feature_vector = [
                point.get("utilization", 0),
                point.get("hour_of_day", 0),
                point.get("day_of_week", 0),
                point.get("month", 0),
                # Add trend features
                data[max(0, i - 5) : i + 1]
                and statistics.mean(
                    [p.get("utilization", 0) for p in data[max(0, i - 5) : i + 1]]
                )
                or 0,
                # Volatility feature
                data[max(0, i - 10) : i + 1]
                and statistics.stdev(
                    [p.get("utilization", 0) for p in data[max(0, i - 10) : i + 1]]
                )
                if len(data[max(0, i - 10) : i + 1]) > 1
                else 0,
            ]

            # Target: next utilization value
            next_utilization = data[i + 1].get("utilization", 0)

            features.append(feature_vector)
            targets.append(next_utilization)

        return features, targets

    async def predict_resource_demand(
        self,
        resource_type: ResourceType,
        current_metrics: Dict[str, Any],
        prediction_horizon_hours: int = 4,
    ) -> Dict[str, Any]:
        """Predict future resource demand."""
        if resource_type not in self.models:
            return {"prediction": None, "confidence": 0.0, "reason": "No trained model"}

        model = self.models[resource_type]
        scaler = self.scalers[resource_type]

        # Prepare current features
        current_time = datetime.now()
        features = [
            current_metrics.get("utilization", 0),
            current_time.hour,
            current_time.weekday(),
            current_time.month,
            current_metrics.get("trend_avg", 0),
            current_metrics.get("volatility", 0),
        ]

        # Scale features
        scaled_features = scaler.transform([features])

        # Make prediction
        prediction = model.predict(scaled_features)[0]

        # Calculate confidence (simplified)
        feature_importance = model.feature_importances_
        confidence = min(1.0, np.mean(feature_importance) * 2)

        # Generate multiple future predictions
        future_predictions = []
        current_features = features.copy()

        for hour in range(prediction_horizon_hours):
            scaled_current = scaler.transform([current_features])
            next_prediction = model.predict(scaled_current)[0]
            future_predictions.append(next_prediction)

            # Update features for next prediction
            current_features[0] = next_prediction  # Update utilization
            current_features[1] = (current_time.hour + hour + 1) % 24  # Update hour

        return {
            "prediction": prediction,
            "confidence": confidence,
            "future_predictions": future_predictions,
            "predicted_peak": max(future_predictions),
            "predicted_low": min(future_predictions),
            "trend": "increasing"
            if future_predictions[-1] > future_predictions[0]
            else "decreasing",
        }

    async def recommend_proactive_scaling(
        self, predictions: Dict[ResourceType, Dict[str, Any]]
    ) -> List[ScalingAction]:
        """Recommend proactive scaling actions based on predictions."""
        recommendations = []

        for resource_type, prediction_data in predictions.items():
            if prediction_data.get("confidence", 0) < 0.7:
                continue  # Skip low-confidence predictions

            predicted_peak = prediction_data.get("predicted_peak", 0)

            # If predicted peak is high, recommend proactive scaling
            if predicted_peak > 80:  # High utilization threshold
                action = ScalingAction(
                    action_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    resource_type=resource_type,
                    direction=ScalingDirection.SCALE_UP,
                    previous_allocation=0.0,  # Will be filled by auto-scaler
                    new_allocation=0.0,  # Will be calculated by auto-scaler
                    trigger_metric="predicted_utilization",
                    trigger_value=predicted_peak,
                    reason=f"Proactive scaling: predicted peak utilization of {predicted_peak:.1f}%",
                    success=False,
                    execution_time=0.0,
                    cost_impact=0.0,
                )
                recommendations.append(action)

        return recommendations


class LoadBalancer:
    """Intelligent load balancing and traffic management."""

    def __init__(self):
        self.backend_instances: Dict[str, Dict[str, Any]] = {}
        self.load_balancing_algorithm = "weighted_round_robin"
        self.health_check_interval = 30  # seconds
        self.circuit_breaker_threshold = 5  # consecutive failures
        self.traffic_patterns: deque = deque(maxlen=1000)

    async def register_backend(
        self,
        instance_id: str,
        endpoint: str,
        weight: int = 100,
        max_connections: int = 1000,
    ) -> None:
        """Register a backend instance."""
        self.backend_instances[instance_id] = {
            "endpoint": endpoint,
            "weight": weight,
            "max_connections": max_connections,
            "current_connections": 0,
            "healthy": True,
            "response_time": 0.0,
            "error_count": 0,
            "last_health_check": datetime.now(),
            "total_requests": 0,
            "successful_requests": 0,
        }

        logging.info(f"Registered backend instance: {instance_id} at {endpoint}")

    async def remove_backend(self, instance_id: str) -> bool:
        """Remove a backend instance."""
        if instance_id in self.backend_instances:
            del self.backend_instances[instance_id]
            logging.info(f"Removed backend instance: {instance_id}")
            return True
        return False

    async def select_backend(self) -> Optional[str]:
        """Select the best backend instance for load balancing."""
        healthy_backends = {
            instance_id: instance
            for instance_id, instance in self.backend_instances.items()
            if instance["healthy"]
            and instance["current_connections"] < instance["max_connections"]
        }

        if not healthy_backends:
            return None

        if self.load_balancing_algorithm == "round_robin":
            return await self._round_robin_selection(healthy_backends)
        elif self.load_balancing_algorithm == "weighted_round_robin":
            return await self._weighted_round_robin_selection(healthy_backends)
        elif self.load_balancing_algorithm == "least_connections":
            return await self._least_connections_selection(healthy_backends)
        elif self.load_balancing_algorithm == "response_time":
            return await self._response_time_selection(healthy_backends)
        else:
            # Default to round robin
            return await self._round_robin_selection(healthy_backends)

    async def _weighted_round_robin_selection(
        self, backends: Dict[str, Dict[str, Any]]
    ) -> str:
        """Select backend using weighted round robin algorithm."""
        # Calculate total weight
        total_weight = sum(backend["weight"] for backend in backends.values())

        # Select based on weight distribution
        import random

        random_value = random.randint(1, total_weight)

        cumulative_weight = 0
        for instance_id, backend in backends.items():
            cumulative_weight += backend["weight"]
            if random_value <= cumulative_weight:
                return instance_id

        # Fallback to first available
        return next(iter(backends.keys()))

    async def _least_connections_selection(
        self, backends: Dict[str, Dict[str, Any]]
    ) -> str:
        """Select backend with least connections."""
        return min(backends.keys(), key=lambda x: backends[x]["current_connections"])

    async def _response_time_selection(
        self, backends: Dict[str, Dict[str, Any]]
    ) -> str:
        """Select backend with best response time."""
        return min(backends.keys(), key=lambda x: backends[x]["response_time"])

    async def _round_robin_selection(self, backends: Dict[str, Dict[str, Any]]) -> str:
        """Simple round robin selection."""
        # Simplified round robin - in production, maintain state
        return next(iter(backends.keys()))

    async def update_backend_metrics(
        self, instance_id: str, response_time: float, success: bool
    ) -> None:
        """Update backend performance metrics."""
        if instance_id not in self.backend_instances:
            return

        backend = self.backend_instances[instance_id]
        backend["total_requests"] += 1

        if success:
            backend["successful_requests"] += 1
            backend["error_count"] = 0  # Reset error count on success
        else:
            backend["error_count"] += 1

        # Update response time (exponential moving average)
        alpha = 0.1
        backend["response_time"] = (
            alpha * response_time + (1 - alpha) * backend["response_time"]
        )

        # Check circuit breaker
        if backend["error_count"] >= self.circuit_breaker_threshold:
            backend["healthy"] = False
            logging.warning(f"Backend {instance_id} marked unhealthy due to errors")

    async def health_check_backends(self) -> Dict[str, bool]:
        """Perform health checks on all backend instances."""
        health_status = {}

        for instance_id, backend in self.backend_instances.items():
            # Simulate health check - in production, make actual HTTP requests
            is_healthy = await self._perform_health_check(backend["endpoint"])

            backend["healthy"] = is_healthy
            backend["last_health_check"] = datetime.now()
            health_status[instance_id] = is_healthy

            if is_healthy and backend["error_count"] > 0:
                backend["error_count"] = 0  # Reset error count if healthy

        return health_status

    async def _perform_health_check(self, endpoint: str) -> bool:
        """Perform actual health check on endpoint."""
        # Simplified health check - in production, make HTTP request to health endpoint
        # For simulation, assume 95% uptime
        import random

        return random.random() > 0.05

    async def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        total_backends = len(self.backend_instances)
        healthy_backends = sum(
            1 for b in self.backend_instances.values() if b["healthy"]
        )

        total_requests = sum(
            b["total_requests"] for b in self.backend_instances.values()
        )
        successful_requests = sum(
            b["successful_requests"] for b in self.backend_instances.values()
        )

        avg_response_time = sum(
            b["response_time"] for b in self.backend_instances.values()
        ) / max(total_backends, 1)

        return {
            "total_backends": total_backends,
            "healthy_backends": healthy_backends,
            "health_percentage": (healthy_backends / max(total_backends, 1)) * 100,
            "total_requests": total_requests,
            "success_rate": (successful_requests / max(total_requests, 1)) * 100,
            "average_response_time": avg_response_time,
            "load_balancing_algorithm": self.load_balancing_algorithm,
            "backend_details": {
                instance_id: {
                    "healthy": backend["healthy"],
                    "connections": backend["current_connections"],
                    "response_time": backend["response_time"],
                    "success_rate": (
                        backend["successful_requests"]
                        / max(backend["total_requests"], 1)
                    )
                    * 100,
                }
                for instance_id, backend in self.backend_instances.items()
            },
        }


class RealtimeOptimizationScalingSystem:
    """Main real-time optimization and scaling system."""

    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self.resource_monitor = ResourceMonitor()
        self.auto_scaler = AutoScaler()
        self.load_balancer = LoadBalancer()
        self.scaling_predictor = ScalingPredictor()

        # System state
        self.optimization_active = False
        self.optimization_strategy = OptimizationStrategy.BALANCED

        # Performance tracking
        self.optimization_metrics = {
            "scaling_actions_executed": 0,
            "cost_savings_achieved": 0.0,
            "performance_improvements": 0.0,
            "system_uptime": datetime.now(),
            "last_optimization": datetime.now(),
        }

    async def start_optimization(self) -> None:
        """Start real-time optimization and scaling."""
        self.optimization_active = True

        # Initialize backend instances for load balancer
        await self._initialize_load_balancer()

        # Start optimization tasks
        optimization_tasks = [
            asyncio.create_task(self._run_resource_monitoring()),
            asyncio.create_task(self._run_auto_scaling()),
            asyncio.create_task(self._run_load_balancing()),
            asyncio.create_task(self._run_predictive_optimization()),
        ]

        logging.info("Real-time optimization and scaling started")

        try:
            await asyncio.gather(*optimization_tasks)
        except Exception as e:
            logging.error(f"Optimization system error: {e}")
        finally:
            self.optimization_active = False

    async def stop_optimization(self) -> None:
        """Stop optimization and scaling."""
        self.optimization_active = False
        logging.info("Real-time optimization and scaling stopped")

    async def _initialize_load_balancer(self) -> None:
        """Initialize load balancer with backend instances."""
        # Register initial backend instances
        await self.load_balancer.register_backend(
            "instance-1", "http://app1:8000", weight=100
        )
        await self.load_balancer.register_backend(
            "instance-2", "http://app2:8000", weight=100
        )
        await self.load_balancer.register_backend(
            "instance-3", "http://app3:8000", weight=80
        )

    async def _run_resource_monitoring(self) -> None:
        """Run continuous resource monitoring."""
        while self.optimization_active:
            try:
                # Collect resource metrics
                current_metrics = await self.resource_monitor.collect_resource_metrics()

                # Update resource allocations with current utilization
                for resource_type, metric in current_metrics.items():
                    if resource_type in self.auto_scaler.resource_allocations:
                        allocation = self.auto_scaler.resource_allocations[
                            resource_type
                        ]
                        allocation.utilization = metric.value
                        allocation.efficiency_score = (
                            await self.resource_monitor.calculate_resource_efficiency(
                                resource_type
                            )
                        )

                await asyncio.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                logging.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(30)

    async def _run_auto_scaling(self) -> None:
        """Run auto-scaling evaluation and execution."""
        while self.optimization_active:
            try:
                # Get current metrics
                current_metrics = await self.resource_monitor.collect_resource_metrics()

                # Evaluate scaling needs
                scaling_actions = await self.auto_scaler.evaluate_scaling_needs(
                    current_metrics
                )

                # Execute scaling actions
                for action in scaling_actions:
                    success = await self.auto_scaler.execute_scaling_action(action)
                    if success:
                        self.optimization_metrics["scaling_actions_executed"] += 1
                        self.optimization_metrics["cost_savings_achieved"] += abs(
                            action.cost_impact
                        )

                        # Update load balancer if instances changed
                        if action.resource_type == ResourceType.APPLICATION_INSTANCES:
                            await self._update_load_balancer_instances(action)

                await asyncio.sleep(60)  # Evaluate every minute

            except Exception as e:
                logging.error(f"Auto-scaling error: {e}")
                await asyncio.sleep(60)

    async def _update_load_balancer_instances(
        self, scaling_action: ScalingAction
    ) -> None:
        """Update load balancer when instances are scaled."""
        if scaling_action.direction == ScalingDirection.SCALE_UP:
            # Add new instance
            new_instance_id = f"instance-{int(scaling_action.new_allocation)}"
            await self.load_balancer.register_backend(
                new_instance_id, f"http://app{int(scaling_action.new_allocation)}:8000"
            )
        elif scaling_action.direction == ScalingDirection.SCALE_DOWN:
            # Remove instance
            instance_to_remove = f"instance-{int(scaling_action.previous_allocation)}"
            await self.load_balancer.remove_backend(instance_to_remove)

    async def _run_load_balancing(self) -> None:
        """Run load balancing optimization."""
        while self.optimization_active:
            try:
                # Perform health checks
                health_status = await self.load_balancer.health_check_backends()

                # Log health status changes
                for instance_id, is_healthy in health_status.items():
                    if not is_healthy:
                        logging.warning(f"Backend instance {instance_id} is unhealthy")

                await asyncio.sleep(30)  # Health check every 30 seconds

            except Exception as e:
                logging.error(f"Load balancing error: {e}")
                await asyncio.sleep(30)

    async def _run_predictive_optimization(self) -> None:
        """Run predictive optimization based on forecasting."""
        # Train prediction models first
        await self._train_prediction_models()

        while self.optimization_active:
            try:
                # Get current metrics for prediction
                predictions = {}

                for resource_type in [
                    ResourceType.CPU,
                    ResourceType.MEMORY,
                    ResourceType.APPLICATION_INSTANCES,
                ]:
                    trends = await self.resource_monitor.get_resource_trends(
                        resource_type
                    )

                    current_metrics = {
                        "utilization": trends.get("current_value", 0),
                        "trend_avg": trends.get("average_value", 0),
                        "volatility": trends.get("volatility", 0),
                    }

                    prediction = await self.scaling_predictor.predict_resource_demand(
                        resource_type, current_metrics, prediction_horizon_hours=2
                    )

                    predictions[resource_type] = prediction

                # Generate proactive scaling recommendations
                proactive_actions = (
                    await self.scaling_predictor.recommend_proactive_scaling(
                        predictions
                    )
                )

                # Execute high-confidence proactive actions
                for action in proactive_actions:
                    if predictions[action.resource_type].get("confidence", 0) > 0.8:
                        # Fill in allocation details from auto-scaler
                        current_allocation = self.auto_scaler.resource_allocations.get(
                            action.resource_type
                        )
                        if current_allocation:
                            action.previous_allocation = (
                                current_allocation.current_allocation
                            )
                            action.new_allocation = (
                                current_allocation.current_allocation * 1.2
                            )  # 20% increase

                            success = await self.auto_scaler.execute_scaling_action(
                                action
                            )
                            if success:
                                logging.info(
                                    f"Proactive scaling executed for {action.resource_type.value}"
                                )

                await asyncio.sleep(300)  # Predictive optimization every 5 minutes

            except Exception as e:
                logging.error(f"Predictive optimization error: {e}")
                await asyncio.sleep(300)

    async def _train_prediction_models(self) -> None:
        """Train prediction models with historical data."""
        # Generate sample historical data for training
        training_data = {}

        for resource_type in [
            ResourceType.CPU,
            ResourceType.MEMORY,
            ResourceType.APPLICATION_INSTANCES,
        ]:
            # Generate realistic historical data
            data = []
            for i in range(200):  # 200 data points
                timestamp = datetime.now() - timedelta(hours=200 - i)

                # Simulate utilization patterns
                base_utilization = 50 + 20 * math.sin(i * 0.1)  # Cyclical pattern
                noise = np.random.normal(0, 5)
                utilization = max(0, min(100, base_utilization + noise))

                data.append(
                    {
                        "utilization": utilization,
                        "hour_of_day": timestamp.hour,
                        "day_of_week": timestamp.weekday(),
                        "month": timestamp.month,
                    }
                )

            training_data[resource_type] = data

        await self.scaling_predictor.train_prediction_models(training_data)

    async def get_optimization_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive optimization dashboard."""
        # Get current resource status
        resource_status = {}
        for resource_type, allocation in self.auto_scaler.resource_allocations.items():
            trends = await self.resource_monitor.get_resource_trends(resource_type)
            resource_status[resource_type.value] = {
                "current_allocation": allocation.current_allocation,
                "utilization": allocation.utilization,
                "efficiency_score": allocation.efficiency_score,
                "trend": trends.get("trend", "stable"),
                "cost_per_hour": allocation.current_allocation
                * allocation.cost_per_unit,
            }

        # Get load balancer status
        lb_stats = await self.load_balancer.get_load_balancer_stats()

        # Get recent scaling actions
        recent_actions = list(self.auto_scaler.scaling_history)[-10:]

        # Calculate optimization metrics
        uptime_hours = (
            datetime.now() - self.optimization_metrics["system_uptime"]
        ).total_seconds() / 3600

        return {
            "dashboard_generated": datetime.now().isoformat(),
            "optimization_status": "active" if self.optimization_active else "inactive",
            "strategy": self.optimization_strategy.value,
            "system_metrics": {
                "uptime_hours": uptime_hours,
                "scaling_actions_executed": self.optimization_metrics[
                    "scaling_actions_executed"
                ],
                "cost_savings_achieved": self.optimization_metrics[
                    "cost_savings_achieved"
                ],
                "optimization_rate": self.optimization_metrics[
                    "scaling_actions_executed"
                ]
                / max(uptime_hours, 1),
            },
            "resource_status": resource_status,
            "load_balancer": {
                "healthy_backends": lb_stats["healthy_backends"],
                "total_backends": lb_stats["total_backends"],
                "success_rate": lb_stats["success_rate"],
                "average_response_time": lb_stats["average_response_time"],
            },
            "recent_scaling_actions": [
                {
                    "timestamp": action.timestamp.isoformat(),
                    "resource_type": action.resource_type.value,
                    "direction": action.direction.value,
                    "reason": action.reason,
                    "success": action.success,
                }
                for action in recent_actions
            ],
            "predictive_models": {
                "trained": self.scaling_predictor.is_trained,
                "model_count": len(self.scaling_predictor.models),
            },
        }

    async def get_optimization_recommendations(
        self,
    ) -> List[OptimizationRecommendation]:
        """Get current optimization recommendations."""
        current_metrics = await self.resource_monitor.collect_resource_metrics()

        # Get scaling recommendations
        recommendations = await self.auto_scaler.get_scaling_recommendations(
            current_metrics
        )

        # Add load balancing recommendations
        lb_stats = await self.load_balancer.get_load_balancer_stats()

        if lb_stats["health_percentage"] < 80:
            recommendations.append(
                OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    category="infrastructure_health",
                    priority="high",
                    title="Backend health issues detected",
                    description=f"Only {lb_stats['health_percentage']:.1f}% of backends are healthy",
                    expected_benefit="Improved system reliability and performance",
                    implementation_effort="medium",
                    estimated_savings=0.0,
                    risk_level="medium",
                    actions=[
                        {"type": "investigate_backend_health", "priority": "immediate"},
                        {"type": "add_backup_instances", "priority": "high"},
                    ],
                    metrics_to_monitor=[
                        "backend_health",
                        "response_time",
                        "error_rate",
                    ],
                )
            )

        return recommendations

    async def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization and scaling report."""
        dashboard = await self.get_optimization_dashboard()
        recommendations = await self.get_optimization_recommendations()

        # Calculate total cost
        total_cost_per_hour = sum(
            status["cost_per_hour"] for status in dashboard["resource_status"].values()
        )

        return {
            "report_generated": datetime.now().isoformat(),
            "executive_summary": {
                "optimization_strategy": dashboard["strategy"],
                "system_health": "optimal"
                if dashboard["load_balancer"]["success_rate"] > 95
                else "needs_attention",
                "cost_efficiency": "good"
                if total_cost_per_hour < 100
                else "review_needed",
                "scaling_effectiveness": dashboard["system_metrics"][
                    "optimization_rate"
                ],
            },
            "resource_utilization": dashboard["resource_status"],
            "scaling_performance": {
                "actions_executed": dashboard["system_metrics"][
                    "scaling_actions_executed"
                ],
                "cost_savings": dashboard["system_metrics"]["cost_savings_achieved"],
                "success_rate": 95.0,  # Calculate from actual data
            },
            "load_balancing": dashboard["load_balancer"],
            "optimization_recommendations": [
                {
                    "title": rec.title,
                    "priority": rec.priority,
                    "expected_benefit": rec.expected_benefit,
                    "estimated_savings": rec.estimated_savings,
                }
                for rec in recommendations[:5]  # Top 5 recommendations
            ],
            "cost_analysis": {
                "current_hourly_cost": total_cost_per_hour,
                "projected_monthly_cost": total_cost_per_hour * 24 * 30,
                "potential_savings": sum(
                    rec.estimated_savings
                    for rec in recommendations
                    if rec.estimated_savings > 0
                ),
            },
        }


# Usage example and testing
async def main():
    """Example usage of the Real-time Optimization & Scaling System."""
    # Initialize SDK (mock)
    sdk = MobileERPSDK()

    # Initialize optimization system
    optimization_system = RealtimeOptimizationScalingSystem(sdk)

    # Start optimization (run for a short time for demo)
    optimization_task = asyncio.create_task(optimization_system.start_optimization())

    # Let it run for a bit to collect data and perform optimizations
    await asyncio.sleep(15)

    # Get optimization dashboard
    dashboard = await optimization_system.get_optimization_dashboard()
    print("Optimization Dashboard:")
    print(f"Status: {dashboard['optimization_status']}")
    print(f"Strategy: {dashboard['strategy']}")
    print(f"Scaling Actions: {dashboard['system_metrics']['scaling_actions_executed']}")
    print(
        f"Load Balancer Health: {dashboard['load_balancer']['healthy_backends']}/{dashboard['load_balancer']['total_backends']}"
    )

    # Get recommendations
    recommendations = await optimization_system.get_optimization_recommendations()
    print(f"\nOptimization Recommendations: {len(recommendations)} generated")
    for rec in recommendations[:3]:
        print(f"- {rec.title} (Priority: {rec.priority})")

    # Generate report
    report = await optimization_system.generate_optimization_report()
    print("\nOptimization Report:")
    print(f"System Health: {report['executive_summary']['system_health']}")
    print(f"Cost Efficiency: {report['executive_summary']['cost_efficiency']}")
    print(f"Current Hourly Cost: ${report['cost_analysis']['current_hourly_cost']:.2f}")

    # Stop optimization
    await optimization_system.stop_optimization()
    optimization_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
