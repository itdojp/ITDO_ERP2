from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func, case, desc, asc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import uuid
from decimal import Decimal

from app.models.crm_extended import (
    CRMCustomer, CustomerInteraction, SalesOpportunity, OpportunityActivity,
    CustomerActivity, CustomerSegment, MarketingCampaign, customer_segment_members
)
from app.schemas.crm_complete_v30 import (
    CRMCustomerCreate, CRMCustomerUpdate, CustomerInteractionCreate, CustomerInteractionUpdate,
    SalesOpportunityCreate, SalesOpportunityUpdate, OpportunityActivityCreate,
    CustomerActivityCreate, CustomerSegmentCreate, CustomerSegmentUpdate,
    MarketingCampaignCreate, MarketingCampaignUpdate
)

class NotFoundError(Exception):
    pass

class DuplicateError(Exception):
    pass

class InvalidStageError(Exception):
    pass

class CRMCustomerCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: str) -> Optional[CRMCustomer]:
        return self.db.query(CRMCustomer).filter(CRMCustomer.id == customer_id).first()

    def get_by_code(self, code: str) -> Optional[CRMCustomer]:
        return self.db.query(CRMCustomer).filter(CRMCustomer.customer_code == code).first()

    def get_by_email(self, email: str) -> Optional[CRMCustomer]:
        return self.db.query(CRMCustomer).filter(CRMCustomer.primary_email == email).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[CRMCustomer], int]:
        query = self.db.query(CRMCustomer)

        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(CRMCustomer.is_active == filters["is_active"])
            if filters.get("is_qualified") is not None:
                query = query.filter(CRMCustomer.is_qualified == filters["is_qualified"])
            if filters.get("is_vip") is not None:
                query = query.filter(CRMCustomer.is_vip == filters["is_vip"])
            if filters.get("customer_type"):
                query = query.filter(CRMCustomer.customer_type == filters["customer_type"])
            if filters.get("customer_segment"):
                query = query.filter(CRMCustomer.customer_segment == filters["customer_segment"])
            if filters.get("lead_status"):
                query = query.filter(CRMCustomer.lead_status == filters["lead_status"])
            if filters.get("customer_stage"):
                query = query.filter(CRMCustomer.customer_stage == filters["customer_stage"])
            if filters.get("lifecycle_stage"):
                query = query.filter(CRMCustomer.lifecycle_stage == filters["lifecycle_stage"])
            if filters.get("assigned_sales_rep"):
                query = query.filter(CRMCustomer.assigned_sales_rep == filters["assigned_sales_rep"])
            if filters.get("assigned_account_manager"):
                query = query.filter(CRMCustomer.assigned_account_manager == filters["assigned_account_manager"])
            if filters.get("lead_source"):
                query = query.filter(CRMCustomer.lead_source == filters["lead_source"])
            if filters.get("industry"):
                query = query.filter(CRMCustomer.industry == filters["industry"])
            if filters.get("company_size"):
                query = query.filter(CRMCustomer.company_size == filters["company_size"])
            if filters.get("do_not_contact") is not None:
                query = query.filter(CRMCustomer.do_not_contact == filters["do_not_contact"])
            if filters.get("marketing_opt_in") is not None:
                query = query.filter(CRMCustomer.marketing_opt_in == filters["marketing_opt_in"])
            if filters.get("lead_score_min"):
                query = query.filter(CRMCustomer.lead_score >= filters["lead_score_min"])
            if filters.get("lead_score_max"):
                query = query.filter(CRMCustomer.lead_score <= filters["lead_score_max"])
            if filters.get("engagement_score_min"):
                query = query.filter(CRMCustomer.engagement_score >= filters["engagement_score_min"])
            if filters.get("lifetime_value_min"):
                query = query.filter(CRMCustomer.lifetime_value >= filters["lifetime_value_min"])
            if filters.get("created_from"):
                query = query.filter(CRMCustomer.created_at >= filters["created_from"])
            if filters.get("created_to"):
                query = query.filter(CRMCustomer.created_at <= filters["created_to"])
            if filters.get("last_activity_from"):
                query = query.filter(CRMCustomer.last_activity_at >= filters["last_activity_from"])
            if filters.get("last_activity_to"):
                query = query.filter(CRMCustomer.last_activity_at <= filters["last_activity_to"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        CRMCustomer.full_name.ilike(search),
                        CRMCustomer.company_name.ilike(search),
                        CRMCustomer.customer_code.ilike(search),
                        CRMCustomer.primary_email.ilike(search),
                        CRMCustomer.primary_phone.ilike(search)
                    )
                )
            if filters.get("tags"):
                # Search for customers with specific tags
                for tag in filters["tags"]:
                    query = query.filter(CRMCustomer.tags.contains([tag]))

        total = query.count()
        
        # Sorting
        sort_by = filters.get("sort_by", "created_at") if filters else "created_at"
        sort_order = filters.get("sort_order", "desc") if filters else "desc"
        
        sort_column = getattr(CRMCustomer, sort_by, CRMCustomer.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        customers = query.offset(skip).limit(limit).all()

        return customers, total

    def create(self, customer_in: CRMCustomerCreate) -> CRMCustomer:
        # Check for duplicates
        if self.get_by_code(customer_in.customer_code):
            raise DuplicateError("Customer code already exists")
        if self.get_by_email(customer_in.primary_email):
            raise DuplicateError("Email already exists")

        db_customer = CRMCustomer(
            id=str(uuid.uuid4()),
            customer_code=customer_in.customer_code,
            first_name=customer_in.first_name,
            last_name=customer_in.last_name,
            full_name=customer_in.full_name,
            company_name=customer_in.company_name,
            job_title=customer_in.job_title,
            department=customer_in.department,
            primary_email=customer_in.primary_email,
            secondary_email=customer_in.secondary_email,
            primary_phone=customer_in.primary_phone,
            secondary_phone=customer_in.secondary_phone,
            mobile_phone=customer_in.mobile_phone,
            website=customer_in.website,
            linkedin_profile=customer_in.linkedin_profile,
            billing_address_line1=customer_in.billing_address_line1,
            billing_city=customer_in.billing_city,
            billing_postal_code=customer_in.billing_postal_code,
            billing_country=customer_in.billing_country,
            mailing_address_line1=customer_in.mailing_address_line1,
            mailing_city=customer_in.mailing_city,
            mailing_postal_code=customer_in.mailing_postal_code,
            mailing_country=customer_in.mailing_country,
            customer_type=customer_in.customer_type,
            customer_segment=customer_in.customer_segment,
            industry=customer_in.industry,
            company_size=customer_in.company_size,
            annual_revenue=customer_in.annual_revenue,
            lead_source=customer_in.lead_source,
            lead_status=customer_in.lead_status,
            customer_stage=customer_in.customer_stage,
            lifecycle_stage=customer_in.lifecycle_stage,
            assigned_sales_rep=customer_in.assigned_sales_rep,
            assigned_account_manager=customer_in.assigned_account_manager,
            email_opt_in=customer_in.email_opt_in,
            sms_opt_in=customer_in.sms_opt_in,
            phone_opt_in=customer_in.phone_opt_in,
            marketing_opt_in=customer_in.marketing_opt_in,
            preferred_contact_method=customer_in.preferred_contact_method,
            preferred_contact_time=customer_in.preferred_contact_time,
            time_zone=customer_in.time_zone,
            tags=customer_in.tags,
            custom_fields=customer_in.custom_fields,
            social_profiles=customer_in.social_profiles,
            notes=customer_in.notes,
            description=customer_in.description
        )

        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)

        return db_customer

    def update(self, customer_id: str, customer_in: CRMCustomerUpdate) -> Optional[CRMCustomer]:
        customer = self.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")

        update_data = customer_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        customer.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def update_activity_timestamp(self, customer_id: str):
        """顧客の最終活動日時を更新"""
        customer = self.get_by_id(customer_id)
        if customer:
            customer.last_activity_at = datetime.utcnow()
            self.db.commit()

    def update_scores(self, customer_id: str, lead_score: Optional[int] = None, engagement_score: Optional[int] = None):
        """リードスコアとエンゲージメントスコアを更新"""
        customer = self.get_by_id(customer_id)
        if customer:
            if lead_score is not None:
                customer.lead_score = max(0, min(100, lead_score))
            if engagement_score is not None:
                customer.engagement_score = max(0, min(100, engagement_score))
            customer.updated_at = datetime.utcnow()
            self.db.commit()

    def add_to_segment(self, customer_id: str, segment_id: str, user_id: str):
        """顧客をセグメントに追加"""
        # Check if already exists
        existing = self.db.query(customer_segment_members).filter(
            customer_segment_members.c.customer_id == customer_id,
            customer_segment_members.c.segment_id == segment_id
        ).first()
        
        if not existing:
            stmt = customer_segment_members.insert().values(
                customer_id=customer_id,
                segment_id=segment_id,
                added_by=user_id
            )
            self.db.execute(stmt)
            self.db.commit()

    def remove_from_segment(self, customer_id: str, segment_id: str):
        """顧客をセグメントから削除"""
        stmt = customer_segment_members.delete().where(
            and_(
                customer_segment_members.c.customer_id == customer_id,
                customer_segment_members.c.segment_id == segment_id
            )
        )
        self.db.execute(stmt)
        self.db.commit()


class CustomerInteractionCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, interaction_id: str) -> Optional[CustomerInteraction]:
        return self.db.query(CustomerInteraction).filter(CustomerInteraction.id == interaction_id).first()

    def get_multi_by_customer(
        self,
        customer_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[CustomerInteraction], int]:
        query = self.db.query(CustomerInteraction).filter(CustomerInteraction.customer_id == customer_id)
        total = query.count()
        interactions = query.offset(skip).limit(limit).order_by(CustomerInteraction.interaction_date.desc()).all()
        return interactions, total

    def create(self, interaction_in: CustomerInteractionCreate, user_id: str) -> CustomerInteraction:
        db_interaction = CustomerInteraction(
            id=str(uuid.uuid4()),
            customer_id=interaction_in.customer_id,
            user_id=user_id,
            interaction_type=interaction_in.interaction_type,
            interaction_direction=interaction_in.interaction_direction,
            subject=interaction_in.subject,
            description=interaction_in.description,
            outcome=interaction_in.outcome,
            next_steps=interaction_in.next_steps,
            interaction_date=interaction_in.interaction_date,
            duration_minutes=interaction_in.duration_minutes,
            scheduled_follow_up=interaction_in.scheduled_follow_up,
            status=interaction_in.status,
            satisfaction_rating=interaction_in.satisfaction_rating,
            lead_quality_score=interaction_in.lead_quality_score,
            channel=interaction_in.channel,
            campaign_id=interaction_in.campaign_id,
            custom_fields=interaction_in.custom_fields
        )

        self.db.add(db_interaction)
        self.db.commit()
        self.db.refresh(db_interaction)

        # Update customer activity timestamp and contact timestamp
        customer_crud = CRMCustomerCRUD(self.db)
        customer_crud.update_activity_timestamp(interaction_in.customer_id)
        
        customer = customer_crud.get_by_id(interaction_in.customer_id)
        if customer:
            customer.last_contacted_at = interaction_in.interaction_date
            self.db.commit()

        return db_interaction

    def update(self, interaction_id: str, interaction_in: CustomerInteractionUpdate) -> Optional[CustomerInteraction]:
        interaction = self.get_by_id(interaction_id)
        if not interaction:
            raise NotFoundError(f"Interaction {interaction_id} not found")

        update_data = interaction_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(interaction, field, value)

        interaction.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(interaction)

        return interaction


class SalesOpportunityCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, opportunity_id: str) -> Optional[SalesOpportunity]:
        return (
            self.db.query(SalesOpportunity)
            .options(joinedload(SalesOpportunity.activities))
            .filter(SalesOpportunity.id == opportunity_id)
            .first()
        )

    def get_by_number(self, opportunity_number: str) -> Optional[SalesOpportunity]:
        return self.db.query(SalesOpportunity).filter(SalesOpportunity.opportunity_number == opportunity_number).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[SalesOpportunity], int]:
        query = self.db.query(SalesOpportunity)

        if filters:
            if filters.get("customer_id"):
                query = query.filter(SalesOpportunity.customer_id == filters["customer_id"])
            if filters.get("owner_id"):
                query = query.filter(SalesOpportunity.owner_id == filters["owner_id"])
            if filters.get("stage"):
                query = query.filter(SalesOpportunity.stage == filters["stage"])
            if filters.get("status"):
                query = query.filter(SalesOpportunity.status == filters["status"])
            if filters.get("source"):
                query = query.filter(SalesOpportunity.source == filters["source"])
            if filters.get("product_category"):
                query = query.filter(SalesOpportunity.product_category == filters["product_category"])
            if filters.get("amount_min"):
                query = query.filter(SalesOpportunity.amount >= filters["amount_min"])
            if filters.get("amount_max"):
                query = query.filter(SalesOpportunity.amount <= filters["amount_max"])
            if filters.get("probability_min"):
                query = query.filter(SalesOpportunity.probability >= filters["probability_min"])
            if filters.get("expected_close_from"):
                query = query.filter(SalesOpportunity.expected_close_date >= filters["expected_close_from"])
            if filters.get("expected_close_to"):
                query = query.filter(SalesOpportunity.expected_close_date <= filters["expected_close_to"])
            if filters.get("created_from"):
                query = query.filter(SalesOpportunity.created_at >= filters["created_from"])
            if filters.get("created_to"):
                query = query.filter(SalesOpportunity.created_at <= filters["created_to"])

        total = query.count()
        opportunities = query.offset(skip).limit(limit).order_by(SalesOpportunity.created_at.desc()).all()

        return opportunities, total

    def create(self, opportunity_in: SalesOpportunityCreate, user_id: str) -> SalesOpportunity:
        # Generate opportunity number
        opportunity_number = self._generate_opportunity_number()

        # Calculate weighted amount
        weighted_amount = None
        if opportunity_in.amount:
            weighted_amount = opportunity_in.amount * (opportunity_in.probability / 100)

        db_opportunity = SalesOpportunity(
            id=str(uuid.uuid4()),
            opportunity_number=opportunity_number,
            customer_id=opportunity_in.customer_id,
            owner_id=user_id,
            name=opportunity_in.name,
            description=opportunity_in.description,
            amount=opportunity_in.amount,
            currency=opportunity_in.currency,
            probability=opportunity_in.probability,
            weighted_amount=weighted_amount,
            stage=opportunity_in.stage,
            stage_updated_at=datetime.utcnow(),
            expected_close_date=opportunity_in.expected_close_date,
            product_category=opportunity_in.product_category,
            solution_type=opportunity_in.solution_type,
            competitors=opportunity_in.competitors,
            decision_criteria=opportunity_in.decision_criteria,
            decision_makers=opportunity_in.decision_makers,
            budget_confirmed=opportunity_in.budget_confirmed,
            timeline_confirmed=opportunity_in.timeline_confirmed,
            authority_confirmed=opportunity_in.authority_confirmed,
            need_confirmed=opportunity_in.need_confirmed,
            source=opportunity_in.source,
            campaign_id=opportunity_in.campaign_id,
            tags=opportunity_in.tags,
            custom_fields=opportunity_in.custom_fields
        )

        self.db.add(db_opportunity)
        self.db.commit()
        self.db.refresh(db_opportunity)

        # Update customer activity timestamp
        customer_crud = CRMCustomerCRUD(self.db)
        customer_crud.update_activity_timestamp(opportunity_in.customer_id)

        return db_opportunity

    def update(self, opportunity_id: str, opportunity_in: SalesOpportunityUpdate) -> Optional[SalesOpportunity]:
        opportunity = self.get_by_id(opportunity_id)
        if not opportunity:
            raise NotFoundError(f"Opportunity {opportunity_id} not found")

        # Check for stage transitions
        old_stage = opportunity.stage
        new_stage = opportunity_in.stage

        if new_stage and new_stage != old_stage:
            if not self._is_valid_stage_transition(old_stage, new_stage):
                raise InvalidStageError(f"Invalid stage transition from {old_stage} to {new_stage}")
            opportunity.stage_updated_at = datetime.utcnow()
            opportunity.last_stage_change_date = date.today()

        update_data = opportunity_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(opportunity, field, value)

        # Recalculate weighted amount if amount or probability changed
        if opportunity.amount and opportunity.probability is not None:
            opportunity.weighted_amount = opportunity.amount * (opportunity.probability / 100)

        # Set close date if won or lost
        if opportunity_in.status in ["won", "lost"] and not opportunity.actual_close_date:
            opportunity.actual_close_date = date.today()

        opportunity.updated_at = datetime.utcnow()
        opportunity.last_activity_date = date.today()

        self.db.commit()
        self.db.refresh(opportunity)

        return opportunity

    def _generate_opportunity_number(self) -> str:
        """案件番号生成"""
        today = datetime.now()
        prefix = f"OPP-{today.year}{today.month:02d}"
        
        last_opp = (
            self.db.query(SalesOpportunity)
            .filter(SalesOpportunity.opportunity_number.like(f"{prefix}%"))
            .order_by(SalesOpportunity.opportunity_number.desc())
            .first()
        )
        
        if last_opp:
            last_number = int(last_opp.opportunity_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"

    def _is_valid_stage_transition(self, current_stage: str, new_stage: str) -> bool:
        """ステージ遷移の妥当性チェック"""
        valid_transitions = {
            "prospecting": ["qualification", "closed_lost"],
            "qualification": ["proposal", "prospecting", "closed_lost"],
            "proposal": ["negotiation", "qualification", "closed_lost"],
            "negotiation": ["closed_won", "closed_lost", "proposal"],
            "closed_won": [],
            "closed_lost": ["prospecting"]  # Re-open lost opportunities
        }
        return new_stage in valid_transitions.get(current_stage, [])

    def get_pipeline_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """パイプライン分析データ取得"""
        query = self.db.query(SalesOpportunity).filter(SalesOpportunity.status == "open")

        if filters:
            if filters.get("owner_id"):
                query = query.filter(SalesOpportunity.owner_id == filters["owner_id"])
            if filters.get("date_from"):
                query = query.filter(SalesOpportunity.created_at >= filters["date_from"])
            if filters.get("date_to"):
                query = query.filter(SalesOpportunity.created_at <= filters["date_to"])

        opportunities = query.all()
        
        # ステージ別集計
        stage_breakdown = {}
        total_pipeline_value = Decimal('0')
        weighted_pipeline_value = Decimal('0')
        
        for opp in opportunities:
            stage = opp.stage
            if stage not in stage_breakdown:
                stage_breakdown[stage] = {"count": 0, "value": Decimal('0'), "weighted_value": Decimal('0')}
            
            stage_breakdown[stage]["count"] += 1
            if opp.amount:
                stage_breakdown[stage]["value"] += opp.amount
                total_pipeline_value += opp.amount
            if opp.weighted_amount:
                stage_breakdown[stage]["weighted_value"] += opp.weighted_amount
                weighted_pipeline_value += opp.weighted_amount

        # 平均案件サイズ
        avg_deal_size = total_pipeline_value / len(opportunities) if opportunities else Decimal('0')

        return {
            "total_opportunities": len(opportunities),
            "total_pipeline_value": total_pipeline_value,
            "weighted_pipeline_value": weighted_pipeline_value,
            "avg_deal_size": avg_deal_size,
            "stage_breakdown": stage_breakdown
        }


class OpportunityActivityCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, activity_in: OpportunityActivityCreate, user_id: str) -> OpportunityActivity:
        db_activity = OpportunityActivity(
            id=str(uuid.uuid4()),
            opportunity_id=activity_in.opportunity_id,
            user_id=user_id,
            activity_type=activity_in.activity_type,
            subject=activity_in.subject,
            description=activity_in.description,
            activity_date=activity_in.activity_date,
            due_date=activity_in.due_date,
            status=activity_in.status,
            priority=activity_in.priority,
            outcome=activity_in.outcome,
            outcome_notes=activity_in.outcome_notes
        )

        self.db.add(db_activity)
        self.db.commit()
        self.db.refresh(db_activity)

        # Update opportunity last activity date
        opportunity = self.db.query(SalesOpportunity).filter(
            SalesOpportunity.id == activity_in.opportunity_id
        ).first()
        if opportunity:
            opportunity.last_activity_date = date.today()
            self.db.commit()

        return db_activity


class CustomerActivityCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, activity_in: CustomerActivityCreate, user_id: Optional[str] = None) -> CustomerActivity:
        db_activity = CustomerActivity(
            id=str(uuid.uuid4()),
            customer_id=activity_in.customer_id,
            user_id=user_id,
            activity_type=activity_in.activity_type,
            activity_category=activity_in.activity_category,
            subject=activity_in.subject,
            description=activity_in.description,
            activity_date=activity_in.activity_date,
            due_date=activity_in.due_date,
            status=activity_in.status,
            priority=activity_in.priority,
            page_url=activity_in.page_url,
            referrer_url=activity_in.referrer_url,
            source=activity_in.source,
            campaign_id=activity_in.campaign_id,
            custom_fields=activity_in.custom_fields
        )

        self.db.add(db_activity)
        self.db.commit()
        self.db.refresh(db_activity)

        # Update customer activity timestamp
        customer_crud = CRMCustomerCRUD(self.db)
        customer_crud.update_activity_timestamp(activity_in.customer_id)

        return db_activity


class CustomerSegmentCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, segment_id: str) -> Optional[CustomerSegment]:
        return self.db.query(CustomerSegment).filter(CustomerSegment.id == segment_id).first()

    def create(self, segment_in: CustomerSegmentCreate, user_id: str) -> CustomerSegment:
        if self.db.query(CustomerSegment).filter(CustomerSegment.name == segment_in.name).first():
            raise DuplicateError("Segment name already exists")

        db_segment = CustomerSegment(
            id=str(uuid.uuid4()),
            name=segment_in.name,
            description=segment_in.description,
            segment_type=segment_in.segment_type,
            criteria=segment_in.criteria,
            color=segment_in.color,
            is_active=segment_in.is_active,
            created_by=user_id
        )

        self.db.add(db_segment)
        self.db.commit()
        self.db.refresh(db_segment)

        return db_segment

    def update(self, segment_id: str, segment_in: CustomerSegmentUpdate) -> Optional[CustomerSegment]:
        segment = self.get_by_id(segment_id)
        if not segment:
            raise NotFoundError(f"Segment {segment_id} not found")

        update_data = segment_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(segment, field, value)

        segment.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(segment)

        return segment

    def calculate_segment_metrics(self, segment_id: str):
        """セグメントのメトリクス再計算"""
        segment = self.get_by_id(segment_id)
        if not segment:
            return

        # Get customers in this segment
        customers_query = (
            self.db.query(CRMCustomer)
            .join(customer_segment_members)
            .filter(customer_segment_members.c.segment_id == segment_id)
        )
        
        customers = customers_query.all()
        
        segment.customer_count = len(customers)
        segment.total_value = sum(c.lifetime_value for c in customers)
        segment.avg_customer_value = segment.total_value / len(customers) if customers else Decimal('0')
        segment.last_calculated_at = datetime.utcnow()
        
        self.db.commit()


class MarketingCampaignCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, campaign_id: str) -> Optional[MarketingCampaign]:
        return self.db.query(MarketingCampaign).filter(MarketingCampaign.id == campaign_id).first()

    def get_by_code(self, code: str) -> Optional[MarketingCampaign]:
        return self.db.query(MarketingCampaign).filter(MarketingCampaign.campaign_code == code).first()

    def create(self, campaign_in: MarketingCampaignCreate, user_id: str) -> MarketingCampaign:
        if self.get_by_code(campaign_in.campaign_code):
            raise DuplicateError("Campaign code already exists")

        db_campaign = MarketingCampaign(
            id=str(uuid.uuid4()),
            campaign_code=campaign_in.campaign_code,
            name=campaign_in.name,
            description=campaign_in.description,
            campaign_type=campaign_in.campaign_type,
            channel=campaign_in.channel,
            start_date=campaign_in.start_date,
            end_date=campaign_in.end_date,
            budget=campaign_in.budget,
            target_audience=campaign_in.target_audience,
            target_segment_ids=campaign_in.target_segment_ids,
            created_by=user_id,
            owned_by=campaign_in.owned_by or user_id,
            tags=campaign_in.tags
        )

        self.db.add(db_campaign)
        self.db.commit()
        self.db.refresh(db_campaign)

        return db_campaign

    def update(self, campaign_id: str, campaign_in: MarketingCampaignUpdate) -> Optional[MarketingCampaign]:
        campaign = self.get_by_id(campaign_id)
        if not campaign:
            raise NotFoundError(f"Campaign {campaign_id} not found")

        update_data = campaign_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        # Recalculate metrics
        if campaign.clicks and campaign.impressions:
            campaign.click_through_rate = Decimal(campaign.clicks) / Decimal(campaign.impressions)
        if campaign.customers_acquired and campaign.leads_generated:
            campaign.conversion_rate = Decimal(campaign.customers_acquired) / Decimal(campaign.leads_generated)
        if campaign.revenue_generated and campaign.actual_cost:
            campaign.return_on_investment = (campaign.revenue_generated - campaign.actual_cost) / campaign.actual_cost * 100
        if campaign.actual_cost and campaign.leads_generated:
            campaign.cost_per_lead = campaign.actual_cost / campaign.leads_generated
        if campaign.actual_cost and campaign.customers_acquired:
            campaign.cost_per_acquisition = campaign.actual_cost / campaign.customers_acquired

        campaign.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(campaign)

        return campaign