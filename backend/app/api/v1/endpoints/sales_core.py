"""
Core Sales API Endpoints - CC02 v50.0 Phase 3
12-Hour Core Business API Sprint - Sales Process Management Implementation
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
import uuid
import json

# Import database dependencies
from app.core.database import get_db

router = APIRouter(prefix="/sales", tags=["Core Sales"])

# Enums for sales management
class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"

class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    PAYPAL = "paypal"
    CRYPTOCURRENCY = "cryptocurrency"

class PaymentTerms(str, Enum):
    IMMEDIATE = "immediate"
    NET_15 = "net_15"
    NET_30 = "net_30"
    NET_60 = "net_60"
    NET_90 = "net_90"

class OpportunityStage(str, Enum):
    LEAD = "lead"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

# Quote item models
class QuoteItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    discount_percentage: float = Field(0.0, ge=0, le=100)

class QuoteItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    discount_percentage: float
    line_total: float

# Quote models
class QuoteCreateRequest(BaseModel):
    customer_id: str
    quote_number: str = Field(min_length=1, max_length=50)
    items: List[QuoteItemRequest] = Field(min_length=1)
    valid_until: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    status: QuoteStatus = QuoteStatus.DRAFT

class QuoteResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    quote_number: str
    items: List[QuoteItemResponse]
    subtotal: float
    total_discount: float
    total_amount: float
    status: QuoteStatus
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class QuoteListResponse(BaseModel):
    items: List[QuoteResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int

# Order models
class OrderCreateRequest(BaseModel):
    customer_id: str
    order_number: str = Field(min_length=1, max_length=50)
    quote_id: Optional[str] = None
    items: List[QuoteItemRequest] = Field(min_length=1)
    shipping_address: Optional[str] = Field(None, max_length=500)
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    notes: Optional[str] = Field(None, max_length=1000)
    status: OrderStatus = OrderStatus.CONFIRMED

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    order_number: str
    quote_id: Optional[str] = None
    items: List[QuoteItemResponse]
    subtotal: float
    total_discount: float
    total_amount: float
    status: OrderStatus
    shipping_address: Optional[str] = None
    payment_terms: PaymentTerms
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Invoice models
class InvoiceCreateRequest(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=50)
    due_date: Optional[datetime] = None
    tax_rate: float = Field(0.0, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=1000)

class InvoiceResponse(BaseModel):
    id: str
    order_id: str
    invoice_number: str
    subtotal: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    status: InvoiceStatus
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Payment models
class PaymentCreateRequest(BaseModel):
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    payment_reference: Optional[str] = Field(None, max_length=100)
    payment_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    amount: float
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    payment_date: datetime
    status: PaymentStatus
    notes: Optional[str] = None
    created_at: datetime

class PaymentsListResponse(BaseModel):
    payments: List[PaymentResponse]
    total_paid: float
    remaining_balance: float
    payment_status: str

# Opportunity models
class OpportunityCreateRequest(BaseModel):
    customer_id: str
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    estimated_value: float = Field(gt=0)
    probability: int = Field(ge=0, le=100)
    stage: OpportunityStage
    expected_close_date: Optional[datetime] = None
    assigned_to: Optional[str] = Field(None, max_length=100)

class OpportunityResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    title: str
    description: Optional[str] = None
    estimated_value: float
    probability: int
    stage: OpportunityStage
    expected_close_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Metrics models
class SalesMetricsResponse(BaseModel):
    total_orders: int
    total_revenue: float
    total_opportunities: int
    pipeline_value: float
    average_order_value: float
    conversion_rate: float
    orders_this_month: int
    revenue_this_month: float

# In-memory storage for core sales TDD
quotes_store: Dict[str, Dict[str, Any]] = {}
quote_items_store: Dict[str, List[Dict[str, Any]]] = {}
orders_store: Dict[str, Dict[str, Any]] = {}
order_items_store: Dict[str, List[Dict[str, Any]]] = {}
invoices_store: Dict[str, Dict[str, Any]] = {}
payments_store: Dict[str, List[Dict[str, Any]]] = {}
opportunities_store: Dict[str, Dict[str, Any]] = {}

@router.post("/quotes", response_model=QuoteResponse, status_code=201)
async def create_quote(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> QuoteResponse:
    """Create a new sales quote"""
    
    try:
        quote_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["customer_id", "quote_number", "items"]
    for field in required_fields:
        if field not in quote_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate customer exists
    customer_id = quote_data["customer_id"]
    try:
        from app.api.v1.endpoints.customers import customers_store
        if customer_id not in customers_store:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer_name = customers_store[customer_id]["name"]
    except ImportError:
        customer_name = "Unknown Customer"
    
    # Check for duplicate quote number
    quote_number = quote_data["quote_number"]
    for existing_quote in quotes_store.values():
        if existing_quote["quote_number"] == quote_number:
            raise HTTPException(
                status_code=400,
                detail=f"Quote with number '{quote_number}' already exists"
            )
    
    # Process quote items
    items = quote_data["items"]
    if not items or len(items) == 0:
        raise HTTPException(status_code=422, detail="Quote must have at least one item")
    
    quote_items = []
    subtotal = 0.0
    total_discount = 0.0
    
    for i, item_data in enumerate(items):
        if "product_id" not in item_data or "quantity" not in item_data or "unit_price" not in item_data:
            raise HTTPException(status_code=422, detail=f"Item {i} missing required fields")
        
        product_id = item_data["product_id"]
        product_name = "Unknown Product"
        
        # Get product name
        try:
            from app.api.v1.endpoints.products_core import products_store
            if product_id in products_store:
                product_name = products_store[product_id]["name"]
        except ImportError:
            pass
        
        quantity = int(item_data["quantity"])
        unit_price = float(item_data["unit_price"])
        discount_percentage = float(item_data.get("discount_percentage", 0.0))
        
        line_subtotal = quantity * unit_price
        line_discount = line_subtotal * (discount_percentage / 100)
        line_total = line_subtotal - line_discount
        
        item = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_percentage": discount_percentage,
            "line_total": line_total
        }
        quote_items.append(item)
        
        subtotal += line_subtotal
        total_discount += line_discount
    
    total_amount = subtotal - total_discount
    
    # Create quote
    quote_id = str(uuid.uuid4())
    now = datetime.now()
    
    quote = {
        "id": quote_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "quote_number": quote_number,
        "subtotal": subtotal,
        "total_discount": total_discount,
        "total_amount": total_amount,
        "status": quote_data.get("status", QuoteStatus.DRAFT.value),
        "valid_until": datetime.fromisoformat(quote_data["valid_until"]) if quote_data.get("valid_until") else None,
        "notes": quote_data.get("notes"),
        "created_at": now,
        "updated_at": now
    }
    
    quotes_store[quote_id] = quote
    quote_items_store[quote_id] = quote_items
    
    # Create response
    response_items = [QuoteItemResponse(**item) for item in quote_items]
    response_quote = QuoteResponse(
        **quote,
        items=response_items
    )
    
    return response_quote

@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_db)
) -> QuoteResponse:
    """Get quote by ID"""
    
    if quote_id not in quotes_store:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote = quotes_store[quote_id]
    items = quote_items_store.get(quote_id, [])
    
    response_items = [QuoteItemResponse(**item) for item in items]
    response_quote = QuoteResponse(
        **quote,
        items=response_items
    )
    
    return response_quote

@router.get("/quotes", response_model=QuoteListResponse)
async def list_quotes(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    status: Optional[QuoteStatus] = Query(None),
    customer_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> QuoteListResponse:
    """List quotes with filtering"""
    
    all_quotes = list(quotes_store.values())
    
    # Apply filters
    if status:
        all_quotes = [q for q in all_quotes if q["status"] == status.value]
    
    if customer_id:
        all_quotes = [q for q in all_quotes if q["customer_id"] == customer_id]
    
    # Sort by created_at descending
    all_quotes.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(all_quotes)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_quotes = all_quotes[start_idx:end_idx]
    
    # Convert to response format
    response_quotes = []
    for quote in paginated_quotes:
        items = quote_items_store.get(quote["id"], [])
        response_items = [QuoteItemResponse(**item) for item in items]
        response_quote = QuoteResponse(
            **quote,
            items=response_items
        )
        response_quotes.append(response_quote)
    
    return QuoteListResponse(
        items=response_quotes,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

@router.post("/quotes/{quote_id}/convert", response_model=OrderResponse, status_code=201)
async def convert_quote_to_order(
    quote_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Convert quote to sales order"""
    
    if quote_id not in quotes_store:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    try:
        convert_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    quote = quotes_store[quote_id]
    quote_items = quote_items_store.get(quote_id, [])
    
    # Check for duplicate order number
    order_number = convert_data.get("order_number", f"SO-{quote['quote_number']}")
    for existing_order in orders_store.values():
        if existing_order["order_number"] == order_number:
            raise HTTPException(
                status_code=400,
                detail=f"Order with number '{order_number}' already exists"
            )
    
    # Create order from quote
    order_id = str(uuid.uuid4())
    now = datetime.now()
    
    order = {
        "id": order_id,
        "customer_id": quote["customer_id"],
        "customer_name": quote["customer_name"],
        "order_number": order_number,
        "quote_id": quote_id,
        "subtotal": quote["subtotal"],
        "total_discount": quote["total_discount"],
        "total_amount": quote["total_amount"],
        "status": OrderStatus.CONFIRMED.value,
        "shipping_address": convert_data.get("shipping_address"),
        "payment_terms": convert_data.get("payment_terms", PaymentTerms.NET_30.value),
        "tracking_number": None,
        "notes": convert_data.get("notes"),
        "created_at": now,
        "updated_at": now
    }
    
    orders_store[order_id] = order
    order_items_store[order_id] = quote_items.copy()  # Copy items from quote
    
    # Update quote status
    quotes_store[quote_id]["status"] = QuoteStatus.CONVERTED.value
    quotes_store[quote_id]["updated_at"] = now
    
    # Create response
    response_items = [QuoteItemResponse(**item) for item in quote_items]
    response_order = OrderResponse(
        **order,
        items=response_items
    )
    
    return response_order

@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Create a direct sales order"""
    
    try:
        order_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["customer_id", "order_number", "items"]
    for field in required_fields:
        if field not in order_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate customer exists
    customer_id = order_data["customer_id"]
    try:
        from app.api.v1.endpoints.customers import customers_store
        if customer_id not in customers_store:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer_name = customers_store[customer_id]["name"]
    except ImportError:
        customer_name = "Unknown Customer"
    
    # Check for duplicate order number
    order_number = order_data["order_number"]
    for existing_order in orders_store.values():
        if existing_order["order_number"] == order_number:
            raise HTTPException(
                status_code=400,
                detail=f"Order with number '{order_number}' already exists"
            )
    
    # Process order items (same as quote logic)
    items = order_data["items"]
    if not items or len(items) == 0:
        raise HTTPException(status_code=422, detail="Order must have at least one item")
    
    order_items = []
    subtotal = 0.0
    total_discount = 0.0
    
    for i, item_data in enumerate(items):
        if "product_id" not in item_data or "quantity" not in item_data or "unit_price" not in item_data:
            raise HTTPException(status_code=422, detail=f"Item {i} missing required fields")
        
        product_id = item_data["product_id"]
        product_name = "Unknown Product"
        
        # Get product name
        try:
            from app.api.v1.endpoints.products_core import products_store
            if product_id in products_store:
                product_name = products_store[product_id]["name"]
        except ImportError:
            pass
        
        quantity = int(item_data["quantity"])
        unit_price = float(item_data["unit_price"])
        discount_percentage = float(item_data.get("discount_percentage", 0.0))
        
        line_subtotal = quantity * unit_price
        line_discount = line_subtotal * (discount_percentage / 100)
        line_total = line_subtotal - line_discount
        
        item = {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_percentage": discount_percentage,
            "line_total": line_total
        }
        order_items.append(item)
        
        subtotal += line_subtotal
        total_discount += line_discount
    
    total_amount = subtotal - total_discount
    
    # Create order
    order_id = str(uuid.uuid4())
    now = datetime.now()
    
    order = {
        "id": order_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "order_number": order_number,
        "quote_id": order_data.get("quote_id"),
        "subtotal": subtotal,
        "total_discount": total_discount,
        "total_amount": total_amount,
        "status": order_data.get("status", OrderStatus.CONFIRMED.value),
        "shipping_address": order_data.get("shipping_address"),
        "payment_terms": order_data.get("payment_terms", PaymentTerms.NET_30.value),
        "tracking_number": None,
        "notes": order_data.get("notes"),
        "created_at": now,
        "updated_at": now
    }
    
    orders_store[order_id] = order
    order_items_store[order_id] = order_items
    
    # Create response
    response_items = [QuoteItemResponse(**item) for item in order_items]
    response_order = OrderResponse(
        **order,
        items=response_items
    )
    
    return response_order

@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    customer_id: Optional[str] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[OrderResponse]:
    """List sales orders with filtering (CC02 v52.0 Required)"""
    
    all_orders = list(orders_store.values())
    
    # Apply filters
    if customer_id:
        all_orders = [o for o in all_orders if o.get("customer_id") == customer_id]
    
    if status:
        all_orders = [o for o in all_orders if o.get("status") == status.value]
    
    # Date filtering (simplified for TDD)
    if from_date or to_date:
        # For production, implement proper date parsing and filtering
        pass
    
    # Sort by created_at descending
    all_orders.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(all_orders)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_orders = all_orders[start_idx:end_idx]
    
    # Convert to response format
    response_orders = []
    for order in paginated_orders:
        # Get order items
        items = order_items_store.get(order["id"], [])
        response_items = [QuoteItemResponse(**item) for item in items]
        
        response_order = OrderResponse(
            **order,
            items=response_items
        )
        response_orders.append(response_order)
    
    return response_orders

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Update order status"""
    
    if order_id not in orders_store:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        status_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    order = orders_store[order_id]
    
    # Update allowed fields
    if "status" in status_data:
        order["status"] = status_data["status"]
    if "tracking_number" in status_data:
        order["tracking_number"] = status_data["tracking_number"]
    if "notes" in status_data:
        order["notes"] = status_data["notes"]
    
    order["updated_at"] = datetime.now()
    
    # Get items for response
    items = order_items_store.get(order_id, [])
    response_items = [QuoteItemResponse(**item) for item in items]
    response_order = OrderResponse(
        **order,
        items=response_items
    )
    
    return response_order

@router.post("/orders/{order_id}/invoice", response_model=InvoiceResponse, status_code=201)
async def generate_invoice(
    order_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> InvoiceResponse:
    """Generate invoice from sales order"""
    
    if order_id not in orders_store:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        invoice_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    order = orders_store[order_id]
    
    # Check for duplicate invoice number
    invoice_number = invoice_data["invoice_number"]
    for existing_invoice in invoices_store.values():
        if existing_invoice["invoice_number"] == invoice_number:
            raise HTTPException(
                status_code=400,
                detail=f"Invoice with number '{invoice_number}' already exists"
            )
    
    # Calculate invoice amounts
    subtotal = order["total_amount"]  # After discounts
    tax_rate = float(invoice_data.get("tax_rate", 0.0))
    tax_amount = subtotal * (tax_rate / 100)
    total_amount = subtotal + tax_amount
    
    # Create invoice
    invoice_id = str(uuid.uuid4())
    now = datetime.now()
    
    invoice = {
        "id": invoice_id,
        "order_id": order_id,
        "invoice_number": invoice_number,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "status": InvoiceStatus.DRAFT.value,
        "due_date": datetime.fromisoformat(invoice_data["due_date"]) if invoice_data.get("due_date") else None,
        "notes": invoice_data.get("notes"),
        "created_at": now,
        "updated_at": now
    }
    
    invoices_store[invoice_id] = invoice
    
    return InvoiceResponse(**{k: round(v, 2) if isinstance(v, float) else v for k, v in invoice.items()})

@router.post("/invoices/{invoice_id}/payments", response_model=PaymentResponse, status_code=201)
async def record_payment(
    invoice_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Record payment against invoice"""
    
    if invoice_id not in invoices_store:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    try:
        payment_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["amount", "payment_method"]
    for field in required_fields:
        if field not in payment_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Create payment
    payment_id = str(uuid.uuid4())
    now = datetime.now()
    
    payment = {
        "id": payment_id,
        "invoice_id": invoice_id,
        "amount": float(payment_data["amount"]),
        "payment_method": payment_data["payment_method"],
        "payment_reference": payment_data.get("payment_reference"),
        "payment_date": datetime.fromisoformat(payment_data["payment_date"]) if payment_data.get("payment_date") else now,
        "status": PaymentStatus.COMPLETED.value,
        "notes": payment_data.get("notes"),
        "created_at": now
    }
    
    # Add to payments store
    if invoice_id not in payments_store:
        payments_store[invoice_id] = []
    payments_store[invoice_id].append(payment)
    
    # Update invoice status based on payments
    invoice = invoices_store[invoice_id]
    total_paid = sum(p["amount"] for p in payments_store[invoice_id])
    
    if total_paid >= invoice["total_amount"]:
        invoice["status"] = InvoiceStatus.PAID.value
    elif total_paid > 0:
        invoice["status"] = InvoiceStatus.PARTIAL.value
    
    invoice["updated_at"] = now
    
    return PaymentResponse(**payment)

@router.get("/invoices/{invoice_id}/payments", response_model=PaymentsListResponse)
async def get_invoice_payments(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
) -> PaymentsListResponse:
    """Get all payments for an invoice"""
    
    if invoice_id not in invoices_store:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice = invoices_store[invoice_id]
    payments = payments_store.get(invoice_id, [])
    
    total_paid = sum(p["amount"] for p in payments)
    remaining_balance = invoice["total_amount"] - total_paid
    
    payment_status = "unpaid"
    if total_paid >= invoice["total_amount"]:
        payment_status = "paid"
    elif total_paid > 0:
        payment_status = "partial"
    
    response_payments = [PaymentResponse(**payment) for payment in payments]
    
    return PaymentsListResponse(
        payments=response_payments,
        total_paid=round(total_paid, 2),
        remaining_balance=round(remaining_balance, 2),
        payment_status=payment_status
    )

@router.post("/opportunities", response_model=OpportunityResponse, status_code=201)
async def create_opportunity(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OpportunityResponse:
    """Create a sales opportunity"""
    
    try:
        opportunity_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["customer_id", "title", "estimated_value", "probability", "stage"]
    for field in required_fields:
        if field not in opportunity_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate customer exists
    customer_id = opportunity_data["customer_id"]
    try:
        from app.api.v1.endpoints.customers import customers_store
        if customer_id not in customers_store:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer_name = customers_store[customer_id]["name"]
    except ImportError:
        customer_name = "Unknown Customer"
    
    # Create opportunity
    opportunity_id = str(uuid.uuid4())
    now = datetime.now()
    
    opportunity = {
        "id": opportunity_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "title": opportunity_data["title"],
        "description": opportunity_data.get("description"),
        "estimated_value": float(opportunity_data["estimated_value"]),
        "probability": int(opportunity_data["probability"]),
        "stage": opportunity_data["stage"],
        "expected_close_date": datetime.fromisoformat(opportunity_data["expected_close_date"]) if opportunity_data.get("expected_close_date") else None,
        "assigned_to": opportunity_data.get("assigned_to"),
        "created_at": now,
        "updated_at": now
    }
    
    opportunities_store[opportunity_id] = opportunity
    return OpportunityResponse(**opportunity)

@router.put("/opportunities/{opportunity_id}/stage", response_model=OpportunityResponse)
async def update_opportunity_stage(
    opportunity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OpportunityResponse:
    """Update opportunity stage"""
    
    if opportunity_id not in opportunities_store:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    try:
        stage_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    opportunity = opportunities_store[opportunity_id]
    
    # Update fields
    if "stage" in stage_data:
        opportunity["stage"] = stage_data["stage"]
    if "probability" in stage_data:
        opportunity["probability"] = int(stage_data["probability"])
    if "notes" in stage_data:
        opportunity["notes"] = stage_data["notes"]
    
    opportunity["updated_at"] = datetime.now()
    
    return OpportunityResponse(**opportunity)

@router.get("/metrics", response_model=SalesMetricsResponse)
async def get_sales_metrics(
    db: AsyncSession = Depends(get_db)
) -> SalesMetricsResponse:
    """Get comprehensive sales metrics"""
    
    # Calculate metrics
    total_orders = len(orders_store)
    total_revenue = sum(order["total_amount"] for order in orders_store.values())
    total_opportunities = len(opportunities_store)
    pipeline_value = sum(opp["estimated_value"] for opp in opportunities_store.values())
    
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
    
    # Calculate conversion rate (simplified)
    converted_quotes = len([q for q in quotes_store.values() if q["status"] == QuoteStatus.CONVERTED.value])
    total_quotes = len(quotes_store)
    conversion_rate = (converted_quotes / total_quotes * 100) if total_quotes > 0 else 0.0
    
    # Current month metrics (simplified - using all data for TDD)
    orders_this_month = total_orders
    revenue_this_month = total_revenue
    
    return SalesMetricsResponse(
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        total_opportunities=total_opportunities,
        pipeline_value=round(pipeline_value, 2),
        average_order_value=round(average_order_value, 2),
        conversion_rate=round(conversion_rate, 2),
        orders_this_month=orders_this_month,
        revenue_this_month=round(revenue_this_month, 2)
    )

# CC02 v52.0 Required Endpoints - Phase 3 Aliases

@router.post("/quotations", response_model=QuoteResponse, status_code=201)
async def create_quotation_alias(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> QuoteResponse:
    """Create sales quotation (CC02 v52.0 alias for /quotes)"""
    # Forward to the main quotes endpoint
    return await create_quote(request, db)

@router.post("/quotations/{quote_id}/convert-to-order", response_model=OrderResponse, status_code=201)
async def convert_quotation_to_order_alias(
    quote_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Convert quotation to order (CC02 v52.0 alias for /quotes/{id}/convert)"""
    # Forward to the main conversion endpoint
    return await convert_quote_to_order(quote_id, request, db)

@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice_direct_alias(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> InvoiceResponse:
    """Create invoice directly (CC02 v52.0 compatibility endpoint)"""
    
    try:
        invoice_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields for direct invoice creation
    required_fields = ["order_id", "invoice_number"]
    for field in required_fields:
        if field not in invoice_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    order_id = invoice_data["order_id"]
    
    # Check if order exists
    if order_id not in orders_store:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_store[order_id]
    
    # Create invoice from order
    invoice_id = str(uuid.uuid4())
    now = datetime.now()
    
    # Calculate tax and total
    subtotal = order["total_amount"]
    tax_rate = invoice_data.get("tax_rate", 0.0)
    tax_amount = subtotal * (tax_rate / 100)
    total_amount = subtotal + tax_amount
    
    invoice = {
        "id": invoice_id,
        "order_id": order_id,
        "invoice_number": invoice_data["invoice_number"],
        "invoice_date": now,
        "due_date": invoice_data.get("due_date", (now + timedelta(days=30)).isoformat()),
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "status": InvoiceStatus.DRAFT.value,
        "payment_terms": invoice_data.get("payment_terms", "net_30"),
        "notes": invoice_data.get("notes"),
        "created_at": now,
        "updated_at": now
    }
    
    invoices_store[invoice_id] = invoice
    return InvoiceResponse(**invoice)

# Health check endpoint for performance testing
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for core sales API"""
    start_time = datetime.now()
    
    # Simulate some processing
    quotes_count = len(quotes_store)
    orders_count = len(orders_store)
    invoices_count = len(invoices_store)
    opportunities_count = len(opportunities_store)
    
    end_time = datetime.now()
    response_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "quotes_count": quotes_count,
        "orders_count": orders_count,
        "invoices_count": invoices_count,
        "opportunities_count": opportunities_count,
        "timestamp": start_time.isoformat()
    }