from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.crud.crm_extended_v30 import (
    CRMCustomerCRUD,
    CustomerActivityCRUD,
    CustomerInteractionCRUD,
    CustomerSegmentCRUD,
    DuplicateError,
    InvalidStageError,
    MarketingCampaignCRUD,
    NotFoundError,
    OpportunityActivityCRUD,
    SalesOpportunityCRUD,
)
from app.schemas.crm_complete_v30 import (
    CRMAnalyticsResponse,
    CRMCustomerCreate,
    CRMCustomerListResponse,
    CRMCustomerResponse,
    CRMCustomerUpdate,
    CRMStatsResponse,
    CustomerActivityCreate,
    CustomerActivityResponse,
    CustomerInteractionCreate,
    CustomerInteractionListResponse,
    CustomerInteractionResponse,
    CustomerInteractionUpdate,
    CustomerSegmentCreate,
    CustomerSegmentResponse,
    CustomerSegmentUpdate,
    MarketingCampaignCreate,
    MarketingCampaignResponse,
    MarketingCampaignUpdate,
    OpportunityActivityCreate,
    OpportunityActivityResponse,
    SalesOpportunityCreate,
    SalesOpportunityListResponse,
    SalesOpportunityResponse,
    SalesOpportunityUpdate,
)

router = APIRouter(prefix="/crm", tags=["crm"])


@router.post(
    "/customers",
    response_model=CRMCustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crm_customer(
    customer: CRMCustomerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """CRM顧客作成"""
    try:
        customer_crud = CRMCustomerCRUD(db)
        return customer_crud.create(customer)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/customers/{customer_id}", response_model=CRMCustomerResponse)
def get_crm_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """CRM顧客詳細取得"""
    customer_crud = CRMCustomerCRUD(db)
    customer = customer_crud.get_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return customer


@router.get("/customers", response_model=CRMCustomerListResponse)
def list_crm_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    is_qualified: Optional[bool] = None,
    is_vip: Optional[bool] = None,
    customer_type: Optional[str] = None,
    customer_segment: Optional[str] = None,
    lead_status: Optional[str] = None,
    customer_stage: Optional[str] = None,
    lifecycle_stage: Optional[str] = None,
    assigned_sales_rep: Optional[str] = None,
    assigned_account_manager: Optional[str] = None,
    lead_source: Optional[str] = None,
    industry: Optional[str] = None,
    company_size: Optional[str] = None,
    do_not_contact: Optional[bool] = None,
    marketing_opt_in: Optional[bool] = None,
    lead_score_min: Optional[int] = None,
    lead_score_max: Optional[int] = None,
    engagement_score_min: Optional[int] = None,
    lifetime_value_min: Optional[Decimal] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    last_activity_from: Optional[datetime] = None,
    last_activity_to: Optional[datetime] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """CRM顧客一覧取得"""
    skip = (page - 1) * per_page
    filters = {}

    # Build filters dictionary
    filter_params = {
        "is_active": is_active,
        "is_qualified": is_qualified,
        "is_vip": is_vip,
        "customer_type": customer_type,
        "customer_segment": customer_segment,
        "lead_status": lead_status,
        "customer_stage": customer_stage,
        "lifecycle_stage": lifecycle_stage,
        "assigned_sales_rep": assigned_sales_rep,
        "assigned_account_manager": assigned_account_manager,
        "lead_source": lead_source,
        "industry": industry,
        "company_size": company_size,
        "do_not_contact": do_not_contact,
        "marketing_opt_in": marketing_opt_in,
        "lead_score_min": lead_score_min,
        "lead_score_max": lead_score_max,
        "engagement_score_min": engagement_score_min,
        "lifetime_value_min": lifetime_value_min,
        "created_from": created_from,
        "created_to": created_to,
        "last_activity_from": last_activity_from,
        "last_activity_to": last_activity_to,
        "search": search,
        "tags": tags,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    customer_crud = CRMCustomerCRUD(db)
    customers, total = customer_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return CRMCustomerListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=customers
    )


@router.put("/customers/{customer_id}", response_model=CRMCustomerResponse)
def update_crm_customer(
    customer_id: str,
    customer_update: CRMCustomerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """CRM顧客情報更新"""
    try:
        customer_crud = CRMCustomerCRUD(db)
        return customer_crud.update(customer_id, customer_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/customers/{customer_id}/segments/{segment_id}/add")
def add_customer_to_segment(
    customer_id: str,
    segment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客をセグメントに追加"""
    customer_crud = CRMCustomerCRUD(db)
    customer_crud.add_to_segment(customer_id, segment_id, current_user["sub"])
    return {"message": "Customer added to segment successfully"}


@router.post("/customers/{customer_id}/segments/{segment_id}/remove")
def remove_customer_from_segment(
    customer_id: str,
    segment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客をセグメントから削除"""
    customer_crud = CRMCustomerCRUD(db)
    customer_crud.remove_from_segment(customer_id, segment_id)
    return {"message": "Customer removed from segment successfully"}


@router.post(
    "/interactions",
    response_model=CustomerInteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_interaction(
    interaction: CustomerInteractionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客インタラクション作成"""
    interaction_crud = CustomerInteractionCRUD(db)
    return interaction_crud.create(interaction, current_user["sub"])


@router.get(
    "/interactions/{interaction_id}", response_model=CustomerInteractionResponse
)
def get_customer_interaction(
    interaction_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客インタラクション詳細取得"""
    interaction_crud = CustomerInteractionCRUD(db)
    interaction = interaction_crud.get_by_id(interaction_id)
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found"
        )
    return interaction


@router.get(
    "/customers/{customer_id}/interactions",
    response_model=CustomerInteractionListResponse,
)
def list_customer_interactions(
    customer_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客インタラクション一覧取得"""
    skip = (page - 1) * per_page
    interaction_crud = CustomerInteractionCRUD(db)
    interactions, total = interaction_crud.get_multi_by_customer(
        customer_id, skip=skip, limit=per_page
    )

    pages = (total + per_page - 1) // per_page

    return CustomerInteractionListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=interactions
    )


@router.put(
    "/interactions/{interaction_id}", response_model=CustomerInteractionResponse
)
def update_customer_interaction(
    interaction_id: str,
    interaction_update: CustomerInteractionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客インタラクション更新"""
    try:
        interaction_crud = CustomerInteractionCRUD(db)
        return interaction_crud.update(interaction_id, interaction_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/opportunities",
    response_model=SalesOpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sales_opportunity(
    opportunity: SalesOpportunityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """営業機会作成"""
    opportunity_crud = SalesOpportunityCRUD(db)
    return opportunity_crud.create(opportunity, current_user["sub"])


@router.get("/opportunities/{opportunity_id}", response_model=SalesOpportunityResponse)
def get_sales_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """営業機会詳細取得"""
    opportunity_crud = SalesOpportunityCRUD(db)
    opportunity = opportunity_crud.get_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opportunity


@router.get("/opportunities", response_model=SalesOpportunityListResponse)
def list_sales_opportunities(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    customer_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    product_category: Optional[str] = None,
    amount_min: Optional[Decimal] = None,
    amount_max: Optional[Decimal] = None,
    probability_min: Optional[int] = None,
    expected_close_from: Optional[date] = None,
    expected_close_to: Optional[date] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """営業機会一覧取得"""
    skip = (page - 1) * per_page
    filters = {}

    filter_params = {
        "customer_id": customer_id,
        "owner_id": owner_id,
        "stage": stage,
        "status": status,
        "source": source,
        "product_category": product_category,
        "amount_min": amount_min,
        "amount_max": amount_max,
        "probability_min": probability_min,
        "expected_close_from": expected_close_from,
        "expected_close_to": expected_close_to,
        "created_from": created_from,
        "created_to": created_to,
    }

    for key, value in filter_params.items():
        if value is not None:
            filters[key] = value

    opportunity_crud = SalesOpportunityCRUD(db)
    opportunities, total = opportunity_crud.get_multi(
        skip=skip, limit=per_page, filters=filters
    )

    pages = (total + per_page - 1) // per_page

    return SalesOpportunityListResponse(
        total=total, page=page, per_page=per_page, pages=pages, items=opportunities
    )


@router.put("/opportunities/{opportunity_id}", response_model=SalesOpportunityResponse)
def update_sales_opportunity(
    opportunity_id: str,
    opportunity_update: SalesOpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """営業機会更新"""
    try:
        opportunity_crud = SalesOpportunityCRUD(db)
        return opportunity_crud.update(opportunity_id, opportunity_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/pipeline/analytics")
def get_pipeline_analytics(
    owner_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """パイプライン分析データ取得"""
    filters = {}
    if owner_id:
        filters["owner_id"] = owner_id
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    opportunity_crud = SalesOpportunityCRUD(db)
    return opportunity_crud.get_pipeline_analytics(filters)


@router.post(
    "/activities/opportunities",
    response_model=OpportunityActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_opportunity_activity(
    activity: OpportunityActivityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """営業機会活動作成"""
    activity_crud = OpportunityActivityCRUD(db)
    return activity_crud.create(activity, current_user["sub"])


@router.post(
    "/activities/customers",
    response_model=CustomerActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_activity(
    activity: CustomerActivityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客活動記録作成"""
    activity_crud = CustomerActivityCRUD(db)
    return activity_crud.create(activity, current_user["sub"])


@router.post(
    "/segments",
    response_model=CustomerSegmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_segment(
    segment: CustomerSegmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客セグメント作成"""
    try:
        segment_crud = CustomerSegmentCRUD(db)
        return segment_crud.create(segment, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/segments/{segment_id}", response_model=CustomerSegmentResponse)
def get_customer_segment(
    segment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客セグメント詳細取得"""
    segment_crud = CustomerSegmentCRUD(db)
    segment = segment_crud.get_by_id(segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found"
        )
    return segment


@router.put("/segments/{segment_id}", response_model=CustomerSegmentResponse)
def update_customer_segment(
    segment_id: str,
    segment_update: CustomerSegmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """顧客セグメント更新"""
    try:
        segment_crud = CustomerSegmentCRUD(db)
        return segment_crud.update(segment_id, segment_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/segments/{segment_id}/calculate")
def calculate_segment_metrics(
    segment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """セグメントメトリクス再計算"""
    segment_crud = CustomerSegmentCRUD(db)
    segment_crud.calculate_segment_metrics(segment_id)
    return {"message": "Segment metrics calculated successfully"}


@router.post(
    "/campaigns",
    response_model=MarketingCampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_marketing_campaign(
    campaign: MarketingCampaignCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """マーケティングキャンペーン作成"""
    try:
        campaign_crud = MarketingCampaignCRUD(db)
        return campaign_crud.create(campaign, current_user["sub"])
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/campaigns/{campaign_id}", response_model=MarketingCampaignResponse)
def get_marketing_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """マーケティングキャンペーン詳細取得"""
    campaign_crud = MarketingCampaignCRUD(db)
    campaign = campaign_crud.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
        )
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=MarketingCampaignResponse)
def update_marketing_campaign(
    campaign_id: str,
    campaign_update: MarketingCampaignUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """マーケティングキャンペーン更新"""
    try:
        campaign_crud = MarketingCampaignCRUD(db)
        return campaign_crud.update(campaign_id, campaign_update)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stats", response_model=CRMStatsResponse)
def get_crm_stats(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """CRM統計取得"""
    from sqlalchemy import func

    from app.models.crm_extended import CRMCustomer, SalesOpportunity

    # 基本統計
    total_customers = db.query(CRMCustomer).count()
    active_customers = (
        db.query(CRMCustomer).filter(CRMCustomer.is_active == True).count()
    )
    qualified_leads = (
        db.query(CRMCustomer).filter(CRMCustomer.is_qualified == True).count()
    )

    total_opportunities = db.query(SalesOpportunity).count()
    open_opportunities = (
        db.query(SalesOpportunity).filter(SalesOpportunity.status == "open").count()
    )

    # Pipeline metrics
    pipeline_query = db.query(SalesOpportunity).filter(
        SalesOpportunity.status == "open"
    )
    total_pipeline_value = pipeline_query.with_entities(
        func.sum(SalesOpportunity.amount)
    ).scalar() or Decimal("0")
    weighted_pipeline_value = pipeline_query.with_entities(
        func.sum(SalesOpportunity.weighted_amount)
    ).scalar() or Decimal("0")

    avg_deal_size = (
        total_pipeline_value / open_opportunities
        if open_opportunities > 0
        else Decimal("0")
    )

    # Win rate calculation
    closed_opportunities = (
        db.query(SalesOpportunity)
        .filter(SalesOpportunity.status.in_(["won", "lost"]))
        .count()
    )
    won_opportunities = (
        db.query(SalesOpportunity).filter(SalesOpportunity.status == "won").count()
    )
    win_rate = (
        (won_opportunities / closed_opportunities * 100)
        if closed_opportunities > 0
        else Decimal("0")
    )

    # Average sales cycle (dummy calculation)
    avg_sales_cycle = 45  # days

    # Stage breakdown
    stage_stats = (
        db.query(SalesOpportunity.stage, func.count(SalesOpportunity.id))
        .filter(SalesOpportunity.status == "open")
        .group_by(SalesOpportunity.stage)
        .all()
    )
    by_stage = {stage: count for stage, count in stage_stats}

    # Source breakdown
    source_stats = (
        db.query(CRMCustomer.lead_source, func.count(CRMCustomer.id))
        .filter(CRMCustomer.lead_source.isnot(None))
        .group_by(CRMCustomer.lead_source)
        .all()
    )
    by_source = {source: count for source, count in source_stats}

    # Segment breakdown
    segment_stats = (
        db.query(CRMCustomer.customer_segment, func.sum(CRMCustomer.lifetime_value))
        .filter(CRMCustomer.customer_segment.isnot(None))
        .group_by(CRMCustomer.customer_segment)
        .all()
    )
    by_segment = {segment: value for segment, value in segment_stats}

    # Top performers (opportunity owners)
    top_performers = (
        db.query(
            SalesOpportunity.owner_id,
            func.sum(SalesOpportunity.amount).label("total_value"),
            func.count(SalesOpportunity.id).label("opportunity_count"),
        )
        .filter(SalesOpportunity.status == "open")
        .group_by(SalesOpportunity.owner_id)
        .order_by(func.sum(SalesOpportunity.amount).desc())
        .limit(5)
        .all()
    )

    top_performers_data = [
        {
            "owner_id": owner_id,
            "total_pipeline_value": total_value,
            "opportunity_count": opp_count,
        }
        for owner_id, total_value, opp_count in top_performers
    ]

    return CRMStatsResponse(
        total_customers=total_customers,
        active_customers=active_customers,
        qualified_leads=qualified_leads,
        total_opportunities=total_opportunities,
        open_opportunities=open_opportunities,
        total_pipeline_value=total_pipeline_value,
        weighted_pipeline_value=weighted_pipeline_value,
        avg_deal_size=avg_deal_size,
        win_rate=win_rate,
        avg_sales_cycle=avg_sales_cycle,
        by_stage=by_stage,
        by_source=by_source,
        by_segment=by_segment,
        top_performers=top_performers_data,
    )


@router.get("/analytics", response_model=CRMAnalyticsResponse)
def get_crm_analytics(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """CRM分析データ取得"""
    from sqlalchemy import func

    from app.models.crm_extended import CRMCustomer, SalesOpportunity

    # Period metrics
    customer_query = db.query(CRMCustomer).filter(
        CRMCustomer.created_at >= date_from, CRMCustomer.created_at <= date_to
    )
    new_customers = customer_query.count()
    qualified_leads = customer_query.filter(CRMCustomer.is_qualified == True).count()

    opp_query = db.query(SalesOpportunity).filter(
        SalesOpportunity.created_at >= date_from, SalesOpportunity.created_at <= date_to
    )
    opportunities_created = opp_query.count()
    deals_won = opp_query.filter(SalesOpportunity.status == "won").count()
    deals_lost = opp_query.filter(SalesOpportunity.status == "lost").count()

    # Revenue
    revenue_generated = opp_query.filter(
        SalesOpportunity.status == "won"
    ).with_entities(func.sum(SalesOpportunity.amount)).scalar() or Decimal("0")

    # Metrics calculations
    pipeline_velocity = Decimal("0")  # days - would need more complex calculation
    lead_conversion_rate = (
        (qualified_leads / new_customers * 100) if new_customers > 0 else Decimal("0")
    )
    opportunity_win_rate = (
        (deals_won / (deals_won + deals_lost) * 100)
        if (deals_won + deals_lost) > 0
        else Decimal("0")
    )

    won_opportunities = opp_query.filter(SalesOpportunity.status == "won").all()
    avg_deal_size = (
        revenue_generated / len(won_opportunities)
        if won_opportunities
        else Decimal("0")
    )

    customer_acquisition_cost = Decimal("0")  # would need campaign cost data
    lifetime_value = db.query(func.avg(CRMCustomer.lifetime_value)).scalar() or Decimal(
        "0"
    )

    # Daily breakdown
    daily_breakdown = []
    current_date = date_from.date()
    end_date = date_to.date()

    while current_date <= end_date:
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = datetime.combine(current_date, datetime.max.time())

        day_customers = (
            db.query(CRMCustomer)
            .filter(
                CRMCustomer.created_at >= day_start, CRMCustomer.created_at <= day_end
            )
            .count()
        )

        day_opportunities = (
            db.query(SalesOpportunity)
            .filter(
                SalesOpportunity.created_at >= day_start,
                SalesOpportunity.created_at <= day_end,
            )
            .count()
        )

        day_revenue = db.query(func.sum(SalesOpportunity.amount)).filter(
            SalesOpportunity.actual_close_date == current_date,
            SalesOpportunity.status == "won",
        ).scalar() or Decimal("0")

        daily_breakdown.append(
            {
                "date": current_date.isoformat(),
                "new_customers": day_customers,
                "opportunities_created": day_opportunities,
                "revenue": day_revenue,
            }
        )

        current_date += timedelta(days=1)

    # Performance by rep
    performance_by_rep = (
        db.query(
            SalesOpportunity.owner_id,
            func.count(case([(SalesOpportunity.status == "won", 1)])).label(
                "deals_won"
            ),
            func.count(case([(SalesOpportunity.status == "lost", 1)])).label(
                "deals_lost"
            ),
            func.sum(
                case(
                    [(SalesOpportunity.status == "won", SalesOpportunity.amount)],
                    else_=0,
                )
            ).label("revenue"),
        )
        .filter(
            SalesOpportunity.created_at >= date_from,
            SalesOpportunity.created_at <= date_to,
        )
        .group_by(SalesOpportunity.owner_id)
        .all()
    )

    performance_data = [
        {
            "owner_id": owner_id,
            "deals_won": won,
            "deals_lost": lost,
            "revenue": rev or Decimal("0"),
            "win_rate": (won / (won + lost) * 100)
            if (won + lost) > 0
            else Decimal("0"),
        }
        for owner_id, won, lost, rev in performance_by_rep
    ]

    return CRMAnalyticsResponse(
        period_start=date_from,
        period_end=date_to,
        new_customers=new_customers,
        qualified_leads=qualified_leads,
        opportunities_created=opportunities_created,
        deals_won=deals_won,
        deals_lost=deals_lost,
        revenue_generated=revenue_generated,
        pipeline_velocity=pipeline_velocity,
        lead_conversion_rate=lead_conversion_rate,
        opportunity_win_rate=opportunity_win_rate,
        avg_deal_size=avg_deal_size,
        customer_acquisition_cost=customer_acquisition_cost,
        lifetime_value=lifetime_value,
        daily_breakdown=daily_breakdown,
        performance_by_rep=performance_data,
    )
