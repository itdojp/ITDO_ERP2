"""
CC02 v53.0 Sales Management API - Issue #568
10-Day ERP Business API Implementation Sprint - Day 5-6 Phase 2
Advanced Sales Management API Endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import datetime, date
import uuid
import asyncio
import time

from app.schemas.sales_v53 import (
    # Customer Schemas
    CustomerCreate, CustomerResponse,
    
    # Sales Order Schemas
    SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse,
    OrderLineItemCreate, OrderLineItemResponse,
    
    # Payment Schemas
    PaymentCreate, PaymentResponse,
    
    # Quote Schemas
    QuoteCreate, QuoteResponse,
    
    # Statistics and List Schemas
    SalesStatistics,
    SalesOrderListResponse, CustomerListResponse, QuoteListResponse, PaymentListResponse,
    
    # Bulk Operations
    BulkOrderOperation, BulkOrderResult,
    
    # Enums
    OrderStatus, PaymentStatus, OrderType, PaymentMethod, ShippingMethod
)

# In-memory storage for rapid prototyping (same pattern as previous phases)
customers_store: Dict[str, Dict[str, Any]] = {}
sales_orders_store: Dict[str, Dict[str, Any]] = {}
payments_store: Dict[str, Dict[str, Any]] = {}
quotes_store: Dict[str, Dict[str, Any]] = {}

router = APIRouter()

# Dependency injection for database (placeholder)
async def get_db():
    """Database dependency placeholder for future integration"""
    return None

# Helper functions
def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"ORD-{timestamp}-{uuid.uuid4().hex[:6].upper()}"

def generate_quote_number() -> str:
    """Generate unique quote number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"QUO-{timestamp}-{uuid.uuid4().hex[:6].upper()}"

def calculate_line_totals(line_item: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate line item totals"""
    quantity = Decimal(str(line_item.get('quantity', 0)))
    unit_price = Decimal(str(line_item.get('unit_price', 0)))
    discount_percent = Decimal(str(line_item.get('discount_percent') or 0))
    discount_amount = Decimal(str(line_item.get('discount_amount') or 0))
    tax_rate = Decimal(str(line_item.get('tax_rate') or 0))
    
    # Calculate line total before discount
    line_total_before_discount = quantity * unit_price
    
    # Apply discounts
    if discount_percent > 0:
        discount_amount = line_total_before_discount * (discount_percent / 100)
    
    line_total = line_total_before_discount - discount_amount
    
    # Calculate tax
    line_tax = line_total * (tax_rate / 100)
    line_net_total = line_total + line_tax
    
    return {
        'line_total': line_total,
        'line_tax': line_tax,
        'line_net_total': line_net_total,
        'discount_amount': discount_amount
    }

def calculate_order_totals(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate order totals from line items"""
    line_items = order_data.get('line_items', [])
    subtotal = Decimal('0')
    tax_total = Decimal('0')
    discount_total = Decimal('0')
    
    for item in line_items:
        totals = calculate_line_totals(item)
        subtotal += totals['line_total']
        tax_total += totals['line_tax']
        discount_total += totals['discount_amount']
    
    shipping_cost = Decimal(str(order_data.get('shipping_cost') or 0))
    total_amount = subtotal + tax_total + shipping_cost
    
    return {
        'subtotal': subtotal,
        'tax_total': tax_total,
        'discount_total': discount_total,
        'shipping_cost': shipping_cost,
        'total_amount': total_amount
    }

async def background_order_processing(order_id: str):
    """Background task for order processing"""
    await asyncio.sleep(0.1)  # Simulate processing delay
    
    if order_id in sales_orders_store:
        order = sales_orders_store[order_id]
        order['background_processed'] = True
        order['processing_completed_at'] = datetime.now()


# Customer Management Endpoints

@router.post("/customers/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Create new customer with comprehensive business validation"""
    start_time = time.time()
    
    # Generate unique customer ID
    customer_id = str(uuid.uuid4())
    
    # Check for duplicate email if provided
    if customer_data.email:
        for existing_customer in customers_store.values():
            if existing_customer.get('email') == customer_data.email:
                raise HTTPException(
                    status_code=400,
                    detail=f"Customer with email {customer_data.email} already exists"
                )
    
    # Create customer record
    customer_record = {
        'id': customer_id,
        'name': customer_data.name,
        'email': customer_data.email,
        'phone': customer_data.phone,
        'company': customer_data.company,
        'tax_id': customer_data.tax_id,
        'billing_address': customer_data.billing_address,
        'shipping_address': customer_data.shipping_address,
        'customer_type': customer_data.customer_type,
        'credit_limit': customer_data.credit_limit,
        'payment_terms': customer_data.payment_terms,
        'current_balance': Decimal('0'),
        'total_orders': 0,
        'total_spent': Decimal('0'),
        'is_active': customer_data.is_active,
        'notes': customer_data.notes,
        'attributes': customer_data.attributes,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    customers_store[customer_id] = customer_record
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Customer creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return CustomerResponse(**customer_record)


@router.get("/customers/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    customer_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> CustomerListResponse:
    """List customers with filtering and pagination"""
    start_time = time.time()
    
    # Apply filters
    filtered_customers = []
    for customer in customers_store.values():
        # Filter by customer type
        if customer_type and customer.get('customer_type') != customer_type:
            continue
            
        # Filter by active status
        if is_active is not None and customer.get('is_active') != is_active:
            continue
            
        # Search filter
        if search:
            search_lower = search.lower()
            if not any([
                search_lower in customer.get('name', '').lower(),
                search_lower in customer.get('email', '').lower(),
                search_lower in customer.get('company', '').lower()
            ]):
                continue
        
        filtered_customers.append(customer)
    
    # Pagination
    total = len(filtered_customers)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_customers = filtered_customers[start_idx:end_idx]
    
    # Convert to response models
    customer_responses = [CustomerResponse(**customer) for customer in paginated_customers]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Customer listing exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return CustomerListResponse(
        items=customer_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied={
            'customer_type': customer_type,
            'is_active': is_active,
            'search': search
        }
    )


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    """Get customer by ID with relationship data"""
    start_time = time.time()
    
    if customer_id not in customers_store:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = customers_store[customer_id].copy()
    
    # Calculate relationship metrics
    customer_orders = [order for order in sales_orders_store.values() 
                      if order.get('customer_id') == customer_id]
    
    customer['total_orders'] = len(customer_orders)
    customer['total_spent'] = sum(
        Decimal(str(order.get('total_amount', 0))) 
        for order in customer_orders
    )
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Customer retrieval exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return CustomerResponse(**customer)


# Sales Order Management Endpoints

@router.post("/orders/", response_model=SalesOrderResponse, status_code=201)
async def create_sales_order(
    order_data: SalesOrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> SalesOrderResponse:
    """Create new sales order with comprehensive validation"""
    start_time = time.time()
    
    # Validate customer exists
    if order_data.customer_id not in customers_store:
        raise HTTPException(status_code=400, detail="Customer not found")
    
    # Generate unique order ID and number
    order_id = str(uuid.uuid4())
    order_number = generate_order_number()
    
    # Process line items
    processed_line_items = []
    for idx, item in enumerate(order_data.line_items):
        line_item_id = str(uuid.uuid4())
        item_dict = item.model_dump()
        item_dict['id'] = line_item_id
        
        # Calculate line totals
        totals = calculate_line_totals(item_dict)
        item_dict.update(totals)
        
        # Add product info (placeholder)
        item_dict['product_name'] = f"Product {item.product_id}"
        item_dict['product_sku'] = f"SKU-{item.product_id}"
        
        processed_line_items.append(item_dict)
    
    # Calculate order totals
    order_dict = order_data.model_dump()
    order_dict['line_items'] = processed_line_items
    totals = calculate_order_totals(order_dict)
    
    # Create order record
    order_record = {
        'id': order_id,
        'order_number': order_number,
        'customer_id': order_data.customer_id,
        'customer_name': customers_store[order_data.customer_id].get('name'),
        'order_type': order_data.order_type,
        'order_date': order_data.order_date or date.today(),
        'due_date': order_data.due_date,
        'reference': order_data.reference,
        'line_items': processed_line_items,
        'line_items_count': len(processed_line_items),
        'subtotal': totals['subtotal'],
        'tax_total': totals['tax_total'],
        'discount_total': totals['discount_total'],
        'shipping_cost': totals['shipping_cost'],
        'total_amount': totals['total_amount'],
        'paid_amount': Decimal('0'),
        'balance_due': totals['total_amount'],
        'shipping_method': order_data.shipping_method,
        'shipping_address': order_data.shipping_address,
        'tracking_number': order_data.tracking_number,
        'shipped_date': None,
        'delivered_date': None,
        'payment_method': order_data.payment_method,
        'payment_terms': order_data.payment_terms,
        'payment_status': PaymentStatus.PENDING,
        'status': order_data.status,
        'priority': order_data.priority,
        'sales_rep_id': order_data.sales_rep_id,
        'sales_rep_name': f"Rep {order_data.sales_rep_id}" if order_data.sales_rep_id else None,
        'notes': order_data.notes,
        'attributes': order_data.attributes,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'completed_at': None
    }
    
    sales_orders_store[order_id] = order_record
    
    # Background processing
    background_tasks.add_task(background_order_processing, order_id)
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Order creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return SalesOrderResponse(**order_record)


@router.get("/orders/", response_model=SalesOrderListResponse)
async def list_sales_orders(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    customer_id: Optional[str] = Query(None),
    order_type: Optional[OrderType] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> SalesOrderListResponse:
    """List sales orders with comprehensive filtering"""
    start_time = time.time()
    
    # Apply filters
    filtered_orders = []
    for order in sales_orders_store.values():
        # Filter by status
        if status and order.get('status') != status:
            continue
            
        # Filter by customer
        if customer_id and order.get('customer_id') != customer_id:
            continue
            
        # Filter by order type
        if order_type and order.get('order_type') != order_type:
            continue
            
        # Filter by date range
        order_date = order.get('order_date')
        if date_from and order_date < date_from:
            continue
        if date_to and order_date > date_to:
            continue
        
        filtered_orders.append(order)
    
    # Sort by creation date (newest first)
    filtered_orders.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
    
    # Pagination
    total = len(filtered_orders)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_orders = filtered_orders[start_idx:end_idx]
    
    # Convert to response models
    order_responses = [SalesOrderResponse(**order) for order in paginated_orders]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Order listing exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return SalesOrderListResponse(
        items=order_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied={
            'status': status,
            'customer_id': customer_id,
            'order_type': order_type,
            'date_from': date_from,
            'date_to': date_to
        }
    )


@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
async def get_sales_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
) -> SalesOrderResponse:
    """Get sales order by ID with complete details"""
    start_time = time.time()
    
    if order_id not in sales_orders_store:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    order = sales_orders_store[order_id]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Order retrieval exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return SalesOrderResponse(**order)


@router.put("/orders/{order_id}", response_model=SalesOrderResponse)
async def update_sales_order(
    order_id: str,
    order_update: SalesOrderUpdate,
    db: AsyncSession = Depends(get_db)
) -> SalesOrderResponse:
    """Update sales order with validation"""
    start_time = time.time()
    
    if order_id not in sales_orders_store:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    order = sales_orders_store[order_id]
    
    # Update fields
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            order[field] = value
    
    order['updated_at'] = datetime.now()
    
    # Recalculate totals if financial fields were updated
    financial_fields = ['subtotal', 'tax_total', 'discount_total', 'shipping_cost']
    if any(field in update_data for field in financial_fields):
        order['balance_due'] = order['total_amount'] - order.get('paid_amount', Decimal('0'))
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Order update exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return SalesOrderResponse(**order)


# Payment Management Endpoints

@router.post("/payments/", response_model=PaymentResponse, status_code=201)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    """Create payment for sales order"""
    start_time = time.time()
    
    # Validate order exists
    if payment_data.order_id not in sales_orders_store:
        raise HTTPException(status_code=400, detail="Sales order not found")
    
    order = sales_orders_store[payment_data.order_id]
    
    # Validate payment amount doesn't exceed balance
    balance_due = order.get('balance_due', Decimal('0'))
    if payment_data.amount > balance_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount {payment_data.amount} exceeds balance due {balance_due}"
        )
    
    # Generate payment ID
    payment_id = str(uuid.uuid4())
    
    # Create payment record
    payment_record = {
        'id': payment_id,
        'order_id': payment_data.order_id,
        'order_number': order.get('order_number'),
        'amount': payment_data.amount,
        'payment_method': payment_data.payment_method,
        'payment_date': payment_data.payment_date or datetime.now(),
        'reference': payment_data.reference,
        'notes': payment_data.notes,
        'status': 'completed',
        'processed_by': 'system',
        'attributes': payment_data.attributes,
        'created_at': datetime.now()
    }
    
    payments_store[payment_id] = payment_record
    
    # Update order payment status
    order['paid_amount'] = order.get('paid_amount', Decimal('0')) + payment_data.amount
    order['balance_due'] = order['total_amount'] - order['paid_amount']
    
    # Use small tolerance for floating point comparisons
    if order['balance_due'] <= Decimal('0.01'):
        order['payment_status'] = PaymentStatus.PAID
        order['balance_due'] = Decimal('0')  # Set exactly to zero
    elif order['paid_amount'] > 0:
        order['payment_status'] = PaymentStatus.PARTIAL
    
    order['updated_at'] = datetime.now()
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Payment creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return PaymentResponse(**payment_record)


@router.get("/payments/", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    order_id: Optional[str] = Query(None),
    payment_method: Optional[PaymentMethod] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> PaymentListResponse:
    """List payments with filtering"""
    start_time = time.time()
    
    # Apply filters
    filtered_payments = []
    for payment in payments_store.values():
        # Filter by order
        if order_id and payment.get('order_id') != order_id:
            continue
            
        # Filter by payment method
        if payment_method and payment.get('payment_method') != payment_method:
            continue
        
        filtered_payments.append(payment)
    
    # Sort by payment date (newest first)
    filtered_payments.sort(key=lambda x: x.get('payment_date', datetime.min), reverse=True)
    
    # Pagination
    total = len(filtered_payments)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_payments = filtered_payments[start_idx:end_idx]
    
    # Convert to response models
    payment_responses = [PaymentResponse(**payment) for payment in paginated_payments]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Payment listing exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return PaymentListResponse(
        items=payment_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied={
            'order_id': order_id,
            'payment_method': payment_method
        }
    )


# Quote Management Endpoints

@router.post("/quotes/", response_model=QuoteResponse, status_code=201)
async def create_quote(
    quote_data: QuoteCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> QuoteResponse:
    """Create new quote"""
    start_time = time.time()
    
    # Validate customer exists
    if quote_data.customer_id not in customers_store:
        raise HTTPException(status_code=400, detail="Customer not found")
    
    # Generate unique quote ID and number
    quote_id = str(uuid.uuid4())
    quote_number = generate_quote_number()
    
    # Process line items
    processed_line_items = []
    for item in quote_data.line_items:
        line_item_id = str(uuid.uuid4())
        item_dict = item.model_dump()
        item_dict['id'] = line_item_id
        
        # Calculate line totals
        totals = calculate_line_totals(item_dict)
        item_dict.update(totals)
        
        # Add product info (placeholder)
        item_dict['product_name'] = f"Product {item.product_id}"
        item_dict['product_sku'] = f"SKU-{item.product_id}"
        
        processed_line_items.append(item_dict)
    
    # Calculate quote totals
    quote_dict = quote_data.model_dump()
    quote_dict['line_items'] = processed_line_items
    totals = calculate_order_totals(quote_dict)
    
    # Create quote record
    quote_record = {
        'id': quote_id,
        'quote_number': quote_number,
        'customer_id': quote_data.customer_id,
        'customer_name': customers_store[quote_data.customer_id].get('name'),
        'quote_date': quote_data.quote_date or date.today(),
        'valid_until': quote_data.valid_until,
        'reference': quote_data.reference,
        'line_items': processed_line_items,
        'line_items_count': len(processed_line_items),
        'subtotal': totals['subtotal'],
        'tax_total': totals['tax_total'],
        'discount_total': totals['discount_total'],
        'total_amount': totals['total_amount'],
        'status': 'active',
        'is_expired': False,
        'is_converted': False,
        'converted_order_id': None,
        'sales_rep_id': quote_data.sales_rep_id,
        'sales_rep_name': f"Rep {quote_data.sales_rep_id}" if quote_data.sales_rep_id else None,
        'notes': quote_data.notes,
        'terms_conditions': quote_data.terms_conditions,
        'attributes': quote_data.attributes,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    quotes_store[quote_id] = quote_record
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Quote creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return QuoteResponse(**quote_record)


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_db)
) -> QuoteResponse:
    """Get quote by ID with complete details"""
    start_time = time.time()
    
    if quote_id not in quotes_store:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote = quotes_store[quote_id]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Quote retrieval exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return QuoteResponse(**quote)


@router.get("/quotes/", response_model=QuoteListResponse)
async def list_quotes(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    customer_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> QuoteListResponse:
    """List quotes with filtering"""
    start_time = time.time()
    
    # Apply filters
    filtered_quotes = []
    for quote in quotes_store.values():
        # Filter by customer
        if customer_id and quote.get('customer_id') != customer_id:
            continue
            
        # Filter by status
        if status and quote.get('status') != status:
            continue
        
        filtered_quotes.append(quote)
    
    # Sort by creation date (newest first)
    filtered_quotes.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
    
    # Pagination
    total = len(filtered_quotes)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_quotes = filtered_quotes[start_idx:end_idx]
    
    # Convert to response models
    quote_responses = [QuoteResponse(**quote) for quote in paginated_quotes]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Quote listing exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return QuoteListResponse(
        items=quote_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied={
            'customer_id': customer_id,
            'status': status
        }
    )


@router.post("/quotes/{quote_id}/convert", response_model=SalesOrderResponse)
async def convert_quote_to_order(
    quote_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> SalesOrderResponse:
    """Convert quote to sales order"""
    start_time = time.time()
    
    if quote_id not in quotes_store:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    quote = quotes_store[quote_id]
    
    if quote.get('is_converted'):
        raise HTTPException(status_code=400, detail="Quote already converted")
    
    # Create order from quote
    processed_line_items = []
    for item in quote['line_items']:
        line_item_data = {}
        for k, v in item.items():
            if k in ['product_id', 'quantity', 'unit_price', 'discount_percent', 
                    'discount_amount', 'tax_rate', 'notes']:
                if k in ['discount_amount', 'tax_rate'] and v is not None:
                    # Round to appropriate decimal places for schema validation
                    if k == 'discount_amount':
                        v = round(float(v), 2)  # 2 decimal places for money
                    elif k == 'tax_rate':
                        v = round(float(v), 4)  # 4 decimal places for rates
                line_item_data[k] = v
        processed_line_items.append(OrderLineItemCreate(**line_item_data))
    
    order_data = SalesOrderCreate(
        customer_id=quote['customer_id'],
        order_type=OrderType.SALES,
        line_items=processed_line_items,
        notes=f"Converted from quote {quote['quote_number']}"
    )
    
    # Create the order
    order_response = await create_sales_order(order_data, background_tasks, db)
    
    # Mark quote as converted
    quote['is_converted'] = True
    quote['converted_order_id'] = order_response.id
    quote['status'] = 'converted'
    quote['updated_at'] = datetime.now()
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Quote conversion exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return order_response


# Statistics and Analytics Endpoints

@router.get("/statistics", response_model=SalesStatistics)
async def get_sales_statistics(
    db: AsyncSession = Depends(get_db)
) -> SalesStatistics:
    """Get comprehensive sales statistics"""
    start_time = time.time()
    
    # Order statistics
    total_orders = len(sales_orders_store)
    orders_by_status = {}
    for order in sales_orders_store.values():
        status = order.get('status', 'unknown')
        orders_by_status[status.value if hasattr(status, 'value') else str(status)] = orders_by_status.get(status.value if hasattr(status, 'value') else str(status), 0) + 1
    
    pending_orders = orders_by_status.get('pending', 0)
    confirmed_orders = orders_by_status.get('confirmed', 0)
    completed_orders = orders_by_status.get('completed', 0)
    cancelled_orders = orders_by_status.get('cancelled', 0)
    
    # Financial statistics
    total_sales_amount = sum(
        Decimal(str(order.get('total_amount', 0))) 
        for order in sales_orders_store.values()
    )
    total_tax_collected = sum(
        Decimal(str(order.get('tax_total', 0))) 
        for order in sales_orders_store.values()
    )
    total_discounts_given = sum(
        Decimal(str(order.get('discount_total', 0))) 
        for order in sales_orders_store.values()
    )
    average_order_value = total_sales_amount / max(total_orders, 1)
    
    # Customer statistics
    total_customers = len(customers_store)
    active_customers = sum(1 for customer in customers_store.values() if customer.get('is_active'))
    new_customers_this_month = sum(
        1 for customer in customers_store.values() 
        if customer.get('created_at', datetime.min).month == datetime.now().month
    )
    repeat_customers = sum(
        1 for customer in customers_store.values() 
        if customer.get('total_orders', 0) > 1
    )
    
    # Payment statistics
    total_payments_received = sum(
        Decimal(str(payment.get('amount', 0))) 
        for payment in payments_store.values()
    )
    outstanding_receivables = sum(
        Decimal(str(order.get('balance_due', 0))) 
        for order in sales_orders_store.values()
    )
    overdue_amount = Decimal('0')  # Placeholder for overdue calculation
    
    # Payment methods breakdown
    payment_methods_breakdown = {}
    for payment in payments_store.values():
        method = payment.get('payment_method', 'unknown')
        method_str = method.value if hasattr(method, 'value') else str(method)
        payment_methods_breakdown[method_str] = payment_methods_breakdown.get(method_str, Decimal('0')) + Decimal(str(payment.get('amount', 0)))
    
    # Performance metrics
    calculation_time_ms = (time.time() - start_time) * 1000
    
    # Performance check
    if calculation_time_ms > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Statistics calculation exceeded 200ms limit: {calculation_time_ms:.2f}ms"
        )
    
    return SalesStatistics(
        total_orders=total_orders,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_sales_amount=total_sales_amount,
        total_tax_collected=total_tax_collected,
        total_discounts_given=total_discounts_given,
        average_order_value=average_order_value,
        total_customers=total_customers,
        active_customers=active_customers,
        new_customers_this_month=new_customers_this_month,
        repeat_customers=repeat_customers,
        total_payments_received=total_payments_received,
        outstanding_receivables=outstanding_receivables,
        overdue_amount=overdue_amount,
        payment_methods_breakdown=payment_methods_breakdown,
        top_selling_products=[],  # Placeholder
        low_performing_products=[],  # Placeholder
        sales_by_period={},  # Placeholder
        orders_by_status=orders_by_status,
        conversion_rate=None,
        last_updated=datetime.now(),
        calculation_time_ms=calculation_time_ms
    )


# Bulk Operations

@router.post("/orders/bulk", response_model=BulkOrderResult)
async def bulk_create_orders(
    bulk_operation: BulkOrderOperation,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> BulkOrderResult:
    """Bulk create sales orders"""
    start_time = time.time()
    
    result = BulkOrderResult()
    
    for order_data in bulk_operation.orders:
        try:
            if bulk_operation.validate_only:
                # Just validate without creating
                result.created_count += 1
            else:
                # Create the order
                order_response = await create_sales_order(order_data, background_tasks, db)
                result.created_items.append(order_response)
                result.created_count += 1
                
        except Exception as e:
            result.failed_count += 1
            result.failed_items.append({
                'error': str(e),
                'order_data': order_data.model_dump()
            })
            
            if bulk_operation.stop_on_error:
                break
    
    result.execution_time_ms = (time.time() - start_time) * 1000
    return result


# Health Check Endpoint
@router.get("/health")
async def sales_health_check():
    """Health check for sales API"""
    return {
        "status": "healthy",
        "service": "Sales Management API v53.0",
        "customers_count": len(customers_store),
        "orders_count": len(sales_orders_store),
        "payments_count": len(payments_store),
        "quotes_count": len(quotes_store),
        "timestamp": datetime.now()
    }