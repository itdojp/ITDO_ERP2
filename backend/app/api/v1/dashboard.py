"""Dashboard API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.dashboard import DashboardService
from app.schemas.dashboard import DashboardStatsResponse, ProgressDataResponse, AlertsResponse
from app.api.errors import APIError


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse, status_code=status.HTTP_200_OK)
def get_dashboard_stats(
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DashboardStatsResponse:
    """Get dashboard statistics.
    
    Returns statistics for projects and tasks, filtered by organization if specified.
    Only superusers can specify organization_id to view other organizations.
    """
    service = DashboardService()
    
    try:
        stats = service.get_dashboard_stats(
            user=current_user,
            db=db,
            organization_id=organization_id
        )
        
        # Convert dict to response model
        return DashboardStatsResponse(
            project_stats=stats["project_stats"],
            task_stats=stats["task_stats"],
            recent_activity=stats["recent_activity"]
        )
    except Exception as e:
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard statistics: {str(e)}"
        )


@router.get("/progress", response_model=ProgressDataResponse, status_code=status.HTTP_200_OK)
def get_progress_data(
    period: str = Query("month", regex="^(week|month|quarter)$", description="Time period"),
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProgressDataResponse:
    """Get progress data for the specified period.
    
    Period options: week, month, quarter
    """
    service = DashboardService()
    
    try:
        progress_data = service.get_progress_data(
            user=current_user,
            db=db,
            period=period,
            organization_id=organization_id
        )
        
        # Convert dict to response model
        return ProgressDataResponse(
            period=progress_data["period"],
            progress_data=progress_data["progress_data"],
            project_progress=progress_data["project_progress"]
        )
    except Exception as e:
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve progress data: {str(e)}"
        )


@router.get("/alerts", response_model=AlertsResponse, status_code=status.HTTP_200_OK)
def get_alerts(
    organization_id: Optional[int] = Query(None, description="Organization ID filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AlertsResponse:
    """Get dashboard alerts.
    
    Returns overdue projects/tasks and upcoming deadlines.
    """
    service = DashboardService()
    
    try:
        alerts = service.get_alerts(
            user=current_user,
            db=db,
            organization_id=organization_id
        )
        
        # Convert dict to response model
        return AlertsResponse(
            overdue_projects=alerts["overdue_projects"],
            overdue_tasks=alerts["overdue_tasks"],
            upcoming_deadlines=alerts["upcoming_deadlines"]
        )
    except Exception as e:
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )