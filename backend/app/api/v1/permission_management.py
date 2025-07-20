"""Permission management API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_current_superuser, get_db
from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.user import User
from app.schemas.error import ErrorResponse
from app.schemas.permission_management import (
    PermissionAuditLog,
    PermissionBulkOperation,
    PermissionBulkOperationResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionTemplate,
    PermissionTemplateCreate,
    RolePermissionAssignment,
    UserEffectivePermissions,
    UserPermissionOverride,
)
from app.services.permission import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permission Management"])


@router.get(
    "/users/{user_id}/effective",
    response_model=UserEffectivePermissions,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def get_user_effective_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserEffectivePermissions:
    """Get user's effective permissions including inheritance."""
    service = PermissionService(db)

    # Check permission to view other user's permissions
    if user_id != current_user.id and not current_user.is_superuser:
        if not service.user_has_permission(current_user.id, "users.permissions.read"):
            raise PermissionDenied("Cannot view other user's permissions")

    try:
        return service.get_user_effective_permissions(user_id)
    except ValueError as e:
        raise NotFound(f"User not found: {str(e)}")


@router.post(
    "/check",
    response_model=PermissionCheckResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
    },
)
def check_user_permissions(
    request: PermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PermissionCheckResponse:
    """Check if a user has specific permissions."""
    service = PermissionService(db)

    # Users can check their own permissions, others need permission
    if request.user_id != current_user.id and not current_user.is_superuser:
        if not service.user_has_permission(current_user.id, "users.permissions.read"):
            raise PermissionDenied("Cannot check other user's permissions")

    return service.check_user_permissions(
        request.user_id, request.permission_codes, request.context
    )


@router.post(
    "/roles/assign",
    response_model=dict,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Role or permissions not found"},
    },
)
def assign_permissions_to_role(
    assignment: RolePermissionAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Assign permissions to a role."""
    service = PermissionService(db)

    # Check permission
    if not current_user.is_superuser:
        if not service.user_has_permission(current_user.id, "roles.permissions.assign"):
            raise PermissionDenied("Cannot assign permissions to roles")

    try:
        count = service.assign_permissions_to_role(
            assignment.role_id, assignment.permission_ids, granted_by=current_user.id
        )
        return {"message": f"Successfully assigned {count} permissions to role"}
    except ValueError as e:
        raise NotFound(str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/users/override",
    response_model=dict,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def create_user_permission_override(
    override: UserPermissionOverride,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> dict[str, str]:
    """Create a user-specific permission override (superuser only)."""
    service = PermissionService(db)

    try:
        result = service.create_user_permission_override(
            override.user_id,
            override.permission_id,
            override.action,
            override.reason,
            override.expires_at,
            created_by=current_user.id,
        )
        return {"message": "Permission override created", "override_id": result.id}
    except ValueError as e:
        raise NotFound(str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/audit-log",
    response_model=List[PermissionAuditLog],
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def get_permission_audit_log(
    user_id: int | None = None,
    permission_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[PermissionAuditLog]:
    """Get permission change audit logs."""
    service = PermissionService(db)

    # Check permission
    if not current_user.is_superuser:
        if not service.user_has_permission(current_user.id, "system.audit.read"):
            raise PermissionDenied("Cannot view audit logs")

    return service.get_permission_audit_log(
        user_id=user_id, permission_id=permission_id, limit=limit, offset=offset
    )


@router.get(
    "/templates",
    response_model=List[PermissionTemplate],
    responses={
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def list_permission_templates(
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[PermissionTemplate]:
    """List available permission templates."""
    service = PermissionService(db)

    # Check permission
    if not service.user_has_permission(current_user.id, "roles.templates.read"):
        raise PermissionDenied("Cannot view permission templates")

    return service.list_permission_templates(is_active=is_active)


@router.post(
    "/templates",
    response_model=PermissionTemplate,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def create_permission_template(
    template: PermissionTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> PermissionTemplate:
    """Create a new permission template (superuser only)."""
    service = PermissionService(db)

    try:
        return service.create_permission_template(
            template.name,
            template.permission_ids,
            template.description,
            template.is_active,
            created_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/bulk",
    response_model=PermissionBulkOperationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
def execute_bulk_permission_operation(
    operation: PermissionBulkOperation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> PermissionBulkOperationResponse:
    """Execute bulk permission operations (superuser only)."""
    service = PermissionService(db)

    try:
        return service.execute_bulk_permission_operation(
            operation.operation,
            operation.target_type,
            operation.target_ids,
            operation.permission_ids,
            operation.reason,
            operation.expires_at,
            performed_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
