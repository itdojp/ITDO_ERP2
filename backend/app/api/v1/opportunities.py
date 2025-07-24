"""
Opportunity API endpoints for CRM functionality.
商談管理APIエンドポイント（CRM機能）
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.customer import (
    OpportunityAnalytics,
    OpportunityCreate,
    OpportunityDetailResponse,
    OpportunityResponse,
    OpportunityUpdate,
)
from app.services.opportunity_service import OpportunityService

router = APIRouter()


@router.get("/", response_model=List[OpportunityResponse])
async def get_opportunities(
    customer_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[OpportunityResponse]:
    """商談一覧取得"""
    service = OpportunityService(db)
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=400, detail="User must belong to an organization"
        )
    opportunities = await service.get_opportunities(
        organization_id=current_user.organization_id,
        customer_id=customer_id,
        owner_id=owner_id,
        status=status,
        stage=stage,
        min_value=min_value,
        max_value=max_value,
        skip=skip,
        limit=limit,
    )
    return opportunities


@router.get("/{opportunity_id}", response_model=OpportunityDetailResponse)
async def get_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OpportunityDetailResponse:
    """商談詳細取得"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    opportunity = await service.get_opportunity_by_id(
        opportunity_id, current_user.organization_id
    )
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opportunity


@router.post("/", response_model=OpportunityResponse)
async def create_opportunity(
    opportunity_data: OpportunityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OpportunityResponse:
    """商談新規作成"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    opportunity = await service.create_opportunity(
        opportunity_data, current_user.organization_id
    )
    return opportunity


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: int,
    opportunity_data: OpportunityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OpportunityResponse:
    """商談更新"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    opportunity = await service.update_opportunity(
        opportunity_id, opportunity_data, current_user.organization_id
    )
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opportunity


@router.delete("/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """商談削除（論理削除）"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    success = await service.delete_opportunity(
        opportunity_id, current_user.organization_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return {"message": "Opportunity deleted successfully"}


@router.put("/{opportunity_id}/stage")
async def update_opportunity_stage(
    opportunity_id: int,
    stage: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OpportunityResponse:
    """商談ステージ更新"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    opportunity = await service.update_stage(
        opportunity_id, stage, current_user.organization_id
    )
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opportunity


@router.put("/{opportunity_id}/close")
async def close_opportunity(
    opportunity_id: int,
    close_status: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OpportunityResponse:
    """商談クローズ"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    opportunity = await service.close_opportunity(
        opportunity_id, close_status, current_user.organization_id, reason=reason
    )
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opportunity


@router.get("/analytics/summary", response_model=OpportunityAnalytics)
async def get_opportunity_analytics(
    owner_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OpportunityAnalytics:
    """商談分析サマリー"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    analytics = await service.get_opportunity_analytics(
        organization_id=current_user.organization_id,
        owner_id=owner_id,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
    )
    return analytics


@router.get("/pipeline/forecast")
async def get_pipeline_forecast(
    owner_id: Optional[int] = None,
    quarters: int = Query(4, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """パイプライン予測"""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    service = OpportunityService(db)
    forecast = await service.get_pipeline_forecast(
        organization_id=current_user.organization_id,
        owner_id=owner_id,
        quarters=quarters,
    )
    return forecast


@router.get("/reports/conversion-rate")
async def get_conversion_rate_report(
    owner_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """成約率レポート"""
    # Ensure organization_id is not None
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization",
        )

    service = OpportunityService(db)
    report = await service.get_conversion_rate_report(
        organization_id=current_user.organization_id,
        owner_id=owner_id,
        start_date=start_date,
        end_date=end_date,
    )
    return report
