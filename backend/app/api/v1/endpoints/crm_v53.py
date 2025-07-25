"""
CC02 v53.0 CRM Management API - Issue #568
10-Day ERP Business API Implementation Sprint - Day 7-8 Phase 2
Customer Relationship Management API Endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import datetime, date, timedelta
import uuid
import asyncio
import time

from app.schemas.crm_v53 import (
    # Lead Schemas
    LeadCreate, LeadUpdate, LeadResponse,
    
    # Opportunity Schemas
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    
    # Contact Schemas
    ContactCreate, ContactResponse,
    
    # Activity Schemas
    ActivityCreate, ActivityUpdate, ActivityResponse,
    
    # Campaign Schemas
    CampaignCreate, CampaignResponse,
    
    # List Response Schemas
    LeadListResponse, OpportunityListResponse, ContactListResponse,
    ActivityListResponse, CampaignListResponse,
    
    # Statistics and Analytics
    CRMStatistics,
    
    # Bulk Operations
    BulkLeadOperation, BulkLeadResult,
    
    # Lead Conversion
    LeadConversionCreate, LeadConversionResult,
    
    # Enums
    LeadStatus, LeadSource, OpportunityStage, ActivityType, ActivityStatus,
    ContactType, CampaignType, CampaignStatus
)

# In-memory storage for rapid prototyping (same pattern as previous phases)
leads_store: Dict[str, Dict[str, Any]] = {}
opportunities_store: Dict[str, Dict[str, Any]] = {}
contacts_store: Dict[str, Dict[str, Any]] = {}
activities_store: Dict[str, Dict[str, Any]] = {}
campaigns_store: Dict[str, Dict[str, Any]] = {}

router = APIRouter()

# Dependency injection for database (placeholder)
async def get_db():
    """Database dependency placeholder for future integration"""
    return None

# Helper functions
def generate_lead_name(first_name: str, last_name: str) -> str:
    """Generate full name for lead"""
    return f"{first_name} {last_name}".strip()

def calculate_weighted_amount(amount: Decimal, probability: Decimal) -> Decimal:
    """Calculate weighted opportunity amount"""
    return amount * (probability / Decimal('100'))

def calculate_days_between(start_date: datetime, end_date: datetime = None) -> int:
    """Calculate days between dates"""
    if not end_date:
        end_date = datetime.now()
    return (end_date - start_date).days

def is_activity_overdue(due_date: datetime, status: ActivityStatus) -> bool:
    """Check if activity is overdue"""
    if status in [ActivityStatus.COMPLETED, ActivityStatus.CANCELLED]:
        return False
    return due_date < datetime.now() if due_date else False

async def background_lead_processing(lead_id: str):
    """Background task for lead processing"""
    await asyncio.sleep(0.1)  # Simulate processing delay
    
    if lead_id in leads_store:
        lead = leads_store[lead_id]
        lead['background_processed'] = True
        lead['processing_completed_at'] = datetime.now()


# Lead Management Endpoints

@router.post("/leads/", response_model=LeadResponse, status_code=201)
async def create_lead(
    lead_data: LeadCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Create new lead with comprehensive business validation"""
    start_time = time.time()
    
    # Generate unique lead ID
    lead_id = str(uuid.uuid4())
    
    # Check for duplicate email if provided
    if lead_data.email:
        for existing_lead in leads_store.values():
            if existing_lead.get('email') == lead_data.email and existing_lead.get('status') != LeadStatus.CONVERTED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Active lead with email {lead_data.email} already exists"
                )
    
    # Create lead record
    full_name = generate_lead_name(lead_data.first_name, lead_data.last_name)
    lead_record = {
        'id': lead_id,
        'first_name': lead_data.first_name,
        'last_name': lead_data.last_name,
        'full_name': full_name,
        'email': lead_data.email,
        'phone': lead_data.phone,
        'company': lead_data.company,
        'job_title': lead_data.job_title,
        'lead_source': lead_data.lead_source,
        'status': lead_data.status,
        'estimated_value': lead_data.estimated_value,
        'probability': lead_data.probability,
        'expected_close_date': lead_data.expected_close_date,
        'address': lead_data.address,
        'website': lead_data.website,
        'industry': lead_data.industry,
        'company_size': lead_data.company_size,
        'annual_revenue': lead_data.annual_revenue,
        'assigned_to': lead_data.assigned_to,
        'assigned_to_name': f"User {lead_data.assigned_to}" if lead_data.assigned_to else None,
        'campaign_id': lead_data.campaign_id,
        'campaign_name': campaigns_store.get(lead_data.campaign_id, {}).get('name') if lead_data.campaign_id else None,
        'is_converted': False,
        'converted_customer_id': None,
        'converted_opportunity_id': None,
        'conversion_date': None,
        'last_contacted': None,
        'activities_count': 0,
        'notes': lead_data.notes,
        'custom_fields': lead_data.custom_fields,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    leads_store[lead_id] = lead_record
    
    # Background processing
    background_tasks.add_task(background_lead_processing, lead_id)
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Lead creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return LeadResponse(**lead_record)


@router.get("/leads/", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[LeadStatus] = Query(None),
    lead_source: Optional[LeadSource] = Query(None),
    assigned_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> LeadListResponse:
    """List leads with comprehensive filtering"""
    start_time = time.time()
    
    # Apply filters
    filtered_leads = []
    for lead in leads_store.values():
        # Filter by status
        if status and lead.get('status') != status:
            continue
            
        # Filter by lead source
        if lead_source and lead.get('lead_source') != lead_source:
            continue
            
        # Filter by assigned user
        if assigned_to and lead.get('assigned_to') != assigned_to:
            continue
            
        # Search filter
        if search:
            search_lower = search.lower()
            if not any([
                search_lower in lead.get('full_name', '').lower(),
                search_lower in lead.get('email', '').lower(),
                search_lower in lead.get('company', '').lower()
            ]):
                continue
        
        filtered_leads.append(lead)
    
    # Sort by creation date (newest first)
    filtered_leads.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
    
    # Pagination
    total = len(filtered_leads)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_leads = filtered_leads[start_idx:end_idx]
    
    # Convert to response models
    lead_responses = [LeadResponse(**lead) for lead in paginated_leads]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Lead listing exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return LeadListResponse(
        items=lead_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied={
            'status': status,
            'lead_source': lead_source,
            'assigned_to': assigned_to,
            'search': search
        }
    )


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Get lead by ID with activity metrics"""
    start_time = time.time()
    
    if lead_id not in leads_store:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads_store[lead_id].copy()
    
    # Calculate activity metrics
    lead_activities = [activity for activity in activities_store.values() 
                      if activity.get('lead_id') == lead_id]
    
    lead['activities_count'] = len(lead_activities)
    
    # Find last contact date
    if lead_activities:
        last_activity = max(lead_activities, key=lambda x: x.get('created_at', datetime.min))
        lead['last_contacted'] = last_activity.get('created_at')
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Lead retrieval exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return LeadResponse(**lead)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_update: LeadUpdate,
    db: AsyncSession = Depends(get_db)
) -> LeadResponse:
    """Update lead with validation"""
    start_time = time.time()
    
    if lead_id not in leads_store:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads_store[lead_id]
    
    # Update fields
    update_data = lead_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            lead[field] = value
    
    # Update full name if name fields changed
    if 'first_name' in update_data or 'last_name' in update_data:
        lead['full_name'] = generate_lead_name(lead['first_name'], lead['last_name'])
    
    lead['updated_at'] = datetime.now()
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Lead update exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return LeadResponse(**lead)


@router.post("/leads/{lead_id}/convert", response_model=LeadConversionResult)
async def convert_lead(
    lead_id: str,
    conversion_data: LeadConversionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> LeadConversionResult:
    """Convert lead to customer/opportunity/contact"""
    start_time = time.time()
    
    if lead_id not in leads_store:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads_store[lead_id]
    
    if lead.get('is_converted'):
        raise HTTPException(status_code=400, detail="Lead already converted")
    
    result = LeadConversionResult(
        lead_id=lead_id,
        conversion_date=datetime.now(),
        notes=conversion_data.conversion_notes
    )
    
    # Create customer if requested
    if conversion_data.create_customer:
        customer_id = str(uuid.uuid4())
        # This would integrate with the sales API's customer creation
        result.customer_id = customer_id
    
    # Create opportunity if requested
    if conversion_data.create_opportunity:
        opportunity_id = str(uuid.uuid4())
        opportunity_record = {
            'id': opportunity_id,
            'name': conversion_data.opportunity_name or f"Opportunity from {lead['full_name']}",
            'customer_id': result.customer_id,
            'lead_id': lead_id,
            'stage': conversion_data.opportunity_stage,
            'amount': conversion_data.opportunity_amount or lead.get('estimated_value', Decimal('0')),
            'probability': lead.get('probability', Decimal('50')),
            'expected_close_date': conversion_data.opportunity_close_date or lead.get('expected_close_date'),
            'actual_close_date': None,
            'lead_source': lead.get('lead_source'),
            'assigned_to': lead.get('assigned_to'),
            'campaign_id': lead.get('campaign_id'),
            'next_step': 'Follow up on converted lead',
            'is_won': False,
            'is_lost': False,
            'activities_count': 0,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        opportunity_record['weighted_amount'] = calculate_weighted_amount(
            opportunity_record['amount'], opportunity_record['probability']
        )
        opportunity_record['days_in_stage'] = 0
        opportunity_record['age_days'] = 0
        
        opportunities_store[opportunity_id] = opportunity_record
        result.opportunity_id = opportunity_id
    
    # Create contact if requested
    if conversion_data.create_contact:
        contact_id = str(uuid.uuid4())
        # This would create a contact record
        result.contact_id = contact_id
    
    # Mark lead as converted
    lead['is_converted'] = True
    lead['status'] = LeadStatus.CONVERTED
    lead['converted_customer_id'] = result.customer_id
    lead['converted_opportunity_id'] = result.opportunity_id
    lead['conversion_date'] = result.conversion_date
    lead['updated_at'] = datetime.now()
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Lead conversion exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return result


# Opportunity Management Endpoints

@router.post("/opportunities/", response_model=OpportunityResponse, status_code=201)
async def create_opportunity(
    opportunity_data: OpportunityCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> OpportunityResponse:
    """Create new opportunity"""
    start_time = time.time()
    
    # Generate unique opportunity ID
    opportunity_id = str(uuid.uuid4())
    
    # Create opportunity record
    opportunity_record = {
        'id': opportunity_id,
        'name': opportunity_data.name,
        'customer_id': opportunity_data.customer_id,
        'customer_name': f"Customer {opportunity_data.customer_id}" if opportunity_data.customer_id else None,
        'lead_id': opportunity_data.lead_id,
        'lead_name': leads_store.get(opportunity_data.lead_id, {}).get('full_name') if opportunity_data.lead_id else None,
        'stage': opportunity_data.stage,
        'amount': opportunity_data.amount,
        'probability': opportunity_data.probability,
        'expected_close_date': opportunity_data.expected_close_date,
        'actual_close_date': opportunity_data.actual_close_date,
        'lead_source': opportunity_data.lead_source,
        'assigned_to': opportunity_data.assigned_to,
        'assigned_to_name': f"User {opportunity_data.assigned_to}" if opportunity_data.assigned_to else None,
        'campaign_id': opportunity_data.campaign_id,
        'campaign_name': campaigns_store.get(opportunity_data.campaign_id, {}).get('name') if opportunity_data.campaign_id else None,
        'competitor': opportunity_data.competitor,
        'next_step': opportunity_data.next_step,
        'description': opportunity_data.description,
        'loss_reason': opportunity_data.loss_reason,
        'is_won': opportunity_data.stage == OpportunityStage.CLOSED_WON,
        'is_lost': opportunity_data.stage == OpportunityStage.CLOSED_LOST,
        'activities_count': 0,
        'last_activity_date': None,
        'custom_fields': opportunity_data.custom_fields,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    # Calculate derived fields
    opportunity_record['weighted_amount'] = calculate_weighted_amount(
        opportunity_record['amount'], opportunity_record['probability']
    )
    opportunity_record['days_in_stage'] = 0
    opportunity_record['age_days'] = 0
    
    opportunities_store[opportunity_id] = opportunity_record
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Opportunity creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return OpportunityResponse(**opportunity_record)


@router.get("/opportunities/", response_model=OpportunityListResponse)
async def list_opportunities(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    stage: Optional[OpportunityStage] = Query(None),
    assigned_to: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    min_amount: Optional[Decimal] = Query(None, ge=0),
    max_amount: Optional[Decimal] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db)
) -> OpportunityListResponse:
    """List opportunities with comprehensive filtering"""
    start_time = time.time()
    
    # Apply filters
    filtered_opportunities = []
    for opportunity in opportunities_store.values():
        # Filter by stage
        if stage and opportunity.get('stage') != stage:
            continue
            
        # Filter by assigned user
        if assigned_to and opportunity.get('assigned_to') != assigned_to:
            continue
            
        # Filter by customer
        if customer_id and opportunity.get('customer_id') != customer_id:
            continue
            
        # Filter by amount range
        amount = opportunity.get('amount', Decimal('0'))
        if min_amount and amount < min_amount:
            continue
        if max_amount and amount > max_amount:
            continue
        
        filtered_opportunities.append(opportunity)
    
    # Sort by amount (highest first)
    filtered_opportunities.sort(key=lambda x: x.get('amount', Decimal('0')), reverse=True)
    
    # Pagination
    total = len(filtered_opportunities)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_opportunities = filtered_opportunities[start_idx:end_idx]
    
    # Convert to response models
    opportunity_responses = [OpportunityResponse(**opp) for opp in paginated_opportunities]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Opportunity listing exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return OpportunityListResponse(
        items=opportunity_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied={
            'stage': stage,
            'assigned_to': assigned_to,
            'customer_id': customer_id,
            'min_amount': min_amount,
            'max_amount': max_amount
        }
    )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db)
) -> OpportunityResponse:
    """Get opportunity by ID with activity metrics"""
    start_time = time.time()
    
    if opportunity_id not in opportunities_store:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opportunity = opportunities_store[opportunity_id].copy()
    
    # Calculate activity metrics
    opp_activities = [activity for activity in activities_store.values() 
                     if activity.get('opportunity_id') == opportunity_id]
    
    opportunity['activities_count'] = len(opp_activities)
    
    # Find last activity date
    if opp_activities:
        last_activity = max(opp_activities, key=lambda x: x.get('created_at', datetime.min))
        opportunity['last_activity_date'] = last_activity.get('created_at')
    
    # Calculate age and stage metrics
    created_at = opportunity.get('created_at', datetime.now())
    opportunity['age_days'] = calculate_days_between(created_at)
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Opportunity retrieval exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return OpportunityResponse(**opportunity)


# Activity Management Endpoints

@router.post("/activities/", response_model=ActivityResponse, status_code=201)
async def create_activity(
    activity_data: ActivityCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> ActivityResponse:
    """Create new activity"""
    start_time = time.time()
    
    # Generate unique activity ID
    activity_id = str(uuid.uuid4())
    
    # Create activity record
    activity_record = {
        'id': activity_id,
        'subject': activity_data.subject,
        'activity_type': activity_data.activity_type,
        'status': activity_data.status,
        'priority': activity_data.priority,
        'due_date': activity_data.due_date,
        'duration_minutes': activity_data.duration_minutes,
        'customer_id': activity_data.customer_id,
        'customer_name': f"Customer {activity_data.customer_id}" if activity_data.customer_id else None,
        'lead_id': activity_data.lead_id,
        'lead_name': leads_store.get(activity_data.lead_id, {}).get('full_name') if activity_data.lead_id else None,
        'opportunity_id': activity_data.opportunity_id,
        'opportunity_name': opportunities_store.get(activity_data.opportunity_id, {}).get('name') if activity_data.opportunity_id else None,
        'contact_id': activity_data.contact_id,
        'contact_name': contacts_store.get(activity_data.contact_id, {}).get('full_name') if activity_data.contact_id else None,
        'assigned_to': activity_data.assigned_to,
        'assigned_to_name': f"User {activity_data.assigned_to}" if activity_data.assigned_to else None,
        'created_by': activity_data.created_by,
        'created_by_name': f"User {activity_data.created_by}" if activity_data.created_by else None,
        'description': activity_data.description,
        'location': activity_data.location,
        'outcome': activity_data.outcome,
        'follow_up_required': activity_data.follow_up_required,
        'follow_up_date': activity_data.follow_up_date,
        'call_result': activity_data.call_result,
        'email_subject': activity_data.email_subject,
        'meeting_attendees': activity_data.meeting_attendees,
        'completed_date': None,
        'completed_by': None,
        'custom_fields': activity_data.custom_fields,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    # Calculate derived fields
    activity_record['is_overdue'] = is_activity_overdue(
        activity_data.due_date, activity_data.status
    ) if activity_data.due_date else False
    
    activities_store[activity_id] = activity_record
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Activity creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return ActivityResponse(**activity_record)


@router.get("/activities/", response_model=ActivityListResponse)
async def list_activities(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    activity_type: Optional[ActivityType] = Query(None),
    status: Optional[ActivityStatus] = Query(None),
    assigned_to: Optional[str] = Query(None),
    overdue_only: Optional[bool] = Query(False),
    db: AsyncSession = Depends(get_db)
) -> ActivityListResponse:
    """List activities with comprehensive filtering"""
    start_time = time.time()
    
    # Apply filters
    filtered_activities = []
    for activity in activities_store.values():
        # Filter by activity type
        if activity_type and activity.get('activity_type') != activity_type:
            continue
            
        # Filter by status
        if status and activity.get('status') != status:
            continue
            
        # Filter by assigned user
        if assigned_to and activity.get('assigned_to') != assigned_to:
            continue
            
        # Filter overdue activities
        if overdue_only and not activity.get('is_overdue', False):
            continue
        
        filtered_activities.append(activity)
    
    # Sort by due date (soonest first)
    filtered_activities.sort(key=lambda x: x.get('due_date') or datetime.max)
    
    # Pagination
    total = len(filtered_activities)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_activities = filtered_activities[start_idx:end_idx]
    
    # Convert to response models
    activity_responses = [ActivityResponse(**activity) for activity in paginated_activities]
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Activity listing exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return ActivityListResponse(
        items=activity_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied={
            'activity_type': activity_type,
            'status': status,
            'assigned_to': assigned_to,
            'overdue_only': overdue_only
        }
    )


# Campaign Management Endpoints

@router.post("/campaigns/", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    campaign_data: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> CampaignResponse:
    """Create new campaign"""
    start_time = time.time()
    
    # Generate unique campaign ID
    campaign_id = str(uuid.uuid4())
    
    # Create campaign record
    campaign_record = {
        'id': campaign_id,
        'name': campaign_data.name,
        'campaign_type': campaign_data.campaign_type,
        'status': campaign_data.status,
        'start_date': campaign_data.start_date,
        'end_date': campaign_data.end_date,
        'budget': campaign_data.budget,
        'expected_revenue': campaign_data.expected_revenue,
        'actual_cost': Decimal('0'),
        'actual_revenue': Decimal('0'),
        'roi': None,
        'leads_generated': 0,
        'opportunities_created': 0,
        'deals_won': 0,
        'conversion_rate': None,
        'target_audience': campaign_data.target_audience,
        'description': campaign_data.description,
        'owner': campaign_data.owner,
        'owner_name': f"User {campaign_data.owner}" if campaign_data.owner else None,
        'is_active': campaign_data.status == CampaignStatus.ACTIVE,
        'is_completed': campaign_data.status == CampaignStatus.COMPLETED,
        'days_remaining': None,
        'custom_fields': campaign_data.custom_fields,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    # Calculate days remaining if end date is set
    if campaign_data.end_date:
        campaign_record['days_remaining'] = calculate_days_between(datetime.now(), 
                                                                  datetime.combine(campaign_data.end_date, datetime.min.time()))
    
    campaigns_store[campaign_id] = campaign_record
    
    # Performance check
    execution_time = (time.time() - start_time) * 1000
    if execution_time > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Campaign creation exceeded 200ms limit: {execution_time:.2f}ms"
        )
    
    return CampaignResponse(**campaign_record)


# CRM Statistics and Analytics

@router.get("/statistics", response_model=CRMStatistics)
async def get_crm_statistics(
    db: AsyncSession = Depends(get_db)
) -> CRMStatistics:
    """Get comprehensive CRM statistics"""
    start_time = time.time()
    
    # Lead Statistics
    total_leads = len(leads_store)
    new_leads = sum(1 for lead in leads_store.values() if lead.get('status') == LeadStatus.NEW)
    qualified_leads = sum(1 for lead in leads_store.values() if lead.get('status') == LeadStatus.QUALIFIED)
    converted_leads = sum(1 for lead in leads_store.values() if lead.get('status') == LeadStatus.CONVERTED)
    lead_conversion_rate = (converted_leads / max(total_leads, 1)) * 100
    
    # Opportunity Statistics
    total_opportunities = len(opportunities_store)
    open_opportunities = sum(1 for opp in opportunities_store.values() 
                           if opp.get('stage') not in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST])
    won_opportunities = sum(1 for opp in opportunities_store.values() if opp.get('is_won'))
    lost_opportunities = sum(1 for opp in opportunities_store.values() if opp.get('is_lost'))
    opportunity_win_rate = (won_opportunities / max(total_opportunities, 1)) * 100
    
    # Calculate financial metrics
    total_pipeline_value = sum(Decimal(str(opp.get('amount', 0))) 
                              for opp in opportunities_store.values())
    weighted_pipeline_value = sum(Decimal(str(opp.get('weighted_amount', 0))) 
                                 for opp in opportunities_store.values())
    average_deal_size = total_pipeline_value / max(total_opportunities, 1)
    
    # Activity Statistics
    total_activities = len(activities_store)
    completed_activities = sum(1 for activity in activities_store.values() 
                             if activity.get('status') == ActivityStatus.COMPLETED)
    overdue_activities = sum(1 for activity in activities_store.values() 
                           if activity.get('is_overdue'))
    activities_this_week = sum(1 for activity in activities_store.values() 
                             if activity.get('created_at', datetime.min) > datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=7))
    activity_completion_rate = (completed_activities / max(total_activities, 1)) * 100
    
    # Contact Statistics
    total_contacts = len(contacts_store)
    decision_makers_count = sum(1 for contact in contacts_store.values() 
                               if contact.get('is_decision_maker'))
    primary_contacts_count = sum(1 for contact in contacts_store.values() 
                               if contact.get('is_primary'))
    contacts_with_activities = len(set(activity.get('contact_id') for activity in activities_store.values() 
                                     if activity.get('contact_id')))
    
    # Campaign Statistics
    active_campaigns = sum(1 for campaign in campaigns_store.values() 
                         if campaign.get('is_active'))
    total_campaigns = len(campaigns_store)
    campaign_roi = Decimal('0')  # Placeholder for ROI calculation
    leads_from_campaigns = sum(1 for lead in leads_store.values() 
                             if lead.get('campaign_id'))
    
    # Analysis by categories
    leads_by_source = {}
    for source in LeadSource:
        leads_by_source[source.value] = sum(1 for lead in leads_store.values() 
                                          if lead.get('lead_source') == source)
    
    opportunities_by_stage = {}
    for stage in OpportunityStage:
        opportunities_by_stage[stage.value] = sum(1 for opp in opportunities_store.values() 
                                                if opp.get('stage') == stage)
    
    activities_by_type = {}
    for activity_type in ActivityType:
        activities_by_type[activity_type.value] = sum(1 for activity in activities_store.values() 
                                                    if activity.get('activity_type') == activity_type)
    
    # Performance metrics
    calculation_time_ms = (time.time() - start_time) * 1000
    
    # Performance check
    if calculation_time_ms > 200:
        raise HTTPException(
            status_code=500,
            detail=f"Statistics calculation exceeded 200ms limit: {calculation_time_ms:.2f}ms"
        )
    
    return CRMStatistics(
        total_leads=total_leads,
        new_leads=new_leads,
        qualified_leads=qualified_leads,
        converted_leads=converted_leads,
        lead_conversion_rate=Decimal(str(lead_conversion_rate)),
        
        total_opportunities=total_opportunities,
        open_opportunities=open_opportunities,
        won_opportunities=won_opportunities,
        lost_opportunities=lost_opportunities,
        opportunity_win_rate=Decimal(str(opportunity_win_rate)),
        average_deal_size=average_deal_size,
        total_pipeline_value=total_pipeline_value,
        weighted_pipeline_value=weighted_pipeline_value,
        
        total_activities=total_activities,
        completed_activities=completed_activities,
        overdue_activities=overdue_activities,
        activities_this_week=activities_this_week,
        activity_completion_rate=Decimal(str(activity_completion_rate)),
        
        total_contacts=total_contacts,
        decision_makers_count=decision_makers_count,
        primary_contacts_count=primary_contacts_count,
        contacts_with_activities=contacts_with_activities,
        
        active_campaigns=active_campaigns,
        total_campaigns=total_campaigns,
        campaign_roi=campaign_roi,
        leads_from_campaigns=leads_from_campaigns,
        
        sales_cycle_days=None,
        activities_per_opportunity=Decimal(str(total_activities / max(total_opportunities, 1))),
        follow_up_response_rate=Decimal('75.0'),  # Placeholder
        
        leads_by_source=leads_by_source,
        opportunities_by_stage=opportunities_by_stage,
        activities_by_type=activities_by_type,
        monthly_performance={},  # Placeholder
        top_performers=[],  # Placeholder
        team_metrics={},  # Placeholder
        
        last_updated=datetime.now(),
        calculation_time_ms=calculation_time_ms
    )


# Bulk Operations

@router.post("/leads/bulk", response_model=BulkLeadResult)
async def bulk_create_leads(
    bulk_operation: BulkLeadOperation,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> BulkLeadResult:
    """Bulk create leads"""
    start_time = time.time()
    
    result = BulkLeadResult()
    
    for lead_data in bulk_operation.leads:
        try:
            # Apply defaults from bulk operation
            if bulk_operation.assign_to:
                lead_data.assigned_to = bulk_operation.assign_to
            if bulk_operation.default_campaign_id:
                lead_data.campaign_id = bulk_operation.default_campaign_id
            
            if bulk_operation.validate_only:
                # Just validate the schema
                LeadCreate(**lead_data.model_dump())
                result.created_count += 1
            else:
                # Create the lead
                lead_response = await create_lead(lead_data, background_tasks, db)
                result.created_items.append(lead_response)
                result.created_count += 1
                
        except Exception as e:
            result.failed_count += 1
            result.failed_items.append({
                'error': str(e),
                'lead_data': lead_data.model_dump() if hasattr(lead_data, 'model_dump') else str(lead_data)
            })
            
            if bulk_operation.stop_on_error:
                break
    
    result.execution_time_ms = (time.time() - start_time) * 1000
    return result


# Health Check Endpoint
@router.get("/health")
async def crm_health_check():
    """Health check for CRM API"""
    return {
        "status": "healthy",
        "service": "CRM Management API v53.0",
        "leads_count": len(leads_store),
        "opportunities_count": len(opportunities_store),
        "contacts_count": len(contacts_store),
        "activities_count": len(activities_store),
        "campaigns_count": len(campaigns_store),
        "timestamp": datetime.now()
    }