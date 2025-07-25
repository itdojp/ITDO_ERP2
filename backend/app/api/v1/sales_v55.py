"""
CC02 v55.0 Sales Management API
Enterprise-grade Sales Analytics and Performance Management System
Day 1 of 7-day intensive backend development - Final API
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.order import Order, OrderItem
from app.models.sales import (
    SalesActivity,
    SalesForecast,
    SalesLead,
    SalesOpportunity,
    SalesTarget,
)
from app.models.user import User

router = APIRouter(prefix="/sales", tags=["sales-v55"])


# Enums
class SalesStage(str, Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    WON = "won"
    LOST = "lost"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    NURTURING = "nurturing"
    CONVERTED = "converted"
    LOST = "lost"


class OpportunityStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    ON_HOLD = "on_hold"


class SalesActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    DEMO = "demo"
    PROPOSAL = "proposal"
    FOLLOW_UP = "follow_up"
    NEGOTIATION = "negotiation"
    CONTRACT = "contract"


class ForecastType(str, Enum):
    CONSERVATIVE = "conservative"
    REALISTIC = "realistic"
    OPTIMISTIC = "optimistic"
    PIPELINE = "pipeline"


class CommissionType(str, Enum):
    PERCENTAGE = "percentage"
    FLAT_RATE = "flat_rate"
    TIERED = "tiered"
    BONUS = "bonus"


class SalesMetricType(str, Enum):
    REVENUE = "revenue"
    UNITS_SOLD = "units_sold"
    CONVERSION_RATE = "conversion_rate"
    AVERAGE_DEAL_SIZE = "average_deal_size"
    SALES_CYCLE_LENGTH = "sales_cycle_length"
    CUSTOMER_ACQUISITION_COST = "customer_acquisition_cost"
    LIFETIME_VALUE = "lifetime_value"


class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


# Request/Response Models
class SalesLeadCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    lead_source: str = Field(..., min_length=1, max_length=100)
    territory_id: Optional[UUID] = None
    estimated_value: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    estimated_close_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)


class SalesLeadResponse(BaseModel):
    id: UUID
    lead_number: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    industry: Optional[str]
    lead_source: str
    status: LeadStatus
    score: int
    territory_id: Optional[UUID]
    territory_name: Optional[str]
    estimated_value: Optional[Decimal]
    estimated_close_date: Optional[date]
    last_contact_date: Optional[datetime]
    next_follow_up: Optional[datetime]
    conversion_probability: int
    notes: Optional[str]
    tags: List[str]
    assigned_to: Optional[UUID]
    assigned_to_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesOpportunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    customer_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    stage: SalesStage = Field(default=SalesStage.PROSPECTING)
    probability: int = Field(default=10, ge=0, le=100)
    estimated_value: Decimal = Field(..., ge=0, decimal_places=2)
    estimated_close_date: date
    territory_id: Optional[UUID] = None
    product_ids: List[UUID] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)


class SalesOpportunityResponse(BaseModel):
    id: UUID
    opportunity_number: str
    name: str
    customer_id: Optional[UUID]
    customer_name: Optional[str]
    lead_id: Optional[UUID]
    lead_name: Optional[str]
    stage: SalesStage
    status: OpportunityStatus
    probability: int
    estimated_value: Decimal
    weighted_value: Decimal
    actual_value: Optional[Decimal]
    estimated_close_date: date
    actual_close_date: Optional[date]
    days_in_stage: int
    total_sales_cycle_days: Optional[int]
    territory_id: Optional[UUID]
    territory_name: Optional[str]
    products: List[Dict[str, Any]]
    description: Optional[str]
    notes: Optional[str]
    next_activity: Optional[Dict[str, Any]]
    assigned_to: UUID
    assigned_to_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesActivityCreate(BaseModel):
    opportunity_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    activity_type: SalesActivityType
    subject: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    scheduled_date: datetime
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    location: Optional[str] = Field(None, max_length=200)
    attendees: List[str] = Field(default_factory=list)
    outcome: Optional[str] = Field(None, max_length=500)
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[datetime] = None


class SalesActivityResponse(BaseModel):
    id: UUID
    opportunity_id: Optional[UUID]
    opportunity_name: Optional[str]
    lead_id: Optional[UUID]
    lead_name: Optional[str]
    customer_id: Optional[UUID]
    customer_name: Optional[str]
    activity_type: SalesActivityType
    subject: str
    description: Optional[str]
    status: str
    scheduled_date: datetime
    completed_date: Optional[datetime]
    duration_minutes: Optional[int]
    location: Optional[str]
    attendees: List[str]
    outcome: Optional[str]
    follow_up_required: bool
    follow_up_date: Optional[datetime]
    created_by: UUID
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesTargetCreate(BaseModel):
    target_type: str = Field(..., regex="^(revenue|units|deals)$")
    period_type: str = Field(..., regex="^(monthly|quarterly|yearly)$")
    period_start: date
    period_end: date
    target_value: Decimal = Field(..., ge=0, decimal_places=2)
    territory_id: Optional[UUID] = None
    product_category_id: Optional[UUID] = None
    description: Optional[str] = Field(None, max_length=500)


class SalesTargetResponse(BaseModel):
    id: UUID
    target_type: str
    period_type: str
    period_start: date
    period_end: date
    target_value: Decimal
    achieved_value: Decimal
    achievement_percentage: Decimal
    territory_id: Optional[UUID]
    territory_name: Optional[str]
    product_category_id: Optional[UUID]
    product_category_name: Optional[str]
    description: Optional[str]
    status: str
    assigned_to: UUID
    assigned_to_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SalesForecastCreate(BaseModel):
    period_start: date
    period_end: date
    forecast_type: ForecastType = Field(default=ForecastType.REALISTIC)
    territory_id: Optional[UUID] = None
    product_category_id: Optional[UUID] = None
    revenue_forecast: Decimal = Field(..., ge=0, decimal_places=2)
    units_forecast: Optional[int] = Field(None, ge=0)
    deals_forecast: Optional[int] = Field(None, ge=0)
    confidence_level: int = Field(default=50, ge=0, le=100)
    assumptions: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)


class SalesForecastResponse(BaseModel):
    id: UUID
    period_start: date
    period_end: date
    forecast_type: ForecastType
    territory_id: Optional[UUID]
    territory_name: Optional[str]
    product_category_id: Optional[UUID]
    product_category_name: Optional[str]
    revenue_forecast: Decimal
    units_forecast: Optional[int]
    deals_forecast: Optional[int]
    actual_revenue: Optional[Decimal]
    actual_units: Optional[int]
    actual_deals: Optional[int]
    accuracy_percentage: Optional[Decimal]
    confidence_level: int
    assumptions: Optional[str]
    notes: Optional[str]
    created_by: UUID
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Helper Functions
async def generate_lead_number(db: AsyncSession, prefix: str = "LEAD") -> str:
    """Generate unique lead number"""
    today = datetime.utcnow().strftime("%Y%m%d")
    full_prefix = f"{prefix}{today}"

    result = await db.execute(
        select(func.max(SalesLead.lead_number)).where(
            SalesLead.lead_number.like(f"{full_prefix}%")
        )
    )

    max_number = result.scalar()

    if max_number:
        try:
            sequence = int(max_number.replace(full_prefix, ""))
            new_sequence = sequence + 1
        except ValueError:
            new_sequence = 1
    else:
        new_sequence = 1

    return f"{full_prefix}{new_sequence:04d}"


async def generate_opportunity_number(db: AsyncSession, prefix: str = "OPP") -> str:
    """Generate unique opportunity number"""
    today = datetime.utcnow().strftime("%Y%m%d")
    full_prefix = f"{prefix}{today}"

    result = await db.execute(
        select(func.max(SalesOpportunity.opportunity_number)).where(
            SalesOpportunity.opportunity_number.like(f"{full_prefix}%")
        )
    )

    max_number = result.scalar()

    if max_number:
        try:
            sequence = int(max_number.replace(full_prefix, ""))
            new_sequence = sequence + 1
        except ValueError:
            new_sequence = 1
    else:
        new_sequence = 1

    return f"{full_prefix}{new_sequence:04d}"


async def calculate_lead_score(lead: SalesLead) -> int:
    """Calculate lead scoring based on various factors"""
    score = 0

    # Company size factor
    if lead.company:
        score += 10

    # Industry factor
    if lead.industry:
        score += 5

    # Contact information completeness
    if lead.phone:
        score += 10
    if lead.email:
        score += 15

    # Engagement factors
    if lead.last_contact_date:
        days_since_contact = (datetime.utcnow() - lead.last_contact_date).days
        if days_since_contact <= 7:
            score += 20
        elif days_since_contact <= 30:
            score += 10

    # Estimated value factor
    if lead.estimated_value:
        if lead.estimated_value >= 100000:
            score += 25
        elif lead.estimated_value >= 50000:
            score += 15
        elif lead.estimated_value >= 10000:
            score += 10

    return min(score, 100)


async def update_opportunity_weighted_value(opportunity: SalesOpportunity) -> Decimal:
    """Calculate weighted value based on probability"""
    return opportunity.estimated_value * (Decimal(opportunity.probability) / 100)


async def calculate_sales_metrics(
    db: AsyncSession,
    period_start: date,
    period_end: date,
    territory_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Calculate sales metrics for a given period"""

    # Base filters
    filters = [
        Order.created_at >= period_start,
        Order.created_at <= period_end,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ]

    if territory_id:
        # Would need to join with sales territory data
        pass

    # Total revenue
    revenue_result = await db.execute(
        select(func.sum(Order.total_amount)).where(and_(*filters))
    )
    total_revenue = revenue_result.scalar() or Decimal("0")

    # Total orders
    orders_result = await db.execute(select(func.count(Order.id)).where(and_(*filters)))
    total_orders = orders_result.scalar() or 0

    # Average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal("0")

    # Total units sold
    units_result = await db.execute(
        select(func.sum(OrderItem.quantity)).join(Order).where(and_(*filters))
    )
    total_units = units_result.scalar() or 0

    return {
        "total_revenue": float(total_revenue),
        "total_orders": total_orders,
        "average_order_value": float(avg_order_value),
        "total_units_sold": total_units,
        "period_start": period_start,
        "period_end": period_end,
        "territory_id": territory_id,
    }


# Lead Management Endpoints
@router.post(
    "/leads", response_model=SalesLeadResponse, status_code=status.HTTP_201_CREATED
)
async def create_lead(
    lead: SalesLeadCreate,
    auto_assign: bool = Query(
        False, description="Automatically assign to territory sales rep"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new sales lead"""

    # Generate lead number
    lead_number = await generate_lead_number(db)

    # Create lead
    db_lead = SalesLead(
        id=uuid4(),
        lead_number=lead_number,
        first_name=lead.first_name,
        last_name=lead.last_name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        job_title=lead.job_title,
        industry=lead.industry,
        lead_source=lead.lead_source,
        status=LeadStatus.NEW,
        territory_id=lead.territory_id,
        estimated_value=lead.estimated_value,
        estimated_close_date=lead.estimated_close_date,
        notes=lead.notes,
        tags=lead.tags,
        assigned_to=current_user.id if not auto_assign else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Auto-assign to territory sales rep if requested
    if auto_assign and lead.territory_id:
        # Would implement territory assignment logic here
        pass

    # Calculate initial lead score
    db_lead.score = await calculate_lead_score(db_lead)

    db.add(db_lead)
    await db.commit()
    await db.refresh(db_lead)

    return SalesLeadResponse(
        id=db_lead.id,
        lead_number=db_lead.lead_number,
        first_name=db_lead.first_name,
        last_name=db_lead.last_name,
        full_name=f"{db_lead.first_name} {db_lead.last_name}",
        email=db_lead.email,
        phone=db_lead.phone,
        company=db_lead.company,
        job_title=db_lead.job_title,
        industry=db_lead.industry,
        lead_source=db_lead.lead_source,
        status=db_lead.status,
        score=db_lead.score,
        territory_id=db_lead.territory_id,
        territory_name=None,  # Would load from territory
        estimated_value=db_lead.estimated_value,
        estimated_close_date=db_lead.estimated_close_date,
        last_contact_date=db_lead.last_contact_date,
        next_follow_up=db_lead.next_follow_up,
        conversion_probability=50,  # Default
        notes=db_lead.notes,
        tags=db_lead.tags,
        assigned_to=db_lead.assigned_to,
        assigned_to_name=current_user.username
        if db_lead.assigned_to == current_user.id
        else None,
        created_at=db_lead.created_at,
        updated_at=db_lead.updated_at,
    )


@router.get("/leads", response_model=List[SalesLeadResponse])
async def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[LeadStatus] = Query(None),
    territory_id: Optional[UUID] = Query(None),
    lead_source: Optional[str] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None, min_length=1),
    sort_by: str = Query(
        "created_at", regex="^(name|company|score|created_at|estimated_value)$"
    ),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of sales leads with filtering"""

    # Build query
    query = select(SalesLead)

    # Apply filters
    if status:
        query = query.where(SalesLead.status == status)

    if territory_id:
        query = query.where(SalesLead.territory_id == territory_id)

    if lead_source:
        query = query.where(SalesLead.lead_source.ilike(f"%{lead_source}%"))

    if assigned_to:
        query = query.where(SalesLead.assigned_to == assigned_to)

    if min_score:
        query = query.where(SalesLead.score >= min_score)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                SalesLead.first_name.ilike(search_term),
                SalesLead.last_name.ilike(search_term),
                SalesLead.company.ilike(search_term),
                SalesLead.email.ilike(search_term),
            )
        )

    # Apply sorting
    if sort_by == "name":
        order_column = SalesLead.first_name
    elif sort_by == "company":
        order_column = SalesLead.company
    elif sort_by == "score":
        order_column = SalesLead.score
    elif sort_by == "estimated_value":
        order_column = SalesLead.estimated_value
    else:
        order_column = SalesLead.created_at

    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    leads = result.scalars().all()

    # Build response
    response_list = []
    for lead in leads:
        response_item = SalesLeadResponse(
            id=lead.id,
            lead_number=lead.lead_number,
            first_name=lead.first_name,
            last_name=lead.last_name,
            full_name=f"{lead.first_name} {lead.last_name}",
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            job_title=lead.job_title,
            industry=lead.industry,
            lead_source=lead.lead_source,
            status=lead.status,
            score=lead.score,
            territory_id=lead.territory_id,
            territory_name=None,
            estimated_value=lead.estimated_value,
            estimated_close_date=lead.estimated_close_date,
            last_contact_date=lead.last_contact_date,
            next_follow_up=lead.next_follow_up,
            conversion_probability=50,
            notes=lead.notes,
            tags=lead.tags,
            assigned_to=lead.assigned_to,
            assigned_to_name=None,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )
        response_list.append(response_item)

    return response_list


@router.post(
    "/leads/{lead_id}/convert",
    response_model=SalesOpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def convert_lead_to_opportunity(
    lead_id: UUID = Path(..., description="Lead ID"),
    opportunity_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Convert a qualified lead to an opportunity"""

    # Get lead
    lead_result = await db.execute(select(SalesLead).where(SalesLead.id == lead_id))
    lead = lead_result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )

    if lead.status != LeadStatus.QUALIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only qualified leads can be converted to opportunities",
        )

    # Generate opportunity number
    opportunity_number = await generate_opportunity_number(db)

    # Create opportunity
    db_opportunity = SalesOpportunity(
        id=uuid4(),
        opportunity_number=opportunity_number,
        name=opportunity_data.get(
            "name", f"Opportunity for {lead.company or lead.first_name}"
        ),
        lead_id=lead_id,
        stage=SalesStage.PROSPECTING,
        status=OpportunityStatus.OPEN,
        probability=opportunity_data.get("probability", 10),
        estimated_value=opportunity_data.get(
            "estimated_value", lead.estimated_value or Decimal("0")
        ),
        estimated_close_date=opportunity_data.get(
            "estimated_close_date", lead.estimated_close_date
        ),
        territory_id=lead.territory_id,
        description=opportunity_data.get("description"),
        notes=opportunity_data.get("notes"),
        assigned_to=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Calculate weighted value
    db_opportunity.weighted_value = await update_opportunity_weighted_value(
        db_opportunity
    )

    db.add(db_opportunity)

    # Update lead status
    lead.status = LeadStatus.CONVERTED
    lead.conversion_date = datetime.utcnow()
    lead.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(db_opportunity)

    return SalesOpportunityResponse(
        id=db_opportunity.id,
        opportunity_number=db_opportunity.opportunity_number,
        name=db_opportunity.name,
        customer_id=None,
        customer_name=None,
        lead_id=db_opportunity.lead_id,
        lead_name=f"{lead.first_name} {lead.last_name}",
        stage=db_opportunity.stage,
        status=db_opportunity.status,
        probability=db_opportunity.probability,
        estimated_value=db_opportunity.estimated_value,
        weighted_value=db_opportunity.weighted_value,
        actual_value=db_opportunity.actual_value,
        estimated_close_date=db_opportunity.estimated_close_date,
        actual_close_date=db_opportunity.actual_close_date,
        days_in_stage=0,
        total_sales_cycle_days=None,
        territory_id=db_opportunity.territory_id,
        territory_name=None,
        products=[],
        description=db_opportunity.description,
        notes=db_opportunity.notes,
        next_activity=None,
        assigned_to=db_opportunity.assigned_to,
        assigned_to_name=current_user.username,
        created_at=db_opportunity.created_at,
        updated_at=db_opportunity.updated_at,
    )


# Opportunity Management Endpoints
@router.post(
    "/opportunities",
    response_model=SalesOpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_opportunity(
    opportunity: SalesOpportunityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new sales opportunity"""

    # Generate opportunity number
    opportunity_number = await generate_opportunity_number(db)

    # Create opportunity
    db_opportunity = SalesOpportunity(
        id=uuid4(),
        opportunity_number=opportunity_number,
        name=opportunity.name,
        customer_id=opportunity.customer_id,
        lead_id=opportunity.lead_id,
        stage=opportunity.stage,
        status=OpportunityStatus.OPEN,
        probability=opportunity.probability,
        estimated_value=opportunity.estimated_value,
        estimated_close_date=opportunity.estimated_close_date,
        territory_id=opportunity.territory_id,
        description=opportunity.description,
        notes=opportunity.notes,
        assigned_to=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Calculate weighted value
    db_opportunity.weighted_value = await update_opportunity_weighted_value(
        db_opportunity
    )

    db.add(db_opportunity)
    await db.commit()
    await db.refresh(db_opportunity)

    return SalesOpportunityResponse(
        id=db_opportunity.id,
        opportunity_number=db_opportunity.opportunity_number,
        name=db_opportunity.name,
        customer_id=db_opportunity.customer_id,
        customer_name=None,
        lead_id=db_opportunity.lead_id,
        lead_name=None,
        stage=db_opportunity.stage,
        status=db_opportunity.status,
        probability=db_opportunity.probability,
        estimated_value=db_opportunity.estimated_value,
        weighted_value=db_opportunity.weighted_value,
        actual_value=db_opportunity.actual_value,
        estimated_close_date=db_opportunity.estimated_close_date,
        actual_close_date=db_opportunity.actual_close_date,
        days_in_stage=0,
        total_sales_cycle_days=None,
        territory_id=db_opportunity.territory_id,
        territory_name=None,
        products=[],
        description=db_opportunity.description,
        notes=db_opportunity.notes,
        next_activity=None,
        assigned_to=db_opportunity.assigned_to,
        assigned_to_name=current_user.username,
        created_at=db_opportunity.created_at,
        updated_at=db_opportunity.updated_at,
    )


@router.get("/opportunities", response_model=List[SalesOpportunityResponse])
async def list_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    stage: Optional[SalesStage] = Query(None),
    status: Optional[OpportunityStatus] = Query(None),
    territory_id: Optional[UUID] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    min_value: Optional[Decimal] = Query(None, ge=0),
    max_value: Optional[Decimal] = Query(None, ge=0),
    close_date_from: Optional[date] = Query(None),
    close_date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None, min_length=1),
    sort_by: str = Query(
        "created_at",
        regex="^(name|stage|estimated_value|estimated_close_date|created_at)$",
    ),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of sales opportunities with filtering"""

    # Build query
    query = select(SalesOpportunity)

    # Apply filters
    if stage:
        query = query.where(SalesOpportunity.stage == stage)

    if status:
        query = query.where(SalesOpportunity.status == status)

    if territory_id:
        query = query.where(SalesOpportunity.territory_id == territory_id)

    if assigned_to:
        query = query.where(SalesOpportunity.assigned_to == assigned_to)

    if min_value:
        query = query.where(SalesOpportunity.estimated_value >= min_value)

    if max_value:
        query = query.where(SalesOpportunity.estimated_value <= max_value)

    if close_date_from:
        query = query.where(SalesOpportunity.estimated_close_date >= close_date_from)

    if close_date_to:
        query = query.where(SalesOpportunity.estimated_close_date <= close_date_to)

    if search:
        search_term = f"%{search}%"
        query = query.where(SalesOpportunity.name.ilike(search_term))

    # Apply sorting
    if sort_by == "name":
        order_column = SalesOpportunity.name
    elif sort_by == "stage":
        order_column = SalesOpportunity.stage
    elif sort_by == "estimated_value":
        order_column = SalesOpportunity.estimated_value
    elif sort_by == "estimated_close_date":
        order_column = SalesOpportunity.estimated_close_date
    else:
        order_column = SalesOpportunity.created_at

    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    opportunities = result.scalars().all()

    # Build response (simplified for brevity)
    response_list = []
    for opp in opportunities:
        response_item = SalesOpportunityResponse(
            id=opp.id,
            opportunity_number=opp.opportunity_number,
            name=opp.name,
            customer_id=opp.customer_id,
            customer_name=None,
            lead_id=opp.lead_id,
            lead_name=None,
            stage=opp.stage,
            status=opp.status,
            probability=opp.probability,
            estimated_value=opp.estimated_value,
            weighted_value=opp.weighted_value or Decimal("0"),
            actual_value=opp.actual_value,
            estimated_close_date=opp.estimated_close_date,
            actual_close_date=opp.actual_close_date,
            days_in_stage=(datetime.utcnow().date() - opp.created_at.date()).days,
            total_sales_cycle_days=None,
            territory_id=opp.territory_id,
            territory_name=None,
            products=[],
            description=opp.description,
            notes=opp.notes,
            next_activity=None,
            assigned_to=opp.assigned_to,
            assigned_to_name=None,
            created_at=opp.created_at,
            updated_at=opp.updated_at,
        )
        response_list.append(response_item)

    return response_list


# Sales Analytics and Reporting
@router.get("/analytics/dashboard", response_model=Dict[str, Any])
async def get_sales_dashboard(
    period_days: int = Query(30, ge=1, le=365),
    territory_id: Optional[UUID] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get sales dashboard analytics"""

    # Calculate period
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=period_days)

    # Get sales metrics
    metrics = await calculate_sales_metrics(db, start_date, end_date, territory_id)

    # Opportunity pipeline
    pipeline_query = select(
        SalesOpportunity.stage,
        func.count(SalesOpportunity.id).label("count"),
        func.sum(SalesOpportunity.estimated_value).label("value"),
        func.sum(SalesOpportunity.weighted_value).label("weighted_value"),
    ).where(SalesOpportunity.status == OpportunityStatus.OPEN)

    if territory_id:
        pipeline_query = pipeline_query.where(
            SalesOpportunity.territory_id == territory_id
        )

    if assigned_to:
        pipeline_query = pipeline_query.where(
            SalesOpportunity.assigned_to == assigned_to
        )

    pipeline_query = pipeline_query.group_by(SalesOpportunity.stage)

    pipeline_result = await db.execute(pipeline_query)
    pipeline_data = {
        stage: {
            "count": count,
            "value": float(value or 0),
            "weighted_value": float(weighted_value or 0),
        }
        for stage, count, value, weighted_value in pipeline_result.fetchall()
    }

    # Lead conversion metrics
    leads_query = select(
        SalesLead.status, func.count(SalesLead.id).label("count")
    ).where(SalesLead.created_at >= start_date)

    if territory_id:
        leads_query = leads_query.where(SalesLead.territory_id == territory_id)

    if assigned_to:
        leads_query = leads_query.where(SalesLead.assigned_to == assigned_to)

    leads_query = leads_query.group_by(SalesLead.status)

    leads_result = await db.execute(leads_query)
    leads_data = {status: count for status, count in leads_result.fetchall()}

    # Monthly trend
    monthly_trend = []
    for i in range(6):  # Last 6 months
        month_start = (end_date.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(
            days=1
        )

        month_metrics = await calculate_sales_metrics(
            db, month_start, month_end, territory_id
        )
        month_metrics["month"] = month_start.strftime("%Y-%m")
        monthly_trend.insert(0, month_metrics)

    return {
        "summary": metrics,
        "pipeline": pipeline_data,
        "leads": leads_data,
        "monthly_trend": monthly_trend,
        "period": {"start_date": start_date, "end_date": end_date, "days": period_days},
        "filters": {"territory_id": territory_id, "assigned_to": assigned_to},
    }


@router.get("/analytics/conversion", response_model=Dict[str, Any])
async def get_conversion_analytics(
    period_days: int = Query(90, ge=30, le=365),
    territory_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get lead to opportunity conversion analytics"""

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=period_days)

    # Lead to opportunity conversion
    leads_created = await db.execute(
        select(func.count(SalesLead.id)).where(SalesLead.created_at >= start_date)
    )
    total_leads = leads_created.scalar() or 0

    opportunities_created = await db.execute(
        select(func.count(SalesOpportunity.id)).where(
            and_(
                SalesOpportunity.created_at >= start_date,
                SalesOpportunity.lead_id.isnot(None),
            )
        )
    )
    total_opportunities = opportunities_created.scalar() or 0

    lead_conversion_rate = (
        (total_opportunities / total_leads * 100) if total_leads > 0 else 0
    )

    # Opportunity to order conversion
    orders_from_opportunities = await db.execute(
        select(func.count(Order.id)).where(
            and_(
                Order.created_at >= start_date,
                Order.status.in_(["completed", "shipped", "delivered"]),
            )
        )
    )
    total_orders = orders_from_opportunities.scalar() or 0

    opportunity_conversion_rate = (
        (total_orders / total_opportunities * 100) if total_opportunities > 0 else 0
    )

    # Average conversion times
    avg_lead_to_opp_time = await db.execute(
        select(
            func.avg(
                func.extract(
                    "epoch", SalesOpportunity.created_at - SalesLead.created_at
                )
                / 86400
            )
        )
        .join(SalesLead, SalesOpportunity.lead_id == SalesLead.id)
        .where(SalesOpportunity.created_at >= start_date)
    )
    avg_lead_time = avg_lead_to_opp_time.scalar() or 0

    return {
        "conversion_funnel": {
            "leads_created": total_leads,
            "opportunities_created": total_opportunities,
            "orders_closed": total_orders,
            "lead_to_opportunity_rate": round(lead_conversion_rate, 2),
            "opportunity_to_order_rate": round(opportunity_conversion_rate, 2),
            "overall_conversion_rate": round(
                (total_orders / total_leads * 100) if total_leads > 0 else 0, 2
            ),
        },
        "conversion_times": {
            "avg_lead_to_opportunity_days": round(avg_lead_time, 1),
            "avg_opportunity_to_order_days": 0,  # Would calculate
            "avg_total_sales_cycle_days": 0,  # Would calculate
        },
        "period": {"start_date": start_date, "end_date": end_date, "days": period_days},
    }


# Sales Activities
@router.post(
    "/activities",
    response_model=SalesActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sales_activity(
    activity: SalesActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new sales activity"""

    db_activity = SalesActivity(
        id=uuid4(),
        opportunity_id=activity.opportunity_id,
        lead_id=activity.lead_id,
        customer_id=activity.customer_id,
        activity_type=activity.activity_type,
        subject=activity.subject,
        description=activity.description,
        status="scheduled",
        scheduled_date=activity.scheduled_date,
        duration_minutes=activity.duration_minutes,
        location=activity.location,
        attendees=activity.attendees,
        outcome=activity.outcome,
        follow_up_required=activity.follow_up_required,
        follow_up_date=activity.follow_up_date,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_activity)
    await db.commit()
    await db.refresh(db_activity)

    return SalesActivityResponse(
        id=db_activity.id,
        opportunity_id=db_activity.opportunity_id,
        opportunity_name=None,
        lead_id=db_activity.lead_id,
        lead_name=None,
        customer_id=db_activity.customer_id,
        customer_name=None,
        activity_type=db_activity.activity_type,
        subject=db_activity.subject,
        description=db_activity.description,
        status=db_activity.status,
        scheduled_date=db_activity.scheduled_date,
        completed_date=db_activity.completed_date,
        duration_minutes=db_activity.duration_minutes,
        location=db_activity.location,
        attendees=db_activity.attendees,
        outcome=db_activity.outcome,
        follow_up_required=db_activity.follow_up_required,
        follow_up_date=db_activity.follow_up_date,
        created_by=db_activity.created_by,
        created_by_name=current_user.username,
        created_at=db_activity.created_at,
        updated_at=db_activity.updated_at,
    )


# Sales Targets and Forecasting
@router.post(
    "/targets", response_model=SalesTargetResponse, status_code=status.HTTP_201_CREATED
)
async def create_sales_target(
    target: SalesTargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new sales target"""

    db_target = SalesTarget(
        id=uuid4(),
        target_type=target.target_type,
        period_type=target.period_type,
        period_start=target.period_start,
        period_end=target.period_end,
        target_value=target.target_value,
        achieved_value=Decimal("0"),
        territory_id=target.territory_id,
        product_category_id=target.product_category_id,
        description=target.description,
        status="active",
        assigned_to=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_target)
    await db.commit()
    await db.refresh(db_target)

    # Calculate achievement percentage
    achievement_percentage = (
        (db_target.achieved_value / db_target.target_value * 100)
        if db_target.target_value > 0
        else Decimal("0")
    )

    return SalesTargetResponse(
        id=db_target.id,
        target_type=db_target.target_type,
        period_type=db_target.period_type,
        period_start=db_target.period_start,
        period_end=db_target.period_end,
        target_value=db_target.target_value,
        achieved_value=db_target.achieved_value,
        achievement_percentage=achievement_percentage,
        territory_id=db_target.territory_id,
        territory_name=None,
        product_category_id=db_target.product_category_id,
        product_category_name=None,
        description=db_target.description,
        status=db_target.status,
        assigned_to=db_target.assigned_to,
        assigned_to_name=current_user.username,
        created_at=db_target.created_at,
        updated_at=db_target.updated_at,
    )


@router.post(
    "/forecasts",
    response_model=SalesForecastResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sales_forecast(
    forecast: SalesForecastCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new sales forecast"""

    db_forecast = SalesForecast(
        id=uuid4(),
        period_start=forecast.period_start,
        period_end=forecast.period_end,
        forecast_type=forecast.forecast_type,
        territory_id=forecast.territory_id,
        product_category_id=forecast.product_category_id,
        revenue_forecast=forecast.revenue_forecast,
        units_forecast=forecast.units_forecast,
        deals_forecast=forecast.deals_forecast,
        confidence_level=forecast.confidence_level,
        assumptions=forecast.assumptions,
        notes=forecast.notes,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_forecast)
    await db.commit()
    await db.refresh(db_forecast)

    return SalesForecastResponse(
        id=db_forecast.id,
        period_start=db_forecast.period_start,
        period_end=db_forecast.period_end,
        forecast_type=db_forecast.forecast_type,
        territory_id=db_forecast.territory_id,
        territory_name=None,
        product_category_id=db_forecast.product_category_id,
        product_category_name=None,
        revenue_forecast=db_forecast.revenue_forecast,
        units_forecast=db_forecast.units_forecast,
        deals_forecast=db_forecast.deals_forecast,
        actual_revenue=db_forecast.actual_revenue,
        actual_units=db_forecast.actual_units,
        actual_deals=db_forecast.actual_deals,
        accuracy_percentage=db_forecast.accuracy_percentage,
        confidence_level=db_forecast.confidence_level,
        assumptions=db_forecast.assumptions,
        notes=db_forecast.notes,
        created_by=db_forecast.created_by,
        created_by_name=current_user.username,
        created_at=db_forecast.created_at,
        updated_at=db_forecast.updated_at,
    )


# Bulk Operations and Advanced Features
@router.post("/bulk/update-lead-status", response_model=Dict[str, Any])
async def bulk_update_lead_status(
    lead_ids: List[UUID] = Body(..., min_items=1, max_items=100),
    new_status: LeadStatus = Body(...),
    reassign_to: Optional[UUID] = Body(None),
    notes: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Bulk update lead status and assignment"""

    # Get leads
    leads_result = await db.execute(select(SalesLead).where(SalesLead.id.in_(lead_ids)))
    leads = leads_result.scalars().all()

    if len(leads) != len(lead_ids):
        found_ids = {lead.id for lead in leads}
        missing_ids = set(lead_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leads not found: {missing_ids}",
        )

    # Update leads
    updated_count = 0
    for lead in leads:
        lead.status = new_status
        if reassign_to:
            lead.assigned_to = reassign_to
        if notes:
            lead.notes = f"{lead.notes}\n{notes}" if lead.notes else notes
        lead.updated_at = datetime.utcnow()
        updated_count += 1

    await db.commit()

    return {
        "updated_count": updated_count,
        "total_requested": len(lead_ids),
        "new_status": new_status,
        "reassigned_to": reassign_to,
    }


@router.get("/reports/pipeline", response_model=Dict[str, Any])
async def get_pipeline_report(
    territory_id: Optional[UUID] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    stage: Optional[SalesStage] = Query(None),
    probability_min: Optional[int] = Query(None, ge=0, le=100),
    close_date_from: Optional[date] = Query(None),
    close_date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Generate detailed pipeline report"""

    # Build query
    query = select(SalesOpportunity).where(
        SalesOpportunity.status == OpportunityStatus.OPEN
    )

    if territory_id:
        query = query.where(SalesOpportunity.territory_id == territory_id)

    if assigned_to:
        query = query.where(SalesOpportunity.assigned_to == assigned_to)

    if stage:
        query = query.where(SalesOpportunity.stage == stage)

    if probability_min:
        query = query.where(SalesOpportunity.probability >= probability_min)

    if close_date_from:
        query = query.where(SalesOpportunity.estimated_close_date >= close_date_from)

    if close_date_to:
        query = query.where(SalesOpportunity.estimated_close_date <= close_date_to)

    opportunities_result = await db.execute(query)
    opportunities = opportunities_result.scalars().all()

    # Calculate pipeline metrics
    pipeline_by_stage = {}
    total_value = Decimal("0")
    total_weighted_value = Decimal("0")

    for opp in opportunities:
        stage = opp.stage.value
        if stage not in pipeline_by_stage:
            pipeline_by_stage[stage] = {
                "count": 0,
                "total_value": Decimal("0"),
                "weighted_value": Decimal("0"),
                "avg_probability": 0,
                "opportunities": [],
            }

        pipeline_by_stage[stage]["count"] += 1
        pipeline_by_stage[stage]["total_value"] += opp.estimated_value
        pipeline_by_stage[stage]["weighted_value"] += opp.weighted_value or Decimal("0")

        total_value += opp.estimated_value
        total_weighted_value += opp.weighted_value or Decimal("0")

        pipeline_by_stage[stage]["opportunities"].append(
            {
                "id": str(opp.id),
                "name": opp.name,
                "estimated_value": float(opp.estimated_value),
                "probability": opp.probability,
                "estimated_close_date": opp.estimated_close_date.isoformat(),
            }
        )

    # Calculate average probabilities
    for stage_data in pipeline_by_stage.values():
        if stage_data["count"] > 0:
            total_prob = sum(opp["probability"] for opp in stage_data["opportunities"])
            stage_data["avg_probability"] = round(total_prob / stage_data["count"], 1)
            stage_data["total_value"] = float(stage_data["total_value"])
            stage_data["weighted_value"] = float(stage_data["weighted_value"])

    return {
        "summary": {
            "total_opportunities": len(opportunities),
            "total_pipeline_value": float(total_value),
            "total_weighted_value": float(total_weighted_value),
            "average_deal_size": float(total_value / len(opportunities))
            if opportunities
            else 0,
            "weighted_close_probability": float(
                total_weighted_value / total_value * 100
            )
            if total_value > 0
            else 0,
        },
        "pipeline_by_stage": pipeline_by_stage,
        "filters": {
            "territory_id": territory_id,
            "assigned_to": assigned_to,
            "stage": stage,
            "probability_min": probability_min,
            "close_date_from": close_date_from,
            "close_date_to": close_date_to,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }
