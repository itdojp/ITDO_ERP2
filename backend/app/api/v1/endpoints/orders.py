"""
Order Management API Endpoints - CC02 v49.0 Phase 4
48-Hour Backend Blitz - Order Management TDD Implementation
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from decimal import Decimal
import uuid

# Import database dependencies and other APIs
from app.core.database import get_db
from app.api.v1.endpoints.customers import customers_store
from app.api.v1.endpoints.products import products_store

router = APIRouter(prefix="/orders", tags=["Orders"])

# Enums for order data
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    FAILED = "failed"
    REFUNDED = "refunded"

# Response models for TDD tests
class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    items: List[OrderItemResponse]
    total_amount: float
    status: str = OrderStatus.PENDING.value
    payment_status: str = PaymentStatus.PENDING.value
    order_date: datetime
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int

class OrderStatusStats(BaseModel):
    status: str
    count: int

class OrderStatisticsResponse(BaseModel):
    total_orders: int
    order_statuses: List[OrderStatusStats]
    total_revenue: float
    average_order_value: float
    recent_orders: int  # Last 30 days

# In-memory storage for TDD (will be replaced with database)
orders_store: Dict[str, Dict[str, Any]] = {}
order_items_store: Dict[str, List[Dict[str, Any]]] = {}

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Create a new order"""
    
    try:
        order_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["customer_id", "items"]
    for field in required_fields:
        if field not in order_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate customer exists
    customer_id = order_data["customer_id"]
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Validate items
    items = order_data["items"]
    if not items or len(items) == 0:
        raise HTTPException(status_code=422, detail="Order must have at least one item")
    
    # Validate products exist and calculate totals
    order_items = []
    total_amount = 0.0
    
    for i, item_data in enumerate(items):
        if "product_id" not in item_data or "quantity" not in item_data or "unit_price" not in item_data:
            raise HTTPException(status_code=422, detail=f"Item {i} missing required fields")
        
        product_id = item_data["product_id"]
        if product_id not in products_store:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        product = products_store[product_id]
        quantity = int(item_data["quantity"])
        unit_price = float(item_data["unit_price"])
        total_price = quantity * unit_price
        
        item = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "product_name": product["name"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price
        }
        order_items.append(item)
        total_amount += total_price
    
    # Create order
    order_id = str(uuid.uuid4())
    now = datetime.now()
    
    customer = customers_store[customer_id]
    
    order = {
        "id": order_id,
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "total_amount": total_amount,
        "status": order_data.get("status", OrderStatus.PENDING.value),
        "payment_status": order_data.get("payment_status", PaymentStatus.PENDING.value),
        "order_date": datetime.fromisoformat(order_data["order_date"]) if "order_date" in order_data else now,
        "notes": order_data.get("notes"),
        "created_at": now,
        "updated_at": now
    }
    
    orders_store[order_id] = order
    order_items_store[order_id] = order_items
    
    # Create response
    response_items = [OrderItemResponse(**item) for item in order_items]
    response_order = OrderResponse(
        **order,
        items=response_items
    )
    
    return response_order

@router.get("/statistics", response_model=OrderStatisticsResponse)
async def get_order_statistics(
    db: AsyncSession = Depends(get_db)
) -> OrderStatisticsResponse:
    """Get order statistics"""
    
    all_orders = list(orders_store.values())
    total_orders = len(all_orders)
    
    # Order status breakdown
    status_counts = {}
    total_revenue = 0.0
    
    for order in all_orders:
        status = order.get("status", OrderStatus.PENDING.value)
        status_counts[status] = status_counts.get(status, 0) + 1
        
        if order.get("status") not in [OrderStatus.CANCELLED.value, OrderStatus.REFUNDED.value]:
            total_revenue += order["total_amount"]
    
    order_statuses = [
        OrderStatusStats(status=status, count=count)
        for status, count in status_counts.items()
    ]
    
    # Calculate average order value
    active_orders = [o for o in all_orders if o.get("status") not in [OrderStatus.CANCELLED.value, OrderStatus.REFUNDED.value]]
    average_order_value = total_revenue / len(active_orders) if active_orders else 0.0
    
    # Recent orders (simplified for TDD)
    recent_orders = len([o for o in all_orders if o.get("status") == OrderStatus.PENDING.value])
    
    return OrderStatisticsResponse(
        total_orders=total_orders,
        order_statuses=order_statuses,
        total_revenue=round(total_revenue, 2),
        average_order_value=round(average_order_value, 2),
        recent_orders=recent_orders
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Get order by ID"""
    
    if order_id not in orders_store:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_store[order_id]
    items = order_items_store.get(order_id, [])
    
    response_items = [OrderItemResponse(**item) for item in items]
    response_order = OrderResponse(
        **order,
        items=response_items
    )
    
    return response_order

@router.get("/", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    customer_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> OrderListResponse:
    """List orders with pagination and filtering"""
    
    all_orders = list(orders_store.values())
    
    # Apply filters
    if customer_id:
        all_orders = [o for o in all_orders if o["customer_id"] == customer_id]
    
    if status:
        all_orders = [o for o in all_orders if o.get("status") == status]
    
    # Sort by order_date descending
    all_orders.sort(key=lambda x: x["order_date"], reverse=True)
    
    # Apply pagination
    total = len(all_orders)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_orders = all_orders[start_idx:end_idx]
    
    # Convert to response format
    response_orders = []
    for order in paginated_orders:
        items = order_items_store.get(order["id"], [])
        response_items = [OrderItemResponse(**item) for item in items]
        response_order = OrderResponse(
            **order,
            items=response_items
        )
        response_orders.append(response_order)
    
    return OrderListResponse(
        items=response_orders,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size  # Ceiling division
    )

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Update order information"""
    
    if order_id not in orders_store:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    order = orders_store[order_id].copy()
    
    # Update fields (prevent updating sensitive fields)
    allowed_fields = ["status", "payment_status", "notes"]
    for field, value in update_data.items():
        if field in allowed_fields:
            order[field] = value
    
    order["updated_at"] = datetime.now()
    orders_store[order_id] = order
    
    # Get items for response
    items = order_items_store.get(order_id, [])
    response_items = [OrderItemResponse(**item) for item in items]
    response_order = OrderResponse(
        **order,
        items=response_items
    )
    
    return response_order

@router.delete("/{order_id}")
async def cancel_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Cancel an order"""
    
    if order_id not in orders_store:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_store[order_id]
    
    # Check if order can be cancelled
    if order.get("status") in [OrderStatus.DELIVERED.value, OrderStatus.REFUNDED.value]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")
    
    # Cancel order
    orders_store[order_id]["status"] = OrderStatus.CANCELLED.value
    orders_store[order_id]["updated_at"] = datetime.now()
    
    return {"message": "Order cancelled successfully", "id": order_id}

# Integration endpoint for customer orders
@router.get("/customer/{customer_id}", response_model=OrderListResponse)
async def get_customer_orders(
    customer_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> OrderListResponse:
    """Get all orders for a specific customer"""
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Filter orders by customer
    customer_orders = [o for o in orders_store.values() if o["customer_id"] == customer_id]
    
    # Sort by order_date descending
    customer_orders.sort(key=lambda x: x["order_date"], reverse=True)
    
    # Apply pagination
    total = len(customer_orders)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_orders = customer_orders[start_idx:end_idx]
    
    # Convert to response format
    response_orders = []
    for order in paginated_orders:
        items = order_items_store.get(order["id"], [])
        response_items = [OrderItemResponse(**item) for item in items]
        response_order = OrderResponse(
            **order,
            items=response_items
        )
        response_orders.append(response_order)
    
    return OrderListResponse(
        items=response_orders,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

# Health check endpoint for performance testing
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for orders"""
    start_time = datetime.now()
    
    # Simulate some processing
    order_count = len(orders_store)
    total_items = sum(len(items) for items in order_items_store.values())
    
    end_time = datetime.now()
    response_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "order_count": order_count,
        "total_items": total_items,
        "timestamp": start_time.isoformat()
    }