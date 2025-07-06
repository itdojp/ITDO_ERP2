"""Project management API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_current_superuser, get_db
from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectSearchParams,
)
from app.services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def create_project(
    project_data: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """Create a new project."""
    service = ProjectService()
    
    try:
        project = service.create_project(
            data=project_data,
            creator=current_user,
            db=db
        )
        db.commit()
        
        return service._project_to_response(project)
        
    except PermissionDenied as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail=str(e),
                code="INSUFFICIENT_PERMISSIONS",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except BusinessLogicError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="VALIDATION_ERROR",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.get(
    "",
    response_model=ProjectListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
    },
)
def list_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    organization_id: Optional[int] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectListResponse:
    """List projects with filtering and pagination."""
    service = ProjectService()
    
    # Build search params
    search_params = ProjectSearchParams(
        search=search,
        status=status,
        organization_id=organization_id,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        page=page,
        limit=limit
    )
    
    return service.search_projects(
        params=search_params,
        searcher=current_user,
        db=db
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """Get project details."""
    service = ProjectService()
    
    try:
        return service.get_project(
            project_id=project_id,
            viewer=current_user,
            db=db
        )
    except NotFound:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Project not found",
                code="PROJECT_NOT_FOUND",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except PermissionDenied:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Access denied",
                code="ACCESS_DENIED",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
def update_project(
    project_id: int,
    project_data: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """Update project information."""
    service = ProjectService()
    
    try:
        project = service.update_project(
            project_id=project_id,
            data=project_data,
            updater=current_user,
            db=db
        )
        db.commit()
        
        return service._project_to_response(project)
        
    except NotFound:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Project not found",
                code="PROJECT_NOT_FOUND",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except PermissionDenied:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=ErrorResponse(
                detail="Access denied",
                code="ACCESS_DENIED",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
    except BusinessLogicError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="VALIDATION_ERROR",
                timestamp=datetime.utcnow()
            ).model_dump()
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> None:
    """Delete project (admin only)."""
    service = ProjectService()
    
    try:
        service.delete_project(
            project_id=project_id,
            deleter=current_user,
            db=db
        )
        db.commit()
        
    except NotFound:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    except PermissionDenied:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )