"""
CC02 v55.0 Customer Management API
Enterprise-grade Customer Relationship Management System
Day 1 of 7-day intensive backend development
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.customer import (
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerCredit,
    CustomerGroup,
    CustomerInteraction,
)
from app.models.user import User

router = APIRouter(prefix="/customers", tags=["customers-v55"])


# Enums
class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    LEAD = "lead"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
    VIP = "vip"


class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    RESELLER = "reseller"


class ContactType(str, Enum):
    PRIMARY = "primary"
    BILLING = "billing"
    SHIPPING = "shipping"
    TECHNICAL = "technical"
    EMERGENCY = "emergency"
    OTHER = "other"


class AddressType(str, Enum):
    BILLING = "billing"
    SHIPPING = "shipping"
    OFFICE = "office"
    HOME = "home"
    OTHER = "other"


class InteractionType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    SUPPORT = "support"
    SALE = "sale"
    COMPLAINT = "complaint"
    FOLLOW_UP = "follow_up"
    QUOTE = "quote"
    OTHER = "other"


class CreditStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"


class PaymentTerms(str, Enum):
    NET_0 = "net_0"
    NET_15 = "net_15"
    NET_30 = "net_30"
    NET_45 = "net_45"
    NET_60 = "net_60"
    NET_90 = "net_90"
    COD = "cod"
    PREPAID = "prepaid"


# Request/Response Models
class CustomerContactCreate(BaseModel):
    contact_type: ContactType = Field(default=ContactType.PRIMARY)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    mobile: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    is_primary: bool = Field(default=False)
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(None, max_length=1000)


class CustomerContactResponse(BaseModel):
    id: UUID
    contact_type: ContactType
    first_name: str
    last_name: str
    full_name: str
    title: Optional[str]
    department: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    fax: Optional[str]
    is_primary: bool
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerAddressCreate(BaseModel):
    address_type: AddressType = Field(default=AddressType.BILLING)
    line1: str = Field(..., min_length=1, max_length=200)
    line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)
    is_primary: bool = Field(default=False)
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(None, max_length=500)


class CustomerAddressResponse(BaseModel):
    id: UUID
    address_type: AddressType
    line1: str
    line2: Optional[str]
    city: str
    state: Optional[str]
    postal_code: str
    country: str
    full_address: str
    is_primary: bool
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerCreditCreate(BaseModel):
    credit_limit: Decimal = Field(..., ge=0, decimal_places=2)
    payment_terms: PaymentTerms = Field(default=PaymentTerms.NET_30)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: CreditStatus = Field(default=CreditStatus.PENDING)
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)


class CustomerCreditResponse(BaseModel):
    id: UUID
    credit_limit: Decimal
    available_credit: Decimal
    used_credit: Decimal
    payment_terms: PaymentTerms
    currency: str
    status: CreditStatus
    approved_by: Optional[UUID]
    approved_by_name: Optional[str]
    approved_at: Optional[datetime]
    last_review_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    customer_number: Optional[str] = Field(None, max_length=50)
    company_name: Optional[str] = Field(None, max_length=200)
    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    status: CustomerStatus = Field(default=CustomerStatus.PROSPECT)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=0)
    annual_revenue: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    group_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    source: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=2000)
    contacts: List[CustomerContactCreate] = Field(default_factory=list, min_items=1)
    addresses: List[CustomerAddressCreate] = Field(default_factory=list)
    credit_info: Optional[CustomerCreditCreate] = None

    @validator("contacts")
    def validate_contacts(cls, v) -> dict:
        if not v:
            raise ValueError("At least one contact is required")

        # Check for multiple primary contacts
        primary_count = sum(1 for contact in v if contact.is_primary)
        if primary_count > 1:
            raise ValueError("Only one contact can be marked as primary")

        return v

    @validator("addresses")
    def validate_addresses(cls, v) -> dict:
        if not v:
            return v

        # Check for multiple primary addresses per type
        billing_primary = sum(
            1
            for addr in v
            if addr.address_type == AddressType.BILLING and addr.is_primary
        )
        shipping_primary = sum(
            1
            for addr in v
            if addr.address_type == AddressType.SHIPPING and addr.is_primary
        )

        if billing_primary > 1:
            raise ValueError("Only one billing address can be marked as primary")
        if shipping_primary > 1:
            raise ValueError("Only one shipping address can be marked as primary")

        return v


class CustomerUpdate(BaseModel):
    customer_number: Optional[str] = Field(None, max_length=50)
    company_name: Optional[str] = Field(None, max_length=200)
    customer_type: Optional[CustomerType] = None
    status: Optional[CustomerStatus] = None
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=0)
    annual_revenue: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    group_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    source: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=2000)


class CustomerResponse(BaseModel):
    id: UUID
    customer_number: str
    company_name: Optional[str]
    customer_type: CustomerType
    status: CustomerStatus
    website: Optional[str]
    industry: Optional[str]
    employee_count: Optional[int]
    annual_revenue: Optional[Decimal]
    currency: str
    tax_id: Optional[str]
    registration_number: Optional[str]
    group_id: Optional[UUID]
    group_name: Optional[str]
    assigned_to: Optional[UUID]
    assigned_to_name: Optional[str]
    source: Optional[str]
    tags: List[str]
    notes: Optional[str]
    contacts: List[CustomerContactResponse]
    addresses: List[CustomerAddressResponse]
    credit_info: Optional[CustomerCreditResponse]
    total_orders: int
    total_spent: Decimal
    average_order_value: Decimal
    last_order_date: Optional[datetime]
    last_interaction_date: Optional[datetime]
    lifetime_value: Decimal
    acquisition_date: date
    days_as_customer: int
    risk_score: Optional[float]
    satisfaction_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    id: UUID
    customer_number: str
    company_name: Optional[str]
    primary_contact_name: str
    primary_contact_email: Optional[str]
    customer_type: CustomerType
    status: CustomerStatus
    industry: Optional[str]
    total_orders: int
    total_spent: Decimal
    last_order_date: Optional[datetime]
    assigned_to_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerInteractionCreate(BaseModel):
    interaction_type: InteractionType = Field(default=InteractionType.OTHER)
    subject: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    contact_id: Optional[UUID] = None
    interaction_date: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: Optional[int] = Field(None, ge=0)
    outcome: Optional[str] = Field(None, max_length=500)
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[datetime] = None
    attachments: List[str] = Field(default_factory=list)


class CustomerInteractionResponse(BaseModel):
    id: UUID
    customer_id: UUID
    interaction_type: InteractionType
    subject: str
    description: Optional[str]
    contact_id: Optional[UUID]
    contact_name: Optional[str]
    interaction_date: datetime
    duration_minutes: Optional[int]
    outcome: Optional[str]
    follow_up_required: bool
    follow_up_date: Optional[datetime]
    attachments: List[str]
    created_by: UUID
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    credit_terms: Optional[PaymentTerms] = None
    is_active: bool = Field(default=True)


class CustomerGroupResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    discount_percentage: Optional[Decimal]
    credit_terms: Optional[PaymentTerms]
    is_active: bool
    customer_count: int
    total_revenue: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: Optional[Dict[str, Any]] = None
    include_inactive: bool = Field(default=False)
    sort_by: Optional[str] = Field(
        None, regex="^(name|company|created_at|total_spent|last_order)$"
    )
    sort_order: Optional[str] = Field(None, regex="^(asc|desc)$")


# Helper Functions
async def generate_customer_number(db: AsyncSession, prefix: str = "CUST") -> str:
    """Generate unique customer number"""
    # Get the highest existing customer number
    result = await db.execute(
        select(func.max(Customer.customer_number)).where(
            Customer.customer_number.like(f"{prefix}%")
        )
    )

    max_number = result.scalar()

    if max_number:
        # Extract numeric part and increment
        try:
            numeric_part = int(max_number.replace(prefix, ""))
            new_number = numeric_part + 1
        except ValueError:
            new_number = 1
    else:
        new_number = 1

    return f"{prefix}{new_number:06d}"


async def validate_customer_group_exists(db: AsyncSession, group_id: UUID) -> bool:
    """Validate that a customer group exists"""
    result = await db.execute(select(CustomerGroup).where(CustomerGroup.id == group_id))
    return result.scalar_one_or_none() is not None


async def calculate_customer_metrics(
    db: AsyncSession, customer_id: UUID
) -> Dict[str, Any]:
    """Calculate various customer metrics"""
    # This would typically join with orders table
    # For now, returning placeholder values
    return {
        "total_orders": 0,
        "total_spent": Decimal("0"),
        "average_order_value": Decimal("0"),
        "last_order_date": None,
        "lifetime_value": Decimal("0"),
    }


async def calculate_risk_score(customer: Customer) -> float:
    """Calculate customer risk score based on various factors"""
    score = 50.0  # Base score

    # Adjust based on status
    if customer.status == CustomerStatus.VIP:
        score -= 20
    elif customer.status == CustomerStatus.BLOCKED:
        score += 30
    elif customer.status == CustomerStatus.SUSPENDED:
        score += 20

    # Adjust based on customer type
    if customer.customer_type == CustomerType.ENTERPRISE:
        score -= 10
    elif customer.customer_type == CustomerType.INDIVIDUAL:
        score += 5

    # Keep score within bounds
    return max(0.0, min(100.0, score))


# Customer Group Endpoints
@router.post(
    "/groups", response_model=CustomerGroupResponse, status_code=status.HTTP_201_CREATED
)
async def create_customer_group(
    group: CustomerGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new customer group"""

    # Check name uniqueness
    existing = await db.execute(
        select(CustomerGroup).where(CustomerGroup.name == group.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer group name already exists",
        )

    # Create group
    db_group = CustomerGroup(
        id=uuid4(),
        name=group.name,
        description=group.description,
        discount_percentage=group.discount_percentage,
        credit_terms=group.credit_terms,
        is_active=group.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)

    # Add computed fields
    db_group.customer_count = 0
    db_group.total_revenue = Decimal("0")

    return db_group


@router.get("/groups", response_model=List[CustomerGroupResponse])
async def list_customer_groups(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    include_stats: bool = Query(True, description="Include customer statistics"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of customer groups"""

    query = select(CustomerGroup)

    if is_active is not None:
        query = query.where(CustomerGroup.is_active == is_active)

    query = query.order_by(CustomerGroup.name)

    result = await db.execute(query)
    groups = result.scalars().all()

    # Add computed fields
    for group in groups:
        if include_stats:
            # Count customers in group
            customer_count = await db.execute(
                select(func.count(Customer.id)).where(Customer.group_id == group.id)
            )
            group.customer_count = customer_count.scalar() or 0

            # Calculate total revenue (would need orders table)
            group.total_revenue = Decimal("0")
        else:
            group.customer_count = 0
            group.total_revenue = Decimal("0")

    return groups


# Customer Endpoints
@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new customer with contacts and addresses"""

    # Validate customer group exists if specified
    if customer.group_id:
        if not await validate_customer_group_exists(db, customer.group_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer group not found"
            )

    # Generate customer number if not provided
    customer_number = customer.customer_number
    if not customer_number:
        customer_number = await generate_customer_number(db)
    else:
        # Check uniqueness
        existing = await db.execute(
            select(Customer).where(Customer.customer_number == customer_number)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer number already exists",
            )

    # Set primary contact if none specified
    if customer.contacts and not any(c.is_primary for c in customer.contacts):
        customer.contacts[0].is_primary = True

    # Set primary addresses if none specified
    billing_addresses = [
        a for a in customer.addresses if a.address_type == AddressType.BILLING
    ]
    if billing_addresses and not any(a.is_primary for a in billing_addresses):
        billing_addresses[0].is_primary = True

    shipping_addresses = [
        a for a in customer.addresses if a.address_type == AddressType.SHIPPING
    ]
    if shipping_addresses and not any(a.is_primary for a in shipping_addresses):
        shipping_addresses[0].is_primary = True

    # Create customer
    db_customer = Customer(
        id=uuid4(),
        customer_number=customer_number,
        company_name=customer.company_name,
        customer_type=customer.customer_type,
        status=customer.status,
        website=customer.website,
        industry=customer.industry,
        employee_count=customer.employee_count,
        annual_revenue=customer.annual_revenue,
        currency=customer.currency,
        tax_id=customer.tax_id,
        registration_number=customer.registration_number,
        group_id=customer.group_id,
        assigned_to=customer.assigned_to,
        source=customer.source,
        tags=customer.tags,
        notes=customer.notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_customer)
    await db.flush()  # Get the customer ID

    # Create contacts
    for contact_data in customer.contacts:
        db_contact = CustomerContact(
            id=uuid4(),
            customer_id=db_customer.id,
            contact_type=contact_data.contact_type,
            first_name=contact_data.first_name,
            last_name=contact_data.last_name,
            title=contact_data.title,
            department=contact_data.department,
            email=contact_data.email,
            phone=contact_data.phone,
            mobile=contact_data.mobile,
            fax=contact_data.fax,
            is_primary=contact_data.is_primary,
            is_active=contact_data.is_active,
            notes=contact_data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(db_contact)

    # Create addresses
    for address_data in customer.addresses:
        db_address = CustomerAddress(
            id=uuid4(),
            customer_id=db_customer.id,
            address_type=address_data.address_type,
            line1=address_data.line1,
            line2=address_data.line2,
            city=address_data.city,
            state=address_data.state,
            postal_code=address_data.postal_code,
            country=address_data.country,
            is_primary=address_data.is_primary,
            is_active=address_data.is_active,
            notes=address_data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(db_address)

    # Create credit info if provided
    if customer.credit_info:
        db_credit = CustomerCredit(
            id=uuid4(),
            customer_id=db_customer.id,
            credit_limit=customer.credit_info.credit_limit,
            payment_terms=customer.credit_info.payment_terms,
            currency=customer.credit_info.currency,
            status=customer.credit_info.status,
            approved_by=customer.credit_info.approved_by,
            approved_at=customer.credit_info.approved_at,
            notes=customer.credit_info.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(db_credit)

    await db.commit()

    # Return complete customer
    return await get_customer(db_customer.id, db)


@router.get("/", response_model=List[CustomerListResponse])
async def list_customers(
    skip: int = Query(0, ge=0, description="Number of customers to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of customers to return"),
    status: Optional[CustomerStatus] = Query(None, description="Filter by status"),
    customer_type: Optional[CustomerType] = Query(None, description="Filter by type"),
    group_id: Optional[UUID] = Query(None, description="Filter by customer group"),
    assigned_to: Optional[UUID] = Query(None, description="Filter by assigned user"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    search: Optional[str] = Query(
        None, min_length=1, description="Search in name, company, or email"
    ),
    sort_by: str = Query(
        "created_at", regex="^(name|company|created_at|total_spent|last_order)$"
    ),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of customers with filtering and pagination"""

    # Build query with joins for optimization
    query = select(Customer).options(
        selectinload(Customer.contacts), joinedload(Customer.group)
    )

    # Apply filters
    if status:
        query = query.where(Customer.status == status)

    if customer_type:
        query = query.where(Customer.customer_type == customer_type)

    if group_id:
        query = query.where(Customer.group_id == group_id)

    if assigned_to:
        query = query.where(Customer.assigned_to == assigned_to)

    if industry:
        query = query.where(Customer.industry.ilike(f"%{industry}%"))

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Customer.company_name.ilike(search_term),
                Customer.customer_number.ilike(search_term),
                # Note: Would need to join with contacts for email/name search in production
            )
        )

    # Apply sorting
    if sort_by == "name":
        order_column = Customer.company_name
    elif sort_by == "company":
        order_column = Customer.company_name
    elif sort_by == "total_spent":
        # Would need to join with orders in production
        order_column = Customer.created_at
    elif sort_by == "last_order":
        # Would need to join with orders in production
        order_column = Customer.updated_at
    else:
        order_column = Customer.created_at

    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    customers = result.unique().scalars().all()

    # Build response list
    response_list = []
    for customer in customers:
        # Get primary contact
        primary_contact = next((c for c in customer.contacts if c.is_primary), None)
        if not primary_contact and customer.contacts:
            primary_contact = customer.contacts[0]

        # Calculate metrics (simplified for now)
        metrics = await calculate_customer_metrics(db, customer.id)

        response_item = CustomerListResponse(
            id=customer.id,
            customer_number=customer.customer_number,
            company_name=customer.company_name,
            primary_contact_name=f"{primary_contact.first_name} {primary_contact.last_name}"
            if primary_contact
            else "N/A",
            primary_contact_email=primary_contact.email if primary_contact else None,
            customer_type=customer.customer_type,
            status=customer.status,
            industry=customer.industry,
            total_orders=metrics["total_orders"],
            total_spent=metrics["total_spent"],
            last_order_date=metrics["last_order_date"],
            assigned_to_name=None,  # TODO: Fetch from user table
            created_at=customer.created_at,
        )
        response_list.append(response_item)

    return response_list


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID = Path(..., description="Customer ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific customer with all details"""

    result = await db.execute(
        select(Customer)
        .options(
            selectinload(Customer.contacts),
            selectinload(Customer.addresses),
            selectinload(Customer.credit_info),
            joinedload(Customer.group),
        )
        .where(Customer.id == customer_id)
    )

    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    # Build contact responses
    contact_responses = []
    for contact in customer.contacts:
        contact_response = CustomerContactResponse(
            id=contact.id,
            contact_type=contact.contact_type,
            first_name=contact.first_name,
            last_name=contact.last_name,
            full_name=f"{contact.first_name} {contact.last_name}",
            title=contact.title,
            department=contact.department,
            email=contact.email,
            phone=contact.phone,
            mobile=contact.mobile,
            fax=contact.fax,
            is_primary=contact.is_primary,
            is_active=contact.is_active,
            notes=contact.notes,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )
        contact_responses.append(contact_response)

    # Build address responses
    address_responses = []
    for address in customer.addresses:
        full_address = f"{address.line1}"
        if address.line2:
            full_address += f", {address.line2}"
        full_address += f", {address.city}"
        if address.state:
            full_address += f", {address.state}"
        full_address += f" {address.postal_code}, {address.country}"

        address_response = CustomerAddressResponse(
            id=address.id,
            address_type=address.address_type,
            line1=address.line1,
            line2=address.line2,
            city=address.city,
            state=address.state,
            postal_code=address.postal_code,
            country=address.country,
            full_address=full_address,
            is_primary=address.is_primary,
            is_active=address.is_active,
            notes=address.notes,
            created_at=address.created_at,
            updated_at=address.updated_at,
        )
        address_responses.append(address_response)

    # Build credit response
    credit_response = None
    if customer.credit_info:
        credit = customer.credit_info
        available_credit = (
            credit.credit_limit
        )  # Would calculate actual available credit in production
        used_credit = Decimal("0")  # Would calculate from orders in production

        credit_response = CustomerCreditResponse(
            id=credit.id,
            credit_limit=credit.credit_limit,
            available_credit=available_credit,
            used_credit=used_credit,
            payment_terms=credit.payment_terms,
            currency=credit.currency,
            status=credit.status,
            approved_by=credit.approved_by,
            approved_by_name=None,  # TODO: Fetch from user table
            approved_at=credit.approved_at,
            last_review_date=None,  # TODO: Calculate from review history
            notes=credit.notes,
            created_at=credit.created_at,
            updated_at=credit.updated_at,
        )

    # Calculate metrics and scores
    metrics = await calculate_customer_metrics(db, customer.id)
    risk_score = await calculate_risk_score(customer)

    # Calculate days as customer
    days_as_customer = (datetime.utcnow().date() - customer.created_at.date()).days

    return CustomerResponse(
        id=customer.id,
        customer_number=customer.customer_number,
        company_name=customer.company_name,
        customer_type=customer.customer_type,
        status=customer.status,
        website=customer.website,
        industry=customer.industry,
        employee_count=customer.employee_count,
        annual_revenue=customer.annual_revenue,
        currency=customer.currency,
        tax_id=customer.tax_id,
        registration_number=customer.registration_number,
        group_id=customer.group_id,
        group_name=customer.group.name if customer.group else None,
        assigned_to=customer.assigned_to,
        assigned_to_name=None,  # TODO: Fetch from user table
        source=customer.source,
        tags=customer.tags,
        notes=customer.notes,
        contacts=contact_responses,
        addresses=address_responses,
        credit_info=credit_response,
        total_orders=metrics["total_orders"],
        total_spent=metrics["total_spent"],
        average_order_value=metrics["average_order_value"],
        last_order_date=metrics["last_order_date"],
        last_interaction_date=None,  # TODO: Calculate from interactions
        lifetime_value=metrics["lifetime_value"],
        acquisition_date=customer.created_at.date(),
        days_as_customer=days_as_customer,
        risk_score=risk_score,
        satisfaction_score=None,  # TODO: Calculate from surveys/feedback
        created_at=customer.created_at,
        updated_at=customer.updated_at,
    )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID = Path(..., description="Customer ID"),
    customer_update: CustomerUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a customer"""

    # Get existing customer
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    db_customer = result.scalar_one_or_none()

    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    # Validate customer group exists if specified
    if customer_update.group_id:
        if not await validate_customer_group_exists(db, customer_update.group_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer group not found"
            )

    # Check customer number uniqueness if changed
    if (
        customer_update.customer_number
        and customer_update.customer_number != db_customer.customer_number
    ):
        existing = await db.execute(
            select(Customer).where(
                and_(
                    Customer.customer_number == customer_update.customer_number,
                    Customer.id != customer_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer number already exists",
            )

    # Update fields
    for field, value in customer_update.dict(exclude_unset=True).items():
        setattr(db_customer, field, value)

    db_customer.updated_at = datetime.utcnow()

    await db.commit()

    # Return updated customer
    return await get_customer(customer_id, db)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID = Path(..., description="Customer ID"),
    force: bool = Query(False, description="Force delete even if orders exist"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a customer and all related records"""

    # Check if customer exists
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    # Check for orders unless force delete (would need orders table in production)
    if not force:
        # TODO: Check for existing orders
        pass

    # Delete related records
    await db.execute(
        delete(CustomerContact).where(CustomerContact.customer_id == customer_id)
    )
    await db.execute(
        delete(CustomerAddress).where(CustomerAddress.customer_id == customer_id)
    )
    await db.execute(
        delete(CustomerCredit).where(CustomerCredit.customer_id == customer_id)
    )
    await db.execute(
        delete(CustomerInteraction).where(
            CustomerInteraction.customer_id == customer_id
        )
    )
    await db.execute(delete(Customer).where(Customer.id == customer_id))

    await db.commit()


# Customer Interactions
@router.post(
    "/{customer_id}/interactions",
    response_model=CustomerInteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_interaction(
    customer_id: UUID = Path(..., description="Customer ID"),
    interaction: CustomerInteractionCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new customer interaction"""

    # Validate customer exists
    customer_result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    # Validate contact exists if specified
    if interaction.contact_id:
        contact_result = await db.execute(
            select(CustomerContact).where(
                and_(
                    CustomerContact.id == interaction.contact_id,
                    CustomerContact.customer_id == customer_id,
                )
            )
        )
        if not contact_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found for this customer",
            )

    # Create interaction
    db_interaction = CustomerInteraction(
        id=uuid4(),
        customer_id=customer_id,
        interaction_type=interaction.interaction_type,
        subject=interaction.subject,
        description=interaction.description,
        contact_id=interaction.contact_id,
        interaction_date=interaction.interaction_date,
        duration_minutes=interaction.duration_minutes,
        outcome=interaction.outcome,
        follow_up_required=interaction.follow_up_required,
        follow_up_date=interaction.follow_up_date,
        attachments=interaction.attachments,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_interaction)
    await db.commit()
    await db.refresh(db_interaction)

    return CustomerInteractionResponse(
        id=db_interaction.id,
        customer_id=db_interaction.customer_id,
        interaction_type=db_interaction.interaction_type,
        subject=db_interaction.subject,
        description=db_interaction.description,
        contact_id=db_interaction.contact_id,
        contact_name=None,  # TODO: Fetch contact name
        interaction_date=db_interaction.interaction_date,
        duration_minutes=db_interaction.duration_minutes,
        outcome=db_interaction.outcome,
        follow_up_required=db_interaction.follow_up_required,
        follow_up_date=db_interaction.follow_up_date,
        attachments=db_interaction.attachments,
        created_by=db_interaction.created_by,
        created_by_name=current_user.full_name or current_user.email,
        created_at=db_interaction.created_at,
        updated_at=db_interaction.updated_at,
    )


@router.get(
    "/{customer_id}/interactions", response_model=List[CustomerInteractionResponse]
)
async def list_customer_interactions(
    customer_id: UUID = Path(..., description="Customer ID"),
    interaction_type: Optional[InteractionType] = Query(
        None, description="Filter by interaction type"
    ),
    start_date: Optional[date] = Query(
        None, description="Filter interactions after this date"
    ),
    end_date: Optional[date] = Query(
        None, description="Filter interactions before this date"
    ),
    limit: int = Query(
        50, ge=1, le=200, description="Number of interactions to return"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Get customer interactions with filtering"""

    # Validate customer exists
    customer_result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    if not customer_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    # Build query
    query = select(CustomerInteraction).where(
        CustomerInteraction.customer_id == customer_id
    )

    if interaction_type:
        query = query.where(CustomerInteraction.interaction_type == interaction_type)

    if start_date:
        query = query.where(CustomerInteraction.interaction_date >= start_date)

    if end_date:
        query = query.where(CustomerInteraction.interaction_date <= end_date)

    query = query.order_by(CustomerInteraction.interaction_date.desc()).limit(limit)

    result = await db.execute(query)
    interactions = result.scalars().all()

    # Build response
    response_list = []
    for interaction in interactions:
        response_item = CustomerInteractionResponse(
            id=interaction.id,
            customer_id=interaction.customer_id,
            interaction_type=interaction.interaction_type,
            subject=interaction.subject,
            description=interaction.description,
            contact_id=interaction.contact_id,
            contact_name=None,  # TODO: Fetch contact name
            interaction_date=interaction.interaction_date,
            duration_minutes=interaction.duration_minutes,
            outcome=interaction.outcome,
            follow_up_required=interaction.follow_up_required,
            follow_up_date=interaction.follow_up_date,
            attachments=interaction.attachments,
            created_by=interaction.created_by,
            created_by_name="Unknown",  # TODO: Fetch user name
            created_at=interaction.created_at,
            updated_at=interaction.updated_at,
        )
        response_list.append(response_item)

    return response_list


# Analytics and Search
@router.post("/search", response_model=List[CustomerListResponse])
async def search_customers(
    search_request: CustomerSearchRequest = Body(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Advanced customer search with filters"""

    # Build base query
    query = select(Customer).options(selectinload(Customer.contacts))

    # Apply search
    search_term = f"%{search_request.query}%"
    query = query.where(
        or_(
            Customer.company_name.ilike(search_term),
            Customer.customer_number.ilike(search_term),
            Customer.tax_id.ilike(search_term),
        )
    )

    # Apply additional filters
    if search_request.filters:
        for key, value in search_request.filters.items():
            if key == "status" and value:
                query = query.where(Customer.status == value)
            elif key == "customer_type" and value:
                query = query.where(Customer.customer_type == value)
            elif key == "industry" and value:
                query = query.where(Customer.industry.ilike(f"%{value}%"))

    # Include inactive customers if requested
    if not search_request.include_inactive:
        query = query.where(Customer.status != CustomerStatus.INACTIVE)

    # Apply sorting
    if search_request.sort_by:
        sort_column = getattr(Customer, search_request.sort_by, Customer.created_at)
        if search_request.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(Customer.created_at.desc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    customers = result.unique().scalars().all()

    # Build response (simplified)
    response_list = []
    for customer in customers:
        primary_contact = next((c for c in customer.contacts if c.is_primary), None)
        if not primary_contact and customer.contacts:
            primary_contact = customer.contacts[0]

        response_item = CustomerListResponse(
            id=customer.id,
            customer_number=customer.customer_number,
            company_name=customer.company_name,
            primary_contact_name=f"{primary_contact.first_name} {primary_contact.last_name}"
            if primary_contact
            else "N/A",
            primary_contact_email=primary_contact.email if primary_contact else None,
            customer_type=customer.customer_type,
            status=customer.status,
            industry=customer.industry,
            total_orders=0,  # TODO: Calculate from orders
            total_spent=Decimal("0"),  # TODO: Calculate from orders
            last_order_date=None,  # TODO: Calculate from orders
            assigned_to_name=None,  # TODO: Fetch from user table
            created_at=customer.created_at,
        )
        response_list.append(response_item)

    return response_list


@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_customer_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    group_id: Optional[UUID] = Query(None, description="Filter by customer group"),
    db: AsyncSession = Depends(get_db),
):
    """Get customer analytics and statistics"""

    # Base query filters
    base_filters = []
    if start_date:
        base_filters.append(Customer.created_at >= start_date)
    if end_date:
        base_filters.append(Customer.created_at <= end_date)
    if group_id:
        base_filters.append(Customer.group_id == group_id)

    # Total customers
    total_query = select(func.count(Customer.id))
    for filter_clause in base_filters:
        total_query = total_query.where(filter_clause)

    total_result = await db.execute(total_query)
    total_customers = total_result.scalar()

    # Customers by status
    status_query = select(Customer.status, func.count(Customer.id))
    for filter_clause in base_filters:
        status_query = status_query.where(filter_clause)
    status_query = status_query.group_by(Customer.status)

    status_result = await db.execute(status_query)
    status_counts = {status: count for status, count in status_result.fetchall()}

    # Customers by type
    type_query = select(Customer.customer_type, func.count(Customer.id))
    for filter_clause in base_filters:
        type_query = type_query.where(filter_clause)
    type_query = type_query.group_by(Customer.customer_type)

    type_result = await db.execute(type_query)
    type_counts = {ctype: count for ctype, count in type_result.fetchall()}

    # Top industries
    industry_query = select(Customer.industry, func.count(Customer.id))
    for filter_clause in base_filters:
        industry_query = industry_query.where(filter_clause)
    industry_query = (
        industry_query.where(Customer.industry.isnot(None))
        .group_by(Customer.industry)
        .order_by(func.count(Customer.id).desc())
        .limit(10)
    )

    industry_result = await db.execute(industry_query)
    top_industries = [
        {"name": industry, "count": count}
        for industry, count in industry_result.fetchall()
    ]

    # New customers trend (last 12 months)
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    trend_query = select(
        func.date_trunc("month", Customer.created_at).label("month"),
        func.count(Customer.id).label("count"),
    ).where(Customer.created_at >= twelve_months_ago)

    for filter_clause in base_filters:
        if "created_at" not in str(filter_clause):  # Avoid duplicate date filters
            trend_query = trend_query.where(filter_clause)

    trend_query = trend_query.group_by("month").order_by("month")

    trend_result = await db.execute(trend_query)
    customer_trend = [
        {"month": month.strftime("%Y-%m"), "count": count}
        for month, count in trend_result.fetchall()
    ]

    return {
        "total_customers": total_customers,
        "customers_by_status": status_counts,
        "customers_by_type": type_counts,
        "top_industries": top_industries,
        "new_customers_trend": customer_trend,
        "vip_customers": status_counts.get(CustomerStatus.VIP, 0),
        "blocked_customers": status_counts.get(CustomerStatus.BLOCKED, 0),
        "analytics_period": {
            "start_date": start_date,
            "end_date": end_date,
            "group_id": group_id,
        },
    }
