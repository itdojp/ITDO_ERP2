"""Project management API endpoints."""

from typing import List, Optional, Union
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectSummary,
    ProjectTree,
    ProjectStatistics,
    ProjectInfo
)
from app.schemas.common import PaginatedResponse
from app.schemas.error import ErrorResponse
from app.services.project import ProjectService
from app.core.exceptions import NotFound, PermissionDenied, BusinessLogicError


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
        409: {"model": ErrorResponse, "description": "Conflict"},
    }
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectResponse, JSONResponse]:
    """Create a new project."""
    service = ProjectService(db)
    
    try:
        project = service.create_project(project_data, current_user.id)
        
        # Build response
        response_data = project.__dict__.copy()
        response_data['member_count'] = 1  # Creator is added as member
        response_data['phase_count'] = 0
        response_data['milestone_count'] = 0
        response_data['sub_project_count'] = 0
        
        return ProjectResponse.model_validate(response_data)
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )
    except NotFound as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="NOT_FOUND"
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
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="An unexpected error occurred",
                code="INTERNAL_ERROR"
            ).model_dump()
        )


@router.get(
    "",
    response_model=PaginatedResponse[ProjectSummary],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def list_projects(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in code, name, description"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[PaginatedResponse[ProjectSummary], JSONResponse]:
    """List projects with filters."""
    service = ProjectService(db)
    
    try:
        projects, total = service.list_projects(
            user_id=current_user.id,
            organization_id=organization_id,
            department_id=department_id,
            status=status,
            priority=priority,
            query=search,
            skip=skip,
            limit=limit
        )
        
        # Convert to summary
        items = []
        for project in projects:
            summary_data = project.__dict__.copy()
            summary_data['is_overdue'] = project.is_overdue
            summary_data['is_active'] = project.status in ['planning', 'in_progress']
            summary_data['member_count'] = service.repository.get_member_count(project.id)
            items.append(ProjectSummary.model_validate(summary_data))
        
        return PaginatedResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
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
    "/tree",
    response_model=List[ProjectTree],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_project_tree(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    root_id: Optional[int] = Query(None, description="Start from specific project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[List[ProjectTree], JSONResponse]:
    """Get project hierarchy tree."""
    service = ProjectService(db)
    
    try:
        trees = service.get_project_tree(
            user_id=current_user.id,
            organization_id=organization_id,
            root_id=root_id
        )
        return trees
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.get(
    "/overdue",
    response_model=List[ProjectSummary],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_overdue_projects(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[List[ProjectSummary], JSONResponse]:
    """Get overdue projects."""
    service = ProjectService(db)
    
    try:
        projects = service.get_overdue_projects(
            user_id=current_user.id,
            organization_id=organization_id
        )
        
        # Convert to summary
        items = []
        for project in projects:
            summary_data = project.__dict__.copy()
            summary_data['is_overdue'] = True
            summary_data['is_active'] = project.status in ['planning', 'in_progress']
            summary_data['member_count'] = service.repository.get_member_count(project.id)
            items.append(ProjectSummary.model_validate(summary_data))
        
        return items
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.get(
    "/my-projects",
    response_model=List[ProjectSummary],
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    }
)
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[ProjectSummary]:
    """Get current user's projects."""
    service = ProjectService(db)
    
    projects = service.get_user_projects(user_id=current_user.id)
    
    # Convert to summary
    items = []
    for project in projects:
        summary_data = project.__dict__.copy()
        summary_data['is_overdue'] = project.is_overdue
        summary_data['is_active'] = project.status in ['planning', 'in_progress']
        summary_data['member_count'] = service.repository.get_member_count(project.id)
        items.append(ProjectSummary.model_validate(summary_data))
    
    return items


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectResponse, JSONResponse]:
    """Get project details."""
    service = ProjectService(db)
    
    try:
        project = service.get_project(project_id, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Build response
        response_data = project.__dict__.copy()
        
        # Add relationship data
        if project.organization:
            response_data['organization'] = {
                'id': project.organization.id,
                'code': project.organization.code,
                'name': project.organization.name
            }
        
        if project.department:
            response_data['department'] = {
                'id': project.department.id,
                'code': project.department.code,
                'name': project.department.name
            }
        
        if project.project_manager:
            response_data['project_manager'] = {
                'id': project.project_manager.id,
                'full_name': project.project_manager.full_name,
                'email': project.project_manager.email
            }
        
        if project.parent:
            response_data['parent'] = {
                'id': project.parent.id,
                'code': project.parent.code,
                'name': project.parent.name
            }
        
        # Add counts
        response_data['sub_project_count'] = len(project.sub_projects)
        response_data['member_count'] = project.members.filter_by(is_active=True).count()
        response_data['phase_count'] = project.phases.filter_by(is_deleted=False).count()
        response_data['milestone_count'] = project.milestones.filter_by(is_deleted=False).count()
        
        return ProjectResponse.model_validate(response_data)
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="An unexpected error occurred",
                code="INTERNAL_ERROR"
            ).model_dump()
        )


@router.get(
    "/{project_id}/statistics",
    response_model=ProjectStatistics,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def get_project_statistics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectStatistics, JSONResponse]:
    """Get project statistics."""
    service = ProjectService(db)
    
    try:
        stats = service.get_project_statistics(project_id, current_user.id)
        return stats
        
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


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectResponse, JSONResponse]:
    """Update project details."""
    service = ProjectService(db)
    
    try:
        project = service.update_project(project_id, project_data, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Reload with relationships
        project = service.get_project(project_id, current_user.id)
        
        # Build response (similar to get_project)
        response_data = project.__dict__.copy()
        
        # Add relationship data
        if project.organization:
            response_data['organization'] = {
                'id': project.organization.id,
                'code': project.organization.code,
                'name': project.organization.name
            }
        
        if project.department:
            response_data['department'] = {
                'id': project.department.id,
                'code': project.department.code,
                'name': project.department.name
            }
        
        if project.project_manager:
            response_data['project_manager'] = {
                'id': project.project_manager.id,
                'full_name': project.project_manager.full_name,
                'email': project.project_manager.email
            }
        
        if project.parent:
            response_data['parent'] = {
                'id': project.parent.id,
                'code': project.parent.code,
                'name': project.parent.name
            }
        
        # Add counts
        response_data['sub_project_count'] = len(project.sub_projects)
        response_data['member_count'] = project.members.filter_by(is_active=True).count()
        response_data['phase_count'] = project.phases.filter_by(is_deleted=False).count()
        response_data['milestone_count'] = project.milestones.filter_by(is_deleted=False).count()
        
        return ProjectResponse.model_validate(response_data)
        
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
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="BUSINESS_LOGIC_ERROR"
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="An unexpected error occurred",
                code="INTERNAL_ERROR"
            ).model_dump()
        )


@router.put(
    "/{project_id}/update-progress",
    response_model=ProjectResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    }
)
def update_project_progress(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[ProjectResponse, JSONResponse]:
    """Update project progress based on phases."""
    service = ProjectService(db)
    
    try:
        project = service.update_project_progress(project_id, current_user.id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        # Build simple response
        response_data = project.__dict__.copy()
        response_data['sub_project_count'] = len(project.sub_projects)
        response_data['member_count'] = 0
        response_data['phase_count'] = 0
        response_data['milestone_count'] = 0
        
        return ProjectResponse.model_validate(response_data)
        
    except PermissionDenied as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="PERMISSION_DENIED"
            ).model_dump()
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
        409: {"model": ErrorResponse, "description": "Conflict"},
    }
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Optional[JSONResponse]:
    """Delete a project (soft delete)."""
    service = ProjectService(db)
    
    try:
        success = service.delete_project(project_id, current_user.id)
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Project not found",
                    code="NOT_FOUND"
                ).model_dump()
            )
        
        return None
        
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