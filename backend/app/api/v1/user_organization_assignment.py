"""
User Organization and Department Assignment API endpoints for Issue #42.
ユーザー組織・部門割り当てAPIエンドポイント（Issue #42）
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user_assignment import (
    BulkUserAssignmentRequest,
    DepartmentUsersResponse,
    OrganizationUsersResponse,
    UserAssignmentCreate,
    UserAssignmentResponse,
    UserAssignmentUpdate,
)
from app.services.user_assignment_service import UserAssignmentService

router = APIRouter(prefix="/user-assignments", tags=["user-assignments"])


@router.get("/organizations/{organization_id}/users")
async def get_organization_users(
    organization_id: int = Path(..., description="Organization ID"),
    include_departments: bool = Query(
        True, description="Include department information"
    ),
    include_inactive: bool = Query(False, description="Include inactive users"),
    role_filter: Optional[str] = Query(None, description="Filter by user role"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationUsersResponse:
    """
    Get all users assigned to an organization.
    組織に割り当てられたユーザー一覧を取得
    """
    service = UserAssignmentService(db)

    try:
        result = await service.get_organization_users(
            organization_id=organization_id,
            include_departments=include_departments,
            include_inactive=include_inactive,
            role_filter=role_filter,
            limit=limit,
            offset=offset,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization users: {str(e)}",
        )


@router.get("/departments/{department_id}/users")
async def get_department_users(
    department_id: int = Path(..., description="Department ID"),
    include_sub_departments: bool = Query(
        False, description="Include users from sub-departments"
    ),
    include_inactive: bool = Query(False, description="Include inactive users"),
    role_filter: Optional[str] = Query(None, description="Filter by user role"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DepartmentUsersResponse:
    """
    Get all users assigned to a department.
    部門に割り当てられたユーザー一覧を取得
    """
    service = UserAssignmentService(db)

    try:
        result = await service.get_department_users(
            department_id=department_id,
            include_sub_departments=include_sub_departments,
            include_inactive=include_inactive,
            role_filter=role_filter,
            limit=limit,
            offset=offset,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department users: {str(e)}",
        )


@router.post("/assign")
async def assign_user_to_organization_department(
    assignment: UserAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserAssignmentResponse:
    """
    Assign user to organization and department.
    ユーザーを組織・部門に割り当て
    """
    # Check permissions - only admins or HR can assign users
    if not (
        current_user.is_superuser
        or "hr_admin" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign users",
        )

    service = UserAssignmentService(db)

    try:
        result = await service.assign_user(
            assignment=assignment, assigned_by=current_user.id
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign user: {str(e)}",
        )


@router.put("/assignments/{assignment_id}")
async def update_user_assignment(
    assignment_id: int = Path(..., description="Assignment ID"),
    assignment_update: UserAssignmentUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserAssignmentResponse:
    """
    Update user assignment.
    ユーザー割り当て情報の更新
    """
    # Check permissions
    if not (
        current_user.is_superuser
        or "hr_admin" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update assignments",
        )

    service = UserAssignmentService(db)

    try:
        result = await service.update_assignment(
            assignment_id=assignment_id,
            assignment_update=assignment_update,
            updated_by=current_user.id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update assignment: {str(e)}",
        )


@router.delete("/assignments/{assignment_id}")
async def remove_user_assignment(
    assignment_id: int = Path(..., description="Assignment ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Remove user assignment.
    ユーザー割り当ての削除
    """
    # Check permissions
    if not (
        current_user.is_superuser
        or "hr_admin" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to remove assignments",
        )

    service = UserAssignmentService(db)

    try:
        result = await service.remove_assignment(
            assignment_id=assignment_id, removed_by=current_user.id
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )

        return {
            "success": True,
            "message": "User assignment removed successfully",
            "assignment_id": assignment_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove assignment: {str(e)}",
        )


@router.post("/bulk-assign")
async def bulk_assign_users(
    bulk_request: BulkUserAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Bulk assign multiple users to organizations and departments.
    複数ユーザーの組織・部門一括割り当て
    """
    # Check permissions - only superusers can perform bulk operations
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for bulk assignments",
        )

    service = UserAssignmentService(db)

    try:
        result = await service.bulk_assign_users(
            bulk_request=bulk_request, assigned_by=current_user.id
        )

        return {
            "success": True,
            "message": "Bulk assignment completed",
            "total_assignments": len(bulk_request.assignments),
            "successful_assignments": result["successful_count"],
            "failed_assignments": result["failed_count"],
            "errors": result.get("errors", []),
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk assignment: {str(e)}",
        )


@router.get("/users/{user_id}/assignments")
async def get_user_assignments(
    user_id: int = Path(..., description="User ID"),
    include_history: bool = Query(False, description="Include assignment history"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get all assignments for a specific user.
    特定ユーザーの割り当て情報を取得
    """
    service = UserAssignmentService(db)

    try:
        result = await service.get_user_assignments(
            user_id=user_id, include_history=include_history
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user assignments: {str(e)}",
        )


@router.post("/users/{user_id}/transfer")
async def transfer_user(
    user_id: int = Path(..., description="User ID to transfer"),
    new_organization_id: Optional[int] = Query(None, description="New organization ID"),
    new_department_id: Optional[int] = Query(None, description="New department ID"),
    transfer_reason: Optional[str] = Query(None, description="Reason for transfer"),
    effective_date: Optional[str] = Query(
        None, description="Effective date (ISO format)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Transfer user to different organization or department.
    ユーザーの組織・部門転籍
    """
    # Check permissions
    if not (
        current_user.is_superuser
        or "hr_admin" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to transfer users",
        )

    service = UserAssignmentService(db)

    try:
        result = await service.transfer_user(
            user_id=user_id,
            new_organization_id=new_organization_id,
            new_department_id=new_department_id,
            transfer_reason=transfer_reason,
            effective_date=effective_date,
            transferred_by=current_user.id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {
            "success": True,
            "message": "User transferred successfully",
            "user_id": user_id,
            "new_organization_id": new_organization_id,
            "new_department_id": new_department_id,
            "transfer_details": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transfer user: {str(e)}",
        )


@router.get("/organizations/{organization_id}/stats")
async def get_organization_assignment_stats(
    organization_id: int = Path(..., description="Organization ID"),
    include_departments: bool = Query(True, description="Include department breakdown"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get organization assignment statistics.
    組織の割り当て統計情報を取得
    """
    service = UserAssignmentService(db)

    try:
        result = await service.get_organization_assignment_stats(
            organization_id=organization_id, include_departments=include_departments
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assignment statistics: {str(e)}",
        )


@router.get("/departments/{department_id}/stats")
async def get_department_assignment_stats(
    department_id: int = Path(..., description="Department ID"),
    include_sub_departments: bool = Query(
        False, description="Include sub-department statistics"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get department assignment statistics.
    部門の割り当て統計情報を取得
    """
    service = UserAssignmentService(db)

    try:
        result = await service.get_department_assignment_stats(
            department_id=department_id, include_sub_departments=include_sub_departments
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assignment statistics: {str(e)}",
        )


@router.get("/validation/assignments")
async def validate_all_assignments(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    fix_issues: bool = Query(False, description="Automatically fix detected issues"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Validate all user assignments for consistency.
    ユーザー割り当ての整合性検証
    """
    # Check permissions - only admins can run validation
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for assignment validation",
        )

    service = UserAssignmentService(db)

    try:
        result = await service.validate_assignments(
            organization_id=organization_id, fix_issues=fix_issues
        )

        return {
            "validation_complete": True,
            "issues_found": result["issues_count"],
            "issues_fixed": result.get("fixed_count", 0) if fix_issues else 0,
            "validation_details": result["issues"],
            "recommendations": result.get("recommendations", []),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assignment validation failed: {str(e)}",
        )
