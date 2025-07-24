import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class SupplierBase(BaseModel):
    supplier_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    supplier_type: str = Field(
        default="vendor", regex="^(vendor|manufacturer|distributor)$"
    )
    supplier_category: Optional[str] = Field(
        None, regex="^(raw_materials|finished_goods|services)$"
    )
    priority_level: str = Field(default="normal", regex="^(critical|high|normal|low)$")

    @validator("supplier_code")
    def code_valid(cls, v) -> dict:
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Supplier code must contain only uppercase letters, numbers, hyphens and underscores"
            )
        return v


class SupplierCreate(SupplierBase):
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
    buyer_id: Optional[str] = None
    notes: Optional[str] = None
    certifications: List[str] = []
    capabilities: List[str] = []


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    company_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    supplier_type: Optional[str] = Field(
        None, regex="^(vendor|manufacturer|distributor)$"
    )
    priority_level: Optional[str] = Field(None, regex="^(critical|high|normal|low)$")
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None
    preferred_supplier: Optional[bool] = None
    certified_supplier: Optional[bool] = None
    notes: Optional[str] = None


class SupplierResponse(SupplierBase):
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
    quality_rating: Decimal
    delivery_rating: Decimal
    service_rating: Decimal
    overall_rating: Decimal
    buyer_id: Optional[str]
    preferred_supplier: bool
    certified_supplier: bool
    total_orders: int
    total_purchases: Decimal
    avg_order_value: Decimal
    last_order_date: Optional[datetime]
    is_active: bool
    is_approved: bool
    notes: Optional[str]
    certifications: List[str]
    capabilities: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class PurchaseRequestItemBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=300)
    quantity: Decimal = Field(..., gt=0)
    estimated_unit_price: Optional[Decimal] = Field(None, ge=0)


class PurchaseRequestItemCreate(PurchaseRequestItemBase):
    product_id: Optional[str] = None
    product_sku: Optional[str] = None
    product_description: Optional[str] = None
    specification: Optional[str] = None
    required_delivery_date: Optional[datetime] = None
    quality_requirements: Optional[str] = None
    preferred_brand: Optional[str] = None
    notes: Optional[str] = None


class PurchaseRequestItemResponse(PurchaseRequestItemBase):
    id: str
    purchase_request_id: str
    product_id: Optional[str]
    product_sku: Optional[str]
    product_description: Optional[str]
    specification: Optional[str]
    estimated_total: Optional[Decimal]
    required_delivery_date: Optional[datetime]
    quality_requirements: Optional[str]
    preferred_brand: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class PurchaseRequestBase(BaseModel):
    required_date: Optional[datetime] = None
    priority: str = Field(default="normal", regex="^(urgent|high|normal|low)$")


class PurchaseRequestCreate(PurchaseRequestBase):
    department_id: Optional[str] = None
    supplier_id: Optional[str] = None
    estimated_total: Optional[Decimal] = Field(None, ge=0)
    justification: Optional[str] = None
    project_code: Optional[str] = None
    cost_center: Optional[str] = None
    internal_notes: Optional[str] = None
    items: List[PurchaseRequestItemCreate] = []


class PurchaseRequestUpdate(BaseModel):
    status: Optional[str] = Field(
        None, regex="^(draft|submitted|approved|rejected|cancelled)$"
    )
    priority: Optional[str] = Field(None, regex="^(urgent|high|normal|low)$")
    required_date: Optional[datetime] = None
    supplier_id: Optional[str] = None
    estimated_total: Optional[Decimal] = Field(None, ge=0)
    justification: Optional[str] = None
    internal_notes: Optional[str] = None


class PurchaseRequestResponse(PurchaseRequestBase):
    id: str
    request_number: str
    requester_id: str
    department_id: Optional[str]
    supplier_id: Optional[str]
    request_date: datetime
    status: str
    approval_status: str
    estimated_total: Decimal
    approved_budget: Optional[Decimal]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    justification: Optional[str]
    project_code: Optional[str]
    cost_center: Optional[str]
    internal_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[PurchaseRequestItemResponse] = []

    class Config:
        orm_mode = True


class PurchaseOrderItemBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=300)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_discount_percentage: Decimal = Field(default=0, ge=0, le=100)


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    product_id: Optional[str] = None
    product_sku: Optional[str] = None
    product_description: Optional[str] = None
    specification: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: str
    purchase_order_id: str
    product_id: Optional[str]
    product_sku: Optional[str]
    product_description: Optional[str]
    specification: Optional[str]
    line_discount_amount: Decimal
    line_total: Decimal
    received_quantity: Decimal
    rejected_quantity: Decimal
    remaining_quantity: Optional[Decimal]
    quality_status: str
    inspection_notes: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class PurchaseOrderBase(BaseModel):
    supplier_id: str
    required_delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    purchase_request_id: Optional[str] = None
    promised_delivery_date: Optional[datetime] = None
    shipping_method: Optional[str] = None
    shipping_address_line1: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: str = "Japan"
    quality_requirements: Optional[str] = None
    contract_terms: Optional[str] = None
    warranty_terms: Optional[str] = None
    internal_notes: Optional[str] = None
    supplier_notes: Optional[str] = None
    project_code: Optional[str] = None
    cost_center: Optional[str] = None
    items: List[PurchaseOrderItemCreate] = []


class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = Field(
        None, regex="^(draft|sent|acknowledged|shipped|received|cancelled)$"
    )
    required_delivery_date: Optional[datetime] = None
    promised_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    shipping_method: Optional[str] = None
    quality_requirements: Optional[str] = None
    internal_notes: Optional[str] = None
    supplier_notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: str
    po_number: str
    purchase_request_id: Optional[str]
    buyer_id: str
    order_date: datetime
    promised_delivery_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    status: str
    receipt_status: str
    subtotal: Decimal
    discount_amount: Decimal
    discount_percentage: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    payment_due_date: Optional[datetime]
    payment_status: str
    paid_amount: Decimal
    shipping_method: Optional[str]
    shipping_address_line1: Optional[str]
    shipping_city: Optional[str]
    shipping_country: Optional[str]
    quality_requirements: Optional[str]
    contract_terms: Optional[str]
    warranty_terms: Optional[str]
    internal_notes: Optional[str]
    supplier_notes: Optional[str]
    project_code: Optional[str]
    cost_center: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[PurchaseOrderItemResponse] = []

    class Config:
        orm_mode = True


class PurchaseReceiptItemBase(BaseModel):
    purchase_order_item_id: str
    product_id: str
    received_quantity: Decimal = Field(..., gt=0)


class PurchaseReceiptItemCreate(PurchaseReceiptItemBase):
    accepted_quantity: Optional[Decimal] = Field(None, ge=0)
    rejected_quantity: Optional[Decimal] = Field(None, ge=0)
    damaged_quantity: Optional[Decimal] = Field(None, ge=0)
    quality_status: str = Field(
        default="pending", regex="^(pending|passed|failed|conditional)$"
    )
    defect_reason: Optional[str] = None
    warehouse_location: Optional[str] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    serial_numbers: List[str] = []
    notes: Optional[str] = None


class PurchaseReceiptItemResponse(PurchaseReceiptItemBase):
    id: str
    purchase_receipt_id: str
    accepted_quantity: Decimal
    rejected_quantity: Decimal
    damaged_quantity: Decimal
    quality_status: str
    defect_reason: Optional[str]
    warehouse_location: Optional[str]
    lot_number: Optional[str]
    expiry_date: Optional[datetime]
    serial_numbers: List[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class PurchaseReceiptBase(BaseModel):
    purchase_order_id: str


class PurchaseReceiptCreate(PurchaseReceiptBase):
    receipt_date: datetime = Field(default_factory=datetime.utcnow)
    delivery_note_number: Optional[str] = None
    carrier: Optional[str] = None
    inspection_status: str = Field(
        default="pending", regex="^(pending|passed|failed|partial)$"
    )
    inspection_notes: Optional[str] = None
    notes: Optional[str] = None
    items: List[PurchaseReceiptItemCreate] = []


class PurchaseReceiptUpdate(BaseModel):
    status: Optional[str] = Field(
        None, regex="^(received|inspected|accepted|rejected)$"
    )
    inspection_status: Optional[str] = Field(
        None, regex="^(pending|passed|failed|partial)$"
    )
    inspection_date: Optional[datetime] = None
    inspection_notes: Optional[str] = None
    notes: Optional[str] = None


class PurchaseReceiptResponse(PurchaseReceiptBase):
    id: str
    receipt_number: str
    receiver_id: str
    receipt_date: datetime
    delivery_note_number: Optional[str]
    carrier: Optional[str]
    status: str
    inspection_status: str
    inspector_id: Optional[str]
    inspection_date: Optional[datetime]
    inspection_notes: Optional[str]
    notes: Optional[str]
    attachments: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[PurchaseReceiptItemResponse] = []

    class Config:
        orm_mode = True


class SupplierProductBase(BaseModel):
    supplier_id: str
    product_id: str
    unit_price: Decimal = Field(..., ge=0)


class SupplierProductCreate(SupplierProductBase):
    supplier_product_code: Optional[str] = None
    supplier_product_name: Optional[str] = None
    currency: str = "JPY"
    minimum_order_quantity: Decimal = Field(default=1, gt=0)
    lead_time_days: int = Field(default=0, ge=0)
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    preferred_supplier: bool = False
    notes: Optional[str] = None


class SupplierProductUpdate(BaseModel):
    unit_price: Optional[Decimal] = Field(None, ge=0)
    minimum_order_quantity: Optional[Decimal] = Field(None, gt=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    contract_end_date: Optional[datetime] = None
    preferred_supplier: Optional[bool] = None
    is_active: Optional[bool] = None
    is_discontinued: Optional[bool] = None
    notes: Optional[str] = None


class SupplierProductResponse(SupplierProductBase):
    id: str
    supplier_product_code: Optional[str]
    supplier_product_name: Optional[str]
    currency: str
    minimum_order_quantity: Decimal
    lead_time_days: int
    contract_start_date: Optional[datetime]
    contract_end_date: Optional[datetime]
    preferred_supplier: bool
    quality_rating: Decimal
    delivery_performance: Decimal
    is_active: bool
    is_discontinued: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class PurchaseStatsResponse(BaseModel):
    total_suppliers: int
    active_suppliers: int
    total_purchase_orders: int
    orders_this_month: int
    total_purchases: Decimal
    purchases_this_month: Decimal
    avg_order_value: Decimal
    by_status: Dict[str, int]
    by_supplier_type: Dict[str, Decimal]
    top_suppliers: List[Dict[str, Any]]
    pending_receipts: int
    overdue_orders: int


class PurchaseAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_spend: Decimal
    orders_count: int
    suppliers_count: int
    avg_order_value: Decimal
    cost_savings: Decimal
    on_time_delivery_rate: Decimal
    quality_rejection_rate: Decimal
    daily_breakdown: List[Dict[str, Any]]
    supplier_performance: List[Dict[str, Any]]


class SupplierListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[SupplierResponse]


class PurchaseRequestListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[PurchaseRequestResponse]


class PurchaseOrderListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[PurchaseOrderResponse]
