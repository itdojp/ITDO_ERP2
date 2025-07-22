from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.core.database_simple import get_db
from app.models.sales_v20 import SalesOrder, SalesOrderItem
from pydantic import BaseModel

router = APIRouter()

class OrderItemCreate(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    discount_percent: float = 0.0

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    items: List[OrderItemCreate]
    notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float
    discount_percent: float

    class Config:
        orm_mode = True

class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_email: Optional[str] = None
    order_date: str
    status: str
    total_amount: float
    tax_amount: float
    items: List[OrderItemResponse] = []

    class Config:
        orm_mode = True

@router.post("/sales/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Generate order number
    order_number = f"SO-{uuid.uuid4().hex[:8].upper()}"
    
    # Create order
    db_order = SalesOrder(
        id=str(uuid.uuid4()),
        order_number=order_number,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        notes=order.notes
    )
    
    db.add(db_order)
    db.flush()  # Get the ID
    
    # Create order items and calculate totals
    total_amount = 0.0
    order_items = []
    
    for item in order.items:
        line_total = item.quantity * item.unit_price
        if item.discount_percent > 0:
            line_total = line_total * (1 - item.discount_percent / 100)
        
        db_item = SalesOrderItem(
            id=str(uuid.uuid4()),
            order_id=db_order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=line_total,
            discount_percent=item.discount_percent
        )
        
        db.add(db_item)
        order_items.append(db_item)
        total_amount += line_total
    
    # Update order totals
    db_order.total_amount = total_amount
    db_order.tax_amount = total_amount * 0.1  # 10% tax
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

@router.get("/sales/orders", response_model=List[OrderResponse])
def list_orders(
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SalesOrder)
    
    if status:
        query = query.filter(SalesOrder.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    return orders

@router.get("/sales/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Load items
    items = db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order_id).all()
    order.items = items
    
    return order

@router.put("/sales/orders/{order_id}/status")
def update_order_status(order_id: str, status: str, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    order.status = status
    db.commit()
    
    return {"message": f"Order status updated to {status}", "order_id": order_id}