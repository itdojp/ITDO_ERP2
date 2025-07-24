from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.crud.purchasing_extended_v30 import (
    DuplicateError,
    InvalidStatusError,
    NotFoundError,
    PurchaseOrderCRUD,
    PurchaseReceiptCRUD,
    PurchaseRequestCRUD,
    SupplierCRUD,
    SupplierProductCRUD,
)
from app.schemas.purchasing_complete_v30 import (
    PurchaseAnalyticsResponse,
    PurchaseOrderCreate,
    PurchaseOrderListResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseReceiptCreate,
    PurchaseReceiptResponse,
    PurchaseRequestCreate,
    PurchaseRequestListResponse,
    PurchaseRequestResponse,
    PurchaseRequestUpdate,
    PurchaseStatsResponse,
    SupplierCreate,
    SupplierListResponse,
    SupplierProductCreate,
    SupplierProductResponse,
    SupplierResponse,
    SupplierUpdate,
)

router = APIRouter(prefix="/purchasing", tags=["purchasing"])


@router.post(
    "/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED
)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー作成"""
    try:
        supplier_crud = SupplierCRUD(db)
        return supplier_crud.create(supplier)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー詳細取得"""
    supplier_crud = SupplierCRUD(db)
    supplier = supplier_crud.get_by_id(supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
        )
    return supplier


@router.get("/suppliers", response_model=SupplierListResponse)
def list_suppliers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    is_approved: Optional[bool] = None,
    supplier_type: Optional[str] = None,
    supplier_category: Optional[str] = None,
    priority_level: Optional[str] = None,
    preferred_supplier: Optional[bool] = None,
    buyer_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー一覧取得"""
    skip = (page - 1) * per_page
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if is_approved is not None:
        filters["is_approved"] = is_approved
    if supplier_type:
        filters["supplier_type"] = supplier_type
    if supplier_category:
        filters["supplier_category"] = supplier_category
    if priority_level:
        filters["priority_level"] = priority_level
    if preferred_supplier is not None:
        filters["preferred_supplier"] = preferred_supplier
    if buyer_id:
        filters["buyer_id"] = buyer_id
    if search:
        filters["search"] = search

    supplier_crud = SupplierCRUD(db)
    suppliers, total = supplier_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return SupplierListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=suppliers
    )


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: str,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー情報更新"""
    try:
        supplier_crud = SupplierCRUD(db)
        return supplier_crud.update(supplier_id, supplier_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/requests",
    response_model=PurchaseRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_request(
    request: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買リクエスト作成"""
    request_crud = PurchaseRequestCRUD(db)
    return request_crud.create(request, current_user["sub"])


@router.get("/requests/{request_id}", response_model=PurchaseRequestResponse)
def get_purchase_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買リクエスト詳細取得"""
    request_crud = PurchaseRequestCRUD(db)
    request = request_crud.get_by_id(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase request not found"
        )
    return request


@router.get("/requests", response_model=PurchaseRequestListResponse)
def list_purchase_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    requester_id: Optional[str] = None,
    department_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    approval_status: Optional[str] = None,
    priority: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    amount_min: Optional[Decimal] = None,
    amount_max: Optional[Decimal] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買リクエスト一覧取得"""
    skip = (page - 1) * per_page
    filters = {}
    if requester_id:
        filters["requester_id"] = requester_id
    if department_id:
        filters["department_id"] = department_id
    if supplier_id:
        filters["supplier_id"] = supplier_id
    if status:
        filters["status"] = status
    if approval_status:
        filters["approval_status"] = approval_status
    if priority:
        filters["priority"] = priority
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if amount_min:
        filters["amount_min"] = amount_min
    if amount_max:
        filters["amount_max"] = amount_max

    request_crud = PurchaseRequestCRUD(db)
    requests, total = request_crud.get_multi(skip=skip, limit=per_page, filters=filters)

    pages = (total + per_page - 1) // per_page

    return PurchaseRequestListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=requests
    )


@router.put("/requests/{request_id}", response_model=PurchaseRequestResponse)
def update_purchase_request(
    request_id: str,
    request_update: PurchaseRequestUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買リクエスト更新"""
    try:
        request_crud = PurchaseRequestCRUD(db)
        return request_crud.update(request_id, request_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/requests/{request_id}/approve", response_model=PurchaseRequestResponse)
def approve_purchase_request(
    request_id: str,
    approved_budget: Decimal = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買リクエスト承認"""
    try:
        request_crud = PurchaseRequestCRUD(db)
        return request_crud.approve_request(
            request_id, current_user["sub"], approved_budget
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/requests/{request_id}/reject", response_model=PurchaseRequestResponse)
def reject_purchase_request(
    request_id: str,
    rejection_reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買リクエスト却下"""
    try:
        request_crud = PurchaseRequestCRUD(db)
        return request_crud.reject_request(
            request_id, current_user["sub"], rejection_reason
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED
)
def create_purchase_order(
    order: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買注文作成"""
    order_crud = PurchaseOrderCRUD(db)
    return order_crud.create(order, current_user["sub"])


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買注文詳細取得"""
    order_crud = PurchaseOrderCRUD(db)
    order = order_crud.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found"
        )
    return order


@router.get("/orders", response_model=PurchaseOrderListResponse)
def list_purchase_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = None,
    buyer_id: Optional[str] = None,
    status: Optional[str] = None,
    receipt_status: Optional[str] = None,
    payment_status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    amount_min: Optional[Decimal] = None,
    amount_max: Optional[Decimal] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買注文一覧取得"""
    skip = (page - 1) * per_page
    filters = {}
    if supplier_id:
        filters["supplier_id"] = supplier_id
    if buyer_id:
        filters["buyer_id"] = buyer_id
    if status:
        filters["status"] = status
    if receipt_status:
        filters["receipt_status"] = receipt_status
    if payment_status:
        filters["payment_status"] = payment_status
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if amount_min:
        filters["amount_min"] = amount_min
    if amount_max:
        filters["amount_max"] = amount_max

    order_crud = PurchaseOrderCRUD(db)
    orders, total = order_crud.get_multi(skip=skip, limit=per_page, filters=filters)

    pages = (total + per_page - 1) // per_page

    return PurchaseOrderListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=orders
    )


@router.put("/orders/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    order_id: str,
    order_update: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買注文更新"""
    try:
        order_crud = PurchaseOrderCRUD(db)
        return order_crud.update(order_id, order_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/orders/{order_id}/acknowledge", response_model=PurchaseOrderResponse)
def acknowledge_purchase_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買注文確認（サプライヤー受注確認）"""
    try:
        order_crud = PurchaseOrderCRUD(db)
        return order_crud.acknowledge_order(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/receipts",
    response_model=PurchaseReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_receipt(
    receipt: PurchaseReceiptCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買受領記録作成"""
    receipt_crud = PurchaseReceiptCRUD(db)
    return receipt_crud.create(receipt, current_user["sub"])


@router.get("/receipts/{receipt_id}", response_model=PurchaseReceiptResponse)
def get_purchase_receipt(
    receipt_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買受領記録詳細取得"""
    receipt_crud = PurchaseReceiptCRUD(db)
    receipt = receipt_crud.get_by_id(receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase receipt not found"
        )
    return receipt


@router.post(
    "/supplier-products",
    response_model=SupplierProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier_product(
    supplier_product: SupplierProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """サプライヤー商品関連作成"""
    try:
        supplier_product_crud = SupplierProductCRUD(db)
        return supplier_product_crud.create(supplier_product)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/analytics", response_model=PurchaseAnalyticsResponse)
def get_purchase_analytics(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """購買分析データ取得"""
    order_crud = PurchaseOrderCRUD(db)
    return order_crud.get_purchase_analytics(date_from, date_to)


@router.get("/stats", response_model=PurchaseStatsResponse)
def get_purchase_stats(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """購買統計取得"""
    from sqlalchemy import func

    from app.models.purchasing_extended import PurchaseOrder, PurchaseReceipt, Supplier

    # 基本統計
    total_suppliers = db.query(Supplier).count()
    active_suppliers = db.query(Supplier).filter(Supplier.is_active).count()
    total_purchase_orders = db.query(PurchaseOrder).count()

    # 今月の統計
    current_month = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    orders_this_month = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.created_at >= current_month)
        .count()
    )

    # 購買統計
    total_purchases = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.status != "cancelled"
    ).scalar() or Decimal("0")

    purchases_this_month = db.query(func.sum(PurchaseOrder.total_amount)).filter(
        PurchaseOrder.created_at >= current_month, PurchaseOrder.status != "cancelled"
    ).scalar() or Decimal("0")

    avg_order_value = (
        total_purchases / total_purchase_orders
        if total_purchase_orders > 0
        else Decimal("0")
    )

    # ステータス別統計
    status_stats = (
        db.query(PurchaseOrder.status, func.count(PurchaseOrder.id))
        .group_by(PurchaseOrder.status)
        .all()
    )
    by_status = {status: count for status, count in status_stats}

    # サプライヤータイプ別統計
    type_stats = (
        db.query(Supplier.supplier_type, func.sum(PurchaseOrder.total_amount))
        .join(PurchaseOrder)
        .filter(PurchaseOrder.status != "cancelled")
        .group_by(Supplier.supplier_type)
        .all()
    )
    by_supplier_type = {supplier_type: amount for supplier_type, amount in type_stats}

    # トップサプライヤー
    top_suppliers = (
        db.query(Supplier)
        .filter(Supplier.total_purchases > 0)
        .order_by(Supplier.total_purchases.desc())
        .limit(5)
        .all()
    )

    top_suppliers_data = [
        {
            "supplier_id": supplier.id,
            "name": supplier.name,
            "company_name": supplier.company_name,
            "total_purchases": supplier.total_purchases,
            "total_orders": supplier.total_orders,
            "overall_rating": supplier.overall_rating,
        }
        for supplier in top_suppliers
    ]

    # 保留中の受領
    pending_receipts = (
        db.query(PurchaseReceipt)
        .filter(PurchaseReceipt.inspection_status == "pending")
        .count()
    )

    # 遅延注文
    overdue_orders = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.promised_delivery_date < datetime.utcnow(),
            PurchaseOrder.status.in_(["sent", "acknowledged"]),
        )
        .count()
    )

    return PurchaseStatsResponse(
        total_suppliers=total_suppliers,
        active_suppliers=active_suppliers,
        total_purchase_orders=total_purchase_orders,
        orders_this_month=orders_this_month,
        total_purchases=total_purchases,
        purchases_this_month=purchases_this_month,
        avg_order_value=avg_order_value,
        by_status=by_status,
        by_supplier_type=by_supplier_type,
        top_suppliers=top_suppliers_data,
        pending_receipts=pending_receipts,
        overdue_orders=overdue_orders,
    )
