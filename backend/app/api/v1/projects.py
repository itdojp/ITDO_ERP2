"""Project API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.project import (
    DeleteResponse,
    PaginatedResponse,
    ProjectCreate,
    ProjectFilter,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    ProjectResponse,
    ProjectStatistics,
    ProjectUpdate,
)
from app.services.permission import PermissionService
from app.services.project import ProjectService

settings = get_settings()
router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """Get project service instance."""
    permission_service = PermissionService(db)
    return ProjectService(db, permission_service=permission_service)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Create a new project."""
    try:
        project = project_service.create_project(
            project_data=project_data,
            owner_id=current_user.id,
            validate_permissions=True,
        )
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/", response_model=PaginatedResponse)
def list_projects(
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of projects to return"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    is_overdue: Optional[bool] = Query(None, description="Filter by overdue status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> PaginatedResponse:
    """List projects with filtering and pagination."""
    try:
        # Create filters
        filters = ProjectFilter(
            organization_id=organization_id,
            department_id=department_id,
            status=status,
            priority=priority,
            search=search,
            is_overdue=is_overdue,
        )

        # Calculate page number
        page = (skip // limit) + 1

        projects, total = project_service.list_projects(
            user_id=current_user.id,
            filters=filters,
            page=page,
            per_page=limit,
            validate_permissions=True,
        )

        # Calculate total pages
        pages = (total + limit - 1) // limit

        return PaginatedResponse(
            items=projects,
            total=total,
            page=page,
            per_page=limit,
            pages=pages,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Get a specific project by ID."""
    try:
        project = project_service.get_project(
            project_id=project_id,
            user_id=current_user.id,
            validate_permissions=True,
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return project
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Update a project."""
    try:
        project = project_service.update_project(
            project_id=project_id,
            project_data=project_data,
            user_id=current_user.id,
            validate_permissions=True,
        )
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/{project_id}", response_model=DeleteResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> DeleteResponse:
    """Delete a project."""
    try:
        success = project_service.delete_project(
            project_id=project_id,
            user_id=current_user.id,
            validate_permissions=True,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return DeleteResponse(
            success=True,
            message="Project deleted successfully",
            deleted_id=project_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def get_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> List[ProjectMemberResponse]:
    """Get all members of a project."""
    try:
        members_data = project_service.get_project_members(
            project_id=project_id,
            user_id=current_user.id,
            validate_permissions=True,
        )

        return [
            ProjectMemberResponse(
                id=member["id"],
                project_id=project_id,
                user_id=member["user_id"],
                user_email=member["user_email"],
                user_name=member["user_name"],
                role=member["role"],
                permissions=member["permissions"],
                joined_at=member["joined_at"],
                updated_at=member["joined_at"],  # Using joined_at as fallback
                is_active=member["is_active"],
            )
            for member in members_data
        ]
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    """Add a member to a project."""
    try:
        success = project_service.add_member(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
            current_user_id=current_user.id,
            permissions=member_data.permissions,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add member to project"
            )

        # Get the updated member info
        members = project_service.get_project_members(
            project_id=project_id,
            user_id=current_user.id,
            validate_permissions=False,  # Already validated above
        )

        # Find the newly added member
        for member in members:
            if member["user_id"] == member_data.user_id:
                return ProjectMemberResponse(
                    id=member["id"],
                    project_id=project_id,
                    user_id=member["user_id"],
                    user_email=member["user_email"],
                    user_name=member["user_name"],
                    role=member["role"],
                    permissions=member["permissions"],
                    joined_at=member["joined_at"],
                    updated_at=member["joined_at"],
                    is_active=member["is_active"],
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Member added but not found in response"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/{project_id}/members/{user_id}", response_model=DeleteResponse)
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> DeleteResponse:
    """Remove a member from a project."""
    try:
        success = project_service.remove_member(
            project_id=project_id,
            user_id=user_id,
            current_user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in project"
            )

        return DeleteResponse(
            success=True,
            message="Member removed from project successfully",
            deleted_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int,
    user_id: int,
    member_data: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    """Update a project member's role and permissions."""
    try:
        success = project_service.update_member_role(
            project_id=project_id,
            user_id=user_id,
            role=member_data.role or "member",
            current_user_id=current_user.id,
            permissions=member_data.permissions,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in project"
            )

        # Get the updated member info
        members = project_service.get_project_members(
            project_id=project_id,
            user_id=current_user.id,
            validate_permissions=False,  # Already validated above
        )

        # Find the updated member
        for member in members:
            if member["user_id"] == user_id:
                return ProjectMemberResponse(
                    id=member["id"],
                    project_id=project_id,
                    user_id=member["user_id"],
                    user_email=member["user_email"],
                    user_name=member["user_name"],
                    role=member["role"],
                    permissions=member["permissions"],
                    joined_at=member["joined_at"],
                    updated_at=member["joined_at"],
                    is_active=member["is_active"],
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found after update"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{project_id}/statistics", response_model=ProjectStatistics)
def get_project_statistics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectStatistics:
    """Get project statistics."""
    try:
        statistics = project_service.get_enhanced_project_statistics(
            project_id=project_id,
            user_id=current_user.id,
        )
        return statistics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{project_id}/tasks")
def get_project_tasks(
    project_id: int,
    include_completed: bool = Query(True, description="Include completed tasks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> List[Dict[str, Any]]:
    """Get all tasks for a project."""
    try:
        tasks = project_service.get_project_tasks(
            project_id=project_id,
            user_id=current_user.id,
            include_completed=include_completed,
        )
        return tasks
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{project_id}/progress")
def get_project_progress(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Dict[str, float]:
    """Get project progress percentage."""
    try:
        progress = project_service.get_project_progress(project_id)
        return {"project_id": project_id, "progress_percentage": progress}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{project_id}/budget")
def get_project_budget_utilization(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
) -> Dict[str, float]:
    """Get project budget utilization."""
    try:
        budget_info = project_service.get_budget_utilization(project_id)
        return budget_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
