"""
CC02 v55.0 Scalability Manager
Horizontal and Vertical Scaling Management System
Day 6 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union, Set, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import asyncio
import json
import math
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ScalingError, ResourceError
from app.models.scaling import (
    ScalingPolicy, ScalingEvent, ResourcePool, LoadBalancer,
    InstanceMetrics, AutoScaler, CapacityPlan
)
from app.services.audit_service import AuditService

class ScalingType(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    HYBRID = "hybrid"

class ScalingDirection(str, Enum):
    UP = "up"
    DOWN = "down"

class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    INSTANCES = "instances"

class LoadBalancingStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"

class InstanceStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    MAINTENANCE = "maintenance"

class ScalingTrigger(str, Enum):
    THRESHOLD = "threshold"
    PREDICTIVE = "predictive"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    EVENT_DRIVEN = "event_driven"

@dataclass
class ScalingMetrics:
    """Scaling decision metrics"""
    timestamp: datetime
    cpu_utilization: float
    memory_utilization: float
    request_rate: float
    response_time: float
    error_rate: float
    queue_depth: int
    active_connections: int
    instance_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScalingDecision:
    """Scaling decision result"""
    decision_id: UUID
    scaling_type: ScalingType
    scaling_direction: ScalingDirection
    target_instances: Optional[int]
    target_resources: Dict[ResourceType, float]
    reason: str
    confidence: float
    estimated_cost: float
    estimated_completion_time: timedelta
    prerequisites: List[str]
    risks: List[str]
    rollback_plan: Dict[str, Any]
    created_at: datetime

@dataclass
class InstanceConfig:
    """Instance configuration"""
    instance_type: str
    cpu_cores: int
    memory_gb: float
    storage_gb: float
    network_bandwidth_mbps: float
    cost_per_hour: float
    availability_zones: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseScalingStrategy(ABC):
    """Base class for scaling strategies"""
    
    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id
        self.enabled = True
    
    @abstractmethod
    async def evaluate(self, metrics: ScalingMetrics) -> Optional[ScalingDecision]:
        """Evaluate if scaling is needed"""
        pass
    
    @abstractmethod
    async def execute(self, decision: ScalingDecision) -> bool:
        """Execute scaling decision"""
        pass

class ThresholdBasedStrategy(BaseScalingStrategy):
    """Threshold-based scaling strategy"""
    
    def __init__(self):
        super().__init__("threshold_based")
        self.thresholds = {
            'cpu_scale_up': 80.0,
            'cpu_scale_down': 20.0,
            'memory_scale_up': 85.0,
            'memory_scale_down': 25.0,
            'response_time_scale_up': 2.0,  # seconds
            'request_rate_scale_up': 1000.0,  # requests/minute
            'min_instances': 2,
            'max_instances': 20
        }
        self.cooldown_period = timedelta(minutes=5)
        self.last_scaling_action: Optional[datetime] = None
    
    async def evaluate(self, metrics: ScalingMetrics) -> Optional[ScalingDecision]:
        """Evaluate threshold-based scaling"""
        
        # Check cooldown period
        if (self.last_scaling_action and 
            datetime.utcnow() - self.last_scaling_action < self.cooldown_period):
            return None
        
        # Scale up conditions
        scale_up_triggers = []
        
        if metrics.cpu_utilization > self.thresholds['cpu_scale_up']:
            scale_up_triggers.append(f"CPU utilization: {metrics.cpu_utilization:.1f}%")
        
        if metrics.memory_utilization > self.thresholds['memory_scale_up']:
            scale_up_triggers.append(f"Memory utilization: {metrics.memory_utilization:.1f}%")
        
        if metrics.response_time > self.thresholds['response_time_scale_up']:
            scale_up_triggers.append(f"Response time: {metrics.response_time:.2f}s")
        
        if metrics.request_rate > self.thresholds['request_rate_scale_up']:
            scale_up_triggers.append(f"Request rate: {metrics.request_rate:.0f}/min")
        
        # Scale down conditions
        scale_down_triggers = []
        
        if (metrics.cpu_utilization < self.thresholds['cpu_scale_down'] and
            metrics.memory_utilization < self.thresholds['memory_scale_down'] and
            metrics.instance_count > self.thresholds['min_instances']):
            scale_down_triggers.append("Low resource utilization")
        
        # Determine scaling decision
        if scale_up_triggers and metrics.instance_count < self.thresholds['max_instances']:
            target_instances = min(
                metrics.instance_count + max(1, metrics.instance_count // 4),
                self.thresholds['max_instances']
            )
            
            return ScalingDecision(
                decision_id=uuid4(),
                scaling_type=ScalingType.HORIZONTAL,
                scaling_direction=ScalingDirection.UP,
                target_instances=target_instances,
                target_resources={},
                reason=f"Scale up triggered by: {', '.join(scale_up_triggers)}",
                confidence=0.8,
                estimated_cost=50.0 * (target_instances - metrics.instance_count),
                estimated_completion_time=timedelta(minutes=5),
                prerequisites=["Health check passing", "Load balancer ready"],
                risks=["Temporary increased costs", "Instance startup time"],
                rollback_plan={
                    "action": "scale_down",
                    "target": metrics.instance_count,
                    "timeout": "10 minutes"
                },
                created_at=datetime.utcnow()
            )
        
        elif scale_down_triggers:
            target_instances = max(
                metrics.instance_count - 1,
                self.thresholds['min_instances']
            )
            
            return ScalingDecision(
                decision_id=uuid4(),
                scaling_type=ScalingType.HORIZONTAL,
                scaling_direction=ScalingDirection.DOWN,
                target_instances=target_instances,
                target_resources={},
                reason=f"Scale down triggered by: {', '.join(scale_down_triggers)}",
                confidence=0.9,
                estimated_cost=-50.0 * (metrics.instance_count - target_instances),
                estimated_completion_time=timedelta(minutes=3),
                prerequisites=["Graceful shutdown possible", "No critical operations"],
                risks=["Potential capacity shortage", "Connection disruption"],
                rollback_plan={
                    "action": "scale_up",
                    "target": metrics.instance_count,
                    "timeout": "5 minutes"
                },
                created_at=datetime.utcnow()
            )
        
        return None
    
    async def execute(self, decision: ScalingDecision) -> bool:
        """Execute threshold-based scaling"""
        try:
            self.last_scaling_action = datetime.utcnow()
            
            if decision.scaling_direction == ScalingDirection.UP:
                return await self._scale_up(decision)
            else:
                return await self._scale_down(decision)
        
        except Exception as e:
            logging.error(f"Failed to execute scaling decision: {e}")
            return False
    
    async def _scale_up(self, decision: ScalingDecision) -> bool:
        """Scale up instances"""
        logging.info(f"Scaling up to {decision.target_instances} instances")
        # In production, would integrate with cloud provider APIs
        return True
    
    async def _scale_down(self, decision: ScalingDecision) -> bool:
        """Scale down instances"""
        logging.info(f"Scaling down to {decision.target_instances} instances")
        # In production, would gracefully terminate instances
        return True

class PredictiveScalingStrategy(BaseScalingStrategy):
    """Machine learning-based predictive scaling"""
    
    def __init__(self):
        super().__init__("predictive")
        self.historical_data: List[ScalingMetrics] = []
        self.prediction_horizon = timedelta(minutes=30)
        self.confidence_threshold = 0.7
    
    async def evaluate(self, metrics: ScalingMetrics) -> Optional[ScalingDecision]:
        """Evaluate predictive scaling"""
        
        # Store historical data
        self.historical_data.append(metrics)
        
        # Keep only last week of data
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        self.historical_data = [
            m for m in self.historical_data
            if m.timestamp > cutoff_time
        ]
        
        # Need sufficient historical data
        if len(self.historical_data) < 100:
            return None
        
        # Predict future load
        predicted_metrics = await self._predict_future_load()
        
        if not predicted_metrics:
            return None
        
        # Check if predicted load requires scaling
        if predicted_metrics.cpu_utilization > 70.0:
            current_instances = metrics.instance_count
            predicted_load_factor = predicted_metrics.cpu_utilization / 100.0
            target_instances = math.ceil(current_instances * predicted_load_factor / 0.7)
            
            if target_instances > current_instances:
                return ScalingDecision(
                    decision_id=uuid4(),
                    scaling_type=ScalingType.HORIZONTAL,
                    scaling_direction=ScalingDirection.UP,
                    target_instances=min(target_instances, 20),
                    target_resources={},
                    reason=f"Predictive scaling for expected {predicted_metrics.cpu_utilization:.1f}% CPU",
                    confidence=0.75,
                    estimated_cost=50.0 * (target_instances - current_instances),
                    estimated_completion_time=timedelta(minutes=5),
                    prerequisites=["Prediction confidence > 70%"],
                    risks=["Prediction accuracy", "Over-provisioning"],
                    rollback_plan={
                        "action": "revert_to_current",
                        "target": current_instances,
                        "timeout": "15 minutes"
                    },
                    created_at=datetime.utcnow()
                )
        
        return None
    
    async def execute(self, decision: ScalingDecision) -> bool:
        """Execute predictive scaling"""
        logging.info(f"Executing predictive scaling: {decision.reason}")
        # In production, would implement actual scaling
        return True
    
    async def _predict_future_load(self) -> Optional[ScalingMetrics]:
        """Predict future load using simple time series analysis"""
        
        if len(self.historical_data) < 50:
            return None
        
        # Simple moving average prediction
        recent_data = self.historical_data[-50:]
        
        avg_cpu = sum(m.cpu_utilization for m in recent_data) / len(recent_data)
        avg_memory = sum(m.memory_utilization for m in recent_data) / len(recent_data)
        avg_request_rate = sum(m.request_rate for m in recent_data) / len(recent_data)
        avg_response_time = sum(m.response_time for m in recent_data) / len(recent_data)
        
        # Apply trend factor (simplified)
        trend_factor = 1.1  # Assume 10% growth trend
        
        return ScalingMetrics(
            timestamp=datetime.utcnow() + self.prediction_horizon,
            cpu_utilization=avg_cpu * trend_factor,
            memory_utilization=avg_memory * trend_factor,
            request_rate=avg_request_rate * trend_factor,
            response_time=avg_response_time,
            error_rate=0.0,
            queue_depth=0,
            active_connections=0,
            instance_count=0
        )

class LoadBalancer:
    """Load balancer management"""
    
    def __init__(self):
        self.strategy = LoadBalancingStrategy.ROUND_ROBIN
        self.instances: List[Dict[str, Any]] = []
        self.health_check_interval = 30  # seconds
        self.health_check_timeout = 5  # seconds
    
    async def add_instance(self, instance_id: str, endpoint: str, weight: float = 1.0):
        """Add instance to load balancer"""
        
        instance = {
            'id': instance_id,
            'endpoint': endpoint,
            'weight': weight,
            'status': InstanceStatus.STARTING,
            'health_check_failures': 0,
            'last_health_check': None,
            'connections': 0,
            'response_time': 0.0,
            'added_at': datetime.utcnow()
        }
        
        self.instances.append(instance)
        
        # Start health checking
        asyncio.create_task(self._monitor_instance_health(instance))
    
    async def remove_instance(self, instance_id: str, graceful: bool = True):
        """Remove instance from load balancer"""
        
        instance = next((i for i in self.instances if i['id'] == instance_id), None)
        if not instance:
            return False
        
        if graceful:
            # Wait for connections to drain
            instance['status'] = InstanceStatus.STOPPING
            await self._drain_connections(instance)
        
        self.instances = [i for i in self.instances if i['id'] != instance_id]
        return True
    
    async def get_next_instance(self) -> Optional[Dict[str, Any]]:
        """Get next instance based on load balancing strategy"""
        
        healthy_instances = [
            i for i in self.instances
            if i['status'] == InstanceStatus.RUNNING
        ]
        
        if not healthy_instances:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(healthy_instances, key=lambda i: i['connections'])
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return min(healthy_instances, key=lambda i: i['response_time'])
        else:
            return healthy_instances[0]
    
    def _round_robin_selection(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Round-robin instance selection"""
        if not hasattr(self, '_rr_index'):
            self._rr_index = 0
        
        instance = instances[self._rr_index % len(instances)]
        self._rr_index += 1
        return instance
    
    async def _monitor_instance_health(self, instance: Dict[str, Any]):
        """Monitor instance health"""
        
        while instance in self.instances:
            try:
                # Perform health check
                healthy = await self._health_check(instance)
                
                if healthy:
                    instance['health_check_failures'] = 0
                    if instance['status'] == InstanceStatus.STARTING:
                        instance['status'] = InstanceStatus.RUNNING
                else:
                    instance['health_check_failures'] += 1
                    
                    if instance['health_check_failures'] >= 3:
                        instance['status'] = InstanceStatus.FAILED
                
                instance['last_health_check'] = datetime.utcnow()
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logging.error(f"Health check error for {instance['id']}: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _health_check(self, instance: Dict[str, Any]) -> bool:
        """Perform health check on instance"""
        try:
            # In production, would make HTTP request to health endpoint
            # For now, simulate health check
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _drain_connections(self, instance: Dict[str, Any]):
        """Drain connections from instance"""
        timeout = 30  # seconds
        start_time = datetime.utcnow()
        
        while (instance['connections'] > 0 and
               (datetime.utcnow() - start_time).total_seconds() < timeout):
            await asyncio.sleep(1)

class AutoScaler:
    """Automatic scaling orchestration"""
    
    def __init__(self):
        self.strategies: List[BaseScalingStrategy] = [
            ThresholdBasedStrategy(),
            PredictiveScalingStrategy()
        ]
        self.load_balancer = LoadBalancer()
        self.audit_service = AuditService()
        self.scaling_history: List[ScalingEvent] = []
        self.instance_configs: Dict[str, InstanceConfig] = {}
        self.current_metrics: Optional[ScalingMetrics] = None
        self.is_enabled = True
    
    async def evaluate_scaling(self, metrics: ScalingMetrics) -> List[ScalingDecision]:
        """Evaluate scaling decisions from all strategies"""
        
        self.current_metrics = metrics
        decisions = []
        
        if not self.is_enabled:
            return decisions
        
        for strategy in self.strategies:
            if strategy.enabled:
                try:
                    decision = await strategy.evaluate(metrics)
                    if decision:
                        decisions.append(decision)
                except Exception as e:
                    logging.error(f"Error in scaling strategy {strategy.strategy_id}: {e}")
        
        return decisions
    
    async def execute_scaling(self, decision: ScalingDecision) -> bool:
        """Execute scaling decision"""
        
        try:
            # Find appropriate strategy
            strategy = next(
                (s for s in self.strategies if s.strategy_id in decision.reason.lower()),
                self.strategies[0]  # Default to first strategy
            )
            
            # Execute scaling
            success = await strategy.execute(decision)
            
            if success:
                # Update load balancer if horizontal scaling
                if decision.scaling_type == ScalingType.HORIZONTAL:
                    await self._update_load_balancer(decision)
                
                # Record scaling event
                await self._record_scaling_event(decision, success)
            
            return success
            
        except Exception as e:
            logging.error(f"Failed to execute scaling decision {decision.decision_id}: {e}")
            await self._record_scaling_event(decision, False, str(e))
            return False
    
    async def _update_load_balancer(self, decision: ScalingDecision):
        """Update load balancer configuration"""
        
        current_instances = len(self.load_balancer.instances)
        target_instances = decision.target_instances or current_instances
        
        if decision.scaling_direction == ScalingDirection.UP:
            # Add new instances
            for i in range(target_instances - current_instances):
                instance_id = f"instance-{uuid4().hex[:8]}"
                endpoint = f"http://instance-{i+current_instances+1}:8000"
                await self.load_balancer.add_instance(instance_id, endpoint)
        
        elif decision.scaling_direction == ScalingDirection.DOWN:
            # Remove instances
            instances_to_remove = current_instances - target_instances
            for i in range(instances_to_remove):
                if self.load_balancer.instances:
                    instance = self.load_balancer.instances[-1]
                    await self.load_balancer.remove_instance(instance['id'], graceful=True)
    
    async def _record_scaling_event(
        self,
        decision: ScalingDecision,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Record scaling event"""
        
        event = ScalingEvent(
            id=uuid4(),
            decision_id=decision.decision_id,
            scaling_type=decision.scaling_type,
            scaling_direction=decision.scaling_direction,
            target_instances=decision.target_instances,
            success=success,
            error_message=error_message,
            execution_time=(datetime.utcnow() - decision.created_at).total_seconds(),
            created_at=datetime.utcnow()
        )
        
        self.scaling_history.append(event)
        
        # Audit log
        await self.audit_service.log_event(
            event_type="scaling_executed",
            entity_type="autoscaler",
            entity_id=decision.decision_id,
            details={
                'scaling_type': decision.scaling_type.value,
                'scaling_direction': decision.scaling_direction.value,
                'target_instances': decision.target_instances,
                'success': success,
                'reason': decision.reason,
                'error_message': error_message
            }
        )
    
    async def get_scaling_metrics(self) -> Dict[str, Any]:
        """Get scaling metrics and statistics"""
        
        recent_events = [
            e for e in self.scaling_history
            if e.created_at > datetime.utcnow() - timedelta(hours=24)
        ]
        
        successful_scalings = len([e for e in recent_events if e.success])
        total_scalings = len(recent_events)
        success_rate = (successful_scalings / total_scalings * 100) if total_scalings > 0 else 0
        
        return {
            'current_instances': len(self.load_balancer.instances),
            'healthy_instances': len([
                i for i in self.load_balancer.instances
                if i['status'] == InstanceStatus.RUNNING
            ]),
            'load_balancing_strategy': self.load_balancer.strategy.value,
            'autoscaling_enabled': self.is_enabled,
            'active_strategies': len([s for s in self.strategies if s.enabled]),
            'scaling_events_24h': total_scalings,
            'scaling_success_rate': success_rate,
            'current_metrics': {
                'cpu_utilization': self.current_metrics.cpu_utilization if self.current_metrics else 0,
                'memory_utilization': self.current_metrics.memory_utilization if self.current_metrics else 0,
                'request_rate': self.current_metrics.request_rate if self.current_metrics else 0,
                'response_time': self.current_metrics.response_time if self.current_metrics else 0
            },
            'generated_at': datetime.utcnow().isoformat()
        }
    
    async def predict_capacity_needs(
        self,
        time_horizon: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """Predict future capacity requirements"""
        
        if not self.current_metrics:
            return {}
        
        # Simple growth projection
        historical_growth_rate = 0.05  # 5% monthly growth
        days = time_horizon.days
        growth_factor = (1 + historical_growth_rate) ** (days / 30.0)
        
        current_instances = len(self.load_balancer.instances)
        predicted_load = self.current_metrics.request_rate * growth_factor
        predicted_instances = math.ceil(current_instances * growth_factor)
        
        estimated_cost = predicted_instances * 50.0 * 24 * days  # $50/hour/instance
        
        return {
            'time_horizon_days': days,
            'current_instances': current_instances,
            'predicted_instances': predicted_instances,
            'growth_factor': growth_factor,
            'predicted_request_rate': predicted_load,
            'estimated_monthly_cost': estimated_cost,
            'recommendations': [
                f"Plan for {predicted_instances} instances",
                f"Budget ${estimated_cost:.2f} for infrastructure",
                "Consider reserved instances for cost optimization"
            ],
            'generated_at': datetime.utcnow().isoformat()
        }

# Singleton instance
scalability_manager = AutoScaler()

# Helper functions
async def evaluate_scaling_needs(metrics: ScalingMetrics) -> List[ScalingDecision]:
    """Evaluate scaling needs"""
    return await scalability_manager.evaluate_scaling(metrics)

async def execute_scaling_decision(decision: ScalingDecision) -> bool:
    """Execute scaling decision"""
    return await scalability_manager.execute_scaling(decision)

async def get_scaling_status() -> Dict[str, Any]:
    """Get current scaling status"""
    return await scalability_manager.get_scaling_metrics()

async def predict_capacity_requirements(days: int = 30) -> Dict[str, Any]:
    """Predict capacity requirements"""
    return await scalability_manager.predict_capacity_needs(timedelta(days=days))