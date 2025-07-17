"""
Enhanced Organization API endpoints for Issue #42.
拡張組織管理APIエンドポイント（Issue #42 - 組織・部門管理API実装と階層構造サポート）
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.organization import (
    OrganizationResponse,
    OrganizationTree,
    OrganizationWithStats,
)
from app.services.enhanced_organization_service import EnhancedOrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations-enhanced"])


@router.get("/{organization_id}/tree")
async def get_organization_tree(
    organization_id: int = Path(..., description="Organization ID"),
    include_departments: bool = Query(True, description="Include department hierarchy"),
    include_users: bool = Query(False, description="Include user assignments"),
    max_depth: int = Query(10, ge=1, le=20, description="Maximum depth to traverse"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationTree:
    """
    Get organization hierarchical tree structure.
    組織階層ツリー構造の取得
    """
    service = EnhancedOrganizationService(db)

    try:
        tree = await service.get_organization_tree(
            organization_id=organization_id,
            include_departments=include_departments,
            include_users=include_users,
            max_depth=max_depth
        )

        if not tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return tree

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization tree: {str(e)}"
        )


@router.get("/{organization_id}/stats")
async def get_organization_statistics(
    organization_id: int = Path(..., description="Organization ID"),
    include_subsidiaries: bool = Query(False, description="Include subsidiary statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationWithStats:
    """
    Get comprehensive organization statistics.
    組織統計情報の取得
    """
    service = EnhancedOrganizationService(db)

    try:
        stats = await service.get_organization_with_stats(
            organization_id=organization_id,
            include_subsidiaries=include_subsidiaries
        )

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization statistics: {str(e)}"
        )


@router.post("/{organization_id}/move")
async def move_organization(
    organization_id: int = Path(..., description="Organization ID to move"),
    new_parent_id: Optional[int] = Query(None, description="New parent organization ID (null for root level)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Move organization to a different parent in the hierarchy.
    組織の階層移動
    """
    # Check permissions - only admins can move organizations
    if not (current_user.is_superuser or "org_admin" in [role.name for role in current_user.roles]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to move organizations"
        )

    service = EnhancedOrganizationService(db)

    try:
        result = await service.move_organization(
            organization_id=organization_id,
            new_parent_id=new_parent_id,
            updated_by=current_user.id
        )

        return {
            "success": True,
            "message": "Organization moved successfully",
            "organization_id": organization_id,
            "new_parent_id": new_parent_id,
            "hierarchy_updated": result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move organization: {str(e)}"
        )


@router.get("/{organization_id}/subsidiaries/all")
async def get_all_subsidiaries(
    organization_id: int = Path(..., description="Parent organization ID"),
    include_inactive: bool = Query(False, description="Include inactive subsidiaries"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[OrganizationResponse]:
    """
    Get all subsidiaries recursively.
    すべての子会社の再帰的取得
    """
    service = EnhancedOrganizationService(db)

    try:
        subsidiaries = await service.get_all_subsidiaries(
            organization_id=organization_id,
            include_inactive=include_inactive
        )

        return subsidiaries

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subsidiaries: {str(e)}"
        )


@router.get("/{organization_id}/hierarchy-path")
async def get_hierarchy_path(
    organization_id: int = Path(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[OrganizationResponse]:
    """
    Get the full hierarchy path from root to the specified organization.
    ルートから指定組織までの階層パスを取得
    """
    service = EnhancedOrganizationService(db)

    try:
        path = await service.get_hierarchy_path(organization_id)

        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        return path

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hierarchy path: {str(e)}"
        )


@router.get("/{organization_id}/validation")
async def validate_organization_hierarchy(
    organization_id: int = Path(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Validate organization hierarchy integrity.
    組織階層の整合性検証
    """
    service = EnhancedOrganizationService(db)

    try:
        validation_result = await service.validate_hierarchy(organization_id)

        return {
            "organization_id": organization_id,
            "is_valid": validation_result["is_valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "recommendations": validation_result.get("recommendations", [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate hierarchy: {str(e)}"
        )


@router.post("/{organization_id}/bulk-update")
async def bulk_update_organization_hierarchy(
    organization_id: int = Path(..., description="Root organization ID"),
    updates: List[Dict[str, Any]] = ...,
    validate_before_commit: bool = Query(True, description="Validate changes before committing"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Perform bulk updates on organization hierarchy.
    組織階層の一括更新
    """
    # Check permissions - only superusers can perform bulk updates
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for bulk updates"
        )

    service = EnhancedOrganizationService(db)

    try:
        result = await service.bulk_update_hierarchy(
            root_organization_id=organization_id,
            updates=updates,
            validate_before_commit=validate_before_commit,
            updated_by=current_user.id
        )

        return {
            "success": True,
            "message": "Bulk update completed successfully",
            "updated_count": result["updated_count"],
            "errors": result.get("errors", []),
            "validation_results": result.get("validation_results", {})
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk update: {str(e)}"
        )


@router.get("/{organization_id}/departments/tree")
async def get_organization_department_tree(
    organization_id: int = Path(..., description="Organization ID"),
    include_users: bool = Query(False, description="Include user assignments"),
    include_inactive: bool = Query(False, description="Include inactive departments"),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum department depth"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get complete department tree for an organization.
    組織の部門ツリー構造を取得
    """
    service = EnhancedOrganizationService(db)

    try:
        department_tree = await service.get_organization_department_tree(
            organization_id=organization_id,
            include_users=include_users,
            include_inactive=include_inactive,
            max_depth=max_depth
        )

        if not department_tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found or has no departments"
            )

        return department_tree

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve department tree: {str(e)}"
        )


@router.get("/search/advanced")
async def advanced_organization_search(
    query: str = Query(..., min_length=1, description="Search query"),
    search_fields: List[str] = Query(default=["name", "code"], description="Fields to search in"),
    filters: Optional[str] = Query(None, description="Additional filters as JSON string"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Advanced organization search with multiple criteria.
    高度な組織検索（複数条件対応）
    """
    service = EnhancedOrganizationService(db)

    try:
        # Parse filters from JSON string if provided
        parsed_filters = {}
        if filters:
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format in filters parameter"
                )

        search_results = await service.advanced_search(
            query=query,
            search_fields=search_fields,
            filters=parsed_filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

        return {
            "results": search_results["organizations"],
            "total_count": search_results["total_count"],
            "query": query,
            "search_fields": search_fields,
            "filters_applied": parsed_filters,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": search_results["total_count"] > (offset + limit)
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
