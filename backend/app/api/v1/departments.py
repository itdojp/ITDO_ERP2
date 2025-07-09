"""Department API endpoints."""

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse, PaginatedResponse
from app.schemas.department import (
    DepartmentBasic,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentSummary,
    DepartmentTree,
    DepartmentUpdate,
    DepartmentWithUsers,
)
from app.services.department import DepartmentService
from app.types import OrganizationId

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get(
    "/",
    response_model=PaginatedResponse[DepartmentSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def list_departments(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    organization_id: Optional[OrganizationId] = Query(
        None, description="Filter by organization"
    ),
    search: Optional[str] = Query(None, description="Search query"),
    active_only: bool = Query(True, description="Only return active departments"),
    department_type: Optional[str] = Query(
        None, description="Filter by department type"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[DepartmentSummary]:
    """List departments with pagination and filtering."""
    service = DepartmentService(db)

    # Build filters
    filters: Dict[str, Any] = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if active_only:
        filters["is_active"] = True
    if department_type:
        filters["department_type"] = department_type

    # Get departments
    if search:
        departments, total = service.search_departments(
            search, skip, limit, organization_id
        )
    else:
        departments, total = service.list_departments(skip, limit, filters)

    # Convert to summary
    items = [service.get_department_summary(dept) for dept in departments]

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/organization/{organization_id}/tree",
    response_model=List[DepartmentTree],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_department_tree(
    organization_id: OrganizationId = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[DepartmentTree]:
    """Get department hierarchy tree for an organization."""
    service = DepartmentService(db)

    # Verify organization exists
    from app.services.organization import OrganizationService

    org_service = OrganizationService(db)
    if not org_service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return service.get_department_tree(organization_id)


@router.put(
    "/reorder",
    response_model=Dict[str, str],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        400: {"model": ErrorResponse, "description": "Invalid department IDs"},
    },
)
def reorder_departments(
    department_ids: List[int] = Body(
        ..., description="List of department IDs in new order"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[Dict[str, str], JSONResponse]:
    """Update display order for multiple departments."""
    if not department_ids:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail="No department IDs provided", code="INVALID_REQUEST"
            ).model_dump(),
        )

    service = DepartmentService(db)

    # Verify all departments exist and get their organizations
    org_ids = set()
    for dept_id in department_ids:
        dept = service.get_department(dept_id)
        if not dept:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail=f"Department {dept_id} not found", code="INVALID_DEPARTMENT"
                ).model_dump(),
            )
        org_ids.add(dept.organization_id)

    # Check permissions for all organizations
    if not current_user.is_superuser:
        for org_id in org_ids:
            if not service.user_has_permission(
                current_user.id, "departments.reorder", org_id
            ):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=ErrorResponse(
                        detail="Insufficient permissions to reorder departments",
                        code="PERMISSION_DENIED",
                    ).model_dump(),
                )

    # Update display order
    service.update_display_order(department_ids)

    return {"message": f"Display order updated for {len(department_ids)} departments"}


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_department(
    department_id: int = Path(..., description="Department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DepartmentResponse:
    """Get department details."""
    service = DepartmentService(db)
    department = service.get_department(department_id)

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    return service.get_department_response(department)


@router.get(
    "/{department_id}/users",
    response_model=DepartmentWithUsers,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_department_users(
    department_id: int = Path(..., description="Department ID"),
    include_sub_departments: bool = Query(
        False, description="Include users from sub-departments"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DepartmentWithUsers:
    """Get department with user list."""
    service = DepartmentService(db)
    department = service.get_department(department_id)

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    return service.get_department_with_users(department, include_sub_departments)


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        409: {"model": ErrorResponse, "description": "Department code already exists"},
    },
)
def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[DepartmentResponse, JSONResponse]:
    """Create a new department."""
    # Check permissions
    service = DepartmentService(db)
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "departments.create", department_data.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to create departments",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Verify organization exists
    from app.services.organization import OrganizationService

    org_service = OrganizationService(db)
    if not org_service.get_organization(department_data.organization_id):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Organization not found", code="ORGANIZATION_NOT_FOUND"
            ).model_dump(),
        )

    # Verify parent department if specified
    if department_data.parent_id:
        parent = service.get_department(department_data.parent_id)
        if not parent or parent.organization_id != department_data.organization_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Invalid parent department", code="INVALID_PARENT"
                ).model_dump(),
            )

    try:
        department = service.create_department(
            department_data, created_by=current_user.id
        )
        return service.get_department_response(department)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(detail=str(e), code="DUPLICATE_CODE").model_dump(),
        )
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Department code already exists in this organization",
                code="DUPLICATE_CODE",
            ).model_dump(),
        )


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department not found"},
        409: {"model": ErrorResponse, "description": "Department code already exists"},
    },
)
def update_department(
    department_id: int = Path(..., description="Department ID"),
    *,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[DepartmentResponse, JSONResponse]:
    """Update department details."""
    service = DepartmentService(db)
    department = service.get_department(department_id)

    if not department:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Department not found", code="NOT_FOUND"
            ).model_dump(),
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "departments.update", department.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to update this department",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Verify parent department if being changed
    if (
        department_data.parent_id is not None
        and department_data.parent_id != department.parent_id
    ):
        if department_data.parent_id == department_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Department cannot be its own parent", code="INVALID_PARENT"
                ).model_dump(),
            )

        if department_data.parent_id:
            parent = service.get_department(department_data.parent_id)
            if not parent or parent.organization_id != department.organization_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ErrorResponse(
                        detail="Invalid parent department", code="INVALID_PARENT"
                    ).model_dump(),
                )

    try:
        updated_department = service.update_department(
            department_id, department_data, updated_by=current_user.id
        )
        if not updated_department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found after update",
            )
        return service.get_department_response(updated_department)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(detail=str(e), code="DUPLICATE_CODE").model_dump(),
        )


@router.delete(
    "/{department_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department not found"},
        409: {"model": ErrorResponse, "description": "Department has sub-departments"},
    },
)
def delete_department(
    department_id: int = Path(..., description="Department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[DeleteResponse, JSONResponse]:
    """Delete (soft delete) a department."""
    service = DepartmentService(db)
    department = service.get_department(department_id)

    if not department:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Department not found", code="NOT_FOUND"
            ).model_dump(),
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "departments.delete", department.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to delete departments",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Check for sub-departments
    if service.has_sub_departments(department_id):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Cannot delete department with active sub-departments",
                code="HAS_SUB_DEPARTMENTS",
            ).model_dump(),
        )

    # Perform soft delete
    success = service.delete_department(department_id, deleted_by=current_user.id)

    return DeleteResponse(
        success=success, message="Department deleted successfully", id=department_id
    )


@router.get(
    "/{department_id}/sub-departments",
    response_model=List[DepartmentBasic],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_sub_departments(
    department_id: int = Path(..., description="Department ID"),
    recursive: bool = Query(False, description="Get all sub-departments recursively"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[DepartmentBasic]:
    """Get sub-departments of a department."""
    service = DepartmentService(db)

    # Check if department exists
    if not service.get_department(department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    if recursive:
        sub_departments = service.get_all_sub_departments(department_id)
    else:
        sub_departments = service.get_direct_sub_departments(department_id)

    return [DepartmentBasic.model_validate(dept, from_attributes=True) for dept in sub_departments]


@router.get(
    "/{department_id}/tree",
    response_model=DepartmentTree,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_department_subtree(
    department_id: int = Path(..., description="Department ID"),
    max_depth: Optional[int] = Query(None, description="Maximum depth to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DepartmentTree:
    """Get department subtree starting from specified department."""
    service = DepartmentService(db)
    
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    # Build subtree recursively
    def build_subtree(dept_id: int, current_depth: int = 0) -> DepartmentTree:
        dept = service.get_department(dept_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Department {dept_id} not found"
            )
        
        children = []
        if max_depth is None or current_depth < max_depth:
            sub_depts = service.get_direct_sub_departments(dept_id)
            for sub in sub_depts:
                children.append(build_subtree(sub.id, current_depth + 1))
        
        manager_name = None
        if dept.manager_id:
            manager = db.query(User).filter(User.id == dept.manager_id).first()
            if manager:
                manager_name = manager.full_name
        
        return DepartmentTree(
            id=dept.id,
            code=dept.code,
            name=dept.name,
            name_en=dept.name_en,
            is_active=dept.is_active,
            level=current_depth,
            parent_id=dept.parent_id,
            manager_id=dept.manager_id,
            manager_name=manager_name,
            user_count=service.get_department_user_count(dept.id),
            children=children,
        )
    
    return build_subtree(department_id)


@router.get(
    "/{department_id}/children",
    response_model=List[DepartmentBasic],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_direct_children(
    department_id: int = Path(..., description="Department ID"),
    active_only: bool = Query(True, description="Only return active departments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[DepartmentBasic]:
    """Get direct children of a department (one level only)."""
    service = DepartmentService(db)
    
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    children = service.get_direct_sub_departments(department_id)
    
    if active_only:
        children = [child for child in children if child.is_active]
    
    return [DepartmentBasic.model_validate(child, from_attributes=True) for child in children]


@router.post(
    "/{department_id}/move",
    response_model=DepartmentResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department not found"},
        400: {"model": ErrorResponse, "description": "Invalid move operation"},
    },
)
def move_department(
    department_id: int = Path(..., description="Department ID to move"),
    new_parent_id: Optional[int] = Body(None, description="New parent department ID (null for root)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[DepartmentResponse, JSONResponse]:
    """Move department to a new parent in the hierarchy."""
    service = DepartmentService(db)
    
    # Check if department exists
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "departments.update", department.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to move department",
                    code="PERMISSION_DENIED"
                ).model_dump(),
            )
    
    # If new parent is specified, verify it exists and is in same organization
    if new_parent_id is not None:
        new_parent = service.get_department(new_parent_id)
        if not new_parent:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="New parent department not found",
                    code="PARENT_NOT_FOUND"
                ).model_dump(),
            )
        
        if new_parent.organization_id != department.organization_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Cannot move department to different organization",
                    code="CROSS_ORG_MOVE"
                ).model_dump(),
            )
    
    try:
        # Perform the move
        updated_department = service.move_department(department_id, new_parent_id)
        return service.get_department_response(updated_department)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e),
                code="INVALID_MOVE"
            ).model_dump(),
        )
    except Exception as e:
        if "circular reference" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Cannot create circular reference in hierarchy",
                    code="CIRCULAR_REFERENCE"
                ).model_dump(),
            )
        elif "maximum depth" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Maximum hierarchy depth exceeded",
                    code="MAX_DEPTH_EXCEEDED"
                ).model_dump(),
            )
        raise


@router.get(
    "/{department_id}/permissions",
    response_model=Dict[str, List[str]],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_department_permissions(
    department_id: int = Path(..., description="Department ID"),
    user_id: Optional[int] = Query(None, description="Specific user ID to check permissions for"),
    include_inherited: bool = Query(True, description="Include inherited permissions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, List[str]]:
    """Get permissions for a department, optionally for a specific user."""
    service = DepartmentService(db)
    
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    # If no specific user is requested, return current user's permissions
    target_user_id = user_id if user_id else current_user.id
    
    # Check if current user can view permissions
    if not current_user.is_superuser and target_user_id != current_user.id:
        if not service.user_has_permission(
            current_user.id, "departments.view_permissions", department.organization_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view department permissions"
            )
    
    # Get permissions
    direct_permissions = service.get_user_department_permissions(target_user_id, department_id)
    
    result = {
        "direct_permissions": direct_permissions,
    }
    
    if include_inherited:
        effective_permissions = service.get_user_effective_permissions(
            target_user_id, department_id
        )
        inherited_permissions = list(set(effective_permissions) - set(direct_permissions))
        result["inherited_permissions"] = inherited_permissions
        result["effective_permissions"] = effective_permissions
        
        # Get inheritance chain
        inheritance_chain = service.get_permission_inheritance_chain(department_id)
        result["inheritance_chain"] = [
            {"id": dept.id, "name": dept.name, "depth": dept.depth}
            for dept in inheritance_chain
        ]
    
    return result


# Department-Task Integration Endpoints

@router.get(
    "/{department_id}/tasks",
    response_model=List[Dict[str, Any]],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_department_tasks(
    department_id: int = Path(..., description="Department ID"),
    include_inherited: bool = Query(True, description="Include inherited tasks"),
    include_delegated: bool = Query(True, description="Include delegated tasks"),
    status: Optional[List[str]] = Query(None, description="Filter by task status"),
    priority: Optional[List[str]] = Query(None, description="Filter by task priority"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """Get all tasks assigned to a department."""
    service = DepartmentService(db)
    
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    # Get tasks
    tasks = service.get_department_tasks(
        department_id,
        include_inherited=include_inherited,
        include_delegated=include_delegated,
        status_filter=status,
        priority_filter=priority,
    )
    
    # Format response with task details and assignment info
    result = []
    for task in tasks:
        # Get assignment details
        assignments = [
            a for a in task.department_assignments 
            if a.department_id == department_id and a.is_active
        ]
        
        assignment_info = None
        if assignments:
            assignment = assignments[0]
            assignment_info = {
                "assignment_type": assignment.assignment_type,
                "visibility_scope": assignment.visibility_scope,
                "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                "delegated_from": assignment.delegated_from_department_id,
            }
        
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "project_id": task.project_id,
            "assignee_id": task.assignee_id,
            "reporter_id": task.reporter_id,
            "assignment_info": assignment_info,
        })
    
    return result


@router.post(
    "/{department_id}/tasks/{task_id}",
    response_model=Dict[str, str],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department or task not found"},
        400: {"model": ErrorResponse, "description": "Invalid assignment"},
    },
)
def assign_task_to_department(
    department_id: int = Path(..., description="Department ID"),
    task_id: int = Path(..., description="Task ID"),
    assignment_type: str = Body("department", description="Assignment type"),
    visibility_scope: str = Body("department", description="Visibility scope"),
    notes: Optional[str] = Body(None, description="Assignment notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[Dict[str, str], JSONResponse]:
    """Assign a task to a department."""
    service = DepartmentService(db)
    
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "tasks.assign", department.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to assign tasks",
                    code="PERMISSION_DENIED"
                ).model_dump(),
            )
    
    try:
        assignment = service.assign_task_to_department(
            task_id=task_id,
            department_id=department_id,
            assignment_type=assignment_type,
            visibility_scope=visibility_scope,
            assigned_by=current_user.id,
            notes=notes,
        )
        return {"message": "Task assigned successfully", "assignment_id": str(assignment.id)}
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(detail=str(e), code="NOT_FOUND").model_dump(),
        )
    except Exception as e:
        if "already assigned" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Task is already assigned to this department",
                    code="ALREADY_ASSIGNED"
                ).model_dump(),
            )
        raise


@router.post(
    "/{department_id}/tasks/{task_id}/delegate",
    response_model=Dict[str, str],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department or task not found"},
        400: {"model": ErrorResponse, "description": "Invalid delegation"},
    },
)
def delegate_task_to_department(
    department_id: int = Path(..., description="Source department ID"),
    task_id: int = Path(..., description="Task ID"),
    to_department_id: int = Body(..., description="Target department ID"),
    notes: Optional[str] = Body(None, description="Delegation notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[Dict[str, str], JSONResponse]:
    """Delegate a task from one department to another."""
    service = DepartmentService(db)
    
    # Verify source department
    source_dept = service.get_department(department_id)
    if not source_dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source department not found"
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "tasks.delegate", source_dept.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to delegate tasks",
                    code="PERMISSION_DENIED"
                ).model_dump(),
            )
    
    try:
        delegation = service.delegate_task(
            task_id=task_id,
            from_department_id=department_id,
            to_department_id=to_department_id,
            delegated_by=current_user.id,
            notes=notes,
        )
        return {
            "message": "Task delegated successfully",
            "delegation_id": str(delegation.id)
        }
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(detail=str(e), code="NOT_FOUND").model_dump(),
        )
    except Exception as e:
        if "not assigned" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Task is not assigned to the source department",
                    code="NOT_ASSIGNED"
                ).model_dump(),
            )
        elif "collaboration" in str(e).lower() or "hierarchy" in str(e).lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail=str(e),
                    code="INVALID_DELEGATION"
                ).model_dump(),
            )
        raise


@router.delete(
    "/{department_id}/tasks/{task_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department or task not found"},
    },
)
def remove_task_from_department(
    department_id: int = Path(..., description="Department ID"),
    task_id: int = Path(..., description="Task ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Union[DeleteResponse, JSONResponse]:
    """Remove task assignment from department."""
    service = DepartmentService(db)
    
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "tasks.unassign", department.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to remove task assignments",
                    code="PERMISSION_DENIED"
                ).model_dump(),
            )
    
    success = service.remove_task_from_department(task_id, department_id, current_user.id)
    
    if not success:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Task assignment not found",
                code="ASSIGNMENT_NOT_FOUND"
            ).model_dump(),
        )
    
    return DeleteResponse(
        deleted=True,
        message="Task assignment removed successfully"
    )


@router.get(
    "/{department_id}/task-statistics",
    response_model=Dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    },
)
def get_department_task_statistics(
    department_id: int = Path(..., description="Department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get task statistics for a department."""
    service = DepartmentService(db)
    
    department = service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    
    return service.get_department_task_statistics(department_id)
