"""
Analytics System API Endpoints - CC02 v31.0 Phase 2

Comprehensive analytics API with:
- Multi-Dimensional Analytics & KPI Tracking
- Real-Time Data Processing & Aggregation
- Advanced Business Intelligence & Reporting
- Performance Metrics & Benchmarking
- Predictive Analytics & Forecasting
- Custom Dashboard & Visualization
- Data Mining & Machine Learning Integration
- Executive Analytics & Strategic Insights
- Operational Analytics & Process Optimization
- Compliance Analytics & Risk Management
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.analytics_v31 import analytics_service
from app.schemas.analytics_v31 import (
    # Data Source schemas
    AnalyticsDataSourceCreateRequest,
    AnalyticsDataSourceUpdateRequest,
    AnalyticsDataSourceResponse,
    DataSourceListResponse,
    DataSourceConnectionTestRequest,
    DataSourceSyncRequest,
    
    # Metric schemas
    AnalyticsMetricCreateRequest,
    AnalyticsMetricUpdateRequest,
    AnalyticsMetricResponse,
    MetricListResponse,
    MetricCalculationRequest,
    MetricComparisonRequest,
    
    # Data Point schemas
    AnalyticsDataPointCreateRequest,
    AnalyticsDataPointResponse,
    DataPointListResponse,
    DataPointQueryRequest,
    
    # Dashboard schemas
    AnalyticsDashboardCreateRequest,
    AnalyticsDashboardUpdateRequest,
    AnalyticsDashboardResponse,
    DashboardListResponse,
    DashboardExportRequest,
    
    # Report schemas
    AnalyticsReportCreateRequest,
    AnalyticsReportUpdateRequest,
    AnalyticsReportResponse,
    ReportListResponse,
    ReportGenerationRequest,
    ReportExecutionResponse,
    
    # Alert schemas
    AnalyticsAlertCreateRequest,
    AnalyticsAlertUpdateRequest,
    AnalyticsAlertResponse,
    AlertListResponse,
    AlertEvaluationRequest,
    
    # Prediction schemas
    AnalyticsPredictionCreateRequest,
    AnalyticsPredictionUpdateRequest,
    AnalyticsPredictionResponse,
    PredictionListResponse,
    PredictionTrainingRequest,
    
    # Insight schemas
    AnalyticsInsightResponse,
    InsightListResponse,
    InsightGenerationRequest,
    
    # Analytics schemas
    AnalyticsQueryRequest,
    AnalyticsQueryResponse,
    AnalyticsHealthResponse,
)

router = APIRouter()


# =============================================================================
# Data Source Management
# =============================================================================

@router.post("/data-sources", response_model=AnalyticsDataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    request: AnalyticsDataSourceCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new analytics data source."""
    try:
        data_source = await analytics_service.create_data_source(db, request.dict())
        return data_source
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create data source: {str(e)}")


@router.get("/data-sources", response_model=DataSourceListResponse)
async def list_data_sources(
    organization_id: str = Query(..., description="Organization ID"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List analytics data sources with filtering and pagination."""
    try:
        data_sources = await analytics_service.list_data_sources(
            db, organization_id, source_type, is_active, page, per_page
        )
        return data_sources
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list data sources: {str(e)}")


@router.get("/data-sources/{data_source_id}", response_model=AnalyticsDataSourceResponse)
async def get_data_source(
    data_source_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics data source."""
    try:
        data_source = await analytics_service.get_data_source(db, data_source_id)
        if not data_source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
        return data_source
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get data source: {str(e)}")


@router.put("/data-sources/{data_source_id}", response_model=AnalyticsDataSourceResponse)
async def update_data_source(
    data_source_id: str,
    request: AnalyticsDataSourceUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an analytics data source."""
    try:
        data_source = await analytics_service.update_data_source(db, data_source_id, request.dict(exclude_unset=True))
        if not data_source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
        return data_source
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update data source: {str(e)}")


@router.post("/data-sources/{data_source_id}/test-connection", response_model=Dict[str, Any])
async def test_data_source_connection(
    data_source_id: str,
    request: DataSourceConnectionTestRequest,
    db: Session = Depends(get_db)
):
    """Test connection to an analytics data source."""
    try:
        result = await analytics_service.test_data_source_connection(db, data_source_id, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to test connection: {str(e)}")


@router.post("/data-sources/{data_source_id}/sync", response_model=Dict[str, Any])
async def sync_data_source(
    data_source_id: str,
    request: DataSourceSyncRequest,
    db: Session = Depends(get_db)
):
    """Sync data from an analytics data source."""
    try:
        result = await analytics_service.sync_data_source(db, data_source_id, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync data source: {str(e)}")


# =============================================================================
# Metrics Management
# =============================================================================

@router.post("/metrics", response_model=AnalyticsMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(
    request: AnalyticsMetricCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new analytics metric."""
    try:
        metric = await analytics_service.create_metric(db, request.dict())
        return metric
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create metric: {str(e)}")


@router.get("/metrics", response_model=MetricListResponse)
async def list_metrics(
    organization_id: str = Query(..., description="Organization ID"),
    analytics_type: Optional[str] = Query(None, description="Filter by analytics type"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List analytics metrics with filtering and pagination."""
    try:
        metrics = await analytics_service.list_metrics(
            db, organization_id, analytics_type, metric_type, is_active, page, per_page
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list metrics: {str(e)}")


@router.get("/metrics/{metric_id}", response_model=AnalyticsMetricResponse)
async def get_metric(
    metric_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics metric."""
    try:
        metric = await analytics_service.get_metric(db, metric_id)
        if not metric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
        return metric
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get metric: {str(e)}")


@router.put("/metrics/{metric_id}", response_model=AnalyticsMetricResponse)
async def update_metric(
    metric_id: str,
    request: AnalyticsMetricUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an analytics metric."""
    try:
        metric = await analytics_service.update_metric(db, metric_id, request.dict(exclude_unset=True))
        if not metric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
        return metric
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update metric: {str(e)}")


@router.post("/metrics/{metric_id}/calculate", response_model=Dict[str, Any])
async def calculate_metric(
    metric_id: str,
    request: MetricCalculationRequest,
    db: Session = Depends(get_db)
):
    """Calculate metric value for a specific period."""
    try:
        result = await analytics_service.calculate_metric(db, metric_id, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to calculate metric: {str(e)}")


@router.post("/metrics/compare", response_model=Dict[str, Any])
async def compare_metrics(
    request: MetricComparisonRequest,
    db: Session = Depends(get_db)
):
    """Compare multiple metrics across different periods."""
    try:
        result = await analytics_service.compare_metrics(db, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to compare metrics: {str(e)}")


# =============================================================================
# Data Points Management
# =============================================================================

@router.post("/data-points", response_model=AnalyticsDataPointResponse, status_code=status.HTTP_201_CREATED)
async def create_data_point(
    request: AnalyticsDataPointCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new analytics data point."""
    try:
        data_point = await analytics_service.create_data_point(db, request.dict())
        return data_point
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create data point: {str(e)}")


@router.post("/data-points/query", response_model=DataPointListResponse)
async def query_data_points(
    request: DataPointQueryRequest,
    db: Session = Depends(get_db)
):
    """Query analytics data points with advanced filtering."""
    try:
        data_points = await analytics_service.query_data_points(db, request.dict())
        return data_points
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to query data points: {str(e)}")


@router.get("/data-points/{data_point_id}", response_model=AnalyticsDataPointResponse)
async def get_data_point(
    data_point_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics data point."""
    try:
        data_point = await analytics_service.get_data_point(db, data_point_id)
        if not data_point:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data point not found")
        return data_point
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get data point: {str(e)}")


# =============================================================================
# Dashboard Management
# =============================================================================

@router.post("/dashboards", response_model=AnalyticsDashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    request: AnalyticsDashboardCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new analytics dashboard."""
    try:
        dashboard = await analytics_service.create_dashboard(db, request.dict())
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create dashboard: {str(e)}")


@router.get("/dashboards", response_model=DashboardListResponse)
async def list_dashboards(
    organization_id: str = Query(..., description="Organization ID"),
    dashboard_type: Optional[str] = Query(None, description="Filter by dashboard type"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List analytics dashboards with filtering and pagination."""
    try:
        dashboards = await analytics_service.list_dashboards(
            db, organization_id, dashboard_type, is_public, is_active, page, per_page
        )
        return dashboards
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list dashboards: {str(e)}")


@router.get("/dashboards/{dashboard_id}", response_model=AnalyticsDashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics dashboard."""
    try:
        dashboard = await analytics_service.get_dashboard(db, dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get dashboard: {str(e)}")


@router.put("/dashboards/{dashboard_id}", response_model=AnalyticsDashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    request: AnalyticsDashboardUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an analytics dashboard."""
    try:
        dashboard = await analytics_service.update_dashboard(db, dashboard_id, request.dict(exclude_unset=True))
        if not dashboard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
        return dashboard
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update dashboard: {str(e)}")


@router.post("/dashboards/{dashboard_id}/export", response_model=Dict[str, Any])
async def export_dashboard(
    dashboard_id: str,
    request: DashboardExportRequest,
    db: Session = Depends(get_db)
):
    """Export dashboard to various formats."""
    try:
        result = await analytics_service.export_dashboard(db, dashboard_id, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export dashboard: {str(e)}")


# =============================================================================
# Report Management
# =============================================================================

@router.post("/reports", response_model=AnalyticsReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: AnalyticsReportCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new analytics report."""
    try:
        report = await analytics_service.create_report(db, request.dict())
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create report: {str(e)}")


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    organization_id: str = Query(..., description="Organization ID"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_scheduled: Optional[bool] = Query(None, description="Filter by scheduled status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List analytics reports with filtering and pagination."""
    try:
        reports = await analytics_service.list_reports(
            db, organization_id, report_type, status, is_scheduled, page, per_page
        )
        return reports
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list reports: {str(e)}")


@router.get("/reports/{report_id}", response_model=AnalyticsReportResponse)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics report."""
    try:
        report = await analytics_service.get_report(db, report_id)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get report: {str(e)}")


@router.put("/reports/{report_id}", response_model=AnalyticsReportResponse)
async def update_report(
    report_id: str,
    request: AnalyticsReportUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an analytics report."""
    try:
        report = await analytics_service.update_report(db, report_id, request.dict(exclude_unset=True))
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return report
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update report: {str(e)}")


@router.post("/reports/{report_id}/generate", response_model=ReportExecutionResponse)
async def generate_report(
    report_id: str,
    request: ReportGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate analytics report execution."""
    try:
        execution = await analytics_service.generate_report(db, report_id, request.dict())
        return execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate report: {str(e)}")


@router.get("/reports/{report_id}/executions", response_model=List[ReportExecutionResponse])
async def list_report_executions(
    report_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List executions for a specific report."""
    try:
        executions = await analytics_service.list_report_executions(db, report_id, page, per_page)
        return executions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list report executions: {str(e)}")


# =============================================================================
# Alert Management
# =============================================================================

@router.post("/alerts", response_model=AnalyticsAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    request: AnalyticsAlertCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new analytics alert."""
    try:
        alert = await analytics_service.create_alert(db, request.dict())
        return alert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create alert: {str(e)}")


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    organization_id: str = Query(..., description="Organization ID"),
    metric_id: Optional[str] = Query(None, description="Filter by metric ID"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_triggered: Optional[bool] = Query(None, description="Filter by triggered status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List analytics alerts with filtering and pagination."""
    try:
        alerts = await analytics_service.list_alerts(
            db, organization_id, metric_id, priority, is_active, is_triggered, page, per_page
        )
        return alerts
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list alerts: {str(e)}")


@router.get("/alerts/{alert_id}", response_model=AnalyticsAlertResponse)
async def get_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics alert."""
    try:
        alert = await analytics_service.get_alert(db, alert_id)
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get alert: {str(e)}")


@router.put("/alerts/{alert_id}", response_model=AnalyticsAlertResponse)
async def update_alert(
    alert_id: str,
    request: AnalyticsAlertUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an analytics alert."""
    try:
        alert = await analytics_service.update_alert(db, alert_id, request.dict(exclude_unset=True))
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        return alert
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update alert: {str(e)}")


@router.post("/alerts/{alert_id}/evaluate", response_model=Dict[str, Any])
async def evaluate_alert(
    alert_id: str,
    request: AlertEvaluationRequest,
    db: Session = Depends(get_db)
):
    """Evaluate alert conditions."""
    try:
        result = await analytics_service.evaluate_alert(db, alert_id, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to evaluate alert: {str(e)}")


# =============================================================================
# Prediction Management
# =============================================================================

@router.post("/predictions", response_model=AnalyticsPredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    request: AnalyticsPredictionCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new analytics prediction model."""
    try:
        prediction = await analytics_service.create_prediction(db, request.dict())
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create prediction: {str(e)}")


@router.get("/predictions", response_model=PredictionListResponse)
async def list_predictions(
    organization_id: str = Query(..., description="Organization ID"),
    prediction_type: Optional[str] = Query(None, description="Filter by prediction type"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List analytics predictions with filtering and pagination."""
    try:
        predictions = await analytics_service.list_predictions(
            db, organization_id, prediction_type, model_type, is_active, page, per_page
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list predictions: {str(e)}")


@router.get("/predictions/{prediction_id}", response_model=AnalyticsPredictionResponse)
async def get_prediction(
    prediction_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics prediction."""
    try:
        prediction = await analytics_service.get_prediction(db, prediction_id)
        if not prediction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
        return prediction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get prediction: {str(e)}")


@router.put("/predictions/{prediction_id}", response_model=AnalyticsPredictionResponse)
async def update_prediction(
    prediction_id: str,
    request: AnalyticsPredictionUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an analytics prediction model."""
    try:
        prediction = await analytics_service.update_prediction(db, prediction_id, request.dict(exclude_unset=True))
        if not prediction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
        return prediction
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update prediction: {str(e)}")


@router.post("/predictions/{prediction_id}/train", response_model=Dict[str, Any])
async def train_prediction_model(
    prediction_id: str,
    request: PredictionTrainingRequest,
    db: Session = Depends(get_db)
):
    """Train analytics prediction model."""
    try:
        result = await analytics_service.train_prediction_model(db, prediction_id, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to train prediction model: {str(e)}")


@router.get("/predictions/{prediction_id}/forecast", response_model=Dict[str, Any])
async def get_prediction_forecast(
    prediction_id: str,
    days_ahead: int = Query(30, ge=1, le=365, description="Days to forecast"),
    db: Session = Depends(get_db)
):
    """Get forecast from analytics prediction model."""
    try:
        result = await analytics_service.get_prediction_forecast(db, prediction_id, days_ahead)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get prediction forecast: {str(e)}")


# =============================================================================
# Insight Management
# =============================================================================

@router.get("/insights", response_model=InsightListResponse)
async def list_insights(
    organization_id: str = Query(..., description="Organization ID"),
    insight_type: Optional[str] = Query(None, description="Filter by insight type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority_min: Optional[float] = Query(None, description="Minimum priority score"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List analytics insights with filtering and pagination."""
    try:
        insights = await analytics_service.list_insights(
            db, organization_id, insight_type, status, priority_min, page, per_page
        )
        return insights
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list insights: {str(e)}")


@router.get("/insights/{insight_id}", response_model=AnalyticsInsightResponse)
async def get_insight(
    insight_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analytics insight."""
    try:
        insight = await analytics_service.get_insight(db, insight_id)
        if not insight:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
        return insight
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get insight: {str(e)}")


@router.post("/insights/generate", response_model=List[AnalyticsInsightResponse])
async def generate_insights(
    request: InsightGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate new analytics insights using AI."""
    try:
        insights = await analytics_service.generate_insights(db, request.dict())
        return insights
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate insights: {str(e)}")


@router.put("/insights/{insight_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_insight(
    insight_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Acknowledge an analytics insight."""
    try:
        result = await analytics_service.acknowledge_insight(db, insight_id, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to acknowledge insight: {str(e)}")


# =============================================================================
# Advanced Analytics
# =============================================================================

@router.post("/query", response_model=AnalyticsQueryResponse)
async def execute_analytics_query(
    request: AnalyticsQueryRequest,
    db: Session = Depends(get_db)
):
    """Execute advanced analytics query with custom SQL or aggregations."""
    try:
        result = await analytics_service.execute_analytics_query(db, request.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to execute analytics query: {str(e)}")


@router.get("/health", response_model=AnalyticsHealthResponse)
async def get_analytics_health(
    db: Session = Depends(get_db)
):
    """Get analytics system health and performance metrics."""
    try:
        health = await analytics_service.get_analytics_health(db)
        return health
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get analytics health: {str(e)}")


@router.delete("/data-sources/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    data_source_id: str,
    db: Session = Depends(get_db)
):
    """Delete an analytics data source."""
    try:
        success = await analytics_service.delete_data_source(db, data_source_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete data source: {str(e)}")


@router.delete("/metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metric_id: str,
    db: Session = Depends(get_db)
):
    """Delete an analytics metric."""
    try:
        success = await analytics_service.delete_metric(db, metric_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete metric: {str(e)}")


@router.delete("/dashboards/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    db: Session = Depends(get_db)
):
    """Delete an analytics dashboard."""
    try:
        success = await analytics_service.delete_dashboard(db, dashboard_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete dashboard: {str(e)}")


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """Delete an analytics report."""
    try:
        success = await analytics_service.delete_report(db, report_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete report: {str(e)}")


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """Delete an analytics alert."""
    try:
        success = await analytics_service.delete_alert(db, alert_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete alert: {str(e)}")


@router.delete("/predictions/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prediction(
    prediction_id: str,
    db: Session = Depends(get_db)
):
    """Delete an analytics prediction model."""
    try:
        success = await analytics_service.delete_prediction(db, prediction_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete prediction: {str(e)}")