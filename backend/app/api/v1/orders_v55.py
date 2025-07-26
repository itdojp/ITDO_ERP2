"""
CC02 v55.0 Order Management API
Enterprise-grade Order Processing and Management System
Day 1 of 7-day intensive backend development
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.customer import Customer
from app.models.inventory import InventoryItem
from app.models.order import (
    Order,
    OrderAddress,
    OrderDiscount,
    OrderHistory,
    OrderItem,
    OrderPayment,
    OrderShipment,
    QuoteItem,
    QuoteRequest,
)
from app.models.product import ProductVariant
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["orders-v55"])


# Enums
class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    ON_HOLD = "on_hold"


class OrderType(str, Enum):
    SALE = "sale"
    RETURN = "return"
    EXCHANGE = "exchange"
    SAMPLE = "sample"
    INTERNAL = "internal"
    TRANSFER = "transfer"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    PREPARED = "prepared"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    LOST = "lost"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BUY_X_GET_Y = "buy_x_get_y"
    FREE_SHIPPING = "free_shipping"


class TaxType(str, Enum):
    SALES_TAX = "sales_tax"
    VAT = "vat"
    GST = "gst"
    EXCISE = "excise"
    IMPORT_DUTY = "import_duty"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


# Request/Response Models
class OrderItemCreate(BaseModel):
    product_variant_id: UUID
    quantity: int = Field(..., ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    discount_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_percentage: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    notes: Optional[str] = Field(None, max_length=500)


class OrderItemResponse(BaseModel):
    id: UUID
    product_variant_id: UUID
    product_name: str
    variant_name: Optional[str]
    sku: str
    quantity: int
    unit_price: Decimal
    discount_percentage: Optional[Decimal]
    discount_amount: Decimal
    tax_percentage: Optional[Decimal]
    tax_amount: Decimal
    line_total: Decimal
    notes: Optional[str]
    availability_status: str
    estimated_delivery: Optional[date]

    class Config:
        from_attributes = True


class OrderAddressCreate(BaseModel):
    address_type: str = Field(..., regex="^(billing|shipping)$")
    line1: str = Field(..., min_length=1, max_length=200)
    line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)
    contact_name: str = Field(..., min_length=1, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)


class OrderAddressResponse(BaseModel):
    id: UUID
    address_type: str
    line1: str
    line2: Optional[str]
    city: str
    state: Optional[str]
    postal_code: str
    country: str
    contact_name: str
    contact_phone: Optional[str]
    full_address: str

    class Config:
        from_attributes = True


class OrderDiscountCreate(BaseModel):
    discount_type: DiscountType
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    percentage: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    applies_to: str = Field(default="order", regex="^(order|shipping|item)$")
    item_id: Optional[UUID] = None

    @validator("percentage", "amount")
    def validate_discount_value(cls, v, values, field) -> dict:
        discount_type = values.get("discount_type")
        if (
            discount_type == DiscountType.PERCENTAGE
            and field.name == "percentage"
            and v is None
        ):
            raise ValueError("Percentage is required for percentage discount type")
        elif (
            discount_type == DiscountType.FIXED_AMOUNT
            and field.name == "amount"
            and v is None
        ):
            raise ValueError("Amount is required for fixed amount discount type")
        return v


class OrderDiscountResponse(BaseModel):
    id: UUID
    discount_type: DiscountType
    name: str
    code: Optional[str]
    percentage: Optional[Decimal]
    amount: Decimal
    applies_to: str
    item_id: Optional[UUID]
    calculated_amount: Decimal

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    customer_id: UUID
    order_type: OrderType = Field(default=OrderType.SALE)
    priority: Priority = Field(default=Priority.NORMAL)
    reference_number: Optional[str] = Field(None, max_length=100)
    po_number: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1"), ge=0, decimal_places=6)
    requested_delivery_date: Optional[date] = None
    special_instructions: Optional[str] = Field(None, max_length=1000)
    internal_notes: Optional[str] = Field(None, max_length=1000)
    items: List[OrderItemCreate] = Field(..., min_items=1)
    billing_address: OrderAddressCreate
    shipping_address: Optional[OrderAddressCreate] = None
    discounts: List[OrderDiscountCreate] = Field(default_factory=list)

    @validator("items")
    def validate_items(cls, v) -> dict:
        if not v:
            raise ValueError("At least one item is required")

        # Check for duplicate product variants
        variant_ids = [item.product_variant_id for item in v]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("Duplicate product variants in order items")

        return v


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    priority: Optional[Priority] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    po_number: Optional[str] = Field(None, max_length=100)
    requested_delivery_date: Optional[date] = None
    special_instructions: Optional[str] = Field(None, max_length=1000)
    internal_notes: Optional[str] = Field(None, max_length=1000)


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    customer_id: UUID
    customer_name: str
    order_type: OrderType
    status: OrderStatus
    payment_status: PaymentStatus
    shipment_status: ShipmentStatus
    priority: Priority
    reference_number: Optional[str]
    po_number: Optional[str]
    currency: str
    exchange_rate: Decimal
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    shipping_total: Decimal
    total_amount: Decimal
    requested_delivery_date: Optional[date]
    estimated_delivery_date: Optional[date]
    shipped_date: Optional[datetime]
    delivered_date: Optional[datetime]
    special_instructions: Optional[str]
    internal_notes: Optional[str]
    items: List[OrderItemResponse]
    billing_address: OrderAddressResponse
    shipping_address: Optional[OrderAddressResponse]
    discounts: List[OrderDiscountResponse]
    payment_terms: Optional[str]
    sales_rep: Optional[str]
    order_source: Optional[str]
    tracking_numbers: List[str]
    created_by: UUID
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    id: UUID
    order_number: str
    customer_name: str
    status: OrderStatus
    payment_status: PaymentStatus
    priority: Priority
    total_amount: Decimal
    currency: str
    requested_delivery_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderShipmentCreate(BaseModel):
    carrier: str = Field(..., min_length=1, max_length=100)
    service_type: str = Field(..., min_length=1, max_length=100)
    tracking_number: str = Field(..., min_length=1, max_length=100)
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    dimensions: Optional[Dict[str, float]] = None
    shipping_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    estimated_delivery: Optional[date] = None
    items: List[Dict[str, Any]] = Field(..., min_items=1)  # {item_id, quantity}
    notes: Optional[str] = Field(None, max_length=500)


class OrderShipmentResponse(BaseModel):
    id: UUID
    order_id: UUID
    carrier: str
    service_type: str
    tracking_number: str
    status: ShipmentStatus
    weight: Optional[Decimal]
    dimensions: Optional[Dict[str, float]]
    shipping_cost: Optional[Decimal]
    shipped_date: Optional[datetime]
    estimated_delivery: Optional[date]
    delivered_date: Optional[datetime]
    items_count: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderPaymentCreate(BaseModel):
    payment_method: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    transaction_id: Optional[str] = Field(None, max_length=100)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class OrderPaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    payment_method: str
    amount: Decimal
    status: PaymentStatus
    transaction_id: Optional[str]
    reference_number: Optional[str]
    processed_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteRequestCreate(BaseModel):
    customer_id: UUID
    valid_until: date
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)
    items: List[OrderItemCreate] = Field(..., min_items=1)


class QuoteResponse(BaseModel):
    id: UUID
    quote_number: str
    customer_id: UUID
    customer_name: str
    status: str
    subtotal: Decimal
    tax_total: Decimal
    total_amount: Decimal
    currency: str
    valid_until: date
    notes: Optional[str]
    items: List[OrderItemResponse]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Helper Functions
async def generate_order_number(db: AsyncSession, prefix: str = "ORD") -> str:
    """Generate unique order number"""
    # Get current date for prefix
    today = datetime.utcnow().strftime("%Y%m%d")
    full_prefix = f"{prefix}{today}"

    # Get the highest existing order number for today
    result = await db.execute(
        select(func.max(Order.order_number)).where(
            Order.order_number.like(f"{full_prefix}%")
        )
    )

    max_number = result.scalar()

    if max_number:
        try:
            sequence = int(max_number.replace(full_prefix, ""))
            new_sequence = sequence + 1
        except ValueError:
            new_sequence = 1
    else:
        new_sequence = 1

    return f"{full_prefix}{new_sequence:04d}"


async def validate_customer_exists(db: AsyncSession, customer_id: UUID) -> bool:
    """Validate that a customer exists and is active"""
    result = await db.execute(
        select(Customer).where(
            and_(Customer.id == customer_id, Customer.status.in_(["active", "vip"]))
        )
    )
    return result.scalar_one_or_none() is not None


async def validate_product_variant_exists(db: AsyncSession, variant_id: UUID) -> bool:
    """Validate that a product variant exists"""
    result = await db.execute(
        select(ProductVariant).where(ProductVariant.id == variant_id)
    )
    return result.scalar_one_or_none() is not None


async def check_inventory_availability(
    db: AsyncSession, variant_id: UUID, quantity: int
) -> Dict[str, Any]:
    """Check inventory availability for a product variant"""
    result = await db.execute(
        select(
            InventoryItem,
            func.sum(InventoryItem.quantity - InventoryItem.reserved_quantity),
        )
        .where(InventoryItem.product_variant_id == variant_id)
        .group_by(InventoryItem.product_variant_id)
    )

    row = result.first()
    if not row:
        return {"available": False, "total_available": 0, "status": "not_in_stock"}

    total_available = row[1] or 0

    if total_available >= quantity:
        return {
            "available": True,
            "total_available": total_available,
            "status": "in_stock",
        }
    elif total_available > 0:
        return {
            "available": False,
            "total_available": total_available,
            "status": "insufficient_stock",
        }
    else:
        return {"available": False, "total_available": 0, "status": "out_of_stock"}


async def reserve_inventory(db: AsyncSession, variant_id: UUID, quantity: int) -> bool:
    """Reserve inventory for an order"""
    # Find inventory items with available stock
    result = await db.execute(
        select(InventoryItem)
        .where(
            and_(
                InventoryItem.product_variant_id == variant_id,
                InventoryItem.quantity - InventoryItem.reserved_quantity > 0,
            )
        )
        .order_by(InventoryItem.created_at)  # FIFO
    )

    items = result.scalars().all()
    remaining_to_reserve = quantity

    for item in items:
        if remaining_to_reserve <= 0:
            break

        available = item.quantity - item.reserved_quantity
        to_reserve = min(available, remaining_to_reserve)

        item.reserved_quantity += to_reserve
        remaining_to_reserve -= to_reserve

    return remaining_to_reserve == 0


async def calculate_order_totals(
    items: List[OrderItem], discounts: List[OrderDiscount]
) -> Dict[str, Decimal]:
    """Calculate order totals including taxes and discounts"""
    subtotal = Decimal("0")
    total_discount = Decimal("0")
    total_tax = Decimal("0")

    # Calculate subtotal
    for item in items:
        line_total = item.quantity * item.unit_price
        subtotal += line_total

    # Apply discounts
    for discount in discounts:
        if discount.discount_type == DiscountType.PERCENTAGE:
            discount_amount = subtotal * (discount.percentage / 100)
        else:
            discount_amount = discount.amount or Decimal("0")

        total_discount += discount_amount

    # Calculate tax (simplified - would be more complex in production)
    taxable_amount = subtotal - total_discount
    total_tax = taxable_amount * Decimal("0.1")  # 10% tax rate

    total_amount = subtotal - total_discount + total_tax

    return {
        "subtotal": subtotal,
        "discount_total": total_discount,
        "tax_total": total_tax,
        "total_amount": total_amount,
    }


async def update_order_status_history(
    db: AsyncSession,
    order_id: UUID,
    old_status: str,
    new_status: str,
    user_id: UUID,
    notes: Optional[str] = None,
):
    """Record order status change in history"""
    history = OrderHistory(
        id=uuid4(),
        order_id=order_id,
        field_name="status",
        old_value=old_status,
        new_value=new_status,
        changed_by=user_id,
        notes=notes,
        changed_at=datetime.utcnow(),
    )
    db.add(history)


# Order Endpoints
@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    auto_confirm: bool = Query(
        False, description="Automatically confirm order if inventory available"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new order"""

    # Validate customer exists
    if not await validate_customer_exists(db, order.customer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or inactive",
        )

    # Validate all product variants exist
    for item in order.items:
        if not await validate_product_variant_exists(db, item.product_variant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product variant {item.product_variant_id} not found",
            )

    # Check inventory availability
    inventory_issues = []
    for item in order.items:
        availability = await check_inventory_availability(
            db, item.product_variant_id, item.quantity
        )
        if not availability["available"]:
            inventory_issues.append(
                {
                    "variant_id": str(item.product_variant_id),
                    "requested": item.quantity,
                    "available": availability["total_available"],
                    "status": availability["status"],
                }
            )

    if inventory_issues and auto_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Insufficient inventory for auto-confirmation",
                "inventory_issues": inventory_issues,
            },
        )

    # Generate order number
    order_number = await generate_order_number(db)

    # Determine initial status
    initial_status = (
        OrderStatus.CONFIRMED
        if auto_confirm and not inventory_issues
        else OrderStatus.PENDING
    )

    # Create order
    db_order = Order(
        id=uuid4(),
        order_number=order_number,
        customer_id=order.customer_id,
        order_type=order.order_type,
        status=initial_status,
        payment_status=PaymentStatus.PENDING,
        shipment_status=ShipmentStatus.PENDING,
        priority=order.priority,
        reference_number=order.reference_number,
        po_number=order.po_number,
        currency=order.currency,
        exchange_rate=order.exchange_rate,
        requested_delivery_date=order.requested_delivery_date,
        special_instructions=order.special_instructions,
        internal_notes=order.internal_notes,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_order)
    await db.flush()  # Get the order ID

    # Create order items
    db_items = []
    for item_data in order.items:
        # Get product variant for pricing if not provided
        if item_data.unit_price is None:
            variant_result = await db.execute(
                select(ProductVariant).where(
                    ProductVariant.id == item_data.product_variant_id
                )
            )
            variant = variant_result.scalar_one()
            unit_price = variant.price
        else:
            unit_price = item_data.unit_price

        # Calculate discounts and taxes
        discount_amount = Decimal("0")
        if item_data.discount_percentage:
            discount_amount = (unit_price * item_data.quantity) * (
                item_data.discount_percentage / 100
            )
        elif item_data.discount_amount:
            discount_amount = item_data.discount_amount

        tax_amount = Decimal("0")
        if item_data.tax_percentage:
            taxable_amount = (unit_price * item_data.quantity) - discount_amount
            tax_amount = taxable_amount * (item_data.tax_percentage / 100)

        line_total = (unit_price * item_data.quantity) - discount_amount + tax_amount

        db_item = OrderItem(
            id=uuid4(),
            order_id=db_order.id,
            product_variant_id=item_data.product_variant_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            discount_percentage=item_data.discount_percentage,
            discount_amount=discount_amount,
            tax_percentage=item_data.tax_percentage,
            tax_amount=tax_amount,
            line_total=line_total,
            notes=item_data.notes,
            created_at=datetime.utcnow(),
        )
        db.add(db_item)
        db_items.append(db_item)

    # Create billing address
    db_billing = OrderAddress(
        id=uuid4(),
        order_id=db_order.id,
        address_type="billing",
        line1=order.billing_address.line1,
        line2=order.billing_address.line2,
        city=order.billing_address.city,
        state=order.billing_address.state,
        postal_code=order.billing_address.postal_code,
        country=order.billing_address.country,
        contact_name=order.billing_address.contact_name,
        contact_phone=order.billing_address.contact_phone,
        created_at=datetime.utcnow(),
    )
    db.add(db_billing)

    # Create shipping address
    db_shipping = None
    if order.shipping_address:
        db_shipping = OrderAddress(
            id=uuid4(),
            order_id=db_order.id,
            address_type="shipping",
            line1=order.shipping_address.line1,
            line2=order.shipping_address.line2,
            city=order.shipping_address.city,
            state=order.shipping_address.state,
            postal_code=order.shipping_address.postal_code,
            country=order.shipping_address.country,
            contact_name=order.shipping_address.contact_name,
            contact_phone=order.shipping_address.contact_phone,
            created_at=datetime.utcnow(),
        )
        db.add(db_shipping)

    # Create discounts
    db_discounts = []
    for discount_data in order.discounts:
        calculated_amount = discount_data.amount or Decimal("0")
        if discount_data.discount_type == DiscountType.PERCENTAGE:
            # Calculate percentage discount (simplified)
            calculated_amount = Decimal("0")  # Would calculate based on subtotal

        db_discount = OrderDiscount(
            id=uuid4(),
            order_id=db_order.id,
            discount_type=discount_data.discount_type,
            name=discount_data.name,
            code=discount_data.code,
            percentage=discount_data.percentage,
            amount=discount_data.amount,
            calculated_amount=calculated_amount,
            applies_to=discount_data.applies_to,
            item_id=discount_data.item_id,
            created_at=datetime.utcnow(),
        )
        db.add(db_discount)
        db_discounts.append(db_discount)

    # Calculate and update order totals
    totals = await calculate_order_totals(db_items, db_discounts)
    db_order.subtotal = totals["subtotal"]
    db_order.discount_total = totals["discount_total"]
    db_order.tax_total = totals["tax_total"]
    db_order.total_amount = totals["total_amount"]

    # Reserve inventory if auto-confirming
    if auto_confirm and not inventory_issues:
        for item in order.items:
            await reserve_inventory(db, item.product_variant_id, item.quantity)

    # Create initial status history
    await update_order_status_history(
        db, db_order.id, "none", initial_status.value, current_user.id, "Order created"
    )

    await db.commit()

    # Return complete order
    return await get_order(db_order.id, db)


@router.get("/", response_model=List[OrderListResponse])
async def list_orders(
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of orders to return"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    order_type: Optional[OrderType] = Query(None, description="Filter by order type"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    date_from: Optional[date] = Query(
        None, description="Filter orders created after this date"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter orders created before this date"
    ),
    search: Optional[str] = Query(
        None, min_length=1, description="Search in order number or PO number"
    ),
    sort_by: str = Query(
        "created_at", regex="^(order_number|customer|status|total_amount|created_at)$"
    ),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of orders with filtering and pagination"""

    # Build query with joins
    query = select(Order).options(joinedload(Order.customer))

    # Apply filters
    if status:
        query = query.where(Order.status == status)

    if customer_id:
        query = query.where(Order.customer_id == customer_id)

    if order_type:
        query = query.where(Order.order_type == order_type)

    if priority:
        query = query.where(Order.priority == priority)

    if date_from:
        query = query.where(Order.created_at >= date_from)

    if date_to:
        query = query.where(Order.created_at <= date_to)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Order.order_number.ilike(search_term),
                Order.po_number.ilike(search_term),
                Order.reference_number.ilike(search_term),
            )
        )

    # Apply sorting
    if sort_by == "order_number":
        order_column = Order.order_number
    elif sort_by == "customer":
        # Would need to join with customer table for proper sorting
        order_column = Order.created_at
    elif sort_by == "status":
        order_column = Order.status
    elif sort_by == "total_amount":
        order_column = Order.total_amount
    else:
        order_column = Order.created_at

    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    orders = result.unique().scalars().all()

    # Build response list
    response_list = []
    for order in orders:
        customer_name = "Unknown Customer"
        if order.customer:
            customer_name = (
                order.customer.company_name or f"{order.customer.customer_number}"
            )

        response_item = OrderListResponse(
            id=order.id,
            order_number=order.order_number,
            customer_name=customer_name,
            status=order.status,
            payment_status=order.payment_status,
            priority=order.priority,
            total_amount=order.total_amount,
            currency=order.currency,
            requested_delivery_date=order.requested_delivery_date,
            created_at=order.created_at,
        )
        response_list.append(response_item)

    return response_list


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID = Path(..., description="Order ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific order with all details"""

    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product_variant),
            selectinload(Order.addresses),
            selectinload(Order.discounts),
            selectinload(Order.shipments),
            selectinload(Order.payments),
            joinedload(Order.customer),
        )
        .where(Order.id == order_id)
    )

    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Build item responses
    item_responses = []
    for item in order.items:
        # Check availability status
        availability = await check_inventory_availability(
            db, item.product_variant_id, item.quantity
        )

        item_response = OrderItemResponse(
            id=item.id,
            product_variant_id=item.product_variant_id,
            product_name=item.product_variant.product.name
            if item.product_variant.product
            else "Unknown Product",
            variant_name=item.product_variant.name,
            sku=item.product_variant.sku,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_percentage=item.discount_percentage,
            discount_amount=item.discount_amount,
            tax_percentage=item.tax_percentage,
            tax_amount=item.tax_amount,
            line_total=item.line_total,
            notes=item.notes,
            availability_status=availability["status"],
            estimated_delivery=None,  # TODO: Calculate based on lead times
        )
        item_responses.append(item_response)

    # Build address responses
    billing_address = None
    shipping_address = None

    for address in order.addresses:
        full_address = f"{address.line1}"
        if address.line2:
            full_address += f", {address.line2}"
        full_address += f", {address.city}"
        if address.state:
            full_address += f", {address.state}"
        full_address += f" {address.postal_code}, {address.country}"

        address_response = OrderAddressResponse(
            id=address.id,
            address_type=address.address_type,
            line1=address.line1,
            line2=address.line2,
            city=address.city,
            state=address.state,
            postal_code=address.postal_code,
            country=address.country,
            contact_name=address.contact_name,
            contact_phone=address.contact_phone,
            full_address=full_address,
        )

        if address.address_type == "billing":
            billing_address = address_response
        else:
            shipping_address = address_response

    # Build discount responses
    discount_responses = []
    for discount in order.discounts:
        discount_response = OrderDiscountResponse(
            id=discount.id,
            discount_type=discount.discount_type,
            name=discount.name,
            code=discount.code,
            percentage=discount.percentage,
            amount=discount.amount or Decimal("0"),
            applies_to=discount.applies_to,
            item_id=discount.item_id,
            calculated_amount=discount.calculated_amount,
        )
        discount_responses.append(discount_response)

    # Get tracking numbers from shipments
    tracking_numbers = [
        shipment.tracking_number
        for shipment in order.shipments
        if shipment.tracking_number
    ]

    # Build customer name
    customer_name = "Unknown Customer"
    if order.customer:
        customer_name = (
            order.customer.company_name or f"{order.customer.customer_number}"
        )

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer_id=order.customer_id,
        customer_name=customer_name,
        order_type=order.order_type,
        status=order.status,
        payment_status=order.payment_status,
        shipment_status=order.shipment_status,
        priority=order.priority,
        reference_number=order.reference_number,
        po_number=order.po_number,
        currency=order.currency,
        exchange_rate=order.exchange_rate,
        subtotal=order.subtotal,
        discount_total=order.discount_total,
        tax_total=order.tax_total,
        shipping_total=order.shipping_total or Decimal("0"),
        total_amount=order.total_amount,
        requested_delivery_date=order.requested_delivery_date,
        estimated_delivery_date=None,  # TODO: Calculate
        shipped_date=order.shipped_date,
        delivered_date=order.delivered_date,
        special_instructions=order.special_instructions,
        internal_notes=order.internal_notes,
        items=item_responses,
        billing_address=billing_address,
        shipping_address=shipping_address,
        discounts=discount_responses,
        payment_terms=None,  # TODO: Get from customer
        sales_rep=None,  # TODO: Get from user
        order_source=None,  # TODO: Add to model
        tracking_numbers=tracking_numbers,
        created_by=order.created_by,
        created_by_name="Unknown",  # TODO: Get from user
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID = Path(..., description="Order ID"),
    order_update: OrderUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an order"""

    # Get existing order
    result = await db.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalar_one_or_none()

    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Check if order can be modified
    if db_order.status in [
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify order in {db_order.status} status",
        )

    # Track status changes for history
    old_status = db_order.status

    # Update fields
    for field, value in order_update.dict(exclude_unset=True).items():
        setattr(db_order, field, value)

    db_order.updated_at = datetime.utcnow()

    # Record status change if applicable
    if order_update.status and order_update.status != old_status:
        await update_order_status_history(
            db, order_id, old_status.value, order_update.status.value, current_user.id
        )

    await db.commit()

    # Return updated order
    return await get_order(order_id, db)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: UUID = Path(..., description="Order ID"),
    reason: str = Query(..., min_length=1, description="Cancellation reason"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel an order"""

    # Get order
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Check if order can be cancelled
    if order.status in [
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in {order.status} status",
        )

    # Update order status
    old_status = order.status
    order.status = OrderStatus.CANCELLED
    order.updated_at = datetime.utcnow()

    # Release reserved inventory
    order_items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    order_items = order_items_result.scalars().all()

    for item in order_items:
        # Find and release reserved inventory
        inventory_result = await db.execute(
            select(InventoryItem)
            .where(
                and_(
                    InventoryItem.product_variant_id == item.product_variant_id,
                    InventoryItem.reserved_quantity > 0,
                )
            )
            .order_by(InventoryItem.created_at)
        )

        inventory_items = inventory_result.scalars().all()
        remaining_to_release = item.quantity

        for inv_item in inventory_items:
            if remaining_to_release <= 0:
                break

            to_release = min(inv_item.reserved_quantity, remaining_to_release)
            inv_item.reserved_quantity -= to_release
            remaining_to_release -= to_release

    # Record status change
    await update_order_status_history(
        db,
        order_id,
        old_status.value,
        OrderStatus.CANCELLED.value,
        current_user.id,
        f"Cancelled: {reason}",
    )

    await db.commit()


# Shipment Endpoints
@router.post(
    "/{order_id}/shipments",
    response_model=OrderShipmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shipment(
    order_id: UUID = Path(..., description="Order ID"),
    shipment: OrderShipmentCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a shipment for an order"""

    # Validate order exists and can be shipped
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status not in [OrderStatus.CONFIRMED, OrderStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create shipment for order in {order.status} status",
        )

    # Validate shipment items exist in order
    order_items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    order_items = {str(item.id): item for item in order_items_result.scalars().all()}

    for shipment_item in shipment.items:
        item_id = shipment_item["item_id"]
        if item_id not in order_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order item {item_id} not found",
            )

    # Create shipment
    db_shipment = OrderShipment(
        id=uuid4(),
        order_id=order_id,
        carrier=shipment.carrier,
        service_type=shipment.service_type,
        tracking_number=shipment.tracking_number,
        status=ShipmentStatus.PREPARED,
        weight=shipment.weight,
        dimensions=shipment.dimensions,
        shipping_cost=shipment.shipping_cost,
        estimated_delivery=shipment.estimated_delivery,
        notes=shipment.notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_shipment)
    await db.flush()

    # Update order status if not already shipped
    if order.status != OrderStatus.SHIPPED:
        old_status = order.status
        order.status = OrderStatus.SHIPPED
        order.shipment_status = ShipmentStatus.SHIPPED
        order.shipped_date = datetime.utcnow()
        order.updated_at = datetime.utcnow()

        await update_order_status_history(
            db,
            order_id,
            old_status.value,
            OrderStatus.SHIPPED.value,
            current_user.id,
            "Shipment created",
        )

    await db.commit()
    await db.refresh(db_shipment)

    return OrderShipmentResponse(
        id=db_shipment.id,
        order_id=db_shipment.order_id,
        carrier=db_shipment.carrier,
        service_type=db_shipment.service_type,
        tracking_number=db_shipment.tracking_number,
        status=db_shipment.status,
        weight=db_shipment.weight,
        dimensions=db_shipment.dimensions,
        shipping_cost=db_shipment.shipping_cost,
        shipped_date=db_shipment.shipped_date,
        estimated_delivery=db_shipment.estimated_delivery,
        delivered_date=db_shipment.delivered_date,
        items_count=len(shipment.items),
        notes=db_shipment.notes,
        created_at=db_shipment.created_at,
        updated_at=db_shipment.updated_at,
    )


# Payment Endpoints
@router.post(
    "/{order_id}/payments",
    response_model=OrderPaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    order_id: UUID = Path(..., description="Order ID"),
    payment: OrderPaymentCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record a payment for an order"""

    # Validate order exists
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Create payment record
    db_payment = OrderPayment(
        id=uuid4(),
        order_id=order_id,
        payment_method=payment.payment_method,
        amount=payment.amount,
        status=PaymentStatus.CAPTURED,  # Assuming successful payment
        transaction_id=payment.transaction_id,
        reference_number=payment.reference_number,
        processed_date=datetime.utcnow(),
        notes=payment.notes,
        created_at=datetime.utcnow(),
    )

    db.add(db_payment)

    # Update order payment status
    total_payments = await db.execute(
        select(func.sum(OrderPayment.amount)).where(
            and_(
                OrderPayment.order_id == order_id,
                OrderPayment.status == PaymentStatus.CAPTURED,
            )
        )
    )

    total_paid = (total_payments.scalar() or Decimal("0")) + payment.amount

    if total_paid >= order.total_amount:
        order.payment_status = PaymentStatus.PAID
    elif total_paid > 0:
        order.payment_status = PaymentStatus.PARTIALLY_PAID

    order.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(db_payment)

    return OrderPaymentResponse(
        id=db_payment.id,
        order_id=db_payment.order_id,
        payment_method=db_payment.payment_method,
        amount=db_payment.amount,
        status=db_payment.status,
        transaction_id=db_payment.transaction_id,
        reference_number=db_payment.reference_number,
        processed_date=db_payment.processed_date,
        notes=db_payment.notes,
        created_at=db_payment.created_at,
    )


# Analytics
@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_order_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    db: AsyncSession = Depends(get_db),
):
    """Get order analytics and statistics"""

    # Base query filters
    base_filters = []
    if start_date:
        base_filters.append(Order.created_at >= start_date)
    if end_date:
        base_filters.append(Order.created_at <= end_date)
    if customer_id:
        base_filters.append(Order.customer_id == customer_id)

    # Total orders and revenue
    totals_query = select(
        func.count(Order.id).label("total_orders"),
        func.sum(Order.total_amount).label("total_revenue"),
        func.avg(Order.total_amount).label("avg_order_value"),
    )

    for filter_clause in base_filters:
        totals_query = totals_query.where(filter_clause)

    totals_result = await db.execute(totals_query)
    totals = totals_result.first()

    # Orders by status
    status_query = select(Order.status, func.count(Order.id))
    for filter_clause in base_filters:
        status_query = status_query.where(filter_clause)
    status_query = status_query.group_by(Order.status)

    status_result = await db.execute(status_query)
    status_counts = {status: count for status, count in status_result.fetchall()}

    # Orders by priority
    priority_query = select(Order.priority, func.count(Order.id))
    for filter_clause in base_filters:
        priority_query = priority_query.where(filter_clause)
    priority_query = priority_query.group_by(Order.priority)

    priority_result = await db.execute(priority_query)
    priority_counts = {
        priority: count for priority, count in priority_result.fetchall()
    }

    # Monthly trend (last 12 months)
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    trend_query = select(
        func.date_trunc("month", Order.created_at).label("month"),
        func.count(Order.id).label("order_count"),
        func.sum(Order.total_amount).label("revenue"),
    ).where(Order.created_at >= twelve_months_ago)

    for filter_clause in base_filters:
        if "created_at" not in str(filter_clause):
            trend_query = trend_query.where(filter_clause)

    trend_query = trend_query.group_by("month").order_by("month")

    trend_result = await db.execute(trend_query)
    monthly_trend = [
        {
            "month": month.strftime("%Y-%m"),
            "order_count": count,
            "revenue": float(revenue or 0),
        }
        for month, count, revenue in trend_result.fetchall()
    ]

    return {
        "summary": {
            "total_orders": totals.total_orders or 0,
            "total_revenue": float(totals.total_revenue or 0),
            "average_order_value": float(totals.avg_order_value or 0),
        },
        "orders_by_status": status_counts,
        "orders_by_priority": priority_counts,
        "monthly_trend": monthly_trend,
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "customer_id": customer_id,
        },
    }


# Quote Management Endpoints
@router.post(
    "/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED
)
async def create_quote(
    quote: QuoteRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new quote for a customer"""

    # Validate customer exists
    if not await validate_customer_exists(db, quote.customer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or inactive",
        )

    # Validate all product variants exist
    for item in quote.items:
        if not await validate_product_variant_exists(db, item.product_variant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product variant {item.product_variant_id} not found",
            )

    # Generate quote number
    quote_number = await generate_order_number(db, "QTE")

    # Create quote
    db_quote = QuoteRequest(
        id=uuid4(),
        quote_number=quote_number,
        customer_id=quote.customer_id,
        status="draft",
        currency=quote.currency,
        valid_until=quote.valid_until,
        notes=quote.notes,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_quote)
    await db.flush()

    # Create quote items
    quote_items = []
    subtotal = Decimal("0")

    for item_data in quote.items:
        # Get product variant for pricing
        variant_result = await db.execute(
            select(ProductVariant).where(
                ProductVariant.id == item_data.product_variant_id
            )
        )
        variant = variant_result.scalar_one()
        unit_price = item_data.unit_price or variant.price

        line_total = unit_price * item_data.quantity
        subtotal += line_total

        db_item = QuoteItem(
            id=uuid4(),
            quote_id=db_quote.id,
            product_variant_id=item_data.product_variant_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            line_total=line_total,
            notes=item_data.notes,
            created_at=datetime.utcnow(),
        )
        db.add(db_item)
        quote_items.append(db_item)

    # Calculate totals
    tax_total = subtotal * Decimal("0.1")  # 10% tax
    total_amount = subtotal + tax_total

    db_quote.subtotal = subtotal
    db_quote.tax_total = tax_total
    db_quote.total_amount = total_amount

    await db.commit()

    # Return quote response
    customer_result = await db.execute(
        select(Customer).where(Customer.id == quote.customer_id)
    )
    customer = customer_result.scalar_one()

    return QuoteResponse(
        id=db_quote.id,
        quote_number=db_quote.quote_number,
        customer_id=db_quote.customer_id,
        customer_name=customer.company_name or customer.customer_number,
        status=db_quote.status,
        subtotal=db_quote.subtotal,
        tax_total=db_quote.tax_total,
        total_amount=db_quote.total_amount,
        currency=db_quote.currency,
        valid_until=db_quote.valid_until,
        notes=db_quote.notes,
        items=[],  # Would need to load items with product details
        created_by=db_quote.created_by,
        created_at=db_quote.created_at,
        updated_at=db_quote.updated_at,
    )


@router.post(
    "/quotes/{quote_id}/convert",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def convert_quote_to_order(
    quote_id: UUID = Path(..., description="Quote ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Convert a quote to an order"""

    # Get quote with items
    quote_result = await db.execute(
        select(QuoteRequest)
        .options(selectinload(QuoteRequest.items))
        .where(QuoteRequest.id == quote_id)
    )
    quote = quote_result.scalar_one_or_none()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found"
        )

    if quote.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved quotes can be converted to orders",
        )

    # Create order from quote
    order_number = await generate_order_number(db)

    db_order = Order(
        id=uuid4(),
        order_number=order_number,
        customer_id=quote.customer_id,
        order_type=OrderType.SALE,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        shipment_status=ShipmentStatus.PENDING,
        priority=Priority.NORMAL,
        currency=quote.currency,
        subtotal=quote.subtotal,
        tax_total=quote.tax_total,
        total_amount=quote.total_amount,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_order)
    await db.flush()

    # Create order items from quote items
    for quote_item in quote.items:
        order_item = OrderItem(
            id=uuid4(),
            order_id=db_order.id,
            product_variant_id=quote_item.product_variant_id,
            quantity=quote_item.quantity,
            unit_price=quote_item.unit_price,
            line_total=quote_item.line_total,
            notes=quote_item.notes,
            created_at=datetime.utcnow(),
        )
        db.add(order_item)

    # Update quote status
    quote.status = "converted"
    quote.updated_at = datetime.utcnow()

    await db.commit()

    # Return created order
    return await get_order(db_order.id, db)


# Bulk Operations
@router.post("/bulk/update-status", response_model=Dict[str, Any])
async def bulk_update_order_status(
    order_ids: List[UUID] = Body(..., min_items=1, max_items=100),
    new_status: OrderStatus = Body(...),
    notes: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Bulk update order status"""

    # Get orders
    result = await db.execute(select(Order).where(Order.id.in_(order_ids)))
    orders = result.scalars().all()

    if len(orders) != len(order_ids):
        found_ids = {order.id for order in orders}
        missing_ids = set(order_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orders not found: {missing_ids}",
        )

    # Update orders
    updated_count = 0
    failed_updates = []

    for order in orders:
        try:
            # Check if status change is valid
            if order.status in [
                OrderStatus.DELIVERED,
                OrderStatus.COMPLETED,
                OrderStatus.CANCELLED,
            ]:
                failed_updates.append(
                    {
                        "order_id": str(order.id),
                        "reason": f"Cannot change status from {order.status}",
                    }
                )
                continue

            old_status = order.status
            order.status = new_status
            order.updated_at = datetime.utcnow()

            # Record history
            await update_order_status_history(
                db, order.id, old_status.value, new_status.value, current_user.id, notes
            )

            updated_count += 1

        except Exception as e:
            failed_updates.append({"order_id": str(order.id), "reason": str(e)})

    await db.commit()

    return {
        "updated_count": updated_count,
        "total_requested": len(order_ids),
        "failed_updates": failed_updates,
        "new_status": new_status,
    }


@router.get("/bulk/export", response_model=Dict[str, Any])
async def export_orders(
    format: str = Query("csv", regex="^(csv|xlsx|json)$"),
    status: Optional[OrderStatus] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Export orders in various formats"""

    # Build export query
    query = select(Order).options(joinedload(Order.customer))

    if status:
        query = query.where(Order.status == status)
    if date_from:
        query = query.where(Order.created_at >= date_from)
    if date_to:
        query = query.where(Order.created_at <= date_to)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)

    result = await db.execute(query)
    orders = result.unique().scalars().all()

    # Prepare export data
    export_data = []
    for order in orders:
        customer_name = "Unknown"
        if order.customer:
            customer_name = (
                order.customer.company_name or order.customer.customer_number
            )

        export_data.append(
            {
                "order_number": order.order_number,
                "customer_name": customer_name,
                "status": order.status,
                "payment_status": order.payment_status,
                "priority": order.priority,
                "total_amount": float(order.total_amount),
                "currency": order.currency,
                "created_at": order.created_at.isoformat(),
                "requested_delivery_date": order.requested_delivery_date.isoformat()
                if order.requested_delivery_date
                else None,
            }
        )

    return {
        "format": format,
        "record_count": len(export_data),
        "data": export_data,
        "generated_at": datetime.utcnow().isoformat(),
        "filters": {
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
            "customer_id": customer_id,
        },
    }


# Order History and Tracking
@router.get("/{order_id}/history", response_model=List[Dict[str, Any]])
async def get_order_history(
    order_id: UUID = Path(..., description="Order ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get order change history"""

    # Validate order exists
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    if not order_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Get history records
    history_result = await db.execute(
        select(OrderHistory)
        .where(OrderHistory.order_id == order_id)
        .order_by(OrderHistory.changed_at.desc())
    )

    history_records = history_result.scalars().all()

    return [
        {
            "id": str(record.id),
            "field_name": record.field_name,
            "old_value": record.old_value,
            "new_value": record.new_value,
            "changed_by": str(record.changed_by),
            "changed_at": record.changed_at.isoformat(),
            "notes": record.notes,
        }
        for record in history_records
    ]


@router.get("/{order_id}/tracking", response_model=Dict[str, Any])
async def get_order_tracking(
    order_id: UUID = Path(..., description="Order ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get order tracking information"""

    # Get order with shipments
    order_result = await db.execute(
        select(Order).options(selectinload(Order.shipments)).where(Order.id == order_id)
    )
    order = order_result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Build tracking response
    shipments = []
    for shipment in order.shipments:
        shipments.append(
            {
                "id": str(shipment.id),
                "carrier": shipment.carrier,
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "shipped_date": shipment.shipped_date.isoformat()
                if shipment.shipped_date
                else None,
                "estimated_delivery": shipment.estimated_delivery.isoformat()
                if shipment.estimated_delivery
                else None,
                "delivered_date": shipment.delivered_date.isoformat()
                if shipment.delivered_date
                else None,
            }
        )

    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "order_status": order.status,
        "shipment_status": order.shipment_status,
        "shipped_date": order.shipped_date.isoformat() if order.shipped_date else None,
        "delivered_date": order.delivered_date.isoformat()
        if order.delivered_date
        else None,
        "shipments": shipments,
        "estimated_delivery_date": None,  # Would calculate from shipments
    }


# Order Validation and Checks
@router.get("/{order_id}/validate", response_model=Dict[str, Any])
async def validate_order(
    order_id: UUID = Path(..., description="Order ID"),
    db: AsyncSession = Depends(get_db),
):
    """Validate order data and inventory availability"""

    # Get order with items
    order_result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = order_result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    validation_results = {
        "order_id": str(order.id),
        "is_valid": True,
        "issues": [],
        "inventory_status": [],
        "total_validation_score": 100,
    }

    # Check inventory availability
    for item in order.items:
        availability = await check_inventory_availability(
            db, item.product_variant_id, item.quantity
        )

        inventory_issue = {
            "item_id": str(item.id),
            "product_variant_id": str(item.product_variant_id),
            "requested_quantity": item.quantity,
            "available_quantity": availability["total_available"],
            "status": availability["status"],
            "is_sufficient": availability["available"],
        }

        validation_results["inventory_status"].append(inventory_issue)

        if not availability["available"]:
            validation_results["is_valid"] = False
            validation_results["issues"].append(
                f"Insufficient inventory for item {item.id}"
            )
            validation_results["total_validation_score"] -= 20

    # Check customer status
    customer_result = await db.execute(
        select(Customer).where(Customer.id == order.customer_id)
    )
    customer = customer_result.scalar_one_or_none()

    if not customer or customer.status not in ["active", "vip"]:
        validation_results["is_valid"] = False
        validation_results["issues"].append("Customer is inactive or not found")
        validation_results["total_validation_score"] -= 30

    # Check order totals
    if order.total_amount <= 0:
        validation_results["is_valid"] = False
        validation_results["issues"].append("Order total must be greater than zero")
        validation_results["total_validation_score"] -= 25

    validation_results["total_validation_score"] = max(
        0, validation_results["total_validation_score"]
    )

    return validation_results


# Advanced Search
@router.get("/search/advanced", response_model=List[OrderListResponse])
async def advanced_order_search(
    query: str = Query(..., min_length=1, description="Search query"),
    search_fields: List[str] = Query(
        default=["order_number", "customer_name", "po_number"],
        description="Fields to search in",
    ),
    filters: Dict[str, Any] = Query(default={}, description="Additional filters"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Advanced search with multiple fields and filters"""

    # Build base query
    base_query = select(Order).options(joinedload(Order.customer))

    # Build search conditions
    search_conditions = []
    search_term = f"%{query}%"

    if "order_number" in search_fields:
        search_conditions.append(Order.order_number.ilike(search_term))

    if "po_number" in search_fields:
        search_conditions.append(Order.po_number.ilike(search_term))

    if "reference_number" in search_fields:
        search_conditions.append(Order.reference_number.ilike(search_term))

    if "customer_name" in search_fields:
        # Would need proper customer name search with joins
        pass

    if search_conditions:
        base_query = base_query.where(or_(*search_conditions))

    # Apply additional filters
    for field, value in filters.items():
        if field == "status" and value:
            base_query = base_query.where(Order.status == value)
        elif field == "priority" and value:
            base_query = base_query.where(Order.priority == value)
        elif field == "min_amount" and value:
            base_query = base_query.where(Order.total_amount >= value)
        elif field == "max_amount" and value:
            base_query = base_query.where(Order.total_amount <= value)

    # Execute query
    base_query = base_query.limit(limit)
    result = await db.execute(base_query)
    orders = result.unique().scalars().all()

    # Build response
    response_list = []
    for order in orders:
        customer_name = "Unknown Customer"
        if order.customer:
            customer_name = (
                order.customer.company_name or order.customer.customer_number
            )

        response_item = OrderListResponse(
            id=order.id,
            order_number=order.order_number,
            customer_name=customer_name,
            status=order.status,
            payment_status=order.payment_status,
            priority=order.priority,
            total_amount=order.total_amount,
            currency=order.currency,
            requested_delivery_date=order.requested_delivery_date,
            created_at=order.created_at,
        )
        response_list.append(response_item)

    return response_list
