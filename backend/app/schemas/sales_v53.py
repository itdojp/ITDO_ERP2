"""
CC02 v53.0 Sales Schemas - Issue #568
10-Day ERP Business API Implementation Sprint - Day 5-6
Enhanced Sales Management API Schemas
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    """Sales order status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class OrderType(str, Enum):
    """Order type enumeration"""
    SALES = "sales"
    RETURN = "return"
    EXCHANGE = "exchange"
    QUOTE = "quote"
    SUBSCRIPTION = "subscription"


class PaymentMethod(str, Enum):
    """Payment method enumeration"""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    ONLINE = "online"
    CRYPTO = "crypto"


class ShippingMethod(str, Enum):
    """Shipping method enumeration"""
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    PICKUP = "pickup"
    DIGITAL = "digital"


# Customer Schemas
class CustomerCreate(BaseModel):
    """Schema for creating customer"""
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    billing_address: Optional[str] = Field(None, max_length=500)
    shipping_address: Optional[str] = Field(None, max_length=500)
    customer_type: str = Field(default="individual", max_length=50)
    credit_limit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    payment_terms: Optional[int] = Field(None, ge=0, description="Payment terms in days")
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(None, max_length=1000)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class CustomerResponse(BaseModel):
    """Schema for customer API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    customer_type: str = "individual"
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[int] = None
    current_balance: Decimal = Decimal("0")
    total_orders: int = 0
    total_spent: Decimal = Decimal("0")
    is_active: bool = True
    notes: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Order Line Item Schema
class OrderLineItemCreate(BaseModel):
    """Schema for creating order line item"""
    product_id: str
    quantity: Decimal = Field(..., gt=0, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    discount_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=4)
    notes: Optional[str] = Field(None, max_length=500)


class OrderLineItemResponse(BaseModel):
    """Schema for order line item responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    line_total: Decimal
    line_tax: Decimal
    line_net_total: Decimal
    notes: Optional[str] = None


# Sales Order Schemas
class SalesOrderCreate(BaseModel):
    """Schema for creating sales order"""
    customer_id: str
    order_type: OrderType = Field(default=OrderType.SALES)
    order_date: Optional[date] = Field(default_factory=date.today)
    due_date: Optional[date] = None
    reference: Optional[str] = Field(None, max_length=100)
    
    # Order lines
    line_items: List[OrderLineItemCreate] = Field(..., min_length=1)
    
    # Financial details
    subtotal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_total: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    discount_total: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    shipping_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    total_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    # Shipping details
    shipping_method: Optional[ShippingMethod] = None
    shipping_address: Optional[str] = Field(None, max_length=500)
    tracking_number: Optional[str] = Field(None, max_length=100)
    
    # Payment details
    payment_method: Optional[PaymentMethod] = None
    payment_terms: Optional[int] = Field(None, ge=0)
    
    # Status and metadata
    status: OrderStatus = Field(default=OrderStatus.DRAFT)
    priority: str = Field(default="normal", max_length=20)
    sales_rep_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v, info):
        if v and 'order_date' in info.data:
            order_date = info.data['order_date']
            if isinstance(order_date, date) and v < order_date:
                raise ValueError('due_date cannot be before order_date')
        return v


class SalesOrderUpdate(BaseModel):
    """Schema for updating sales order"""
    order_type: Optional[OrderType] = None
    due_date: Optional[date] = None
    reference: Optional[str] = Field(None, max_length=100)
    
    # Financial details
    subtotal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_total: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    discount_total: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    shipping_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    total_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    # Shipping details
    shipping_method: Optional[ShippingMethod] = None
    shipping_address: Optional[str] = Field(None, max_length=500)
    tracking_number: Optional[str] = Field(None, max_length=100)
    
    # Payment details
    payment_method: Optional[PaymentMethod] = None
    payment_terms: Optional[int] = Field(None, ge=0)
    
    # Status and metadata
    status: Optional[OrderStatus] = None
    priority: Optional[str] = Field(None, max_length=20)
    sales_rep_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    attributes: Optional[Dict[str, Any]] = None


class SalesOrderResponse(BaseModel):
    """Schema for sales order API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    order_number: str
    customer_id: str
    customer_name: Optional[str] = None
    order_type: OrderType
    order_date: date
    due_date: Optional[date] = None
    reference: Optional[str] = None
    
    # Order lines
    line_items: List[OrderLineItemResponse] = Field(default_factory=list)
    line_items_count: int = 0
    
    # Financial details
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    paid_amount: Decimal = Decimal("0")
    balance_due: Decimal
    
    # Shipping details
    shipping_method: Optional[ShippingMethod] = None
    shipping_address: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    
    # Payment details
    payment_method: Optional[PaymentMethod] = None
    payment_terms: Optional[int] = None
    payment_status: PaymentStatus
    
    # Status and metadata
    status: OrderStatus
    priority: str = "normal"
    sales_rep_id: Optional[str] = None
    sales_rep_name: Optional[str] = None
    notes: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# Payment Schemas
class PaymentCreate(BaseModel):
    """Schema for creating payment"""
    order_id: str
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: PaymentMethod
    payment_date: Optional[datetime] = Field(default_factory=datetime.now)
    reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class PaymentResponse(BaseModel):
    """Schema for payment API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    order_id: str
    order_number: Optional[str] = None
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: datetime
    reference: Optional[str] = None
    notes: Optional[str] = None
    status: str = "completed"
    processed_by: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# Quote Schemas
class QuoteCreate(BaseModel):
    """Schema for creating quote"""
    customer_id: str
    quote_date: Optional[date] = Field(default_factory=date.today)
    valid_until: Optional[date] = None
    reference: Optional[str] = Field(None, max_length=100)
    
    # Quote lines
    line_items: List[OrderLineItemCreate] = Field(..., min_length=1)
    
    # Financial details
    subtotal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_total: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    discount_total: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    total_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    # Metadata
    sales_rep_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    terms_conditions: Optional[str] = Field(None, max_length=2000)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class QuoteResponse(BaseModel):
    """Schema for quote API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    quote_number: str
    customer_id: str
    customer_name: Optional[str] = None
    quote_date: date
    valid_until: Optional[date] = None
    reference: Optional[str] = None
    
    # Quote lines
    line_items: List[OrderLineItemResponse] = Field(default_factory=list)
    line_items_count: int = 0
    
    # Financial details
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    total_amount: Decimal
    
    # Status
    status: str = "active"
    is_expired: bool = False
    is_converted: bool = False
    converted_order_id: Optional[str] = None
    
    # Metadata
    sales_rep_id: Optional[str] = None
    sales_rep_name: Optional[str] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


# Statistics and Analytics Schemas
class SalesStatistics(BaseModel):
    """Enhanced sales statistics"""
    # Order Statistics
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    completed_orders: int
    cancelled_orders: int
    
    # Financial Statistics
    total_sales_amount: Decimal
    total_tax_collected: Decimal
    total_discounts_given: Decimal
    average_order_value: Decimal
    
    # Customer Statistics
    total_customers: int
    active_customers: int
    new_customers_this_month: int
    repeat_customers: int
    
    # Payment Statistics
    total_payments_received: Decimal
    outstanding_receivables: Decimal
    overdue_amount: Decimal
    payment_methods_breakdown: Dict[str, Decimal]
    
    # Product Performance
    top_selling_products: List[Dict[str, Any]]
    low_performing_products: List[Dict[str, Any]]
    
    # Time-based Analysis
    sales_by_period: Dict[str, Decimal]
    orders_by_status: Dict[str, int]
    conversion_rate: Optional[Decimal] = None
    
    # Performance Metrics
    last_updated: datetime
    calculation_time_ms: float


# List Response Schemas
class SalesOrderListResponse(BaseModel):
    """Schema for paginated sales order list responses"""
    items: List[SalesOrderResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class CustomerListResponse(BaseModel):
    """Schema for paginated customer list responses"""
    items: List[CustomerResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class QuoteListResponse(BaseModel):
    """Schema for paginated quote list responses"""
    items: List[QuoteResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class PaymentListResponse(BaseModel):
    """Schema for paginated payment list responses"""
    items: List[PaymentResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# Bulk Operations Schemas
class BulkOrderOperation(BaseModel):
    """Schema for bulk order operations"""
    orders: List[SalesOrderCreate]
    validate_only: bool = Field(default=False)
    stop_on_error: bool = Field(default=False)


class BulkOrderResult(BaseModel):
    """Schema for bulk order operation results"""
    created_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    created_items: List[SalesOrderResponse] = Field(default_factory=list)
    updated_items: List[SalesOrderResponse] = Field(default_factory=list)
    failed_items: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: Optional[float] = None


# Error Schemas
class SalesError(BaseModel):
    """Sales-specific error response"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# API Response Wrappers
class SalesAPIResponse(BaseModel):
    """Sales-specific API response"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Union[
        SalesOrderResponse, 
        CustomerResponse,
        QuoteResponse,
        PaymentResponse,
        SalesStatistics,
        SalesOrderListResponse,
        CustomerListResponse,
        QuoteListResponse,
        PaymentListResponse
    ]] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None