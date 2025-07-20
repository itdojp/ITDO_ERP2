"""
Expense Category API endpoints for financial management.
費目管理APIエンドポイント（財務管理機能）
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.expense_category import (
    ExpenseCategoryAnalytics,
    ExpenseCategoryBulkCreate,
    ExpenseCategoryCreate,
    ExpenseCategoryResponse,
    ExpenseCategoryTreeResponse,
    ExpenseCategoryUpdate,
)
from app.services.expense_category_service import ExpenseCategoryService

router = APIRouter()


@router.get("/", response_model=List[ExpenseCategoryResponse])
async def get_expense_categories(
    parent_id: Optional[int] = None,
    category_type: Optional[str] = None,
    include_children: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ExpenseCategoryResponse]:
    """費目一覧取得"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    categories = await service.get_categories(
        organization_id=current_user.organization_id,
        parent_id=parent_id,
        category_type=category_type,
        include_children=include_children,
    )
    return categories


@router.get("/tree")
async def get_expense_category_tree(
    category_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Any]:
    """費目ツリー構造取得"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    tree = await service.get_category_tree(
        organization_id=current_user.organization_id, category_type=category_type
    )
    return tree


@router.get("/{category_id}", response_model=ExpenseCategoryResponse)
async def get_expense_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseCategoryResponse:
    """費目詳細取得"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    category = await service.get_category_by_id(
        category_id, current_user.organization_id
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found"
        )
    return category


@router.post("/", response_model=ExpenseCategoryResponse)
async def create_expense_category(
    category_data: ExpenseCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseCategoryResponse:
    """費目新規作成"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    category = await service.create_category(
        category_data, current_user.organization_id
    )
    return category


@router.post("/bulk", response_model=List[ExpenseCategoryResponse])
async def create_expense_categories_bulk(
    categories_data: ExpenseCategoryBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ExpenseCategoryResponse]:
    """費目一括作成"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    categories = await service.create_categories_bulk(
        categories_data, current_user.organization_id
    )
    return categories


@router.put("/{category_id}", response_model=ExpenseCategoryResponse)
async def update_expense_category(
    category_id: int,
    category_data: ExpenseCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseCategoryResponse:
    """費目更新"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    category = await service.update_category(
        category_id, category_data, current_user.organization_id
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found"
        )
    return category


@router.delete("/{category_id}")
async def delete_expense_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """費目削除（論理削除）"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    success = await service.delete_category(category_id, current_user.organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense category not found"
        )
    return {"message": "Expense category deleted successfully"}


@router.get("/analytics/usage", response_model=ExpenseCategoryAnalytics)
async def get_expense_category_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseCategoryAnalytics:
    """費目使用状況分析"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization"
        )
    
    service = ExpenseCategoryService(db)
    analytics = await service.get_category_analytics(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )
    return analytics
