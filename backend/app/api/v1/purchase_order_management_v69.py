"""
ITDO ERP Backend - Purchase Order Management v69
Complete Purchase Order Management System with vendor management, procurement workflow, and cost analysis
Day 11: Purchase Order Management Implementation
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import aioredis
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    and_,
    func,
    or_,
    select,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload

from app.core.database import Base, get_db


# Enums
class PurchaseOrderStatus(str, Enum):
    """Purchase order status enumeration"""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class ProcurementType(str, Enum):
    """Procurement type enumeration"""

    STANDARD = "standard"
    EMERGENCY = "emergency"
    BLANKET = "blanket"
    CONTRACT = "contract"
    SERVICES = "services"
    MAINTENANCE = "maintenance"


class ReceivingStatus(str, Enum):
    """Receiving status enumeration"""

    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETED = "completed"
    DISCREPANCY = "discrepancy"
    REJECTED = "rejected"


class PaymentTerms(str, Enum):
    """Payment terms enumeration"""

    NET_30 = "net_30"
    NET_60 = "net_60"
    NET_90 = "net_90"
    COD = "cod"
    PREPAID = "prepaid"
    DUE_ON_RECEIPT = "due_on_receipt"
    INSTALLMENTS = "installments"


class VendorStatus(str, Enum):
    """Vendor status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending_approval"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


# Database Models
class Vendor(Base):
    """Vendor/Supplier management model"""

    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(300))
    tax_id = Column(String(50))
    status = Column(SQLEnum(VendorStatus), default=VendorStatus.ACTIVE, index=True)

    # Contact information
    contact_person = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))

    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))

    # Financial terms
    payment_terms = Column(SQLEnum(PaymentTerms), default=PaymentTerms.NET_30)
    credit_limit = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")

    # Performance metrics
    rating = Column(Numeric(3, 2))  # 0.00 to 5.00
    on_time_delivery_rate = Column(Numeric(5, 2))  # Percentage
    quality_rating = Column(Numeric(3, 2))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    contracts = relationship("VendorContract", back_populates="vendor")


class VendorContract(Base):
    """Vendor contract management"""

    __tablename__ = "vendor_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    contract_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)

    # Contract terms
    contract_type = Column(String(50))  # master, blanket, service, etc.
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    auto_renewal = Column(Boolean, default=False)

    # Financial terms
    total_value = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    payment_terms = Column(SQLEnum(PaymentTerms))

    # Status
    status = Column(String(50), default="active")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="contracts")


class PurchaseRequisition(Base):
    """Purchase requisition model"""

    __tablename__ = "purchase_requisitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)

    # Requester information
    requested_by = Column(String(100), nullable=False)
    department = Column(String(100))
    cost_center = Column(String(50))

    # Procurement details
    procurement_type = Column(
        SQLEnum(ProcurementType), default=ProcurementType.STANDARD
    )
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    required_date = Column(DateTime, nullable=False)

    # Financial
    estimated_total = Column(Numeric(15, 2))
    budget_code = Column(String(50))
    currency = Column(String(3), default="USD")

    # Status and workflow
    status = Column(String(50), default="draft")
    approval_status = Column(String(50), default="pending")
    approved_by = Column(String(100))
    approved_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lines = relationship(
        "PurchaseRequisitionLine",
        back_populates="requisition",
        cascade="all, delete-orphan",
    )


class PurchaseRequisitionLine(Base):
    """Purchase requisition line items"""

    __tablename__ = "purchase_requisition_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_requisitions.id"), nullable=False
    )
    line_number = Column(String(10), nullable=False)

    # Product information
    product_id = Column(UUID(as_uuid=True))  # Optional reference to product catalog
    description = Column(String(500), nullable=False)
    specification = Column(Text)

    # Quantity and units
    quantity = Column(Numeric(12, 4), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)

    # Pricing
    estimated_unit_price = Column(Numeric(12, 4))
    estimated_total_price = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")

    # Delivery
    required_date = Column(DateTime)
    delivery_location = Column(String(255))

    # Status
    status = Column(String(50), default="active")

    # Relationships
    requisition = relationship("PurchaseRequisition", back_populates="lines")


class PurchaseOrder(Base):
    """Purchase order model"""

    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)

    # Order details
    order_date = Column(DateTime, default=datetime.utcnow)
    required_date = Column(DateTime, nullable=False)
    procurement_type = Column(
        SQLEnum(ProcurementType), default=ProcurementType.STANDARD
    )
    priority = Column(String(20), default="normal")

    # Financial terms
    currency = Column(String(3), default="USD")
    payment_terms = Column(SQLEnum(PaymentTerms))
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    shipping_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)

    # Delivery information
    delivery_address = Column(Text)
    delivery_contact = Column(String(100))
    delivery_phone = Column(String(50))
    shipping_method = Column(String(100))

    # Status and workflow
    status = Column(
        SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, index=True
    )
    approval_required = Column(Boolean, default=True)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    acknowledged_at = Column(DateTime)

    # Additional information
    notes = Column(Text)
    terms_conditions = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    receipts = relationship("PurchaseReceipt", back_populates="purchase_order")


class PurchaseOrderLine(Base):
    """Purchase order line items"""

    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False
    )
    line_number = Column(String(10), nullable=False)

    # Product information
    product_id = Column(UUID(as_uuid=True))
    sku = Column(String(100))
    description = Column(String(500), nullable=False)
    specification = Column(Text)

    # Quantity and pricing
    quantity = Column(Numeric(12, 4), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    unit_price = Column(Numeric(12, 4), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_rate = Column(Numeric(5, 4), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    line_total = Column(Numeric(15, 2), nullable=False)

    # Delivery
    required_date = Column(DateTime)
    delivery_location = Column(String(255))

    # Receiving tracking
    quantity_received = Column(Numeric(12, 4), default=0)
    quantity_billed = Column(Numeric(12, 4), default=0)

    # Status
    status = Column(String(50), default="active")

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")


class PurchaseReceipt(Base):
    """Purchase receipt/goods received note"""

    __tablename__ = "purchase_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_number = Column(String(50), unique=True, nullable=False)
    purchase_order_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False
    )

    # Receipt details
    receipt_date = Column(DateTime, default=datetime.utcnow)
    received_by = Column(String(100), nullable=False)
    delivery_note_number = Column(String(100))
    carrier = Column(String(100))

    # Status
    status = Column(SQLEnum(ReceivingStatus), default=ReceivingStatus.PENDING)
    inspection_required = Column(Boolean, default=True)
    inspection_completed = Column(Boolean, default=False)

    # Quality control
    quality_status = Column(String(50))  # passed, failed, conditional
    inspector = Column(String(100))
    inspection_notes = Column(Text)

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="receipts")
    lines = relationship(
        "PurchaseReceiptLine", back_populates="receipt", cascade="all, delete-orphan"
    )


class PurchaseReceiptLine(Base):
    """Purchase receipt line items"""

    __tablename__ = "purchase_receipt_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_receipts.id"), nullable=False
    )
    po_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id"))

    # Item details
    product_id = Column(UUID(as_uuid=True))
    description = Column(String(500), nullable=False)

    # Quantities
    quantity_ordered = Column(Numeric(12, 4), nullable=False)
    quantity_received = Column(Numeric(12, 4), nullable=False)
    quantity_accepted = Column(Numeric(12, 4), default=0)
    quantity_rejected = Column(Numeric(12, 4), default=0)
    unit_of_measure = Column(String(50), nullable=False)

    # Quality control
    lot_number = Column(String(100))
    expiry_date = Column(DateTime)
    quality_status = Column(String(50))
    rejection_reason = Column(String(500))

    # Location
    received_location = Column(String(255))

    # Relationships
    receipt = relationship("PurchaseReceipt", back_populates="lines")


# Pydantic Models
class VendorBase(BaseModel):
    """Base vendor model"""

    code: str = Field(..., description="Vendor code")
    name: str = Field(..., description="Vendor name")
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    status: VendorStatus = VendorStatus.ACTIVE
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    credit_limit: Optional[Decimal] = None
    currency: str = "USD"


class VendorCreate(VendorBase):
    """Vendor creation model"""

    pass


class VendorUpdate(BaseModel):
    """Vendor update model"""

    name: Optional[str] = None
    legal_name: Optional[str] = None
    status: Optional[VendorStatus] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    payment_terms: Optional[PaymentTerms] = None
    credit_limit: Optional[Decimal] = None


class VendorResponse(VendorBase):
    """Vendor response model"""

    id: uuid.UUID
    rating: Optional[Decimal] = None
    on_time_delivery_rate: Optional[Decimal] = None
    quality_rating: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseRequisitionLineBase(BaseModel):
    """Base purchase requisition line"""

    line_number: str
    product_id: Optional[uuid.UUID] = None
    description: str
    specification: Optional[str] = None
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str
    estimated_unit_price: Optional[Decimal] = None
    required_date: Optional[datetime] = None
    delivery_location: Optional[str] = None


class PurchaseRequisitionBase(BaseModel):
    """Base purchase requisition model"""

    title: str
    description: Optional[str] = None
    requested_by: str
    department: Optional[str] = None
    cost_center: Optional[str] = None
    procurement_type: ProcurementType = ProcurementType.STANDARD
    priority: str = "normal"
    required_date: datetime
    budget_code: Optional[str] = None
    currency: str = "USD"
    lines: List[PurchaseRequisitionLineBase] = []


class PurchaseRequisitionCreate(PurchaseRequisitionBase):
    """Purchase requisition creation model"""

    pass


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line"""

    line_number: str
    product_id: Optional[uuid.UUID] = None
    sku: Optional[str] = None
    description: str
    specification: Optional[str] = None
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str
    unit_price: Decimal = Field(..., ge=0)
    discount_percentage: Decimal = Field(default=0, ge=0, le=100)
    tax_rate: Decimal = Field(default=0, ge=0)
    required_date: Optional[datetime] = None
    delivery_location: Optional[str] = None


class PurchaseOrderBase(BaseModel):
    """Base purchase order model"""

    vendor_id: uuid.UUID
    required_date: datetime
    procurement_type: ProcurementType = ProcurementType.STANDARD
    priority: str = "normal"
    currency: str = "USD"
    payment_terms: Optional[PaymentTerms] = None
    delivery_address: Optional[str] = None
    delivery_contact: Optional[str] = None
    delivery_phone: Optional[str] = None
    shipping_method: Optional[str] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    lines: List[PurchaseOrderLineBase] = []


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation model"""

    pass


class PurchaseOrderResponse(BaseModel):
    """Purchase order response model"""

    id: uuid.UUID
    po_number: str
    vendor_id: uuid.UUID
    vendor_name: str
    order_date: datetime
    required_date: datetime
    status: PurchaseOrderStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseReceiptLineBase(BaseModel):
    """Base purchase receipt line"""

    po_line_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    description: str
    quantity_ordered: Decimal
    quantity_received: Decimal = Field(..., ge=0)
    quantity_accepted: Decimal = Field(default=0, ge=0)
    quantity_rejected: Decimal = Field(default=0, ge=0)
    unit_of_measure: str
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    quality_status: Optional[str] = None
    rejection_reason: Optional[str] = None
    received_location: Optional[str] = None


class PurchaseReceiptBase(BaseModel):
    """Base purchase receipt model"""

    purchase_order_id: uuid.UUID
    received_by: str
    delivery_note_number: Optional[str] = None
    carrier: Optional[str] = None
    inspection_required: bool = True
    notes: Optional[str] = None
    lines: List[PurchaseReceiptLineBase] = []


class PurchaseReceiptCreate(PurchaseReceiptBase):
    """Purchase receipt creation model"""

    pass


class CostAnalysisRequest(BaseModel):
    """Cost analysis request model"""

    vendor_ids: Optional[List[uuid.UUID]] = None
    product_ids: Optional[List[uuid.UUID]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    analysis_type: str = "variance"  # variance, trend, comparison
    group_by: str = "vendor"  # vendor, product, category, month


# Service Layer
class PurchaseOrderManagementService:
    """Comprehensive purchase order management service"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis) -> dict:
        self.db = db
        self.redis = redis_client

    # Vendor Management
    async def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        """Create new vendor"""
        # Check if vendor code already exists
        existing_vendor = await self.db.execute(
            select(Vendor).where(Vendor.code == vendor_data.code)
        )
        if existing_vendor.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Vendor code already exists")

        vendor = Vendor(**vendor_data.dict())
        self.db.add(vendor)
        await self.db.commit()
        await self.db.refresh(vendor)

        # Cache vendor data
        await self._cache_vendor(vendor)

        return vendor

    async def get_vendors(
        self,
        status: Optional[VendorStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get vendors with filtering"""
        query = select(Vendor)

        # Apply filters
        if status:
            query = query.where(Vendor.status == status)

        if search:
            search_filter = or_(
                Vendor.name.ilike(f"%{search}%"),
                Vendor.code.ilike(f"%{search}%"),
                Vendor.contact_person.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Vendor.name)

        result = await self.db.execute(query)
        vendors = result.scalars().all()

        return {"vendors": vendors, "total": total, "skip": skip, "limit": limit}

    async def update_vendor_performance(
        self, vendor_id: uuid.UUID, on_time_delivery: bool, quality_rating: Decimal
    ) -> Vendor:
        """Update vendor performance metrics"""
        vendor = await self.db.get(Vendor, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        # Update on-time delivery rate
        current_orders = await self.db.execute(
            select(func.count(PurchaseOrder.id)).where(
                and_(
                    PurchaseOrder.vendor_id == vendor_id,
                    PurchaseOrder.status.in_(
                        [PurchaseOrderStatus.COMPLETED, PurchaseOrderStatus.RECEIVED]
                    ),
                )
            )
        )
        total_orders = current_orders.scalar() or 1

        # Simple running average (in production, use more sophisticated calculation)
        if vendor.on_time_delivery_rate:
            new_rate = (
                vendor.on_time_delivery_rate * (total_orders - 1)
                + (100 if on_time_delivery else 0)
            ) / total_orders
        else:
            new_rate = 100 if on_time_delivery else 0

        vendor.on_time_delivery_rate = Decimal(str(new_rate)).quantize(Decimal("0.01"))

        # Update quality rating (weighted average)
        if vendor.quality_rating:
            vendor.quality_rating = (vendor.quality_rating + quality_rating) / 2
        else:
            vendor.quality_rating = quality_rating

        # Calculate overall rating
        vendor.rating = (vendor.on_time_delivery_rate / 20 + vendor.quality_rating) / 2

        await self.db.commit()
        await self.db.refresh(vendor)

        return vendor

    # Purchase Requisition Management
    async def create_purchase_requisition(
        self, requisition_data: PurchaseRequisitionCreate
    ) -> PurchaseRequisition:
        """Create new purchase requisition"""
        # Generate requisition number
        req_number = await self._generate_requisition_number()

        # Calculate estimated total
        estimated_total = Decimal("0")
        for line in requisition_data.lines:
            if line.estimated_unit_price:
                estimated_total += line.quantity * line.estimated_unit_price

        # Create requisition
        requisition = PurchaseRequisition(
            requisition_number=req_number,
            estimated_total=estimated_total,
            **requisition_data.dict(exclude={"lines"}),
        )

        self.db.add(requisition)
        await self.db.flush()

        # Create requisition lines
        for line_data in requisition_data.lines:
            line = PurchaseRequisitionLine(
                requisition_id=requisition.id,
                estimated_total_price=line_data.quantity
                * (line_data.estimated_unit_price or Decimal("0")),
                **line_data.dict(),
            )
            self.db.add(line)

        await self.db.commit()
        await self.db.refresh(requisition)

        return requisition

    async def approve_requisition(
        self, requisition_id: uuid.UUID, approved_by: str, notes: Optional[str] = None
    ) -> PurchaseRequisition:
        """Approve purchase requisition"""
        requisition = await self.db.get(PurchaseRequisition, requisition_id)
        if not requisition:
            raise HTTPException(status_code=404, detail="Requisition not found")

        if requisition.approval_status != "pending":
            raise HTTPException(status_code=400, detail="Requisition already processed")

        requisition.approval_status = "approved"
        requisition.approved_by = approved_by
        requisition.approved_at = datetime.utcnow()
        requisition.status = "approved"

        await self.db.commit()
        await self.db.refresh(requisition)

        return requisition

    # Purchase Order Management
    async def create_purchase_order(
        self, po_data: PurchaseOrderCreate
    ) -> PurchaseOrder:
        """Create new purchase order"""
        # Validate vendor
        vendor = await self.db.get(Vendor, po_data.vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        if vendor.status != VendorStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Vendor is not active")

        # Generate PO number
        po_number = await self._generate_po_number()

        # Calculate totals
        totals = self._calculate_po_totals(po_data.lines)

        # Create purchase order
        purchase_order = PurchaseOrder(
            po_number=po_number,
            payment_terms=po_data.payment_terms or vendor.payment_terms,
            **po_data.dict(exclude={"lines"}),
            **totals,
        )

        self.db.add(purchase_order)
        await self.db.flush()

        # Create PO lines
        for line_data in po_data.lines:
            line_total = self._calculate_line_total(
                line_data.quantity,
                line_data.unit_price,
                line_data.discount_percentage,
                line_data.tax_rate,
            )

            line = PurchaseOrderLine(
                purchase_order_id=purchase_order.id,
                discount_amount=line_data.quantity
                * line_data.unit_price
                * line_data.discount_percentage
                / 100,
                tax_amount=line_total * line_data.tax_rate / 100,
                line_total=line_total + (line_total * line_data.tax_rate / 100),
                **line_data.dict(),
            )
            self.db.add(line)

        await self.db.commit()
        await self.db.refresh(purchase_order)

        # Cache PO data
        await self._cache_purchase_order(purchase_order)

        return purchase_order

    async def get_purchase_orders(
        self,
        vendor_id: Optional[uuid.UUID] = None,
        status: Optional[PurchaseOrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get purchase orders with filtering"""
        query = select(PurchaseOrder).options(selectinload(PurchaseOrder.vendor))

        # Apply filters
        if vendor_id:
            query = query.where(PurchaseOrder.vendor_id == vendor_id)

        if status:
            query = query.where(PurchaseOrder.status == status)

        if start_date:
            query = query.where(PurchaseOrder.order_date >= start_date)

        if end_date:
            query = query.where(PurchaseOrder.order_date <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = (
            query.offset(skip).limit(limit).order_by(PurchaseOrder.order_date.desc())
        )

        result = await self.db.execute(query)
        orders = result.scalars().all()

        return {"purchase_orders": orders, "total": total, "skip": skip, "limit": limit}

    async def approve_purchase_order(
        self, po_id: uuid.UUID, approved_by: str
    ) -> PurchaseOrder:
        """Approve purchase order"""
        po = await self.db.get(PurchaseOrder, po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if po.status != PurchaseOrderStatus.PENDING_APPROVAL:
            raise HTTPException(
                status_code=400, detail="Purchase order not pending approval"
            )

        po.status = PurchaseOrderStatus.APPROVED
        po.approved_by = approved_by
        po.approved_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(po)

        return po

    async def send_purchase_order(self, po_id: uuid.UUID) -> Dict[str, Any]:
        """Send purchase order to vendor"""
        po = await self.db.get(PurchaseOrder, po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if po.status != PurchaseOrderStatus.APPROVED:
            raise HTTPException(
                status_code=400, detail="Purchase order must be approved before sending"
            )

        # In a real implementation, this would integrate with email/EDI systems
        po.status = PurchaseOrderStatus.SENT
        po.sent_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(po)

        return {
            "message": "Purchase order sent successfully",
            "po_number": po.po_number,
            "sent_at": po.sent_at,
        }

    # Purchase Receipt Management
    async def create_purchase_receipt(
        self, receipt_data: PurchaseReceiptCreate
    ) -> PurchaseReceipt:
        """Create purchase receipt/goods received note"""
        # Validate purchase order
        po = await self.db.get(PurchaseOrder, receipt_data.purchase_order_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if po.status not in [
            PurchaseOrderStatus.SENT,
            PurchaseOrderStatus.ACKNOWLEDGED,
        ]:
            raise HTTPException(
                status_code=400, detail="Purchase order not ready for receiving"
            )

        # Generate receipt number
        receipt_number = await self._generate_receipt_number()

        # Create receipt
        receipt = PurchaseReceipt(
            receipt_number=receipt_number, **receipt_data.dict(exclude={"lines"})
        )

        self.db.add(receipt)
        await self.db.flush()

        # Create receipt lines
        for line_data in receipt_data.lines:
            line = PurchaseReceiptLine(receipt_id=receipt.id, **line_data.dict())
            self.db.add(line)

        # Update PO status
        await self._update_po_receiving_status(po.id)

        await self.db.commit()
        await self.db.refresh(receipt)

        return receipt

    async def complete_inspection(
        self,
        receipt_id: uuid.UUID,
        inspector: str,
        quality_status: str,
        notes: Optional[str] = None,
    ) -> PurchaseReceipt:
        """Complete quality inspection"""
        receipt = await self.db.get(PurchaseReceipt, receipt_id)
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        receipt.inspection_completed = True
        receipt.quality_status = quality_status
        receipt.inspector = inspector
        receipt.inspection_notes = notes

        if quality_status == "passed":
            receipt.status = ReceivingStatus.COMPLETED
        elif quality_status == "failed":
            receipt.status = ReceivingStatus.REJECTED
        else:
            receipt.status = ReceivingStatus.DISCREPANCY

        await self.db.commit()
        await self.db.refresh(receipt)

        return receipt

    # Cost Analysis
    async def generate_cost_analysis(
        self, request: CostAnalysisRequest
    ) -> Dict[str, Any]:
        """Generate cost analysis report"""
        base_query = (
            select(PurchaseOrder, PurchaseOrderLine, Vendor)
            .join(
                PurchaseOrderLine,
                PurchaseOrder.id == PurchaseOrderLine.purchase_order_id,
            )
            .join(Vendor, PurchaseOrder.vendor_id == Vendor.id)
        )

        # Apply filters
        if request.vendor_ids:
            base_query = base_query.where(
                PurchaseOrder.vendor_id.in_(request.vendor_ids)
            )

        if request.start_date:
            base_query = base_query.where(
                PurchaseOrder.order_date >= request.start_date
            )

        if request.end_date:
            base_query = base_query.where(PurchaseOrder.order_date <= request.end_date)

        result = await self.db.execute(base_query)
        data = result.all()

        # Analyze based on analysis type
        if request.analysis_type == "variance":
            analysis = await self._analyze_cost_variance(data, request.group_by)
        elif request.analysis_type == "trend":
            analysis = await self._analyze_cost_trend(data, request.group_by)
        else:
            analysis = await self._analyze_cost_comparison(data, request.group_by)

        return {
            "analysis_type": request.analysis_type,
            "group_by": request.group_by,
            "period": {"start_date": request.start_date, "end_date": request.end_date},
            "summary": analysis["summary"],
            "details": analysis["details"],
            "recommendations": analysis["recommendations"],
        }

    # Helper Methods
    async def _generate_po_number(self) -> str:
        """Generate unique purchase order number"""
        today = datetime.utcnow().strftime("%Y%m%d")
        counter = await self.redis.incr(f"po_counter_{today}")
        await self.redis.expire(f"po_counter_{today}", 86400)  # 24 hours
        return f"PO-{today}-{counter:06d}"

    async def _generate_requisition_number(self) -> str:
        """Generate unique requisition number"""
        today = datetime.utcnow().strftime("%Y%m%d")
        counter = await self.redis.incr(f"req_counter_{today}")
        await self.redis.expire(f"req_counter_{today}", 86400)
        return f"REQ-{today}-{counter:06d}"

    async def _generate_receipt_number(self) -> str:
        """Generate unique receipt number"""
        today = datetime.utcnow().strftime("%Y%m%d")
        counter = await self.redis.incr(f"receipt_counter_{today}")
        await self.redis.expire(f"receipt_counter_{today}", 86400)
        return f"GRN-{today}-{counter:06d}"

    def _calculate_po_totals(
        self, lines: List[PurchaseOrderLineBase]
    ) -> Dict[str, Decimal]:
        """Calculate purchase order totals"""
        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")

        for line in lines:
            line_subtotal = line.quantity * line.unit_price
            line_discount = line_subtotal * line.discount_percentage / 100
            line_net = line_subtotal - line_discount
            line_tax = line_net * line.tax_rate / 100

            subtotal += line_subtotal
            discount_amount += line_discount
            tax_amount += line_tax

        total_amount = subtotal - discount_amount + tax_amount

        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
        }

    def _calculate_line_total(
        self,
        quantity: Decimal,
        unit_price: Decimal,
        discount_percentage: Decimal,
        tax_rate: Decimal,
    ) -> Decimal:
        """Calculate line total before tax"""
        subtotal = quantity * unit_price
        discount = subtotal * discount_percentage / 100
        return subtotal - discount

    async def _cache_vendor(self, vendor: Vendor) -> None:
        """Cache vendor data"""
        vendor_data = {
            "id": str(vendor.id),
            "code": vendor.code,
            "name": vendor.name,
            "status": vendor.status,
            "payment_terms": vendor.payment_terms,
        }
        await self.redis.setex(
            f"vendor:{vendor.id}",
            3600,  # 1 hour
            str(vendor_data),
        )

    async def _cache_purchase_order(self, po: PurchaseOrder) -> None:
        """Cache purchase order data"""
        po_data = {
            "id": str(po.id),
            "po_number": po.po_number,
            "vendor_id": str(po.vendor_id),
            "status": po.status,
            "total_amount": str(po.total_amount),
        }
        await self.redis.setex(
            f"purchase_order:{po.id}",
            7200,  # 2 hours
            str(po_data),
        )

    async def _update_po_receiving_status(self, po_id: uuid.UUID) -> None:
        """Update purchase order receiving status"""
        # Check if all lines are fully received
        po_lines = await self.db.execute(
            select(PurchaseOrderLine).where(
                PurchaseOrderLine.purchase_order_id == po_id
            )
        )
        lines = po_lines.scalars().all()

        fully_received = all(line.quantity_received >= line.quantity for line in lines)
        partially_received = any(line.quantity_received > 0 for line in lines)

        po = await self.db.get(PurchaseOrder, po_id)
        if fully_received:
            po.status = PurchaseOrderStatus.RECEIVED
        elif partially_received:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED

    async def _analyze_cost_variance(self, data: List, group_by: str) -> Dict[str, Any]:
        """Analyze cost variance"""
        # Simplified implementation
        total_spend = sum(row.PurchaseOrderLine.line_total for row in data)
        avg_unit_cost = total_spend / len(data) if data else Decimal("0")

        return {
            "summary": {
                "total_spend": total_spend,
                "average_unit_cost": avg_unit_cost,
                "variance_percentage": Decimal("0"),  # Placeholder
            },
            "details": [],
            "recommendations": [
                "Consider negotiating better prices with high-spend vendors",
                "Review procurement processes for cost optimization",
            ],
        }

    async def _analyze_cost_trend(self, data: List, group_by: str) -> Dict[str, Any]:
        """Analyze cost trends"""
        # Simplified implementation
        return {"summary": {"trend": "stable"}, "details": [], "recommendations": []}

    async def _analyze_cost_comparison(
        self, data: List, group_by: str
    ) -> Dict[str, Any]:
        """Compare costs across different dimensions"""
        # Simplified implementation
        return {
            "summary": {"comparison": "baseline"},
            "details": [],
            "recommendations": [],
        }


# API Router
router = APIRouter(
    prefix="/api/v1/purchase-orders", tags=["Purchase Order Management v69"]
)


@router.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    vendor_data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
) -> VendorResponse:
    """Create new vendor"""
    service = PurchaseOrderManagementService(db, redis_client)
    vendor = await service.create_vendor(vendor_data)
    return VendorResponse.from_orm(vendor)


@router.get("/vendors")
async def get_vendors(
    status: Optional[VendorStatus] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Get vendors with filtering"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.get_vendors(status, search, skip, limit)


@router.post("/requisitions")
async def create_purchase_requisition(
    requisition_data: PurchaseRequisitionCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Create new purchase requisition"""
    service = PurchaseOrderManagementService(db, redis_client)
    requisition = await service.create_purchase_requisition(requisition_data)
    return requisition


@router.put("/requisitions/{requisition_id}/approve")
async def approve_requisition(
    requisition_id: uuid.UUID,
    approved_by: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Approve purchase requisition"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.approve_requisition(requisition_id, approved_by, notes)


@router.post("/", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
) -> PurchaseOrderResponse:
    """Create new purchase order"""
    service = PurchaseOrderManagementService(db, redis_client)
    po = await service.create_purchase_order(po_data)

    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        vendor_id=po.vendor_id,
        vendor_name=po.vendor.name,
        order_date=po.order_date,
        required_date=po.required_date,
        status=po.status,
        subtotal=po.subtotal,
        tax_amount=po.tax_amount,
        total_amount=po.total_amount,
        currency=po.currency,
        created_at=po.created_at,
        updated_at=po.updated_at,
    )


@router.get("/")
async def get_purchase_orders(
    vendor_id: Optional[uuid.UUID] = None,
    status: Optional[PurchaseOrderStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Get purchase orders with filtering"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.get_purchase_orders(
        vendor_id, status, start_date, end_date, skip, limit
    )


@router.put("/{po_id}/approve")
async def approve_purchase_order(
    po_id: uuid.UUID,
    approved_by: str,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Approve purchase order"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.approve_purchase_order(po_id, approved_by)


@router.post("/{po_id}/send")
async def send_purchase_order(
    po_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Send purchase order to vendor"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.send_purchase_order(po_id)


@router.post("/receipts")
async def create_purchase_receipt(
    receipt_data: PurchaseReceiptCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Create purchase receipt/goods received note"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.create_purchase_receipt(receipt_data)


@router.put("/receipts/{receipt_id}/inspect")
async def complete_inspection(
    receipt_id: uuid.UUID,
    inspector: str,
    quality_status: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Complete quality inspection"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.complete_inspection(
        receipt_id, inspector, quality_status, notes
    )


@router.post("/cost-analysis")
async def generate_cost_analysis(
    request: CostAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Generate cost analysis report"""
    service = PurchaseOrderManagementService(db, redis_client)
    return await service.generate_cost_analysis(request)


# Include router in main app
def get_router() -> None:
    """Get the purchase order management router"""
    return router
