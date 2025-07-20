"""Permission inheritance API endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.user import User
from app.schemas.permission_inheritance import (
    InheritanceConflict,
    InheritanceConflictResolution,
    PermissionDependency,
    PermissionDependencyCreate,
    PermissionInheritanceCreate,
    PermissionInheritanceRule,
    PermissionInheritanceUpdate,
)
from app.services.permission_inheritance import PermissionInheritanceService

router = APIRouter()


@router.post("/inheritance-rules", response_model=PermissionInheritanceRule)
def create_inheritance_rule(
    rule_data: PermissionInheritanceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PermissionInheritanceRule:
    """Create a new permission inheritance rule."""
    service = PermissionInheritanceService(db)
    try:
        return service.create_inheritance_rule(
            parent_role_id=rule_data.parent_role_id,
            child_role_id=rule_data.child_role_id,
            creator=current_user,
            db=db,
            inherit_all=rule_data.inherit_all,
            selected_permissions=rule_data.selected_permissions,
            priority=rule_data.priority,
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except NotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDenied as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.put("/inheritance-rules/{rule_id}", response_model=PermissionInheritanceRule)
def update_inheritance_rule(
    rule_id: int,
    update_data: PermissionInheritanceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PermissionInheritanceRule:
    """Update an existing inheritance rule."""
    service = PermissionInheritanceService(db)
    try:
        return service.update_inheritance_rule(rule_id, update_data, current_user, db)
    except NotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDenied as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post("/permission-dependencies", response_model=PermissionDependency)
def create_permission_dependency(
    dependency_data: PermissionDependencyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PermissionDependency:
    """Create a permission dependency."""
    service = PermissionInheritanceService(db)
    try:
        return service.create_permission_dependency(
            permission_id=dependency_data.permission_id,
            requires_permission_id=dependency_data.requires_permission_id,
            creator=current_user,
            db=db,
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except NotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDenied as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/roles/{role_id}/effective-permissions")
def get_effective_permissions(
    role_id: int,
    include_source: bool = Query(
        False, description="Include permission source information"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get effective permissions for a role."""
    service = PermissionInheritanceService(db)
    try:
        if include_source:
            return service.get_effective_permissions_with_source(role_id)
        else:
            return service.get_effective_permissions(role_id)
    except NotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/roles/{role_id}/inheritance-conflicts", response_model=List[InheritanceConflict]
)
def get_inheritance_conflicts(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[InheritanceConflict]:
    """Get inheritance conflicts for a role."""
    service = PermissionInheritanceService(db)
    return service.get_inheritance_conflicts(role_id)


@router.post("/roles/{role_id}/resolve-conflict")
def resolve_inheritance_conflict(
    role_id: int,
    resolution: InheritanceConflictResolution,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Resolve an inheritance conflict."""
    service = PermissionInheritanceService(db)
    try:
        service.resolve_inheritance_conflict(role_id, resolution, current_user, db)
        return {"message": "Conflict resolved successfully"}
    except NotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionDenied as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/roles/{role_id}/audit-logs")
def get_inheritance_audit_logs(
    role_id: int,
    limit: int = Query(50, ge=1, le=1000, description="Number of results"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get inheritance audit logs for a role."""
    service = PermissionInheritanceService(db)
    try:
        logs = service.get_inheritance_audit_logs(role_id)
        # Apply limit
        return logs[:limit]
    except NotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/permissions/{permission_id}/dependencies",
    response_model=List[PermissionDependency],
)
def get_permission_dependencies(
    permission_id: int,
    transitive: bool = Query(False, description="Include transitive dependencies"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[PermissionDependency]:
    """Get dependencies for a permission."""
    service = PermissionInheritanceService(db)
    if transitive:
        # Get all dependencies including transitive ones
        deps = service.get_all_permission_dependencies(permission_id)
        return [
            PermissionDependency(
                id=0,  # Placeholder for transitive dependencies
                permission_id=permission_id,
                permission_code="",  # Will be filled by actual implementation
                requires_permission_id=dep.id,
                requires_permission_code=dep.code,
                is_active=True,
                created_at=dep.created_at,
                created_by=0,  # Placeholder
            )
            for dep in deps
        ]
    else:
        # Direct dependencies only - would need additional service method
        return []
