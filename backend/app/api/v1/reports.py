"""Report management API endpoints for Phase 7 analytics functionality."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report import (
    ReportCreate,
    ReportDataResponse,
    ReportExecutionResponse,
    ReportResponse,
    ReportUpdate,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new report definition."""
    service = ReportService(db)
    report = await service.create_report(report_data)
    return report


@router.get("/", response_model=List[ReportResponse])
async def get_reports(
    organization_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get list of reports with optional filtering."""
    service = ReportService(db)
    reports = await service.get_reports(
        organization_id=organization_id,
        category=category,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get report by ID."""
    service = ReportService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int, report_data: ReportUpdate, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update report definition."""
    service = ReportService(db)
    report = await service.update_report(report_id, report_data)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}")
async def delete_report(
    report_id: int, db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete report (soft delete)."""
    service = ReportService(db)
    success = await service.delete_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted successfully"}


# Report Execution endpoints
@router.post("/{report_id}/execute", response_model=ReportExecutionResponse)
async def execute_report(
    report_id: int,
    parameters: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Execute a report with optional parameters."""
    service = ReportService(db)
    execution = await service.execute_report(
        report_id=report_id, parameters=parameters, background_tasks=background_tasks
    )
    return execution


@router.get("/{report_id}/executions", response_model=List[ReportExecutionResponse])
async def get_report_executions(
    report_id: int,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get report execution history."""
    service = ReportService(db)
    executions = await service.get_report_executions(
        report_id=report_id, status=status, skip=skip, limit=limit
    )
    return executions


@router.get("/executions/{execution_id}", response_model=ReportExecutionResponse)
async def get_report_execution(
    execution_id: int, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get report execution by ID."""
    service = ReportService(db)
    execution = await service.get_report_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Report execution not found")
    return execution


@router.get("/executions/{execution_id}/data", response_model=ReportDataResponse)
async def get_report_data(
    execution_id: int,
    format: str = Query("json", pattern="^(json|csv|excel)$"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get report execution data in specified format."""
    service = ReportService(db)
    data = await service.get_report_data(execution_id, format)
    if not data:
        raise HTTPException(status_code=404, detail="Report execution not found")
    return data


@router.get("/executions/{execution_id}/download")
async def download_report(
    execution_id: int,
    format: str = Query("excel", pattern="^(csv|excel|pdf)$"),
    db: Session = Depends(get_db),
):
    """Download report in specified format."""
    service = ReportService(db)
    file_response = await service.download_report(execution_id, format)
    if not file_response:
        raise HTTPException(status_code=404, detail="Report execution not found")
    return file_response


# Report Templates and Categories
@router.get("/templates/", response_model=List[Dict[str, Any]])
async def get_report_templates(
    category: Optional[str] = Query(None), db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get available report templates."""
    service = ReportService(db)
    templates = await service.get_report_templates(category)
    return templates


@router.get("/categories/")
async def get_report_categories(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get available report categories."""
    service = ReportService(db)
    categories = await service.get_report_categories()
    return categories


# Scheduled Reports
@router.post("/{report_id}/schedule")
async def schedule_report(
    report_id: int, schedule_config: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Schedule a report for automatic execution."""
    service = ReportService(db)
    schedule = await service.schedule_report(report_id, schedule_config)
    return schedule


@router.get("/{report_id}/schedules")
async def get_report_schedules(
    report_id: int, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get scheduled executions for a report."""
    service = ReportService(db)
    schedules = await service.get_report_schedules(report_id)
    return schedules


@router.delete("/schedules/{schedule_id}")
async def cancel_report_schedule(
    schedule_id: int, db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Cancel a scheduled report."""
    service = ReportService(db)
    success = await service.cancel_report_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule cancelled successfully"}


# Report Analytics and Performance
@router.get("/{report_id}/analytics")
async def get_report_analytics(
    report_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get report usage and performance analytics."""
    service = ReportService(db)
    analytics = await service.get_report_analytics(
        report_id=report_id, start_date=start_date, end_date=end_date
    )
    return analytics


@router.get("/system/performance")
async def get_system_performance(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get overall reporting system performance metrics."""
    service = ReportService(db)
    performance = await service.get_system_performance()
    return performance


# Real-time Report Data (WebSocket alternative)
@router.get("/{report_id}/realtime")
async def get_realtime_report_data(
    report_id: int,
    refresh_interval: int = Query(30, ge=5, le=300),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get real-time report data for dashboard updates."""
    service = ReportService(db)
    data = await service.get_realtime_report_data(report_id, refresh_interval)
    return data


# Data Visualization endpoints
@router.get("/{report_id}/charts")
async def get_report_charts(
    report_id: int, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get chart configurations for report visualization."""
    service = ReportService(db)
    charts = await service.get_report_charts(report_id)
    return charts


@router.post("/{report_id}/charts")
async def create_report_chart(
    report_id: int, chart_config: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new chart for report visualization."""
    service = ReportService(db)
    chart = await service.create_report_chart(report_id, chart_config)
    return chart
