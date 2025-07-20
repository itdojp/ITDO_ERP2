"""Permission Matrix API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.services.permission_matrix import (
    PermissionLevel,
    check_permission,
    get_permission_level,
    get_permission_matrix,
    get_user_permissions,
)

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "/check",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def check_user_permission(
    permission: str = Query(..., description="Permission to check"),
    organization_id: int = Query(..., description="Organization ID"),
    department_id: Optional[int] = Query(None, description="Department ID"),
    context: Optional[str] = Query(
        None, description="Context (organization, department)"
    ),
    user_id: Optional[int] = Query(
        None, description="User ID to check (defaults to current user)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Check if a user has a specific permission.

    Validates whether a user has the specified permission within the given context.
    """
    try:
        # Determine target user
        target_user = current_user
        if user_id and user_id != current_user.id:
            # Check if current user can check other users' permissions
            if not current_user.is_superuser:
                if not check_permission(
                    current_user, "read:user_permissions", organization_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Insufficient permissions to check other users' permissions"
                        ),
                    )

            # Get target user
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

        # Check permission
        has_permission = check_permission(
            target_user, permission, organization_id, department_id, context
        )

        return {
            "user_id": target_user.id,
            "permission": permission,
            "organization_id": organization_id,
            "department_id": department_id,
            "context": context,
            "has_permission": has_permission,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking permission: {str(e)}",
        )


@router.get(
    "/user/level",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def get_user_permission_level(
    organization_id: int = Query(..., description="Organization ID"),
    department_id: Optional[int] = Query(None, description="Department ID"),
    user_id: Optional[int] = Query(
        None, description="User ID (defaults to current user)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Get the effective permission level for a user.

    Returns the highest permission level the user has in the given context.
    """
    try:
        # Determine target user
        target_user = current_user
        if user_id and user_id != current_user.id:
            # Check if current user can view other users' permission levels
            if not current_user.is_superuser:
                if not check_permission(
                    current_user, "read:user_permissions", organization_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Insufficient permissions to view "
                            "other users' permission levels"
                        ),
                    )

            # Get target user
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

        # Get permission level
        permission_level = get_permission_level(
            target_user, organization_id, department_id
        )

        return {
            "user_id": target_user.id,
            "organization_id": organization_id,
            "department_id": department_id,
            "permission_level": permission_level.value,
            "level_index": get_permission_matrix().PERMISSION_HIERARCHY.index(
                permission_level
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting permission level: {str(e)}",
        )


@router.get(
    "/user/permissions",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def get_user_all_permissions(
    organization_id: int = Query(..., description="Organization ID"),
    department_id: Optional[int] = Query(None, description="Department ID"),
    user_id: Optional[int] = Query(
        None, description="User ID (defaults to current user)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Get all permissions for a user.

    Returns all base and context-specific permissions for the user.
    """
    try:
        # Determine target user
        target_user = current_user
        if user_id and user_id != current_user.id:
            # Check if current user can view other users' permissions
            if not current_user.is_superuser:
                if not check_permission(
                    current_user, "read:user_permissions", organization_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Insufficient permissions to view other users' permissions"
                        ),
                    )

            # Get target user
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

        # Get all permissions
        user_permissions = get_user_permissions(
            target_user, organization_id, department_id
        )

        # Convert sets to lists for JSON serialization
        serialized_permissions = {
            "base": list(user_permissions["base"]),
            "contexts": {},
        }

        for context, perms in user_permissions["contexts"].items():
            serialized_permissions["contexts"][context] = list(perms)

        return {
            "user_id": target_user.id,
            "organization_id": organization_id,
            "department_id": department_id,
            "permissions": serialized_permissions,
            "permission_count": len(user_permissions["base"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user permissions: {str(e)}",
        )


@router.get(
    "/matrix/levels",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def get_permission_levels(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Get all permission levels and their hierarchy.

    Returns information about the permission level hierarchy.
    """
    try:
        # Check if user has permission to view permission matrix
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view permission matrix",
            )

        matrix = get_permission_matrix()

        return {
            "hierarchy": [level.value for level in matrix.PERMISSION_HIERARCHY],
            "levels": {
                level.value: {
                    "index": matrix.PERMISSION_HIERARCHY.index(level),
                    "name": level.value.title(),
                    "description": f"{level.value.title()} permission level",
                }
                for level in matrix.PERMISSION_HIERARCHY
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting permission levels: {str(e)}",
        )


@router.get(
    "/matrix/level/{level}/permissions",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Permission level not found"},
    },
)
def get_level_permissions(
    level: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Get all permissions for a specific permission level.

    Returns base and context-specific permissions for the given level.
    """
    try:
        # Check if user has permission to view permission matrix
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view permission matrix",
            )

        # Validate permission level
        try:
            permission_level = PermissionLevel(level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission level '{level}' not found",
            )

        matrix = get_permission_matrix()
        all_permissions = matrix.get_all_permissions(permission_level)

        # Convert sets to lists for JSON serialization
        serialized_permissions = {"base": list(all_permissions["base"]), "contexts": {}}

        for context, perms in all_permissions["contexts"].items():
            serialized_permissions["contexts"][context] = list(perms)

        return {
            "level": level,
            "permissions": serialized_permissions,
            "base_permission_count": len(all_permissions["base"]),
            "context_permission_counts": {
                context: len(perms)
                for context, perms in all_permissions["contexts"].items()
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting level permissions: {str(e)}",
        )


@router.get(
    "/matrix/compare",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Permission level not found"},
    },
)
def compare_permission_levels(
    level1: str = Query(..., description="First permission level"),
    level2: str = Query(..., description="Second permission level"),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Compare permissions between two permission levels.

    Returns the differences and similarities between two permission levels.
    """
    try:
        # Check if user has permission to view permission matrix
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view permission matrix",
            )

        # Validate permission levels
        try:
            permission_level1 = PermissionLevel(level1)
            permission_level2 = PermissionLevel(level2)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invalid permission level: {str(e)}",
            )

        matrix = get_permission_matrix()
        differences = matrix.get_permission_differences(
            permission_level1, permission_level2
        )

        # Convert sets to lists for JSON serialization
        serialized_differences = {}
        for key, perms in differences.items():
            serialized_differences[key] = list(perms)

        return {
            "level1": level1,
            "level2": level2,
            "differences": serialized_differences,
            "difference_counts": {
                key: len(perms) for key, perms in differences.items()
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing permission levels: {str(e)}",
        )


@router.get(
    "/matrix/report",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def get_permission_matrix_report(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Generate a comprehensive permission matrix report.

    Returns detailed information about the entire permission matrix.
    """
    try:
        # Check if user has permission to view permission matrix
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view permission matrix report",
            )

        matrix = get_permission_matrix()
        report = matrix.generate_permission_report()

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating permission matrix report: {str(e)}",
        )


@router.post(
    "/matrix/validate",
    response_model=dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
def validate_permission_matrix(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """
    Validate the permission matrix hierarchy.

    Checks if the permission hierarchy is correctly configured.
    """
    try:
        # Check if user has permission to validate permission matrix
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to validate permission matrix",
            )

        matrix = get_permission_matrix()
        is_valid = matrix.validate_permission_hierarchy()

        return {
            "is_valid": is_valid,
            "hierarchy": [level.value for level in matrix.PERMISSION_HIERARCHY],
            "validation_message": "Permission hierarchy is valid"
            if is_valid
            else "Permission hierarchy validation failed",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating permission matrix: {str(e)}",
        )
