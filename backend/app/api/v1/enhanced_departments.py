"""
Enhanced Department API endpoints for Issue #42.
拡張部門管理APIエンドポイント（Issue #42 - 組織・部門管理API実装と階層構造サポート）
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.department import (
    DepartmentResponse,
    DepartmentTree,
    DepartmentWithStats,
)
from app.services.enhanced_department_service import EnhancedDepartmentService

router = APIRouter(prefix="/departments", tags=["departments-enhanced"])


@router.get("/{department_id}/tree")
async def get_department_tree(
    department_id: int = Path(..., description="Department ID"),
    include_users: bool = Query(False, description="Include user assignments"),
    include_inactive: bool = Query(
        False, description="Include inactive sub-departments"
    ),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum depth to traverse"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DepartmentTree:
    """
    Get department hierarchical tree structure.
    部門階層ツリー構造の取得
    """
    service = EnhancedDepartmentService(db)

    try:
        tree = await service.get_department_tree(
            department_id=department_id,
            include_users=include_users,
            include_inactive=include_inactive,
            max_depth=max_depth,
        )

        if not tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        return tree

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department tree: {str(e)}",
        )


@router.get("/{department_id}/stats")
async def get_department_statistics(
    department_id: int = Path(..., description="Department ID"),
    include_sub_departments: bool = Query(
        False, description="Include sub-department statistics"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DepartmentWithStats:
    """
    Get comprehensive department statistics.
    部門統計情報の取得
    """
    service = EnhancedDepartmentService(db)

    try:
        stats = await service.get_department_with_stats(
            department_id=department_id, include_sub_departments=include_sub_departments
        )

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department statistics: {str(e)}",
        )


@router.post("/{department_id}/move")
async def move_department(
    department_id: int = Path(..., description="Department ID to move"),
    new_parent_id: Optional[int] = Query(
        None, description="New parent department ID (null for root level)"
    ),
    new_organization_id: Optional[int] = Query(
        None, description="New organization ID (for cross-org moves)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Move department to a different parent or organization.
    部門の階層移動・組織間移動
    """
    # Check permissions - only admins or department managers can move departments
    if not (
        current_user.is_superuser
        or "dept_admin" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to move departments",
        )

    service = EnhancedDepartmentService(db)

    try:
        result = await service.move_department(
            department_id=department_id,
            new_parent_id=new_parent_id,
            new_organization_id=new_organization_id,
            updated_by=current_user.id,
        )

        return {
            "success": True,
            "message": "Department moved successfully",
            "department_id": department_id,
            "new_parent_id": new_parent_id,
            "new_organization_id": new_organization_id,
            "hierarchy_updated": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move department: {str(e)}",
        )


@router.get("/{department_id}/children/all")
async def get_all_sub_departments(
    department_id: int = Path(..., description="Parent department ID"),
    include_inactive: bool = Query(
        False, description="Include inactive sub-departments"
    ),
    flatten: bool = Query(
        False, description="Return flat list instead of hierarchical"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DepartmentResponse]:
    """
    Get all sub-departments recursively.
    すべての子部門の再帰的取得
    """
    service = EnhancedDepartmentService(db)

    try:
        sub_departments = await service.get_all_sub_departments(
            department_id=department_id,
            include_inactive=include_inactive,
            flatten=flatten,
        )

        return sub_departments

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sub-departments: {str(e)}",
        )


@router.get("/{department_id}/hierarchy-path")
async def get_department_hierarchy_path(
    department_id: int = Path(..., description="Department ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DepartmentResponse]:
    """
    Get the full hierarchy path from root department to the specified department.
    ルート部門から指定部門までの階層パスを取得
    """
    service = EnhancedDepartmentService(db)

    try:
        path = await service.get_hierarchy_path(department_id)

        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        return path

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hierarchy path: {str(e)}",
        )


@router.get("/{department_id}/validation")
async def validate_department_hierarchy(
    department_id: int = Path(..., description="Department ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Validate department hierarchy integrity.
    部門階層の整合性検証
    """
    service = EnhancedDepartmentService(db)

    try:
        validation_result = await service.validate_hierarchy(department_id)

        return {
            "department_id": department_id,
            "is_valid": validation_result["is_valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "recommendations": validation_result.get("recommendations", []),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate hierarchy: {str(e)}",
        )


@router.post("/{department_id}/bulk-update")
async def bulk_update_department_hierarchy(
    department_id: int = Path(..., description="Root department ID"),
    updates: List[Dict[str, Any]] = ...,
    validate_before_commit: bool = Query(
        True, description="Validate changes before committing"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Perform bulk updates on department hierarchy.
    部門階層の一括更新
    """
    # Check permissions - only superusers can perform bulk updates
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for bulk updates",
        )

    service = EnhancedDepartmentService(db)

    try:
        result = await service.bulk_update_hierarchy(
            root_department_id=department_id,
            updates=updates,
            validate_before_commit=validate_before_commit,
            updated_by=current_user.id,
        )

        return {
            "success": True,
            "message": "Bulk update completed successfully",
            "updated_count": result["updated_count"],
            "errors": result.get("errors", []),
            "validation_results": result.get("validation_results", {}),
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk update: {str(e)}",
        )


@router.get("/{department_id}/users/all")
async def get_department_users_recursive(
    department_id: int = Path(..., description="Department ID"),
    include_sub_departments: bool = Query(
        True, description="Include users from sub-departments"
    ),
    include_inactive: bool = Query(False, description="Include inactive users"),
    role_filter: Optional[str] = Query(None, description="Filter by user role"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get all users in department and sub-departments.
    部門およびサブ部門のすべてのユーザーを取得
    """
    service = EnhancedDepartmentService(db)

    try:
        users_data = await service.get_department_users_recursive(
            department_id=department_id,
            include_sub_departments=include_sub_departments,
            include_inactive=include_inactive,
            role_filter=role_filter,
        )

        if users_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        return users_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department users: {str(e)}",
        )


@router.post("/{department_id}/update-paths")
async def update_department_paths(
    department_id: int = Path(..., description="Root department ID"),
    recursive: bool = Query(True, description="Update paths for all sub-departments"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update materialized paths for department hierarchy.
    部門階層のマテリアライズドパス更新
    """
    # Check permissions - only admins can update paths
    if not (
        current_user.is_superuser
        or "dept_admin" in [role.name for role in current_user.roles]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update department paths",
        )

    service = EnhancedDepartmentService(db)

    try:
        result = await service.update_materialized_paths(
            department_id=department_id, recursive=recursive
        )

        return {
            "success": True,
            "message": "Department paths updated successfully",
            "department_id": department_id,
            "updated_count": result["updated_count"],
            "errors": result.get("errors", []),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update department paths: {str(e)}",
        )


@router.get("/search/advanced")
async def advanced_department_search(
    query: str = Query(..., min_length=1, description="Search query"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    search_fields: List[str] = Query(
        ["name", "code"], description="Fields to search in"
    ),
    filters: Optional[Dict[str, Any]] = Query(None, description="Additional filters"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Advanced department search with multiple criteria.
    高度な部門検索（複数条件対応）
    """
    service = EnhancedDepartmentService(db)

    try:
        search_results = await service.advanced_search(
            query=query,
            organization_id=organization_id,
            search_fields=search_fields,
            filters=filters or {},
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        return {
            "results": search_results["departments"],
            "total_count": search_results["total_count"],
            "query": query,
            "search_fields": search_fields,
            "filters_applied": filters or {},
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": search_results["total_count"] > (offset + limit),
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/{department_id}/performance-metrics")
async def get_department_performance_metrics(
    department_id: int = Path(..., description="Department ID"),
    include_sub_departments: bool = Query(
        False, description="Include sub-department metrics"
    ),
    metric_types: List[str] = Query(
        ["headcount", "budget", "tasks"], description="Types of metrics to include"
    ),
    date_range_days: int = Query(
        30, ge=1, le=365, description="Date range for metrics calculation"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get department performance metrics and KPIs.
    部門パフォーマンス指標とKPIの取得
    """
    service = EnhancedDepartmentService(db)

    try:
        metrics = await service.get_performance_metrics(
            department_id=department_id,
            include_sub_departments=include_sub_departments,
            metric_types=metric_types,
            date_range_days=date_range_days,
        )

        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}",
        )
