"""
CC02 v55.0 Scalability Management API
Horizontal and Vertical Scaling Management Interface
Day 6 of 7-day intensive backend development
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.scaling import ScalingEvent, ScalingPolicy
from app.models.user import User
from app.services.scalability_manager import (
    InstanceStatus,
    LoadBalancingStrategy,
    ScalingDirection,
    ScalingMetrics,
    ScalingTrigger,
    ScalingType,
    scalability_manager,
)

router = APIRouter(prefix="/scalability", tags=["scalability"])


# Request/Response Models
class ScalingMetricsRequest(BaseModel):
    cpu_utilization: float = Field(..., ge=0.0, le=100.0)
    memory_utilization: float = Field(..., ge=0.0, le=100.0)
    request_rate: float = Field(..., ge=0.0)
    response_time: float = Field(..., ge=0.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    queue_depth: int = Field(default=0, ge=0)
    active_connections: int = Field(default=0, ge=0)
    instance_count: int = Field(..., ge=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScalingDecisionResponse(BaseModel):
    decision_id: UUID
    scaling_type: ScalingType
    scaling_direction: ScalingDirection
    target_instances: Optional[int]
    target_resources: Dict[str, float]
    reason: str
    confidence: float
    estimated_cost: float
    estimated_completion_time_minutes: float
    prerequisites: List[str]
    risks: List[str]
    rollback_plan: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ScalingPolicyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    scaling_type: ScalingType
    trigger_type: ScalingTrigger
    conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: Dict[str, Any] = Field(default_factory=dict)
    cooldown_minutes: int = Field(default=5, ge=1, le=60)
    min_instances: int = Field(default=1, ge=1)
    max_instances: int = Field(default=10, ge=1)
    is_active: bool = Field(default=True)


class ScalingPolicyResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    scaling_type: ScalingType
    trigger_type: ScalingTrigger
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    cooldown_minutes: int
    min_instances: int
    max_instances: int
    is_active: bool
    triggered_count: int
    last_triggered: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstanceConfigRequest(BaseModel):
    instance_type: str = Field(..., min_length=1, max_length=50)
    cpu_cores: int = Field(..., ge=1, le=64)
    memory_gb: float = Field(..., ge=0.5, le=256.0)
    storage_gb: float = Field(..., ge=1.0, le=1000.0)
    network_bandwidth_mbps: float = Field(..., ge=1.0, le=10000.0)
    cost_per_hour: float = Field(..., ge=0.01, le=100.0)
    availability_zones: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InstanceConfigResponse(BaseModel):
    id: UUID
    instance_type: str
    cpu_cores: int
    memory_gb: float
    storage_gb: float
    network_bandwidth_mbps: float
    cost_per_hour: float
    availability_zones: List[str]
    metadata: Dict[str, Any]
    is_active: bool
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class LoadBalancerConfigRequest(BaseModel):
    strategy: LoadBalancingStrategy
    health_check_interval: int = Field(default=30, ge=10, le=300)
    health_check_timeout: int = Field(default=5, ge=1, le=30)
    connection_draining_timeout: int = Field(default=30, ge=10, le=300)
    sticky_sessions: bool = Field(default=False)
    ssl_termination: bool = Field(default=True)


class LoadBalancerStatusResponse(BaseModel):
    strategy: LoadBalancingStrategy
    total_instances: int
    healthy_instances: int
    unhealthy_instances: int
    total_connections: int
    average_response_time: float
    requests_per_minute: float
    health_check_interval: int
    last_health_check: datetime
    instances: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class CapacityPlanRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    time_horizon_days: int = Field(..., ge=7, le=365)
    expected_growth_rate: float = Field(..., ge=0.0, le=10.0)
    peak_factors: Dict[str, float] = Field(default_factory=dict)
    budget_constraints: Dict[str, float] = Field(default_factory=dict)


class CapacityPlanResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    time_horizon_days: int
    expected_growth_rate: float
    peak_factors: Dict[str, float]
    budget_constraints: Dict[str, float]
    projected_instances: List[int]
    projected_costs: List[float]
    recommendations: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScalingExecutionRequest(BaseModel):
    decision_id: UUID
    confirm_execution: bool = Field(default=False)
    override_safety_checks: bool = Field(default=False)
    execution_notes: Optional[str] = Field(None, max_length=500)


# Scaling Evaluation and Decision Making
@router.post("/evaluate", response_model=List[ScalingDecisionResponse])
async def evaluate_scaling(
    metrics: ScalingMetricsRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Evaluate scaling decisions based on current metrics"""

    scaling_metrics = ScalingMetrics(
        timestamp=datetime.utcnow(),
        cpu_utilization=metrics.cpu_utilization,
        memory_utilization=metrics.memory_utilization,
        request_rate=metrics.request_rate,
        response_time=metrics.response_time,
        error_rate=metrics.error_rate,
        queue_depth=metrics.queue_depth,
        active_connections=metrics.active_connections,
        instance_count=metrics.instance_count,
        metadata=metrics.metadata,
    )

    decisions = await scalability_manager.evaluate_scaling(scaling_metrics)

    return [
        ScalingDecisionResponse(
            decision_id=decision.decision_id,
            scaling_type=decision.scaling_type,
            scaling_direction=decision.scaling_direction,
            target_instances=decision.target_instances,
            target_resources={k.value: v for k, v in decision.target_resources.items()},
            reason=decision.reason,
            confidence=decision.confidence,
            estimated_cost=decision.estimated_cost,
            estimated_completion_time_minutes=decision.estimated_completion_time.total_seconds()
            / 60,
            prerequisites=decision.prerequisites,
            risks=decision.risks,
            rollback_plan=decision.rollback_plan,
            created_at=decision.created_at,
        )
        for decision in decisions
    ]


@router.post("/execute")
async def execute_scaling(
    request: ScalingExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """Execute scaling decision"""

    if not request.confirm_execution:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm execution to proceed",
        )

    # Find the decision
    decision = None
    for strategy in scalability_manager.strategies:
        # In production, would look up decision from database
        pass

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scaling decision not found"
        )

    # Execute scaling in background
    background_tasks.add_task(
        _execute_scaling_background, request.decision_id, request.execution_notes
    )

    return {
        "decision_id": str(request.decision_id),
        "status": "execution_started",
        "message": "Scaling execution initiated in background",
        "started_at": datetime.utcnow().isoformat(),
    }


async def _execute_scaling_background(decision_id: UUID, notes: Optional[str]) -> dict:
    """Execute scaling in background"""
    try:
        # In production, would retrieve decision and execute
        logging.info(f"Executing scaling decision {decision_id}")
        await asyncio.sleep(2)  # Simulate execution time
        logging.info(f"Scaling decision {decision_id} completed successfully")
    except Exception as e:
        logging.error(f"Scaling execution failed for {decision_id}: {e}")


# Scaling Policies Management
@router.post(
    "/policies",
    response_model=ScalingPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scaling_policy(
    policy: ScalingPolicyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create scaling policy"""

    # Validate conditions and actions
    if not policy.conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scaling conditions cannot be empty",
        )

    if not policy.actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scaling actions cannot be empty",
        )

    db_policy = ScalingPolicy(
        id=uuid4(),
        name=policy.name,
        description=policy.description,
        scaling_type=policy.scaling_type,
        trigger_type=policy.trigger_type,
        conditions=policy.conditions,
        actions=policy.actions,
        cooldown_minutes=policy.cooldown_minutes,
        min_instances=policy.min_instances,
        max_instances=policy.max_instances,
        is_active=policy.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)

    return ScalingPolicyResponse(
        id=db_policy.id,
        name=db_policy.name,
        description=db_policy.description,
        scaling_type=db_policy.scaling_type,
        trigger_type=db_policy.trigger_type,
        conditions=db_policy.conditions,
        actions=db_policy.actions,
        cooldown_minutes=db_policy.cooldown_minutes,
        min_instances=db_policy.min_instances,
        max_instances=db_policy.max_instances,
        is_active=db_policy.is_active,
        triggered_count=0,
        last_triggered=None,
        created_at=db_policy.created_at,
        updated_at=db_policy.updated_at,
    )


@router.get("/policies", response_model=List[ScalingPolicyResponse])
async def list_scaling_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    scaling_type: Optional[ScalingType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List scaling policies"""

    query = select(ScalingPolicy)

    if scaling_type:
        query = query.where(ScalingPolicy.scaling_type == scaling_type)

    if is_active is not None:
        query = query.where(ScalingPolicy.is_active == is_active)

    query = query.offset(skip).limit(limit).order_by(ScalingPolicy.created_at.desc())

    result = await db.execute(query)
    policies = result.scalars().all()

    return [
        ScalingPolicyResponse(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            scaling_type=policy.scaling_type,
            trigger_type=policy.trigger_type,
            conditions=policy.conditions,
            actions=policy.actions,
            cooldown_minutes=policy.cooldown_minutes,
            min_instances=policy.min_instances,
            max_instances=policy.max_instances,
            is_active=policy.is_active,
            triggered_count=0,  # Would calculate from scaling events
            last_triggered=None,  # Would get from scaling events
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )
        for policy in policies
    ]


@router.put("/policies/{policy_id}", response_model=ScalingPolicyResponse)
async def update_scaling_policy(
    policy_id: UUID = Path(...),
    policy_update: ScalingPolicyRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update scaling policy"""

    policy_result = await db.execute(
        select(ScalingPolicy).where(ScalingPolicy.id == policy_id)
    )
    policy = policy_result.scalar_one_or_none()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scaling policy not found"
        )

    # Update policy fields
    policy.name = policy_update.name
    policy.description = policy_update.description
    policy.scaling_type = policy_update.scaling_type
    policy.trigger_type = policy_update.trigger_type
    policy.conditions = policy_update.conditions
    policy.actions = policy_update.actions
    policy.cooldown_minutes = policy_update.cooldown_minutes
    policy.min_instances = policy_update.min_instances
    policy.max_instances = policy_update.max_instances
    policy.is_active = policy_update.is_active
    policy.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(policy)

    return ScalingPolicyResponse(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        scaling_type=policy.scaling_type,
        trigger_type=policy.trigger_type,
        conditions=policy.conditions,
        actions=policy.actions,
        cooldown_minutes=policy.cooldown_minutes,
        min_instances=policy.min_instances,
        max_instances=policy.max_instances,
        is_active=policy.is_active,
        triggered_count=0,
        last_triggered=None,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


# Load Balancer Management
@router.post("/load-balancer/config")
async def configure_load_balancer(
    config: LoadBalancerConfigRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Configure load balancer settings"""

    scalability_manager.load_balancer.strategy = config.strategy
    scalability_manager.load_balancer.health_check_interval = (
        config.health_check_interval
    )
    scalability_manager.load_balancer.health_check_timeout = config.health_check_timeout

    return {
        "status": "configured",
        "message": "Load balancer configuration updated",
        "strategy": config.strategy.value,
        "health_check_interval": config.health_check_interval,
        "configured_at": datetime.utcnow().isoformat(),
    }


@router.get("/load-balancer/status", response_model=LoadBalancerStatusResponse)
async def get_load_balancer_status(
    current_user: User = Depends(get_current_active_user),
):
    """Get load balancer status"""

    lb = scalability_manager.load_balancer
    instances = lb.instances

    healthy_instances = [i for i in instances if i["status"] == InstanceStatus.RUNNING]
    unhealthy_instances = [
        i for i in instances if i["status"] != InstanceStatus.RUNNING
    ]

    total_connections = sum(i["connections"] for i in instances)
    avg_response_time = (
        sum(i["response_time"] for i in instances) / len(instances)
        if instances
        else 0.0
    )

    return LoadBalancerStatusResponse(
        strategy=lb.strategy,
        total_instances=len(instances),
        healthy_instances=len(healthy_instances),
        unhealthy_instances=len(unhealthy_instances),
        total_connections=total_connections,
        average_response_time=avg_response_time,
        requests_per_minute=0.0,  # Would calculate from metrics
        health_check_interval=lb.health_check_interval,
        last_health_check=datetime.utcnow(),
        instances=[
            {
                "id": i["id"],
                "endpoint": i["endpoint"],
                "status": i["status"].value,
                "connections": i["connections"],
                "response_time": i["response_time"],
                "health_check_failures": i["health_check_failures"],
                "last_health_check": i["last_health_check"].isoformat()
                if i["last_health_check"]
                else None,
            }
            for i in instances
        ],
    )


@router.post("/load-balancer/instances/{instance_id}/remove")
async def remove_instance_from_load_balancer(
    instance_id: str = Path(...),
    graceful: bool = Query(default=True),
    current_user: User = Depends(get_current_active_user),
):
    """Remove instance from load balancer"""

    success = await scalability_manager.load_balancer.remove_instance(
        instance_id, graceful
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found in load balancer",
        )

    return {
        "instance_id": instance_id,
        "status": "removed",
        "graceful": graceful,
        "removed_at": datetime.utcnow().isoformat(),
    }


# Capacity Planning
@router.post(
    "/capacity-plan",
    response_model=CapacityPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_capacity_plan(
    plan: CapacityPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create capacity planning analysis"""

    # Generate capacity projections
    predictions = await scalability_manager.predict_capacity_needs(
        timedelta(days=plan.time_horizon_days)
    )

    # Create projected instances timeline
    projected_instances = []
    projected_costs = []
    current_instances = predictions.get("current_instances", 1)
    growth_factor = (1 + plan.expected_growth_rate / 100) ** (1 / 12)  # Monthly growth

    for month in range(plan.time_horizon_days // 30):
        instances = math.ceil(current_instances * (growth_factor**month))
        cost = instances * 50.0 * 24 * 30  # $50/hour/instance * 24h * 30 days
        projected_instances.append(instances)
        projected_costs.append(cost)

    # Generate recommendations
    recommendations = [
        f"Plan for up to {max(projected_instances)} instances",
        f"Budget ${sum(projected_costs):,.2f} over {plan.time_horizon_days} days",
        "Consider reserved instances for 20-30% cost savings",
        "Implement auto-scaling to optimize costs",
        "Monitor actual vs. projected growth monthly",
    ]

    return CapacityPlanResponse(
        id=uuid4(),
        name=plan.name,
        description=plan.description,
        time_horizon_days=plan.time_horizon_days,
        expected_growth_rate=plan.expected_growth_rate,
        peak_factors=plan.peak_factors,
        budget_constraints=plan.budget_constraints,
        projected_instances=projected_instances,
        projected_costs=projected_costs,
        recommendations=recommendations,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get("/capacity-plan/predict")
async def predict_capacity_requirements(
    time_horizon_days: int = Query(30, ge=7, le=365),
    growth_rate: float = Query(5.0, ge=0.0, le=50.0),
    current_user: User = Depends(get_current_active_user),
):
    """Predict capacity requirements"""

    predictions = await scalability_manager.predict_capacity_needs(
        timedelta(days=time_horizon_days)
    )

    return {
        "time_horizon_days": time_horizon_days,
        "predicted_instances": predictions.get("predicted_instances", 0),
        "growth_factor": predictions.get("growth_factor", 1.0),
        "estimated_cost": predictions.get("estimated_monthly_cost", 0.0),
        "recommendations": predictions.get("recommendations", []),
        "generated_at": predictions.get("generated_at", datetime.utcnow().isoformat()),
    }


# Scaling Metrics and Analytics
@router.get("/metrics")
async def get_scaling_metrics(
    period_hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_active_user),
):
    """Get scaling metrics and analytics"""

    metrics = await scalability_manager.get_scaling_metrics()

    return {
        "period_hours": period_hours,
        "current_status": {
            "instances": metrics.get("current_instances", 0),
            "healthy_instances": metrics.get("healthy_instances", 0),
            "load_balancing_strategy": metrics.get(
                "load_balancing_strategy", "round_robin"
            ),
            "autoscaling_enabled": metrics.get("autoscaling_enabled", False),
        },
        "scaling_activity": {
            "events_24h": metrics.get("scaling_events_24h", 0),
            "success_rate": metrics.get("scaling_success_rate", 0.0),
            "active_strategies": metrics.get("active_strategies", 0),
        },
        "current_metrics": metrics.get("current_metrics", {}),
        "generated_at": metrics.get("generated_at"),
    }


@router.get("/events")
async def get_scaling_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    scaling_type: Optional[ScalingType] = Query(None),
    success_only: Optional[bool] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get scaling events history"""

    query = select(ScalingEvent)

    if scaling_type:
        query = query.where(ScalingEvent.scaling_type == scaling_type)

    if success_only is not None:
        query = query.where(ScalingEvent.success == success_only)

    if start_date:
        query = query.where(ScalingEvent.created_at >= start_date)

    if end_date:
        query = query.where(ScalingEvent.created_at <= end_date)

    query = query.offset(skip).limit(limit).order_by(ScalingEvent.created_at.desc())

    result = await db.execute(query)
    events = result.scalars().all()

    return [
        {
            "id": str(event.id),
            "decision_id": str(event.decision_id),
            "scaling_type": event.scaling_type.value,
            "scaling_direction": event.scaling_direction.value,
            "target_instances": event.target_instances,
            "success": event.success,
            "error_message": event.error_message,
            "execution_time": event.execution_time,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


# System Control
@router.post("/autoscaling/enable")
async def enable_autoscaling(current_user: User = Depends(get_current_active_user)):
    """Enable automatic scaling"""

    scalability_manager.is_enabled = True

    return {
        "status": "enabled",
        "message": "Automatic scaling has been enabled",
        "enabled_at": datetime.utcnow().isoformat(),
    }


@router.post("/autoscaling/disable")
async def disable_autoscaling(current_user: User = Depends(get_current_active_user)):
    """Disable automatic scaling"""

    scalability_manager.is_enabled = False

    return {
        "status": "disabled",
        "message": "Automatic scaling has been disabled",
        "disabled_at": datetime.utcnow().isoformat(),
    }


@router.get("/health")
async def get_scalability_health(current_user: User = Depends(get_current_active_user)):
    """Get scalability system health"""

    metrics = await scalability_manager.get_scaling_metrics()

    # Determine health status
    health_status = "healthy"
    issues = []

    if metrics.get("healthy_instances", 0) < metrics.get("current_instances", 1):
        health_status = "degraded"
        issues.append("Some instances are unhealthy")

    if not metrics.get("autoscaling_enabled", False):
        issues.append("Autoscaling is disabled")

    if metrics.get("scaling_success_rate", 100) < 90:
        health_status = "degraded"
        issues.append("Low scaling success rate")

    return {
        "status": health_status,
        "issues": issues,
        "autoscaling_enabled": metrics.get("autoscaling_enabled", False),
        "current_instances": metrics.get("current_instances", 0),
        "healthy_instances": metrics.get("healthy_instances", 0),
        "load_balancer_strategy": metrics.get("load_balancing_strategy", "unknown"),
        "last_scaling_event": None,  # Would get from recent events
        "checked_at": datetime.utcnow().isoformat(),
    }
