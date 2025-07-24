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
    """
    Retrieve a paginated list of customers with advanced filtering capabilities.

    This endpoint provides comprehensive customer data with multiple filtering options:
    - Filter by customer status (active, inactive, prospect, archived)
    - Filter by customer type (individual, corporate, government, non-profit)
    - Filter by industry sector
    - Filter by assigned sales representative
    - Full-text search across customer names and descriptions

    **Query Parameters:**
    - `status`: Customer status filter (active, inactive, prospect, archived)
    - `customer_type`: Type of customer (individual, corporate, government)
    - `industry`: Industry sector (technology, healthcare, finance, etc.)
    - `sales_rep_id`: ID of assigned sales representative
    - `search`: Text search across customer names and descriptions
    - `skip`: Number of records to skip for pagination (default: 0)
    - `limit`: Maximum number of records to return (1-1000, default: 100)

    **Example Request:**
    ```
    GET /customers/?status=active&industry=technology&limit=50&skip=0
    ```

    **Response Example:**
    ```json
    [
        {
            "id": 1,
            "name": "Tech Innovations Inc.",
            "customer_code": "CUST-001",
            "customer_type": "corporate",
            "industry": "technology",
            "status": "active",
            "contact_email": "contact@techinnovations.com",
            "phone": "+1-555-0123",
            "address": {
                "street": "123 Tech Street",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94105",
                "country": "USA"
            },
            "sales_rep": {
                "id": 5,
                "name": "Sarah Johnson",
                "email": "sarah.johnson@company.com"
            },
            "total_revenue": 125000.00,
            "last_interaction": "2024-03-15T14:30:00Z",
            "created_at": "2023-06-01T09:00:00Z",
            "updated_at": "2024-03-15T14:30:00Z"
        }
    ]
    ```

    **Error Responses:**
    - `400 Bad Request`: Invalid query parameters
    - `401 Unauthorized`: Authentication required
    - `422 Unprocessable Entity`: Parameter validation errors
    """
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
    customer = await service.get_customer_by_id(
        customer_id, current_user.organization_id
    )
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
    """
    Create a new customer record with comprehensive profile information.

    This endpoint creates a complete customer profile including:
    - Basic company/individual information
    - Contact details and communication preferences
    - Industry classification and business details
    - Sales representative assignment
    - Initial relationship status and notes

    **Request Body Example:**
    ```json
    {
        "name": "Global Manufacturing Corp",
        "customer_type": "corporate",
        "industry": "manufacturing",
        "contact_email": "procurement@globalmanuf.com",
        "phone": "+1-555-0199",
        "website": "https://www.globalmanuf.com",
        "address": {
            "street": "456 Industrial Way",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
            "country": "USA"
        },
        "billing_address": {
            "street": "789 Finance Blvd",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48202",
            "country": "USA"
        },
        "sales_rep_id": 3,
        "annual_revenue": 5000000.00,
        "employee_count": 250,
        "payment_terms": "NET_30",
        "credit_limit": 100000.00,
        "tags": ["enterprise", "manufacturing", "priority"]
    }
    ```

    **Response Example:**
    ```json
    {
        "id": 42,
        "customer_code": "CUST-042",
        "name": "Global Manufacturing Corp",
        "customer_type": "corporate",
        "industry": "manufacturing",
        "status": "prospect",
        "contact_email": "procurement@globalmanuf.com",
        "phone": "+1-555-0199",
        "website": "https://www.globalmanuf.com",
        "sales_rep": {
            "id": 3,
            "name": "Michael Chen",
            "email": "michael.chen@company.com"
        },
        "created_at": "2024-03-20T10:15:30Z",
        "updated_at": "2024-03-20T10:15:30Z"
    }
    ```

    **Validation Rules:**
    - `name`: Required, 1-255 characters
    - `contact_email`: Must be valid email format
    - `customer_type`: Must be one of: individual, corporate, government, non-profit
    - `phone`: Optional, valid phone number format
    - `industry`: Must be from predefined industry list

    **Error Responses:**
    - `400 Bad Request`: Invalid customer data or duplicate email
    - `401 Unauthorized`: Authentication required
    - `422 Unprocessable Entity`: Validation errors
    """
    service = CustomerService(db)
    customer = await service.create_customer(
        customer_data, current_user.organization_id
    )
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
