import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItemBase(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class OrderItem(OrderItemBase):
    id: str
    line_total: float


class SalesOrderBase(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    items: List[OrderItemBase]


class SalesOrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[OrderStatus] = None


class SalesOrder(SalesOrderBase):
    id: str
    order_number: str
    status: OrderStatus
    items: List[OrderItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    created_at: datetime
    updated_at: datetime


# モックデータストア
sales_orders_db = {}
order_counter = 1000


@router.post("/sales-orders", response_model=SalesOrder, status_code=201)
async def create_sales_order(order: SalesOrderCreate):
    """売上オーダーを作成"""
    global order_counter
    order_counter += 1

    order_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # オーダーアイテムを処理
    processed_items = []
    subtotal = 0

    for item in order.items:
        item_id = str(uuid.uuid4())
        line_total = item.quantity * item.unit_price

        processed_item = {
            "id": item_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "line_total": line_total,
        }

        processed_items.append(processed_item)
        subtotal += line_total

    # 税金計算（10%）
    tax_amount = subtotal * 0.10
    total_amount = subtotal + tax_amount

    new_order = {
        "id": order_id,
        "order_number": f"SO-{order_counter:06d}",
        "status": OrderStatus.DRAFT,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "notes": order.notes,
        "items": processed_items,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "created_at": now,
        "updated_at": now,
    }

    sales_orders_db[order_id] = new_order
    return new_order


@router.get("/sales-orders", response_model=List[SalesOrder])
async def list_sales_orders(
    status: Optional[OrderStatus] = None,
    customer_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """売上オーダー一覧を取得"""
    orders = list(sales_orders_db.values())

    if status:
        orders = [o for o in orders if o["status"] == status]

    if customer_name:
        orders = [
            o for o in orders if customer_name.lower() in o["customer_name"].lower()
        ]

    # 作成日時で降順ソート
    orders.sort(key=lambda x: x["created_at"], reverse=True)

    return orders[skip : skip + limit]


@router.get("/sales-orders/{order_id}", response_model=SalesOrder)
async def get_sales_order(order_id: str):
    """売上オーダー詳細を取得"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="売上オーダーが見つかりません")
    return sales_orders_db[order_id]


@router.put("/sales-orders/{order_id}", response_model=SalesOrder)
async def update_sales_order(order_id: str, order_update: SalesOrderUpdate):
    """売上オーダーを更新"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="売上オーダーが見つかりません")

    order = sales_orders_db[order_id]
    update_data = order_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        order[field] = value

    order["updated_at"] = datetime.utcnow()
    return order


@router.post("/sales-orders/{order_id}/confirm")
async def confirm_sales_order(order_id: str):
    """売上オーダーを確定"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="売上オーダーが見つかりません")

    order = sales_orders_db[order_id]

    if order["status"] != OrderStatus.DRAFT:
        raise HTTPException(
            status_code=400, detail="確定できるのは下書き状態のオーダーのみです"
        )

    order["status"] = OrderStatus.CONFIRMED
    order["updated_at"] = datetime.utcnow()

    return {
        "message": f"オーダー {order['order_number']} が確定されました",
        "order": order,
    }


@router.post("/sales-orders/{order_id}/ship")
async def ship_sales_order(order_id: str, tracking_number: Optional[str] = None):
    """売上オーダーを出荷"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="売上オーダーが見つかりません")

    order = sales_orders_db[order_id]

    if order["status"] not in [OrderStatus.CONFIRMED, OrderStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail="出荷できるのは確定済みまたは処理中のオーダーのみです",
        )

    order["status"] = OrderStatus.SHIPPED
    order["updated_at"] = datetime.utcnow()

    if tracking_number:
        if "shipping_info" not in order:
            order["shipping_info"] = {}
        order["shipping_info"]["tracking_number"] = tracking_number

    return {
        "message": f"オーダー {order['order_number']} が出荷されました",
        "tracking_number": tracking_number,
    }


@router.post("/sales-orders/{order_id}/cancel")
async def cancel_sales_order(order_id: str, reason: Optional[str] = None):
    """売上オーダーをキャンセル"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="売上オーダーが見つかりません")

    order = sales_orders_db[order_id]

    if order["status"] in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
        raise HTTPException(
            status_code=400,
            detail="出荷済みまたは配達済みのオーダーはキャンセルできません",
        )

    order["status"] = OrderStatus.CANCELLED
    order["updated_at"] = datetime.utcnow()

    if reason:
        if "cancellation_info" not in order:
            order["cancellation_info"] = {}
        order["cancellation_info"]["reason"] = reason
        order["cancellation_info"]["cancelled_at"] = datetime.utcnow()

    return {
        "message": f"オーダー {order['order_number']} がキャンセルされました",
        "reason": reason,
    }


@router.get("/sales-orders/{order_id}/summary")
async def get_order_summary(order_id: str):
    """売上オーダーのサマリーを取得"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="売上オーダーが見つかりません")

    order = sales_orders_db[order_id]

    return {
        "order_number": order["order_number"],
        "status": order["status"],
        "customer_name": order["customer_name"],
        "total_items": len(order["items"]),
        "total_quantity": sum(item["quantity"] for item in order["items"]),
        "total_amount": order["total_amount"],
        "created_at": order["created_at"],
        "updated_at": order["updated_at"],
    }
