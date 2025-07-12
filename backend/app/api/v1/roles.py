"""Role API endpoints."""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import DeleteResponse, ErrorResponse, PaginatedResponse
from app.schemas.role import (
    PermissionBasic,
    RoleCreate,
    RoleResponse,
    RoleSummary,
    RoleTree,
    RoleUpdate,
    RoleWithPermissions,
    UserRoleAssignment,
    UserRoleResponse,
)
from app.services.role import RoleService
from app.types import OrganizationId, UserId

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get(
    "/",
    response_model=PaginatedResponse[RoleSummary],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def list_roles(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    organization_id: OrganizationId | None = Query(
        None, description="Filter by organization"
    ),
    search: str | None = Query(None, description="Search query"),
    active_only: bool = Query(True, description="Only return active roles"),
    role_type: str | None = Query(None, description="Filter by role type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[RoleSummary]:
    """List roles with pagination and filtering."""
    service = RoleService(db)

    # Build filters
    filters: dict[str, Any] = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if active_only:
        filters["is_active"] = True
    if role_type:
        filters["role_type"] = role_type  # Keep as string, will be handled in service

    # Get roles
    if search:
        roles, total = service.search_roles(search, skip, limit, filters)
    else:
        roles, total = service.list_roles(skip, active_only, limit, organization_id)

    # Convert to summary
    items = [service.get_role_summary(role) for role in roles]

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/organization/{organization_id}/tree",
    response_model=list[RoleTree],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
def get_role_tree(
    organization_id: OrganizationId = Path(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[RoleTree]:
    """Get role hierarchy tree for an organization."""
    service = RoleService(db)

    # Verify organization exists
    from app.services.organization import OrganizationService

    org_service = OrganizationService(db)
    if not org_service.get_organization(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return service.get_role_tree(organization_id)


@router.get(
    "/permissions",
    response_model=list[PermissionBasic],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
def list_all_permissions(
    category: str | None = Query(None, description="Filter by permission category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PermissionBasic]:
    """List all available permissions."""
    service = RoleService(db)
    return service.list_all_permissions(category)


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def get_role(
    role_id: int = Path(..., description="Role ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse:
    """Get role details."""
    service = RoleService(db)
    role = service.get_role(role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    return service.get_role_response(role)


@router.get(
    "/{role_id}/permissions",
    response_model=RoleWithPermissions,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def get_role_permissions(
    role_id: int = Path(..., description="Role ID"),
    include_inherited: bool = Query(True, description="Include inherited permissions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleWithPermissions:
    """Get role with permission details."""
    service = RoleService(db)
    role = service.get_role(role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )

    return service.get_role_with_permissions(role, include_inherited)


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        409: {"model": ErrorResponse, "description": "Role name already exists"},
    },
)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse | JSONResponse:
    """Create a new role."""
    # Check permissions
    service = RoleService(db)
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "roles.create", role_data.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to create roles",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Verify organization exists
    from app.services.organization import OrganizationService

    org_service = OrganizationService(db)
    if not org_service.get_organization(role_data.organization_id):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Organization not found", code="ORGANIZATION_NOT_FOUND"
            ).model_dump(),
        )

    # Verify parent role if specified
    if role_data.parent_id:
        parent = service.get_role(role_data.parent_id)
        if not parent or parent.organization_id != role_data.organization_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Invalid parent role", code="INVALID_PARENT"
                ).model_dump(),
            )

    try:
        role = service.create_role(role_data, created_by=current_user.id)
        return service.get_role_response(role)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(detail=str(e), code="DUPLICATE_NAME").model_dump(),
        )
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Role name already exists in this organization",
                code="DUPLICATE_NAME",
            ).model_dump(),
        )


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
        409: {"model": ErrorResponse, "description": "Role name already exists"},
    },
)
def update_role(
    role_id: int = Path(..., description="Role ID"),
    *,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse | JSONResponse:
    """Update role details."""
    service = RoleService(db)
    role = service.get_role(role_id)

    if not role:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Role not found", code="NOT_FOUND"
            ).model_dump(),
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "roles.update", role.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to update this role",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Verify parent role if being changed
    if role_data.parent_id is not None and role_data.parent_id != role.parent_id:
        if role_data.parent_id == role_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    detail="Role cannot be its own parent", code="INVALID_PARENT"
                ).model_dump(),
            )

        if role_data.parent_id:
            parent = service.get_role(role_data.parent_id)
            if not parent or parent.organization_id != role.organization_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ErrorResponse(
                        detail="Invalid parent role", code="INVALID_PARENT"
                    ).model_dump(),
                )

    try:
        updated_role = service.update_role(
            role_id, role_data, updated_by=current_user.id
        )
        if updated_role is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=ErrorResponse(
                    detail="Role not found", code="ROLE_NOT_FOUND"
                ).model_dump(),
            )
        return service.get_role_response(updated_role)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(detail=str(e), code="DUPLICATE_NAME").model_dump(),
        )


@router.put(
    "/{role_id}/permissions",
    response_model=RoleResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
    },
)
def update_role_permissions(
    role_id: int = Path(..., description="Role ID"),
    permission_codes: list[str] = Body(..., description="List of permission codes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RoleResponse | JSONResponse:
    """Update role permissions."""
    service = RoleService(db)
    role = service.get_role(role_id)

    if not role:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Role not found", code="NOT_FOUND"
            ).model_dump(),
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "roles.update_permissions", role.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to update role permissions",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    try:
        updated_role = service.update_role_permissions(
            role_id, permission_codes, updated_by=current_user.id
        )
        return service.get_role_response(updated_role)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(e), code="INVALID_PERMISSION"
            ).model_dump(),
        )


@router.delete(
    "/{role_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Role not found"},
        409: {"model": ErrorResponse, "description": "Role is in use"},
    },
)
def delete_role(
    role_id: int = Path(..., description="Role ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeleteResponse | JSONResponse:
    """Delete (soft delete) a role."""
    service = RoleService(db)
    role = service.get_role(role_id)

    if not role:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Role not found", code="NOT_FOUND"
            ).model_dump(),
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "roles.delete", role.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to delete roles",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Check if role is in use
    if service.is_role_in_use(role_id):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Cannot delete role that is assigned to users",
                code="ROLE_IN_USE",
            ).model_dump(),
        )

    # Perform soft delete
    success = service.delete_role(role_id, deleted_by=current_user.id)

    return DeleteResponse(
        success=success, message="Role deleted successfully", id=role_id
    )


@router.post(
    "/assign",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "User or role not found"},
        409: {"model": ErrorResponse, "description": "Assignment already exists"},
    },
)
def assign_role_to_user(
    assignment: UserRoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserRoleResponse | JSONResponse:
    """Assign a role to a user."""
    service = RoleService(db)

    # Get role to check organization
    role = service.get_role(assignment.role_id)
    if not role:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Role not found", code="ROLE_NOT_FOUND"
            ).model_dump(),
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "roles.assign", role.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to assign roles",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Check if user exists
    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="User not found", code="USER_NOT_FOUND"
            ).model_dump(),
        )

    try:
        user_role = service.assign_role_to_user(assignment, assigned_by=current_user.id)
        return service.get_user_role_response(user_role)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(detail=str(e), code="ASSIGNMENT_EXISTS").model_dump(),
        )


@router.delete(
    "/assign/{user_id}/{role_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Assignment not found"},
    },
)
def remove_role_from_user(
    user_id: UserId = Path(..., description="User ID"),
    role_id: int = Path(..., description="Role ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DeleteResponse | JSONResponse:
    """Remove a role from a user."""
    service = RoleService(db)

    # Get role to check organization
    role = service.get_role(role_id)
    if not role:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Role not found", code="ROLE_NOT_FOUND"
            ).model_dump(),
        )

    # Check permissions
    if not current_user.is_superuser:
        if not service.user_has_permission(
            current_user.id, "roles.unassign", role.organization_id
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    detail="Insufficient permissions to remove role assignments",
                    code="PERMISSION_DENIED",
                ).model_dump(),
            )

    # Ensure organization_id is not None
    if role.organization_id is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail="Role must have an organization", code="INVALID_ROLE"
            ).model_dump(),
        )

    success = service.remove_role_from_user(
        user_id, role_id, role.organization_id, current_user.id
    )

    if not success:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponse(
                detail="Role assignment not found", code="ASSIGNMENT_NOT_FOUND"
            ).model_dump(),
        )

    return DeleteResponse(
        success=success, message="Role removed from user successfully", id=role_id
    )


@router.get(
    "/user/{user_id}",
    response_model=list[UserRoleResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
def get_user_roles(
    user_id: UserId = Path(..., description="User ID"),
    organization_id: OrganizationId | None = Query(
        None, description="Filter by organization"
    ),
    active_only: bool = Query(True, description="Only return active assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[UserRoleResponse]:
    """Get all roles assigned to a user."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    service = RoleService(db)
    user_role_responses = service.get_user_roles(user_id)

    return user_role_responses  # Already UserRoleResponse objects
