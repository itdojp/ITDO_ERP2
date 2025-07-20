"""
Customer Activity API endpoints for CRM functionality.
顧客活動履歴APIエンドポイント（CRM機能）
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.customer import (
    CustomerActivityCreate,
    CustomerActivityResponse,
    CustomerActivityUpdate,
)
from app.services.customer_activity_service import CustomerActivityService

router = APIRouter()


@router.get("/", response_model=List[CustomerActivityResponse])
async def get_customer_activities(
    customer_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    activity_type: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客活動履歴一覧取得"""
    service = CustomerActivityService(db)
    activities = await service.get_activities(
        organization_id=current_user.organization_id,
        customer_id=customer_id,
        opportunity_id=opportunity_id,
        activity_type=activity_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return activities


@router.get("/{activity_id}", response_model=CustomerActivityResponse)
async def get_customer_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客活動詳細取得"""
    service = CustomerActivityService(db)
    activity = await service.get_activity_by_id(
        activity_id, current_user.organization_id
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return activity


@router.post("/", response_model=CustomerActivityResponse)
async def create_customer_activity(
    activity_data: CustomerActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客活動新規作成"""
    service = CustomerActivityService(db)
    activity = await service.create_activity(
        activity_data, current_user.organization_id, current_user.id
    )
    return activity


@router.put("/{activity_id}", response_model=CustomerActivityResponse)
async def update_customer_activity(
    activity_id: int,
    activity_data: CustomerActivityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客活動更新"""
    service = CustomerActivityService(db)
    activity = await service.update_activity(
        activity_id, activity_data, current_user.organization_id
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return activity


@router.delete("/{activity_id}")
async def delete_customer_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客活動削除（論理削除）"""
    service = CustomerActivityService(db)
    success = await service.delete_activity(activity_id, current_user.organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return {"message": "Activity deleted successfully"}


@router.get("/reports/activity-summary")
async def get_activity_summary(
    customer_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """活動サマリーレポート"""
    service = CustomerActivityService(db)
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    summary = await service.get_activity_summary(
        organization_id=current_user.organization_id,
        customer_id=customer_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    return summary


@router.get("/upcoming/next-actions")
async def get_upcoming_actions(
    user_id: Optional[int] = None,
    days_ahead: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """今後のアクション予定"""
    service = CustomerActivityService(db)
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    actions = await service.get_upcoming_actions(
        organization_id=current_user.organization_id,
        user_id=user_id or current_user.id,
        days_ahead=days_ahead,
    )
    return actions


@router.put("/{activity_id}/complete")
async def complete_activity(
    activity_id: int,
    outcome: Optional[str] = None,
    next_action: Optional[str] = None,
    next_action_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """活動完了"""
    service = CustomerActivityService(db)
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    activity = await service.complete_activity(
        activity_id=activity_id,
        organization_id=current_user.organization_id,
        outcome=outcome,
        next_action=next_action,
        next_action_date=next_action_date,
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return activity
