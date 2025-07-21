"""Advanced Business Intelligence & Analytics API endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.business_intelligence import (
    bi_engine,
    MetricDefinition,
    MetricType,
    AggregationMethod,
    ChartType,
    AlertSeverity,
    DashboardWidget,
    Dashboard,
    AlertRule,
    check_business_intelligence_health,
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class MetricDefinitionRequest(BaseModel):
    """Metric definition request schema."""
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    metric_type: MetricType
    source_table: str = Field(..., max_length=100)
    source_column: str = Field(..., max_length=100)
    aggregation_method: AggregationMethod
    filters: Optional[Dict[str, Any]] = {}
    group_by: Optional[List[str]] = []
    time_dimension: str = Field("created_at", max_length=100)
    custom_formula: Optional[str] = Field(None, max_length=500)
    unit: str = Field("", max_length=50)
    target_value: Optional[float] = None


class MetricDefinitionResponse(BaseModel):
    """Metric definition response schema."""
    id: str
    name: str
    description: str
    metric_type: str
    source_table: str
    source_column: str
    aggregation_method: str
    filters: Dict[str, Any]
    group_by: List[str]
    time_dimension: str
    custom_formula: Optional[str]
    unit: str
    target_value: Optional[float]

    class Config:
        from_attributes = True


class DashboardWidgetRequest(BaseModel):
    """Dashboard widget request schema."""
    title: str = Field(..., max_length=200)
    chart_type: ChartType
    metric_ids: List[str]
    position: Dict[str, int]  # x, y, width, height
    filters: Optional[Dict[str, Any]] = {}
    refresh_interval: int = Field(300, ge=60, le=3600)


class DashboardWidgetResponse(BaseModel):
    """Dashboard widget response schema."""
    id: str
    title: str
    chart_type: str
    metric_ids: List[str]
    position: Dict[str, int]
    filters: Dict[str, Any]
    refresh_interval: int

    class Config:
        from_attributes = True


class DashboardRequest(BaseModel):
    """Dashboard request schema."""
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    widgets: Optional[List[DashboardWidgetRequest]] = []
    shared_filters: Optional[Dict[str, Any]] = {}


class DashboardResponse(BaseModel):
    """Dashboard response schema."""
    id: str
    name: str
    description: str
    widgets: List[DashboardWidgetResponse]
    shared_filters: Dict[str, Any]
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertRuleRequest(BaseModel):
    """Alert rule request schema."""
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    metric_id: str = Field(..., max_length=100)
    condition: str = Field(..., max_length=200)
    severity: AlertSeverity
    notification_channels: Optional[List[str]] = []
    cooldown_minutes: int = Field(60, ge=5, le=1440)
    enabled: bool = True


class AlertRuleResponse(BaseModel):
    """Alert rule response schema."""
    id: str
    name: str
    description: str
    metric_id: str
    condition: str
    severity: str
    notification_channels: List[str]
    cooldown_minutes: int
    enabled: bool

    class Config:
        from_attributes = True


class AnalyticsRequest(BaseModel):
    """Analytics computation request schema."""
    metric_ids: List[str] = Field(..., min_items=1)
    start_date: datetime
    end_date: datetime
    tenant_id: Optional[str] = None


class ForecastRequest(BaseModel):
    """Forecast request schema."""
    metric_id: str = Field(..., max_length=100)
    forecast_periods: int = Field(30, ge=1, le=365)


class InsightResponse(BaseModel):
    """Business insight response schema."""
    type: str
    metric_id: str
    message: str
    impact: str
    recommendation: str


class AnalyticsResponse(BaseModel):
    """Analytics response schema."""
    metrics: Dict[str, Any]
    insights: List[InsightResponse]
    time_range: Dict[str, str]
    computed_at: str


class BIHealthResponse(BaseModel):
    """BI system health response schema."""
    status: str
    metrics_count: int
    dashboards_count: int
    alert_rules_count: int
    active_alerts: int
    cache_size: int
    processing_history: int
    last_updated: str


# Metric Management Endpoints
@router.post("/metrics", response_model=MetricDefinitionResponse)
async def create_metric(
    metric_request: MetricDefinitionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new business metric definition."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        metric = MetricDefinition(
            id="",  # Will be auto-generated
            name=metric_request.name,
            description=metric_request.description,
            metric_type=metric_request.metric_type,
            source_table=metric_request.source_table,
            source_column=metric_request.source_column,
            aggregation_method=metric_request.aggregation_method,
            filters=metric_request.filters or {},
            group_by=metric_request.group_by or [],
            time_dimension=metric_request.time_dimension,
            custom_formula=metric_request.custom_formula,
            unit=metric_request.unit,
            target_value=metric_request.target_value
        )
        
        metric_id = await bi_engine.register_metric(metric)
        registered_metric = await bi_engine.get_metric(metric_id)
        
        return MetricDefinitionResponse(
            id=registered_metric.id,
            name=registered_metric.name,
            description=registered_metric.description,
            metric_type=registered_metric.metric_type.value,
            source_table=registered_metric.source_table,
            source_column=registered_metric.source_column,
            aggregation_method=registered_metric.aggregation_method.value,
            filters=registered_metric.filters,
            group_by=registered_metric.group_by,
            time_dimension=registered_metric.time_dimension,
            custom_formula=registered_metric.custom_formula,
            unit=registered_metric.unit,
            target_value=registered_metric.target_value
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create metric: {str(e)}"
        )


@router.get("/metrics", response_model=List[MetricDefinitionResponse])
async def list_metrics(
    metric_type: Optional[MetricType] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List all business metrics, optionally filtered by type."""
    try:
        metrics = await bi_engine.list_metrics(metric_type)
        
        return [
            MetricDefinitionResponse(
                id=metric.id,
                name=metric.name,
                description=metric.description,
                metric_type=metric.metric_type.value,
                source_table=metric.source_table,
                source_column=metric.source_column,
                aggregation_method=metric.aggregation_method.value,
                filters=metric.filters,
                group_by=metric.group_by,
                time_dimension=metric.time_dimension,
                custom_formula=metric.custom_formula,
                unit=metric.unit,
                target_value=metric.target_value
            )
            for metric in metrics
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get("/metrics/{metric_id}", response_model=MetricDefinitionResponse)
async def get_metric(
    metric_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific metric definition."""
    try:
        metric = await bi_engine.get_metric(metric_id)
        
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found"
            )
        
        return MetricDefinitionResponse(
            id=metric.id,
            name=metric.name,
            description=metric.description,
            metric_type=metric.metric_type.value,
            source_table=metric.source_table,
            source_column=metric.source_column,
            aggregation_method=metric.aggregation_method.value,
            filters=metric.filters,
            group_by=metric.group_by,
            time_dimension=metric.time_dimension,
            custom_formula=metric.custom_formula,
            unit=metric.unit,
            target_value=metric.target_value
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metric: {str(e)}"
        )


# Dashboard Management Endpoints
@router.post("/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    dashboard_request: DashboardRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new BI dashboard."""
    try:
        # Convert widget requests to widget objects
        widgets = []
        for widget_req in dashboard_request.widgets or []:
            widget = DashboardWidget(
                id="",  # Will be auto-generated
                title=widget_req.title,
                chart_type=widget_req.chart_type,
                metric_ids=widget_req.metric_ids,
                position=widget_req.position,
                filters=widget_req.filters or {},
                refresh_interval=widget_req.refresh_interval
            )
            widgets.append(widget)
        
        dashboard = Dashboard(
            id="",  # Will be auto-generated
            name=dashboard_request.name,
            description=dashboard_request.description,
            widgets=widgets,
            shared_filters=dashboard_request.shared_filters or {},
            owner_id=str(current_user.id)
        )
        
        dashboard_id = await bi_engine.create_dashboard(dashboard)
        created_dashboard = await bi_engine.get_dashboard(dashboard_id)
        
        # Convert widgets to response format
        widget_responses = []
        for widget in created_dashboard.widgets:
            widget_responses.append(DashboardWidgetResponse(
                id=widget.id,
                title=widget.title,
                chart_type=widget.chart_type.value,
                metric_ids=widget.metric_ids,
                position=widget.position,
                filters=widget.filters,
                refresh_interval=widget.refresh_interval
            ))
        
        return DashboardResponse(
            id=created_dashboard.id,
            name=created_dashboard.name,
            description=created_dashboard.description,
            widgets=widget_responses,
            shared_filters=created_dashboard.shared_filters,
            owner_id=created_dashboard.owner_id,
            created_at=created_dashboard.created_at,
            updated_at=created_dashboard.updated_at
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard: {str(e)}"
        )


@router.get("/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_user)
):
    """List all dashboards."""
    try:
        dashboards = await bi_engine.list_dashboards()
        
        dashboard_responses = []
        for dashboard in dashboards:
            # Convert widgets to response format
            widget_responses = []
            for widget in dashboard.widgets:
                widget_responses.append(DashboardWidgetResponse(
                    id=widget.id,
                    title=widget.title,
                    chart_type=widget.chart_type.value,
                    metric_ids=widget.metric_ids,
                    position=widget.position,
                    filters=widget.filters,
                    refresh_interval=widget.refresh_interval
                ))
            
            dashboard_responses.append(DashboardResponse(
                id=dashboard.id,
                name=dashboard.name,
                description=dashboard.description,
                widgets=widget_responses,
                shared_filters=dashboard.shared_filters,
                owner_id=dashboard.owner_id,
                created_at=dashboard.created_at,
                updated_at=dashboard.updated_at
            ))
        
        return dashboard_responses
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboards: {str(e)}"
        )


@router.get("/dashboards/{dashboard_id}/data")
async def get_dashboard_data(
    dashboard_id: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_user)
):
    """Get data for dashboard widgets."""
    try:
        dashboard_data = await bi_engine.generate_dashboard_data(
            dashboard_id, start_date, end_date
        )
        
        if "error" in dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=dashboard_data["error"]
            )
        
        return dashboard_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard data: {str(e)}"
        )


# Analytics Endpoints
@router.post("/analytics", response_model=AnalyticsResponse)
async def compute_analytics(
    analytics_request: AnalyticsRequest,
    current_user: User = Depends(get_current_user)
):
    """Compute analytics for specified metrics."""
    try:
        analytics_result = await bi_engine.compute_analytics(
            metric_ids=analytics_request.metric_ids,
            start_date=analytics_request.start_date,
            end_date=analytics_request.end_date,
            tenant_id=analytics_request.tenant_id
        )
        
        # Convert insights to response format
        insight_responses = []
        for insight in analytics_result["insights"]:
            insight_responses.append(InsightResponse(
                type=insight["type"],
                metric_id=insight["metric_id"],
                message=insight["message"],
                impact=insight["impact"],
                recommendation=insight["recommendation"]
            ))
        
        return AnalyticsResponse(
            metrics=analytics_result["metrics"],
            insights=insight_responses,
            time_range=analytics_result["time_range"],
            computed_at=analytics_result["computed_at"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute analytics: {str(e)}"
        )


@router.post("/forecast")
async def generate_forecast(
    forecast_request: ForecastRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate forecast for a metric."""
    try:
        forecast_result = await bi_engine.generate_forecast(
            metric_id=forecast_request.metric_id,
            forecast_periods=forecast_request.forecast_periods
        )
        
        if "error" in forecast_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=forecast_result["error"]
            )
        
        return forecast_result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(e)}"
        )


# Alert Management Endpoints
@router.post("/alerts/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    alert_request: AlertRuleRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new alert rule."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        alert_rule = AlertRule(
            id="",  # Will be auto-generated
            name=alert_request.name,
            description=alert_request.description,
            metric_id=alert_request.metric_id,
            condition=alert_request.condition,
            severity=alert_request.severity,
            notification_channels=alert_request.notification_channels or [],
            cooldown_minutes=alert_request.cooldown_minutes,
            enabled=alert_request.enabled
        )
        
        rule_id = await bi_engine.create_alert_rule(alert_rule)
        created_rule = await bi_engine.get_alert_rule(rule_id)
        
        return AlertRuleResponse(
            id=created_rule.id,
            name=created_rule.name,
            description=created_rule.description,
            metric_id=created_rule.metric_id,
            condition=created_rule.condition,
            severity=created_rule.severity.value,
            notification_channels=created_rule.notification_channels,
            cooldown_minutes=created_rule.cooldown_minutes,
            enabled=created_rule.enabled
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert rule: {str(e)}"
        )


@router.get("/alerts/active")
async def get_active_alerts(
    current_user: User = Depends(get_current_user)
):
    """Get currently active alerts."""
    try:
        active_alerts = bi_engine.alert_processor.active_alerts
        
        alert_list = []
        for alert_id, alert in active_alerts.items():
            alert_list.append({
                "id": alert.id,
                "rule_id": alert.rule_id,
                "metric_id": alert.metric_id,
                "severity": alert.severity.value,
                "message": alert.message,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "triggered_at": alert.triggered_at.isoformat(),
                "acknowledged": alert.acknowledged
            })
        
        return {
            "active_alerts": alert_list,
            "total_count": len(alert_list),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active alerts: {str(e)}"
        )


# System Information Endpoints
@router.get("/system/metrics-types")
async def list_metric_types():
    """List available metric types."""
    return {
        "metric_types": [mt.value for mt in MetricType],
        "aggregation_methods": [am.value for am in AggregationMethod],
        "chart_types": [ct.value for ct in ChartType],
        "alert_severities": [as_.value for as_ in AlertSeverity]
    }


@router.get("/health", response_model=BIHealthResponse)
async def bi_health_check():
    """Check Business Intelligence system health."""
    try:
        health_info = await check_business_intelligence_health()
        
        return BIHealthResponse(
            status=health_info["status"],
            metrics_count=health_info["metrics_count"],
            dashboards_count=health_info["dashboards_count"],
            alert_rules_count=health_info["alert_rules_count"],
            active_alerts=health_info["active_alerts"],
            cache_size=health_info["cache_size"],
            processing_history=health_info["processing_history"],
            last_updated=health_info["last_updated"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"BI health check failed: {str(e)}"
        )