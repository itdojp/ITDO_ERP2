"""Task management API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.task import TaskService

router = APIRouter()


@router.post("", response_model=TaskResponse, status_code=http_status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Create a new task."""
    service = TaskService()
    try:
        return service.create_task(task_data=task_data, user=current_user, db=db)
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    project_id: int | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assignee_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str | None = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskListResponse:
    """List tasks with filters and pagination."""
    service = TaskService()

    filters: dict[str, Any] = {}
    if project_id is not None:
        filters["project_id"] = project_id
    if status is not None:
        filters["status"] = status
    if priority is not None:
        filters["priority"] = priority
    if assignee_id is not None:
        filters["assignee_id"] = assignee_id

    try:
        return service.list_tasks(
            filters=filters,
            user=current_user,
            db=db,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tasks",
        )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Get task details."""
    service = TaskService()
    try:
        return service.get_task(task_id=task_id, user=current_user, db=db)
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    update_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Update task information."""
    service = TaskService()
    try:
        return service.update_task(
            task_id=task_id, update_data=update_data, user=current_user, db=db
        )
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{task_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a task."""
    service = TaskService()
    try:
        service.delete_task(task_id=task_id, user=current_user, db=db)
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Update task http_status."""
    service = TaskService()
    try:
        return service.update_task_status(
            task_id=task_id, status_update=status_update, user=current_user, db=db
        )
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotImplementedError:
        raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail="Status update not implemented yet",
        )


# CRITICAL: Department Integration Endpoints for Phase 3


@router.post(
    "/department/{department_id}",
    response_model=TaskResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_department_task(
    department_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Create a new task assigned to a department."""
    service = TaskService()
    try:
        return service.create_department_task(
            task_data=task_data, user=current_user, db=db, department_id=department_id
        )
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department task: {str(e)}",
        )


@router.get("/department/{department_id}", response_model=TaskListResponse)
def get_department_tasks(
    department_id: int,
    include_subdepartments: bool = Query(
        True, description="Include subdepartment tasks"
    ),
    status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskListResponse:
    """Get tasks for a department with hierarchical support."""
    service = TaskService()
    try:
        return service.get_department_tasks(
            department_id=department_id,
            user=current_user,
            db=db,
            include_subdepartments=include_subdepartments,
            status_filter=status,
            page=page,
            page_size=page_size,
        )
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get department tasks: {str(e)}",
        )


@router.put("/{task_id}/assign-department/{department_id}", response_model=TaskResponse)
def assign_task_to_department(
    task_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Assign an existing task to a department."""
    service = TaskService()
    try:
        return service.assign_task_to_department(
            task_id=task_id, department_id=department_id, user=current_user, db=db
        )
    except NotFound as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign task to department: {str(e)}",
        )


@router.get("/by-visibility/{visibility_scope}", response_model=TaskListResponse)
def get_tasks_by_visibility(
    visibility_scope: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskListResponse:
    """Get tasks based on visibility scope."""
    service = TaskService()
    try:
        return service.get_tasks_by_visibility(
            user=current_user,
            db=db,
            visibility_scope=visibility_scope,
            page=page,
            page_size=page_size,
        )
    except PermissionDenied as e:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks by visibility: {str(e)}",
        )
