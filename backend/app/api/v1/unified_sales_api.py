"""
ITDO ERP Backend - Unified Sales API
Day 13: API Integration - Sales Management Unified API
Integrates sales_v21.py and sales_order_management_v68.py functionality
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.sales import OrderLine, SalesOrder
from app.models.user import User

# Mock authentication dependency for unified APIs
async def get_current_user() -> User:
    """Mock current user for unified APIs"""
    from unittest.mock import Mock
    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


# Sales Status Enums
class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class OrderType(str, Enum):
    SALE = "sale"
    QUOTE = "quote"
    RETURN = "return"


# Pydantic Schemas
class OrderLineBase(BaseModel):
    """Base order line schema"""

    product_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class OrderLineCreate(OrderLineBase):
    """Schema for creating order line"""

    pass


class OrderLineResponse(OrderLineBase):
    """Schema for order line response"""

    id: uuid.UUID
    line_total: Decimal
    tax_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class SalesOrderBase(BaseModel):
    """Base sales order schema"""

    customer_id: Optional[uuid.UUID] = None
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    shipping_address: Optional[Dict[str, str]] = None
    order_type: OrderType = OrderType.SALE
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SalesOrderCreate(SalesOrderBase):
    """Schema for creating sales order"""

    order_lines: List[OrderLineCreate] = Field(..., min_items=1)


class SalesOrderUpdate(BaseModel):
    """Schema for updating sales order"""

    customer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    shipping_address: Optional[Dict[str, str]] = None
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class SalesOrderResponse(SalesOrderBase):
    """Schema for sales order response"""

    id: uuid.UUID
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    order_lines: List[OrderLineResponse] = Field(default_factory=list)
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Schema for paginated order list response"""

    orders: List[SalesOrderResponse]
    total: int
    page: int
    size: int
    pages: int


class QuoteRequest(BaseModel):
    """Schema for quote generation request"""

    customer_id: Optional[uuid.UUID] = None
    customer_email: str
    quote_lines: List[OrderLineCreate] = Field(..., min_items=1)
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class QuoteResponse(BaseModel):
    """Schema for quote response"""

    quote_id: uuid.UUID
    quote_number: str
    customer_email: str
    quote_lines: List[OrderLineResponse]
    subtotal: Decimal
    tax_total: Decimal
    total_amount: Decimal
    valid_until: datetime
    created_at: datetime
    status: str = "active"


# Unified Sales Service
class UnifiedSalesService:
    """Unified service for sales management operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def create_sales_order(
        self, order_data: SalesOrderCreate, user_id: uuid.UUID
    ) -> SalesOrderResponse:
        """Create a new sales order with unified processing"""

        # Generate order number
        order_counter = await self.redis.incr(
            f"order_counter:{datetime.utcnow().strftime('%Y%m%d')}"
        )
        await self.redis.expire(
            f"order_counter:{datetime.utcnow().strftime('%Y%m%d')}", 86400
        )
        order_number = f"SO-{datetime.utcnow().strftime('%Y%m%d')}-{order_counter:06d}"

        # Create order
        order = SalesOrder(
            id=uuid.uuid4(),
            order_number=order_number,
            customer_id=order_data.customer_id,
            customer_name=order_data.customer_name,
            customer_email=order_data.customer_email,
            customer_phone=order_data.customer_phone,
            billing_address=order_data.billing_address,
            shipping_address=order_data.shipping_address,
            order_type=order_data.order_type.value,
            currency=order_data.currency,
            status=OrderStatus.DRAFT.value,
            payment_status=PaymentStatus.PENDING.value,
            notes=order_data.notes,
            internal_notes=order_data.internal_notes,
            tags=order_data.tags,
            created_at=datetime.utcnow(),
            created_by=user_id,
        )

        self.db.add(order)

        # Create order lines and calculate totals
        subtotal = Decimal("0")
        tax_total = Decimal("0")
        discount_total = Decimal("0")

        for line_data in order_data.order_lines:
            line_subtotal = line_data.quantity * line_data.unit_price

            # Calculate discount
            line_discount = Decimal("0")
            if line_data.discount_percent:
                line_discount = line_subtotal * (line_data.discount_percent / 100)
            elif line_data.discount_amount:
                line_discount = line_data.discount_amount

            discounted_amount = line_subtotal - line_discount

            # Calculate tax
            line_tax = Decimal("0")
            if line_data.tax_rate:
                line_tax = discounted_amount * (line_data.tax_rate / 100)

            line_total = discounted_amount + line_tax

            # Create order line
            order_line = OrderLine(
                id=uuid.uuid4(),
                order_id=order.id,
                product_id=line_data.product_id,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                discount_amount=line_discount,
                tax_rate=line_data.tax_rate,
                tax_amount=line_tax,
                line_total=line_total,
                notes=line_data.notes,
                created_at=datetime.utcnow(),
            )

            self.db.add(order_line)

            subtotal += line_subtotal
            discount_total += line_discount
            tax_total += line_tax

        # Update order totals
        order.subtotal = subtotal
        order.discount_total = discount_total
        order.tax_total = tax_total
        order.total_amount = subtotal - discount_total + tax_total

        await self.db.commit()
        await self.db.refresh(order)

        # Load with relations for response
        result = await self.db.execute(
            select(SalesOrder)
            .options(selectinload(SalesOrder.order_lines))
            .where(SalesOrder.id == order.id)
        )
        order_with_lines = result.scalar_one()

        return SalesOrderResponse.from_orm(order_with_lines)

    async def get_sales_order(
        self, order_id: uuid.UUID
    ) -> Optional[SalesOrderResponse]:
        """Get a sales order by ID"""

        result = await self.db.execute(
            select(SalesOrder)
            .options(selectinload(SalesOrder.order_lines))
            .where(SalesOrder.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            return None

        return SalesOrderResponse.from_orm(order)

    async def update_sales_order(
        self, order_id: uuid.UUID, order_data: SalesOrderUpdate, user_id: uuid.UUID
    ) -> Optional[SalesOrderResponse]:
        """Update a sales order"""

        result = await self.db.execute(
            select(SalesOrder).where(SalesOrder.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            return None

        # Update fields
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        order.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(order)

        return await self.get_sales_order(order_id)

    async def confirm_order(
        self, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[SalesOrderResponse]:
        """Confirm a sales order"""

        result = await self.db.execute(
            select(SalesOrder).where(SalesOrder.id == order_id)
        )
        order = result.scalar_one_or_none()

        if not order:
            return None

        if order.status != OrderStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft orders can be confirmed",
            )

        order.status = OrderStatus.CONFIRMED.value
        order.updated_at = datetime.utcnow()

        await self.db.commit()

        return await self.get_sales_order(order_id)

    async def list_sales_orders(
        self,
        page: int = 1,
        size: int = 50,
        customer_name: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        order_type: Optional[OrderType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> OrderListResponse:
        """List sales orders with filtering and pagination"""

        query = select(SalesOrder).options(selectinload(SalesOrder.order_lines))

        # Apply filters
        filters = []
        if customer_name:
            filters.append(SalesOrder.customer_name.ilike(f"%{customer_name}%"))

        if status:
            filters.append(SalesOrder.status == status.value)

        if order_type:
            filters.append(SalesOrder.order_type == order_type.value)

        if date_from:
            filters.append(SalesOrder.created_at >= date_from)

        if date_to:
            filters.append(SalesOrder.created_at <= date_to)

        if filters:
            query = query.where(and_(*filters))

        # Apply sorting
        sort_column = getattr(SalesOrder, sort_by, SalesOrder.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Get total count
        count_query = select(func.count(SalesOrder.id))
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        orders = result.scalars().all()

        return OrderListResponse(
            orders=[SalesOrderResponse.from_orm(o) for o in orders],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def generate_quote(
        self, quote_data: QuoteRequest, user_id: uuid.UUID
    ) -> QuoteResponse:
        """Generate a sales quote"""

        # Generate quote number
        quote_counter = await self.redis.incr(
            f"quote_counter:{datetime.utcnow().strftime('%Y%m%d')}"
        )
        await self.redis.expire(
            f"quote_counter:{datetime.utcnow().strftime('%Y%m%d')}", 86400
        )
        quote_number = f"QT-{datetime.utcnow().strftime('%Y%m%d')}-{quote_counter:06d}"

        # Calculate quote totals
        subtotal = Decimal("0")
        tax_total = Decimal("0")
        quote_lines = []

        for line_data in quote_data.quote_lines:
            line_subtotal = line_data.quantity * line_data.unit_price

            # Calculate discount
            line_discount = Decimal("0")
            if line_data.discount_percent:
                line_discount = line_subtotal * (line_data.discount_percent / 100)
            elif line_data.discount_amount:
                line_discount = line_data.discount_amount

            discounted_amount = line_subtotal - line_discount

            # Calculate tax
            line_tax = Decimal("0")
            if line_data.tax_rate:
                line_tax = discounted_amount * (line_data.tax_rate / 100)

            line_total = discounted_amount + line_tax

            quote_line = OrderLineResponse(
                id=uuid.uuid4(),
                product_id=line_data.product_id,
                quantity=line_data.quantity,
                unit_price=line_data.unit_price,
                discount_percent=line_data.discount_percent,
                discount_amount=line_discount,
                tax_rate=line_data.tax_rate,
                tax_amount=line_tax,
                line_total=line_total,
                notes=line_data.notes,
                created_at=datetime.utcnow(),
            )

            quote_lines.append(quote_line)
            subtotal += line_subtotal
            tax_total += line_tax

        # Set quote validity (default 30 days)
        valid_until = quote_data.valid_until or (datetime.utcnow() + timedelta(days=30))

        quote_response = QuoteResponse(
            quote_id=uuid.uuid4(),
            quote_number=quote_number,
            customer_email=quote_data.customer_email,
            quote_lines=quote_lines,
            subtotal=subtotal,
            tax_total=tax_total,
            total_amount=subtotal + tax_total,
            valid_until=valid_until,
            created_at=datetime.utcnow(),
        )

        # Cache the quote
        await self.redis.setex(
            f"quote:{quote_response.quote_id}",
            86400 * 30,  # 30 days
            quote_response.json(),
        )

        return quote_response


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_sales_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> UnifiedSalesService:
    """Get sales service instance"""
    return UnifiedSalesService(db, redis)


# API Endpoints - Unified Sales API
@router.post(
    "/orders", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED
)
async def create_sales_order(
    order_data: SalesOrderCreate,
    current_user: User = Depends(get_current_user),
    service: UnifiedSalesService = Depends(get_sales_service),
):
    """Create a new sales order"""
    return await service.create_sales_order(order_data, current_user.id)


@router.get("/orders", response_model=OrderListResponse)
async def list_sales_orders(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    customer_name: Optional[str] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    order_type: Optional[OrderType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    service: UnifiedSalesService = Depends(get_sales_service),
):
    """List sales orders with filtering and pagination"""
    return await service.list_sales_orders(
        page=page,
        size=size,
        customer_name=customer_name,
        status=status,
        order_type=order_type,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order(
    order_id: uuid.UUID, service: UnifiedSalesService = Depends(get_sales_service)
):
    """Get a sales order by ID"""
    order = await service.get_sales_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found"
        )
    return order


@router.put("/orders/{order_id}", response_model=SalesOrderResponse)
async def update_sales_order(
    order_id: uuid.UUID,
    order_data: SalesOrderUpdate,
    current_user: User = Depends(get_current_user),
    service: UnifiedSalesService = Depends(get_sales_service),
):
    """Update a sales order"""
    order = await service.update_sales_order(order_id, order_data, current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found"
        )
    return order


@router.post("/orders/{order_id}/confirm", response_model=SalesOrderResponse)
async def confirm_sales_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: UnifiedSalesService = Depends(get_sales_service),
):
    """Confirm a sales order"""
    order = await service.confirm_order(order_id, current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found"
        )
    return order


@router.post(
    "/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED
)
async def generate_quote(
    quote_data: QuoteRequest,
    current_user: User = Depends(get_current_user),
    service: UnifiedSalesService = Depends(get_sales_service),
):
    """Generate a sales quote"""
    return await service.generate_quote(quote_data, current_user.id)


# Legacy endpoints for backward compatibility
@router.post("/sales-v21", response_model=Dict[str, Any], deprecated=True)
async def create_sale_v21(
    product_id: int,
    quantity: int,
    total: float,
    current_user: User = Depends(get_current_user),
    service: UnifiedSalesService = Depends(get_sales_service),
):
    """Legacy v21 sales creation endpoint (deprecated)"""
    try:
        # Create a simplified order for backward compatibility
        order_data = SalesOrderCreate(
            customer_name="Legacy Customer",
            customer_email="legacy@example.com",
            order_lines=[
                OrderLineCreate(
                    product_id=uuid.UUID(int=product_id),
                    quantity=Decimal(str(quantity)),
                    unit_price=Decimal(str(total)) / Decimal(str(quantity)),
                )
            ],
        )

        result = await service.create_sales_order(order_data, current_user.id)

        return {
            "id": str(result.id),
            "product_id": product_id,
            "quantity": quantity,
            "total": total,
            "status": "success",
        }
    except Exception as e:
        return {
            "id": product_id,
            "product_id": product_id,
            "quantity": quantity,
            "total": total,
            "status": "error",
            "message": str(e),
        }


@router.get("/sales-v21", response_model=List[Dict[str, Any]], deprecated=True)
async def list_sales_v21(service: UnifiedSalesService = Depends(get_sales_service)):
    """Legacy v21 sales listing endpoint (deprecated)"""
    orders = await service.list_sales_orders(page=1, size=100)
    return [
        {
            "id": str(order.id),
            "product_id": str(order.order_lines[0].product_id)
            if order.order_lines
            else "",
            "quantity": float(order.order_lines[0].quantity)
            if order.order_lines
            else 0,
            "total": float(order.total_amount),
        }
        for order in orders.orders
    ]


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for unified sales API"""
    return {
        "status": "healthy",
        "service": "unified-sales-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
