"""
CRM (Customer Relationship Management) CRUD Operations - CC02 v31.0 Phase 2

Comprehensive CRM operations with:
- Customer Management & Lifecycle
- Contact Management & Relationship Tracking
- Lead Management & Nurturing
- Opportunity Management & Sales Pipeline
- Sales Process Automation
- Campaign Management & ROI Tracking
- Customer Service & Support
- CRM Analytics & Reporting
- Activity Tracking & Communication History
- Customer Health & Satisfaction Monitoring
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.crm_extended import (
    CampaignExtended,
    ContactExtended,
    CRMActivity,
    CustomerExtended,
    LeadExtended,
    LeadStatus,
    OpportunityExtended,
    OpportunityStage,
    SupportTicket,
    SupportTicketStatus,
)

# =============================================================================
# Customer Management CRUD
# =============================================================================


def create_customer(db: Session, customer_data: Any) -> CustomerExtended:
    """Create a new customer with validation."""
    # Generate unique customer code if not provided
    if not hasattr(customer_data, "customer_code") or not customer_data.customer_code:
        org_id = customer_data.organization_id
        count = (
            db.query(CustomerExtended)
            .filter(CustomerExtended.organization_id == org_id)
            .count()
        )
        customer_data.customer_code = f"CUST-{org_id[:3].upper()}-{count + 1:05d}"

    # Validate account manager exists if specified
    if (
        hasattr(customer_data, "account_manager_id")
        and customer_data.account_manager_id
    ):
        from app.models.user import User

        manager = (
            db.query(User).filter(User.id == customer_data.account_manager_id).first()
        )
        if not manager:
            raise ValueError("Account manager not found")

    customer = CustomerExtended(**customer_data.model_dump())
    customer.created_by = getattr(customer_data, "created_by", "system")
    customer.acquisition_date = customer.acquisition_date or date.today()

    # Initialize customer metrics
    customer.total_orders = 0
    customer.total_revenue = Decimal("0")
    customer.lifetime_value = Decimal("0")

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer(db: Session, customer_id: str) -> Optional[CustomerExtended]:
    """Get customer by ID with related data."""
    return (
        db.query(CustomerExtended)
        .options(
            joinedload(CustomerExtended.account_manager),
            joinedload(CustomerExtended.contacts),
            joinedload(CustomerExtended.opportunities),
            joinedload(CustomerExtended.activities),
            joinedload(CustomerExtended.support_tickets),
        )
        .filter(CustomerExtended.id == customer_id)
        .first()
    )


def get_customers(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[CustomerExtended]:
    """Get customers with filtering and pagination."""
    query = db.query(CustomerExtended)

    if filters:
        if "organization_id" in filters:
            query = query.filter(
                CustomerExtended.organization_id == filters["organization_id"]
            )
        if "account_manager_id" in filters:
            query = query.filter(
                CustomerExtended.account_manager_id == filters["account_manager_id"]
            )
        if "customer_tier" in filters:
            query = query.filter(
                CustomerExtended.customer_tier == filters["customer_tier"]
            )
        if "industry" in filters:
            query = query.filter(CustomerExtended.industry == filters["industry"])
        if "is_active" in filters:
            query = query.filter(CustomerExtended.is_active == filters["is_active"])
        if "is_prospect" in filters:
            query = query.filter(CustomerExtended.is_prospect == filters["is_prospect"])
        if "company_size" in filters:
            query = query.filter(
                CustomerExtended.company_size == filters["company_size"]
            )
        if "search_text" in filters:
            search = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    CustomerExtended.company_name.ilike(search),
                    CustomerExtended.legal_name.ilike(search),
                    CustomerExtended.customer_code.ilike(search),
                )
            )

    return (
        query.options(
            joinedload(CustomerExtended.account_manager),
            joinedload(CustomerExtended.contacts),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_customer(
    db: Session, customer_id: str, customer_data: Any
) -> Optional[CustomerExtended]:
    """Update customer with validation."""
    customer = (
        db.query(CustomerExtended).filter(CustomerExtended.id == customer_id).first()
    )
    if not customer:
        return None

    update_data = customer_data.model_dump(exclude_unset=True)

    # Validate account manager if being updated
    if "account_manager_id" in update_data and update_data["account_manager_id"]:
        from app.models.user import User

        manager = (
            db.query(User).filter(User.id == update_data["account_manager_id"]).first()
        )
        if not manager:
            raise ValueError("Account manager not found")

    for field, value in update_data.items():
        setattr(customer, field, value)

    customer.updated_at = datetime.utcnow()
    customer.updated_by = getattr(customer_data, "updated_by", "system")

    db.commit()
    db.refresh(customer)

    return customer


def calculate_customer_health_score(db: Session, customer_id: str) -> Dict[str, Any]:
    """Calculate comprehensive customer health score."""
    customer = (
        db.query(CustomerExtended).filter(CustomerExtended.id == customer_id).first()
    )
    if not customer:
        raise ValueError("Customer not found")

    health_factors = {}

    # Revenue health (30% weight) - based on revenue trend
    recent_revenue = get_customer_revenue_last_n_months(db, customer_id, 3)
    previous_revenue = get_customer_revenue_months_ago(db, customer_id, 3, 6)

    if previous_revenue > 0:
        revenue_growth = ((recent_revenue - previous_revenue) / previous_revenue) * 100
        revenue_health = min(max(50 + revenue_growth, 0), 100)
    else:
        revenue_health = 75 if recent_revenue > 0 else 25

    health_factors["revenue"] = {"score": revenue_health, "weight": 0.3}

    # Engagement health (25% weight) - based on recent activities
    last_activity = (
        db.query(func.max(CRMActivity.activity_date))
        .filter(
            CRMActivity.customer_id == customer_id,
            CRMActivity.activity_date >= datetime.utcnow() - timedelta(days=90),
        )
        .scalar()
    )

    if last_activity:
        days_since = (datetime.utcnow().date() - last_activity.date()).days
        engagement_health = max(100 - (days_since * 2), 0)
    else:
        engagement_health = 0

    health_factors["engagement"] = {"score": engagement_health, "weight": 0.25}

    # Support health (20% weight) - based on support tickets
    open_tickets = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.customer_id == customer_id,
            SupportTicket.status.in_(
                [SupportTicketStatus.OPEN, SupportTicketStatus.IN_PROGRESS]
            ),
        )
        .count()
    )

    recent_tickets = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.customer_id == customer_id,
            SupportTicket.created_date >= datetime.utcnow() - timedelta(days=30),
        )
        .count()
    )

    support_health = max(100 - (open_tickets * 15) - (recent_tickets * 5), 0)
    health_factors["support"] = {"score": support_health, "weight": 0.2}

    # Payment health (15% weight) - based on payment behavior
    # This would require payment/invoice data - placeholder for now
    payment_health = customer.health_score * 20 if customer.health_score else 75
    health_factors["payment"] = {"score": payment_health, "weight": 0.15}

    # Product usage health (10% weight) - placeholder
    usage_health = 75  # Would be calculated based on product usage data
    health_factors["usage"] = {"score": usage_health, "weight": 0.1}

    # Calculate overall health score
    overall_score = sum(
        factor["score"] * factor["weight"] for factor in health_factors.values()
    )

    # Update customer health score
    customer.health_score = Decimal(overall_score / 20)  # Convert to 0-5 scale
    db.commit()

    # Determine health status
    if overall_score >= 80:
        health_status = "healthy"
    elif overall_score >= 60:
        health_status = "at_risk"
    elif overall_score >= 40:
        health_status = "unhealthy"
    else:
        health_status = "critical"

    return {
        "customer_id": customer_id,
        "overall_health_score": round(overall_score, 2),
        "health_status": health_status,
        "health_factors": health_factors,
        "recommendations": generate_customer_health_recommendations(health_factors),
    }


def get_customer_revenue_last_n_months(
    db: Session, customer_id: str, months: int
) -> Decimal:
    """Get customer revenue for the last N months."""
    # This would query actual order/invoice data - placeholder for now
    return Decimal("10000")  # Placeholder value


def get_customer_revenue_months_ago(
    db: Session, customer_id: str, start_months: int, end_months: int
) -> Decimal:
    """Get customer revenue for a period months ago."""
    # This would query actual order/invoice data - placeholder for now
    return Decimal("8000")  # Placeholder value


def generate_customer_health_recommendations(
    health_factors: Dict[str, Any],
) -> List[str]:
    """Generate recommendations based on health factors."""
    recommendations = []

    for factor_name, factor_data in health_factors.items():
        if factor_data["score"] < 60:
            if factor_name == "revenue":
                recommendations.append(
                    "Consider upselling or cross-selling opportunities"
                )
            elif factor_name == "engagement":
                recommendations.append(
                    "Increase customer touchpoints and communications"
                )
            elif factor_name == "support":
                recommendations.append("Address outstanding support issues promptly")
            elif factor_name == "payment":
                recommendations.append("Review payment terms and credit limits")
            elif factor_name == "usage":
                recommendations.append("Provide additional training or onboarding")

    if not recommendations:
        recommendations.append("Customer appears healthy - maintain regular contact")

    return recommendations


# =============================================================================
# Contact Management CRUD
# =============================================================================


def create_contact(db: Session, contact_data: Any) -> ContactExtended:
    """Create a new contact with validation."""
    # Validate customer exists
    customer = (
        db.query(CustomerExtended)
        .filter(CustomerExtended.id == contact_data.customer_id)
        .first()
    )
    if not customer:
        raise ValueError("Customer not found")

    contact = ContactExtended(**contact_data.model_dump())
    contact.created_by = getattr(contact_data, "created_by", "system")

    # Set as primary contact if it's the first contact for this customer
    existing_contacts = (
        db.query(ContactExtended)
        .filter(ContactExtended.customer_id == contact_data.customer_id)
        .count()
    )

    if existing_contacts == 0:
        contact.is_primary = True

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


def get_contact(db: Session, contact_id: str) -> Optional[ContactExtended]:
    """Get contact by ID with related data."""
    return (
        db.query(ContactExtended)
        .options(
            joinedload(ContactExtended.customer), joinedload(ContactExtended.activities)
        )
        .filter(ContactExtended.id == contact_id)
        .first()
    )


def get_contacts(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[ContactExtended]:
    """Get contacts with filtering and pagination."""
    query = db.query(ContactExtended)

    if filters:
        if "customer_id" in filters:
            query = query.filter(ContactExtended.customer_id == filters["customer_id"])
        if "organization_id" in filters:
            query = query.filter(
                ContactExtended.organization_id == filters["organization_id"]
            )
        if "contact_type" in filters:
            query = query.filter(
                ContactExtended.contact_type == filters["contact_type"]
            )
        if "is_active" in filters:
            query = query.filter(ContactExtended.is_active == filters["is_active"])
        if "is_primary" in filters:
            query = query.filter(ContactExtended.is_primary == filters["is_primary"])
        if "is_decision_maker" in filters:
            query = query.filter(
                ContactExtended.is_decision_maker == filters["is_decision_maker"]
            )
        if "search_text" in filters:
            search = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    ContactExtended.first_name.ilike(search),
                    ContactExtended.last_name.ilike(search),
                    ContactExtended.work_email.ilike(search),
                    ContactExtended.job_title.ilike(search),
                )
            )

    return (
        query.options(joinedload(ContactExtended.customer))
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_contact(
    db: Session, contact_id: str, contact_data: Any
) -> Optional[ContactExtended]:
    """Update contact with validation."""
    contact = db.query(ContactExtended).filter(ContactExtended.id == contact_id).first()
    if not contact:
        return None

    update_data = contact_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(contact, field, value)

    contact.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(contact)

    return contact


# =============================================================================
# Lead Management CRUD
# =============================================================================


def create_lead(db: Session, lead_data: Any) -> LeadExtended:
    """Create a new lead with validation."""
    # Generate unique lead number if not provided
    if not hasattr(lead_data, "lead_number") or not lead_data.lead_number:
        org_id = lead_data.organization_id
        count = (
            db.query(LeadExtended)
            .filter(LeadExtended.organization_id == org_id)
            .count()
        )
        lead_data.lead_number = f"LEAD-{org_id[:3].upper()}-{count + 1:05d}"

    lead = LeadExtended(**lead_data.model_dump())
    lead.created_by = getattr(lead_data, "created_by", "system")

    # Calculate initial lead score
    lead.lead_score = calculate_lead_score(lead)

    db.add(lead)
    db.commit()
    db.refresh(lead)

    return lead


def calculate_lead_score(lead: LeadExtended) -> int:
    """Calculate lead score based on various factors."""
    score = 0

    # Company size scoring
    if lead.company_size:
        size_scores = {
            "startup": 20,
            "small": 40,
            "medium": 60,
            "large": 80,
            "enterprise": 100,
        }
        score += size_scores.get(lead.company_size, 0)

    # Industry scoring (some industries might be more valuable)
    if lead.industry:
        # Placeholder - would be customized based on business
        score += 30

    # Budget range scoring
    if lead.budget_range:
        # Would parse budget range and score accordingly
        score += 25

    # Decision maker bonus
    if lead.decision_maker:
        score += 30

    # Need identified bonus
    if lead.need_identified:
        score += 25

    return min(score, 100)  # Cap at 100


def get_lead(db: Session, lead_id: str) -> Optional[LeadExtended]:
    """Get lead by ID with related data."""
    return (
        db.query(LeadExtended)
        .options(
            joinedload(LeadExtended.assigned_to),
            joinedload(LeadExtended.activities),
            joinedload(LeadExtended.campaign),
        )
        .filter(LeadExtended.id == lead_id)
        .first()
    )


def get_leads(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[LeadExtended]:
    """Get leads with filtering and pagination."""
    query = db.query(LeadExtended)

    if filters:
        if "organization_id" in filters:
            query = query.filter(
                LeadExtended.organization_id == filters["organization_id"]
            )
        if "status" in filters:
            query = query.filter(LeadExtended.status == filters["status"])
        if "lead_source" in filters:
            query = query.filter(LeadExtended.lead_source == filters["lead_source"])
        if "assigned_to_id" in filters:
            query = query.filter(
                LeadExtended.assigned_to_id == filters["assigned_to_id"]
            )
        if "is_qualified" in filters:
            query = query.filter(LeadExtended.is_qualified == filters["is_qualified"])
        if "min_lead_score" in filters:
            query = query.filter(LeadExtended.lead_score >= filters["min_lead_score"])
        if "campaign_id" in filters:
            query = query.filter(LeadExtended.campaign_id == filters["campaign_id"])
        if "search_text" in filters:
            search = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    LeadExtended.first_name.ilike(search),
                    LeadExtended.last_name.ilike(search),
                    LeadExtended.company_name.ilike(search),
                    LeadExtended.email.ilike(search),
                )
            )

    return (
        query.options(
            joinedload(LeadExtended.assigned_to), joinedload(LeadExtended.campaign)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_lead(db: Session, lead_id: str, lead_data: Any) -> Optional[LeadExtended]:
    """Update lead with validation and score recalculation."""
    lead = db.query(LeadExtended).filter(LeadExtended.id == lead_id).first()
    if not lead:
        return None

    update_data = lead_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(lead, field, value)

    # Recalculate lead score
    lead.lead_score = calculate_lead_score(lead)

    # Auto-qualify lead if score is high enough
    if lead.lead_score >= 70 and not lead.is_qualified:
        lead.is_qualified = True
        lead.is_sales_qualified = True

    # Update status based on qualification
    if lead.is_qualified and lead.status == LeadStatus.NEW:
        lead.status = LeadStatus.QUALIFIED

    lead.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(lead)

    return lead


def convert_lead_to_customer(
    db: Session, lead_id: str, customer_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Convert qualified lead to customer and opportunity."""
    lead = db.query(LeadExtended).filter(LeadExtended.id == lead_id).first()
    if not lead:
        raise ValueError("Lead not found")

    if not lead.is_qualified:
        raise ValueError("Lead must be qualified before conversion")

    # Create customer from lead data
    customer_create_data = {
        "organization_id": lead.organization_id,
        "company_name": lead.company_name or f"{lead.first_name} {lead.last_name}",
        "industry": lead.industry,
        "website": lead.website,
        "main_email": lead.email,
        "main_phone": lead.phone,
        "main_address_line1": lead.address_line1,
        "main_city": lead.city,
        "main_state_province": lead.state_province,
        "main_postal_code": lead.postal_code,
        "main_country": lead.country,
        "company_size": lead.company_size,
        "annual_revenue": lead.annual_revenue,
        "employee_count": lead.employee_count,
        "sales_rep_id": lead.assigned_to_id,
        "acquisition_date": date.today(),
        "created_by": "system",
    }

    # Override with any provided customer data
    if customer_data:
        customer_create_data.update(customer_data)

    # Create customer
    from app.schemas.crm_v31 import CustomerCreate

    customer_schema = CustomerCreate(**customer_create_data)
    customer = create_customer(db, customer_schema)

    # Create primary contact from lead
    contact_create_data = {
        "customer_id": customer.id,
        "organization_id": lead.organization_id,
        "first_name": lead.first_name or "Unknown",
        "last_name": lead.last_name or "Contact",
        "job_title": lead.job_title,
        "work_email": lead.email,
        "work_phone": lead.phone,
        "mobile_phone": lead.mobile_phone,
        "is_primary": True,
        "is_decision_maker": lead.decision_maker,
        "created_by": "system",
    }

    from app.schemas.crm_v31 import ContactCreate

    contact_schema = ContactCreate(**contact_create_data)
    contact = create_contact(db, contact_schema)

    # Update lead status
    lead.status = LeadStatus.CONVERTED
    lead.customer_id = customer.id
    lead.conversion_date = datetime.utcnow()

    db.commit()

    return {
        "lead_id": lead_id,
        "customer_id": customer.id,
        "contact_id": contact.id,
        "conversion_date": lead.conversion_date,
    }


# =============================================================================
# Opportunity Management CRUD
# =============================================================================


def create_opportunity(db: Session, opportunity_data: Any) -> OpportunityExtended:
    """Create a new opportunity with validation."""
    # Validate customer exists
    customer = (
        db.query(CustomerExtended)
        .filter(CustomerExtended.id == opportunity_data.customer_id)
        .first()
    )
    if not customer:
        raise ValueError("Customer not found")

    # Generate unique opportunity number if not provided
    if (
        not hasattr(opportunity_data, "opportunity_number")
        or not opportunity_data.opportunity_number
    ):
        org_id = opportunity_data.organization_id
        count = (
            db.query(OpportunityExtended)
            .filter(OpportunityExtended.organization_id == org_id)
            .count()
        )
        opportunity_data.opportunity_number = (
            f"OPP-{org_id[:3].upper()}-{count + 1:05d}"
        )

    opportunity = OpportunityExtended(**opportunity_data.model_dump())
    opportunity.created_by = getattr(opportunity_data, "created_by", "system")

    # Calculate weighted amount
    if opportunity.amount and opportunity.probability:
        opportunity.weighted_amount = opportunity.amount * (
            opportunity.probability / 100
        )

    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    return opportunity


def get_opportunity(db: Session, opportunity_id: str) -> Optional[OpportunityExtended]:
    """Get opportunity by ID with related data."""
    return (
        db.query(OpportunityExtended)
        .options(
            joinedload(OpportunityExtended.customer),
            joinedload(OpportunityExtended.sales_rep),
            joinedload(OpportunityExtended.activities),
        )
        .filter(OpportunityExtended.id == opportunity_id)
        .first()
    )


def get_opportunities(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[OpportunityExtended]:
    """Get opportunities with filtering and pagination."""
    query = db.query(OpportunityExtended)

    if filters:
        if "organization_id" in filters:
            query = query.filter(
                OpportunityExtended.organization_id == filters["organization_id"]
            )
        if "customer_id" in filters:
            query = query.filter(
                OpportunityExtended.customer_id == filters["customer_id"]
            )
        if "stage" in filters:
            query = query.filter(OpportunityExtended.stage == filters["stage"])
        if "sales_rep_id" in filters:
            query = query.filter(
                OpportunityExtended.sales_rep_id == filters["sales_rep_id"]
            )
        if "is_active" in filters:
            query = query.filter(OpportunityExtended.is_active == filters["is_active"])
        if "min_amount" in filters:
            query = query.filter(OpportunityExtended.amount >= filters["min_amount"])
        if "max_amount" in filters:
            query = query.filter(OpportunityExtended.amount <= filters["max_amount"])
        if "expected_close_date_from" in filters:
            query = query.filter(
                OpportunityExtended.expected_close_date
                >= filters["expected_close_date_from"]
            )
        if "expected_close_date_to" in filters:
            query = query.filter(
                OpportunityExtended.expected_close_date
                <= filters["expected_close_date_to"]
            )

    return (
        query.options(
            joinedload(OpportunityExtended.customer),
            joinedload(OpportunityExtended.sales_rep),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_opportunity(
    db: Session, opportunity_id: str, opportunity_data: Any
) -> Optional[OpportunityExtended]:
    """Update opportunity with validation and calculations."""
    opportunity = (
        db.query(OpportunityExtended)
        .filter(OpportunityExtended.id == opportunity_id)
        .first()
    )
    if not opportunity:
        return None

    update_data = opportunity_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(opportunity, field, value)

    # Recalculate weighted amount
    if opportunity.amount and opportunity.probability:
        opportunity.weighted_amount = opportunity.amount * (
            opportunity.probability / 100
        )

    # Set close date if won or lost
    if opportunity.stage in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]:
        if not opportunity.actual_close_date:
            opportunity.actual_close_date = date.today()

    opportunity.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(opportunity)

    return opportunity


# =============================================================================
# Activity Tracking CRUD
# =============================================================================


def create_activity(db: Session, activity_data: Any) -> CRMActivity:
    """Create a new CRM activity."""
    activity = CRMActivity(**activity_data.model_dump())

    # Auto-complete if activity date is in the past
    if activity.activity_date < datetime.utcnow():
        activity.is_completed = True
        activity.completion_date = activity.activity_date

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


def get_activities(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[CRMActivity]:
    """Get activities with filtering."""
    query = db.query(CRMActivity)

    if filters:
        if "customer_id" in filters:
            query = query.filter(CRMActivity.customer_id == filters["customer_id"])
        if "contact_id" in filters:
            query = query.filter(CRMActivity.contact_id == filters["contact_id"])
        if "lead_id" in filters:
            query = query.filter(CRMActivity.lead_id == filters["lead_id"])
        if "opportunity_id" in filters:
            query = query.filter(
                CRMActivity.opportunity_id == filters["opportunity_id"]
            )
        if "owner_id" in filters:
            query = query.filter(CRMActivity.owner_id == filters["owner_id"])
        if "activity_type" in filters:
            query = query.filter(CRMActivity.activity_type == filters["activity_type"])
        if "is_completed" in filters:
            query = query.filter(CRMActivity.is_completed == filters["is_completed"])
        if "date_from" in filters:
            query = query.filter(CRMActivity.activity_date >= filters["date_from"])
        if "date_to" in filters:
            query = query.filter(CRMActivity.activity_date <= filters["date_to"])

    return (
        query.options(
            joinedload(CRMActivity.customer),
            joinedload(CRMActivity.contact),
            joinedload(CRMActivity.owner),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_activity(
    db: Session, activity_id: str, activity_data: Any
) -> Optional[CRMActivity]:
    """Update activity."""
    activity = db.query(CRMActivity).filter(CRMActivity.id == activity_id).first()
    if not activity:
        return None

    update_data = activity_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(activity, field, value)

    activity.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(activity)

    return activity


# =============================================================================
# Campaign Management CRUD
# =============================================================================


def create_campaign(db: Session, campaign_data: Any) -> CampaignExtended:
    """Create a new marketing campaign."""
    # Generate unique campaign code if not provided
    if not hasattr(campaign_data, "campaign_code") or not campaign_data.campaign_code:
        org_id = campaign_data.organization_id
        count = (
            db.query(CampaignExtended)
            .filter(CampaignExtended.organization_id == org_id)
            .count()
        )
        campaign_data.campaign_code = f"CAMP-{org_id[:3].upper()}-{count + 1:04d}"

    campaign = CampaignExtended(**campaign_data.model_dump())
    campaign.created_by = getattr(campaign_data, "created_by", "system")

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return campaign


def get_campaign(db: Session, campaign_id: str) -> Optional[CampaignExtended]:
    """Get campaign by ID."""
    return (
        db.query(CampaignExtended)
        .options(joinedload(CampaignExtended.leads))
        .filter(CampaignExtended.id == campaign_id)
        .first()
    )


def get_campaigns(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[CampaignExtended]:
    """Get campaigns with filtering."""
    query = db.query(CampaignExtended)

    if filters:
        if "organization_id" in filters:
            query = query.filter(
                CampaignExtended.organization_id == filters["organization_id"]
            )
        if "campaign_type" in filters:
            query = query.filter(
                CampaignExtended.campaign_type == filters["campaign_type"]
            )
        if "status" in filters:
            query = query.filter(CampaignExtended.status == filters["status"])
        if "is_active" in filters:
            query = query.filter(CampaignExtended.is_active == filters["is_active"])

    return query.offset(skip).limit(limit).all()


def update_campaign(
    db: Session, campaign_id: str, campaign_data: Any
) -> Optional[CampaignExtended]:
    """Update campaign with ROI calculations."""
    campaign = (
        db.query(CampaignExtended).filter(CampaignExtended.id == campaign_id).first()
    )
    if not campaign:
        return None

    update_data = campaign_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(campaign, field, value)

    # Calculate ROI if we have cost and revenue data
    if campaign.actual_cost and campaign.revenue_generated:
        if campaign.actual_cost > 0:
            campaign.roi_percentage = (
                (campaign.revenue_generated - campaign.actual_cost)
                / campaign.actual_cost
            ) * 100
            campaign.roas = campaign.revenue_generated / campaign.actual_cost

    # Calculate cost per lead
    if campaign.actual_cost and campaign.leads_generated:
        if campaign.leads_generated > 0:
            campaign.cost_per_lead = campaign.actual_cost / campaign.leads_generated

    campaign.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(campaign)

    return campaign


# =============================================================================
# Support Ticket Management CRUD
# =============================================================================


def create_support_ticket(db: Session, ticket_data: Any) -> SupportTicket:
    """Create a new support ticket."""
    # Validate customer exists
    customer = (
        db.query(CustomerExtended)
        .filter(CustomerExtended.id == ticket_data.customer_id)
        .first()
    )
    if not customer:
        raise ValueError("Customer not found")

    # Generate unique ticket number if not provided
    if not hasattr(ticket_data, "ticket_number") or not ticket_data.ticket_number:
        org_id = ticket_data.organization_id
        count = (
            db.query(SupportTicket)
            .filter(SupportTicket.organization_id == org_id)
            .count()
        )
        ticket_data.ticket_number = f"TICK-{org_id[:3].upper()}-{count + 1:05d}"

    ticket = SupportTicket(**ticket_data.model_dump())
    ticket.created_date = ticket.created_date or datetime.utcnow()

    # Set SLA due date based on priority
    if ticket.priority:
        sla_hours = {"low": 72, "medium": 24, "high": 8, "urgent": 4, "critical": 2}
        hours = sla_hours.get(ticket.priority.value, 24)
        ticket.sla_due_date = ticket.created_date + timedelta(hours=hours)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


def get_support_ticket(db: Session, ticket_id: str) -> Optional[SupportTicket]:
    """Get support ticket by ID."""
    return (
        db.query(SupportTicket)
        .options(
            joinedload(SupportTicket.customer),
            joinedload(SupportTicket.contact),
            joinedload(SupportTicket.assigned_to),
        )
        .filter(SupportTicket.id == ticket_id)
        .first()
    )


def get_support_tickets(
    db: Session,
    filters: Optional[Dict[str, Any]] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[SupportTicket]:
    """Get support tickets with filtering."""
    query = db.query(SupportTicket)

    if filters:
        if "customer_id" in filters:
            query = query.filter(SupportTicket.customer_id == filters["customer_id"])
        if "status" in filters:
            query = query.filter(SupportTicket.status == filters["status"])
        if "priority" in filters:
            query = query.filter(SupportTicket.priority == filters["priority"])
        if "assigned_to_id" in filters:
            query = query.filter(
                SupportTicket.assigned_to_id == filters["assigned_to_id"]
            )
        if "is_escalated" in filters:
            query = query.filter(SupportTicket.is_escalated == filters["is_escalated"])

    return (
        query.options(
            joinedload(SupportTicket.customer), joinedload(SupportTicket.assigned_to)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_support_ticket(
    db: Session, ticket_id: str, ticket_data: Any
) -> Optional[SupportTicket]:
    """Update support ticket with SLA tracking."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        return None

    update_data = ticket_data.model_dump(exclude_unset=True)

    # Track first response time
    if "status" in update_data and not ticket.first_response_date:
        if update_data["status"] != "open":
            ticket.first_response_date = datetime.utcnow()
            if ticket.created_date:
                ticket.response_time_minutes = int(
                    (ticket.first_response_date - ticket.created_date).total_seconds()
                    / 60
                )

    for field, value in update_data.items():
        setattr(ticket, field, value)

    # Set resolution date if ticket is resolved
    if ticket.status == SupportTicketStatus.RESOLVED and not ticket.resolved_date:
        ticket.resolved_date = datetime.utcnow()
        if ticket.created_date:
            ticket.resolution_time_minutes = int(
                (ticket.resolved_date - ticket.created_date).total_seconds() / 60
            )

    # Check for SLA breach
    if ticket.sla_due_date and datetime.utcnow() > ticket.sla_due_date:
        if ticket.status not in [
            SupportTicketStatus.RESOLVED,
            SupportTicketStatus.CLOSED,
        ]:
            ticket.sla_breached = True

    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return ticket


# =============================================================================
# CRM Analytics and Reporting
# =============================================================================


def get_crm_dashboard_metrics(
    db: Session, organization_id: str, date_from: date, date_to: date
) -> Dict[str, Any]:
    """Get comprehensive CRM dashboard metrics."""
    # Lead metrics
    leads_created = (
        db.query(LeadExtended)
        .filter(
            LeadExtended.organization_id == organization_id,
            func.date(LeadExtended.created_at) >= date_from,
            func.date(LeadExtended.created_at) <= date_to,
        )
        .count()
    )

    leads_converted = (
        db.query(LeadExtended)
        .filter(
            LeadExtended.organization_id == organization_id,
            LeadExtended.status == LeadStatus.CONVERTED,
            func.date(LeadExtended.conversion_date) >= date_from,
            func.date(LeadExtended.conversion_date) <= date_to,
        )
        .count()
    )

    # Opportunity metrics
    opportunities_created = (
        db.query(OpportunityExtended)
        .filter(
            OpportunityExtended.organization_id == organization_id,
            func.date(OpportunityExtended.created_at) >= date_from,
            func.date(OpportunityExtended.created_at) <= date_to,
        )
        .count()
    )

    opportunities_won = (
        db.query(OpportunityExtended)
        .filter(
            OpportunityExtended.organization_id == organization_id,
            OpportunityExtended.stage == OpportunityStage.CLOSED_WON,
            OpportunityExtended.actual_close_date >= date_from,
            OpportunityExtended.actual_close_date <= date_to,
        )
        .count()
    )

    # Revenue metrics
    total_revenue = (
        db.query(func.sum(OpportunityExtended.amount))
        .filter(
            OpportunityExtended.organization_id == organization_id,
            OpportunityExtended.stage == OpportunityStage.CLOSED_WON,
            OpportunityExtended.actual_close_date >= date_from,
            OpportunityExtended.actual_close_date <= date_to,
        )
        .scalar()
        or 0
    )

    # Pipeline value
    pipeline_value = (
        db.query(func.sum(OpportunityExtended.amount))
        .filter(
            OpportunityExtended.organization_id == organization_id,
            OpportunityExtended.is_active,
            OpportunityExtended.stage.notin_(
                [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]
            ),
        )
        .scalar()
        or 0
    )

    # Customer metrics
    new_customers = (
        db.query(CustomerExtended)
        .filter(
            CustomerExtended.organization_id == organization_id,
            CustomerExtended.acquisition_date >= date_from,
            CustomerExtended.acquisition_date <= date_to,
        )
        .count()
    )

    # Activity metrics
    total_activities = (
        db.query(CRMActivity)
        .filter(
            CRMActivity.organization_id == organization_id,
            func.date(CRMActivity.activity_date) >= date_from,
            func.date(CRMActivity.activity_date) <= date_to,
        )
        .count()
    )

    return {
        "organization_id": organization_id,
        "period_start": date_from,
        "period_end": date_to,
        "leads_created": leads_created,
        "leads_converted": leads_converted,
        "lead_conversion_rate": (leads_converted / leads_created * 100)
        if leads_created > 0
        else 0,
        "opportunities_created": opportunities_created,
        "opportunities_won": opportunities_won,
        "win_rate": (opportunities_won / opportunities_created * 100)
        if opportunities_created > 0
        else 0,
        "total_revenue": float(total_revenue),
        "pipeline_value": float(pipeline_value),
        "new_customers": new_customers,
        "total_activities": total_activities,
        "metrics_date": datetime.utcnow(),
    }
