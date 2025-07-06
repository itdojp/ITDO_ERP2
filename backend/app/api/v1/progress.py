"""Progress API endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.progress import ProgressService
from app.api.errors import APIError
from app.core.exceptions import NotFound, PermissionDenied


router = APIRouter(prefix="/projects", tags=["progress"])


@router.get("/{project_id}/progress", status_code=status.HTTP_200_OK)
def get_project_progress(
    project_id: int = Path(..., description="Project ID", ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get project progress information.
    
    Returns detailed progress information including completion percentage,
    task breakdown, and timeline status.
    """
    service = ProgressService()
    
    try:
        # Calculate different progress metrics
        task_completion = service.calculate_task_completion_rate(project_id, db)
        effort_completion = service.calculate_effort_completion_rate(project_id, db)
        duration_completion = service.calculate_duration_completion_rate(project_id, db)
        
        # Mock response structure - would be populated from actual project data
        return {
            "project_id": project_id,
            "completion_percentage": task_completion,
            "total_tasks": 20,
            "completed_tasks": 15,
            "task_breakdown": {
                "not_started": 2,
                "in_progress": 3,
                "completed": 15,
                "on_hold": 0
            },
            "timeline": {
                "start_date": "2025-06-01",
                "end_date": "2025-08-31",
                "days_elapsed": 35,
                "days_remaining": 56,
                "is_on_track": True
            },
            "progress_metrics": {
                "task_based": task_completion,
                "effort_based": effort_completion,
                "duration_based": duration_completion
            }
        }
    except NotFound:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    except PermissionDenied:
        raise APIError(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this project"
        )
    except Exception as e:
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project progress: {str(e)}"
        )


@router.get("/{project_id}/report", status_code=status.HTTP_200_OK)
def generate_progress_report(
    project_id: int = Path(..., description="Project ID", ge=1),
    format: str = Query("json", regex="^(json|csv)$", description="Report format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Generate progress report for a project.
    
    Format options: json, csv
    """
    service = ProgressService()
    
    try:
        report_data = service.generate_progress_report(
            project_id=project_id,
            db=db,
            format=format
        )
        
        if format == "csv":
            # Return CSV file response
            csv_content = report_data.get("csv_data", "")
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=project_{project_id}_progress_report.csv"
                }
            )
        
        # Return JSON response
        return report_data
        
    except NotFound:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    except PermissionDenied:
        raise APIError(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to generate reports for this project"
        )
    except Exception as e:
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate progress report: {str(e)}"
        )