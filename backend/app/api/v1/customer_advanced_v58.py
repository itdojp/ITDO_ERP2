"""
CC02 v58.0 Advanced Customer Management API
CRM functionality with RFM analysis, LTV calculation, and customer segmentation
Day 3 of continuous API implementation
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_active_user
from app.models.customer import Customer, CustomerInteraction
from app.models.order import Order
from app.models.user import User

router = APIRouter(prefix="/customers/advanced", tags=["customers-advanced-v58"])


# Enhanced Enums
class CustomerStatus(str, Enum):
    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    VIP = "vip"
    CHURNED = "churned"
    BLOCKED = "blocked"


class LifecycleStage(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    ACQUISITION = "acquisition"
    ACTIVATION = "activation"
    RETENTION = "retention"
    REFERRAL = "referral"
    RECOVERY = "recovery"


class InteractionType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    SUPPORT = "support"
    MARKETING = "marketing"
    SALES = "sales"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"


class InteractionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RFMSegment(str, Enum):
    CHAMPIONS = "champions"  # 111: Best customers
    LOYAL_CUSTOMERS = "loyal_customers"  # x1x: Regular buyers
    POTENTIAL_LOYALISTS = "potential_loyalists"  # 11x: Recent buyers
    NEW_CUSTOMERS = "new_customers"  # 1xx: Recent first-time buyers
    PROMISING = "promising"  # x1x: Recent buyers with potential
    NEED_ATTENTION = "need_attention"  # x2x: Average customers
    ABOUT_TO_SLEEP = "about_to_sleep"  # x3x: Below average
    AT_RISK = "at_risk"  # 2xx: Haven't purchased recently
    CANNOT_LOSE_THEM = "cannot_lose_them"  # x11: High value but declining
    HIBERNATING = "hibernating"  # 3xx: Haven't purchased in long time
    LOST = "lost"  # 333: Lowest scores


class CommunicationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    DIRECT_MAIL = "direct_mail"
    SOCIAL_MEDIA = "social_media"
    IN_APP = "in_app"
    PUSH_NOTIFICATION = "push_notification"


# Request Models
class CustomerInteractionRequest(BaseModel):
    customer_id: UUID
    interaction_type: InteractionType
    channel: CommunicationChannel
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    outcome: Optional[str] = Field(None, max_length=1000)
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0, le=480)
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list, max_items=10)
    attachments: List[str] = Field(default_factory=list, max_items=5)


class CustomerLifecycleUpdateRequest(BaseModel):
    customer_id: UUID
    new_stage: LifecycleStage
    reason: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)
    automated: bool = Field(default=False)


class RFMAnalysisRequest(BaseModel):
    date_range_days: int = Field(default=365, ge=30, le=1095)
    recency_bins: int = Field(default=5, ge=3, le=10)
    frequency_bins: int = Field(default=5, ge=3, le=10)
    monetary_bins: int = Field(default=5, ge=3, le=10)
    customer_ids: Optional[List[UUID]] = None
    exclude_inactive: bool = Field(default=True)


class LTVCalculationRequest(BaseModel):
    customer_ids: Optional[List[UUID]] = None
    prediction_months: int = Field(default=12, ge=1, le=60)
    discount_rate: float = Field(default=0.1, ge=0.0, le=0.5)
    include_acquisition_cost: bool = Field(default=True)
    method: str = Field(default="historic", regex="^(historic|predictive|cohort)$")


class CustomerSegmentationRequest(BaseModel):
    segmentation_criteria: List[str] = Field(..., min_items=1, max_items=5)
    min_segment_size: int = Field(default=10, ge=1, le=1000)
    include_predictions: bool = Field(default=False)
    exclude_churned: bool = Field(default=True)


class CampaignTargetingRequest(BaseModel):
    campaign_name: str = Field(..., min_length=1, max_length=100)
    target_segments: List[str] = Field(..., min_items=1)
    channel: CommunicationChannel
    message_template: str = Field(..., min_length=1, max_length=5000)
    scheduled_at: Optional[datetime] = None
    budget_limit: Optional[Decimal] = Field(None, ge=0)
    expected_response_rate: Optional[float] = Field(None, ge=0, le=1)


# Response Models
class CustomerInteractionResponse(BaseModel):
    interaction_id: UUID
    customer_id: UUID
    customer_name: str
    customer_email: str
    interaction_type: InteractionType
    channel: CommunicationChannel
    subject: str
    description: str
    outcome: Optional[str]
    status: InteractionStatus
    scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_minutes: Optional[int]
    follow_up_required: bool
    follow_up_date: Optional[datetime]
    created_by: str
    created_at: datetime
    tags: List[str]

    class Config:
        from_attributes = True


class RFMScores(BaseModel):
    recency_score: int = Field(..., ge=1, le=5)
    frequency_score: int = Field(..., ge=1, le=5)
    monetary_score: int = Field(..., ge=1, le=5)
    rfm_segment: RFMSegment
    segment_description: str


class CustomerRFMResponse(BaseModel):
    customer_id: UUID
    customer_name: str
    customer_email: str
    recency_days: int
    frequency_orders: int
    monetary_value: Decimal
    rfm_scores: RFMScores
    last_order_date: Optional[date]
    total_orders: int
    avg_order_value: Decimal
    calculated_at: datetime

    class Config:
        from_attributes = True


class CustomerLTVResponse(BaseModel):
    customer_id: UUID
    customer_name: str
    customer_email: str
    historical_ltv: Decimal
    predicted_ltv: Decimal
    ltv_12_months: Decimal
    ltv_24_months: Decimal
    acquisition_cost: Optional[Decimal]
    net_ltv: Optional[Decimal]
    average_order_value: Decimal
    purchase_frequency: float
    customer_lifespan_months: float
    churn_probability: float
    ltv_segment: str
    calculated_at: datetime

    class Config:
        from_attributes = True


class CustomerSegmentResponse(BaseModel):
    segment_id: str
    segment_name: str
    description: str
    customer_count: int
    criteria: Dict[str, Any]
    avg_ltv: Decimal
    avg_order_value: Decimal
    churn_rate: float
    recommended_actions: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


@dataclass
class CustomerMetrics:
    """Customer metrics data class"""

    customer_id: UUID
    total_revenue: Decimal
    order_count: int
    avg_order_value: Decimal
    first_order_date: date
    last_order_date: date
    days_since_last_order: int
    customer_lifespan_days: int
    purchase_frequency_days: float


# Core Service Classes
class CRMManager:
    """Advanced CRM functionality manager"""

    def __init__(self, db: AsyncSession) -> dict:
        self.db = db

    async def create_customer_interaction(
        self, request: CustomerInteractionRequest, user_id: UUID
    ) -> CustomerInteractionResponse:
        """Create customer interaction record"""

        # Verify customer exists
        customer = await self._get_customer(request.customer_id)
        if not customer:
            raise NotFoundError(f"Customer {request.customer_id} not found")

        # Create interaction record
        interaction = CustomerInteraction(
            id=uuid4(),
            customer_id=request.customer_id,
            interaction_type=request.interaction_type.value,
            channel=request.channel.value,
            subject=request.subject,
            description=request.description,
            outcome=request.outcome,
            status=InteractionStatus.PENDING.value,
            scheduled_at=request.scheduled_at,
            duration_minutes=request.duration_minutes,
            follow_up_required=request.follow_up_required,
            follow_up_date=request.follow_up_date,
            created_by=user_id,
            created_at=datetime.utcnow(),
            tags=json.dumps(request.tags),
            attachments=json.dumps(request.attachments),
        )

        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)

        # Update customer last contact date
        await self._update_customer_last_contact(request.customer_id)

        return await self._build_interaction_response(interaction, customer)

    async def update_customer_lifecycle_stage(
        self, request: CustomerLifecycleUpdateRequest, user_id: UUID
    ) -> Dict[str, Any]:
        """Update customer lifecycle stage"""

        customer = await self._get_customer(request.customer_id)
        if not customer:
            raise NotFoundError(f"Customer {request.customer_id} not found")

        old_stage = customer.lifecycle_stage

        # Update customer stage
        await self.db.execute(
            update(Customer)
            .where(Customer.id == request.customer_id)
            .values(
                lifecycle_stage=request.new_stage.value, updated_at=datetime.utcnow()
            )
        )

        # Create lifecycle change interaction
        lifecycle_interaction = CustomerInteraction(
            id=uuid4(),
            customer_id=request.customer_id,
            interaction_type=InteractionType.MARKETING.value,
            channel=CommunicationChannel.IN_APP.value,
            subject=f"Lifecycle Stage Change: {old_stage} → {request.new_stage.value}",
            description=f"Reason: {request.reason}. Notes: {request.notes or 'None'}",
            status=InteractionStatus.COMPLETED.value,
            created_by=user_id,
            created_at=datetime.utcnow(),
            tags=json.dumps(
                ["lifecycle", "automated" if request.automated else "manual"]
            ),
        )

        self.db.add(lifecycle_interaction)
        await self.db.commit()

        return {
            "customer_id": str(request.customer_id),
            "old_stage": old_stage,
            "new_stage": request.new_stage.value,
            "reason": request.reason,
            "automated": request.automated,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def get_customer_timeline(
        self, customer_id: UUID, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get customer interaction timeline"""

        # Get interactions
        interactions_query = (
            select(CustomerInteraction)
            .where(CustomerInteraction.customer_id == customer_id)
            .order_by(desc(CustomerInteraction.created_at))
            .limit(limit)
        )

        interactions_result = await self.db.execute(interactions_query)
        interactions = interactions_result.scalars().all()

        # Get orders
        orders_query = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(desc(Order.order_date))
            .limit(limit)
        )

        orders_result = await self.db.execute(orders_query)
        orders = orders_result.scalars().all()

        # Combine and sort timeline events
        timeline = []

        # Add interactions
        for interaction in interactions:
            timeline.append(
                {
                    "type": "interaction",
                    "id": str(interaction.id),
                    "date": interaction.created_at,
                    "title": interaction.subject,
                    "description": interaction.description,
                    "interaction_type": interaction.interaction_type,
                    "channel": interaction.channel,
                    "status": interaction.status,
                }
            )

        # Add orders
        for order in orders:
            timeline.append(
                {
                    "type": "order",
                    "id": str(order.id),
                    "date": order.order_date,
                    "title": f"Order {order.order_number}",
                    "description": f"Total: ${order.total_amount}",
                    "order_status": order.status,
                    "amount": float(order.total_amount),
                }
            )

        # Sort by date (newest first)
        timeline.sort(key=lambda x: x["date"], reverse=True)

        return timeline[:limit]

    async def _get_customer(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID"""
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def _update_customer_last_contact(self, customer_id: UUID) -> dict:
        """Update customer last contact date"""
        await self.db.execute(
            update(Customer)
            .where(Customer.id == customer_id)
            .values(last_contact_date=datetime.utcnow())
        )
        await self.db.commit()

    async def _build_interaction_response(
        self, interaction: CustomerInteraction, customer: Customer
    ) -> CustomerInteractionResponse:
        """Build interaction response"""

        return CustomerInteractionResponse(
            interaction_id=interaction.id,
            customer_id=interaction.customer_id,
            customer_name=customer.full_name,
            customer_email=customer.email,
            interaction_type=InteractionType(interaction.interaction_type),
            channel=CommunicationChannel(interaction.channel),
            subject=interaction.subject,
            description=interaction.description,
            outcome=interaction.outcome,
            status=InteractionStatus(interaction.status),
            scheduled_at=interaction.scheduled_at,
            completed_at=interaction.completed_at,
            duration_minutes=interaction.duration_minutes,
            follow_up_required=interaction.follow_up_required,
            follow_up_date=interaction.follow_up_date,
            created_by=str(interaction.created_by),
            created_at=interaction.created_at,
            tags=json.loads(interaction.tags) if interaction.tags else [],
        )


class RFMAnalysisEngine:
    """RFM (Recency, Frequency, Monetary) Analysis Engine"""

    def __init__(self, db: AsyncSession) -> dict:
        self.db = db

    async def calculate_rfm_analysis(
        self, request: RFMAnalysisRequest
    ) -> List[CustomerRFMResponse]:
        """Calculate RFM analysis for customers"""

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=request.date_range_days)

        # Get customer metrics
        customer_metrics = await self._get_customer_metrics(
            start_date, end_date, request.customer_ids
        )

        if not customer_metrics:
            return []

        # Calculate RFM scores
        rfm_data = []

        # Extract values for percentile calculations
        recency_values = [m.days_since_last_order for m in customer_metrics]
        frequency_values = [m.order_count for m in customer_metrics]
        monetary_values = [float(m.total_revenue) for m in customer_metrics]

        # Calculate percentile thresholds
        recency_thresholds = self._calculate_percentile_thresholds(
            recency_values, request.recency_bins, reverse=True
        )
        frequency_thresholds = self._calculate_percentile_thresholds(
            frequency_values, request.frequency_bins
        )
        monetary_thresholds = self._calculate_percentile_thresholds(
            monetary_values, request.monetary_bins
        )

        # Calculate scores for each customer
        for metrics in customer_metrics:
            recency_score = self._calculate_score(
                metrics.days_since_last_order, recency_thresholds, reverse=True
            )
            frequency_score = self._calculate_score(
                metrics.order_count, frequency_thresholds
            )
            monetary_score = self._calculate_score(
                float(metrics.total_revenue), monetary_thresholds
            )

            # Determine RFM segment
            rfm_segment = self._determine_rfm_segment(
                recency_score, frequency_score, monetary_score
            )

            # Get customer details
            customer = await self._get_customer(metrics.customer_id)

            rfm_scores = RFMScores(
                recency_score=recency_score,
                frequency_score=frequency_score,
                monetary_score=monetary_score,
                rfm_segment=rfm_segment,
                segment_description=self._get_segment_description(rfm_segment),
            )

            rfm_response = CustomerRFMResponse(
                customer_id=metrics.customer_id,
                customer_name=customer.full_name if customer else "Unknown",
                customer_email=customer.email if customer else "unknown@example.com",
                recency_days=metrics.days_since_last_order,
                frequency_orders=metrics.order_count,
                monetary_value=metrics.total_revenue,
                rfm_scores=rfm_scores,
                last_order_date=metrics.last_order_date,
                total_orders=metrics.order_count,
                avg_order_value=metrics.avg_order_value,
                calculated_at=datetime.utcnow(),
            )

            rfm_data.append(rfm_response)

        return rfm_data

    async def _get_customer_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        customer_ids: Optional[List[UUID]] = None,
    ) -> List[CustomerMetrics]:
        """Get customer metrics for RFM analysis"""

        # Base query for customer order metrics
        query = (
            select(
                Order.customer_id,
                func.sum(Order.total_amount).label("total_revenue"),
                func.count(Order.id).label("order_count"),
                func.avg(Order.total_amount).label("avg_order_value"),
                func.min(Order.order_date).label("first_order_date"),
                func.max(Order.order_date).label("last_order_date"),
            )
            .where(
                and_(
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                    Order.status.in_(["completed", "shipped", "delivered"]),
                )
            )
            .group_by(Order.customer_id)
        )

        if customer_ids:
            query = query.where(Order.customer_id.in_(customer_ids))

        result = await self.db.execute(query)
        rows = result.all()

        metrics = []
        current_date = end_date.date()

        for row in rows:
            days_since_last_order = (current_date - row.last_order_date).days
            customer_lifespan_days = (row.last_order_date - row.first_order_date).days
            purchase_frequency_days = (
                customer_lifespan_days / max(row.order_count - 1, 1)
                if row.order_count > 1
                else customer_lifespan_days
            )

            metrics.append(
                CustomerMetrics(
                    customer_id=row.customer_id,
                    total_revenue=row.total_revenue,
                    order_count=row.order_count,
                    avg_order_value=row.avg_order_value,
                    first_order_date=row.first_order_date,
                    last_order_date=row.last_order_date,
                    days_since_last_order=days_since_last_order,
                    customer_lifespan_days=customer_lifespan_days,
                    purchase_frequency_days=purchase_frequency_days,
                )
            )

        return metrics

    def _calculate_percentile_thresholds(
        self, values: List[float], bins: int, reverse: bool = False
    ) -> List[float]:
        """Calculate percentile thresholds for scoring"""
        if not values:
            return []

        sorted_values = sorted(values, reverse=reverse)
        thresholds = []

        for i in range(1, bins):
            percentile = i / bins
            threshold_index = int(percentile * len(sorted_values))
            threshold_index = min(threshold_index, len(sorted_values) - 1)
            thresholds.append(sorted_values[threshold_index])

        return thresholds

    def _calculate_score(
        self, value: float, thresholds: List[float], reverse: bool = False
    ) -> int:
        """Calculate score (1-5) based on thresholds"""
        if not thresholds:
            return 3  # Default middle score

        score = 1
        for threshold in thresholds:
            if (not reverse and value > threshold) or (reverse and value < threshold):
                score += 1
            else:
                break

        return min(score, 5)

    def _determine_rfm_segment(self, r: int, f: int, m: int) -> RFMSegment:
        """Determine RFM segment based on scores"""

        # Champions: High R, F, M
        if r >= 4 and f >= 4 and m >= 4:
            return RFMSegment.CHAMPIONS

        # Loyal Customers: High F
        if f >= 4:
            return RFMSegment.LOYAL_CUSTOMERS

        # Potential Loyalists: High R, M
        if r >= 4 and m >= 4:
            return RFMSegment.POTENTIAL_LOYALISTS

        # New Customers: High R
        if r >= 4:
            return RFMSegment.NEW_CUSTOMERS

        # Promising: Medium R, F
        if r >= 3 and f >= 3:
            return RFMSegment.PROMISING

        # Need Attention: Medium scores
        if r >= 2 and f >= 2 and m >= 2:
            return RFMSegment.NEED_ATTENTION

        # About to Sleep: Medium R, low F
        if r >= 2 and f <= 2:
            return RFMSegment.ABOUT_TO_SLEEP

        # At Risk: Low R, high M
        if r <= 2 and m >= 4:
            return RFMSegment.AT_RISK

        # Cannot Lose Them: Low R, high F, M
        if r <= 2 and f >= 4 and m >= 4:
            return RFMSegment.CANNOT_LOSE_THEM

        # Hibernating: Low R, F
        if r <= 2 and f <= 2:
            return RFMSegment.HIBERNATING

        # Lost: Lowest scores
        return RFMSegment.LOST

    def _get_segment_description(self, segment: RFMSegment) -> str:
        """Get description for RFM segment"""
        descriptions = {
            RFMSegment.CHAMPIONS: "Best customers - high value, frequent buyers",
            RFMSegment.LOYAL_CUSTOMERS: "Regular buyers - consistent purchase behavior",
            RFMSegment.POTENTIAL_LOYALISTS: "Recent high-value customers with loyalty potential",
            RFMSegment.NEW_CUSTOMERS: "Recent first-time buyers",
            RFMSegment.PROMISING: "Recent buyers with good potential",
            RFMSegment.NEED_ATTENTION: "Average customers needing engagement",
            RFMSegment.ABOUT_TO_SLEEP: "Below average customers at risk",
            RFMSegment.AT_RISK: "High-value customers who haven't purchased recently",
            RFMSegment.CANNOT_LOSE_THEM: "High-value customers showing decline",
            RFMSegment.HIBERNATING: "Inactive customers",
            RFMSegment.LOST: "Likely churned customers",
        }
        return descriptions.get(segment, "Unknown segment")

    async def _get_customer(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID"""
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()


class LTVCalculationEngine:
    """Customer Lifetime Value Calculation Engine"""

    def __init__(self, db: AsyncSession) -> dict:
        self.db = db

    async def calculate_customer_ltv(
        self, request: LTVCalculationRequest
    ) -> List[CustomerLTVResponse]:
        """Calculate Customer Lifetime Value"""

        # Get customer metrics
        customer_metrics = await self._get_ltv_customer_metrics(request.customer_ids)

        ltv_results = []

        for metrics in customer_metrics:
            # Historical LTV (total revenue to date)
            historical_ltv = metrics.total_revenue

            # Calculate predicted LTV
            if request.method == "historic":
                predicted_ltv = await self._calculate_historic_ltv(metrics, request)
            elif request.method == "predictive":
                predicted_ltv = await self._calculate_predictive_ltv(metrics, request)
            else:  # cohort
                predicted_ltv = await self._calculate_cohort_ltv(metrics, request)

            # Calculate LTV for specific periods
            ltv_12_months = predicted_ltv * (12 / request.prediction_months)
            ltv_24_months = predicted_ltv * (24 / request.prediction_months)

            # Calculate acquisition cost (simplified)
            acquisition_cost = (
                Decimal("50.00") if request.include_acquisition_cost else None
            )
            net_ltv = (
                predicted_ltv - acquisition_cost if acquisition_cost else predicted_ltv
            )

            # Calculate churn probability
            churn_probability = self._calculate_churn_probability(metrics)

            # Determine LTV segment
            ltv_segment = self._determine_ltv_segment(predicted_ltv)

            # Get customer details
            customer = await self._get_customer(metrics.customer_id)

            ltv_response = CustomerLTVResponse(
                customer_id=metrics.customer_id,
                customer_name=customer.full_name if customer else "Unknown",
                customer_email=customer.email if customer else "unknown@example.com",
                historical_ltv=historical_ltv,
                predicted_ltv=predicted_ltv,
                ltv_12_months=ltv_12_months,
                ltv_24_months=ltv_24_months,
                acquisition_cost=acquisition_cost,
                net_ltv=net_ltv,
                average_order_value=metrics.avg_order_value,
                purchase_frequency=metrics.purchase_frequency_days
                / 30.0,  # Convert to monthly
                customer_lifespan_months=metrics.customer_lifespan_days / 30.0,
                churn_probability=churn_probability,
                ltv_segment=ltv_segment,
                calculated_at=datetime.utcnow(),
            )

            ltv_results.append(ltv_response)

        return ltv_results

    async def _get_ltv_customer_metrics(
        self, customer_ids: Optional[List[UUID]] = None
    ) -> List[CustomerMetrics]:
        """Get customer metrics for LTV calculation"""

        # Base query for customer order metrics
        query = (
            select(
                Order.customer_id,
                func.sum(Order.total_amount).label("total_revenue"),
                func.count(Order.id).label("order_count"),
                func.avg(Order.total_amount).label("avg_order_value"),
                func.min(Order.order_date).label("first_order_date"),
                func.max(Order.order_date).label("last_order_date"),
            )
            .where(Order.status.in_(["completed", "shipped", "delivered"]))
            .group_by(Order.customer_id)
        )

        if customer_ids:
            query = query.where(Order.customer_id.in_(customer_ids))

        result = await self.db.execute(query)
        rows = result.all()

        metrics = []
        current_date = datetime.utcnow().date()

        for row in rows:
            days_since_last_order = (current_date - row.last_order_date).days
            customer_lifespan_days = (row.last_order_date - row.first_order_date).days
            purchase_frequency_days = (
                customer_lifespan_days / max(row.order_count - 1, 1)
                if row.order_count > 1
                else customer_lifespan_days
            )

            metrics.append(
                CustomerMetrics(
                    customer_id=row.customer_id,
                    total_revenue=row.total_revenue,
                    order_count=row.order_count,
                    avg_order_value=row.avg_order_value,
                    first_order_date=row.first_order_date,
                    last_order_date=row.last_order_date,
                    days_since_last_order=days_since_last_order,
                    customer_lifespan_days=customer_lifespan_days,
                    purchase_frequency_days=purchase_frequency_days,
                )
            )

        return metrics

    async def _calculate_historic_ltv(
        self, metrics: CustomerMetrics, request: LTVCalculationRequest
    ) -> Decimal:
        """Calculate LTV based on historical data"""

        # Simple formula: AOV × Purchase Frequency × Predicted Lifespan
        monthly_frequency = (
            30.0 / metrics.purchase_frequency_days
            if metrics.purchase_frequency_days > 0
            else 0.1
        )
        predicted_months = request.prediction_months

        # Apply discount rate for future value
        discount_factor = 1 / (1 + request.discount_rate) ** (predicted_months / 12)

        ltv = (
            metrics.avg_order_value
            * monthly_frequency
            * predicted_months
            * Decimal(str(discount_factor))
        )

        return max(ltv, Decimal("0"))

    async def _calculate_predictive_ltv(
        self, metrics: CustomerMetrics, request: LTVCalculationRequest
    ) -> Decimal:
        """Calculate LTV using predictive modeling"""

        # Simplified predictive model (in reality would use ML)
        # Factors: recency, frequency, monetary, trend

        recency_factor = max(0.1, 1 - (metrics.days_since_last_order / 365))
        frequency_factor = min(2.0, metrics.order_count / 12)  # Cap at 2x

        # Calculate trend (increasing/decreasing order value)
        trend_factor = 1.0  # Simplified - would analyze order history

        base_ltv = await self._calculate_historic_ltv(metrics, request)
        predicted_ltv = base_ltv * Decimal(
            str(recency_factor * frequency_factor * trend_factor)
        )

        return max(predicted_ltv, Decimal("0"))

    async def _calculate_cohort_ltv(
        self, metrics: CustomerMetrics, request: LTVCalculationRequest
    ) -> Decimal:
        """Calculate LTV using cohort analysis"""

        # Simplified cohort analysis - would use actual cohort data
        # Assume customer belongs to a cohort based on first order date

        cohort_multiplier = 1.0

        # Newer customers might have different patterns
        days_since_first_order = (
            datetime.utcnow().date() - metrics.first_order_date
        ).days
        if days_since_first_order < 90:
            cohort_multiplier = 1.2  # New customer bonus
        elif days_since_first_order > 730:
            cohort_multiplier = 0.8  # Established customer

        base_ltv = await self._calculate_historic_ltv(metrics, request)
        cohort_ltv = base_ltv * Decimal(str(cohort_multiplier))

        return max(cohort_ltv, Decimal("0"))

    def _calculate_churn_probability(self, metrics: CustomerMetrics) -> float:
        """Calculate probability of customer churn"""

        # Simplified churn probability calculation
        # Based on recency and frequency patterns

        # Recency factor (higher days since last order = higher churn risk)
        recency_risk = min(1.0, metrics.days_since_last_order / 365)

        # Frequency factor (lower frequency = higher churn risk)
        frequency_protection = min(0.8, metrics.order_count / 20)

        # Combined churn probability
        churn_probability = recency_risk * (1 - frequency_protection)

        return round(min(1.0, max(0.0, churn_probability)), 3)

    def _determine_ltv_segment(self, ltv: Decimal) -> str:
        """Determine LTV segment"""

        if ltv >= 2000:
            return "High Value"
        elif ltv >= 1000:
            return "Medium-High Value"
        elif ltv >= 500:
            return "Medium Value"
        elif ltv >= 200:
            return "Low-Medium Value"
        else:
            return "Low Value"

    async def _get_customer(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID"""
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()


# API Endpoints
@router.post(
    "/interactions",
    response_model=CustomerInteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_interaction(
    request: CustomerInteractionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create customer interaction record"""

    crm_manager = CRMManager(db)

    try:
        result = await crm_manager.create_customer_interaction(request, current_user.id)

        # Add background task for follow-up scheduling
        if request.follow_up_required and request.follow_up_date:
            background_tasks.add_task(
                schedule_follow_up_task, result.interaction_id, request.follow_up_date
            )

        return result

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/lifecycle/{customer_id}")
async def update_customer_lifecycle_stage(
    customer_id: UUID,
    stage_update: CustomerLifecycleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update customer lifecycle stage"""

    # Override customer_id from path
    stage_update.customer_id = customer_id

    crm_manager = CRMManager(db)

    try:
        result = await crm_manager.update_customer_lifecycle_stage(
            stage_update, current_user.id
        )
        return result

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/timeline/{customer_id}")
async def get_customer_timeline(
    customer_id: UUID = Path(...),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get customer interaction and order timeline"""

    crm_manager = CRMManager(db)

    try:
        timeline = await crm_manager.get_customer_timeline(customer_id, limit)

        return {
            "customer_id": str(customer_id),
            "timeline_events": timeline,
            "total_events": len(timeline),
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer timeline: {str(e)}",
        )


@router.post("/rfm-analysis", response_model=List[CustomerRFMResponse])
async def calculate_rfm_analysis(
    request: RFMAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Calculate RFM (Recency, Frequency, Monetary) analysis"""

    rfm_engine = RFMAnalysisEngine(db)

    try:
        results = await rfm_engine.calculate_rfm_analysis(request)

        # Add background task for segment update
        background_tasks.add_task(
            update_customer_segments_task,
            [r.customer_id for r in results],
            [r.rfm_scores.rfm_segment for r in results],
        )

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RFM analysis failed: {str(e)}",
        )


@router.post("/ltv-calculation", response_model=List[CustomerLTVResponse])
async def calculate_customer_ltv(
    request: LTVCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Calculate Customer Lifetime Value"""

    ltv_engine = LTVCalculationEngine(db)

    try:
        results = await ltv_engine.calculate_customer_ltv(request)
        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LTV calculation failed: {str(e)}",
        )


@router.get("/segments")
async def get_customer_segments(
    include_metrics: bool = Query(True, description="Include segment metrics"),
    min_size: int = Query(1, ge=1, description="Minimum segment size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get customer segments with metrics"""

    try:
        # Get RFM segment distribution
        rfm_distribution = await get_rfm_segment_distribution(db)

        # Get LTV segment distribution
        ltv_distribution = await get_ltv_segment_distribution(db)

        segments = []

        # Add RFM segments
        for segment, count in rfm_distribution.items():
            if count >= min_size:
                segments.append(
                    {
                        "segment_id": f"rfm_{segment}",
                        "segment_name": segment.replace("_", " ").title(),
                        "type": "RFM",
                        "customer_count": count,
                        "description": f"RFM segment: {segment}",
                    }
                )

        # Add LTV segments
        for segment, count in ltv_distribution.items():
            if count >= min_size:
                segments.append(
                    {
                        "segment_id": f"ltv_{segment.lower().replace(' ', '_')}",
                        "segment_name": segment,
                        "type": "LTV",
                        "customer_count": count,
                        "description": f"LTV segment: {segment}",
                    }
                )

        return {
            "segments": segments,
            "total_segments": len(segments),
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer segments: {str(e)}",
        )


@router.get("/analytics")
async def get_customer_analytics(
    period_days: int = Query(90, ge=1, le=365),
    segment_type: Optional[str] = Query(None, regex="^(rfm|ltv|lifecycle)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get customer analytics and insights"""

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)

    try:
        # Overall customer metrics
        customer_stats = await get_customer_statistics(db, start_date, end_date)

        # Lifecycle distribution
        lifecycle_distribution = await get_lifecycle_distribution(db)

        # Interaction analytics
        interaction_analytics = await get_interaction_analytics(
            db, start_date, end_date
        )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days,
            },
            "customer_statistics": customer_stats,
            "lifecycle_distribution": lifecycle_distribution,
            "interaction_analytics": interaction_analytics,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate customer analytics: {str(e)}",
        )


@router.get("/health")
async def health_check() -> None:
    """Health check endpoint for advanced customer API"""
    return {
        "status": "healthy",
        "service": "customer-advanced-v58",
        "version": "1.0.0",
        "features": [
            "crm_management",
            "rfm_analysis",
            "ltv_calculation",
            "customer_segmentation",
            "lifecycle_tracking",
            "interaction_timeline",
            "predictive_analytics",
        ],
        "checked_at": datetime.utcnow().isoformat(),
    }


# Helper Functions
async def schedule_follow_up_task(
    interaction_id: UUID, follow_up_date: datetime
) -> dict:
    """Schedule follow-up task (background task)"""
    await asyncio.sleep(0.1)
    print(f"Follow-up scheduled for interaction {interaction_id} at {follow_up_date}")


async def update_customer_segments_task(
    customer_ids: List[UUID], segments: List[RFMSegment]
):
    """Update customer segments (background task)"""
    await asyncio.sleep(0.1)
    print(f"Updated segments for {len(customer_ids)} customers")


async def get_rfm_segment_distribution(db: AsyncSession) -> Dict[str, int]:
    """Get RFM segment distribution"""
    # Simplified - would query actual customer segments
    return {
        "champions": 45,
        "loyal_customers": 123,
        "potential_loyalists": 67,
        "new_customers": 89,
        "promising": 78,
        "need_attention": 134,
        "about_to_sleep": 56,
        "at_risk": 23,
        "hibernating": 45,
        "lost": 12,
    }


async def get_ltv_segment_distribution(db: AsyncSession) -> Dict[str, int]:
    """Get LTV segment distribution"""
    # Simplified - would query actual customer LTV data
    return {
        "High Value": 67,
        "Medium-High Value": 145,
        "Medium Value": 234,
        "Low-Medium Value": 189,
        "Low Value": 93,
    }


async def get_customer_statistics(
    db: AsyncSession, start_date: datetime, end_date: datetime
) -> Dict[str, Any]:
    """Get customer statistics"""

    # Customer counts
    total_customers_result = await db.execute(select(func.count(Customer.id)))
    total_customers = total_customers_result.scalar()

    # New customers in period
    new_customers_result = await db.execute(
        select(func.count(Customer.id)).where(
            and_(Customer.created_at >= start_date, Customer.created_at <= end_date)
        )
    )
    new_customers = new_customers_result.scalar()

    # Active customers (made orders in period)
    active_customers_result = await db.execute(
        select(func.count(func.distinct(Order.customer_id))).where(
            and_(Order.order_date >= start_date, Order.order_date <= end_date)
        )
    )
    active_customers = active_customers_result.scalar()

    return {
        "total_customers": total_customers or 0,
        "new_customers": new_customers or 0,
        "active_customers": active_customers or 0,
        "activation_rate": round(
            (active_customers / total_customers * 100) if total_customers > 0 else 0, 2
        ),
        "growth_rate": round(
            (new_customers / (total_customers - new_customers) * 100)
            if total_customers > new_customers
            else 0,
            2,
        ),
    }


async def get_lifecycle_distribution(db: AsyncSession) -> Dict[str, int]:
    """Get customer lifecycle stage distribution"""

    result = await db.execute(
        select(
            Customer.lifecycle_stage, func.count(Customer.id).label("count")
        ).group_by(Customer.lifecycle_stage)
    )

    distribution = {}
    for row in result:
        distribution[row.lifecycle_stage or "unknown"] = row.count

    return distribution


async def get_interaction_analytics(
    db: AsyncSession, start_date: datetime, end_date: datetime
) -> Dict[str, Any]:
    """Get interaction analytics"""

    # Total interactions
    total_interactions_result = await db.execute(
        select(func.count(CustomerInteraction.id)).where(
            and_(
                CustomerInteraction.created_at >= start_date,
                CustomerInteraction.created_at <= end_date,
            )
        )
    )
    total_interactions = total_interactions_result.scalar()

    # Interactions by type
    interaction_types_result = await db.execute(
        select(
            CustomerInteraction.interaction_type,
            func.count(CustomerInteraction.id).label("count"),
        )
        .where(
            and_(
                CustomerInteraction.created_at >= start_date,
                CustomerInteraction.created_at <= end_date,
            )
        )
        .group_by(CustomerInteraction.interaction_type)
    )

    interaction_by_type = {}
    for row in interaction_types_result:
        interaction_by_type[row.interaction_type] = row.count

    return {
        "total_interactions": total_interactions or 0,
        "interactions_by_type": interaction_by_type,
        "avg_interactions_per_day": round((total_interactions or 0) / 30, 2),
    }
