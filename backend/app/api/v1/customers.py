"""
Customer API endpoints for CRM functionality.
顧客管理APIエンドポイント（CRM機能）
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.customer import (
    CustomerAnalytics,
    CustomerBulkCreate,
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService

router = APIRouter()


@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    status: Optional[str] = None,
    customer_type: Optional[str] = None,
    industry: Optional[str] = None,
    sales_rep_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客一覧取得"""
    service = CustomerService(db)
    customers = await service.get_customers(
        organization_id=current_user.organization_id,
        status=status,
        customer_type=customer_type,
        industry=industry,
        sales_rep_id=sales_rep_id,
        search=search,
        skip=skip,
        limit=limit,
    )
    return customers


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客詳細取得"""
    service = CustomerService(db)
    customer = await service.get_customer_by_id(customer_id, current_user.organization_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return customer


@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客新規作成"""
    service = CustomerService(db)
    customer = await service.create_customer(customer_data, current_user.organization_id)
    return customer


@router.post("/bulk", response_model=List[CustomerResponse])
async def create_customers_bulk(
    customers_data: CustomerBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客一括作成"""
    service = CustomerService(db)
    customers = await service.create_customers_bulk(
        customers_data, current_user.organization_id
    )
    return customers


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客更新"""
    service = CustomerService(db)
    customer = await service.update_customer(
        customer_id, customer_data, current_user.organization_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客削除（論理削除）"""
    service = CustomerService(db)
    success = await service.delete_customer(customer_id, current_user.organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return {"message": "Customer deleted successfully"}


@router.get("/analytics/summary", response_model=CustomerAnalytics)
async def get_customer_analytics(
    industry: Optional[str] = None,
    sales_rep_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客分析サマリー"""
    service = CustomerService(db)
    analytics = await service.get_customer_analytics(
        organization_id=current_user.organization_id,
        industry=industry,
        sales_rep_id=sales_rep_id,
    )
    return analytics


@router.put("/{customer_id}/assign-sales-rep")
async def assign_sales_rep(
    customer_id: int,
    sales_rep_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """営業担当者アサイン"""
    service = CustomerService(db)
    success = await service.assign_sales_rep(
        customer_id, sales_rep_id, current_user.organization_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return {"message": "Sales representative assigned successfully"}


@router.get("/{customer_id}/sales-summary")
async def get_customer_sales_summary(
    customer_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """顧客売上サマリー"""
    service = CustomerService(db)
    summary = await service.get_sales_summary(
        customer_id,
        current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return summary
