from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.crud.sales_extended_v30 import (
    CustomerCRUD,
    DuplicateError,
    InvalidStatusError,
    InvoiceCRUD,
    NotFoundError,
    PaymentCRUD,
    QuoteCRUD,
    SalesOrderCRUD,
    ShipmentCRUD,
)
from app.schemas.sales_complete_v30 import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
    InvoiceResponse,
    PaymentCreate,
    PaymentResponse,
    QuoteCreate,
    QuoteResponse,
    SalesAnalyticsResponse,
    SalesOrderCreate,
    SalesOrderListResponse,
    SalesOrderResponse,
    SalesOrderUpdate,
    SalesStatsResponse,
    ShipmentCreate,
    ShipmentResponse,
)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post(
    "/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED
)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客作成"""
    try:
        customer_crud = CustomerCRUD(db)
        return customer_crud.create(customer)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客詳細取得"""
    customer_crud = CustomerCRUD(db)
    customer = customer_crud.get_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return customer


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    customer_type: Optional[str] = None,
    customer_group: Optional[str] = None,
    is_vip: Optional[bool] = None,
    sales_rep_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客一覧取得"""
    skip = (page - 1) * per_page
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if customer_type:
        filters["customer_type"] = customer_type
    if customer_group:
        filters["customer_group"] = customer_group
    if is_vip is not None:
        filters["is_vip"] = is_vip
    if sales_rep_id:
        filters["sales_rep_id"] = sales_rep_id
    if search:
        filters["search"] = search

    customer_crud = CustomerCRUD(db)
    customers, total = customer_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return CustomerListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=customers
    )


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客情報更新"""
    try:
        customer_crud = CustomerCRUD(db)
        return customer_crud.update(customer_id, customer_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/orders", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED
)
def create_sales_order(
    order: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """販売注文作成"""
    order_crud = SalesOrderCRUD(db)
    return order_crud.create(order, current_user["sub"])


@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """販売注文詳細取得"""
    order_crud = SalesOrderCRUD(db)
    order = order_crud.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found"
        )
    return order


@router.get("/orders", response_model=SalesOrderListResponse)
def list_sales_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    sales_rep_id: Optional[str] = None,
    sales_channel: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    amount_min: Optional[Decimal] = None,
    amount_max: Optional[Decimal] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """販売注文一覧取得"""
    skip = (page - 1) * per_page
    filters = {}
    if customer_id:
        filters["customer_id"] = customer_id
    if status:
        filters["status"] = status
    if sales_rep_id:
        filters["sales_rep_id"] = sales_rep_id
    if sales_channel:
        filters["sales_channel"] = sales_channel
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if amount_min:
        filters["amount_min"] = amount_min
    if amount_max:
        filters["amount_max"] = amount_max

    order_crud = SalesOrderCRUD(db)
    orders, total = order_crud.get_multi(skip=skip, limit=per_page, filters=filters)

    pages = (total + per_page - 1) // per_page

    return SalesOrderListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=orders
    )


@router.put("/orders/{order_id}", response_model=SalesOrderResponse)
def update_sales_order(
    order_id: str,
    order_update: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """販売注文更新"""
    try:
        order_crud = SalesOrderCRUD(db)
        return order_crud.update(order_id, order_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{order_id}/confirm", response_model=SalesOrderResponse)
def confirm_sales_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """販売注文確定"""
    try:
        order_crud = SalesOrderCRUD(db)
        return order_crud.confirm_order(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED
)
def create_quote(
    quote: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """見積作成"""
    quote_crud = QuoteCRUD(db)
    return quote_crud.create(quote, current_user["sub"])


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """見積詳細取得"""
    quote_crud = QuoteCRUD(db)
    quote = quote_crud.get_by_id(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found"
        )
    return quote


@router.post(
    "/invoices/from-order/{order_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice_from_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """注文から請求書作成"""
    try:
        invoice_crud = InvoiceCRUD(db)
        return invoice_crud.create_from_order(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """請求書詳細取得"""
    invoice_crud = InvoiceCRUD(db)
    invoice = invoice_crud.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    return invoice


@router.post(
    "/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED
)
def record_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """支払記録作成"""
    try:
        payment_crud = PaymentCRUD(db)
        return payment_crud.create(payment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED
)
def create_shipment(
    shipment: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """出荷記録作成"""
    shipment_crud = ShipmentCRUD(db)
    return shipment_crud.create(shipment)


@router.get("/analytics", response_model=SalesAnalyticsResponse)
def get_sales_analytics(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """売上分析データ取得"""
    order_crud = SalesOrderCRUD(db)
    return order_crud.get_sales_analytics(date_from, date_to)


@router.get("/stats", response_model=SalesStatsResponse)
def get_sales_stats(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """売上統計取得"""
    from sqlalchemy import func

    from app.models.sales_extended import Customer, SalesOrder

    # 基本統計
    total_customers = db.query(Customer).count()
    active_customers = db.query(Customer).filter(Customer.is_active).count()
    total_orders = db.query(SalesOrder).count()

    # 今月の統計
    current_month = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    orders_this_month = (
        db.query(SalesOrder).filter(SalesOrder.created_at >= current_month).count()
    )

    # 売上統計
    total_sales = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.status != "cancelled"
    ).scalar() or Decimal("0")

    sales_this_month = db.query(func.sum(SalesOrder.total_amount)).filter(
        SalesOrder.created_at >= current_month, SalesOrder.status != "cancelled"
    ).scalar() or Decimal("0")

    avg_order_value = total_sales / total_orders if total_orders > 0 else Decimal("0")

    # ステータス別統計
    status_stats = (
        db.query(SalesOrder.status, func.count(SalesOrder.id))
        .group_by(SalesOrder.status)
        .all()
    )
    by_status = {status: count for status, count in status_stats}

    # チャネル別統計
    channel_stats = (
        db.query(SalesOrder.sales_channel, func.sum(SalesOrder.total_amount))
        .filter(SalesOrder.status != "cancelled")
        .group_by(SalesOrder.sales_channel)
        .all()
    )
    by_channel = {channel: amount for channel, amount in channel_stats}

    # トップ顧客
    top_customers = (
        db.query(Customer)
        .filter(Customer.total_sales > 0)
        .order_by(Customer.total_sales.desc())
        .limit(5)
        .all()
    )

    top_customers_data = [
        {
            "customer_id": customer.id,
            "name": customer.name,
            "company_name": customer.company_name,
            "total_sales": customer.total_sales,
            "total_orders": customer.total_orders,
        }
        for customer in top_customers
    ]

    return SalesStatsResponse(
        total_customers=total_customers,
        active_customers=active_customers,
        total_orders=total_orders,
        orders_this_month=orders_this_month,
        total_sales=total_sales,
        sales_this_month=sales_this_month,
        avg_order_value=avg_order_value,
        by_status=by_status,
        by_channel=by_channel,
        top_customers=top_customers_data,
    )
