"""
ITDO ERP Backend - Product Pricing & Discount Management v66
Advanced pricing system with dynamic pricing, discounts, and promotional campaigns
Day 8: Product Pricing & Discount Management Implementation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import aioredis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from sqlalchemy.sql import and_, func, or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.base import BaseTable

# ============================================================================
# Enums and Constants
# ============================================================================


class DiscountType(str, Enum):
    """Discount type enumeration"""

    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BUY_X_GET_Y = "buy_x_get_y"
    BULK_PRICING = "bulk_pricing"
    TIERED_PRICING = "tiered_pricing"


class DiscountScope(str, Enum):
    """Discount scope enumeration"""

    PRODUCT = "product"
    CATEGORY = "category"
    BRAND = "brand"
    CUSTOMER_GROUP = "customer_group"
    ORDER_TOTAL = "order_total"
    GLOBAL = "global"


class PricingRuleType(str, Enum):
    """Pricing rule type enumeration"""

    DYNAMIC = "dynamic"
    SCHEDULED = "scheduled"
    CONDITIONAL = "conditional"
    COMPETITIVE = "competitive"
    INVENTORY_BASED = "inventory_based"


class CampaignStatus(str, Enum):
    """Campaign status enumeration"""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ============================================================================
# Database Models
# ============================================================================


class PricingRule(BaseTable):
    """Dynamic pricing rules model"""

    __tablename__ = "pricing_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    rule_type = Column(String(50), nullable=False)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Rule conditions (JSON)
    conditions = Column(JSON)  # Complex condition logic
    actions = Column(JSON)  # Pricing actions to apply

    # Scheduling
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    max_usage = Column(Integer)

    # Relationships
    price_adjustments = relationship("PriceAdjustment", back_populates="pricing_rule")

    __table_args__ = (
        Index("idx_pricing_rule_type", "rule_type"),
        Index("idx_pricing_rule_active", "is_active"),
        Index("idx_pricing_rule_dates", "start_date", "end_date"),
    )


class Discount(BaseTable):
    """Discount model with flexible discount types"""

    __tablename__ = "discounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Discount configuration
    discount_type = Column(String(50), nullable=False)
    discount_scope = Column(String(50), nullable=False)
    discount_value = Column(DECIMAL(15, 4), nullable=False)
    max_discount_amount = Column(DECIMAL(15, 4))

    # Usage restrictions
    min_order_amount = Column(DECIMAL(15, 4))
    max_usage_per_customer = Column(Integer)
    max_total_usage = Column(Integer)
    current_usage = Column(Integer, default=0)

    # Validity period
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_stackable = Column(Boolean, default=False)

    # Target criteria (JSON)
    target_criteria = Column(JSON)  # Products, categories, customer groups, etc.

    # Additional configuration
    buy_x_get_y_config = Column(JSON)  # For buy X get Y discounts
    bulk_pricing_tiers = Column(JSON)  # For bulk/tiered pricing

    # Relationships
    campaign_discounts = relationship("CampaignDiscount", back_populates="discount")
    discount_usages = relationship("DiscountUsage", back_populates="discount")

    __table_args__ = (
        Index("idx_discount_code", "code"),
        Index("idx_discount_type", "discount_type"),
        Index("idx_discount_scope", "discount_scope"),
        Index("idx_discount_validity", "valid_from", "valid_until"),
        Index("idx_discount_active", "is_active"),
        CheckConstraint("discount_value >= 0", name="check_discount_value_positive"),
        CheckConstraint("valid_until > valid_from", name="check_valid_date_range"),
    )


class PromotionalCampaign(BaseTable):
    """Promotional campaign model"""

    __tablename__ = "promotional_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    campaign_type = Column(
        String(50), nullable=False
    )  # seasonal, flash_sale, clearance, etc.

    # Campaign period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Status and settings
    status = Column(String(50), default=CampaignStatus.DRAFT)
    priority = Column(Integer, default=0)

    # Target audience
    target_customer_groups = Column(JSON)
    target_regions = Column(JSON)

    # Campaign metrics
    budget = Column(DECIMAL(15, 4))
    spent_amount = Column(DECIMAL(15, 4), default=0)
    target_sales = Column(DECIMAL(15, 4))
    actual_sales = Column(DECIMAL(15, 4), default=0)

    # Marketing settings
    banner_image_url = Column(String(500))
    landing_page_url = Column(String(500))
    email_template_id = Column(String(100))

    # Relationships
    campaign_discounts = relationship("CampaignDiscount", back_populates="campaign")
    campaign_products = relationship("CampaignProduct", back_populates="campaign")

    __table_args__ = (
        Index("idx_campaign_status", "status"),
        Index("idx_campaign_dates", "start_date", "end_date"),
        Index("idx_campaign_type", "campaign_type"),
        CheckConstraint("end_date > start_date", name="check_campaign_date_range"),
    )


class CampaignDiscount(BaseTable):
    """Campaign-discount relationship model"""

    __tablename__ = "campaign_discounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(
        UUID(as_uuid=True), ForeignKey("promotional_campaigns.id"), nullable=False
    )
    discount_id = Column(UUID(as_uuid=True), ForeignKey("discounts.id"), nullable=False)
    priority = Column(Integer, default=0)

    # Relationships
    campaign = relationship("PromotionalCampaign", back_populates="campaign_discounts")
    discount = relationship("Discount", back_populates="campaign_discounts")

    __table_args__ = (
        Index("idx_campaign_discount_campaign", "campaign_id"),
        Index("idx_campaign_discount_discount", "discount_id"),
        UniqueConstraint("campaign_id", "discount_id", name="uq_campaign_discount"),
    )


class CampaignProduct(BaseTable):
    """Campaign-product relationship model"""

    __tablename__ = "campaign_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(
        UUID(as_uuid=True), ForeignKey("promotional_campaigns.id"), nullable=False
    )
    product_id = Column(UUID(as_uuid=True), nullable=False)  # References products table

    # Product-specific campaign settings
    special_price = Column(DECIMAL(15, 4))
    discount_percentage = Column(DECIMAL(5, 2))
    is_featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    # Relationships
    campaign = relationship("PromotionalCampaign", back_populates="campaign_products")

    __table_args__ = (
        Index("idx_campaign_product_campaign", "campaign_id"),
        Index("idx_campaign_product_product", "product_id"),
        UniqueConstraint("campaign_id", "product_id", name="uq_campaign_product"),
    )


class PriceAdjustment(BaseTable):
    """Price adjustment log model"""

    __tablename__ = "price_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    pricing_rule_id = Column(UUID(as_uuid=True), ForeignKey("pricing_rules.id"))

    # Price details
    original_price = Column(DECIMAL(15, 4), nullable=False)
    adjusted_price = Column(DECIMAL(15, 4), nullable=False)
    adjustment_amount = Column(DECIMAL(15, 4), nullable=False)
    adjustment_type = Column(
        String(50), nullable=False
    )  # percentage, fixed, rule_based

    # Context
    reason = Column(String(500))
    applied_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)

    # User tracking
    created_by = Column(UUID(as_uuid=True))

    # Relationships
    pricing_rule = relationship("PricingRule", back_populates="price_adjustments")

    __table_args__ = (
        Index("idx_price_adj_product", "product_id"),
        Index("idx_price_adj_rule", "pricing_rule_id"),
        Index("idx_price_adj_applied", "applied_at"),
        CheckConstraint("adjusted_price >= 0", name="check_adjusted_price_positive"),
    )


class DiscountUsage(BaseTable):
    """Discount usage tracking model"""

    __tablename__ = "discount_usages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discount_id = Column(UUID(as_uuid=True), ForeignKey("discounts.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True))
    order_id = Column(UUID(as_uuid=True))

    # Usage details
    discount_amount = Column(DECIMAL(15, 4), nullable=False)
    order_total = Column(DECIMAL(15, 4), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    discount = relationship("Discount", back_populates="discount_usages")

    __table_args__ = (
        Index("idx_discount_usage_discount", "discount_id"),
        Index("idx_discount_usage_customer", "customer_id"),
        Index("idx_discount_usage_order", "order_id"),
        Index("idx_discount_usage_date", "used_at"),
    )


class CustomerPricing(BaseTable):
    """Customer-specific pricing model"""

    __tablename__ = "customer_pricing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)

    # Pricing details
    special_price = Column(DECIMAL(15, 4), nullable=False)
    discount_percentage = Column(DECIMAL(5, 2))
    min_quantity = Column(Integer, default=1)

    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Notes
    notes = Column(Text)

    __table_args__ = (
        Index("idx_customer_pricing_customer", "customer_id"),
        Index("idx_customer_pricing_product", "product_id"),
        Index("idx_customer_pricing_validity", "valid_from", "valid_until"),
        UniqueConstraint(
            "customer_id", "product_id", name="uq_customer_product_pricing"
        ),
        CheckConstraint("special_price >= 0", name="check_special_price_positive"),
    )


# ============================================================================
# Pydantic Schemas
# ============================================================================


class PricingRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    rule_type: PricingRuleType
    priority: int = 0
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_usage: Optional[int] = None
    is_active: bool = True


class DiscountCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    discount_type: DiscountType
    discount_scope: DiscountScope
    discount_value: Decimal = Field(..., ge=0)
    max_discount_amount: Optional[Decimal] = Field(None, ge=0)
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    max_usage_per_customer: Optional[int] = Field(None, ge=1)
    max_total_usage: Optional[int] = Field(None, ge=1)
    valid_from: datetime
    valid_until: datetime
    is_stackable: bool = False
    target_criteria: Optional[Dict[str, Any]] = None
    buy_x_get_y_config: Optional[Dict[str, Any]] = None
    bulk_pricing_tiers: Optional[List[Dict[str, Any]]] = None

    @validator("valid_until")
    def validate_dates(cls, v, values):
        if "valid_from" in values and v <= values["valid_from"]:
            raise ValueError("valid_until must be after valid_from")
        return v


class PromotionalCampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    campaign_type: str = Field(..., min_length=1, max_length=50)
    start_date: datetime
    end_date: datetime
    priority: int = 0
    target_customer_groups: Optional[List[str]] = None
    target_regions: Optional[List[str]] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    target_sales: Optional[Decimal] = Field(None, ge=0)
    banner_image_url: Optional[str] = Field(None, max_length=500)
    landing_page_url: Optional[str] = Field(None, max_length=500)
    email_template_id: Optional[str] = Field(None, max_length=100)

    @validator("end_date")
    def validate_dates(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class PriceCalculationRequest(BaseModel):
    product_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    quantity: int = Field(..., ge=1)
    discount_codes: Optional[List[str]] = None
    campaign_id: Optional[uuid.UUID] = None


class PriceCalculationResponse(BaseModel):
    product_id: uuid.UUID
    base_price: Decimal
    final_price: Decimal
    total_discount: Decimal
    discount_percentage: Decimal
    applied_discounts: List[Dict[str, Any]]
    price_breakdown: Dict[str, Any]
    valid_until: Optional[datetime]


class BulkPricingResponse(BaseModel):
    products: List[PriceCalculationResponse]
    total_amount: Decimal
    total_discount: Decimal
    order_level_discounts: List[Dict[str, Any]]


# ============================================================================
# Service Classes
# ============================================================================


class PricingEngine:
    """Advanced pricing engine with dynamic pricing capabilities"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def calculate_product_price(
        self,
        product_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        quantity: int = 1,
        discount_codes: Optional[List[str]] = None,
        campaign_id: Optional[uuid.UUID] = None,
    ) -> PriceCalculationResponse:
        """Calculate final product price with all applicable discounts"""

        # Get base product price (assuming products table exists)
        base_price_query = text("""
            SELECT base_price, compare_at_price, cost_price
            FROM products
            WHERE id = :product_id
        """)

        result = await self.db.execute(base_price_query, {"product_id": product_id})
        product_data = result.fetchone()

        if not product_data:
            raise HTTPException(status_code=404, detail="Product not found")

        base_price = Decimal(str(product_data.base_price))
        current_price = base_price
        total_discount = Decimal("0")
        applied_discounts = []

        # Step 1: Apply customer-specific pricing
        if customer_id:
            customer_price = await self._get_customer_specific_price(
                product_id, customer_id, quantity
            )
            if customer_price:
                customer_discount = base_price - customer_price["price"]
                if customer_discount > 0:
                    applied_discounts.append(
                        {
                            "type": "customer_specific",
                            "name": "Customer Special Price",
                            "discount_amount": customer_discount,
                            "final_price": customer_price["price"],
                        }
                    )
                    current_price = customer_price["price"]
                    total_discount += customer_discount

        # Step 2: Apply pricing rules
        pricing_rules = await self._get_applicable_pricing_rules(
            product_id, customer_id, quantity
        )
        for rule in pricing_rules:
            rule_discount = await self._apply_pricing_rule(
                rule, current_price, quantity
            )
            if rule_discount > 0:
                applied_discounts.append(
                    {
                        "type": "pricing_rule",
                        "name": rule["name"],
                        "discount_amount": rule_discount,
                        "rule_id": rule["id"],
                    }
                )
                current_price -= rule_discount
                total_discount += rule_discount

        # Step 3: Apply campaign discounts
        if campaign_id:
            campaign_discounts = await self._get_campaign_discounts(
                campaign_id, product_id
            )
            for discount in campaign_discounts:
                discount_amount = await self._calculate_discount_amount(
                    discount, current_price, quantity
                )
                if discount_amount > 0:
                    applied_discounts.append(
                        {
                            "type": "campaign",
                            "name": discount["name"],
                            "discount_amount": discount_amount,
                            "campaign_id": campaign_id,
                        }
                    )
                    current_price -= discount_amount
                    total_discount += discount_amount

        # Step 4: Apply discount codes
        if discount_codes:
            for code in discount_codes:
                discount = await self._get_discount_by_code(code)
                if discount and await self._is_discount_applicable(
                    discount, product_id, customer_id, quantity
                ):
                    discount_amount = await self._calculate_discount_amount(
                        discount, current_price, quantity
                    )
                    if discount_amount > 0:
                        applied_discounts.append(
                            {
                                "type": "coupon",
                                "name": discount["name"],
                                "code": code,
                                "discount_amount": discount_amount,
                            }
                        )
                        current_price -= discount_amount
                        total_discount += discount_amount

        # Step 5: Apply bulk pricing
        bulk_discount = await self._calculate_bulk_pricing(
            product_id, quantity, current_price
        )
        if bulk_discount > 0:
            applied_discounts.append(
                {
                    "type": "bulk_pricing",
                    "name": "Bulk Discount",
                    "discount_amount": bulk_discount,
                    "quantity": quantity,
                }
            )
            current_price -= bulk_discount
            total_discount += bulk_discount

        # Ensure price doesn't go below cost price (if configured)
        min_price = await self._get_minimum_price(product_id)
        if min_price and current_price < min_price:
            adjustment = min_price - current_price
            total_discount -= adjustment
            current_price = min_price
            applied_discounts.append(
                {
                    "type": "minimum_price_adjustment",
                    "name": "Minimum Price Protection",
                    "adjustment_amount": adjustment,
                }
            )

        # Calculate discount percentage
        discount_percentage = (
            (total_discount / base_price * 100) if base_price > 0 else Decimal("0")
        )

        # Price breakdown
        price_breakdown = {
            "base_price": base_price,
            "total_discount": total_discount,
            "discount_percentage": discount_percentage,
            "final_price": current_price,
            "savings": total_discount,
            "quantity": quantity,
            "unit_price": current_price,
            "line_total": current_price * quantity,
        }

        return PriceCalculationResponse(
            product_id=product_id,
            base_price=base_price,
            final_price=current_price,
            total_discount=total_discount,
            discount_percentage=discount_percentage,
            applied_discounts=applied_discounts,
            price_breakdown=price_breakdown,
            valid_until=datetime.utcnow() + timedelta(hours=24),  # Cache for 24 hours
        )

    async def _get_customer_specific_price(
        self, product_id: uuid.UUID, customer_id: uuid.UUID, quantity: int
    ) -> Optional[Dict[str, Any]]:
        """Get customer-specific pricing if available"""
        query = select(CustomerPricing).where(
            and_(
                CustomerPricing.customer_id == customer_id,
                CustomerPricing.product_id == product_id,
                CustomerPricing.is_active,
                CustomerPricing.min_quantity <= quantity,
                or_(
                    CustomerPricing.valid_until.is_(None),
                    CustomerPricing.valid_until > datetime.utcnow(),
                ),
            )
        )

        result = await self.db.execute(query)
        pricing = result.scalar_one_or_none()

        if pricing:
            return {
                "price": pricing.special_price,
                "discount_percentage": pricing.discount_percentage,
                "min_quantity": pricing.min_quantity,
            }

        return None

    async def _get_applicable_pricing_rules(
        self, product_id: uuid.UUID, customer_id: Optional[uuid.UUID], quantity: int
    ) -> List[Dict[str, Any]]:
        """Get applicable pricing rules"""
        query = (
            select(PricingRule)
            .where(
                and_(
                    PricingRule.is_active,
                    or_(
                        PricingRule.start_date.is_(None),
                        PricingRule.start_date <= datetime.utcnow(),
                    ),
                    or_(
                        PricingRule.end_date.is_(None),
                        PricingRule.end_date > datetime.utcnow(),
                    ),
                )
            )
            .order_by(PricingRule.priority.desc())
        )

        result = await self.db.execute(query)
        rules = result.scalars().all()

        applicable_rules = []
        for rule in rules:
            if await self._evaluate_rule_conditions(
                rule, product_id, customer_id, quantity
            ):
                applicable_rules.append(
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "rule_type": rule.rule_type,
                        "conditions": rule.conditions,
                        "actions": rule.actions,
                        "priority": rule.priority,
                    }
                )

        return applicable_rules

    async def _evaluate_rule_conditions(
        self,
        rule: PricingRule,
        product_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
        quantity: int,
    ) -> bool:
        """Evaluate if pricing rule conditions are met"""
        if not rule.conditions:
            return True

        conditions = rule.conditions

        # Check product conditions
        if "products" in conditions:
            product_condition = conditions["products"]
            if "include" in product_condition:
                if str(product_id) not in product_condition["include"]:
                    return False
            if "exclude" in product_condition:
                if str(product_id) in product_condition["exclude"]:
                    return False

        # Check quantity conditions
        if "quantity" in conditions:
            qty_condition = conditions["quantity"]
            if "min" in qty_condition and quantity < qty_condition["min"]:
                return False
            if "max" in qty_condition and quantity > qty_condition["max"]:
                return False

        # Check customer conditions
        if customer_id and "customers" in conditions:
            customer_condition = conditions["customers"]
            if "include" in customer_condition:
                if str(customer_id) not in customer_condition["include"]:
                    return False
            if "exclude" in customer_condition:
                if str(customer_id) in customer_condition["exclude"]:
                    return False

        # Check time-based conditions
        if "time" in conditions:
            time_condition = conditions["time"]
            current_time = datetime.utcnow()

            if "day_of_week" in time_condition:
                if current_time.weekday() not in time_condition["day_of_week"]:
                    return False

            if "hour_range" in time_condition:
                hour_range = time_condition["hour_range"]
                if not (hour_range["start"] <= current_time.hour <= hour_range["end"]):
                    return False

        return True

    async def _apply_pricing_rule(
        self, rule: Dict[str, Any], current_price: Decimal, quantity: int
    ) -> Decimal:
        """Apply pricing rule and return discount amount"""
        actions = rule["actions"]
        discount_amount = Decimal("0")

        if "percentage_discount" in actions:
            percentage = Decimal(str(actions["percentage_discount"]))
            discount_amount = current_price * (percentage / 100)

        elif "fixed_discount" in actions:
            discount_amount = Decimal(str(actions["fixed_discount"]))

        elif "price_override" in actions:
            new_price = Decimal(str(actions["price_override"]))
            discount_amount = max(Decimal("0"), current_price - new_price)

        elif "dynamic_pricing" in actions:
            # Advanced dynamic pricing logic
            dynamic_config = actions["dynamic_pricing"]

            if dynamic_config.get("type") == "inventory_based":
                # Adjust price based on inventory levels
                inventory_level = await self._get_product_inventory_level(
                    rule["product_id"]
                )
                if inventory_level < dynamic_config.get("low_stock_threshold", 10):
                    # Increase price for low stock
                    price_increase = current_price * (
                        Decimal(str(dynamic_config.get("low_stock_multiplier", 1.1)))
                        - 1
                    )
                    discount_amount = (
                        -price_increase
                    )  # Negative discount = price increase
                elif inventory_level > dynamic_config.get("high_stock_threshold", 100):
                    # Decrease price for high stock
                    discount_amount = current_price * (
                        Decimal(str(dynamic_config.get("high_stock_discount", 0.05)))
                    )

        # Apply maximum discount limits
        if "max_discount" in actions:
            max_discount = Decimal(str(actions["max_discount"]))
            discount_amount = min(discount_amount, max_discount)

        return discount_amount

    async def _get_campaign_discounts(
        self, campaign_id: uuid.UUID, product_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get applicable campaign discounts"""
        query = (
            select(Discount)
            .join(CampaignDiscount)
            .where(
                and_(
                    CampaignDiscount.campaign_id == campaign_id,
                    Discount.is_active,
                    Discount.valid_from <= datetime.utcnow(),
                    Discount.valid_until > datetime.utcnow(),
                )
            )
            .order_by(CampaignDiscount.priority.desc())
        )

        result = await self.db.execute(query)
        discounts = result.scalars().all()

        applicable_discounts = []
        for discount in discounts:
            if await self._is_discount_applicable_to_product(discount, product_id):
                applicable_discounts.append(
                    {
                        "id": discount.id,
                        "name": discount.name,
                        "code": discount.code,
                        "discount_type": discount.discount_type,
                        "discount_value": discount.discount_value,
                        "max_discount_amount": discount.max_discount_amount,
                        "target_criteria": discount.target_criteria,
                    }
                )

        return applicable_discounts

    async def _calculate_discount_amount(
        self, discount: Dict[str, Any], current_price: Decimal, quantity: int
    ) -> Decimal:
        """Calculate discount amount based on discount configuration"""
        discount_type = discount["discount_type"]
        discount_value = Decimal(str(discount["discount_value"]))

        if discount_type == DiscountType.PERCENTAGE:
            discount_amount = current_price * (discount_value / 100)

        elif discount_type == DiscountType.FIXED_AMOUNT:
            discount_amount = discount_value

        elif discount_type == DiscountType.BUY_X_GET_Y:
            # Implement buy X get Y logic
            config = discount.get("buy_x_get_y_config", {})
            buy_quantity = config.get("buy_quantity", 1)
            get_quantity = config.get("get_quantity", 1)

            if quantity >= buy_quantity:
                free_items = (quantity // buy_quantity) * get_quantity
                discount_amount = min(free_items, quantity) * current_price
            else:
                discount_amount = Decimal("0")

        elif discount_type == DiscountType.BULK_PRICING:
            # Implement bulk pricing tiers
            tiers = discount.get("bulk_pricing_tiers", [])
            discount_amount = Decimal("0")

            for tier in tiers:
                if quantity >= tier["min_quantity"]:
                    if tier["discount_type"] == "percentage":
                        discount_amount = current_price * (
                            Decimal(str(tier["discount_value"])) / 100
                        )
                    else:
                        discount_amount = Decimal(str(tier["discount_value"]))

        else:
            discount_amount = Decimal("0")

        # Apply maximum discount limit
        if discount.get("max_discount_amount"):
            max_discount = Decimal(str(discount["max_discount_amount"]))
            discount_amount = min(discount_amount, max_discount)

        return discount_amount

    async def _get_discount_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get discount by code"""
        query = select(Discount).where(
            and_(
                Discount.code == code,
                Discount.is_active,
                Discount.valid_from <= datetime.utcnow(),
                Discount.valid_until > datetime.utcnow(),
            )
        )

        result = await self.db.execute(query)
        discount = result.scalar_one_or_none()

        if discount:
            return {
                "id": discount.id,
                "name": discount.name,
                "code": discount.code,
                "discount_type": discount.discount_type,
                "discount_scope": discount.discount_scope,
                "discount_value": discount.discount_value,
                "max_discount_amount": discount.max_discount_amount,
                "target_criteria": discount.target_criteria,
                "buy_x_get_y_config": discount.buy_x_get_y_config,
                "bulk_pricing_tiers": discount.bulk_pricing_tiers,
            }

        return None

    async def _is_discount_applicable(
        self,
        discount: Dict[str, Any],
        product_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
        quantity: int,
    ) -> bool:
        """Check if discount is applicable"""
        # Check usage limits
        if (
            discount.get("max_total_usage")
            and discount.get("current_usage", 0) >= discount["max_total_usage"]
        ):
            return False

        if customer_id and discount.get("max_usage_per_customer"):
            customer_usage_query = select(func.count(DiscountUsage.id)).where(
                and_(
                    DiscountUsage.discount_id == discount["id"],
                    DiscountUsage.customer_id == customer_id,
                )
            )
            result = await self.db.execute(customer_usage_query)
            customer_usage = result.scalar()

            if customer_usage >= discount["max_usage_per_customer"]:
                return False

        # Check product applicability
        return await self._is_discount_applicable_to_product(discount, product_id)

    async def _is_discount_applicable_to_product(
        self, discount: Dict[str, Any], product_id: uuid.UUID
    ) -> bool:
        """Check if discount applies to specific product"""
        scope = discount["discount_scope"]
        target_criteria = discount.get("target_criteria", {})

        if scope == DiscountScope.GLOBAL:
            return True

        elif scope == DiscountScope.PRODUCT:
            if "products" in target_criteria:
                return str(product_id) in target_criteria["products"]

        elif scope == DiscountScope.CATEGORY:
            if "categories" in target_criteria:
                # Check if product belongs to target categories
                product_category_query = text("""
                    SELECT category_id FROM products WHERE id = :product_id
                """)
                result = await self.db.execute(
                    product_category_query, {"product_id": product_id}
                )
                product_data = result.fetchone()

                if (
                    product_data
                    and str(product_data.category_id) in target_criteria["categories"]
                ):
                    return True

        elif scope == DiscountScope.BRAND:
            if "brands" in target_criteria:
                # Check if product belongs to target brands
                product_brand_query = text("""
                    SELECT brand_id FROM products WHERE id = :product_id
                """)
                result = await self.db.execute(
                    product_brand_query, {"product_id": product_id}
                )
                product_data = result.fetchone()

                if (
                    product_data
                    and str(product_data.brand_id) in target_criteria["brands"]
                ):
                    return True

        return False

    async def _calculate_bulk_pricing(
        self, product_id: uuid.UUID, quantity: int, current_price: Decimal
    ) -> Decimal:
        """Calculate bulk pricing discount"""
        # Check for product-specific bulk pricing rules
        bulk_rules_query = select(Discount).where(
            and_(
                Discount.discount_type == DiscountType.BULK_PRICING,
                Discount.is_active,
                Discount.valid_from <= datetime.utcnow(),
                Discount.valid_until > datetime.utcnow(),
            )
        )

        result = await self.db.execute(bulk_rules_query)
        bulk_rules = result.scalars().all()

        best_discount = Decimal("0")

        for rule in bulk_rules:
            if await self._is_discount_applicable_to_product(rule.__dict__, product_id):
                tiers = rule.bulk_pricing_tiers or []

                for tier in tiers:
                    if quantity >= tier["min_quantity"]:
                        if tier["discount_type"] == "percentage":
                            discount = current_price * (
                                Decimal(str(tier["discount_value"])) / 100
                            )
                        else:
                            discount = Decimal(str(tier["discount_value"]))

                        best_discount = max(best_discount, discount)

        return best_discount

    async def _get_minimum_price(self, product_id: uuid.UUID) -> Optional[Decimal]:
        """Get minimum allowed price for product"""
        min_price_query = text("""
            SELECT cost_price FROM products WHERE id = :product_id
        """)

        result = await self.db.execute(min_price_query, {"product_id": product_id})
        product_data = result.fetchone()

        if product_data and product_data.cost_price:
            return Decimal(str(product_data.cost_price))

        return None

    async def calculate_bulk_pricing(
        self, items: List[PriceCalculationRequest]
    ) -> BulkPricingResponse:
        """Calculate pricing for multiple products with order-level discounts"""
        product_prices = []
        subtotal = Decimal("0")
        total_product_discount = Decimal("0")

        # Calculate individual product prices
        for item in items:
            price_result = await self.calculate_product_price(
                product_id=item.product_id,
                customer_id=item.customer_id,
                quantity=item.quantity,
                discount_codes=item.discount_codes,
                campaign_id=item.campaign_id,
            )

            product_prices.append(price_result)
            subtotal += price_result.final_price * item.quantity
            total_product_discount += price_result.total_discount * item.quantity

        # Apply order-level discounts
        order_level_discounts = []
        order_discount_amount = Decimal("0")

        # Check for order total-based discounts
        order_discounts = await self._get_order_level_discounts(
            subtotal, items[0].customer_id if items else None
        )

        for discount in order_discounts:
            discount_amount = await self._calculate_order_discount(discount, subtotal)
            if discount_amount > 0:
                order_level_discounts.append(
                    {
                        "type": "order_total",
                        "name": discount["name"],
                        "discount_amount": discount_amount,
                        "conditions": discount.get("conditions", {}),
                    }
                )
                order_discount_amount += discount_amount

        final_total = subtotal - order_discount_amount
        total_discount = total_product_discount + order_discount_amount

        return BulkPricingResponse(
            products=product_prices,
            total_amount=final_total,
            total_discount=total_discount,
            order_level_discounts=order_level_discounts,
        )

    async def _get_order_level_discounts(
        self, order_total: Decimal, customer_id: Optional[uuid.UUID]
    ) -> List[Dict[str, Any]]:
        """Get applicable order-level discounts"""
        query = select(Discount).where(
            and_(
                Discount.discount_scope == DiscountScope.ORDER_TOTAL,
                Discount.is_active,
                Discount.valid_from <= datetime.utcnow(),
                Discount.valid_until > datetime.utcnow(),
                or_(
                    Discount.min_order_amount.is_(None),
                    Discount.min_order_amount <= order_total,
                ),
            )
        )

        result = await self.db.execute(query)
        discounts = result.scalars().all()

        applicable_discounts = []
        for discount in discounts:
            applicable_discounts.append(
                {
                    "id": discount.id,
                    "name": discount.name,
                    "discount_type": discount.discount_type,
                    "discount_value": discount.discount_value,
                    "max_discount_amount": discount.max_discount_amount,
                    "min_order_amount": discount.min_order_amount,
                    "conditions": discount.target_criteria,
                }
            )

        return applicable_discounts

    async def _calculate_order_discount(
        self, discount: Dict[str, Any], order_total: Decimal
    ) -> Decimal:
        """Calculate order-level discount amount"""
        discount_type = discount["discount_type"]
        discount_value = Decimal(str(discount["discount_value"]))

        if discount_type == DiscountType.PERCENTAGE:
            discount_amount = order_total * (discount_value / 100)
        else:
            discount_amount = discount_value

        # Apply maximum discount limit
        if discount.get("max_discount_amount"):
            max_discount = Decimal(str(discount["max_discount_amount"]))
            discount_amount = min(discount_amount, max_discount)

        return discount_amount


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/pricing", tags=["Product Pricing v66"])


@router.post("/calculate", response_model=PriceCalculationResponse)
async def calculate_price(
    request: PriceCalculationRequest, db: AsyncSession = Depends(get_db)
):
    """Calculate product price with all applicable discounts"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    pricing_engine = PricingEngine(db, redis_client)

    return await pricing_engine.calculate_product_price(
        product_id=request.product_id,
        customer_id=request.customer_id,
        quantity=request.quantity,
        discount_codes=request.discount_codes,
        campaign_id=request.campaign_id,
    )


@router.post("/calculate-bulk", response_model=BulkPricingResponse)
async def calculate_bulk_price(
    items: List[PriceCalculationRequest], db: AsyncSession = Depends(get_db)
):
    """Calculate bulk pricing for multiple products"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    pricing_engine = PricingEngine(db, redis_client)

    return await pricing_engine.calculate_bulk_pricing(items)


@router.post("/discounts", response_model=Dict[str, Any])
async def create_discount(
    discount_data: DiscountCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create new discount"""
    # Check if discount code already exists
    existing_query = select(Discount).where(Discount.code == discount_data.code)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Discount code already exists")

    discount = Discount(**discount_data.dict())
    db.add(discount)
    await db.commit()
    await db.refresh(discount)

    return {"id": discount.id, "code": discount.code, "status": "created"}


@router.post("/campaigns", response_model=Dict[str, Any])
async def create_campaign(
    campaign_data: PromotionalCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create promotional campaign"""
    campaign = PromotionalCampaign(**campaign_data.dict())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    return {"id": campaign.id, "name": campaign.name, "status": "created"}


@router.post("/rules", response_model=Dict[str, Any])
async def create_pricing_rule(
    rule_data: PricingRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create pricing rule"""
    rule = PricingRule(**rule_data.dict())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return {"id": rule.id, "name": rule.name, "status": "created"}


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Pricing service health check"""
    return {
        "status": "healthy",
        "service": "product_pricing_v66",
        "version": "66.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "dynamic_pricing",
            "discount_management",
            "promotional_campaigns",
            "customer_specific_pricing",
            "bulk_pricing",
            "pricing_rules",
        ],
    }
