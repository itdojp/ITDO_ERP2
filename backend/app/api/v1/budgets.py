"""
Budget API endpoints for financial management.
予算管理APIエンドポイント（財務管理機能）
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetItemCreate,
    BudgetItemResponse,
    BudgetItemUpdate,
    BudgetResponse,
    BudgetUpdate,
)
from app.services.budget_service import BudgetService

router = APIRouter()


@router.get("/", response_model=List[BudgetResponse])
async def get_budgets(
    fiscal_year: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算一覧取得"""
    service = BudgetService(db)
    budgets = await service.get_budgets(
        organization_id=current_user.organization_id,
        fiscal_year=fiscal_year,
        status=status,
        skip=skip,
        limit=limit,
    )
    return budgets


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算詳細取得"""
    service = BudgetService(db)
    budget = await service.get_budget_by_id(budget_id, current_user.organization_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )
    return budget


@router.post("/", response_model=BudgetResponse)
async def create_budget(
    budget_data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算新規作成"""
    service = BudgetService(db)
    budget = await service.create_budget(
        budget_data, current_user.organization_id, current_user.id
    )
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算更新"""
    service = BudgetService(db)
    budget = await service.update_budget(
        budget_id, budget_data, current_user.organization_id
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )
    return budget


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算削除（論理削除）"""
    service = BudgetService(db)
    success = await service.delete_budget(budget_id, current_user.organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )
    return {"message": "Budget deleted successfully"}


@router.post("/{budget_id}/approve", response_model=BudgetResponse)
async def approve_budget(
    budget_id: int,
    approval_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算承認"""
    service = BudgetService(db)
    budget = await service.approve_budget(
        budget_id, approval_data, current_user.organization_id, current_user.id
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )
    return budget


@router.post("/{budget_id}/items", response_model=BudgetItemResponse)
async def create_budget_item(
    budget_id: int,
    item_data: BudgetItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算項目新規作成"""
    service = BudgetService(db)
    item = await service.create_budget_item(
        budget_id, item_data, current_user.organization_id
    )
    return item


@router.put("/{budget_id}/items/{item_id}", response_model=BudgetItemResponse)
async def update_budget_item(
    budget_id: int,
    item_id: int,
    item_data: BudgetItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算項目更新"""
    service = BudgetService(db)
    item = await service.update_budget_item(
        budget_id, item_id, item_data, current_user.organization_id
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget item not found"
        )
    return item


@router.delete("/{budget_id}/items/{item_id}")
async def delete_budget_item(
    budget_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算項目削除"""
    service = BudgetService(db)
    success = await service.delete_budget_item(
        budget_id, item_id, current_user.organization_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget item not found"
        )
    return {"message": "Budget item deleted successfully"}


@router.get("/{budget_id}/report", response_model=dict)
async def get_budget_report(
    budget_id: int,
    include_variance: bool = True,
    include_utilization: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算実績レポート"""
    service = BudgetService(db)
    report = await service.get_budget_report(
        budget_id,
        current_user.organization_id,
        include_variance=include_variance,
        include_utilization=include_utilization,
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found"
        )
    return report


@router.get("/analytics/summary", response_model=dict)
async def get_budget_analytics(
    fiscal_year: Optional[int] = None,
    department_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """予算分析サマリー"""
    service = BudgetService(db)
    analytics = await service.get_budget_analytics(
        organization_id=current_user.organization_id,
        fiscal_year=fiscal_year,
        department_id=department_id,
    )
    return analytics
