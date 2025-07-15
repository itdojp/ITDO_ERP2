"""Role permission UI API endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFound, PermissionDenied
from app.models.user import User
from app.schemas.role_permission_ui import (
    BulkPermissionUpdate,
    PermissionConflict,
    PermissionInheritanceTree,
    PermissionMatrix,
    PermissionMatrixUpdate,
    PermissionSearchResult,
    UIPermissionCategory,
)
from app.services.role_permission_ui import RolePermissionUIService

router = APIRouter()


@router.get("/definitions", response_model=List[UIPermissionCategory])
def get_permission_definitions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[UIPermissionCategory]:
    """Get all permission definitions organized by category."""
    service = RolePermissionUIService(db)
    return service.get_permission_definitions()


@router.get("/structure", response_model=Dict[str, Any])
def get_permission_ui_structure(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get permission structure for UI rendering."""
    service = RolePermissionUIService(db)
    return service.get_permission_ui_structure()


@router.get("/role/{role_id}/matrix", response_model=PermissionMatrix)
def get_role_permission_matrix(
    role_id: int,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PermissionMatrix:
    """Get permission matrix for a role."""
    service = RolePermissionUIService(db)
    try:
        return service.get_role_permission_matrix(role_id, organization_id)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません"
        )


@router.put("/role/{role_id}/matrix", response_model=PermissionMatrix)
def update_role_permissions(
    role_id: int,
    update_data: PermissionMatrixUpdate,
    organization_id: int = Query(..., description="Organization ID"),
    enforce_dependencies: bool = Query(
        False, description="Enforce permission dependencies"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PermissionMatrix:
    """Update role permissions."""
    service = RolePermissionUIService(db)
    try:
        return service.update_role_permissions(
            role_id, organization_id, update_data, current_user, enforce_dependencies
        )
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません"
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限を更新する権限がありません",
        )


@router.post(
    "/role/{role_id}/copy-from/{source_role_id}", response_model=PermissionMatrix
)
def copy_permissions_from_role(
    role_id: int,
    source_role_id: int,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PermissionMatrix:
    """Copy permissions from one role to another."""
    service = RolePermissionUIService(db)
    try:
        return service.copy_permissions_from_role(
            source_role_id, role_id, organization_id, current_user
        )
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ソースロールまたはターゲットロールが見つかりません",
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限をコピーする権限がありません",
        )


@router.get("/role/{role_id}/inheritance", response_model=PermissionInheritanceTree)
def get_permission_inheritance_tree(
    role_id: int,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PermissionInheritanceTree:
    """Get permission inheritance tree for a role."""
    service = RolePermissionUIService(db)
    try:
        return service.get_permission_inheritance_tree(role_id, organization_id)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません"
        )


@router.get("/role/{role_id}/effective", response_model=Dict[str, bool])
def get_effective_permissions(
    role_id: int,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, bool]:
    """Get effective permissions including inheritance."""
    service = RolePermissionUIService(db)
    try:
        return service.get_effective_permissions(role_id, organization_id)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません"
        )


@router.get("/role/{role_id}/conflicts", response_model=List[PermissionConflict])
def get_permission_conflicts(
    role_id: int,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[PermissionConflict]:
    """Get permission conflicts in inheritance chain."""
    service = RolePermissionUIService(db)
    try:
        return service.get_permission_conflicts(role_id, organization_id)
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ロールが見つかりません"
        )


@router.put("/bulk-update", response_model=List[PermissionMatrix])
def bulk_update_permissions(
    bulk_data: BulkPermissionUpdate,
    organization_id: int = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[PermissionMatrix]:
    """Bulk update permissions for multiple roles."""
    service = RolePermissionUIService(db)
    try:
        return service.bulk_update_permissions(
            organization_id, bulk_data.role_permissions, current_user
        )
    except PermissionDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="権限を一括更新する権限がありません",
        )


@router.get("/search", response_model=List[PermissionSearchResult])
def search_permissions(
    query: str = Query(..., description="Search query"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> List[PermissionSearchResult]:
    """Search permissions by name or code."""
    service = RolePermissionUIService(db)
    return service.search_permissions(query)
