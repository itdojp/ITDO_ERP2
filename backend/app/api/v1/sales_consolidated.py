"""
Consolidated Sales API - Day 13 API Consolidation
Integrates functionality from all sales API versions into a single, comprehensive API.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/sales", tags=["sales"])

# =====================================
# ENUMS
# =====================================

class OrderStatus(str, Enum):
    """Sales order status"""
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    FAILED = "failed"
    REFUNDED = "refunded"

class OrderType(str, Enum):
    """Order type"""
    STANDARD = "standard"
    EXPRESS = "express"
    BULK = "bulk"
    SUBSCRIPTION = "subscription"

# =====================================
# SCHEMAS
# =====================================

class SalesOrderItemBase(BaseModel):
    """Base sales order item schema"""
    product_id: str
    quantity: int
    unit_price: Decimal
    discount_percentage: float = 0.0
    tax_percentage: float = 0.0

class SalesOrderItemCreate(SalesOrderItemBase):
    """Sales order item creation schema"""
    pass

class SalesOrderItemResponse(SalesOrderItemBase):
    """Sales order item response schema"""
    id: str
    line_total: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    net_amount: Decimal

class SalesOrderBase(BaseModel):
    """Base sales order schema"""
    customer_id: str
    order_type: OrderType = OrderType.STANDARD
    currency: str = "USD"
    notes: Optional[str] = None
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None

class SalesOrderCreate(SalesOrderBase):
    """Sales order creation schema"""
    items: List[SalesOrderItemCreate]
    expected_delivery_date: Optional[date] = None

class SalesOrderUpdate(BaseModel):
    """Sales order update schema"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None

class SalesOrderResponse(SalesOrderBase):
    """Sales order response schema"""
    id: str
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    items: List[SalesOrderItemResponse]
    subtotal: Decimal
    total_discount: Decimal
    total_tax: Decimal
    total_amount: Decimal
    order_date: datetime
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class QuoteBase(BaseModel):
    """Base quote schema"""
    customer_id: str
    valid_until: date
    currency: str = "USD"
    notes: Optional[str] = None

class QuoteCreate(QuoteBase):
    """Quote creation schema"""
    items: List[SalesOrderItemCreate]

class QuoteResponse(QuoteBase):
    """Quote response schema"""
    id: str
    quote_number: str
    items: List[SalesOrderItemResponse]
    subtotal: Decimal
    total_discount: Decimal
    total_tax: Decimal
    total_amount: Decimal
    quote_date: datetime
    is_converted: bool = False
    converted_order_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class InvoiceBase(BaseModel):
    """Base invoice schema"""
    order_id: str
    due_date: date
    payment_terms: Optional[str] = None
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    """Invoice creation schema"""
    pass

class InvoiceResponse(InvoiceBase):
    """Invoice response schema"""
    id: str
    invoice_number: str
    order: SalesOrderResponse
    invoice_date: datetime
    amount_due: Decimal
    amount_paid: Decimal
    amount_remaining: Decimal
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

class PaymentBase(BaseModel):
    """Base payment schema"""
    invoice_id: str
    amount: Decimal
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    """Payment creation schema"""
    pass

class PaymentResponse(PaymentBase):
    """Payment response schema"""
    id: str
    payment_date: datetime
    created_at: datetime

class SalesReportRequest(BaseModel):
    """Sales report request"""
    date_from: date
    date_to: date
    customer_ids: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None
    include_items: bool = False
    group_by: Optional[str] = None  # customer, product, date

class SalesReportResponse(BaseModel):
    """Sales report response"""
    period: Dict[str, date]
    summary: Dict[str, Any]
    orders: List[SalesOrderResponse]
    generated_at: datetime

# Legacy schemas for backward compatibility
class LegacySalesV21(BaseModel):
    """Legacy v21 sales format"""
    id: int
    customer_id: str
    amount: float
    date: str

# =====================================
# MOCK DATA STORES
# =====================================

# Mock databases
sales_orders_db: Dict[str, Dict[str, Any]] = {}
quotes_db: Dict[str, Dict[str, Any]] = {}
invoices_db: Dict[str, Dict[str, Any]] = {}
payments_db: Dict[str, Dict[str, Any]] = {}
legacy_sales_db: List[Dict[str, Any]] = []

# Counters for sequential numbers
order_counter = 1000
quote_counter = 2000
invoice_counter = 3000

# =====================================
# UTILITY FUNCTIONS
# =====================================

def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())

def generate_order_number() -> str:
    """Generate sequential order number"""
    global order_counter
    order_counter += 1
    return f"SO-{order_counter}"

def generate_quote_number() -> str:
    """Generate sequential quote number"""
    global quote_counter
    quote_counter += 1
    return f"QT-{quote_counter}"

def generate_invoice_number() -> str:
    """Generate sequential invoice number"""
    global invoice_counter
    invoice_counter += 1
    return f"INV-{invoice_counter}"

def calculate_item_totals(item: Dict[str, Any]) -> Dict[str, Decimal]:
    """Calculate line item totals"""
    unit_price = Decimal(str(item["unit_price"]))
    quantity = item["quantity"]
    discount_percentage = item["discount_percentage"]
    tax_percentage = item["tax_percentage"]
    
    line_total = unit_price * quantity
    discount_amount = line_total * Decimal(str(discount_percentage)) / 100
    subtotal = line_total - discount_amount
    tax_amount = subtotal * Decimal(str(tax_percentage)) / 100
    net_amount = subtotal + tax_amount
    
    return {
        "line_total": line_total,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "net_amount": net_amount
    }

def calculate_order_totals(items: List[Dict[str, Any]]) -> Dict[str, Decimal]:
    """Calculate order totals"""
    subtotal = Decimal("0")
    total_discount = Decimal("0")
    total_tax = Decimal("0")
    
    for item in items:
        totals = calculate_item_totals(item)
        subtotal += totals["line_total"]
        total_discount += totals["discount_amount"]
        total_tax += totals["tax_amount"]
    
    total_amount = subtotal - total_discount + total_tax
    
    return {
        "subtotal": subtotal,
        "total_discount": total_discount,
        "total_tax": total_tax,
        "total_amount": total_amount
    }

async def get_current_user():
    """Mock current user"""
    return {"id": "current-user", "is_admin": True}

def validate_customer_exists(customer_id: str) -> bool:
    """Mock customer validation"""
    return True  # Mock validation

def validate_product_exists(product_id: str) -> bool:
    """Mock product validation"""
    return True  # Mock validation

# =====================================
# QUOTES MANAGEMENT
# =====================================

@router.post("/quotes", response_model=QuoteResponse, status_code=201)
async def create_quote(
    quote: QuoteCreate,
    current_user = Depends(get_current_user)
) -> QuoteResponse:
    """Create a new sales quote"""
    # Validate customer exists
    if not validate_customer_exists(quote.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Validate all products exist
    for item in quote.items:
        if not validate_product_exists(item.product_id):
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
    
    quote_id = generate_id()
    quote_number = generate_quote_number()
    now = datetime.utcnow()
    
    # Process items
    processed_items = []
    for item_data in quote.items:
        item_id = generate_id()
        item_dict = item_data.dict()
        item_dict["id"] = item_id
        
        # Calculate totals
        totals = calculate_item_totals(item_dict)
        item_dict.update(totals)
        
        processed_items.append(item_dict)
    
    # Calculate order totals
    order_totals = calculate_order_totals(processed_items)
    
    new_quote = {
        "id": quote_id,
        "quote_number": quote_number,
        "customer_id": quote.customer_id,
        "valid_until": quote.valid_until,
        "currency": quote.currency,
        "notes": quote.notes,
        "items": processed_items,
        "quote_date": now,
        "is_converted": False,
        "converted_order_id": None,
        "created_at": now,
        "updated_at": now,
        **order_totals
    }
    
    quotes_db[quote_id] = new_quote
    
    # Convert items to response format
    response_items = [SalesOrderItemResponse(**item) for item in processed_items]
    
    return QuoteResponse(**{**new_quote, "items": response_items})

@router.get("/quotes", response_model=List[QuoteResponse])
async def list_quotes(
    customer_id: Optional[str] = None,
    is_converted: Optional[bool] = None,
    current_user = Depends(get_current_user)
) -> List[QuoteResponse]:
    """List quotes with filtering"""
    filtered_quotes = []
    
    for quote_data in quotes_db.values():
        if customer_id and quote_data["customer_id"] != customer_id:
            continue
        if is_converted is not None and quote_data["is_converted"] != is_converted:
            continue
        
        # Convert items to response format
        response_items = [SalesOrderItemResponse(**item) for item in quote_data["items"]]
        quote_response = QuoteResponse(**{**quote_data, "items": response_items})
        filtered_quotes.append(quote_response)
    
    return filtered_quotes

@router.post("/quotes/{quote_id}/convert", response_model=SalesOrderResponse)
async def convert_quote_to_order(
    quote_id: str,
    current_user = Depends(get_current_user)
) -> SalesOrderResponse:
    """Convert a quote to a sales order"""
    if quote_id not in quotes_db:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote_data = quotes_db[quote_id]
    
    if quote_data["is_converted"]:
        raise HTTPException(status_code=400, detail="Quote has already been converted")
    
    # Create order from quote
    order_create = SalesOrderCreate(
        customer_id=quote_data["customer_id"],
        currency=quote_data["currency"],
        notes=f"Converted from quote {quote_data['quote_number']}",
        items=[SalesOrderItemCreate(**item) for item in quote_data["items"]]
    )
    
    order_response = await create_sales_order(order_create)
    
    # Update quote
    quote_data["is_converted"] = True
    quote_data["converted_order_id"] = order_response.id
    quote_data["updated_at"] = datetime.utcnow()
    
    return order_response

# =====================================
# SALES ORDERS MANAGEMENT
# =====================================

@router.post("/orders", response_model=SalesOrderResponse, status_code=201)
async def create_sales_order(
    order: SalesOrderCreate,
    current_user = Depends(get_current_user)
) -> SalesOrderResponse:
    """Create a new sales order"""
    # Validate customer exists
    if not validate_customer_exists(order.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Validate all products exist
    for item in order.items:
        if not validate_product_exists(item.product_id):
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
    
    order_id = generate_id()
    order_number = generate_order_number()
    now = datetime.utcnow()
    
    # Process items
    processed_items = []
    for item_data in order.items:
        item_id = generate_id()
        item_dict = item_data.dict()
        item_dict["id"] = item_id
        
        # Calculate totals
        totals = calculate_item_totals(item_dict)
        item_dict.update(totals)
        
        processed_items.append(item_dict)
    
    # Calculate order totals
    order_totals = calculate_order_totals(processed_items)
    
    new_order = {
        "id": order_id,
        "order_number": order_number,
        "customer_id": order.customer_id,
        "order_type": order.order_type,
        "status": OrderStatus.DRAFT,
        "payment_status": PaymentStatus.PENDING,
        "currency": order.currency,
        "notes": order.notes,
        "shipping_address": order.shipping_address,
        "billing_address": order.billing_address,
        "items": processed_items,
        "order_date": now,
        "expected_delivery_date": order.expected_delivery_date,
        "actual_delivery_date": None,
        "created_at": now,
        "updated_at": now,
        **order_totals
    }
    
    sales_orders_db[order_id] = new_order
    
    # Convert items to response format
    response_items = [SalesOrderItemResponse(**item) for item in processed_items]
    
    return SalesOrderResponse(**{**new_order, "items": response_items})

@router.get("/orders", response_model=List[SalesOrderResponse])
async def list_sales_orders(
    customer_id: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_user)
) -> List[SalesOrderResponse]:
    """List sales orders with filtering"""
    filtered_orders = []
    
    for order_data in sales_orders_db.values():
        if customer_id and order_data["customer_id"] != customer_id:
            continue
        if status and order_data["status"] != status:
            continue
        if payment_status and order_data["payment_status"] != payment_status:
            continue
        if date_from and order_data["order_date"].date() < date_from:
            continue
        if date_to and order_data["order_date"].date() > date_to:
            continue
        
        # Convert items to response format
        response_items = [SalesOrderItemResponse(**item) for item in order_data["items"]]
        order_response = SalesOrderResponse(**{**order_data, "items": response_items})
        filtered_orders.append(order_response)
    
    # Sort by order date (newest first) and apply pagination
    filtered_orders.sort(key=lambda x: x.order_date, reverse=True)
    return filtered_orders[skip:skip + limit]

@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order(
    order_id: str,
    current_user = Depends(get_current_user)
) -> SalesOrderResponse:
    """Get a specific sales order"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    order_data = sales_orders_db[order_id]
    response_items = [SalesOrderItemResponse(**item) for item in order_data["items"]]
    
    return SalesOrderResponse(**{**order_data, "items": response_items})

@router.put("/orders/{order_id}", response_model=SalesOrderResponse)
async def update_sales_order(
    order_id: str,
    order_update: SalesOrderUpdate,
    current_user = Depends(get_current_user)
) -> SalesOrderResponse:
    """Update a sales order"""
    if order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    order_data = sales_orders_db[order_id].copy()
    update_data = order_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        order_data[field] = value
    
    order_data["updated_at"] = datetime.utcnow()
    sales_orders_db[order_id] = order_data
    
    response_items = [SalesOrderItemResponse(**item) for item in order_data["items"]]
    return SalesOrderResponse(**{**order_data, "items": response_items})

# =====================================
# INVOICING
# =====================================

@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    invoice: InvoiceCreate,
    current_user = Depends(get_current_user)
) -> InvoiceResponse:
    """Create an invoice from a sales order"""
    if invoice.order_id not in sales_orders_db:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    order_data = sales_orders_db[invoice.order_id]
    
    # Check if invoice already exists for this order
    for existing_invoice in invoices_db.values():
        if existing_invoice["order_id"] == invoice.order_id:
            raise HTTPException(
                status_code=400, 
                detail="Invoice already exists for this order"
            )
    
    invoice_id = generate_id()
    invoice_number = generate_invoice_number()
    now = datetime.utcnow()
    
    new_invoice = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "order_id": invoice.order_id,
        "due_date": invoice.due_date,
        "payment_terms": invoice.payment_terms,
        "notes": invoice.notes,
        "invoice_date": now,
        "amount_due": order_data["total_amount"],
        "amount_paid": Decimal("0"),
        "amount_remaining": order_data["total_amount"],
        "payment_status": PaymentStatus.PENDING,
        "created_at": now,
        "updated_at": now
    }
    
    invoices_db[invoice_id] = new_invoice
    
    # Create response with order details
    order_items = [SalesOrderItemResponse(**item) for item in order_data["items"]]
    order_response = SalesOrderResponse(**{**order_data, "items": order_items})
    
    return InvoiceResponse(**{**new_invoice, "order": order_response})

@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    payment_status: Optional[PaymentStatus] = None,
    overdue_only: bool = False,
    current_user = Depends(get_current_user)
) -> List[InvoiceResponse]:
    """List invoices with filtering"""
    filtered_invoices = []
    today = datetime.utcnow().date()
    
    for invoice_data in invoices_db.values():
        if payment_status and invoice_data["payment_status"] != payment_status:
            continue
        if overdue_only and (invoice_data["due_date"] >= today or 
                           invoice_data["payment_status"] == PaymentStatus.PAID):
            continue
        
        # Get order details
        order_data = sales_orders_db[invoice_data["order_id"]]
        order_items = [SalesOrderItemResponse(**item) for item in order_data["items"]]
        order_response = SalesOrderResponse(**{**order_data, "items": order_items})
        
        invoice_response = InvoiceResponse(**{**invoice_data, "order": order_response})
        filtered_invoices.append(invoice_response)
    
    return filtered_invoices

# =====================================
# PAYMENTS
# =====================================

@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payment: PaymentCreate,
    current_user = Depends(get_current_user)
) -> PaymentResponse:
    """Record a payment against an invoice"""
    if payment.invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice_data = invoices_db[payment.invoice_id]
    
    if payment.amount > invoice_data["amount_remaining"]:
        raise HTTPException(
            status_code=400,
            detail="Payment amount exceeds remaining invoice amount"
        )
    
    payment_id = generate_id()
    now = datetime.utcnow()
    
    new_payment = {
        "id": payment_id,
        "invoice_id": payment.invoice_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "payment_date": now,
        "created_at": now
    }
    
    payments_db[payment_id] = new_payment
    
    # Update invoice
    invoice_data["amount_paid"] += payment.amount
    invoice_data["amount_remaining"] -= payment.amount
    
    if invoice_data["amount_remaining"] <= 0:
        invoice_data["payment_status"] = PaymentStatus.PAID
    elif invoice_data["amount_paid"] > 0:
        invoice_data["payment_status"] = PaymentStatus.PARTIAL
    
    invoice_data["updated_at"] = now
    
    return PaymentResponse(**new_payment)

@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    invoice_id: Optional[str] = None,
    current_user = Depends(get_current_user)
) -> List[PaymentResponse]:
    """List payments"""
    filtered_payments = []
    
    for payment_data in payments_db.values():
        if invoice_id and payment_data["invoice_id"] != invoice_id:
            continue
        
        filtered_payments.append(PaymentResponse(**payment_data))
    
    return filtered_payments

# =====================================
# REPORTS AND ANALYTICS
# =====================================

@router.post("/reports", response_model=SalesReportResponse)
async def generate_sales_report(
    request: SalesReportRequest,
    current_user = Depends(get_current_user)
) -> SalesReportResponse:
    """Generate comprehensive sales report"""
    # Filter orders
    filtered_orders = []
    for order_data in sales_orders_db.values():
        order_date = order_data["order_date"].date()
        if order_date < request.date_from or order_date > request.date_to:
            continue
        if request.customer_ids and order_data["customer_id"] not in request.customer_ids:
            continue
        if request.product_ids:
            has_product = any(
                item["product_id"] in request.product_ids 
                for item in order_data["items"]
            )
            if not has_product:
                continue
        
        # Convert items to response format
        response_items = [SalesOrderItemResponse(**item) for item in order_data["items"]]
        order_response = SalesOrderResponse(**{**order_data, "items": response_items})
        filtered_orders.append(order_response)
    
    # Generate summary
    total_orders = len(filtered_orders)
    total_revenue = sum(order.total_amount for order in filtered_orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal("0")
    
    summary = {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "average_order_value": float(avg_order_value),
        "period_days": (request.date_to - request.date_from).days + 1
    }
    
    return SalesReportResponse(
        period={"from": request.date_from, "to": request.date_to},
        summary=summary,
        orders=filtered_orders,
        generated_at=datetime.utcnow()
    )

@router.get("/analytics/dashboard")
async def get_sales_dashboard(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get sales dashboard analytics"""
    today = datetime.utcnow().date()
    
    # Calculate metrics
    total_orders = len(sales_orders_db)
    total_revenue = sum(
        Decimal(str(order["total_amount"])) 
        for order in sales_orders_db.values()
    )
    
    pending_orders = len([
        order for order in sales_orders_db.values()
        if order["status"] in [OrderStatus.DRAFT, OrderStatus.PENDING]
    ])
    
    overdue_invoices = len([
        invoice for invoice in invoices_db.values()
        if (invoice["due_date"] < today and 
            invoice["payment_status"] != PaymentStatus.PAID)
    ])
    
    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "pending_orders": pending_orders,
        "overdue_invoices": overdue_invoices,
        "total_quotes": len(quotes_db),
        "converted_quotes": len([q for q in quotes_db.values() if q["is_converted"]]),
        "last_updated": datetime.utcnow().isoformat()
    }

# =====================================
# BACKWARD COMPATIBILITY
# =====================================

@router.post("/sales-v21", response_model=LegacySalesV21)
async def create_sales_v21(
    customer_id: str, 
    amount: float
) -> LegacySalesV21:
    """Legacy v21 endpoint for backward compatibility"""
    legacy_id = len(legacy_sales_db) + 1
    
    # Create in new format
    order_create = SalesOrderCreate(
        customer_id=customer_id,
        items=[SalesOrderItemCreate(
            product_id="LEGACY_PRODUCT",
            quantity=1,
            unit_price=Decimal(str(amount)),
            discount_percentage=0.0,
            tax_percentage=0.0
        )]
    )
    
    order_response = await create_sales_order(order_create)
    
    # Store in legacy format
    legacy_sale = {
        "id": legacy_id,
        "customer_id": customer_id,
        "amount": amount,
        "date": datetime.utcnow().isoformat()
    }
    legacy_sales_db.append(legacy_sale)
    
    return LegacySalesV21(**legacy_sale)

@router.get("/sales-v21", response_model=List[LegacySalesV21])
async def list_sales_v21() -> List[LegacySalesV21]:
    """Legacy v21 list endpoint for backward compatibility"""
    return [LegacySalesV21(**sale) for sale in legacy_sales_db]

# =====================================
# HEALTH CHECK
# =====================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """API health check"""
    return {
        "status": "healthy",
        "total_orders": len(sales_orders_db),
        "total_quotes": len(quotes_db),
        "total_invoices": len(invoices_db),
        "total_payments": len(payments_db),
        "api_version": "consolidated_v1.0",
        "timestamp": datetime.utcnow().isoformat()
    }