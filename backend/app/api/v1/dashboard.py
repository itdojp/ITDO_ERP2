"""Dashboard API endpoints."""

from typing import Optional, Union, Dict, Any, List
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.dashboard import (
    MainDashboardData,
    PersonalDashboardData,
    ProjectDashboardStats,
    OrganizationStats,
    PersonalStats,
    TrendData,
    DashboardFilters
)
from app.schemas.error import ErrorResponse
from app.services.dashboard import DashboardService
from app.core.exceptions import NotFound, PermissionDenied


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/main",
    response_model=MainDashboardData,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_main_dashboard(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    date_range: str = Query("month", description="Date range: today, week, month, quarter"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    refresh: bool = Query(False, description="Force refresh cache"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[MainDashboardData, JSONResponse]:
    """Get main dashboard data for organization overview."""
    service = DashboardService(db)
    
    filters = DashboardFilters(
        organization_id=organization_id,
        department_id=department_id,
        date_range=date_range,
        status_filter=status_filter,
        refresh=refresh
    )
    
    try:
        dashboard_data = service.get_main_dashboard(current_user.id, filters)
        return dashboard_data
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.get(
    "/personal",
    response_model=PersonalDashboardData,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_personal_dashboard(
    date_range: str = Query("month", description="Date range: today, week, month, quarter"),
    refresh: bool = Query(False, description="Force refresh cache"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> PersonalDashboardData:
    """Get personal dashboard data for current user."""
    service = DashboardService(db)
    
    filters = DashboardFilters(
        date_range=date_range,
        refresh=refresh
    )
    
    return service.get_personal_dashboard(current_user.id, filters)


@router.get(
    "/project/{project_id}",
    response_model=ProjectDashboardStats,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def get_project_dashboard(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectDashboardStats, JSONResponse]:
    """Get project-specific dashboard data."""
    service = DashboardService(db)
    
    try:
        dashboard_data = service.get_project_dashboard(project_id, current_user.id)
        return dashboard_data
        
    except NotFound as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="NOT_FOUND"
            ).model_dump()
        )
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.get(
    "/stats/organization",
    response_model=OrganizationStats,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_organization_stats(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    refresh: bool = Query(False, description="Force refresh cache"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[OrganizationStats, JSONResponse]:
    """Get organization statistics."""
    service = DashboardService(db)
    
    try:
        stats = service._get_organization_stats(current_user.id, organization_id)
        return stats
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.get(
    "/stats/personal",
    response_model=PersonalStats,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_personal_stats(
    date_range: str = Query("month", description="Date range: today, week, month, quarter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> PersonalStats:
    """Get personal statistics for current user."""
    service = DashboardService(db)
    return service._get_personal_stats(current_user.id, date_range)


@router.get(
    "/stats/trends",
    response_model=list[TrendData],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_performance_trends(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    period: str = Query("month", description="Period: week, month, quarter"),
    metric: str = Query("projects", description="Metric: projects, tasks, budget"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[list[TrendData], JSONResponse]:
    """Get performance trends data."""
    service = DashboardService(db)
    
    filters = DashboardFilters(
        organization_id=organization_id,
        date_range=period
    )
    
    try:
        trends = service._get_performance_trends(current_user.id, filters)
        return trends
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.get(
    "/activities/recent",
    response_model=list,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_recent_activities(
    limit: int = Query(20, ge=1, le=100, description="Number of activities to return"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[List[Dict[str, Any]], JSONResponse]:
    """Get recent activities."""
    service = DashboardService(db)
    
    filters = DashboardFilters(
        organization_id=organization_id
    )
    
    try:
        activities = service._get_recent_activities(current_user.id, filters, limit)
        # Convert to dict format
        return [activity.model_dump() for activity in activities]
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.get(
    "/health",
    response_model=dict,
    summary="Dashboard health check"
)
def dashboard_health_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Health check for dashboard services."""
    try:
        # Test database connection
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar()
        
        return {
            "status": "healthy",
            "database": "connected" if result == 1 else "disconnected",
            "timestamp": "2025-01-06T12:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": "2025-01-06T12:00:00Z"
        }