"""Task management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.services.task import TaskService
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, TaskSearchParams,
    TaskStatusUpdate, TaskAssignmentCreate, TaskDependencyCreate, TaskCommentCreate,
    BulkTaskUpdate, BulkOperationResponse, UserWorkloadResponse, TaskAnalyticsResponse
)
from app.core.exceptions import (
    NotFound, PermissionDenied, BusinessLogicError, CircularDependency,
    InvalidTransition, DependencyExists, OptimisticLockError
)

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new task."""
    service = TaskService(db)
    try:
        return service.create_task(task_data, current_user)
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=TaskListResponse)
def get_tasks(
    search: Optional[str] = Query(None, description="Search in title and description"),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    project_id: Optional[int] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    is_overdue: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get tasks with filtering and pagination."""
    try:
        # Parse date strings
        from datetime import datetime
        due_date_from_dt = None
        due_date_to_dt = None
        
        if due_date_from:
            due_date_from_dt = datetime.fromisoformat(due_date_from)
        if due_date_to:
            due_date_to_dt = datetime.fromisoformat(due_date_to)
        
        # Create search params
        search_params = TaskSearchParams(
            search=search,
            status=status_filter,
            priority=priority,
            assignee_id=assignee_id,
            project_id=project_id,
            due_date_from=due_date_from_dt,
            due_date_to=due_date_to_dt,
            tags=tags,
            is_overdue=is_overdue,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        service = TaskService(db)
        return service.search_tasks(search_params, current_user)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date format: {e}")
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get task by ID."""
    service = TaskService(db)
    try:
        return service.get_task(task_id, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update task with optimistic locking."""
    service = TaskService(db)
    try:
        return service.update_task(task_id, task_data, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete task (soft delete)."""
    service = TaskService(db)
    try:
        service.delete_task(task_id, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DependencyExists as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update task status with validation."""
    service = TaskService(db)
    try:
        return service.update_task_status(
            task_id, status_update.status, current_user,
            status_update.comment, status_update.version
        )
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidTransition as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{task_id}/assignments", status_code=status.HTTP_201_CREATED)
def assign_user_to_task(
    task_id: int,
    assignment_data: TaskAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign user to task."""
    service = TaskService(db)
    try:
        service.assign_user(task_id, assignment_data.user_id, assignment_data.role, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{task_id}/assignments/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user_assignment(
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove user assignment from task."""
    service = TaskService(db)
    try:
        service.remove_assignment(task_id, user_id, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{task_id}/dependencies", status_code=status.HTTP_201_CREATED)
def add_task_dependency(
    task_id: int,
    dependency_data: TaskDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add dependency to task."""
    service = TaskService(db)
    try:
        service.add_dependency(task_id, dependency_data, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CircularDependency as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task_dependency(
    dependency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove task dependency."""
    service = TaskService(db)
    try:
        service.remove_dependency(dependency_id, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{task_id}/dependencies")
def get_task_dependencies(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get task dependency tree."""
    service = TaskService(db)
    try:
        # Check task access
        service.get_task(task_id, current_user)
        return service.repository.get_dependency_tree(task_id)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{task_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment_to_task(
    task_id: int,
    comment_data: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add comment to task."""
    service = TaskService(db)
    try:
        service.add_comment(task_id, comment_data, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{task_id}/comments")
def get_task_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get task comments."""
    service = TaskService(db)
    try:
        # Check task access
        task = service.get_task(task_id, current_user)
        # TODO: Return actual comments
        return {"task_id": task_id, "comments": []}
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{task_id}/attachments", status_code=status.HTTP_201_CREATED)
def upload_task_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload file attachment to task."""
    service = TaskService(db)
    try:
        # Check task access
        task = service.get_task(task_id, current_user)
        
        # File size validation (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size and file.size > max_size:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
        
        # TODO: Implement actual file storage and virus scanning
        return {"message": "File upload not yet implemented", "task_id": task_id, "filename": file.filename}
        
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{task_id}/attachments/{attachment_id}")
def download_task_attachment(
    task_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download task attachment."""
    service = TaskService(db)
    try:
        # Check task access
        task = service.get_task(task_id, current_user)
        
        # TODO: Implement actual file download
        return {"message": "File download not yet implemented", "task_id": task_id, "attachment_id": attachment_id}
        
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/bulk", response_model=BulkOperationResponse)
def bulk_update_tasks(
    update_data: BulkTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk update multiple tasks."""
    service = TaskService(db)
    try:
        return service.bulk_update_tasks(update_data, current_user)
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/analytics/workload/{user_id}", response_model=UserWorkloadResponse)
def get_user_workload(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user workload analytics."""
    service = TaskService(db)
    try:
        user_organizations = [org.id for org in current_user.get_organizations()]
        if not user_organizations:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no organization access")
        return service.get_user_workload(user_id, user_organizations[0])
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/analytics/organization", response_model=TaskAnalyticsResponse)
def get_organization_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get organization task analytics."""
    service = TaskService(db)
    user_organizations = [org.id for org in current_user.get_organizations()]
    if not user_organizations:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no organization access")
    return service.get_task_analytics(user_organizations[0])


@router.get("/projects/{project_id}/critical-path", response_model=List[TaskResponse])
def get_project_critical_path(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get critical path for project."""
    service = TaskService(db)
    try:
        return service.calculate_critical_path(project_id, current_user)
    except NotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/users/{user_id}/tasks", response_model=List[TaskResponse])
def get_user_tasks(
    user_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get tasks assigned to user."""
    service = TaskService(db)
    try:
        from app.models.task import TaskStatus
        status_enum = TaskStatus(status_filter) if status_filter else None
        
        user_organizations = [org.id for org in current_user.get_organizations()]
        if not user_organizations:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no organization access")
        
        tasks = service.repository.get_user_tasks(
            user_id, user_organizations[0], status_enum, limit
        )
        return [service._task_to_response(task) for task in tasks]
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {e}")
    except PermissionDenied as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))