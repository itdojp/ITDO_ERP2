"""Task management API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.task import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskListResponse,
    TaskSearchParams,
)
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
def create_task(
    project_id: int,
    task_data: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Create a new task in a project."""
    service = TaskService()
    
    # Set project_id from URL
    task_data.project_id = project_id
    
    try:
        task = service.create_task(
            data=task_data,
            creator=current_user,
            db=db
        )
        db.commit()
        
        return service._task_to_response(task)
        
    except NotFound as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="PROJECT_NOT_FOUND",
                timestamp=datetime.utcnow()
            ).model_dump()
        )
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
    "/projects/{project_id}/tasks",
    response_model=TaskListResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
def list_project_tasks(
    project_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskListResponse:
    """List tasks for a project with filtering and pagination."""
    service = TaskService()
    
    # Build search params
    search_params = TaskSearchParams(
        search=search,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        limit=limit
    )
    
    try:
        return service.search_tasks_by_project(
            project_id=project_id,
            params=search_params,
            searcher=current_user,
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


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Get task details."""
    service = TaskService()
    
    try:
        return service.get_task(
            task_id=task_id,
            viewer=current_user,
            db=db
        )
    except NotFound:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Task not found",
                code="TASK_NOT_FOUND",
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
    "/{task_id}",
    response_model=TaskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def update_task(
    task_id: int,
    task_data: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Update task information."""
    service = TaskService()
    
    try:
        task = service.update_task(
            task_id=task_id,
            data=task_data,
            updater=current_user,
            db=db
        )
        db.commit()
        
        return service._task_to_response(task)
        
    except NotFound:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Task not found",
                code="TASK_NOT_FOUND",
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


@router.put(
    "/{task_id}/assign",
    response_model=TaskResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Task or user not found"},
    },
)
def assign_task(
    task_id: int,
    assignee_id: int = Query(..., description="User ID to assign the task to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Assign task to a user."""
    service = TaskService()
    
    try:
        task = service.assign_task(
            task_id=task_id,
            assignee_id=assignee_id,
            assigner=current_user,
            db=db
        )
        db.commit()
        
        return service._task_to_response(task)
        
    except NotFound as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail=str(e),
                code="NOT_FOUND",
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


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete task."""
    service = TaskService()
    
    try:
        service.delete_task(
            task_id=task_id,
            deleter=current_user,
            db=db
        )
        db.commit()
        
    except NotFound:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    except PermissionDenied:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )