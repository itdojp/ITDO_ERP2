from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func, desc, asc, case
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import uuid
from decimal import Decimal

from app.models.supplier_relationship_extended import (
    SupplierRelationship, SupplierPerformanceReview, SupplierNegotiation, 
    SupplierContract, ContractAmendment, ContractMilestone, NegotiationMeeting
)
from app.schemas.supplier_relationship_v30 import (
    SupplierRelationshipCreate, SupplierRelationshipUpdate,
    SupplierPerformanceReviewCreate, SupplierPerformanceReviewUpdate,
    SupplierNegotiationCreate, SupplierNegotiationUpdate,
    SupplierContractCreate, SupplierContractUpdate
)

class NotFoundError(Exception):
    pass

class DuplicateError(Exception):
    pass

class InvalidStatusError(Exception):
    pass

class SupplierRelationshipCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, relationship_id: str) -> Optional[SupplierRelationship]:
        return (
            self.db.query(SupplierRelationship)
            .options(
                joinedload(SupplierRelationship.supplier),
                joinedload(SupplierRelationship.relationship_manager)
            )
            .filter(SupplierRelationship.id == relationship_id)
            .first()
        )

    def get_by_supplier(self, supplier_id: str) -> Optional[SupplierRelationship]:
        return self.db.query(SupplierRelationship).filter(
            SupplierRelationship.supplier_id == supplier_id
        ).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[SupplierRelationship], int]:
        query = self.db.query(SupplierRelationship)

        if filters:
            if filters.get("supplier_id"):
                query = query.filter(SupplierRelationship.supplier_id == filters["supplier_id"])
            if filters.get("relationship_manager_id"):
                query = query.filter(SupplierRelationship.relationship_manager_id == filters["relationship_manager_id"])
            if filters.get("relationship_type"):
                query = query.filter(SupplierRelationship.relationship_type == filters["relationship_type"])
            if filters.get("partnership_level"):
                query = query.filter(SupplierRelationship.partnership_level == filters["partnership_level"])
            if filters.get("contract_type"):
                query = query.filter(SupplierRelationship.contract_type == filters["contract_type"])
            if filters.get("status"):
                query = query.filter(SupplierRelationship.status == filters["status"])
            if filters.get("risk_level"):
                query = query.filter(SupplierRelationship.risk_level == filters["risk_level"])
            if filters.get("strategic_importance"):
                query = query.filter(SupplierRelationship.strategic_importance == filters["strategic_importance"])
            if filters.get("overall_score_min"):
                query = query.filter(SupplierRelationship.overall_score >= filters["overall_score_min"])
            if filters.get("annual_spend_min"):
                query = query.filter(SupplierRelationship.annual_spend >= filters["annual_spend_min"])
            if filters.get("contract_expiring_days"):
                expiry_date = date.today() + timedelta(days=filters["contract_expiring_days"])
                query = query.filter(
                    SupplierRelationship.contract_end_date <= expiry_date,
                    SupplierRelationship.contract_end_date >= date.today()
                )
            if filters.get("review_overdue"):
                query = query.filter(SupplierRelationship.next_review_date < date.today())

        total = query.count()
        
        # Sorting
        sort_by = filters.get("sort_by", "created_at") if filters else "created_at"
        sort_order = filters.get("sort_order", "desc") if filters else "desc"
        
        sort_column = getattr(SupplierRelationship, sort_by, SupplierRelationship.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        relationships = query.offset(skip).limit(limit).all()

        return relationships, total

    def create(self, relationship_in: SupplierRelationshipCreate, user_id: str) -> SupplierRelationship:
        # Check if relationship already exists for this supplier
        existing = self.get_by_supplier(relationship_in.supplier_id)
        if existing:
            raise DuplicateError("Supplier relationship already exists for this supplier")

        db_relationship = SupplierRelationship(
            id=str(uuid.uuid4()),
            supplier_id=relationship_in.supplier_id,
            relationship_manager_id=user_id,
            relationship_type=relationship_in.relationship_type,
            partnership_level=relationship_in.partnership_level,
            contract_type=relationship_in.contract_type,
            contract_start_date=relationship_in.contract_start_date,
            contract_end_date=relationship_in.contract_end_date,
            auto_renewal=relationship_in.auto_renewal,
            renewal_notice_days=relationship_in.renewal_notice_days,
            overall_score=relationship_in.overall_score,
            quality_score=relationship_in.quality_score,
            delivery_score=relationship_in.delivery_score,
            service_score=relationship_in.service_score,
            cost_competitiveness=relationship_in.cost_competitiveness,
            innovation_score=relationship_in.innovation_score,
            annual_spend=relationship_in.annual_spend,
            spend_percentage=relationship_in.spend_percentage,
            cost_savings_achieved=relationship_in.cost_savings_achieved,
            risk_level=relationship_in.risk_level,
            business_continuity_risk=relationship_in.business_continuity_risk,
            financial_risk=relationship_in.financial_risk,
            compliance_risk=relationship_in.compliance_risk,
            geographic_risk=relationship_in.geographic_risk,
            strategic_importance=relationship_in.strategic_importance,
            business_impact=relationship_in.business_impact,
            substitutability=relationship_in.substitutability,
            next_review_date=relationship_in.next_review_date,
            review_frequency_months=relationship_in.review_frequency_months,
            notes=relationship_in.notes,
            strengths=relationship_in.strengths,
            weaknesses=relationship_in.weaknesses,
            improvement_areas=relationship_in.improvement_areas,
            action_items=relationship_in.action_items
        )

        self.db.add(db_relationship)
        self.db.commit()
        self.db.refresh(db_relationship)

        return db_relationship

    def update(self, relationship_id: str, relationship_in: SupplierRelationshipUpdate) -> Optional[SupplierRelationship]:
        relationship = self.get_by_id(relationship_id)
        if not relationship:
            raise NotFoundError(f"Supplier relationship {relationship_id} not found")

        update_data = relationship_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(relationship, field, value)

        relationship.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(relationship)

        return relationship

    def approve(self, relationship_id: str, approver_id: str) -> SupplierRelationship:
        """サプライヤー関係承認"""
        relationship = self.get_by_id(relationship_id)
        if not relationship:
            raise NotFoundError(f"Supplier relationship {relationship_id} not found")

        relationship.approval_status = "approved"
        relationship.approved_by = approver_id
        relationship.approved_at = datetime.utcnow()
        relationship.status = "active"

        self.db.commit()
        self.db.refresh(relationship)

        return relationship

    def schedule_review(self, relationship_id: str, review_date: date):
        """レビュー日程設定"""
        relationship = self.get_by_id(relationship_id)
        if relationship:
            relationship.next_review_date = review_date
            relationship.updated_at = datetime.utcnow()
            self.db.commit()


class SupplierPerformanceReviewCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: str) -> Optional[SupplierPerformanceReview]:
        return self.db.query(SupplierPerformanceReview).filter(
            SupplierPerformanceReview.id == review_id
        ).first()

    def get_multi_by_relationship(
        self,
        relationship_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[SupplierPerformanceReview], int]:
        query = self.db.query(SupplierPerformanceReview).filter(
            SupplierPerformanceReview.supplier_relationship_id == relationship_id
        )
        total = query.count()
        reviews = query.offset(skip).limit(limit).order_by(
            SupplierPerformanceReview.review_period_end.desc()
        ).all()
        return reviews, total

    def create(self, review_in: SupplierPerformanceReviewCreate, user_id: str) -> SupplierPerformanceReview:
        db_review = SupplierPerformanceReview(
            id=str(uuid.uuid4()),
            supplier_relationship_id=review_in.supplier_relationship_id,
            reviewer_id=user_id,
            review_period_start=review_in.review_period_start,
            review_period_end=review_in.review_period_end,
            review_type=review_in.review_type,
            quality_rating=review_in.quality_rating,
            delivery_rating=review_in.delivery_rating,
            service_rating=review_in.service_rating,
            cost_rating=review_in.cost_rating,
            innovation_rating=review_in.innovation_rating,
            compliance_rating=review_in.compliance_rating,
            communication_rating=review_in.communication_rating,
            responsiveness_rating=review_in.responsiveness_rating,
            on_time_delivery_rate=review_in.on_time_delivery_rate,
            quality_defect_rate=review_in.quality_defect_rate,
            cost_variance=review_in.cost_variance,
            invoice_accuracy_rate=review_in.invoice_accuracy_rate,
            response_time_hours=review_in.response_time_hours,
            strengths_identified=review_in.strengths_identified,
            weaknesses_identified=review_in.weaknesses_identified,
            improvement_recommendations=review_in.improvement_recommendations,
            action_items=review_in.action_items,
            quality_comments=review_in.quality_comments,
            delivery_comments=review_in.delivery_comments,
            service_comments=review_in.service_comments,
            cost_comments=review_in.cost_comments,
            general_comments=review_in.general_comments,
            next_period_goals=review_in.next_period_goals,
            improvement_plan=review_in.improvement_plan
        )

        # Calculate overall rating
        ratings = [
            review_in.quality_rating, review_in.delivery_rating, review_in.service_rating,
            review_in.cost_rating, review_in.innovation_rating, review_in.compliance_rating,
            review_in.communication_rating, review_in.responsiveness_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            db_review.overall_rating = sum(valid_ratings) / len(valid_ratings)
            
            # Assign grade based on overall rating
            if db_review.overall_rating >= 4.5:
                db_review.overall_grade = "A+"
            elif db_review.overall_rating >= 4.0:
                db_review.overall_grade = "A"
            elif db_review.overall_rating >= 3.5:
                db_review.overall_grade = "B+"
            elif db_review.overall_rating >= 3.0:
                db_review.overall_grade = "B"
            elif db_review.overall_rating >= 2.5:
                db_review.overall_grade = "C+"
            elif db_review.overall_rating >= 2.0:
                db_review.overall_grade = "C"
            elif db_review.overall_rating >= 1.0:
                db_review.overall_grade = "D"
            else:
                db_review.overall_grade = "F"

        self.db.add(db_review)
        self.db.commit()
        self.db.refresh(db_review)

        # Update supplier relationship scores
        self._update_relationship_scores(review_in.supplier_relationship_id, db_review)

        return db_review

    def update(self, review_id: str, review_in: SupplierPerformanceReviewUpdate) -> Optional[SupplierPerformanceReview]:
        review = self.get_by_id(review_id)
        if not review:
            raise NotFoundError(f"Performance review {review_id} not found")

        update_data = review_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)

        review.updated_at = datetime.utcnow()

        if review_in.review_status == "completed" and not review.completed_at:
            review.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(review)

        return review

    def approve(self, review_id: str, approver_id: str) -> SupplierPerformanceReview:
        """パフォーマンスレビュー承認"""
        review = self.get_by_id(review_id)
        if not review:
            raise NotFoundError(f"Performance review {review_id} not found")

        review.review_status = "approved"
        review.approved_by = approver_id
        review.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(review)

        return review

    def _update_relationship_scores(self, relationship_id: str, review: SupplierPerformanceReview):
        """関係のスコアを最新レビューで更新"""
        relationship = self.db.query(SupplierRelationship).filter(
            SupplierRelationship.id == relationship_id
        ).first()
        
        if relationship and review.overall_rating:
            relationship.overall_score = review.overall_rating
            if review.quality_rating:
                relationship.quality_score = review.quality_rating
            if review.delivery_rating:
                relationship.delivery_score = review.delivery_rating
            if review.service_rating:
                relationship.service_score = review.service_rating
            
            relationship.last_reviewed_at = datetime.utcnow()
            self.db.commit()


class SupplierNegotiationCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, negotiation_id: str) -> Optional[SupplierNegotiation]:
        return (
            self.db.query(SupplierNegotiation)
            .options(joinedload(SupplierNegotiation.meetings))
            .filter(SupplierNegotiation.id == negotiation_id)
            .first()
        )

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[SupplierNegotiation], int]:
        query = self.db.query(SupplierNegotiation)

        if filters:
            if filters.get("supplier_relationship_id"):
                query = query.filter(SupplierNegotiation.supplier_relationship_id == filters["supplier_relationship_id"])
            if filters.get("lead_negotiator_id"):
                query = query.filter(SupplierNegotiation.lead_negotiator_id == filters["lead_negotiator_id"])
            if filters.get("negotiation_type"):
                query = query.filter(SupplierNegotiation.negotiation_type == filters["negotiation_type"])
            if filters.get("status"):
                query = query.filter(SupplierNegotiation.status == filters["status"])
            if filters.get("current_phase"):
                query = query.filter(SupplierNegotiation.current_phase == filters["current_phase"])

        total = query.count()
        negotiations = query.offset(skip).limit(limit).order_by(
            SupplierNegotiation.created_at.desc()
        ).all()

        return negotiations, total

    def create(self, negotiation_in: SupplierNegotiationCreate, user_id: str) -> SupplierNegotiation:
        db_negotiation = SupplierNegotiation(
            id=str(uuid.uuid4()),
            supplier_relationship_id=negotiation_in.supplier_relationship_id,
            lead_negotiator_id=user_id,
            negotiation_title=negotiation_in.negotiation_title,
            negotiation_type=negotiation_in.negotiation_type,
            description=negotiation_in.description,
            start_date=negotiation_in.start_date,
            target_completion_date=negotiation_in.target_completion_date,
            primary_objectives=negotiation_in.primary_objectives,
            secondary_objectives=negotiation_in.secondary_objectives,
            minimum_acceptable_terms=negotiation_in.minimum_acceptable_terms,
            current_annual_value=negotiation_in.current_annual_value,
            target_annual_value=negotiation_in.target_annual_value,
            estimated_savings=negotiation_in.estimated_savings,
            payment_terms=negotiation_in.payment_terms,
            delivery_terms=negotiation_in.delivery_terms,
            quality_requirements=negotiation_in.quality_requirements,
            service_level_agreements=negotiation_in.service_level_agreements,
            penalty_clauses=negotiation_in.penalty_clauses,
            identified_risks=negotiation_in.identified_risks,
            mitigation_strategies=negotiation_in.mitigation_strategies,
            escalation_points=negotiation_in.escalation_points,
            negotiation_team=negotiation_in.negotiation_team,
            supplier_representatives=negotiation_in.supplier_representatives
        )

        self.db.add(db_negotiation)
        self.db.commit()
        self.db.refresh(db_negotiation)

        return db_negotiation

    def update(self, negotiation_id: str, negotiation_in: SupplierNegotiationUpdate) -> Optional[SupplierNegotiation]:
        negotiation = self.get_by_id(negotiation_id)
        if not negotiation:
            raise NotFoundError(f"Negotiation {negotiation_id} not found")

        update_data = negotiation_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(negotiation, field, value)

        negotiation.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(negotiation)

        return negotiation

    def complete(self, negotiation_id: str, final_agreement_document: Optional[str] = None) -> SupplierNegotiation:
        """交渉完了"""
        negotiation = self.get_by_id(negotiation_id)
        if not negotiation:
            raise NotFoundError(f"Negotiation {negotiation_id} not found")

        negotiation.status = "completed"
        negotiation.current_phase = "finalization"
        negotiation.actual_completion_date = date.today()
        if final_agreement_document:
            negotiation.final_agreement_document = final_agreement_document

        # Calculate success metrics
        if negotiation.primary_objectives and negotiation.achieved_outcomes:
            achieved_count = len(negotiation.achieved_outcomes)
            total_objectives = len(negotiation.primary_objectives) + len(negotiation.secondary_objectives or [])
            if total_objectives > 0:
                negotiation.objectives_achieved_percentage = Decimal(achieved_count / total_objectives * 100)

        self.db.commit()
        self.db.refresh(negotiation)

        return negotiation


class SupplierContractCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, contract_id: str) -> Optional[SupplierContract]:
        return (
            self.db.query(SupplierContract)
            .options(
                joinedload(SupplierContract.amendments),
                joinedload(SupplierContract.milestones)
            )
            .filter(SupplierContract.id == contract_id)
            .first()
        )

    def get_by_number(self, contract_number: str) -> Optional[SupplierContract]:
        return self.db.query(SupplierContract).filter(
            SupplierContract.contract_number == contract_number
        ).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[SupplierContract], int]:
        query = self.db.query(SupplierContract)

        if filters:
            if filters.get("supplier_id"):
                query = query.filter(SupplierContract.supplier_id == filters["supplier_id"])
            if filters.get("contract_manager_id"):
                query = query.filter(SupplierContract.contract_manager_id == filters["contract_manager_id"])
            if filters.get("contract_type"):
                query = query.filter(SupplierContract.contract_type == filters["contract_type"])
            if filters.get("status"):
                query = query.filter(SupplierContract.status == filters["status"])
            if filters.get("expiring_days"):
                expiry_date = date.today() + timedelta(days=filters["expiring_days"])
                query = query.filter(
                    SupplierContract.expiration_date <= expiry_date,
                    SupplierContract.expiration_date >= date.today()
                )
            if filters.get("signed"):
                if filters["signed"]:
                    query = query.filter(
                        and_(
                            SupplierContract.signed_by_supplier == True,
                            SupplierContract.signed_by_company == True
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            SupplierContract.signed_by_supplier == False,
                            SupplierContract.signed_by_company == False
                        )
                    )

        total = query.count()
        contracts = query.offset(skip).limit(limit).order_by(
            SupplierContract.created_at.desc()
        ).all()

        return contracts, total

    def create(self, contract_in: SupplierContractCreate, user_id: str) -> SupplierContract:
        # Generate contract number
        contract_number = self._generate_contract_number()

        db_contract = SupplierContract(
            id=str(uuid.uuid4()),
            contract_number=contract_number,
            supplier_id=contract_in.supplier_id,
            contract_manager_id=user_id,
            contract_title=contract_in.contract_title,
            contract_type=contract_in.contract_type,
            effective_date=contract_in.effective_date,
            expiration_date=contract_in.expiration_date,
            contract_duration_months=contract_in.contract_duration_months,
            auto_renewal=contract_in.auto_renewal,
            renewal_notice_days=contract_in.renewal_notice_days,
            contract_value=contract_in.contract_value,
            currency=contract_in.currency,
            pricing_model=contract_in.pricing_model,
            payment_terms=contract_in.payment_terms,
            payment_schedule=contract_in.payment_schedule,
            early_payment_discount=contract_in.early_payment_discount,
            late_payment_penalty=contract_in.late_payment_penalty,
            delivery_terms=contract_in.delivery_terms,
            delivery_location=contract_in.delivery_location,
            lead_time_days=contract_in.lead_time_days,
            minimum_order_quantity=contract_in.minimum_order_quantity,
            quality_standards=contract_in.quality_standards,
            compliance_requirements=contract_in.compliance_requirements,
            audit_rights=contract_in.audit_rights,
            certifications_required=contract_in.certifications_required,
            service_level_agreements=contract_in.service_level_agreements,
            key_performance_indicators=contract_in.key_performance_indicators,
            performance_bonuses=contract_in.performance_bonuses,
            performance_penalties=contract_in.performance_penalties,
            liability_cap=contract_in.liability_cap,
            insurance_requirements=contract_in.insurance_requirements,
            force_majeure_clauses=contract_in.force_majeure_clauses,
            termination_conditions=contract_in.termination_conditions,
            contract_document_path=contract_in.contract_document_path,
            related_documents=contract_in.related_documents,
            confidentiality_level=contract_in.confidentiality_level,
            tags=contract_in.tags,
            notes=contract_in.notes
        )

        self.db.add(db_contract)
        self.db.commit()
        self.db.refresh(db_contract)

        # Create renewal milestone if applicable
        if db_contract.expiration_date and db_contract.renewal_notice_days:
            milestone_date = db_contract.expiration_date - timedelta(days=db_contract.renewal_notice_days)
            self._create_renewal_milestone(db_contract.id, milestone_date)

        return db_contract

    def update(self, contract_id: str, contract_in: SupplierContractUpdate) -> Optional[SupplierContract]:
        contract = self.get_by_id(contract_id)
        if not contract:
            raise NotFoundError(f"Contract {contract_id} not found")

        update_data = contract_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        contract.updated_at = datetime.utcnow()

        # Update status if fully signed
        if contract_in.signed_by_supplier and contract_in.signed_by_company:
            contract.status = "active"
            if contract_in.signing_date:
                contract.signing_date = contract_in.signing_date

        self.db.commit()
        self.db.refresh(contract)

        return contract

    def _generate_contract_number(self) -> str:
        """契約番号生成"""
        today = datetime.now()
        prefix = f"SC-{today.year}{today.month:02d}"
        
        last_contract = (
            self.db.query(SupplierContract)
            .filter(SupplierContract.contract_number.like(f"{prefix}%"))
            .order_by(SupplierContract.contract_number.desc())
            .first()
        )
        
        if last_contract:
            last_number = int(last_contract.contract_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}-{new_number:04d}"

    def _create_renewal_milestone(self, contract_id: str, milestone_date: date):
        """更新マイルストーン作成"""
        milestone = ContractMilestone(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            milestone_name="Contract Renewal Notice",
            milestone_type="renewal",
            description="Send renewal notice to supplier",
            planned_date=milestone_date,
            reminder_days_before=7
        )
        
        self.db.add(milestone)
        self.db.commit()

    def get_expiring_contracts(self, days: int = 30) -> List[SupplierContract]:
        """期限が近い契約取得"""
        expiry_date = date.today() + timedelta(days=days)
        return (
            self.db.query(SupplierContract)
            .filter(
                SupplierContract.expiration_date <= expiry_date,
                SupplierContract.expiration_date >= date.today(),
                SupplierContract.status == "active"
            )
            .all()
        )

    def get_relationship_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """サプライヤー関係分析データ取得"""
        query = self.db.query(SupplierRelationship)

        if filters:
            if filters.get("date_from"):
                query = query.filter(SupplierRelationship.created_at >= filters["date_from"])
            if filters.get("date_to"):
                query = query.filter(SupplierRelationship.created_at <= filters["date_to"])

        relationships = query.all()
        
        total_relationships = len(relationships)
        active_relationships = len([r for r in relationships if r.status == "active"])
        strategic_partnerships = len([r for r in relationships if r.partnership_level == "strategic"])
        
        # 平均スコア
        scores = [r.overall_score for r in relationships if r.overall_score > 0]
        avg_relationship_score = sum(scores) / len(scores) if scores else Decimal('0')
        
        # 支出統計
        total_annual_spend = sum(r.annual_spend for r in relationships)
        cost_savings_achieved = sum(r.cost_savings_achieved for r in relationships)
        
        # 期限切れ契約
        contracts_expiring_soon = len(self.get_expiring_contracts(30))
        
        # レビュー期限切れ
        reviews_overdue = len([r for r in relationships 
                             if r.next_review_date and r.next_review_date < date.today()])
        
        # パートナーシップレベル別分布
        by_partnership_level = {}
        for level in ["strategic", "preferred", "standard", "conditional"]:
            count = len([r for r in relationships if r.partnership_level == level])
            by_partnership_level[level] = count
        
        # リスクレベル別分布
        by_risk_level = {}
        for level in ["critical", "high", "medium", "low"]:
            count = len([r for r in relationships if r.risk_level == level])
            by_risk_level[level] = count
        
        # トップサプライヤー（支出別）
        top_suppliers = sorted(relationships, key=lambda x: x.annual_spend, reverse=True)[:5]
        top_suppliers_data = [
            {
                "supplier_id": r.supplier_id,
                "annual_spend": r.annual_spend,
                "overall_score": r.overall_score,
                "partnership_level": r.partnership_level
            }
            for r in top_suppliers
        ]
        
        # 関係タイプ別分布
        relationship_distribution = {}
        for rel_type in ["vendor", "partner", "strategic", "preferred"]:
            count = len([r for r in relationships if r.relationship_type == rel_type])
            relationship_distribution[rel_type] = count

        return {
            "total_relationships": total_relationships,
            "active_relationships": active_relationships,
            "strategic_partnerships": strategic_partnerships,
            "avg_relationship_score": avg_relationship_score,
            "total_annual_spend": total_annual_spend,
            "cost_savings_achieved": cost_savings_achieved,
            "contracts_expiring_soon": contracts_expiring_soon,
            "reviews_overdue": reviews_overdue,
            "by_partnership_level": by_partnership_level,
            "by_risk_level": by_risk_level,
            "top_suppliers_by_spend": top_suppliers_data,
            "relationship_distribution": relationship_distribution
        }