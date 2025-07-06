"""Project phase management API endpoints."""

from typing import List, Optional, Union
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.project_phase import ProjectPhase
from app.schemas.project_phase import (
    ProjectPhaseCreate,
    ProjectPhaseUpdate,
    ProjectPhaseResponse,
    ProjectPhaseSummary
)
from app.schemas.error import ErrorResponse
from app.services.project import ProjectService
from app.core.exceptions import NotFound, PermissionDenied, BusinessLogicError


router = APIRouter(prefix="/projects/{project_id}/phases", tags=["Project Phases"])


@router.post(
    "",
    response_model=ProjectPhaseResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def create_project_phase(
    project_id: int,
    phase_data: ProjectPhaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectPhaseResponse, JSONResponse]:
    """Create a new project phase."""
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
            raise PermissionDenied("You don't have permission to manage project phases")
        
        # Create phase
        phase = ProjectPhase(
            project_id=project_id,
            phase_number=phase_data.phase_number,
            name=phase_data.name,
            description=phase_data.description,
            planned_start_date=phase_data.planned_start_date,
            planned_end_date=phase_data.planned_end_date,
            status=phase_data.status,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        # Validate dates
        phase.validate_dates()
        
        db.add(phase)
        db.commit()
        db.refresh(phase)
        
        # Update project progress
        service.update_project_progress(project_id, current_user.id)
        
        # Build response
        response_data = phase.__dict__.copy()
        response_data['duration_days'] = phase.duration_days
        response_data['is_active'] = phase.is_active
        response_data['is_completed'] = phase.is_completed
        response_data['is_overdue'] = phase.is_overdue
        
        return ProjectPhaseResponse.model_validate(response_data)
        
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
    response_model=List[ProjectPhaseSummary],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def list_project_phases(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[List[ProjectPhaseSummary], JSONResponse]:
    """List project phases."""
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
        
        # Get phases
        phases = project.phases.filter_by(is_deleted=False).order_by(ProjectPhase.phase_number).all()
        
        # Convert to summary
        items = []
        for phase in phases:
            summary_data = phase.__dict__.copy()
            summary_data['duration_days'] = phase.duration_days
            summary_data['is_active'] = phase.is_active
            summary_data['is_completed'] = phase.is_completed
            summary_data['is_overdue'] = phase.is_overdue
            summary_data['milestone_count'] = phase.milestones.filter_by(is_deleted=False).count()
            items.append(ProjectPhaseSummary.model_validate(summary_data))
        
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
    "/{phase_id}",
    response_model=ProjectPhaseResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def update_project_phase(
    project_id: int,
    phase_id: int,
    phase_data: ProjectPhaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectPhaseResponse, JSONResponse]:
    """Update project phase details."""
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
            raise PermissionDenied("You don't have permission to manage project phases")
        
        # Get phase
        phase = project.phases.filter_by(id=phase_id).first()
        if not phase:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project phase not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Update phase
        update_data = phase_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(phase, key, value)
        
        phase.updated_by = current_user.id
        phase.validate_dates()
        
        # Update status based on progress
        if phase.progress_percentage == 100 and phase.status == 'in_progress':
            phase.complete()
        
        db.commit()
        db.refresh(phase)
        
        # Update project progress
        service.update_project_progress(project_id, current_user.id)
        
        # Build response
        response_data = phase.__dict__.copy()
        response_data['duration_days'] = phase.duration_days
        response_data['is_active'] = phase.is_active
        response_data['is_completed'] = phase.is_completed
        response_data['is_overdue'] = phase.is_overdue
        
        return ProjectPhaseResponse.model_validate(response_data)
        
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


@router.delete(
    "/{phase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def delete_project_phase(
    project_id: int,
    phase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Optional[JSONResponse]:
    """Delete a project phase (soft delete)."""
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
            raise PermissionDenied("You don't have permission to manage project phases")
        
        # Get phase
        phase = project.phases.filter_by(id=phase_id).first()
        if not phase:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project phase not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Soft delete
        phase.soft_delete(deleted_by=current_user.id)
        db.commit()
        
        # Update project progress
        service.update_project_progress(project_id, current_user.id)
        
        return None
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )