"""
CC02 v55.0 Performance Monitoring API
Advanced Performance Analytics and Optimization Management
Day 6 of 7-day intensive backend development
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.performance import PerformanceMetric
from app.models.user import User
from app.services.performance_optimizer import (
    AlertSeverity,
    MetricType,
    OptimizationType,
    performance_optimizer,
)

router = APIRouter(prefix="/performance", tags=["performance-monitoring"])


# Request/Response Models
class MetricRequest(BaseModel):
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class MetricResponse(BaseModel):
    id: UUID
    metric_type: MetricType
    value: float
    labels: Dict[str, str]
    metadata: Dict[str, Any]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class OptimizationRecommendationResponse(BaseModel):
    id: UUID
    optimization_type: OptimizationType
    priority: int
    description: str
    estimated_improvement: float
    implementation_cost: int
    affected_components: List[str]
    recommended_actions: List[str]
    is_applied: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    metric_type: MetricType
    threshold: float
    operator: str = Field(..., regex="^(>|<|>=|<=|==|!=)$")
    severity: AlertSeverity
    duration_seconds: int = Field(default=300, ge=60, le=3600)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)


class AlertRuleResponse(BaseModel):
    id: UUID
    name: str
    metric_type: MetricType
    threshold: float
    operator: str
    severity: AlertSeverity
    duration_seconds: int
    description: Optional[str]
    is_active: bool
    triggered_count: int
    last_triggered: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BenchmarkRequest(BaseModel):
    operation_name: str = Field(..., min_length=1, max_length=100)
    operation_type: str = Field(..., min_length=1, max_length=50)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    iterations: int = Field(default=1, ge=1, le=1000)


class BenchmarkResponse(BaseModel):
    operation_name: str
    operation_type: str
    iterations: int
    total_execution_time: float
    average_execution_time: float
    min_execution_time: float
    max_execution_time: float
    memory_usage_delta: int
    success_rate: float
    error_messages: List[str]
    benchmark_id: UUID
    executed_at: datetime

    class Config:
        from_attributes = True


class QueryProfileResponse(BaseModel):
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

    class Config:
        from_attributes = True


class SystemHealthResponse(BaseModel):
    overall_status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    database_connections: int
    api_response_time: float
    error_rate: float
    cache_hit_rate: float
    active_alerts: int
    pending_optimizations: int
    system_uptime: float
    last_updated: datetime

    class Config:
        from_attributes = True


# Metrics Management
@router.post(
    "/metrics", response_model=MetricResponse, status_code=status.HTTP_201_CREATED
)
async def create_metric(
    metric: MetricRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a performance metric"""

    timestamp = metric.timestamp or datetime.utcnow()

    db_metric = PerformanceMetric(
        id=uuid4(),
        metric_type=metric.metric_type,
        value=metric.value,
        labels=metric.labels,
        metadata=metric.metadata,
        timestamp=timestamp,
        created_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(db_metric)
    await db.commit()
    await db.refresh(db_metric)

    return MetricResponse(
        id=db_metric.id,
        metric_type=db_metric.metric_type,
        value=db_metric.value,
        labels=db_metric.labels,
        metadata=db_metric.metadata,
        timestamp=db_metric.timestamp,
        created_at=db_metric.created_at,
    )


@router.post("/metrics/batch")
async def create_metrics_batch(
    metrics: List[MetricRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create multiple performance metrics in batch"""

    if len(metrics) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 1000 metrics",
        )

    created_metrics = []

    for metric_request in metrics:
        timestamp = metric_request.timestamp or datetime.utcnow()

        db_metric = PerformanceMetric(
            id=uuid4(),
            metric_type=metric_request.metric_type,
            value=metric_request.value,
            labels=metric_request.labels,
            metadata=metric_request.metadata,
            timestamp=timestamp,
            created_at=datetime.utcnow(),
            created_by=current_user.id,
        )

        db.add(db_metric)
        created_metrics.append(db_metric.id)

    await db.commit()

    return {
        "created_count": len(created_metrics),
        "metric_ids": [str(mid) for mid in created_metrics],
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    metric_type: Optional[MetricType] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    labels: Optional[str] = Query(None, description="JSON string of label filters"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get performance metrics"""

    query = select(PerformanceMetric)

    if metric_type:
        query = query.where(PerformanceMetric.metric_type == metric_type)

    if start_time:
        query = query.where(PerformanceMetric.timestamp >= start_time)

    if end_time:
        query = query.where(PerformanceMetric.timestamp <= end_time)

    # TODO: Add label filtering

    query = query.offset(skip).limit(limit).order_by(PerformanceMetric.timestamp.desc())

    result = await db.execute(query)
    metrics = result.scalars().all()

    return [
        MetricResponse(
            id=metric.id,
            metric_type=metric.metric_type,
            value=metric.value,
            labels=metric.labels,
            metadata=metric.metadata,
            timestamp=metric.timestamp,
            created_at=metric.created_at,
        )
        for metric in metrics
    ]


@router.get("/metrics/summary")
async def get_metrics_summary(
    period_minutes: int = Query(60, ge=1, le=1440),
    metric_types: Optional[str] = Query(
        None, description="Comma-separated list of metric types"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get metrics summary for specified period"""

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=period_minutes)

    query = (
        select(
            PerformanceMetric.metric_type,
            func.count(PerformanceMetric.id).label("count"),
            func.avg(PerformanceMetric.value).label("average"),
            func.min(PerformanceMetric.value).label("minimum"),
            func.max(PerformanceMetric.value).label("maximum"),
            func.stddev(PerformanceMetric.value).label("std_dev"),
        )
        .where(
            and_(
                PerformanceMetric.timestamp >= start_time,
                PerformanceMetric.timestamp <= end_time,
            )
        )
        .group_by(PerformanceMetric.metric_type)
    )

    if metric_types:
        type_list = [MetricType(mt.strip()) for mt in metric_types.split(",")]
        query = query.where(PerformanceMetric.metric_type.in_(type_list))

    result = await db.execute(query)
    summaries = result.fetchall()

    return {
        "period": {
            "minutes": period_minutes,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
        "metrics": [
            {
                "metric_type": summary.metric_type.value,
                "count": summary.count,
                "average": float(summary.average) if summary.average else 0,
                "minimum": float(summary.minimum) if summary.minimum else 0,
                "maximum": float(summary.maximum) if summary.maximum else 0,
                "std_dev": float(summary.std_dev) if summary.std_dev else 0,
            }
            for summary in summaries
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }


# Optimization Recommendations
@router.get("/optimizations", response_model=List[OptimizationRecommendationResponse])
async def get_optimization_recommendations(
    optimization_type: Optional[OptimizationType] = Query(None),
    min_priority: int = Query(0, ge=0, le=10),
    applied: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
):
    """Get optimization recommendations"""

    recommendations = await performance_optimizer.get_recommendations(
        optimization_type=optimization_type,
        min_priority=min_priority,
        limit=limit + skip,
    )

    # Apply pagination
    paginated_recommendations = recommendations[skip : skip + limit]

    # Filter by applied status if specified
    if applied is not None:
        paginated_recommendations = [
            r
            for r in paginated_recommendations
            if (r.id in performance_optimizer.applied_optimizations) == applied
        ]

    return [
        OptimizationRecommendationResponse(
            id=rec.id,
            optimization_type=rec.optimization_type,
            priority=rec.priority,
            description=rec.description,
            estimated_improvement=rec.estimated_improvement,
            implementation_cost=rec.implementation_cost,
            affected_components=rec.affected_components,
            recommended_actions=rec.recommended_actions,
            is_applied=rec.id in performance_optimizer.applied_optimizations,
            created_at=rec.created_at,
        )
        for rec in paginated_recommendations
    ]


@router.post("/optimizations/{recommendation_id}/apply")
async def apply_optimization_recommendation(
    recommendation_id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
):
    """Apply optimization recommendation"""

    success = await performance_optimizer.apply_recommendation(recommendation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to apply optimization recommendation",
        )

    return {
        "recommendation_id": str(recommendation_id),
        "status": "applied",
        "message": "Optimization recommendation applied successfully",
        "applied_at": datetime.utcnow().isoformat(),
    }


# System Health and Status
@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(current_user: User = Depends(get_current_active_user)):
    """Get system health status"""

    # Get current metrics from performance optimizer
    summary = await performance_optimizer.get_performance_summary(period_minutes=5)

    # Extract health indicators
    metrics = summary.get("metrics", {})
    cpu_usage = metrics.get("cpu_usage", {}).get("current", 0)
    memory_usage = metrics.get("memory_usage", {}).get("current", 0)
    metrics.get("disk_io", {}).get("current", 0)
    network_io = metrics.get("network_io", {}).get("current", 0)

    # Determine overall health status
    overall_status = "healthy"

    if cpu_usage > 80 or memory_usage > 80:
        overall_status = "degraded"
    elif cpu_usage > 95 or memory_usage > 95:
        overall_status = "critical"

    active_alerts = len(summary.get("active_alerts", []))
    if active_alerts > 0:
        overall_status = "warning" if overall_status == "healthy" else overall_status

    return SystemHealthResponse(
        overall_status=overall_status,
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=0.0,  # Would implement disk usage monitoring
        network_io=network_io,
        database_connections=0,  # Would get from connection pool
        api_response_time=metrics.get("api_response_time", {}).get("current", 0),
        error_rate=metrics.get("error_rate", {}).get("current", 0),
        cache_hit_rate=metrics.get("cache_hit_rate", {}).get("current", 100),
        active_alerts=active_alerts,
        pending_optimizations=summary.get("total_recommendations", 0)
        - summary.get("applied_optimizations", 0),
        system_uptime=0.0,  # Would calculate from startup time
        last_updated=datetime.utcnow(),
    )


@router.get("/dashboard")
async def get_performance_dashboard(
    period_minutes: int = Query(60, ge=1, le=1440),
    current_user: User = Depends(get_current_active_user),
):
    """Get performance dashboard data"""

    summary = await performance_optimizer.get_performance_summary(period_minutes)

    # Get additional database statistics
    # TODO: Add database-specific metrics

    return {
        "period": {
            "minutes": period_minutes,
            "end_time": datetime.utcnow().isoformat(),
        },
        "system_metrics": summary.get("metrics", {}),
        "alerts": {
            "active_count": len(summary.get("active_alerts", [])),
            "active_alerts": summary.get("active_alerts", []),
        },
        "optimizations": {
            "total_recommendations": summary.get("total_recommendations", 0),
            "applied_count": summary.get("applied_optimizations", 0),
            "recent_recommendations": summary.get("recent_recommendations", []),
        },
        "optimizers": summary.get("optimizers_status", []),
        "generated_at": summary.get("generated_at"),
    }


# Benchmarking
@router.post("/benchmark", response_model=BenchmarkResponse)
async def create_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """Create and execute performance benchmark"""

    benchmark_id = uuid4()

    # Execute benchmark in background
    background_tasks.add_task(
        _execute_benchmark,
        benchmark_id,
        request.operation_name,
        request.operation_type,
        request.parameters,
        request.iterations,
    )

    return BenchmarkResponse(
        operation_name=request.operation_name,
        operation_type=request.operation_type,
        iterations=request.iterations,
        total_execution_time=0.0,
        average_execution_time=0.0,
        min_execution_time=0.0,
        max_execution_time=0.0,
        memory_usage_delta=0,
        success_rate=0.0,
        error_messages=[],
        benchmark_id=benchmark_id,
        executed_at=datetime.utcnow(),
    )


async def _execute_benchmark(
    benchmark_id: UUID,
    operation_name: str,
    operation_type: str,
    parameters: Dict[str, Any],
    iterations: int,
):
    """Execute benchmark in background"""

    execution_times = []
    memory_deltas = []
    errors = []

    for i in range(iterations):
        try:
            # Create a mock operation based on type
            if operation_type == "database_query":
                result = await _benchmark_database_operation(parameters)
            elif operation_type == "api_call":
                result = await _benchmark_api_operation(parameters)
            elif operation_type == "computation":
                result = await _benchmark_computation_operation(parameters)
            else:
                result = await _benchmark_generic_operation(parameters)

            execution_times.append(result["execution_time"])
            memory_deltas.append(result["memory_delta"])

        except Exception as e:
            errors.append(str(e))

    # Calculate statistics
    if execution_times:
        total_execution_time = sum(execution_times)
        average_execution_time = total_execution_time / len(execution_times)
        min(execution_times)
        max(execution_times)
        (len(execution_times) / iterations) * 100
        int(sum(memory_deltas) / len(memory_deltas)) if memory_deltas else 0
    else:
        total_execution_time = 0.0
        average_execution_time = 0.0

    # Store benchmark results
    # In production, would store in database
    logging.info(
        f"Benchmark {benchmark_id} completed: {average_execution_time:.3f}s avg"
    )


async def _benchmark_database_operation(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Benchmark database operation"""
    import time

    import psutil

    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss

    # Simulate database operation
    await asyncio.sleep(0.01)  # Simulate query execution

    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss

    return {
        "execution_time": end_time - start_time,
        "memory_delta": end_memory - start_memory,
    }


async def _benchmark_api_operation(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Benchmark API operation"""
    import time

    import psutil

    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss

    # Simulate API call
    await asyncio.sleep(0.05)  # Simulate network request

    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss

    return {
        "execution_time": end_time - start_time,
        "memory_delta": end_memory - start_memory,
    }


async def _benchmark_computation_operation(
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """Benchmark computation operation"""
    import time

    import psutil

    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss

    # Simulate computation
    sum(range(10000))  # Simple computation

    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss

    return {
        "execution_time": end_time - start_time,
        "memory_delta": end_memory - start_memory,
    }


async def _benchmark_generic_operation(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Benchmark generic operation"""
    import time

    import psutil

    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss

    # Simulate generic operation
    await asyncio.sleep(0.001)

    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss

    return {
        "execution_time": end_time - start_time,
        "memory_delta": end_memory - start_memory,
    }


# Query Performance Analysis
@router.get("/queries/profile", response_model=List[QueryProfileResponse])
async def get_query_profiles(
    min_execution_time: float = Query(0.0, ge=0.0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
):
    """Get SQL query performance profiles"""

    # Get query profiles from performance optimizer
    query_optimizer = next(
        (
            opt
            for opt in performance_optimizer.optimizers
            if opt.optimizer_id == "query_optimizer"
        ),
        None,
    )

    if not query_optimizer:
        return []

    profiles = []
    for query_hash, analysis in query_optimizer.query_profiles.items():
        if analysis.average_execution_time >= min_execution_time:
            profiles.append(
                QueryProfileResponse(
                    query_hash=analysis.query_hash,
                    query_text=analysis.query_text[:500] + "..."
                    if len(analysis.query_text) > 500
                    else analysis.query_text,
                    execution_count=analysis.execution_count,
                    total_execution_time=analysis.total_execution_time,
                    average_execution_time=analysis.average_execution_time,
                    max_execution_time=analysis.max_execution_time,
                    rows_affected=analysis.rows_affected,
                    tables_accessed=analysis.tables_accessed,
                    indexes_used=analysis.indexes_used,
                    optimization_opportunities=analysis.optimization_opportunities,
                )
            )

    # Sort by average execution time (descending)
    profiles.sort(key=lambda p: p.average_execution_time, reverse=True)

    return profiles[:limit]


# Real-time Metrics Streaming
@router.get("/metrics/stream")
async def stream_metrics(
    metric_types: Optional[str] = Query(
        None, description="Comma-separated list of metric types"
    ),
    interval_seconds: int = Query(5, ge=1, le=60),
    current_user: User = Depends(get_current_active_user),
):
    """Stream real-time performance metrics (Server-Sent Events)"""

    async def metric_generator() -> None:
        """Generate SSE metrics"""

        target_metrics = None
        if metric_types:
            target_metrics = [MetricType(mt.strip()) for mt in metric_types.split(",")]

        while True:
            try:
                # Collect current metrics
                current_metrics = (
                    await performance_optimizer.system_monitor.collect_metrics()
                )

                # Filter metrics if specified
                if target_metrics:
                    filtered_metrics = {
                        k: v
                        for k, v in current_metrics.metrics.items()
                        if k in target_metrics
                    }
                    current_metrics.metrics = filtered_metrics

                # Format as SSE
                metric_data = {
                    "timestamp": current_metrics.timestamp.isoformat(),
                    "metrics": {k.value: v for k, v in current_metrics.metrics.items()},
                    "labels": current_metrics.labels,
                }

                yield f"data: {json.dumps(metric_data)}\n\n"

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                error_data = {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                await asyncio.sleep(interval_seconds)

    return StreamingResponse(
        metric_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


# System Control
@router.post("/monitoring/start")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """Start performance monitoring system"""

    background_tasks.add_task(performance_optimizer.start_monitoring)

    return {
        "status": "started",
        "message": "Performance monitoring started",
        "started_at": datetime.utcnow().isoformat(),
    }


@router.get("/status")
async def get_monitoring_status(current_user: User = Depends(get_current_active_user)):
    """Get monitoring system status"""

    return {
        "monitoring_active": True,  # Would check actual status
        "optimizers_count": len(performance_optimizer.optimizers),
        "active_optimizers": [
            opt.optimizer_id for opt in performance_optimizer.optimizers if opt.enabled
        ],
        "metrics_collected": len(performance_optimizer.system_monitor.metrics_history),
        "recommendations_generated": len(performance_optimizer.optimization_history),
        "optimizations_applied": len(performance_optimizer.applied_optimizations),
        "status_checked_at": datetime.utcnow().isoformat(),
    }
