"""
ITDO ERP Backend - Sales Order Management v68
Complete sales order processing system with workflow engine, pricing, and fulfillment
Day 10: Sales Order Management System Implementation
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/sales", tags=["sales-orders"])


# Enums for Sales Order Management
class OrderStatus(str, Enum):
    """Sales order status enumeration"""

    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderType(str, Enum):
    """Order type enumeration"""

    STANDARD = "standard"
    RUSH = "rush"
    BACKORDER = "backorder"
    DROPSHIP = "dropship"
    SUBSCRIPTION = "subscription"
    SAMPLE = "sample"
    RETURN_EXCHANGE = "return_exchange"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class ShippingMethod(str, Enum):
    """Shipping method enumeration"""

    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    PICKUP = "pickup"
    DELIVERY = "delivery"


class PricingStrategy(str, Enum):
    """Pricing strategy enumeration"""

    LIST_PRICE = "list_price"
    CUSTOMER_SPECIFIC = "customer_specific"
    VOLUME_DISCOUNT = "volume_discount"
    PROMOTIONAL = "promotional"
    CONTRACT = "contract"


# Pydantic Models
class OrderLineItem(BaseModel):
    """Sales order line item model"""

    id: Optional[uuid.UUID] = None
    product_id: uuid.UUID
    sku: Optional[str] = None
    product_name: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_percentage: Optional[Decimal] = Field(default=0, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(default=0, ge=0)
    line_total: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = Field(default=0, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(default=0, ge=0)
    notes: Optional[str] = None

    @validator("line_total", always=True)
    def calculate_line_total(cls, v, values) -> dict:
        """Calculate line total including discounts and taxes"""
        quantity = values.get("quantity", 0)
        unit_price = values.get("unit_price", 0)
        discount_amount = values.get("discount_amount", 0)
        tax_amount = values.get("tax_amount", 0)

        subtotal = quantity * unit_price - discount_amount
        return subtotal + tax_amount


class OrderShippingAddress(BaseModel):
    """Shipping address model"""

    name: str
    company: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    special_instructions: Optional[str] = None


class OrderCreate(BaseModel):
    """Sales order creation model"""

    customer_id: uuid.UUID
    order_type: OrderType = OrderType.STANDARD
    priority: int = Field(default=1, ge=1, le=5)
    currency: str = Field(default="USD")
    payment_terms: Optional[str] = None
    shipping_method: ShippingMethod = ShippingMethod.STANDARD
    requested_delivery_date: Optional[datetime] = None
    shipping_address: OrderShippingAddress
    billing_address: Optional[OrderShippingAddress] = None
    line_items: List[OrderLineItem]
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    reference_number: Optional[str] = None
    sales_rep_id: Optional[uuid.UUID] = None


class OrderUpdate(BaseModel):
    """Sales order update model"""

    status: Optional[OrderStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    shipping_method: Optional[ShippingMethod] = None
    requested_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class OrderQuoteRequest(BaseModel):
    """Order quote request model"""

    customer_id: uuid.UUID
    line_items: List[OrderLineItem]
    shipping_address: OrderShippingAddress
    shipping_method: ShippingMethod = ShippingMethod.STANDARD
    requested_delivery_date: Optional[datetime] = None


class OrderFulfillmentRequest(BaseModel):
    """Order fulfillment request model"""

    line_items: List[Dict[str, Any]]  # line_item_id -> quantity_to_fulfill
    shipping_carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Sales order response model"""

    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    status: OrderStatus
    order_type: OrderType
    priority: int
    currency: str
    subtotal: Decimal
    tax_total: Decimal
    shipping_total: Decimal
    discount_total: Decimal
    total_amount: Decimal
    payment_status: PaymentStatus
    shipping_method: ShippingMethod
    order_date: datetime
    requested_delivery_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    line_items: List[OrderLineItem]
    created_at: datetime
    updated_at: datetime


# Database Models (SQLAlchemy - placeholder references)
# These would typically be defined in app/models/sales.py
class SalesOrder:
    """Sales order database model placeholder"""

    pass


class SalesOrderLineItem:
    """Sales order line item database model placeholder"""

    pass


class OrderHistory:
    """Order status history database model placeholder"""

    pass


class SalesOrderManagementService:
    """Comprehensive sales order management service"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis) -> dict:
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour
        self.order_number_prefix = "SO"

    async def generate_order_number(self) -> str:
        """Generate unique order number"""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        cache_key = f"order_counter:{date_str}"

        counter = await self.redis.incr(cache_key)
        await self.redis.expire(cache_key, 86400)  # Expire at end of day

        return f"{self.order_number_prefix}-{date_str}-{counter:06d}"

    async def create_order_quote(
        self, quote_request: OrderQuoteRequest
    ) -> Dict[str, Any]:
        """Generate order quote with pricing and availability"""
        try:
            # Get customer information
            customer = await self._get_customer(quote_request.customer_id)
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Calculate pricing for line items
            quoted_items = []
            subtotal = Decimal("0.00")
            total_tax = Decimal("0.00")

            for item in quote_request.line_items:
                # Get product information and pricing
                product_info = await self._get_product_info(item.product_id)
                if not product_info:
                    raise HTTPException(
                        status_code=404, detail=f"Product {item.product_id} not found"
                    )

                # Calculate customer-specific pricing
                pricing = await self._calculate_pricing(
                    customer_id=quote_request.customer_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    pricing_strategy=PricingStrategy.CUSTOMER_SPECIFIC,
                )

                # Check inventory availability
                availability = await self._check_inventory_availability(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    delivery_date=quote_request.requested_delivery_date,
                )

                # Calculate taxes
                tax_info = await self._calculate_tax(
                    product_id=item.product_id,
                    customer_id=quote_request.customer_id,
                    amount=pricing["unit_price"] * item.quantity,
                    shipping_address=quote_request.shipping_address,
                )

                quoted_item = {
                    "product_id": item.product_id,
                    "sku": product_info["sku"],
                    "product_name": product_info["name"],
                    "quantity": item.quantity,
                    "list_price": product_info["list_price"],
                    "unit_price": pricing["unit_price"],
                    "discount_percentage": pricing["discount_percentage"],
                    "discount_amount": pricing["discount_amount"],
                    "tax_rate": tax_info["tax_rate"],
                    "tax_amount": tax_info["tax_amount"],
                    "line_total": pricing["line_total"] + tax_info["tax_amount"],
                    "availability": availability,
                }

                quoted_items.append(quoted_item)
                subtotal += pricing["line_total"]
                total_tax += tax_info["tax_amount"]

            # Calculate shipping costs
            shipping_cost = await self._calculate_shipping(
                items=quoted_items,
                shipping_address=quote_request.shipping_address,
                shipping_method=quote_request.shipping_method,
                customer_id=quote_request.customer_id,
            )

            # Generate quote
            quote = {
                "quote_id": str(uuid.uuid4()),
                "customer_id": quote_request.customer_id,
                "customer_name": customer["name"],
                "quote_date": datetime.utcnow().isoformat(),
                "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "currency": "USD",
                "line_items": quoted_items,
                "subtotal": float(subtotal),
                "tax_total": float(total_tax),
                "shipping_total": float(shipping_cost["amount"]),
                "total_amount": float(subtotal + total_tax + shipping_cost["amount"]),
                "shipping_method": quote_request.shipping_method,
                "estimated_delivery_days": shipping_cost["estimated_days"],
                "notes": "Quote valid for 30 days. Prices subject to change.",
            }

            # Cache quote for quick access
            cache_key = f"quote:{quote['quote_id']}"
            await self.redis.setex(
                cache_key,
                86400 * 30,  # 30 days
                json.dumps(quote, default=str),
            )

            logger.info(
                f"Generated quote {quote['quote_id']} for customer {quote_request.customer_id}"
            )
            return quote

        except Exception as e:
            logger.error(f"Error generating quote: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate quote")

    async def create_sales_order(self, order_data: OrderCreate) -> OrderResponse:
        """Create new sales order"""
        try:
            # Generate order number
            order_number = await self.generate_order_number()

            # Validate customer
            customer = await self._get_customer(order_data.customer_id)
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Validate and price line items
            processed_items = []
            subtotal = Decimal("0.00")
            total_tax = Decimal("0.00")
            total_discount = Decimal("0.00")

            for item in order_data.line_items:
                # Get product and validate
                product_info = await self._get_product_info(item.product_id)
                if not product_info:
                    raise HTTPException(
                        status_code=404, detail=f"Product {item.product_id} not found"
                    )

                # Check inventory availability
                availability = await self._check_inventory_availability(
                    product_id=item.product_id, quantity=item.quantity
                )

                if not availability["available"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient inventory for product {product_info['sku']}",
                    )

                # Calculate pricing
                pricing = await self._calculate_pricing(
                    customer_id=order_data.customer_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                )

                # Calculate taxes
                tax_info = await self._calculate_tax(
                    product_id=item.product_id,
                    customer_id=order_data.customer_id,
                    amount=pricing["line_total"],
                    shipping_address=order_data.shipping_address,
                )

                processed_item = {
                    "id": uuid.uuid4(),
                    "product_id": item.product_id,
                    "sku": product_info["sku"],
                    "product_name": product_info["name"],
                    "quantity": item.quantity,
                    "unit_price": pricing["unit_price"],
                    "discount_percentage": pricing["discount_percentage"],
                    "discount_amount": pricing["discount_amount"],
                    "line_total": pricing["line_total"],
                    "tax_rate": tax_info["tax_rate"],
                    "tax_amount": tax_info["tax_amount"],
                    "notes": item.notes,
                }

                processed_items.append(processed_item)
                subtotal += pricing["line_total"]
                total_tax += tax_info["tax_amount"]
                total_discount += pricing["discount_amount"]

            # Calculate shipping
            shipping_cost = await self._calculate_shipping(
                items=processed_items,
                shipping_address=order_data.shipping_address,
                shipping_method=order_data.shipping_method,
                customer_id=order_data.customer_id,
            )

            # Calculate delivery date
            estimated_delivery = await self._calculate_delivery_date(
                shipping_method=order_data.shipping_method,
                shipping_address=order_data.shipping_address,
                requested_date=order_data.requested_delivery_date,
            )

            # Create order record
            order_id = uuid.uuid4()
            order_record = {
                "id": order_id,
                "order_number": order_number,
                "customer_id": order_data.customer_id,
                "status": OrderStatus.PENDING,
                "order_type": order_data.order_type,
                "priority": order_data.priority,
                "currency": order_data.currency,
                "subtotal": subtotal,
                "tax_total": total_tax,
                "shipping_total": shipping_cost["amount"],
                "discount_total": total_discount,
                "total_amount": subtotal + total_tax + shipping_cost["amount"],
                "payment_status": PaymentStatus.PENDING,
                "payment_terms": order_data.payment_terms,
                "shipping_method": order_data.shipping_method,
                "order_date": datetime.utcnow(),
                "requested_delivery_date": order_data.requested_delivery_date,
                "estimated_delivery_date": estimated_delivery,
                "shipping_address": order_data.shipping_address.dict(),
                "billing_address": order_data.billing_address.dict()
                if order_data.billing_address
                else None,
                "notes": order_data.notes,
                "internal_notes": order_data.internal_notes,
                "reference_number": order_data.reference_number,
                "sales_rep_id": order_data.sales_rep_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Save to database (mock implementation)
            await self._save_order_to_db(order_record, processed_items)

            # Create inventory allocations
            await self._create_inventory_allocations(order_id, processed_items)

            # Add to order workflow
            await self._initiate_order_workflow(order_id, order_data.order_type)

            # Cache order
            cache_key = f"order:{order_id}"
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(
                    {**order_record, "line_items": processed_items}, default=str
                ),
            )

            # Create order history entry
            await self._add_order_history(
                order_id=order_id,
                status=OrderStatus.PENDING,
                notes="Order created",
                user_id=None,
            )

            # Send notifications
            await self._send_order_notifications(order_id, "created")

            logger.info(
                f"Created order {order_number} for customer {order_data.customer_id}"
            )

            # Return order response
            return OrderResponse(
                id=order_id,
                order_number=order_number,
                customer_id=order_data.customer_id,
                customer_name=customer["name"],
                status=OrderStatus.PENDING,
                order_type=order_data.order_type,
                priority=order_data.priority,
                currency=order_data.currency,
                subtotal=subtotal,
                tax_total=total_tax,
                shipping_total=shipping_cost["amount"],
                discount_total=total_discount,
                total_amount=subtotal + total_tax + shipping_cost["amount"],
                payment_status=PaymentStatus.PENDING,
                shipping_method=order_data.shipping_method,
                order_date=order_record["order_date"],
                requested_delivery_date=order_data.requested_delivery_date,
                estimated_delivery_date=estimated_delivery,
                line_items=[OrderLineItem(**item) for item in processed_items],
                created_at=order_record["created_at"],
                updated_at=order_record["updated_at"],
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating sales order: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create sales order")

    async def get_order(self, order_id: uuid.UUID) -> Optional[OrderResponse]:
        """Get sales order by ID"""
        try:
            # Try cache first
            cache_key = f"order:{order_id}"
            cached_order = await self.redis.get(cache_key)

            if cached_order:
                order_data = json.loads(cached_order)
                return OrderResponse(**order_data)

            # Get from database
            order_data = await self._get_order_from_db(order_id)
            if not order_data:
                return None

            # Cache for future requests
            await self.redis.setex(
                cache_key, self.cache_ttl, json.dumps(order_data, default=str)
            )

            return OrderResponse(**order_data)

        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve order")

    async def update_order_status(
        self,
        order_id: uuid.UUID,
        new_status: OrderStatus,
        notes: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> OrderResponse:
        """Update order status with workflow validation"""
        try:
            # Get current order
            order = await self.get_order(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            # Validate status transition
            if not await self._validate_status_transition(order.status, new_status):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status transition from {order.status} to {new_status}",
                )

            # Update order status
            await self._update_order_status_in_db(order_id, new_status)

            # Add history entry
            await self._add_order_history(
                order_id=order_id,
                status=new_status,
                notes=notes or f"Status updated to {new_status}",
                user_id=user_id,
            )

            # Execute status-specific actions
            await self._execute_status_actions(order_id, new_status)

            # Invalidate cache
            cache_key = f"order:{order_id}"
            await self.redis.delete(cache_key)

            # Send notifications
            await self._send_order_notifications(
                order_id, f"status_changed_{new_status}"
            )

            logger.info(f"Updated order {order_id} status to {new_status}")

            # Return updated order
            return await self.get_order(order_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update order status")

    async def fulfill_order(
        self, order_id: uuid.UUID, fulfillment_request: OrderFulfillmentRequest
    ) -> Dict[str, Any]:
        """Fulfill order (full or partial)"""
        try:
            # Get order
            order = await self.get_order(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            if order.status not in [
                OrderStatus.CONFIRMED,
                OrderStatus.IN_PROGRESS,
                OrderStatus.PARTIALLY_FULFILLED,
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot fulfill order with status {order.status}",
                )

            # Process fulfillment for each line item
            fulfillment_results = []
            total_fulfilled = 0
            total_items = len(order.line_items)

            for line_item_data in fulfillment_request.line_items:
                line_item_id = uuid.UUID(line_item_data["line_item_id"])
                quantity_to_fulfill = Decimal(str(line_item_data["quantity"]))

                # Find the line item
                line_item = next(
                    (item for item in order.line_items if item.id == line_item_id), None
                )

                if not line_item:
                    raise HTTPException(
                        status_code=404, detail=f"Line item {line_item_id} not found"
                    )

                # Check inventory allocation
                allocation = await self._get_inventory_allocation(
                    order_id, line_item_id
                )
                if (
                    not allocation
                    or allocation["available_quantity"] < quantity_to_fulfill
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient allocated inventory for line item {line_item_id}",
                    )

                # Create fulfillment record
                fulfillment_record = await self._create_fulfillment_record(
                    order_id=order_id,
                    line_item_id=line_item_id,
                    product_id=line_item.product_id,
                    quantity=quantity_to_fulfill,
                    tracking_number=fulfillment_request.tracking_number,
                    carrier=fulfillment_request.shipping_carrier,
                )

                # Update inventory allocation
                await self._update_inventory_allocation(
                    order_id=order_id,
                    line_item_id=line_item_id,
                    fulfilled_quantity=quantity_to_fulfill,
                )

                fulfillment_results.append(
                    {
                        "line_item_id": line_item_id,
                        "product_id": line_item.product_id,
                        "quantity_fulfilled": quantity_to_fulfill,
                        "fulfillment_id": fulfillment_record["id"],
                    }
                )

                if quantity_to_fulfill >= line_item.quantity:
                    total_fulfilled += 1

            # Determine new order status
            if total_fulfilled == total_items:
                new_status = OrderStatus.FULFILLED
            else:
                new_status = OrderStatus.PARTIALLY_FULFILLED

            # Update order status
            await self.update_order_status(
                order_id=order_id,
                new_status=new_status,
                notes=f"Fulfillment processed - {total_fulfilled}/{total_items} items fulfilled",
            )

            # Create shipment if tracking number provided
            shipment = None
            if fulfillment_request.tracking_number:
                shipment = await self._create_shipment(
                    order_id=order_id,
                    tracking_number=fulfillment_request.tracking_number,
                    carrier=fulfillment_request.shipping_carrier,
                    line_items=fulfillment_results,
                )

            logger.info(
                f"Fulfilled order {order_id} - {total_fulfilled}/{total_items} items"
            )

            return {
                "order_id": order_id,
                "fulfillment_status": new_status,
                "fulfilled_items": total_fulfilled,
                "total_items": total_items,
                "fulfillment_results": fulfillment_results,
                "shipment": shipment,
                "notes": fulfillment_request.notes,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fulfilling order: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fulfill order")

    async def cancel_order(
        self, order_id: uuid.UUID, reason: str, user_id: Optional[uuid.UUID] = None
    ) -> OrderResponse:
        """Cancel sales order"""
        try:
            # Get order
            order = await self.get_order(order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            if order.status in [
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED,
                OrderStatus.COMPLETED,
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel order with status {order.status}",
                )

            # Release inventory allocations
            await self._release_inventory_allocations(order_id)

            # Cancel any pending shipments
            await self._cancel_pending_shipments(order_id)

            # Update order status
            await self.update_order_status(
                order_id=order_id,
                new_status=OrderStatus.CANCELLED,
                notes=f"Order cancelled: {reason}",
                user_id=user_id,
            )

            # Process refunds if payment was made
            if order.payment_status in [
                PaymentStatus.PAID,
                PaymentStatus.PARTIALLY_PAID,
            ]:
                await self._process_refund(order_id, reason)

            logger.info(f"Cancelled order {order_id}: {reason}")

            return await self.get_order(order_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to cancel order")

    async def get_orders(
        self,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[OrderStatus] = None,
        order_type: Optional[OrderType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """Get orders with filtering and pagination"""
        try:
            # Build filter conditions
            filters = {}
            if customer_id:
                filters["customer_id"] = customer_id
            if status:
                filters["status"] = status
            if order_type:
                filters["order_type"] = order_type
            if date_from:
                filters["date_from"] = date_from
            if date_to:
                filters["date_to"] = date_to

            # Get orders from database
            orders_data = await self._get_orders_from_db(
                filters=filters, page=page, size=size
            )

            orders = [OrderResponse(**order) for order in orders_data["orders"]]

            return {
                "orders": orders,
                "total": orders_data["total"],
                "page": page,
                "size": size,
                "pages": (orders_data["total"] + size - 1) // size,
            }

        except Exception as e:
            logger.error(f"Error retrieving orders: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve orders")

    async def get_order_analytics(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get sales order analytics"""
        try:
            # Set default date range if not provided
            if not date_to:
                date_to = datetime.utcnow()
            if not date_from:
                date_from = date_to - timedelta(days=30)

            # Get analytics data from database
            analytics = await self._get_order_analytics_from_db(date_from, date_to)

            return {
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "summary": {
                    "total_orders": analytics["total_orders"],
                    "total_revenue": float(analytics["total_revenue"]),
                    "average_order_value": float(analytics["average_order_value"]),
                    "total_items_sold": analytics["total_items_sold"],
                },
                "status_breakdown": analytics["status_breakdown"],
                "order_type_breakdown": analytics["order_type_breakdown"],
                "daily_trends": analytics["daily_trends"],
                "top_products": analytics["top_products"],
                "top_customers": analytics["top_customers"],
            }

        except Exception as e:
            logger.error(f"Error retrieving order analytics: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

    # Helper methods (mock implementations)
    async def _get_customer(self, customer_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get customer information"""
        # Mock implementation - would query customer database
        return {
            "id": customer_id,
            "name": "Sample Customer",
            "email": "customer@example.com",
            "customer_type": "standard",
            "credit_limit": Decimal("10000.00"),
            "payment_terms": "Net 30",
        }

    async def _get_product_info(
        self, product_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Get product information"""
        # Mock implementation - would query product database
        return {
            "id": product_id,
            "sku": f"SKU-{str(product_id)[:8]}",
            "name": "Sample Product",
            "list_price": Decimal("100.00"),
            "cost": Decimal("60.00"),
            "weight": Decimal("1.5"),
            "dimensions": {"length": 10, "width": 8, "height": 6},
        }

    async def _calculate_pricing(
        self,
        customer_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: Decimal,
        pricing_strategy: PricingStrategy = PricingStrategy.LIST_PRICE,
    ) -> Dict[str, Any]:
        """Calculate customer-specific pricing"""
        # Mock implementation - would apply pricing rules
        list_price = Decimal("100.00")
        discount_percentage = Decimal("0.00")

        # Apply volume discounts
        if quantity >= 100:
            discount_percentage = Decimal("10.00")
        elif quantity >= 50:
            discount_percentage = Decimal("5.00")

        unit_price = list_price * (1 - discount_percentage / 100)
        line_total = unit_price * quantity
        discount_amount = (list_price - unit_price) * quantity

        return {
            "unit_price": unit_price,
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "line_total": line_total,
        }

    async def _calculate_tax(
        self,
        product_id: uuid.UUID,
        customer_id: uuid.UUID,
        amount: Decimal,
        shipping_address: OrderShippingAddress,
    ) -> Dict[str, Any]:
        """Calculate tax for line item"""
        # Mock implementation - would use tax service
        tax_rate = Decimal("8.25")  # Example tax rate
        tax_amount = amount * (tax_rate / 100)

        return {
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "tax_jurisdiction": f"{shipping_address.city}, {shipping_address.state}",
        }

    async def _calculate_shipping(
        self,
        items: List[Dict[str, Any]],
        shipping_address: OrderShippingAddress,
        shipping_method: ShippingMethod,
        customer_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Calculate shipping costs"""
        # Mock implementation - would use shipping service
        base_cost = Decimal("15.00")

        if shipping_method == ShippingMethod.EXPRESS:
            base_cost *= 2
        elif shipping_method == ShippingMethod.OVERNIGHT:
            base_cost *= 3

        return {
            "amount": base_cost,
            "method": shipping_method,
            "estimated_days": 3 if shipping_method == ShippingMethod.STANDARD else 1,
        }

    async def _check_inventory_availability(
        self,
        product_id: uuid.UUID,
        quantity: Decimal,
        delivery_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Check inventory availability"""
        # Mock implementation - would check inventory system
        return {
            "available": True,
            "available_quantity": quantity + 50,
            "earliest_availability": datetime.utcnow(),
        }

    async def _calculate_delivery_date(
        self,
        shipping_method: ShippingMethod,
        shipping_address: OrderShippingAddress,
        requested_date: Optional[datetime] = None,
    ) -> datetime:
        """Calculate estimated delivery date"""
        # Mock implementation
        days_to_add = 5
        if shipping_method == ShippingMethod.EXPRESS:
            days_to_add = 2
        elif shipping_method == ShippingMethod.OVERNIGHT:
            days_to_add = 1

        estimated = datetime.utcnow() + timedelta(days=days_to_add)

        if requested_date and requested_date > estimated:
            return requested_date

        return estimated

    async def _save_order_to_db(
        self, order_record: Dict[str, Any], line_items: List[Dict[str, Any]]
    ):
        """Save order to database"""
        # Mock implementation - would save to actual database
        pass

    async def _get_order_from_db(self, order_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get order from database"""
        # Mock implementation - would query database
        return None

    async def _update_order_status_in_db(
        self, order_id: uuid.UUID, status: OrderStatus
    ):
        """Update order status in database"""
        # Mock implementation
        pass

    async def _get_orders_from_db(
        self, filters: Dict[str, Any], page: int, size: int
    ) -> Dict[str, Any]:
        """Get orders from database with filters"""
        # Mock implementation
        return {"orders": [], "total": 0}

    async def _get_order_analytics_from_db(
        self, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        """Get order analytics from database"""
        # Mock implementation
        return {
            "total_orders": 0,
            "total_revenue": Decimal("0.00"),
            "average_order_value": Decimal("0.00"),
            "total_items_sold": 0,
            "status_breakdown": {},
            "order_type_breakdown": {},
            "daily_trends": [],
            "top_products": [],
            "top_customers": [],
        }

    async def _create_inventory_allocations(
        self, order_id: uuid.UUID, line_items: List[Dict[str, Any]]
    ):
        """Create inventory allocations for order"""
        # Mock implementation - would integrate with inventory system
        pass

    async def _release_inventory_allocations(self, order_id: uuid.UUID) -> dict:
        """Release inventory allocations"""
        # Mock implementation
        pass

    async def _initiate_order_workflow(
        self, order_id: uuid.UUID, order_type: OrderType
    ):
        """Initiate order workflow"""
        # Mock implementation - would start workflow engine
        pass

    async def _validate_status_transition(
        self, current_status: OrderStatus, new_status: OrderStatus
    ) -> bool:
        """Validate if status transition is allowed"""
        # Define valid transitions
        valid_transitions = {
            OrderStatus.DRAFT: [OrderStatus.PENDING, OrderStatus.CANCELLED],
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
            OrderStatus.IN_PROGRESS: [
                OrderStatus.PARTIALLY_FULFILLED,
                OrderStatus.FULFILLED,
                OrderStatus.CANCELLED,
            ],
            OrderStatus.PARTIALLY_FULFILLED: [
                OrderStatus.FULFILLED,
                OrderStatus.CANCELLED,
            ],
            OrderStatus.FULFILLED: [OrderStatus.SHIPPED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELLED: [OrderStatus.REFUNDED],
            OrderStatus.REFUNDED: [],
        }

        return new_status in valid_transitions.get(current_status, [])

    async def _execute_status_actions(
        self, order_id: uuid.UUID, status: OrderStatus
    ) -> dict:
        """Execute actions specific to status change"""
        # Mock implementation - would execute status-specific logic
        pass

    async def _add_order_history(
        self,
        order_id: uuid.UUID,
        status: OrderStatus,
        notes: str,
        user_id: Optional[uuid.UUID] = None,
    ):
        """Add order history entry"""
        # Mock implementation - would save to order history table
        pass

    async def _send_order_notifications(
        self, order_id: uuid.UUID, event_type: str
    ) -> dict:
        """Send order notifications"""
        # Mock implementation - would send notifications
        pass

    async def _get_inventory_allocation(
        self, order_id: uuid.UUID, line_item_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Get inventory allocation for line item"""
        # Mock implementation
        return {"available_quantity": Decimal("100.00")}

    async def _create_fulfillment_record(
        self,
        order_id: uuid.UUID,
        line_item_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: Decimal,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create fulfillment record"""
        # Mock implementation
        return {"id": uuid.uuid4()}

    async def _update_inventory_allocation(
        self, order_id: uuid.UUID, line_item_id: uuid.UUID, fulfilled_quantity: Decimal
    ):
        """Update inventory allocation after fulfillment"""
        # Mock implementation
        pass

    async def _create_shipment(
        self,
        order_id: uuid.UUID,
        tracking_number: str,
        carrier: Optional[str],
        line_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create shipment record"""
        # Mock implementation
        return {
            "shipment_id": str(uuid.uuid4()),
            "tracking_number": tracking_number,
            "carrier": carrier,
            "status": "created",
        }

    async def _cancel_pending_shipments(self, order_id: uuid.UUID) -> dict:
        """Cancel pending shipments"""
        # Mock implementation
        pass

    async def _process_refund(self, order_id: uuid.UUID, reason: str) -> dict:
        """Process refund for cancelled order"""
        # Mock implementation - would integrate with payment system
        pass


# API Endpoints
@router.post("/quotes", response_model=Dict[str, Any])
async def create_order_quote(
    quote_request: OrderQuoteRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Generate order quote with pricing and availability"""
    service = SalesOrderManagementService(db, redis_client)
    return await service.create_order_quote(quote_request)


@router.post("/orders", response_model=OrderResponse)
async def create_sales_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Create new sales order"""
    service = SalesOrderManagementService(db, redis_client)
    order = await service.create_sales_order(order_data)

    # Add background task for order processing
    background_tasks.add_task(
        service._initiate_order_workflow, order.id, order.order_type
    )

    return order


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_sales_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Get sales order by ID"""
    service = SalesOrderManagementService(db, redis_client)
    order = await service.get_order(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.get("/orders", response_model=Dict[str, Any])
async def get_sales_orders(
    customer_id: Optional[uuid.UUID] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    order_type: Optional[OrderType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Get sales orders with filtering and pagination"""
    service = SalesOrderManagementService(db, redis_client)
    return await service.get_orders(
        customer_id=customer_id,
        status=status,
        order_type=order_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: uuid.UUID,
    status_update: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Update order status"""
    service = SalesOrderManagementService(db, redis_client)

    new_status = OrderStatus(status_update["status"])
    notes = status_update.get("notes")
    user_id = status_update.get("user_id")

    return await service.update_order_status(
        order_id=order_id,
        new_status=new_status,
        notes=notes,
        user_id=uuid.UUID(user_id) if user_id else None,
    )


@router.post("/orders/{order_id}/fulfill")
async def fulfill_order(
    order_id: uuid.UUID,
    fulfillment_request: OrderFulfillmentRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Fulfill order (full or partial)"""
    service = SalesOrderManagementService(db, redis_client)
    return await service.fulfill_order(order_id, fulfillment_request)


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: uuid.UUID,
    cancellation_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Cancel sales order"""
    service = SalesOrderManagementService(db, redis_client)

    reason = cancellation_data["reason"]
    user_id = cancellation_data.get("user_id")

    return await service.cancel_order(
        order_id=order_id,
        reason=reason,
        user_id=uuid.UUID(user_id) if user_id else None,
    )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_order_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Get sales order analytics"""
    service = SalesOrderManagementService(db, redis_client)
    return await service.get_order_analytics(date_from, date_to)


@router.get("/health")
async def health_check() -> None:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sales_order_management_v68",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# Include router in main application
def setup_sales_order_routes(app) -> dict:
    """Setup sales order management routes"""
    app.include_router(router)
    return app
