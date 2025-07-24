"""
CRM API v31.0 - Customer Relationship Management API

Comprehensive CRM system with 10 core endpoints:
1. Customer Management
2. Contact Management
3. Lead Management
4. Opportunity Management
5. Activity Tracking
6. Campaign Management
7. Support Tickets
8. CRM Analytics
9. Lead Conversion
10. Sales Pipeline Management
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.crm_v31 import (  # Activity schemas; Campaign schemas; Contact schemas; Analytics schemas; Customer schemas; Lead schemas; Opportunity schemas; Support ticket schemas
    ActivityCreate,
    ActivityFilterRequest,
    ActivityResponse,
    ActivityUpdate,
    AssignLeadRequest,
    BulkEmailCampaignRequest,
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    ConvertLeadRequest,
    CRMDashboardMetrics,
    CustomerCreate,
    CustomerFilterRequest,
    CustomerHealthScore,
    CustomerResponse,
    CustomerUpdate,
    EscalateTicketRequest,
    LeadConversionAnalysis,
    LeadCreate,
    LeadFilterRequest,
    LeadResponse,
    LeadUpdate,
    OpportunityCreate,
    OpportunityFilterRequest,
    OpportunityResponse,
    OpportunityUpdate,
    SalesForecast,
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketUpdate,
    UpdateOpportunityStageRequest,
)

router = APIRouter()
crm_service = CRMService()


# =============================================================================
# 1. Customer Management Endpoints
# =============================================================================


@router.post(
    "/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED
)
async def create_customer(
    customer: CustomerCreate, db: Session = Depends(get_db)
) -> CustomerResponse:
    """
    Create a new customer in the CRM system.

    Features:
    - Comprehensive customer profile creation
    - Automatic customer code generation
    - Customer segmentation and tiering
    - Account manager assignment
    - Custom fields support
    """
    try:
        # Generate unique customer code if not provided
        if not customer.customer_code:
            customer.customer_code = f"CUST-{uuid4().hex[:8].upper()}"

        created_customer = await crm_service.create_customer(db, customer)
        return created_customer

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create customer: {str(e)}",
        )


@router.get("/customers", response_model=List[CustomerResponse])
async def list_customers(
    db: Session = Depends(get_db),
    organization_id: Optional[str] = Query(None),
    account_manager_id: Optional[str] = Query(None),
    customer_tier: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    is_prospect: Optional[bool] = Query(None),
    search_text: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[CustomerResponse]:
    """
    List customers with advanced filtering and search capabilities.

    Features:
    - Multi-criteria filtering
    - Full-text search across customer data
    - Pagination support
    - Account manager filtering
    - Customer tier and segment filtering
    """
    filter_request = CustomerFilterRequest(
        organization_id=organization_id,
        account_manager_id=account_manager_id,
        customer_tier=customer_tier,
        industry=industry,
        is_active=is_active,
        is_prospect=is_prospect,
        search_text=search_text,
    )

    customers = await crm_service.get_customers(db, filter_request, skip, limit)
    return customers


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str, db: Session = Depends(get_db)
) -> CustomerResponse:
    """Get customer details by ID with comprehensive profile information."""
    customer = await crm_service.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str, customer_update: CustomerUpdate, db: Session = Depends(get_db)
) -> CustomerResponse:
    """
    Update customer information with comprehensive profile management.

    Features:
    - Partial updates support
    - Customer lifecycle tracking
    - Automatic health score recalculation
    - Audit trail maintenance
    """
    updated_customer = await crm_service.update_customer(
        db, customer_id, customer_update
    )
    if not updated_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return updated_customer


@router.get("/customers/{customer_id}/health-score", response_model=CustomerHealthScore)
async def get_customer_health_score(
    customer_id: str, db: Session = Depends(get_db)
) -> CustomerHealthScore:
    """
    Calculate and return comprehensive customer health score.

    Features:
    - Multi-factor health analysis
    - Engagement scoring
    - Revenue contribution analysis
    - Risk assessment
    - Actionable recommendations
    """
    health_score = await crm_service.calculate_customer_health_score(db, customer_id)
    if not health_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or health score cannot be calculated",
        )
    return health_score


# =============================================================================
# 2. Contact Management Endpoints
# =============================================================================


@router.post(
    "/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED
)
async def create_contact(
    contact: ContactCreate, db: Session = Depends(get_db)
) -> ContactResponse:
    """
    Create a new contact for a customer.

    Features:
    - Comprehensive contact profile
    - Relationship hierarchy management
    - Decision maker identification
    - Social media integration
    - Communication preferences
    """
    try:
        created_contact = await crm_service.create_contact(db, contact)
        return created_contact

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create contact: {str(e)}",
        )


@router.get("/contacts", response_model=List[ContactResponse])
async def list_contacts(
    db: Session = Depends(get_db),
    customer_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    contact_type: Optional[str] = Query(None),
    is_decision_maker: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[ContactResponse]:
    """List contacts with filtering by customer, type, and decision-making authority."""
    contacts = await crm_service.get_contacts(
        db,
        customer_id,
        organization_id,
        contact_type,
        is_decision_maker,
        is_active,
        skip,
        limit,
    )
    return contacts


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str, db: Session = Depends(get_db)
) -> ContactResponse:
    """Get contact details by ID with full profile information."""
    contact = await crm_service.get_contact_by_id(db, contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str, contact_update: ContactUpdate, db: Session = Depends(get_db)
) -> ContactResponse:
    """Update contact information with relationship tracking."""
    updated_contact = await crm_service.update_contact(db, contact_id, contact_update)
    if not updated_contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return updated_contact


# =============================================================================
# 3. Lead Management Endpoints
# =============================================================================


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)) -> LeadResponse:
    """
    Create a new lead in the CRM system.

    Features:
    - Automatic lead scoring
    - Source tracking and attribution
    - Qualification workflow
    - Assignment automation
    - Campaign integration
    """
    try:
        # Generate unique lead number if not provided
        if not lead.lead_number:
            lead.lead_number = f"LEAD-{uuid4().hex[:8].upper()}"

        created_lead = await crm_service.create_lead(db, lead)
        return created_lead

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create lead: {str(e)}",
        )


@router.get("/leads", response_model=List[LeadResponse])
async def list_leads(
    db: Session = Depends(get_db),
    organization_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    lead_source: Optional[str] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    is_qualified: Optional[bool] = Query(None),
    min_lead_score: Optional[int] = Query(None, ge=0, le=100),
    campaign_id: Optional[str] = Query(None),
    search_text: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[LeadResponse]:
    """
    List leads with comprehensive filtering and search capabilities.

    Features:
    - Multi-criteria filtering
    - Lead score filtering
    - Campaign attribution filtering
    - Assignment status filtering
    - Full-text search
    """
    filter_request = LeadFilterRequest(
        organization_id=organization_id,
        status=status,
        lead_source=lead_source,
        assigned_to_id=assigned_to_id,
        is_qualified=is_qualified,
        min_lead_score=min_lead_score,
        campaign_id=campaign_id,
        search_text=search_text,
    )

    leads = await crm_service.get_leads(db, filter_request, skip, limit)
    return leads


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str, db: Session = Depends(get_db)) -> LeadResponse:
    """Get lead details by ID with scoring and qualification information."""
    lead = await crm_service.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )
    return lead


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str, lead_update: LeadUpdate, db: Session = Depends(get_db)
) -> LeadResponse:
    """
    Update lead information with automatic scoring recalculation.

    Features:
    - Dynamic lead scoring updates
    - Qualification status tracking
    - Assignment history
    - Activity timeline updates
    """
    updated_lead = await crm_service.update_lead(db, lead_id, lead_update)
    if not updated_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found"
        )
    return updated_lead


@router.post("/leads/{lead_id}/convert", response_model=LeadConversionAnalysis)
async def convert_lead(
    lead_id: str, conversion_request: ConvertLeadRequest, db: Session = Depends(get_db)
) -> LeadConversionAnalysis:
    """
    Convert lead to customer and opportunity.

    Features:
    - Automatic customer creation
    - Opportunity generation
    - Conversion tracking
    - Data migration and mapping
    - Conversion analytics
    """
    try:
        conversion_result = await crm_service.convert_lead_to_customer(
            db, lead_id, conversion_request.customer_data
        )
        return conversion_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to convert lead: {str(e)}",
        )


@router.post("/leads/{lead_id}/assign", response_model=LeadResponse)
async def assign_lead(
    lead_id: str, assignment_request: AssignLeadRequest, db: Session = Depends(get_db)
) -> LeadResponse:
    """Assign lead to sales representative with notification."""
    try:
        assigned_lead = await crm_service.assign_lead(
            db, lead_id, assignment_request.assigned_to_id, assignment_request.notes
        )
        return assigned_lead

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign lead: {str(e)}",
        )


# =============================================================================
# 4. Opportunity Management Endpoints
# =============================================================================


@router.post(
    "/opportunities",
    response_model=OpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_opportunity(
    opportunity: OpportunityCreate, db: Session = Depends(get_db)
) -> OpportunityResponse:
    """
    Create a new sales opportunity.

    Features:
    - Pipeline stage management
    - Revenue forecasting
    - Competition tracking
    - Decision process mapping
    - Product/service configuration
    """
    try:
        # Generate unique opportunity number if not provided
        if not opportunity.opportunity_number:
            opportunity.opportunity_number = f"OPP-{uuid4().hex[:8].upper()}"

        created_opportunity = await crm_service.create_opportunity(db, opportunity)
        return created_opportunity

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create opportunity: {str(e)}",
        )


@router.get("/opportunities", response_model=List[OpportunityResponse])
async def list_opportunities(
    db: Session = Depends(get_db),
    organization_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    sales_rep_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    min_amount: Optional[Decimal] = Query(None, ge=0),
    max_amount: Optional[Decimal] = Query(None, ge=0),
    expected_close_date_from: Optional[date] = Query(None),
    expected_close_date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[OpportunityResponse]:
    """
    List opportunities with comprehensive filtering for pipeline management.

    Features:
    - Stage-based filtering
    - Amount range filtering
    - Timeline filtering
    - Sales rep filtering
    - Customer filtering
    """
    filter_request = OpportunityFilterRequest(
        organization_id=organization_id,
        customer_id=customer_id,
        stage=stage,
        sales_rep_id=sales_rep_id,
        is_active=is_active,
        min_amount=min_amount,
        max_amount=max_amount,
        expected_close_date_from=expected_close_date_from,
        expected_close_date_to=expected_close_date_to,
    )

    opportunities = await crm_service.get_opportunities(db, filter_request, skip, limit)
    return opportunities


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str, db: Session = Depends(get_db)
) -> OpportunityResponse:
    """Get opportunity details by ID with complete sales information."""
    opportunity = await crm_service.get_opportunity_by_id(db, opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opportunity


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    opportunity_update: OpportunityUpdate,
    db: Session = Depends(get_db),
) -> OpportunityResponse:
    """
    Update opportunity with automatic pipeline management.

    Features:
    - Stage progression tracking
    - Probability adjustments
    - Weighted amount calculations
    - Forecast category updates
    - Competition analysis updates
    """
    updated_opportunity = await crm_service.update_opportunity(
        db, opportunity_id, opportunity_update
    )
    if not updated_opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return updated_opportunity


@router.post(
    "/opportunities/{opportunity_id}/update-stage", response_model=OpportunityResponse
)
async def update_opportunity_stage(
    opportunity_id: str,
    stage_update: UpdateOpportunityStageRequest,
    db: Session = Depends(get_db),
) -> OpportunityResponse:
    """
    Update opportunity stage with automatic pipeline management.

    Features:
    - Stage progression validation
    - Automatic probability updates
    - Pipeline velocity tracking
    - Stage-specific requirements
    - Activity logging
    """
    try:
        updated_opportunity = await crm_service.update_opportunity_stage(
            db,
            opportunity_id,
            stage_update.stage,
            stage_update.probability,
            stage_update.notes,
        )
        return updated_opportunity

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update opportunity stage: {str(e)}",
        )


@router.get("/sales-forecast", response_model=SalesForecast)
async def get_sales_forecast(
    organization_id: str = Query(...),
    forecast_period: str = Query("monthly"),
    db: Session = Depends(get_db),
) -> SalesForecast:
    """
    Generate sales forecast based on pipeline analysis.

    Features:
    - Pipeline value analysis
    - Weighted forecasting
    - Stage-based probability calculations
    - Historical accuracy tracking
    - Committed vs. best-case scenarios
    """
    forecast = await crm_service.generate_sales_forecast(
        db, organization_id, forecast_period
    )
    return forecast


# =============================================================================
# 5. Activity Tracking Endpoints
# =============================================================================


@router.post(
    "/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED
)
async def create_activity(
    activity: ActivityCreate, db: Session = Depends(get_db)
) -> ActivityResponse:
    """
    Create a new CRM activity for tracking customer interactions.

    Features:
    - Multi-entity relationship tracking
    - Communication channel tracking
    - Outcome recording
    - Follow-up automation
    - Integration with email/calendar systems
    """
    try:
        created_activity = await crm_service.create_activity(db, activity)
        return created_activity

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create activity: {str(e)}",
        )


@router.get("/activities", response_model=List[ActivityResponse])
async def list_activities(
    db: Session = Depends(get_db),
    customer_id: Optional[str] = Query(None),
    contact_id: Optional[str] = Query(None),
    lead_id: Optional[str] = Query(None),
    opportunity_id: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    activity_type: Optional[str] = Query(None),
    is_completed: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[ActivityResponse]:
    """
    List activities with comprehensive filtering for activity management.

    Features:
    - Multi-entity filtering
    - Activity type filtering
    - Date range filtering
    - Completion status filtering
    - Owner/assignee filtering
    """
    filter_request = ActivityFilterRequest(
        customer_id=customer_id,
        contact_id=contact_id,
        lead_id=lead_id,
        opportunity_id=opportunity_id,
        owner_id=owner_id,
        activity_type=activity_type,
        is_completed=is_completed,
        date_from=date_from,
        date_to=date_to,
    )

    activities = await crm_service.get_activities(db, filter_request, skip, limit)
    return activities


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str, db: Session = Depends(get_db)
) -> ActivityResponse:
    """Get activity details by ID with complete interaction information."""
    activity = await crm_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return activity


@router.put("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str, activity_update: ActivityUpdate, db: Session = Depends(get_db)
) -> ActivityResponse:
    """
    Update activity with outcome tracking and follow-up management.

    Features:
    - Completion tracking
    - Outcome recording
    - Follow-up scheduling
    - Communication metrics
    - Integration updates
    """
    updated_activity = await crm_service.update_activity(
        db, activity_id, activity_update
    )
    if not updated_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return updated_activity


# =============================================================================
# 6. Campaign Management Endpoints
# =============================================================================


@router.post(
    "/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED
)
async def create_campaign(
    campaign: CampaignCreate, db: Session = Depends(get_db)
) -> CampaignResponse:
    """
    Create a new marketing campaign.

    Features:
    - Multi-channel campaign setup
    - Target audience configuration
    - Budget and goal setting
    - ROI tracking preparation
    - Integration with marketing tools
    """
    try:
        # Generate unique campaign code if not provided
        if not campaign.campaign_code:
            campaign.campaign_code = f"CAMP-{uuid4().hex[:8].upper()}"

        created_campaign = await crm_service.create_campaign(db, campaign)
        return created_campaign

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create campaign: {str(e)}",
        )


@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    db: Session = Depends(get_db),
    organization_id: Optional[str] = Query(None),
    campaign_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[CampaignResponse]:
    """List campaigns with filtering by type, status, and activity."""
    campaigns = await crm_service.get_campaigns(
        db, organization_id, campaign_type, status, is_active, skip, limit
    )
    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str, db: Session = Depends(get_db)
) -> CampaignResponse:
    """Get campaign details by ID with complete performance metrics."""
    campaign = await crm_service.get_campaign_by_id(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str, campaign_update: CampaignUpdate, db: Session = Depends(get_db)
) -> CampaignResponse:
    """
    Update campaign with performance tracking and ROI calculation.

    Features:
    - Real-time performance updates
    - ROI calculation
    - Conversion tracking
    - Budget management
    - Automated reporting
    """
    updated_campaign = await crm_service.update_campaign(
        db, campaign_id, campaign_update
    )
    if not updated_campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    return updated_campaign


@router.post("/campaigns/{campaign_id}/send-email", response_model=Dict[str, Any])
async def send_bulk_email_campaign(
    campaign_id: str,
    email_request: BulkEmailCampaignRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Execute bulk email campaign with tracking.

    Features:
    - Bulk email sending
    - Recipient list management
    - Template integration
    - Delivery tracking
    - Open/click tracking
    """
    try:
        result = await crm_service.send_bulk_email_campaign(
            db,
            campaign_id,
            email_request.recipient_list,
            email_request.email_template_id,
            email_request.send_date,
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send email campaign: {str(e)}",
        )


# =============================================================================
# 7. Support Ticket Management Endpoints
# =============================================================================


@router.post(
    "/support-tickets",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_support_ticket(
    ticket: SupportTicketCreate, db: Session = Depends(get_db)
) -> SupportTicketResponse:
    """
    Create a new customer support ticket.

    Features:
    - Automatic ticket numbering
    - Priority assessment
    - SLA calculation
    - Auto-assignment rules
    - Customer notification
    """
    try:
        # Generate unique ticket number if not provided
        if not ticket.ticket_number:
            ticket.ticket_number = f"TICK-{uuid4().hex[:8].upper()}"

        created_ticket = await crm_service.create_support_ticket(db, ticket)
        return created_ticket

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create support ticket: {str(e)}",
        )


@router.get("/support-tickets", response_model=List[SupportTicketResponse])
async def list_support_tickets(
    db: Session = Depends(get_db),
    customer_id: Optional[str] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_escalated: Optional[bool] = Query(None),
    sla_breached: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> List[SupportTicketResponse]:
    """List support tickets with comprehensive filtering for support management."""
    tickets = await crm_service.get_support_tickets(
        db,
        customer_id,
        assigned_to_id,
        status,
        priority,
        category,
        is_escalated,
        sla_breached,
        skip,
        limit,
    )
    return tickets


@router.get("/support-tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_support_ticket(
    ticket_id: str, db: Session = Depends(get_db)
) -> SupportTicketResponse:
    """Get support ticket details by ID with complete case information."""
    ticket = await crm_service.get_support_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found"
        )
    return ticket


@router.put("/support-tickets/{ticket_id}", response_model=SupportTicketResponse)
async def update_support_ticket(
    ticket_id: str, ticket_update: SupportTicketUpdate, db: Session = Depends(get_db)
) -> SupportTicketResponse:
    """
    Update support ticket with SLA tracking and resolution management.

    Features:
    - Status progression tracking
    - Resolution time calculation
    - Customer satisfaction tracking
    - SLA compliance monitoring
    - Escalation management
    """
    updated_ticket = await crm_service.update_support_ticket(
        db, ticket_id, ticket_update
    )
    if not updated_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Support ticket not found"
        )
    return updated_ticket


@router.post(
    "/support-tickets/{ticket_id}/escalate", response_model=SupportTicketResponse
)
async def escalate_support_ticket(
    ticket_id: str,
    escalation_request: EscalateTicketRequest,
    db: Session = Depends(get_db),
) -> SupportTicketResponse:
    """
    Escalate support ticket to higher level support.

    Features:
    - Escalation workflow
    - Assignment transfer
    - Escalation reason tracking
    - Notification automation
    - SLA adjustment
    """
    try:
        escalated_ticket = await crm_service.escalate_support_ticket(
            db,
            ticket_id,
            escalation_request.escalated_to_id,
            escalation_request.escalation_reason,
        )
        return escalated_ticket

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to escalate ticket: {str(e)}",
        )


# =============================================================================
# 8. CRM Analytics and Reporting Endpoints
# =============================================================================


@router.get("/analytics/dashboard", response_model=CRMDashboardMetrics)
async def get_crm_dashboard_metrics(
    organization_id: str = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
) -> CRMDashboardMetrics:
    """
    Get comprehensive CRM dashboard metrics for specified period.

    Features:
    - Lead conversion metrics
    - Opportunity win rates
    - Revenue analysis
    - Pipeline health
    - Activity summaries
    - Customer acquisition metrics
    """
    metrics = await crm_service.get_crm_dashboard_metrics(
        db, organization_id, period_start, period_end
    )
    return metrics


@router.get("/analytics/pipeline", response_model=Dict[str, Any])
async def get_pipeline_analytics(
    organization_id: str = Query(...),
    sales_rep_id: Optional[str] = Query(None),
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed sales pipeline analytics and insights.

    Features:
    - Pipeline value by stage
    - Velocity analysis
    - Conversion rates by stage
    - Average deal size
    - Sales cycle analysis
    - Forecasting accuracy
    """
    analytics = await crm_service.get_pipeline_analytics(
        db, organization_id, sales_rep_id, period_start, period_end
    )
    return analytics


@router.get("/analytics/performance", response_model=Dict[str, Any])
async def get_sales_performance_analytics(
    organization_id: str = Query(...),
    sales_rep_id: Optional[str] = Query(None),
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get sales performance analytics for teams or individuals.

    Features:
    - Quota attainment
    - Activity metrics
    - Conversion rates
    - Revenue contribution
    - Performance ranking
    - Goal tracking
    """
    performance = await crm_service.get_sales_performance_analytics(
        db, organization_id, sales_rep_id, period_start, period_end
    )
    return performance


@router.get("/analytics/customer-insights", response_model=Dict[str, Any])
async def get_customer_insights(
    organization_id: str = Query(...),
    customer_segment: Optional[str] = Query(None),
    analysis_period: int = Query(12, ge=1, le=60),  # months
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive customer insights and behavior analysis.

    Features:
    - Customer lifetime value analysis
    - Churn prediction
    - Segmentation insights
    - Engagement patterns
    - Health score distribution
    - Revenue trends by segment
    """
    insights = await crm_service.get_customer_insights(
        db, organization_id, customer_segment, analysis_period
    )
    return insights


# =============================================================================
# 9. Lead Conversion Analysis Endpoints
# =============================================================================


@router.get("/analytics/lead-conversion", response_model=Dict[str, Any])
async def get_lead_conversion_analytics(
    organization_id: str = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    lead_source: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed lead conversion analytics and funnel analysis.

    Features:
    - Conversion funnel analysis
    - Source performance comparison
    - Campaign effectiveness
    - Time-to-conversion analysis
    - Cost per acquisition
    - Quality scoring trends
    """
    analytics = await crm_service.get_lead_conversion_analytics(
        db, organization_id, period_start, period_end, lead_source, campaign_id
    )
    return analytics


@router.get("/leads/{lead_id}/conversion-probability", response_model=Dict[str, Any])
async def get_lead_conversion_probability(
    lead_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calculate lead conversion probability using machine learning models.

    Features:
    - AI-powered conversion prediction
    - Factor analysis
    - Confidence intervals
    - Recommended actions
    - Historical comparison
    """
    probability = await crm_service.calculate_lead_conversion_probability(db, lead_id)
    if not probability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found or insufficient data for analysis",
        )
    return probability


# =============================================================================
# 10. Sales Pipeline Management Endpoints
# =============================================================================


@router.get("/pipeline/overview", response_model=Dict[str, Any])
async def get_pipeline_overview(
    organization_id: str = Query(...),
    sales_rep_id: Optional[str] = Query(None),
    time_period: str = Query("current_quarter"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive sales pipeline overview and management dashboard.

    Features:
    - Pipeline value by stage
    - Deal progression tracking
    - Key performance indicators
    - Risk assessment
    - Forecast accuracy
    - Action items and recommendations
    """
    overview = await crm_service.get_pipeline_overview(
        db, organization_id, sales_rep_id, time_period
    )
    return overview


@router.get("/pipeline/velocity", response_model=Dict[str, Any])
async def get_pipeline_velocity_analysis(
    organization_id: str = Query(...),
    period_months: int = Query(6, ge=1, le=24),
    stage_analysis: bool = Query(True),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get pipeline velocity analysis for sales process optimization.

    Features:
    - Average time in each stage
    - Velocity trends over time
    - Bottleneck identification
    - Stage progression rates
    - Optimization recommendations
    - Comparative analysis
    """
    velocity = await crm_service.get_pipeline_velocity_analysis(
        db, organization_id, period_months, stage_analysis
    )
    return velocity


@router.get("/pipeline/forecast-accuracy", response_model=Dict[str, Any])
async def get_forecast_accuracy_analysis(
    organization_id: str = Query(...),
    lookback_months: int = Query(12, ge=3, le=36),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Analyze forecast accuracy and prediction reliability.

    Features:
    - Historical forecast vs. actual comparison
    - Accuracy by time period
    - Accuracy by sales rep
    - Improvement recommendations
    - Confidence interval analysis
    - Trend identification
    """
    accuracy = await crm_service.get_forecast_accuracy_analysis(
        db, organization_id, lookback_months
    )
    return accuracy


@router.post("/pipeline/bulk-update", response_model=Dict[str, Any])
async def bulk_update_pipeline(
    updates: List[Dict[str, Any]], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform bulk updates on multiple opportunities in the pipeline.

    Features:
    - Bulk stage updates
    - Bulk probability adjustments
    - Bulk assignment changes
    - Validation and error handling
    - Audit trail generation
    - Performance optimization
    """
    try:
        result = await crm_service.bulk_update_opportunities(db, updates)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to perform bulk update: {str(e)}",
        )


# =============================================================================
# Health Check and System Status
# =============================================================================


@router.get("/health", response_model=Dict[str, Any])
async def crm_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    CRM system health check and status information.

    Features:
    - Database connectivity
    - Service availability
    - Performance metrics
    - System status
    - Version information
    """
    try:
        health_status = await crm_service.get_system_health(db)
        return health_status

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
