"""Task management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskListResponse:
    """List tasks with filters and pagination."""
    service = TaskService()

    filters = {}
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """Update task status."""
    service = TaskService()
    try:
        return service.update_task_status(
            task_id=task_id, status_update=status_update, user=current_user, db=db
        )
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Status update not implemented yet",
        )
