import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class CustomerBase(BaseModel):
    customer_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    customer_type: str = Field(default="individual", regex="^(individual|business)$")
    customer_group: str = Field(default="standard", max_length=50)
    priority_level: str = Field(default="normal", regex="^(high|normal|low)$")

    @validator("customer_code")
    def code_valid(cls, v) -> dict:
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Customer code must contain only uppercase letters, numbers, hyphens and underscores"
            )
        return v


class CustomerCreate(CustomerBase):
    mobile: Optional[str] = None
    website: Optional[str] = None

    # 請求先住所
    billing_address_line1: Optional[str] = None
    billing_city: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: str = "Japan"

    # 配送先住所
    shipping_address_line1: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: str = "Japan"

    industry: Optional[str] = None
    credit_limit: Decimal = Field(default=0, ge=0)
    payment_terms: str = Field(default="net_30", max_length=50)
    tax_id: Optional[str] = None
    tax_exempt: bool = False
    sales_rep_id: Optional[str] = None
    acquisition_source: Optional[str] = None
    notes: Optional[str] = None
    preferences: Dict[str, Any] = {}


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    customer_type: Optional[str] = Field(None, regex="^(individual|business)$")
    customer_group: Optional[str] = None
    priority_level: Optional[str] = Field(None, regex="^(high|normal|low)$")
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None
    is_vip: Optional[bool] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: str
    mobile: Optional[str]
    website: Optional[str]
    billing_address_line1: Optional[str]
    billing_city: Optional[str]
    billing_country: str
    shipping_address_line1: Optional[str]
    shipping_city: Optional[str]
    shipping_country: str
    industry: Optional[str]
    credit_limit: Decimal
    credit_balance: Decimal
    payment_terms: str
    tax_id: Optional[str]
    tax_exempt: bool
    sales_rep_id: Optional[str]
    total_orders: int
    total_sales: Decimal
    avg_order_value: Decimal
    last_order_date: Optional[datetime]
    is_active: bool
    is_vip: bool
    notes: Optional[str]
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class SalesOrderItemBase(BaseModel):
    product_id: str
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_discount_percentage: Decimal = Field(default=0, ge=0, le=100)


class SalesOrderItemCreate(SalesOrderItemBase):
    product_sku: Optional[str] = None
    product_name: Optional[str] = None
    custom_attributes: Dict[str, Any] = {}
    notes: Optional[str] = None


class SalesOrderItemResponse(SalesOrderItemBase):
    id: str
    sales_order_id: str
    product_sku: Optional[str]
    product_name: Optional[str]
    product_description: Optional[str]
    line_discount_amount: Decimal
    line_total: Decimal
    reserved_inventory_id: Optional[str]
    shipped_quantity: Decimal
    delivered_quantity: Decimal
    item_status: str
    custom_attributes: Dict[str, Any]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class SalesOrderBase(BaseModel):
    customer_id: str
    requested_delivery_date: Optional[datetime] = None
    priority: str = Field(default="normal", regex="^(high|normal|low)$")
    payment_terms: Optional[str] = None
    shipping_method: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    quote_id: Optional[str] = None
    shipping_address_line1: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: str = "Japan"
    sales_channel: str = Field(default="direct", regex="^(direct|online|partner)$")
    referral_source: Optional[str] = None
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    custom_fields: Dict[str, Any] = {}
    items: List[SalesOrderItemCreate] = []


class SalesOrderUpdate(BaseModel):
    status: Optional[str] = Field(
        None, regex="^(draft|confirmed|processing|shipped|delivered|cancelled)$"
    )
    priority: Optional[str] = Field(None, regex="^(high|normal|low)$")
    requested_delivery_date: Optional[datetime] = None
    promised_delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    shipping_method: Optional[str] = None
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None


class SalesOrderResponse(SalesOrderBase):
    id: str
    order_number: str
    quote_id: Optional[str]
    order_date: datetime
    promised_delivery_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    discount_percentage: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    payment_status: str
    payment_due_date: Optional[datetime]
    paid_amount: Decimal
    shipping_address_line1: Optional[str]
    shipping_city: Optional[str]
    shipping_country: str
    tracking_number: Optional[str]
    sales_rep_id: Optional[str]
    sales_channel: str
    internal_notes: Optional[str]
    customer_notes: Optional[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[SalesOrderItemResponse] = []

    class Config:
        orm_mode = True


class QuoteItemBase(BaseModel):
    product_id: str
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_discount_amount: Decimal = Field(default=0, ge=0)


class QuoteItemCreate(QuoteItemBase):
    product_sku: Optional[str] = None
    product_name: Optional[str] = None
    notes: Optional[str] = None


class QuoteItemResponse(QuoteItemBase):
    id: str
    quote_id: str
    product_sku: Optional[str]
    product_name: Optional[str]
    product_description: Optional[str]
    line_total: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class QuoteBase(BaseModel):
    customer_id: str
    valid_until: datetime
    win_probability: Decimal = Field(default=0, ge=0, le=100)
    expected_close_date: Optional[datetime] = None


class QuoteCreate(QuoteBase):
    description: Optional[str] = None
    terms_conditions: Optional[str] = None
    internal_notes: Optional[str] = None
    items: List[QuoteItemCreate] = []


class QuoteUpdate(BaseModel):
    status: Optional[str] = Field(
        None, regex="^(draft|sent|accepted|rejected|expired)$"
    )
    valid_until: Optional[datetime] = None
    win_probability: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None


class QuoteResponse(QuoteBase):
    id: str
    quote_number: str
    quote_date: datetime
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    sales_rep_id: Optional[str]
    description: Optional[str]
    terms_conditions: Optional[str]
    internal_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[QuoteItemResponse] = []

    class Config:
        orm_mode = True


class InvoiceBase(BaseModel):
    sales_order_id: str
    customer_id: str
    due_date: datetime
    payment_terms: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(draft|sent|paid|overdue|cancelled)$")
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    id: str
    invoice_number: str
    invoice_date: datetime
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class PaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., regex="^(cash|check|credit_card|bank_transfer)$")
    reference_number: Optional[str] = None


class PaymentCreate(PaymentBase):
    invoice_id: str
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: str
    invoice_id: str
    customer_id: str
    payment_date: datetime
    transaction_id: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ShipmentItemBase(BaseModel):
    sales_order_item_id: str
    product_id: str
    quantity_shipped: Decimal = Field(..., gt=0)


class ShipmentItemCreate(ShipmentItemBase):
    serial_numbers: List[str] = []


class ShipmentItemResponse(ShipmentItemBase):
    id: str
    shipment_id: str
    quantity_delivered: Decimal
    serial_numbers: List[str]
    created_at: datetime

    class Config:
        orm_mode = True


class ShipmentBase(BaseModel):
    sales_order_id: str
    carrier: Optional[str] = None
    shipping_method: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None


class ShipmentCreate(ShipmentBase):
    delivery_address_line1: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_postal_code: Optional[str] = None
    delivery_country: str = "Japan"
    notes: Optional[str] = None
    items: List[ShipmentItemCreate] = []


class ShipmentUpdate(BaseModel):
    status: Optional[str] = Field(
        None, regex="^(pending|shipped|in_transit|delivered|returned)$"
    )
    tracking_number: Optional[str] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    shipping_cost: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class ShipmentResponse(ShipmentBase):
    id: str
    shipment_number: str
    shipped_date: Optional[datetime]
    delivered_date: Optional[datetime]
    status: str
    tracking_number: Optional[str]
    shipping_cost: Optional[Decimal]
    delivery_address_line1: Optional[str]
    delivery_city: Optional[str]
    delivery_country: str
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[ShipmentItemResponse] = []

    class Config:
        orm_mode = True


class SalesStatsResponse(BaseModel):
    total_customers: int
    active_customers: int
    total_orders: int
    orders_this_month: int
    total_sales: Decimal
    sales_this_month: Decimal
    avg_order_value: Decimal
    by_status: Dict[str, int]
    by_channel: Dict[str, Decimal]
    top_customers: List[Dict[str, Any]]


class SalesAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    revenue: Decimal
    orders_count: int
    customers_count: int
    avg_order_value: Decimal
    conversion_rate: Decimal
    growth_rate: Decimal
    daily_breakdown: List[Dict[str, Any]]


class CustomerListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[CustomerResponse]


class SalesOrderListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SalesOrderResponse]
