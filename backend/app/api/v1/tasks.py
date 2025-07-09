"""Task API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse, PaginatedResponse
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskSummary,
    TaskFilter,
    TaskBulkOperation,
    TaskStatusTransition,
    TaskStatistics,
    TaskTimeEntry,
    TaskComment,
    TaskAssignment,
    PaginatedTaskResponse,
)
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=http_status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Project not found"},
    },
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Create a new task."""
    service = TaskService(db)
    
    try:
        return service.create_task(
            task_data=task_data,
            creator_id=current_user.id,
            validate_permissions=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    "",
    response_model=PaginatedTaskResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def list_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee ID"),
    reporter_id: Optional[int] = Query(None, description="Filter by reporter ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    is_overdue: Optional[bool] = Query(None, description="Filter by overdue status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedTaskResponse:
    """List tasks with filtering and pagination."""
    service = TaskService(db)
    
    # Build filter
    filters = TaskFilter(
        project_id=project_id,
        assignee_id=assignee_id,
        reporter_id=reporter_id,
        status=status,
        priority=priority,
        task_type=task_type,
        is_overdue=is_overdue,
        search=search,
    )
    
    try:
        tasks, total = service.list_tasks(
            user_id=current_user.id,
            filters=filters,
            page=page,
            per_page=per_page,
            validate_permissions=True,
        )
        
        return PaginatedTaskResponse(
            items=tasks,
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    "/search",
    response_model=List[TaskResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def search_tasks(
    q: str = Query(..., description="Search query"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TaskResponse]:
    """Search tasks by title and description."""
    service = TaskService(db)
    
    return service.search_tasks(
        query=q,
        user_id=current_user.id,
        project_id=project_id,
        limit=limit,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Get a task by ID."""
    service = TaskService(db)
    
    try:
        task = service.get_task(
            task_id=task_id,
            user_id=current_user.id,
            validate_permissions=True,
        )
        
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        
        return task
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Update a task."""
    service = TaskService(db)
    
    try:
        return service.update_task(
            task_id=task_id,
            task_data=task_data,
            user_id=current_user.id,
            validate_permissions=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete(
    "/{task_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeleteResponse:
    """Delete a task."""
    service = TaskService(db)
    
    try:
        success = service.delete_task(
            task_id=task_id,
            user_id=current_user.id,
            validate_permissions=True,
        )
        
        return DeleteResponse(
            success=success,
            message="Task deleted successfully",
            id=task_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    "/{task_id}/statistics",
    response_model=TaskStatistics,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def get_task_statistics(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskStatistics:
    """Get task statistics."""
    service = TaskService(db)
    
    try:
        return service.get_task_statistics(
            task_id=task_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/{task_id}/status",
    response_model=TaskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid status transition"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def transition_task_status(
    task_id: int,
    transition: TaskStatusTransition,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Transition task status."""
    service = TaskService(db)
    
    try:
        return service.transition_task_status(
            task_id=task_id,
            transition=transition,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/bulk",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid bulk operation"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def bulk_update_tasks(
    bulk_operation: TaskBulkOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Bulk update tasks."""
    service = TaskService(db)
    
    try:
        return service.bulk_update_tasks(
            bulk_operation=bulk_operation,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    "/{task_id}/dependencies",
    response_model=List[TaskResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def get_task_dependencies(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TaskResponse]:
    """Get task dependencies."""
    service = TaskService(db)
    
    try:
        return service.get_task_dependencies(
            task_id=task_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    "/{task_id}/subtasks",
    response_model=List[TaskResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def get_task_subtasks(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[TaskResponse]:
    """Get task subtasks."""
    service = TaskService(db)
    
    try:
        return service.get_task_subtasks(
            task_id=task_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/{task_id}/assign",
    response_model=TaskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid assignment"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def assign_task(
    task_id: int,
    assignment: TaskAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Assign task to a user."""
    service = TaskService(db)
    
    try:
        task_update = TaskUpdate(assignee_id=assignment.assignee_id)
        return service.update_task(
            task_id=task_id,
            task_data=task_update,
            user_id=current_user.id,
            validate_permissions=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/{task_id}/time",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid time entry"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def log_time(
    task_id: int,
    time_entry: TaskTimeEntry,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Log time spent on a task."""
    service = TaskService(db)
    
    try:
        # Get current task
        task = service.get_task(task_id, current_user.id)
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        
        # Update actual hours
        new_actual_hours = (task.actual_hours or 0) + time_entry.hours_worked
        task_update = TaskUpdate(actual_hours=new_actual_hours)
        
        updated_task = service.update_task(
            task_id=task_id,
            task_data=task_update,
            user_id=current_user.id,
            validate_permissions=True,
        )
        
        return {
            "success": True,
            "message": "Time logged successfully",
            "hours_logged": time_entry.hours_worked,
            "total_hours": updated_task.actual_hours,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/{task_id}/comments",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid comment"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
def add_comment(
    task_id: int,
    comment: TaskComment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Add a comment to a task."""
    service = TaskService(db)
    
    try:
        # Verify task exists and user has permission
        task = service.get_task(task_id, current_user.id)
        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        
        # In a real implementation, you'd save the comment to a comments table
        # For now, just return success
        return {
            "success": True,
            "message": "Comment added successfully",
            "comment_id": 1,  # Placeholder
        }
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )