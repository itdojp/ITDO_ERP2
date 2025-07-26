"""
CC02 v78.0 Day 23: Infrastructure Auto Management & Scaling Module
Enterprise-grade infrastructure automation with intelligent scaling, resource optimization, and cost management.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import boto3
import numpy as np
from kubernetes import client, config
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from app.mobile_sdk.core import MobileERPSDK

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"


class ResourceType(Enum):
    """Infrastructure resource types."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    LOAD_BALANCER = "load_balancer"
    CDN = "cdn"


class ScalingAction(Enum):
    """Auto-scaling actions."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    OPTIMIZE = "optimize"
    TERMINATE = "terminate"
    MIGRATE = "migrate"


class ResourceStatus(Enum):
    """Resource status states."""
    RUNNING = "running"
    STOPPED = "stopped"
    PENDING = "pending"
    TERMINATING = "terminating"
    FAILED = "failed"
    OPTIMIZING = "optimizing"


@dataclass
class InfrastructureResource:
    """Infrastructure resource definition."""
    resource_id: str
    resource_type: ResourceType
    cloud_provider: CloudProvider
    region: str
    
    # Resource specifications
    cpu_cores: int
    memory_gb: int
    storage_gb: int
    network_bandwidth_mbps: int
    
    # Current state
    status: ResourceStatus
    utilization: Dict[str, float] = field(default_factory=dict)
    cost_per_hour: float = 0.0
    
    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_scaled: Optional[datetime] = None
    
    # Performance metrics
    avg_cpu_utilization: float = 0.0
    avg_memory_utilization: float = 0.0
    network_io_mbps: float = 0.0
    disk_io_mbps: float = 0.0


@dataclass
class ScalingRule:
    """Auto-scaling rule definition."""
    rule_id: str
    resource_type: ResourceType
    metric_name: str
    
    # Thresholds
    scale_up_threshold: float
    scale_down_threshold: float
    
    # Scaling parameters
    scale_up_factor: float = 1.5
    scale_down_factor: float = 0.8
    min_instances: int = 1
    max_instances: int = 100
    
    # Cooldown periods
    scale_up_cooldown_minutes: int = 5
    scale_down_cooldown_minutes: int = 15
    
    # Evaluation parameters
    evaluation_period_minutes: int = 5
    datapoints_to_alarm: int = 2
    
    enabled: bool = True


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation."""
    recommendation_id: str
    resource_id: str
    recommendation_type: str
    
    # Cost impact
    current_monthly_cost: float
    projected_monthly_cost: float
    potential_savings: float
    
    # Implementation details
    action_required: str
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    
    description: str
    justification: str


class CloudResourceManager:
    """Manages cloud resources across different providers."""
    
    def __init__(self):
        self.cloud_clients = {}
        self.resources: Dict[str, InfrastructureResource] = {}
        self.resource_history: List[Dict[str, Any]] = []
        
        # Initialize cloud clients
        self._initialize_cloud_clients()
    
    def _initialize_cloud_clients(self):
        """Initialize cloud provider clients."""
        try:
            # AWS client
            self.cloud_clients[CloudProvider.AWS] = {
                'ec2': boto3.client('ec2'),
                'rds': boto3.client('rds'),
                'ecs': boto3.client('ecs'),
                'lambda': boto3.client('lambda'),
                'cloudwatch': boto3.client('cloudwatch')
            }
        except Exception as e:
            logger.warning(f"Failed to initialize AWS client: {e}")
        
        # Azure and GCP clients would be initialized similarly
        # For now, we'll simulate their functionality
    
    async def discover_resources(self, cloud_provider: CloudProvider, region: str = None) -> List[InfrastructureResource]:
        """Discover existing infrastructure resources."""
        discovered_resources = []
        
        try:
            if cloud_provider == CloudProvider.AWS:
                discovered_resources.extend(await self._discover_aws_resources(region))
            elif cloud_provider == CloudProvider.AZURE:
                discovered_resources.extend(await self._discover_azure_resources(region))
            elif cloud_provider == CloudProvider.GCP:
                discovered_resources.extend(await self._discover_gcp_resources(region))
            
            # Update local resource cache
            for resource in discovered_resources:
                self.resources[resource.resource_id] = resource
            
            logger.info(f"Discovered {len(discovered_resources)} resources in {cloud_provider.value}")
            
        except Exception as e:
            logger.error(f"Resource discovery failed for {cloud_provider.value}: {e}")
        
        return discovered_resources
    
    async def _discover_aws_resources(self, region: str = None) -> List[InfrastructureResource]:
        """Discover AWS resources."""
        resources = []
        
        try:
            ec2_client = self.cloud_clients[CloudProvider.AWS]['ec2']
            
            # Discover EC2 instances
            if region:
                response = ec2_client.describe_instances()
            else:
                # For demo, create sample resources
                sample_resources = [
                    InfrastructureResource(
                        resource_id="i-0123456789abcdef0",
                        resource_type=ResourceType.COMPUTE,
                        cloud_provider=CloudProvider.AWS,
                        region="us-east-1",
                        cpu_cores=4,
                        memory_gb=16,
                        storage_gb=100,
                        network_bandwidth_mbps=1000,
                        status=ResourceStatus.RUNNING,
                        cost_per_hour=0.20,
                        tags={"Environment": "production", "Application": "itdo-erp"},
                        avg_cpu_utilization=65.0,
                        avg_memory_utilization=70.0
                    ),
                    InfrastructureResource(
                        resource_id="rds-postgres-prod",
                        resource_type=ResourceType.DATABASE,
                        cloud_provider=CloudProvider.AWS,
                        region="us-east-1",
                        cpu_cores=8,
                        memory_gb=32,
                        storage_gb=500,
                        network_bandwidth_mbps=2000,
                        status=ResourceStatus.RUNNING,
                        cost_per_hour=0.80,
                        tags={"Environment": "production", "Database": "postgresql"},
                        avg_cpu_utilization=45.0,
                        avg_memory_utilization=60.0
                    )
                ]
                resources.extend(sample_resources)
            
        except Exception as e:
            logger.error(f"AWS resource discovery failed: {e}")
        
        return resources
    
    async def _discover_azure_resources(self, region: str = None) -> List[InfrastructureResource]:
        """Discover Azure resources."""
        # Simulate Azure resource discovery
        return []
    
    async def _discover_gcp_resources(self, region: str = None) -> List[InfrastructureResource]:
        """Discover GCP resources."""
        # Simulate GCP resource discovery
        return []
    
    async def create_resource(self, resource_spec: Dict[str, Any]) -> InfrastructureResource:
        """Create new infrastructure resource."""
        try:
            cloud_provider = CloudProvider(resource_spec['cloud_provider'])
            resource_type = ResourceType(resource_spec['resource_type'])
            
            # Generate resource ID
            resource_id = f"{resource_type.value}-{int(time.time())}"
            
            resource = InfrastructureResource(
                resource_id=resource_id,
                resource_type=resource_type,
                cloud_provider=cloud_provider,
                region=resource_spec.get('region', 'us-east-1'),
                cpu_cores=resource_spec.get('cpu_cores', 2),
                memory_gb=resource_spec.get('memory_gb', 4),
                storage_gb=resource_spec.get('storage_gb', 20),
                network_bandwidth_mbps=resource_spec.get('network_bandwidth_mbps', 1000),
                status=ResourceStatus.PENDING,
                cost_per_hour=resource_spec.get('cost_per_hour', 0.10),
                tags=resource_spec.get('tags', {})
            )
            
            # Simulate resource creation
            await asyncio.sleep(2)
            resource.status = ResourceStatus.RUNNING
            
            self.resources[resource_id] = resource
            
            # Record creation event
            self.resource_history.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'create',
                'resource_id': resource_id,
                'resource_type': resource_type.value,
                'cloud_provider': cloud_provider.value
            })
            
            logger.info(f"Created resource: {resource_id}")
            return resource
            
        except Exception as e:
            logger.error(f"Resource creation failed: {e}")
            raise
    
    async def scale_resource(self, resource_id: str, scaling_action: ScalingAction, 
                           scaling_factor: float = 1.5) -> bool:
        """Scale infrastructure resource."""
        try:
            if resource_id not in self.resources:
                raise ValueError(f"Resource not found: {resource_id}")
            
            resource = self.resources[resource_id]
            
            if scaling_action == ScalingAction.SCALE_UP:
                # Increase resource capacity
                resource.cpu_cores = int(resource.cpu_cores * scaling_factor)
                resource.memory_gb = int(resource.memory_gb * scaling_factor)
                new_cost = resource.cost_per_hour * scaling_factor
            
            elif scaling_action == ScalingAction.SCALE_DOWN:
                # Decrease resource capacity
                resource.cpu_cores = max(1, int(resource.cpu_cores / scaling_factor))
                resource.memory_gb = max(1, int(resource.memory_gb / scaling_factor))
                new_cost = resource.cost_per_hour / scaling_factor
            
            elif scaling_action == ScalingAction.OPTIMIZE:
                # Optimize resource configuration
                # This would involve more complex optimization logic
                new_cost = resource.cost_per_hour * 0.9  # 10% cost reduction
            
            else:
                logger.warning(f"Scaling action {scaling_action.value} not implemented")
                return False
            
            resource.cost_per_hour = new_cost
            resource.last_scaled = datetime.now()
            resource.status = ResourceStatus.OPTIMIZING
            
            # Simulate scaling operation
            await asyncio.sleep(3)
            resource.status = ResourceStatus.RUNNING
            
            # Record scaling event
            self.resource_history.append({
                'timestamp': datetime.now().isoformat(),
                'action': scaling_action.value,
                'resource_id': resource_id,
                'scaling_factor': scaling_factor,
                'new_cpu_cores': resource.cpu_cores,
                'new_memory_gb': resource.memory_gb,
                'new_cost_per_hour': resource.cost_per_hour
            })
            
            logger.info(f"Scaled resource {resource_id}: {scaling_action.value} (factor: {scaling_factor})")
            return True
            
        except Exception as e:
            logger.error(f"Resource scaling failed: {e}")
            return False
    
    async def terminate_resource(self, resource_id: str) -> bool:
        """Terminate infrastructure resource."""
        try:
            if resource_id not in self.resources:
                raise ValueError(f"Resource not found: {resource_id}")
            
            resource = self.resources[resource_id]
            resource.status = ResourceStatus.TERMINATING
            
            # Simulate termination
            await asyncio.sleep(2)
            
            # Remove from active resources
            del self.resources[resource_id]
            
            # Record termination event
            self.resource_history.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'terminate',
                'resource_id': resource_id,
                'resource_type': resource.resource_type.value
            })
            
            logger.info(f"Terminated resource: {resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Resource termination failed: {e}")
            return False
    
    def get_resource_utilization(self, resource_id: str) -> Dict[str, float]:
        """Get current resource utilization metrics."""
        if resource_id not in self.resources:
            return {}
        
        resource = self.resources[resource_id]
        
        # Simulate real-time utilization data
        current_utilization = {
            'cpu_percent': np.random.normal(resource.avg_cpu_utilization, 10),
            'memory_percent': np.random.normal(resource.avg_memory_utilization, 8),
            'network_io_mbps': resource.network_io_mbps + np.random.normal(0, 5),
            'disk_io_mbps': resource.disk_io_mbps + np.random.normal(0, 2),
            'timestamp': time.time()
        }
        
        # Ensure values are within valid ranges
        current_utilization['cpu_percent'] = max(0, min(100, current_utilization['cpu_percent']))
        current_utilization['memory_percent'] = max(0, min(100, current_utilization['memory_percent']))
        current_utilization['network_io_mbps'] = max(0, current_utilization['network_io_mbps'])
        current_utilization['disk_io_mbps'] = max(0, current_utilization['disk_io_mbps'])
        
        return current_utilization


class AutoScalingEngine:
    """Intelligent auto-scaling engine for infrastructure resources."""
    
    def __init__(self, resource_manager: CloudResourceManager):
        self.resource_manager = resource_manager
        self.scaling_rules: Dict[str, ScalingRule] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        
        # ML models for predictive scaling
        self.demand_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Initialize default scaling rules
        self._initialize_default_scaling_rules()
    
    def _initialize_default_scaling_rules(self):
        """Initialize default auto-scaling rules."""
        # CPU-based scaling rule
        cpu_rule = ScalingRule(
            rule_id="cpu-scaling-rule",
            resource_type=ResourceType.COMPUTE,
            metric_name="cpu_percent",
            scale_up_threshold=80.0,
            scale_down_threshold=30.0,
            scale_up_factor=1.5,
            scale_down_factor=0.7,
            min_instances=2,
            max_instances=20,
            scale_up_cooldown_minutes=5,
            scale_down_cooldown_minutes=15
        )
        
        # Memory-based scaling rule
        memory_rule = ScalingRule(
            rule_id="memory-scaling-rule",
            resource_type=ResourceType.COMPUTE,
            metric_name="memory_percent",
            scale_up_threshold=85.0,
            scale_down_threshold=40.0,
            scale_up_factor=1.3,
            scale_down_factor=0.8,
            min_instances=1,
            max_instances=15,
            scale_up_cooldown_minutes=10,
            scale_down_cooldown_minutes=20
        )
        
        # Database connection scaling rule
        db_rule = ScalingRule(
            rule_id="database-connections-rule",
            resource_type=ResourceType.DATABASE,
            metric_name="connection_utilization",
            scale_up_threshold=75.0,
            scale_down_threshold=25.0,
            scale_up_factor=1.2,
            scale_down_factor=0.9,
            min_instances=1,
            max_instances=5,
            scale_up_cooldown_minutes=15,
            scale_down_cooldown_minutes=30
        )
        
        self.scaling_rules["cpu"] = cpu_rule
        self.scaling_rules["memory"] = memory_rule
        self.scaling_rules["database"] = db_rule
    
    async def evaluate_scaling_needs(self) -> List[Dict[str, Any]]:
        """Evaluate scaling needs for all resources."""
        scaling_decisions = []
        
        for resource_id, resource in self.resource_manager.resources.items():
            try:
                # Get current utilization
                utilization = self.resource_manager.get_resource_utilization(resource_id)
                
                if not utilization:
                    continue
                
                # Evaluate against scaling rules
                for rule_id, rule in self.scaling_rules.items():
                    if not rule.enabled or rule.resource_type != resource.resource_type:
                        continue
                    
                    if rule.metric_name not in utilization:
                        continue
                    
                    metric_value = utilization[rule.metric_name]
                    scaling_decision = await self._evaluate_scaling_rule(
                        resource, rule, metric_value
                    )
                    
                    if scaling_decision:
                        scaling_decisions.append(scaling_decision)
            
            except Exception as e:
                logger.error(f"Error evaluating scaling for resource {resource_id}: {e}")
        
        return scaling_decisions
    
    async def _evaluate_scaling_rule(self, resource: InfrastructureResource, 
                                   rule: ScalingRule, metric_value: float) -> Optional[Dict[str, Any]]:
        """Evaluate individual scaling rule."""
        try:
            # Check cooldown period
            if resource.last_scaled:
                time_since_scaling = (datetime.now() - resource.last_scaled).total_seconds() / 60
                
                if metric_value > rule.scale_up_threshold:
                    if time_since_scaling < rule.scale_up_cooldown_minutes:
                        return None  # Still in cooldown
                elif metric_value < rule.scale_down_threshold:
                    if time_since_scaling < rule.scale_down_cooldown_minutes:
                        return None  # Still in cooldown
            
            # Determine scaling action
            scaling_action = None
            scaling_factor = 1.0
            
            if metric_value > rule.scale_up_threshold:
                scaling_action = ScalingAction.SCALE_UP
                scaling_factor = rule.scale_up_factor
                
            elif metric_value < rule.scale_down_threshold:
                scaling_action = ScalingAction.SCALE_DOWN
                scaling_factor = rule.scale_down_factor
            
            if scaling_action:
                return {
                    'resource_id': resource.resource_id,
                    'rule_id': rule.rule_id,
                    'metric_name': rule.metric_name,
                    'metric_value': metric_value,
                    'threshold_breached': rule.scale_up_threshold if scaling_action == ScalingAction.SCALE_UP else rule.scale_down_threshold,
                    'scaling_action': scaling_action,
                    'scaling_factor': scaling_factor,
                    'priority': 'high' if metric_value > rule.scale_up_threshold * 1.2 else 'medium'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating scaling rule {rule.rule_id}: {e}")
            return None
    
    async def execute_scaling_decision(self, scaling_decision: Dict[str, Any]) -> bool:
        """Execute scaling decision."""
        try:
            resource_id = scaling_decision['resource_id']
            scaling_action = scaling_decision['scaling_action']
            scaling_factor = scaling_decision['scaling_factor']
            
            # Execute scaling
            success = await self.resource_manager.scale_resource(
                resource_id, scaling_action, scaling_factor
            )
            
            if success:
                # Record scaling decision
                self.scaling_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'resource_id': resource_id,
                    'rule_id': scaling_decision['rule_id'],
                    'metric_name': scaling_decision['metric_name'],
                    'metric_value': scaling_decision['metric_value'],
                    'scaling_action': scaling_action.value,
                    'scaling_factor': scaling_factor,
                    'success': True
                })
                
                logger.info(f"Executed scaling decision for {resource_id}: {scaling_action.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to execute scaling decision: {e}")
            
            # Record failed scaling attempt
            self.scaling_history.append({
                'timestamp': datetime.now().isoformat(),
                'resource_id': scaling_decision.get('resource_id'),
                'scaling_action': scaling_decision.get('scaling_action', {}).get('value', 'unknown'),
                'success': False,
                'error': str(e)
            })
            
            return False
    
    async def train_predictive_model(self, historical_data: List[Dict[str, Any]]):
        """Train predictive scaling model."""
        if len(historical_data) < 100:
            logger.warning("Insufficient historical data for predictive model training")
            return
        
        try:
            # Prepare training data
            features = []
            targets = []
            
            for data_point in historical_data:
                feature_vector = [
                    data_point.get('cpu_percent', 0),
                    data_point.get('memory_percent', 0),
                    data_point.get('network_io_mbps', 0),
                    data_point.get('request_rate', 0),
                    data_point.get('hour_of_day', 0),
                    data_point.get('day_of_week', 0)
                ]
                
                # Target is the resource demand in the next hour
                target = data_point.get('future_demand', 0)
                
                features.append(feature_vector)
                targets.append(target)
            
            X = np.array(features)
            y = np.array(targets)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.demand_predictor.fit(X_scaled, y)
            self.is_trained = True
            
            logger.info(f"Predictive scaling model trained with {len(features)} samples")
            
        except Exception as e:
            logger.error(f"Error training predictive model: {e}")
    
    async def predict_scaling_needs(self, resource_id: str, hours_ahead: int = 1) -> Optional[Dict[str, Any]]:
        """Predict future scaling needs."""
        if not self.is_trained:
            return None
        
        try:
            # Get current utilization
            utilization = self.resource_manager.get_resource_utilization(resource_id)
            if not utilization:
                return None
            
            # Prepare feature vector for prediction
            current_time = datetime.now()
            feature_vector = [
                utilization.get('cpu_percent', 0),
                utilization.get('memory_percent', 0),
                utilization.get('network_io_mbps', 0),
                100,  # Mock request rate
                (current_time.hour + hours_ahead) % 24,
                current_time.weekday()
            ]
            
            X = np.array([feature_vector])
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            predicted_demand = self.demand_predictor.predict(X_scaled)[0]
            
            # Determine if scaling is needed
            current_capacity = utilization.get('cpu_percent', 0)
            
            scaling_needed = None
            if predicted_demand > current_capacity * 1.2:
                scaling_needed = ScalingAction.SCALE_UP
            elif predicted_demand < current_capacity * 0.6:
                scaling_needed = ScalingAction.SCALE_DOWN
            
            return {
                'resource_id': resource_id,
                'predicted_demand': predicted_demand,
                'current_capacity': current_capacity,
                'scaling_needed': scaling_needed,
                'confidence': 0.8,  # Mock confidence score
                'hours_ahead': hours_ahead
            }
            
        except Exception as e:
            logger.error(f"Error predicting scaling needs: {e}")
            return None


class CostOptimizer:
    """Optimizes infrastructure costs through intelligent resource management."""
    
    def __init__(self, resource_manager: CloudResourceManager):
        self.resource_manager = resource_manager
        self.optimization_history: List[CostOptimizationRecommendation] = []
        
        # Cost optimization rules
        self.optimization_rules = {
            'underutilized_resources': {
                'cpu_threshold': 20.0,
                'memory_threshold': 30.0,
                'evaluation_period_days': 7
            },
            'oversized_resources': {
                'cpu_threshold': 90.0,
                'memory_threshold': 95.0,
                'frequency_threshold': 0.1  # 10% of time
            },
            'unused_resources': {
                'cpu_threshold': 5.0,
                'network_threshold': 1.0,
                'evaluation_period_days': 3
            }
        }
    
    async def analyze_cost_optimization_opportunities(self) -> List[CostOptimizationRecommendation]:
        """Analyze and generate cost optimization recommendations."""
        recommendations = []
        
        for resource_id, resource in self.resource_manager.resources.items():
            try:
                # Get resource utilization history
                utilization_history = await self._get_utilization_history(resource_id)
                
                if not utilization_history:
                    continue
                
                # Analyze for different optimization opportunities
                underutil_rec = await self._analyze_underutilized_resource(resource, utilization_history)
                if underutil_rec:
                    recommendations.append(underutil_rec)
                
                oversized_rec = await self._analyze_oversized_resource(resource, utilization_history)
                if oversized_rec:
                    recommendations.append(oversized_rec)
                
                unused_rec = await self._analyze_unused_resource(resource, utilization_history)
                if unused_rec:
                    recommendations.append(unused_rec)
                
                rightsizing_rec = await self._analyze_rightsizing_opportunity(resource, utilization_history)
                if rightsizing_rec:
                    recommendations.append(rightsizing_rec)
            
            except Exception as e:
                logger.error(f"Error analyzing cost optimization for {resource_id}: {e}")
        
        # Sort recommendations by potential savings
        recommendations.sort(key=lambda x: x.potential_savings, reverse=True)
        
        return recommendations
    
    async def _get_utilization_history(self, resource_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get historical utilization data for resource."""
        # In a real implementation, this would query monitoring systems
        # For now, simulate historical data
        
        history = []
        for i in range(days * 24):  # Hourly data for specified days
            timestamp = datetime.now() - timedelta(hours=i)
            
            # Simulate utilization data with some variation
            base_cpu = self.resource_manager.resources[resource_id].avg_cpu_utilization
            base_memory = self.resource_manager.resources[resource_id].avg_memory_utilization
            
            cpu_utilization = max(0, min(100, base_cpu + np.random.normal(0, 15)))
            memory_utilization = max(0, min(100, base_memory + np.random.normal(0, 10)))
            
            history.append({
                'timestamp': timestamp,
                'cpu_percent': cpu_utilization,
                'memory_percent': memory_utilization,
                'network_io_mbps': np.random.normal(10, 5),
                'disk_io_mbps': np.random.normal(5, 2)
            })
        
        return history
    
    async def _analyze_underutilized_resource(self, resource: InfrastructureResource, 
                                           utilization_history: List[Dict[str, Any]]) -> Optional[CostOptimizationRecommendation]:
        """Analyze for underutilized resources."""
        if not utilization_history:
            return None
        
        avg_cpu = np.mean([u['cpu_percent'] for u in utilization_history])
        avg_memory = np.mean([u['memory_percent'] for u in utilization_history])
        
        rules = self.optimization_rules['underutilized_resources']
        
        if avg_cpu < rules['cpu_threshold'] and avg_memory < rules['memory_threshold']:
            # Calculate potential savings
            current_monthly_cost = resource.cost_per_hour * 24 * 30
            
            # Suggest downsizing to 70% of current capacity
            new_cost_per_hour = resource.cost_per_hour * 0.7
            projected_monthly_cost = new_cost_per_hour * 24 * 30
            potential_savings = current_monthly_cost - projected_monthly_cost
            
            return CostOptimizationRecommendation(
                recommendation_id=f"underutil_{resource.resource_id}",
                resource_id=resource.resource_id,
                recommendation_type="downsize_underutilized",
                current_monthly_cost=current_monthly_cost,
                projected_monthly_cost=projected_monthly_cost,
                potential_savings=potential_savings,
                action_required="Downsize resource by 30%",
                implementation_effort="medium",
                risk_level="low",
                description=f"Resource consistently under {rules['cpu_threshold']}% CPU and {rules['memory_threshold']}% memory utilization",
                justification=f"Average utilization: CPU {avg_cpu:.1f}%, Memory {avg_memory:.1f}%"
            )
        
        return None
    
    async def _analyze_oversized_resource(self, resource: InfrastructureResource, 
                                        utilization_history: List[Dict[str, Any]]) -> Optional[CostOptimizationRecommendation]:
        """Analyze for oversized resources."""
        if not utilization_history:
            return None
        
        rules = self.optimization_rules['oversized_resources']
        
        # Calculate frequency of high utilization
        high_cpu_count = sum(1 for u in utilization_history if u['cpu_percent'] > rules['cpu_threshold'])
        high_memory_count = sum(1 for u in utilization_history if u['memory_percent'] > rules['memory_threshold'])
        
        high_cpu_frequency = high_cpu_count / len(utilization_history)
        high_memory_frequency = high_memory_count / len(utilization_history)
        
        if high_cpu_frequency > rules['frequency_threshold'] or high_memory_frequency > rules['frequency_threshold']:
            # Calculate potential costs for upsizing
            current_monthly_cost = resource.cost_per_hour * 24 * 30
            
            # Suggest upsizing by 50%
            new_cost_per_hour = resource.cost_per_hour * 1.5
            projected_monthly_cost = new_cost_per_hour * 24 * 30
            potential_savings = -(projected_monthly_cost - current_monthly_cost)  # Negative savings (additional cost)
            
            return CostOptimizationRecommendation(
                recommendation_id=f"oversized_{resource.resource_id}",
                resource_id=resource.resource_id,
                recommendation_type="upsize_oversized",
                current_monthly_cost=current_monthly_cost,
                projected_monthly_cost=projected_monthly_cost,
                potential_savings=potential_savings,
                action_required="Upsize resource by 50%",
                implementation_effort="medium",
                risk_level="medium",
                description=f"Resource frequently exceeds capacity thresholds",
                justification=f"High utilization frequency: CPU {high_cpu_frequency:.1%}, Memory {high_memory_frequency:.1%}"
            )
        
        return None
    
    async def _analyze_unused_resource(self, resource: InfrastructureResource, 
                                     utilization_history: List[Dict[str, Any]]) -> Optional[CostOptimizationRecommendation]:
        """Analyze for unused resources."""
        if not utilization_history:
            return None
        
        rules = self.optimization_rules['unused_resources']
        
        avg_cpu = np.mean([u['cpu_percent'] for u in utilization_history])
        avg_network = np.mean([u['network_io_mbps'] for u in utilization_history])
        
        if avg_cpu < rules['cpu_threshold'] and avg_network < rules['network_threshold']:
            current_monthly_cost = resource.cost_per_hour * 24 * 30
            
            return CostOptimizationRecommendation(
                recommendation_id=f"unused_{resource.resource_id}",
                resource_id=resource.resource_id,
                recommendation_type="terminate_unused",
                current_monthly_cost=current_monthly_cost,
                projected_monthly_cost=0.0,
                potential_savings=current_monthly_cost,
                action_required="Terminate unused resource",
                implementation_effort="low",
                risk_level="low",
                description="Resource appears to be unused based on minimal activity",
                justification=f"Very low utilization: CPU {avg_cpu:.1f}%, Network {avg_network:.1f} Mbps"
            )
        
        return None
    
    async def _analyze_rightsizing_opportunity(self, resource: InfrastructureResource, 
                                             utilization_history: List[Dict[str, Any]]) -> Optional[CostOptimizationRecommendation]:
        """Analyze rightsizing opportunities."""
        if not utilization_history:
            return None
        
        # Calculate optimal sizing based on 95th percentile usage
        cpu_values = [u['cpu_percent'] for u in utilization_history]
        memory_values = [u['memory_percent'] for u in utilization_history]
        
        cpu_95th = np.percentile(cpu_values, 95)
        memory_95th = np.percentile(memory_values, 95)
        
        # Suggest rightsizing if current capacity is significantly different from optimal
        optimal_cpu_ratio = cpu_95th / 80  # Target 80% utilization at peak
        optimal_memory_ratio = memory_95th / 80
        
        optimal_ratio = max(optimal_cpu_ratio, optimal_memory_ratio)
        
        if optimal_ratio < 0.7 or optimal_ratio > 1.3:  # More than 30% difference
            current_monthly_cost = resource.cost_per_hour * 24 * 30
            new_cost_per_hour = resource.cost_per_hour * optimal_ratio
            projected_monthly_cost = new_cost_per_hour * 24 * 30
            potential_savings = current_monthly_cost - projected_monthly_cost
            
            action = "Upsize" if optimal_ratio > 1 else "Downsize"
            
            return CostOptimizationRecommendation(
                recommendation_id=f"rightsize_{resource.resource_id}",
                resource_id=resource.resource_id,
                recommendation_type="rightsize_resource",
                current_monthly_cost=current_monthly_cost,
                projected_monthly_cost=projected_monthly_cost,
                potential_savings=potential_savings,
                action_required=f"{action} resource to optimal capacity",
                implementation_effort="medium",
                risk_level="low",
                description=f"Rightsize resource based on 95th percentile utilization",
                justification=f"Optimal sizing ratio: {optimal_ratio:.2f} (CPU 95th: {cpu_95th:.1f}%, Memory 95th: {memory_95th:.1f}%)"
            )
        
        return None
    
    async def implement_cost_optimization(self, recommendation: CostOptimizationRecommendation) -> bool:
        """Implement cost optimization recommendation."""
        try:
            resource_id = recommendation.resource_id
            
            if recommendation.recommendation_type == "downsize_underutilized":
                success = await self.resource_manager.scale_resource(
                    resource_id, ScalingAction.SCALE_DOWN, 0.7
                )
            elif recommendation.recommendation_type == "upsize_oversized":
                success = await self.resource_manager.scale_resource(
                    resource_id, ScalingAction.SCALE_UP, 1.5
                )
            elif recommendation.recommendation_type == "terminate_unused":
                success = await self.resource_manager.terminate_resource(resource_id)
            elif recommendation.recommendation_type == "rightsize_resource":
                # Calculate rightsizing factor from recommendation
                scaling_factor = recommendation.projected_monthly_cost / recommendation.current_monthly_cost
                scaling_action = ScalingAction.SCALE_UP if scaling_factor > 1 else ScalingAction.SCALE_DOWN
                success = await self.resource_manager.scale_resource(
                    resource_id, scaling_action, abs(scaling_factor)
                )
            else:
                logger.warning(f"Unknown optimization type: {recommendation.recommendation_type}")
                return False
            
            if success:
                self.optimization_history.append(recommendation)
                logger.info(f"Implemented cost optimization: {recommendation.recommendation_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to implement cost optimization: {e}")
            return False


class InfrastructureAutoManagementSystem:
    """Main infrastructure auto management and scaling system."""
    
    def __init__(self, sdk: MobileERPSDK):
        self.sdk = sdk
        self.resource_manager = CloudResourceManager()
        self.auto_scaler = AutoScalingEngine(self.resource_manager)
        self.cost_optimizer = CostOptimizer(self.resource_manager)
        
        # System configuration
        self.management_enabled = True
        self.auto_scaling_enabled = True
        self.cost_optimization_enabled = True
        
        # Monitoring intervals
        self.scaling_check_interval = 300  # 5 minutes
        self.cost_optimization_interval = 86400  # 24 hours
        self.resource_discovery_interval = 3600  # 1 hour
        
        # System metrics
        self.metrics = {
            'total_resources': 0,
            'active_resources': 0,
            'total_scaling_actions': 0,
            'successful_scaling_actions': 0,
            'total_cost_optimizations': 0,
            'cost_savings_achieved': 0.0,
            'average_resource_utilization': 0.0,
            'infrastructure_efficiency_score': 0.0
        }
    
    async def start_management_system(self):
        """Start the infrastructure auto management system."""
        logger.info("Starting Infrastructure Auto Management & Scaling System")
        
        # Discover existing resources
        await self._discover_all_resources()
        
        # Start background management tasks
        tasks = [
            asyncio.create_task(self._auto_scaling_loop()),
            asyncio.create_task(self._cost_optimization_loop()),
            asyncio.create_task(self._resource_discovery_loop()),
            asyncio.create_task(self._metrics_update_loop()),
            asyncio.create_task(self._health_monitoring_loop())
        ]
        
        await asyncio.gather(*tasks)
    
    async def _discover_all_resources(self):
        """Discover resources across all configured cloud providers."""
        try:
            # Discover AWS resources
            aws_resources = await self.resource_manager.discover_resources(CloudProvider.AWS)
            logger.info(f"Discovered {len(aws_resources)} AWS resources")
            
            # Discover other cloud providers
            # azure_resources = await self.resource_manager.discover_resources(CloudProvider.AZURE)
            # gcp_resources = await self.resource_manager.discover_resources(CloudProvider.GCP)
            
            # Update metrics
            self.metrics['total_resources'] = len(self.resource_manager.resources)
            self.metrics['active_resources'] = len([r for r in self.resource_manager.resources.values() 
                                                  if r.status == ResourceStatus.RUNNING])
            
        except Exception as e:
            logger.error(f"Error during resource discovery: {e}")
    
    async def _auto_scaling_loop(self):
        """Auto-scaling management loop."""
        while self.management_enabled and self.auto_scaling_enabled:
            try:
                # Evaluate scaling needs
                scaling_decisions = await self.auto_scaler.evaluate_scaling_needs()
                
                # Execute scaling decisions
                for decision in scaling_decisions:
                    success = await self.auto_scaler.execute_scaling_decision(decision)
                    
                    self.metrics['total_scaling_actions'] += 1
                    if success:
                        self.metrics['successful_scaling_actions'] += 1
                
                if scaling_decisions:
                    logger.info(f"Processed {len(scaling_decisions)} scaling decisions")
                
                await asyncio.sleep(self.scaling_check_interval)
                
            except Exception as e:
                logger.error(f"Error in auto-scaling loop: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    async def _cost_optimization_loop(self):
        """Cost optimization management loop."""
        while self.management_enabled and self.cost_optimization_enabled:
            try:
                # Analyze cost optimization opportunities
                recommendations = await self.cost_optimizer.analyze_cost_optimization_opportunities()
                
                # Implement low-risk, high-impact optimizations automatically
                for recommendation in recommendations[:3]:  # Top 3 recommendations
                    if (recommendation.risk_level == "low" and 
                        recommendation.potential_savings > 50):  # $50+ savings
                        
                        success = await self.cost_optimizer.implement_cost_optimization(recommendation)
                        
                        self.metrics['total_cost_optimizations'] += 1
                        if success:
                            self.metrics['cost_savings_achieved'] += recommendation.potential_savings
                
                if recommendations:
                    logger.info(f"Analyzed {len(recommendations)} cost optimization opportunities")
                
                await asyncio.sleep(self.cost_optimization_interval)
                
            except Exception as e:
                logger.error(f"Error in cost optimization loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _resource_discovery_loop(self):
        """Resource discovery loop."""
        while self.management_enabled:
            try:
                await self._discover_all_resources()
                await asyncio.sleep(self.resource_discovery_interval)
                
            except Exception as e:
                logger.error(f"Error in resource discovery loop: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _metrics_update_loop(self):
        """Update system metrics continuously."""
        while self.management_enabled:
            try:
                # Calculate average resource utilization
                if self.resource_manager.resources:
                    total_cpu_util = 0
                    total_memory_util = 0
                    active_resources = 0
                    
                    for resource in self.resource_manager.resources.values():
                        if resource.status == ResourceStatus.RUNNING:
                            total_cpu_util += resource.avg_cpu_utilization
                            total_memory_util += resource.avg_memory_utilization
                            active_resources += 1
                    
                    if active_resources > 0:
                        avg_cpu = total_cpu_util / active_resources
                        avg_memory = total_memory_util / active_resources
                        self.metrics['average_resource_utilization'] = (avg_cpu + avg_memory) / 2
                
                # Calculate infrastructure efficiency score
                if self.metrics['total_scaling_actions'] > 0:
                    scaling_success_rate = (self.metrics['successful_scaling_actions'] / 
                                          self.metrics['total_scaling_actions'])
                else:
                    scaling_success_rate = 1.0
                
                utilization_score = min(100, self.metrics['average_resource_utilization'])
                cost_efficiency = min(100, self.metrics['cost_savings_achieved'] / 1000)  # Normalize
                
                self.metrics['infrastructure_efficiency_score'] = (
                    scaling_success_rate * 40 + 
                    utilization_score * 0.4 + 
                    cost_efficiency * 0.2
                )
                
                await asyncio.sleep(600)  # Update every 10 minutes
                
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(1200)
    
    async def _health_monitoring_loop(self):
        """Monitor infrastructure health."""
        while self.management_enabled:
            try:
                # Check resource health
                unhealthy_resources = []
                
                for resource_id, resource in self.resource_manager.resources.items():
                    if resource.status in [ResourceStatus.FAILED, ResourceStatus.TERMINATING]:
                        unhealthy_resources.append(resource_id)
                
                if unhealthy_resources:
                    logger.warning(f"Unhealthy resources detected: {unhealthy_resources}")
                    # Could trigger automatic remediation here
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(600)
    
    async def create_infrastructure_resource(self, resource_spec: Dict[str, Any]) -> InfrastructureResource:
        """Create new infrastructure resource."""
        return await self.resource_manager.create_resource(resource_spec)
    
    async def scale_resource_manually(self, resource_id: str, scaling_action: ScalingAction, 
                                    scaling_factor: float = 1.5) -> bool:
        """Manually scale infrastructure resource."""
        return await self.resource_manager.scale_resource(resource_id, scaling_action, scaling_factor)
    
    async def get_cost_optimization_recommendations(self) -> List[CostOptimizationRecommendation]:
        """Get current cost optimization recommendations."""
        return await self.cost_optimizer.analyze_cost_optimization_opportunities()
    
    async def implement_recommendation(self, recommendation_id: str) -> bool:
        """Implement specific cost optimization recommendation."""
        recommendations = await self.cost_optimizer.analyze_cost_optimization_opportunities()
        
        for recommendation in recommendations:
            if recommendation.recommendation_id == recommendation_id:
                return await self.cost_optimizer.implement_cost_optimization(recommendation)
        
        return False
    
    def get_management_report(self) -> Dict[str, Any]:
        """Get comprehensive infrastructure management report."""
        # Calculate resource distribution
        resource_by_type = {}
        resource_by_provider = {}
        resource_by_status = {}
        
        for resource in self.resource_manager.resources.values():
            # By type
            type_name = resource.resource_type.value
            resource_by_type[type_name] = resource_by_type.get(type_name, 0) + 1
            
            # By provider
            provider_name = resource.cloud_provider.value
            resource_by_provider[provider_name] = resource_by_provider.get(provider_name, 0) + 1
            
            # By status
            status_name = resource.status.value
            resource_by_status[status_name] = resource_by_status.get(status_name, 0) + 1
        
        # Calculate total monthly cost
        total_monthly_cost = sum(
            resource.cost_per_hour * 24 * 30 
            for resource in self.resource_manager.resources.values()
        )
        
        return {
            "system_metrics": self.metrics,
            "resource_summary": {
                "total_resources": len(self.resource_manager.resources),
                "by_type": resource_by_type,
                "by_provider": resource_by_provider,
                "by_status": resource_by_status,
                "total_monthly_cost": total_monthly_cost
            },
            "scaling_summary": {
                "recent_scaling_actions": len(self.auto_scaler.scaling_history[-10:]),
                "scaling_rules_active": len([r for r in self.auto_scaler.scaling_rules.values() if r.enabled]),
                "predictive_scaling_enabled": self.auto_scaler.is_trained
            },
            "cost_optimization": {
                "total_optimizations": len(self.cost_optimizer.optimization_history),
                "total_savings": sum(opt.potential_savings for opt in self.cost_optimizer.optimization_history),
                "last_optimization": (
                    self.cost_optimizer.optimization_history[-1].recommendation_id 
                    if self.cost_optimizer.optimization_history else None
                )
            },
            "recent_activities": {
                "resource_changes": self.resource_manager.resource_history[-10:],
                "scaling_actions": self.auto_scaler.scaling_history[-10:],
                "cost_optimizations": [
                    {
                        "recommendation_id": opt.recommendation_id,
                        "resource_id": opt.resource_id,
                        "savings": opt.potential_savings,
                        "type": opt.recommendation_type
                    }
                    for opt in self.cost_optimizer.optimization_history[-5:]
                ]
            }
        }


# Example usage and integration
async def main():
    """Example usage of the Infrastructure Auto Management System."""
    # Initialize with mobile ERP SDK
    sdk = MobileERPSDK()
    
    # Create management system
    management_system = InfrastructureAutoManagementSystem(sdk)
    
    # Start management system
    await management_system.start_management_system()


if __name__ == "__main__":
    asyncio.run(main())