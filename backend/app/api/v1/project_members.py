"""Project member management API endpoints."""

from typing import List, Optional, Union
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberResponse,
    ProjectMemberSummary
)
from app.schemas.error import ErrorResponse
from app.services.project import ProjectService
from app.core.exceptions import NotFound, PermissionDenied, BusinessLogicError


router = APIRouter(prefix="/projects/{project_id}/members", tags=["Project Members"])


@router.post(
    "",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
        409: {"model": ErrorResponse, "description": "Conflict"},
    }
)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectMemberResponse, JSONResponse]:
    """Add a member to project."""
    service = ProjectService(db)
    
    try:
        member = service.add_project_member(
            project_id=project_id,
            member_user_id=member_data.user_id,
            role=member_data.role,
            allocation_percentage=member_data.allocation_percentage,
            start_date=member_data.start_date,
            end_date=member_data.end_date,
            user_id=current_user.id
        )
        
        # Build response
        response_data = member.__dict__.copy()
        response_data['user'] = {
            'id': member.user.id,
            'full_name': member.user.full_name,
            'email': member.user.email
        }
        
        return ProjectMemberResponse.model_validate(response_data)
        
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
    except BusinessLogicError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail=str(e),
                code="BUSINESS_LOGIC_ERROR"
            ).model_dump()
        )


@router.get(
    "",
    response_model=List[ProjectMemberSummary],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def list_project_members(
    project_id: int,
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[List[ProjectMemberSummary], JSONResponse]:
    """List project members."""
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
        
        # Get members
        members = project.members.filter_by(is_active=is_active).all()
        
        # Convert to summary
        items = []
        for member in members:
            summary_data = member.__dict__.copy()
            summary_data['user'] = {
                'id': member.user.id,
                'full_name': member.user.full_name,
                'email': member.user.email,
                'department': member.user.department.name if member.user.department else None
            }
            summary_data['days_allocated'] = member.days_allocated
            summary_data['is_current'] = member.is_current
            items.append(ProjectMemberSummary.model_validate(summary_data))
        
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
    "/{member_id}",
    response_model=ProjectMemberResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def update_project_member(
    project_id: int,
    member_id: int,
    member_data: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectMemberResponse, JSONResponse]:
    """Update project member details."""
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
        
        if not service._can_manage_members(current_user.id, project):
            raise PermissionDenied("You don't have permission to manage project members")
        
        # Get member
        member = project.members.filter_by(id=member_id).first()
        if not member:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project member not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Update member
        update_data = member_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(member, key, value)
        
        member.updated_by = current_user.id
        member.validate_dates()
        member.validate_allocation()
        
        db.commit()
        db.refresh(member)
        
        # Build response
        response_data = member.__dict__.copy()
        response_data['user'] = {
            'id': member.user.id,
            'full_name': member.user.full_name,
            'email': member.user.email
        }
        
        return ProjectMemberResponse.model_validate(response_data)
        
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
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    }
)
def remove_project_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Optional[JSONResponse]:
    """Remove a member from project."""
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
        
        if not service._can_manage_members(current_user.id, project):
            raise PermissionDenied("You don't have permission to manage project members")
        
        # Get member
        member = project.members.filter_by(id=member_id).first()
        if not member:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project member not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Deactivate member
        member.deactivate(end_date=date.today())
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