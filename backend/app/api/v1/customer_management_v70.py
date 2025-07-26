"""
ITDO ERP Backend - Customer Management v70
Complete Customer Relationship Management System with segmentation, loyalty, and analytics
Day 12: Customer Management Implementation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
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
class CustomerStatus(str, Enum):
    """Customer status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class CustomerType(str, Enum):
    """Customer type enumeration"""

    INDIVIDUAL = "individual"
    BUSINESS = "business"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerSegment(str, Enum):
    """Customer segment enumeration"""

    PREMIUM = "premium"
    STANDARD = "standard"
    BASIC = "basic"
    VIP = "vip"
    ENTERPRISE = "enterprise"


class ContactType(str, Enum):
    """Contact type enumeration"""

    PRIMARY = "primary"
    BILLING = "billing"
    SHIPPING = "shipping"
    TECHNICAL = "technical"
    SALES = "sales"


class TicketStatus(str, Enum):
    """Support ticket status enumeration"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketPriority(str, Enum):
    """Support ticket priority enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class LoyaltyTierStatus(str, Enum):
    """Loyalty tier status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


# Database Models
class Customer(Base):
    """Customer master model"""

    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(300))
    customer_type = Column(SQLEnum(CustomerType), default=CustomerType.INDIVIDUAL)
    status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.ACTIVE, index=True)

    # Business information
    tax_id = Column(String(50))
    business_registration = Column(String(100))
    industry = Column(String(100))
    website = Column(String(255))

    # Segmentation
    segment = Column(SQLEnum(CustomerSegment), default=CustomerSegment.STANDARD)
    credit_limit = Column(Numeric(15, 2))
    payment_terms = Column(String(50), default="net_30")
    currency = Column(String(3), default="USD")

    # Contact preferences
    preferred_language = Column(String(10), default="en")
    preferred_communication = Column(
        String(20), default="email"
    )  # email, phone, sms, mail
    timezone = Column(String(50))

    # Analytics fields
    total_orders = Column(Numeric(10, 0), default=0)
    total_revenue = Column(Numeric(15, 2), default=0)
    average_order_value = Column(Numeric(15, 2), default=0)
    lifetime_value = Column(Numeric(15, 2), default=0)
    last_order_date = Column(DateTime)
    acquisition_date = Column(DateTime, default=datetime.utcnow)
    acquisition_source = Column(String(100))

    # Risk and compliance
    risk_score = Column(Numeric(5, 2), default=0)  # 0-100
    compliance_status = Column(String(50), default="compliant")
    kyc_verified = Column(Boolean, default=False)
    kyc_verification_date = Column(DateTime)

    # Notes and tags
    notes = Column(Text)
    tags = Column(String(500))  # Comma-separated tags

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contacts = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan"
    )
    addresses = relationship(
        "CustomerAddress", back_populates="customer", cascade="all, delete-orphan"
    )
    tickets = relationship("SupportTicket", back_populates="customer")
    loyalty_accounts = relationship("LoyaltyAccount", back_populates="customer")


class CustomerContact(Base):
    """Customer contact information"""

    __tablename__ = "customer_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    contact_type = Column(SQLEnum(ContactType), default=ContactType.PRIMARY)

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(50))
    department = Column(String(100))

    # Contact information
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))
    fax = Column(String(50))

    # Preferences
    is_primary = Column(Boolean, default=False)
    receive_marketing = Column(Boolean, default=True)
    receive_notifications = Column(Boolean, default=True)
    preferred_contact_method = Column(String(20), default="email")

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="contacts")


class CustomerAddress(Base):
    """Customer address information"""

    __tablename__ = "customer_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    address_type = Column(String(20), default="billing")  # billing, shipping, mailing

    # Address components
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), nullable=False)

    # Flags
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Validation
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="addresses")


class SupportTicket(Base):
    """Customer support ticket"""

    __tablename__ = "support_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Ticket details
    subject = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100))
    subcategory = Column(String(100))

    # Status and priority
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN, index=True)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM)

    # Assignment
    assigned_to = Column(String(100))
    assigned_team = Column(String(100))

    # Tracking
    reported_by = Column(String(100))
    resolution = Column(Text)
    resolution_time = Column(Numeric(10, 2))  # Hours to resolution

    # Dates
    due_date = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Customer satisfaction
    satisfaction_rating = Column(Numeric(3, 2))  # 1-5 scale
    feedback = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="tickets")
    interactions = relationship(
        "TicketInteraction", back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketInteraction(Base):
    """Support ticket interactions"""

    __tablename__ = "ticket_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(
        UUID(as_uuid=True), ForeignKey("support_tickets.id"), nullable=False
    )

    # Interaction details
    interaction_type = Column(
        String(50), nullable=False
    )  # note, email, call, chat, status_change
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)

    # Author
    created_by = Column(String(100), nullable=False)
    created_by_type = Column(String(20), default="staff")  # staff, customer, system

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket = relationship("SupportTicket", back_populates="interactions")


class LoyaltyTier(Base):
    """Loyalty program tiers"""

    __tablename__ = "loyalty_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    # Tier requirements
    minimum_points = Column(Numeric(10, 0), default=0)
    minimum_spending = Column(Numeric(15, 2), default=0)
    minimum_orders = Column(Numeric(5, 0), default=0)

    # Benefits
    points_multiplier = Column(Numeric(5, 2), default=1.0)  # Points earned multiplier
    discount_percentage = Column(Numeric(5, 2), default=0)
    free_shipping = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)

    # Configuration
    is_active = Column(Boolean, default=True)
    sort_order = Column(Numeric(3, 0), default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    loyalty_accounts = relationship("LoyaltyAccount", back_populates="tier")


class LoyaltyAccount(Base):
    """Customer loyalty account"""

    __tablename__ = "loyalty_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, unique=True
    )
    tier_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_tiers.id"))

    # Points and status
    current_points = Column(Numeric(12, 0), default=0)
    lifetime_points_earned = Column(Numeric(15, 0), default=0)
    lifetime_points_redeemed = Column(Numeric(15, 0), default=0)
    tier_points = Column(Numeric(12, 0), default=0)  # Points for tier calculation

    # Tier tracking
    tier_status = Column(SQLEnum(LoyaltyTierStatus), default=LoyaltyTierStatus.ACTIVE)
    tier_achieved_date = Column(DateTime)
    tier_expiry_date = Column(DateTime)

    # Account status
    is_active = Column(Boolean, default=True)
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    last_activity_date = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="loyalty_accounts")
    tier = relationship("LoyaltyTier", back_populates="loyalty_accounts")
    transactions = relationship(
        "LoyaltyTransaction", back_populates="account", cascade="all, delete-orphan"
    )


class LoyaltyTransaction(Base):
    """Loyalty points transactions"""

    __tablename__ = "loyalty_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True), ForeignKey("loyalty_accounts.id"), nullable=False
    )

    # Transaction details
    transaction_type = Column(
        String(20), nullable=False
    )  # earned, redeemed, expired, adjusted
    points = Column(Numeric(10, 0), nullable=False)
    points_balance = Column(Numeric(12, 0), nullable=False)

    # Reference information
    reference_type = Column(String(50))  # order, return, manual, expiry
    reference_id = Column(String(100))
    description = Column(String(500))

    # Expiry tracking
    expiry_date = Column(DateTime)
    is_expired = Column(Boolean, default=False)

    # Processing
    processed_by = Column(String(100))
    processing_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    account = relationship("LoyaltyAccount", back_populates="transactions")


class CustomerAnalytics(Base):
    """Customer analytics and insights"""

    __tablename__ = "customer_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, unique=True
    )

    # RFM Analysis (Recency, Frequency, Monetary)
    rfm_recency = Column(Numeric(5, 0))  # Days since last order
    rfm_frequency = Column(Numeric(5, 0))  # Number of orders
    rfm_monetary = Column(Numeric(15, 2))  # Total spending
    rfm_score = Column(String(3))  # e.g., "555" for best customers

    # Purchase behavior
    preferred_categories = Column(String(500))
    preferred_brands = Column(String(500))
    average_days_between_orders = Column(Numeric(5, 1))
    seasonal_patterns = Column(Text)  # JSON data

    # Engagement metrics
    email_open_rate = Column(Numeric(5, 2))
    email_click_rate = Column(Numeric(5, 2))
    website_visits = Column(Numeric(8, 0))
    last_website_visit = Column(DateTime)

    # Predictions
    churn_probability = Column(Numeric(5, 2))  # 0-100%
    next_purchase_prediction = Column(DateTime)
    predicted_ltv = Column(Numeric(15, 2))

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models
class CustomerContactBase(BaseModel):
    """Base customer contact model"""

    contact_type: ContactType = ContactType.PRIMARY
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    receive_marketing: bool = True
    receive_notifications: bool = True
    preferred_contact_method: str = "email"
    notes: Optional[str] = None


class CustomerAddressBase(BaseModel):
    """Base customer address model"""

    address_type: str = "billing"
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = Field(..., min_length=1, max_length=100)
    is_primary: bool = False
    is_active: bool = True


class CustomerBase(BaseModel):
    """Base customer model"""

    name: str = Field(..., min_length=1, max_length=200)
    legal_name: Optional[str] = None
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    status: CustomerStatus = CustomerStatus.ACTIVE
    tax_id: Optional[str] = None
    business_registration: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    segment: CustomerSegment = CustomerSegment.STANDARD
    credit_limit: Optional[Decimal] = None
    payment_terms: str = "net_30"
    currency: str = "USD"
    preferred_language: str = "en"
    preferred_communication: str = "email"
    timezone: Optional[str] = None
    acquisition_source: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Customer creation model"""

    contacts: List[CustomerContactBase] = []
    addresses: List[CustomerAddressBase] = []


class CustomerUpdate(BaseModel):
    """Customer update model"""

    name: Optional[str] = None
    legal_name: Optional[str] = None
    status: Optional[CustomerStatus] = None
    segment: Optional[CustomerSegment] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_communication: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class CustomerResponse(CustomerBase):
    """Customer response model"""

    id: uuid.UUID
    customer_number: str
    total_orders: Decimal
    total_revenue: Decimal
    average_order_value: Decimal
    lifetime_value: Decimal
    last_order_date: Optional[datetime] = None
    acquisition_date: datetime
    risk_score: Decimal
    compliance_status: str
    kyc_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportTicketBase(BaseModel):
    """Base support ticket model"""

    subject: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: TicketPriority = TicketPriority.MEDIUM
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    due_date: Optional[datetime] = None


class SupportTicketCreate(SupportTicketBase):
    """Support ticket creation model"""

    customer_id: uuid.UUID
    reported_by: str


class SupportTicketUpdate(BaseModel):
    """Support ticket update model"""

    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    resolution: Optional[str] = None
    due_date: Optional[datetime] = None


class TicketInteractionCreate(BaseModel):
    """Ticket interaction creation model"""

    interaction_type: str
    content: str
    is_internal: bool = False
    created_by: str
    created_by_type: str = "staff"


class LoyaltyTierBase(BaseModel):
    """Base loyalty tier model"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    minimum_points: Decimal = Field(default=0, ge=0)
    minimum_spending: Decimal = Field(default=0, ge=0)
    minimum_orders: Decimal = Field(default=0, ge=0)
    points_multiplier: Decimal = Field(default=1.0, ge=0.1, le=10.0)
    discount_percentage: Decimal = Field(default=0, ge=0, le=100)
    free_shipping: bool = False
    priority_support: bool = False
    is_active: bool = True
    sort_order: Decimal = Field(default=0, ge=0)


class LoyaltyTierCreate(LoyaltyTierBase):
    """Loyalty tier creation model"""

    pass


class LoyaltyTransactionRequest(BaseModel):
    """Loyalty transaction request model"""

    customer_id: uuid.UUID
    transaction_type: str  # earned, redeemed, expired, adjusted
    points: Decimal = Field(
        ..., description="Points amount (positive for earn, negative for redeem)"
    )
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    processed_by: str


class CustomerAnalyticsRequest(BaseModel):
    """Customer analytics request model"""

    customer_ids: Optional[List[uuid.UUID]] = None
    segments: Optional[List[CustomerSegment]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    analytics_type: str = "rfm"  # rfm, churn, ltv, segmentation
    include_predictions: bool = True


# Service Layer
class CustomerManagementService:
    """Comprehensive customer management service"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    # Customer Management
    async def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """Create new customer with contacts and addresses"""
        # Generate customer number
        customer_number = await self._generate_customer_number()

        # Create customer
        customer = Customer(
            customer_number=customer_number,
            **customer_data.dict(exclude={"contacts", "addresses"}),
        )

        self.db.add(customer)
        await self.db.flush()

        # Create contacts
        for contact_data in customer_data.contacts:
            contact = CustomerContact(customer_id=customer.id, **contact_data.dict())
            self.db.add(contact)

        # Create addresses
        for address_data in customer_data.addresses:
            address = CustomerAddress(customer_id=customer.id, **address_data.dict())
            self.db.add(address)

        await self.db.commit()
        await self.db.refresh(customer)

        # Cache customer data
        await self._cache_customer(customer)

        # Initialize loyalty account if applicable
        await self._initialize_loyalty_account(customer.id)

        return customer

    async def get_customers(
        self,
        status: Optional[CustomerStatus] = None,
        segment: Optional[CustomerSegment] = None,
        customer_type: Optional[CustomerType] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get customers with filtering"""
        query = select(Customer).options(
            selectinload(Customer.contacts), selectinload(Customer.addresses)
        )

        # Apply filters
        if status:
            query = query.where(Customer.status == status)

        if segment:
            query = query.where(Customer.segment == segment)

        if customer_type:
            query = query.where(Customer.customer_type == customer_type)

        if search:
            search_filter = or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.customer_number.ilike(f"%{search}%"),
                Customer.legal_name.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.alias())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(Customer.name)

        result = await self.db.execute(query)
        customers = result.scalars().all()

        return {"customers": customers, "total": total, "skip": skip, "limit": limit}

    async def update_customer(
        self, customer_id: uuid.UUID, update_data: CustomerUpdate
    ) -> Customer:
        """Update customer information"""
        customer = await self.db.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(customer, field, value)

        customer.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(customer)

        # Update cache
        await self._cache_customer(customer)

        return customer

    async def update_customer_analytics(self, customer_id: uuid.UUID) -> None:
        """Update customer analytics and metrics"""
        customer = await self.db.get(Customer, customer_id)
        if not customer:
            return

        # Calculate basic metrics (simplified for demo)
        # In production, this would involve complex queries and calculations
        total_orders = await self._get_customer_order_count(customer_id)
        total_revenue = await self._get_customer_total_revenue(customer_id)
        last_order_date = await self._get_customer_last_order_date(customer_id)

        # Update customer metrics
        customer.total_orders = total_orders
        customer.total_revenue = total_revenue
        customer.last_order_date = last_order_date

        if total_orders > 0:
            customer.average_order_value = total_revenue / total_orders

        # Calculate lifetime value (simplified)
        customer.lifetime_value = total_revenue * Decimal("1.2")  # 20% markup

        # Update segment based on metrics
        await self._update_customer_segment(customer)

        await self.db.commit()

    # Support Ticket Management
    async def create_support_ticket(
        self, ticket_data: SupportTicketCreate
    ) -> SupportTicket:
        """Create new support ticket"""
        # Validate customer exists
        customer = await self.db.get(Customer, ticket_data.customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Generate ticket number
        ticket_number = await self._generate_ticket_number()

        # Create ticket
        ticket = SupportTicket(
            ticket_number=ticket_number,
            **ticket_data.dict(),
        )

        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)

        # Create initial interaction
        initial_interaction = TicketInteraction(
            ticket_id=ticket.id,
            interaction_type="note",
            content=f"Ticket created: {ticket.description}",
            created_by=ticket_data.reported_by,
            created_by_type="customer",
        )
        self.db.add(initial_interaction)
        await self.db.commit()

        return ticket

    async def update_ticket_status(
        self,
        ticket_id: uuid.UUID,
        status: TicketStatus,
        updated_by: str,
        notes: Optional[str] = None,
    ) -> SupportTicket:
        """Update support ticket status"""
        ticket = await self.db.get(SupportTicket, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        old_status = ticket.status
        ticket.status = status
        ticket.updated_at = datetime.utcnow()

        # Set resolution/close dates
        if status == TicketStatus.RESOLVED and old_status != TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
            # Calculate resolution time
            if ticket.created_at:
                resolution_hours = (
                    datetime.utcnow() - ticket.created_at
                ).total_seconds() / 3600
                ticket.resolution_time = Decimal(str(resolution_hours))

        elif status == TicketStatus.CLOSED and old_status != TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()

        # Create status change interaction
        interaction_content = f"Status changed from {old_status} to {status}"
        if notes:
            interaction_content += f"\nNotes: {notes}"

        interaction = TicketInteraction(
            ticket_id=ticket.id,
            interaction_type="status_change",
            content=interaction_content,
            created_by=updated_by,
            created_by_type="staff",
        )
        self.db.add(interaction)

        await self.db.commit()
        await self.db.refresh(ticket)

        return ticket

    async def add_ticket_interaction(
        self, ticket_id: uuid.UUID, interaction_data: TicketInteractionCreate
    ) -> TicketInteraction:
        """Add interaction to support ticket"""
        ticket = await self.db.get(SupportTicket, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        interaction = TicketInteraction(ticket_id=ticket_id, **interaction_data.dict())

        self.db.add(interaction)

        # Update ticket's last modified time
        ticket.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(interaction)

        return interaction

    # Loyalty Program Management
    async def create_loyalty_tier(self, tier_data: LoyaltyTierCreate) -> LoyaltyTier:
        """Create new loyalty tier"""
        # Check if tier name already exists
        existing_tier = await self.db.execute(
            select(LoyaltyTier).where(LoyaltyTier.name == tier_data.name)
        )
        if existing_tier.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="Loyalty tier name already exists"
            )

        tier = LoyaltyTier(**tier_data.dict())
        self.db.add(tier)
        await self.db.commit()
        await self.db.refresh(tier)

        return tier

    async def process_loyalty_transaction(
        self, transaction_data: LoyaltyTransactionRequest
    ) -> Dict[str, Any]:
        """Process loyalty points transaction"""
        # Get customer's loyalty account
        account_query = select(LoyaltyAccount).where(
            LoyaltyAccount.customer_id == transaction_data.customer_id
        )
        account_result = await self.db.execute(account_query)
        account = account_result.scalar_one_or_none()

        if not account:
            # Create loyalty account if it doesn't exist
            account = await self._initialize_loyalty_account(
                transaction_data.customer_id
            )

        # Validate transaction
        if (
            transaction_data.transaction_type == "redeemed"
            and account.current_points < abs(transaction_data.points)
        ):
            raise HTTPException(status_code=400, detail="Insufficient points balance")

        # Calculate new balance
        points_change = transaction_data.points
        new_balance = account.current_points + points_change

        # Create transaction record
        transaction = LoyaltyTransaction(
            account_id=account.id,
            transaction_type=transaction_data.transaction_type,
            points=points_change,
            points_balance=new_balance,
            reference_type=transaction_data.reference_type,
            reference_id=transaction_data.reference_id,
            description=transaction_data.description,
            processed_by=transaction_data.processed_by,
        )

        # Update account
        account.current_points = new_balance
        account.last_activity_date = datetime.utcnow()

        if transaction_data.transaction_type == "earned":
            account.lifetime_points_earned += points_change
            account.tier_points += points_change
        elif transaction_data.transaction_type == "redeemed":
            account.lifetime_points_redeemed += abs(points_change)

        # Check for tier upgrades
        await self._check_tier_upgrade(account)

        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)

        return {
            "transaction_id": transaction.id,
            "new_balance": new_balance,
            "account_tier": account.tier.name if account.tier else None,
            "message": "Transaction processed successfully",
        }

    async def generate_customer_analytics(
        self, request: CustomerAnalyticsRequest
    ) -> Dict[str, Any]:
        """Generate comprehensive customer analytics"""
        base_query = select(Customer)

        # Apply filters
        if request.customer_ids:
            base_query = base_query.where(Customer.id.in_(request.customer_ids))

        if request.segments:
            base_query = base_query.where(Customer.segment.in_(request.segments))

        result = await self.db.execute(base_query)
        customers = result.scalars().all()

        # Generate analytics based on type
        if request.analytics_type == "rfm":
            analytics = await self._generate_rfm_analysis(customers)
        elif request.analytics_type == "churn":
            analytics = await self._generate_churn_analysis(customers)
        elif request.analytics_type == "ltv":
            analytics = await self._generate_ltv_analysis(customers)
        else:
            analytics = await self._generate_segmentation_analysis(customers)

        return {
            "analytics_type": request.analytics_type,
            "total_customers": len(customers),
            "analysis_date": datetime.utcnow(),
            "summary": analytics["summary"],
            "segments": analytics["segments"],
            "recommendations": analytics["recommendations"],
            "include_predictions": request.include_predictions,
        }

    # Helper Methods
    async def _generate_customer_number(self) -> str:
        """Generate unique customer number"""
        today = datetime.utcnow().strftime("%Y%m%d")
        counter = await self.redis.incr(f"customer_counter_{today}")
        await self.redis.expire(f"customer_counter_{today}", 86400)  # 24 hours
        return f"CUST-{today}-{counter:06d}"

    async def _generate_ticket_number(self) -> str:
        """Generate unique ticket number"""
        today = datetime.utcnow().strftime("%Y%m%d")
        counter = await self.redis.incr(f"ticket_counter_{today}")
        await self.redis.expire(f"ticket_counter_{today}", 86400)
        return f"TKT-{today}-{counter:06d}"

    async def _cache_customer(self, customer: Customer) -> None:
        """Cache customer data"""
        customer_data = {
            "id": str(customer.id),
            "customer_number": customer.customer_number,
            "name": customer.name,
            "status": customer.status,
            "segment": customer.segment,
        }
        await self.redis.setex(
            f"customer:{customer.id}",
            3600,  # 1 hour
            str(customer_data),
        )

    async def _initialize_loyalty_account(
        self, customer_id: uuid.UUID
    ) -> LoyaltyAccount:
        """Initialize loyalty account for customer"""
        # Get default tier (lowest tier)
        default_tier_query = (
            select(LoyaltyTier)
            .where(LoyaltyTier.is_active)
            .order_by(LoyaltyTier.sort_order)
        )
        tier_result = await self.db.execute(default_tier_query)
        default_tier = tier_result.scalars().first()

        account = LoyaltyAccount(
            customer_id=customer_id, tier_id=default_tier.id if default_tier else None
        )

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        return account

    async def _check_tier_upgrade(self, account: LoyaltyAccount) -> None:
        """Check and process tier upgrades"""
        # Get all active tiers ordered by requirements
        tiers_query = (
            select(LoyaltyTier)
            .where(LoyaltyTier.is_active)
            .order_by(LoyaltyTier.minimum_points.desc())
        )
        tiers_result = await self.db.execute(tiers_query)
        tiers = tiers_result.scalars().all()

        # Find highest qualifying tier
        new_tier = None
        for tier in tiers:
            if account.tier_points >= tier.minimum_points:
                new_tier = tier
                break

        # Update tier if changed
        if new_tier and (not account.tier_id or new_tier.id != account.tier_id):
            account.tier_id = new_tier.id
            account.tier_achieved_date = datetime.utcnow()
            account.tier_expiry_date = datetime.utcnow() + timedelta(days=365)  # 1 year
            account.tier_status = LoyaltyTierStatus.ACTIVE

    async def _update_customer_segment(self, customer: Customer) -> None:
        """Update customer segment based on metrics"""
        # Simplified segmentation logic
        if customer.total_revenue > 10000:
            customer.segment = CustomerSegment.VIP
        elif customer.total_revenue > 5000:
            customer.segment = CustomerSegment.PREMIUM
        elif customer.total_revenue > 1000:
            customer.segment = CustomerSegment.STANDARD
        else:
            customer.segment = CustomerSegment.BASIC

    async def _get_customer_order_count(self, customer_id: uuid.UUID) -> Decimal:
        """Get customer's total order count"""
        # Placeholder - would query orders table in real implementation
        return Decimal("5")

    async def _get_customer_total_revenue(self, customer_id: uuid.UUID) -> Decimal:
        """Get customer's total revenue"""
        # Placeholder - would query orders table in real implementation
        return Decimal("2500.00")

    async def _get_customer_last_order_date(
        self, customer_id: uuid.UUID
    ) -> Optional[datetime]:
        """Get customer's last order date"""
        # Placeholder - would query orders table in real implementation
        return datetime.utcnow() - timedelta(days=30)

    async def _generate_rfm_analysis(self, customers: List[Customer]) -> Dict[str, Any]:
        """Generate RFM (Recency, Frequency, Monetary) analysis"""
        # Simplified RFM analysis
        segments = {
            "champions": 0,
            "loyal_customers": 0,
            "potential_loyalists": 0,
            "at_risk": 0,
            "lost": 0,
        }

        for customer in customers:
            # Simplified scoring based on metrics
            if customer.total_revenue > 5000 and customer.total_orders > 10:
                segments["champions"] += 1
            elif customer.total_revenue > 2000:
                segments["loyal_customers"] += 1
            elif customer.total_orders > 5:
                segments["potential_loyalists"] += 1
            elif (
                customer.last_order_date
                and customer.last_order_date < datetime.utcnow() - timedelta(days=180)
            ):
                segments["at_risk"] += 1
            else:
                segments["lost"] += 1

        return {
            "summary": {
                "total_analyzed": len(customers),
                "high_value_customers": segments["champions"]
                + segments["loyal_customers"],
                "at_risk_customers": segments["at_risk"] + segments["lost"],
            },
            "segments": segments,
            "recommendations": [
                "Focus retention efforts on 'Champions' and 'Loyal Customers'",
                "Create re-engagement campaigns for 'At Risk' customers",
                "Develop win-back campaigns for 'Lost' customers",
            ],
        }

    async def _generate_churn_analysis(
        self, customers: List[Customer]
    ) -> Dict[str, Any]:
        """Generate churn analysis"""
        # Simplified churn analysis
        high_churn_risk = 0
        medium_churn_risk = 0
        low_churn_risk = 0

        for customer in customers:
            # Simplified churn risk calculation
            if (
                customer.last_order_date
                and customer.last_order_date < datetime.utcnow() - timedelta(days=180)
            ):
                high_churn_risk += 1
            elif (
                customer.last_order_date
                and customer.last_order_date < datetime.utcnow() - timedelta(days=90)
            ):
                medium_churn_risk += 1
            else:
                low_churn_risk += 1

        return {
            "summary": {
                "total_analyzed": len(customers),
                "high_risk": high_churn_risk,
                "medium_risk": medium_churn_risk,
                "low_risk": low_churn_risk,
            },
            "segments": {
                "high_churn_risk": high_churn_risk,
                "medium_churn_risk": medium_churn_risk,
                "low_churn_risk": low_churn_risk,
            },
            "recommendations": [
                "Implement proactive retention campaigns for high-risk customers",
                "Monitor medium-risk customers closely",
                "Maintain engagement with low-risk customers",
            ],
        }

    async def _generate_ltv_analysis(self, customers: List[Customer]) -> Dict[str, Any]:
        """Generate lifetime value analysis"""
        # Simplified LTV analysis
        total_ltv = sum(customer.lifetime_value or 0 for customer in customers)
        avg_ltv = total_ltv / len(customers) if customers else 0

        ltv_segments = {"high": 0, "medium": 0, "low": 0}

        for customer in customers:
            ltv = customer.lifetime_value or 0
            if ltv > avg_ltv * 2:
                ltv_segments["high"] += 1
            elif ltv > avg_ltv:
                ltv_segments["medium"] += 1
            else:
                ltv_segments["low"] += 1

        return {
            "summary": {
                "total_analyzed": len(customers),
                "total_ltv": total_ltv,
                "average_ltv": avg_ltv,
            },
            "segments": ltv_segments,
            "recommendations": [
                "Focus on retaining high-LTV customers",
                "Develop upselling strategies for medium-LTV customers",
                "Create acquisition campaigns targeting high-value prospects",
            ],
        }

    async def _generate_segmentation_analysis(
        self, customers: List[Customer]
    ) -> Dict[str, Any]:
        """Generate customer segmentation analysis"""
        segments = {}
        for customer in customers:
            segment = customer.segment
            segments[segment] = segments.get(segment, 0) + 1

        return {
            "summary": {
                "total_analyzed": len(customers),
                "segments_count": len(segments),
            },
            "segments": segments,
            "recommendations": [
                "Tailor marketing messages by segment",
                "Develop segment-specific product offerings",
                "Optimize pricing strategies by segment",
            ],
        }


# API Router
router = APIRouter(prefix="/api/v1/customers", tags=["Customer Management v70"])


@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
) -> CustomerResponse:
    """Create new customer"""
    service = CustomerManagementService(db, redis_client)
    customer = await service.create_customer(customer_data)
    return CustomerResponse.from_orm(customer)


@router.get("/")
async def get_customers(
    status: Optional[CustomerStatus] = None,
    segment: Optional[CustomerSegment] = None,
    customer_type: Optional[CustomerType] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Get customers with filtering"""
    service = CustomerManagementService(db, redis_client)
    return await service.get_customers(
        status, segment, customer_type, search, skip, limit
    )


@router.put("/{customer_id}")
async def update_customer(
    customer_id: uuid.UUID,
    update_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Update customer information"""
    service = CustomerManagementService(db, redis_client)
    return await service.update_customer(customer_id, update_data)


@router.post("/tickets")
async def create_support_ticket(
    ticket_data: SupportTicketCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Create new support ticket"""
    service = CustomerManagementService(db, redis_client)
    return await service.create_support_ticket(ticket_data)


@router.put("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: uuid.UUID,
    status: TicketStatus,
    updated_by: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Update support ticket status"""
    service = CustomerManagementService(db, redis_client)
    return await service.update_ticket_status(ticket_id, status, updated_by, notes)


@router.post("/tickets/{ticket_id}/interactions")
async def add_ticket_interaction(
    ticket_id: uuid.UUID,
    interaction_data: TicketInteractionCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Add interaction to support ticket"""
    service = CustomerManagementService(db, redis_client)
    return await service.add_ticket_interaction(ticket_id, interaction_data)


@router.post("/loyalty/tiers")
async def create_loyalty_tier(
    tier_data: LoyaltyTierCreate,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Create new loyalty tier"""
    service = CustomerManagementService(db, redis_client)
    return await service.create_loyalty_tier(tier_data)


@router.post("/loyalty/transactions")
async def process_loyalty_transaction(
    transaction_data: LoyaltyTransactionRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Process loyalty points transaction"""
    service = CustomerManagementService(db, redis_client)
    return await service.process_loyalty_transaction(transaction_data)


@router.post("/analytics")
async def generate_customer_analytics(
    request: CustomerAnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(
        lambda: aioredis.from_url("redis://localhost:6379")
    ),
):
    """Generate customer analytics and insights"""
    service = CustomerManagementService(db, redis_client)
    return await service.generate_customer_analytics(request)


# Include router in main app
def get_router():
    """Get the customer management router"""
    return router
