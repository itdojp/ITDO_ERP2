"""Department API endpoints."""
from typing import List, Optional, Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentSummary,
    DepartmentTree,
    DepartmentWithUsers,
    DepartmentBasic
)
from app.schemas.common import ErrorResponse, PaginatedResponse, DeleteResponse
from app.services.department import DepartmentService
from app.types import OrganizationId

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get(
    "/",
    response_model=PaginatedResponse[DepartmentSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    }
)
def list_departments(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    organization_id: Optional[OrganizationId] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search query"),
    active_only: bool = Query(True, description="Only return active departments"),
    department_type: Optional[str] = Query(None, description="Filter by department type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
        departments, total = service.search_departments(search, skip, limit, organization_id)
    else:
        departments, total = service.list_departments(skip, limit, filters)
    
    # Convert to summary
    items = [service.get_department_summary(dept) for dept in departments]
    
    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/organization/{organization_id}/tree",
    response_model=List[DepartmentTree],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    }
)
def get_department_tree(
    organization_id: OrganizationId = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[DepartmentTree]:
    """Get department hierarchy tree for an organization."""
    service = DepartmentService(db)
    
    # Verify organization exists
    from app.services.organization import OrganizationService
    org_service = OrganizationService(db)
    if not org_service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return service.get_department_tree(organization_id)


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    }
)
def get_department(
    department_id: int = Path(..., description="Department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> DepartmentResponse:
    """Get department details."""
    service = DepartmentService(db)
    department = service.get_department(department_id)
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    return service.get_department_response(department)


@router.get(
    "/{department_id}/users",
    response_model=DepartmentWithUsers,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    }
)
def get_department_users(
    department_id: int = Path(..., description="Department ID"),
    include_sub_departments: bool = Query(False, description="Include users from sub-departments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> DepartmentWithUsers:
    """Get department with user list."""
    service = DepartmentService(db)
    department = service.get_department(department_id)
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
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
    }
)
def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[DepartmentResponse, JSONResponse]:
    """Create a new department."""
    # Check permissions
    service = DepartmentService(db)
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id,
            "departments.create",
            department_data.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to create departments",
                    code="PERMISSION_DENIED"
                ).model_dump()
            )
    
    # Verify organization exists
    from app.services.organization import OrganizationService
    org_service = OrganizationService(db)
    if not org_service.get_organization(department_data.organization_id):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Organization not found",
                code="ORGANIZATION_NOT_FOUND"
            ).model_dump()
        )
    
    # Verify parent department if specified
    if department_data.parent_id:
        parent = service.get_department(department_data.parent_id)
        if not parent or parent.organization_id != department_data.organization_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Invalid parent department",
                    code="INVALID_PARENT"
                ).model_dump()
            )
    
    try:
        department = service.create_department(
            department_data,
            created_by=current_user.id
        )
        return service.get_department_response(department)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail=str(e),
                code="DUPLICATE_CODE"
            ).model_dump()
        )
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Department code already exists in this organization",
                code="DUPLICATE_CODE"
            ).model_dump()
        )


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department not found"},
        409: {"model": ErrorResponse, "description": "Department code already exists"},
    }
)
def update_department(
    department_id: int = Path(..., description="Department ID"),
    department_data: DepartmentUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[DepartmentResponse, JSONResponse]:
    """Update department details."""
    service = DepartmentService(db)
    department = service.get_department(department_id)
    
    if not department:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Department not found",
                code="NOT_FOUND"
            ).model_dump()
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id,
            "departments.update",
            department.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to update this department",
                    code="PERMISSION_DENIED"
                ).model_dump()
            )
    
    # Verify parent department if being changed
    if department_data.parent_id is not None and department_data.parent_id != department.parent_id:
        if department_data.parent_id == department_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Department cannot be its own parent",
                    code="INVALID_PARENT"
                ).model_dump()
            )
        
        if department_data.parent_id:
            parent = service.get_department(department_data.parent_id)
            if not parent or parent.organization_id != department.organization_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ErrorResponse(
                        detail="Invalid parent department",
                        code="INVALID_PARENT"
                    ).model_dump()
                )
    
    try:
        updated_department = service.update_department(
            department_id,
            department_data,
            updated_by=current_user.id
        )
        if not updated_department:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update department"
            )
        return service.get_department_response(updated_department)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail=str(e),
                code="DUPLICATE_CODE"
            ).model_dump()
        )


@router.delete(
    "/{department_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Department not found"},
        409: {"model": ErrorResponse, "description": "Department has sub-departments"},
    }
)
def delete_department(
    department_id: int = Path(..., description="Department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[DeleteResponse, JSONResponse]:
    """Delete (soft delete) a department."""
    service = DepartmentService(db)
    department = service.get_department(department_id)
    
    if not department:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Department not found",
                code="NOT_FOUND"
            ).model_dump()
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id,
            "departments.delete",
            department.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to delete departments",
                    code="PERMISSION_DENIED"
                ).model_dump()
            )
    
    # Check for sub-departments
    if service.has_sub_departments(department_id):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Cannot delete department with active sub-departments",
                code="HAS_SUB_DEPARTMENTS"
            ).model_dump()
        )
    
    # Perform soft delete
    success = service.delete_department(department_id, deleted_by=current_user.id)
    
    return DeleteResponse(
        success=success,
        message="Department deleted successfully",
        id=department_id
    )


@router.get(
    "/{department_id}/sub-departments",
    response_model=List[DepartmentBasic],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Department not found"},
    }
)
def get_sub_departments(
    department_id: int = Path(..., description="Department ID"),
    recursive: bool = Query(False, description="Get all sub-departments recursively"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[DepartmentBasic]:
    """Get sub-departments of a department."""
    service = DepartmentService(db)
    
    # Check if department exists
    if not service.get_department(department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    if recursive:
        sub_departments = service.get_all_sub_departments(department_id)
    else:
        sub_departments = service.get_direct_sub_departments(department_id)
    
    return [
        DepartmentBasic.model_validate(dept.to_dict())
        for dept in sub_departments
    ]


@router.put(
    "/reorder",
    response_model=Dict[str, str],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        400: {"model": ErrorResponse, "description": "Invalid department IDs"},
    }
)
def reorder_departments(
    department_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[Dict[str, str], JSONResponse]:
    """Update display order for multiple departments."""
    if not department_ids:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail="No department IDs provided",
                code="INVALID_REQUEST"
            ).model_dump()
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
                    detail=f"Department {dept_id} not found",
                    code="INVALID_DEPARTMENT"
                ).model_dump()
            )
        org_ids.add(dept.organization_id)
    
    # Check permissions for all organizations
    if not current_user.is_superuser:
        for org_id in org_ids:
            if not service.user_has_permission(
                current_user.id,
                "departments.reorder",
                org_id
            ):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=ErrorResponse(
                        detail="Insufficient permissions to reorder departments",
                        code="PERMISSION_DENIED"
                    ).model_dump()
                )
    
    # Update display order
    service.update_display_order(department_ids)
    
    return {"message": f"Display order updated for {len(department_ids)} departments"}