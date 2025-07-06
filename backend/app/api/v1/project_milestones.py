"""Project milestone management API endpoints."""

from typing import List, Optional, Union
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.project_milestone import ProjectMilestone
from app.schemas.project_milestone import (
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    ProjectMilestoneResponse,
    ProjectMilestoneSummary
)
from app.schemas.error import ErrorResponse
from app.services.project import ProjectService
from app.core.exceptions import NotFound, PermissionDenied, BusinessLogicError


router = APIRouter(prefix="/projects/{project_id}/milestones", tags=["Project Milestones"])


@router.post(
    "",
    response_model=ProjectMilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def create_project_milestone(
    project_id: int,
    milestone_data: ProjectMilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectMilestoneResponse, JSONResponse]:
    """Create a new project milestone."""
    service = ProjectService(db)
    
    try:
        # Check permissions
        project = service.get_project(project_id, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        if not service._can_update_project(current_user.id, project):
            raise PermissionDenied("You don't have permission to manage project milestones")
        
        # Create milestone
        milestone = ProjectMilestone(
            project_id=project_id,
            phase_id=milestone_data.phase_id,
            name=milestone_data.name,
            description=milestone_data.description,
            due_date=milestone_data.due_date,
            is_critical=milestone_data.is_critical,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        # Validate dates
        milestone.validate_dates()
        
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        
        # Build response
        response_data = milestone.__dict__.copy()
        response_data['is_completed'] = milestone.is_completed
        response_data['is_missed'] = milestone.is_missed
        response_data['is_pending'] = milestone.is_pending
        response_data['is_overdue'] = milestone.is_overdue
        response_data['days_until_due'] = milestone.days_until_due
        response_data['is_upcoming'] = milestone.is_upcoming(days=7)
        
        return ProjectMilestoneResponse.model_validate(response_data)
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="VALIDATION_ERROR"
            ).model_dump()
        )


@router.get(
    "",
    response_model=List[ProjectMilestoneSummary],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def list_project_milestones(
    project_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    is_critical: Optional[bool] = Query(None, description="Filter critical milestones"),
    upcoming_days: Optional[int] = Query(None, description="Filter upcoming within days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[List[ProjectMilestoneSummary], JSONResponse]:
    """List project milestones."""
    service = ProjectService(db)
    
    try:
        # Check project exists and user has access
        project = service.get_project(project_id, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Get milestones
        query = project.milestones.filter_by(is_deleted=False)
        
        if status:
            query = query.filter_by(status=status)
        
        if is_critical is not None:
            query = query.filter_by(is_critical=is_critical)
        
        milestones = query.order_by(ProjectMilestone.due_date).all()
        
        # Filter upcoming if specified
        if upcoming_days is not None:
            milestones = [m for m in milestones if m.is_upcoming(days=upcoming_days)]
        
        # Convert to summary
        items = []
        for milestone in milestones:
            summary_data = milestone.__dict__.copy()
            summary_data['is_completed'] = milestone.is_completed
            summary_data['is_missed'] = milestone.is_missed
            summary_data['is_pending'] = milestone.is_pending
            summary_data['is_overdue'] = milestone.is_overdue
            summary_data['days_until_due'] = milestone.days_until_due
            summary_data['is_upcoming'] = milestone.is_upcoming(days=7)
            items.append(ProjectMilestoneSummary.model_validate(summary_data))
        
        return items
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.put(
    "/{milestone_id}",
    response_model=ProjectMilestoneResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def update_project_milestone(
    project_id: int,
    milestone_id: int,
    milestone_data: ProjectMilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectMilestoneResponse, JSONResponse]:
    """Update project milestone details."""
    service = ProjectService(db)
    
    try:
        # Check permissions
        project = service.get_project(project_id, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        if not service._can_update_project(current_user.id, project):
            raise PermissionDenied("You don't have permission to manage project milestones")
        
        # Get milestone
        milestone = project.milestones.filter_by(id=milestone_id).first()
        if not milestone:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project milestone not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Update milestone
        update_data = milestone_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(milestone, key, value)
        
        milestone.updated_by = current_user.id
        
        # Validate dates if updated
        if 'due_date' in update_data:
            milestone.validate_dates()
        
        db.commit()
        db.refresh(milestone)
        
        # Build response
        response_data = milestone.__dict__.copy()
        response_data['is_completed'] = milestone.is_completed
        response_data['is_missed'] = milestone.is_missed
        response_data['is_pending'] = milestone.is_pending
        response_data['is_overdue'] = milestone.is_overdue
        response_data['days_until_due'] = milestone.days_until_due
        response_data['is_upcoming'] = milestone.is_upcoming(days=7)
        response_data['completion_delay_days'] = milestone.completion_delay_days
        
        return ProjectMilestoneResponse.model_validate(response_data)
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="VALIDATION_ERROR"
            ).model_dump()
        )


@router.put(
    "/{milestone_id}/complete",
    response_model=ProjectMilestoneResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def complete_milestone(
    project_id: int,
    milestone_id: int,
    completion_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectMilestoneResponse, JSONResponse]:
    """Mark milestone as completed."""
    service = ProjectService(db)
    
    try:
        # Check permissions
        project = service.get_project(project_id, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        if not service._can_update_project(current_user.id, project):
            raise PermissionDenied("You don't have permission to manage project milestones")
        
        # Get milestone
        milestone = project.milestones.filter_by(id=milestone_id).first()
        if not milestone:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project milestone not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Complete milestone
        milestone.complete(completion_date)
        milestone.updated_by = current_user.id
        db.commit()
        db.refresh(milestone)
        
        # Build response
        response_data = milestone.__dict__.copy()
        response_data['is_completed'] = True
        response_data['is_missed'] = False
        response_data['is_pending'] = False
        response_data['is_overdue'] = False
        response_data['days_until_due'] = milestone.days_until_due
        response_data['completion_delay_days'] = milestone.completion_delay_days
        
        return ProjectMilestoneResponse.model_validate(response_data)
        
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="VALIDATION_ERROR"
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


@router.delete(
    "/{milestone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def delete_project_milestone(
    project_id: int,
    milestone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Optional[JSONResponse]:
    """Delete a project milestone (soft delete)."""
    service = ProjectService(db)
    
    try:
        # Check permissions
        project = service.get_project(project_id, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        if not service._can_update_project(current_user.id, project):
            raise PermissionDenied("You don't have permission to manage project milestones")
        
        # Get milestone
        milestone = project.milestones.filter_by(id=milestone_id).first()
        if not milestone:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project milestone not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Soft delete
        milestone.soft_delete(deleted_by=current_user.id)
        db.commit()
        
        return None
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )