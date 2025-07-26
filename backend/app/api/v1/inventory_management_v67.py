"""
ITDO ERP Backend - Advanced Inventory Management System v67
Comprehensive multi-location inventory management with real-time tracking, forecasting, and automation
Day 9: Advanced Inventory Management Implementation
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
import hashlib
import aioredis
from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Boolean, DECIMAL, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, JSON, BigInteger
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, and_, or_, text
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.base import BaseTable

# ============================================================================
# Enums and Constants
# ============================================================================

class MovementType(str, Enum):
    """Inventory movement type enumeration"""
    RECEIPT = "receipt"
    SHIPMENT = "shipment"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    PRODUCTION = "production"
    CONSUMPTION = "consumption"
    CYCLE_COUNT = "cycle_count"
    DAMAGED = "damaged"
    EXPIRED = "expired"

class LocationType(str, Enum):
    """Location type enumeration"""
    WAREHOUSE = "warehouse"
    STORE = "store"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    TRANSIT = "transit"
    VIRTUAL = "virtual"
    QUARANTINE = "quarantine"
    DAMAGED = "damaged"

class InventoryStatus(str, Enum):
    """Inventory status enumeration"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    QUARANTINE = "quarantine"
    DAMAGED = "damaged"
    EXPIRED = "expired"
    IN_TRANSIT = "in_transit"
    ALLOCATED = "allocated"

class ReplenishmentMethod(str, Enum):
    """Replenishment method enumeration"""
    REORDER_POINT = "reorder_point"
    PERIODIC_REVIEW = "periodic_review"
    JIT = "just_in_time"
    KANBAN = "kanban"
    MRP = "mrp"
    MANUAL = "manual"

class ForecastMethod(str, Enum):
    """Forecast method enumeration"""
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    ARIMA = "arima"
    MACHINE_LEARNING = "machine_learning"

# ============================================================================
# Database Models
# ============================================================================

class Location(BaseTable):
    """Inventory location model"""
    __tablename__ = "inventory_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    location_type = Column(String(50), nullable=False)
    
    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"))
    level = Column(Integer, default=0)
    path = Column(String(1000))  # Materialized path for hierarchy
    
    # Address information
    address = Column(JSON)
    timezone = Column(String(50), default="UTC")
    
    # Configuration
    is_active = Column(Boolean, default=True)
    accepts_receipts = Column(Boolean, default=True)
    accepts_shipments = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)
    
    # Capacity management
    total_capacity = Column(DECIMAL(15, 4))
    used_capacity = Column(DECIMAL(15, 4), default=0)
    capacity_unit = Column(String(20), default="cubic_meter")
    
    # Contact information
    manager_name = Column(String(200))
    contact_email = Column(String(254))
    contact_phone = Column(String(20))
    
    # Relationships
    parent = relationship("Location", remote_side=[id], back_populates="children")
    children = relationship("Location", back_populates="parent")
    inventories = relationship("InventoryBalance", back_populates="location")
    movements = relationship("InventoryMovement", back_populates="location")
    
    __table_args__ = (
        Index("idx_location_code", "code"),
        Index("idx_location_type", "location_type"),
        Index("idx_location_active", "is_active"),
        Index("idx_location_parent", "parent_id"),
    )

class InventoryBalance(BaseTable):
    """Real-time inventory balance model"""
    __tablename__ = "inventory_balances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    
    # Quantities
    quantity_on_hand = Column(DECIMAL(15, 4), default=0)
    quantity_available = Column(DECIMAL(15, 4), default=0)
    quantity_reserved = Column(DECIMAL(15, 4), default=0)
    quantity_allocated = Column(DECIMAL(15, 4), default=0)
    quantity_in_transit = Column(DECIMAL(15, 4), default=0)
    
    # Cost information
    unit_cost = Column(DECIMAL(15, 4))
    total_cost = Column(DECIMAL(15, 4))
    average_cost = Column(DECIMAL(15, 4))
    
    # Stock levels
    minimum_stock = Column(DECIMAL(15, 4), default=0)
    maximum_stock = Column(DECIMAL(15, 4))
    reorder_point = Column(DECIMAL(15, 4))
    safety_stock = Column(DECIMAL(15, 4), default=0)
    
    # Status and dates
    status = Column(String(50), default=InventoryStatus.AVAILABLE)
    last_counted = Column(DateTime)
    last_movement = Column(DateTime)
    
    # Batch/lot tracking
    lot_number = Column(String(100))
    expiry_date = Column(DateTime)
    manufacture_date = Column(DateTime)
    
    # Relationships
    location = relationship("Location", back_populates="inventories")
    movements = relationship("InventoryMovement", back_populates="inventory_balance")
    
    __table_args__ = (
        Index("idx_inventory_product", "product_id"),
        Index("idx_inventory_location", "location_id"),
        Index("idx_inventory_status", "status"),
        Index("idx_inventory_lot", "lot_number"),
        Index("idx_inventory_expiry", "expiry_date"),
        UniqueConstraint("product_id", "location_id", "lot_number", name="uq_product_location_lot"),
        CheckConstraint("quantity_on_hand >= 0", name="check_quantity_positive"),
    )

class InventoryMovement(BaseTable):
    """Inventory movement transaction model"""
    __tablename__ = "inventory_movements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movement_number = Column(String(50), unique=True, nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    inventory_balance_id = Column(UUID(as_uuid=True), ForeignKey("inventory_balances.id"))
    
    # Movement details
    movement_type = Column(String(50), nullable=False)
    movement_date = Column(DateTime, default=datetime.utcnow)
    quantity = Column(DECIMAL(15, 4), nullable=False)
    unit_cost = Column(DECIMAL(15, 4))
    total_cost = Column(DECIMAL(15, 4))
    
    # Reference information
    reference_type = Column(String(50))  # purchase_order, sales_order, transfer, etc.
    reference_id = Column(String(100))
    reference_number = Column(String(100))
    
    # Transfer details (for transfers)
    from_location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"))
    to_location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"))
    
    # Batch/lot information
    lot_number = Column(String(100))
    expiry_date = Column(DateTime)
    
    # Status and approval
    status = Column(String(50), default="pending")
    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime)
    
    # Notes and documentation
    reason = Column(Text)
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True))
    
    # Relationships
    location = relationship("Location", foreign_keys=[location_id], back_populates="movements")
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])
    inventory_balance = relationship("InventoryBalance", back_populates="movements")
    
    __table_args__ = (
        Index("idx_movement_number", "movement_number"),
        Index("idx_movement_product", "product_id"),
        Index("idx_movement_location", "location_id"),
        Index("idx_movement_type", "movement_type"),
        Index("idx_movement_date", "movement_date"),
        Index("idx_movement_reference", "reference_type", "reference_id"),
        Index("idx_movement_lot", "lot_number"),
    )

class StockAdjustment(BaseTable):
    """Stock adjustment model"""
    __tablename__ = "stock_adjustments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adjustment_number = Column(String(50), unique=True, nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    
    # Adjustment details
    adjustment_date = Column(DateTime, default=datetime.utcnow)
    adjustment_type = Column(String(50), nullable=False)  # cycle_count, physical_count, adjustment
    reason = Column(String(500))
    notes = Column(Text)
    
    # Status
    status = Column(String(50), default="draft")
    submitted_by = Column(UUID(as_uuid=True))
    submitted_at = Column(DateTime)
    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime)
    
    # Summary
    total_items = Column(Integer, default=0)
    total_variance_value = Column(DECIMAL(15, 4), default=0)
    
    # Relationships
    location = relationship("Location")
    adjustment_lines = relationship("StockAdjustmentLine", back_populates="adjustment")
    
    __table_args__ = (
        Index("idx_adjustment_number", "adjustment_number"),
        Index("idx_adjustment_location", "location_id"),
        Index("idx_adjustment_date", "adjustment_date"),
        Index("idx_adjustment_status", "status"),
    )

class StockAdjustmentLine(BaseTable):
    """Stock adjustment line item model"""
    __tablename__ = "stock_adjustment_lines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adjustment_id = Column(UUID(as_uuid=True), ForeignKey("stock_adjustments.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Quantities
    system_quantity = Column(DECIMAL(15, 4), nullable=False)
    counted_quantity = Column(DECIMAL(15, 4), nullable=False)
    variance_quantity = Column(DECIMAL(15, 4), nullable=False)
    
    # Cost information
    unit_cost = Column(DECIMAL(15, 4))
    variance_value = Column(DECIMAL(15, 4))
    
    # Batch/lot information
    lot_number = Column(String(100))
    expiry_date = Column(DateTime)
    
    # Notes
    reason = Column(String(500))
    notes = Column(Text)
    counted_by = Column(UUID(as_uuid=True))
    counted_at = Column(DateTime)
    
    # Relationships
    adjustment = relationship("StockAdjustment", back_populates="adjustment_lines")
    
    __table_args__ = (
        Index("idx_adj_line_adjustment", "adjustment_id"),
        Index("idx_adj_line_product", "product_id"),
        Index("idx_adj_line_lot", "lot_number"),
    )

class ReplenishmentRule(BaseTable):
    """Automatic replenishment rule model"""
    __tablename__ = "replenishment_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    
    # Rule configuration
    rule_name = Column(String(200), nullable=False)
    replenishment_method = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # Thresholds
    reorder_point = Column(DECIMAL(15, 4))
    minimum_order_quantity = Column(DECIMAL(15, 4))
    maximum_order_quantity = Column(DECIMAL(15, 4))
    order_multiple = Column(DECIMAL(15, 4), default=1)
    
    # Timing
    lead_time_days = Column(Integer, default=0)
    review_period_days = Column(Integer, default=7)
    safety_stock_days = Column(Integer, default=0)
    
    # Supplier information
    preferred_supplier_id = Column(UUID(as_uuid=True))
    backup_supplier_id = Column(UUID(as_uuid=True))
    
    # Cost constraints
    maximum_unit_cost = Column(DECIMAL(15, 4))
    budget_limit = Column(DECIMAL(15, 4))
    
    # Seasonal factors
    seasonal_factors = Column(JSON)  # Monthly multipliers
    
    # Automation settings
    auto_create_po = Column(Boolean, default=False)
    auto_approve_po = Column(Boolean, default=False)
    notification_emails = Column(JSON)
    
    # Performance tracking
    last_triggered = Column(DateTime)
    total_orders_generated = Column(Integer, default=0)
    avg_fulfillment_time = Column(DECIMAL(10, 2))
    
    # Relationships
    location = relationship("Location")
    
    __table_args__ = (
        Index("idx_replenish_product", "product_id"),
        Index("idx_replenish_location", "location_id"),
        Index("idx_replenish_active", "is_active"),
        Index("idx_replenish_method", "replenishment_method"),
    )

class DemandForecast(BaseTable):
    """Demand forecast model"""
    __tablename__ = "demand_forecasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"))
    
    # Forecast details
    forecast_date = Column(DateTime, nullable=False)
    forecast_period = Column(String(20), nullable=False)  # daily, weekly, monthly
    forecast_method = Column(String(50), nullable=False)
    
    # Forecast values
    forecasted_demand = Column(DECIMAL(15, 4), nullable=False)
    lower_bound = Column(DECIMAL(15, 4))
    upper_bound = Column(DECIMAL(15, 4))
    confidence_level = Column(DECIMAL(5, 2))
    
    # Historical comparison
    actual_demand = Column(DECIMAL(15, 4))
    forecast_accuracy = Column(DECIMAL(5, 2))
    
    # Model parameters
    model_parameters = Column(JSON)
    seasonal_index = Column(DECIMAL(10, 4))
    trend_factor = Column(DECIMAL(10, 4))
    
    # Metadata
    created_by_model = Column(String(100))
    model_version = Column(String(20))
    training_data_period = Column(String(100))
    
    # Relationships
    location = relationship("Location")
    
    __table_args__ = (
        Index("idx_forecast_product", "product_id"),
        Index("idx_forecast_location", "location_id"),
        Index("idx_forecast_date", "forecast_date"),
        Index("idx_forecast_period", "forecast_period"),
        Index("idx_forecast_method", "forecast_method"),
    )

class InventoryAlert(BaseTable):
    """Inventory alert model"""
    __tablename__ = "inventory_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"))
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # low_stock, overstock, expiry, etc.
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Trigger conditions
    trigger_value = Column(DECIMAL(15, 4))
    threshold_value = Column(DECIMAL(15, 4))
    
    # Status
    status = Column(String(50), default="active")  # active, acknowledged, resolved, dismissed
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_by = Column(UUID(as_uuid=True))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Action taken
    action_taken = Column(Text)
    auto_resolved = Column(Boolean, default=False)
    
    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_emails = Column(JSON)
    
    # Relationships
    location = relationship("Location")
    
    __table_args__ = (
        Index("idx_alert_product", "product_id"),
        Index("idx_alert_location", "location_id"),
        Index("idx_alert_type", "alert_type"),
        Index("idx_alert_severity", "severity"),
        Index("idx_alert_status", "status"),
        Index("idx_alert_created", "created_at"),
    )

class InventoryCycle(BaseTable):
    """Inventory cycle count model"""
    __tablename__ = "inventory_cycles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_name = Column(String(200), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    
    # Cycle configuration
    cycle_type = Column(String(50), nullable=False)  # full, partial, abc, random
    frequency = Column(String(50))  # daily, weekly, monthly, quarterly, annually
    
    # Scheduling
    scheduled_date = Column(DateTime)
    started_date = Column(DateTime)
    completed_date = Column(DateTime)
    next_cycle_date = Column(DateTime)
    
    # Status
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed, cancelled
    assigned_to = Column(UUID(as_uuid=True))
    
    # Progress tracking
    total_items = Column(Integer, default=0)
    counted_items = Column(Integer, default=0)
    variance_items = Column(Integer, default=0)
    completion_percentage = Column(DECIMAL(5, 2), default=0)
    
    # Results summary
    total_variance_value = Column(DECIMAL(15, 4), default=0)
    accuracy_percentage = Column(DECIMAL(5, 2))
    
    # Configuration
    count_tolerance_percentage = Column(DECIMAL(5, 2), default=0)
    require_approval = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    location = relationship("Location")
    cycle_items = relationship("InventoryCycleItem", back_populates="cycle")
    
    __table_args__ = (
        Index("idx_cycle_location", "location_id"),
        Index("idx_cycle_type", "cycle_type"),
        Index("idx_cycle_status", "status"),
        Index("idx_cycle_scheduled", "scheduled_date"),
    )

class InventoryCycleItem(BaseTable):
    """Inventory cycle count item model"""
    __tablename__ = "inventory_cycle_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id = Column(UUID(as_uuid=True), ForeignKey("inventory_cycles.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Count details
    system_quantity = Column(DECIMAL(15, 4), nullable=False)
    first_count = Column(DECIMAL(15, 4))
    second_count = Column(DECIMAL(15, 4))
    final_count = Column(DECIMAL(15, 4))
    
    # Variance analysis
    variance_quantity = Column(DECIMAL(15, 4))
    variance_percentage = Column(DECIMAL(5, 2))
    variance_value = Column(DECIMAL(15, 4))
    within_tolerance = Column(Boolean)
    
    # Count information
    counted_by = Column(UUID(as_uuid=True))
    counted_at = Column(DateTime)
    verified_by = Column(UUID(as_uuid=True))
    verified_at = Column(DateTime)
    
    # Batch/lot information
    lot_number = Column(String(100))
    expiry_date = Column(DateTime)
    
    # Status and notes
    status = Column(String(50), default="pending")  # pending, counted, verified, adjusted
    notes = Column(Text)
    reason_code = Column(String(50))
    
    # Relationships
    cycle = relationship("InventoryCycle", back_populates="cycle_items")
    
    __table_args__ = (
        Index("idx_cycle_item_cycle", "cycle_id"),
        Index("idx_cycle_item_product", "product_id"),
        Index("idx_cycle_item_status", "status"),
        Index("idx_cycle_item_lot", "lot_number"),
    )

# ============================================================================
# Pydantic Schemas
# ============================================================================

class LocationCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    location_type: LocationType
    parent_id: Optional[uuid.UUID] = None
    address: Optional[Dict[str, Any]] = None
    timezone: str = "UTC"
    is_active: bool = True
    accepts_receipts: bool = True
    accepts_shipments: bool = True
    total_capacity: Optional[Decimal] = None
    capacity_unit: str = "cubic_meter"
    manager_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class LocationResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    location_type: str
    parent_id: Optional[uuid.UUID]
    level: int
    path: Optional[str]
    address: Optional[Dict[str, Any]]
    is_active: bool
    total_capacity: Optional[Decimal]
    used_capacity: Decimal
    capacity_utilization: Optional[Decimal] = None
    manager_name: Optional[str]
    contact_email: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InventoryMovementCreate(BaseModel):
    product_id: uuid.UUID
    location_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Optional[Decimal] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    reference_number: Optional[str] = None
    from_location_id: Optional[uuid.UUID] = None
    to_location_id: Optional[uuid.UUID] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

class InventoryMovementResponse(BaseModel):
    id: uuid.UUID
    movement_number: str
    product_id: uuid.UUID
    location_id: uuid.UUID
    movement_type: str
    movement_date: datetime
    quantity: Decimal
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    reference_type: Optional[str]
    reference_number: Optional[str]
    lot_number: Optional[str]
    status: str
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class InventoryBalanceResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    location_id: uuid.UUID
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    minimum_stock: Decimal
    reorder_point: Optional[Decimal]
    status: str
    lot_number: Optional[str]
    expiry_date: Optional[datetime]
    last_movement: Optional[datetime]
    
    class Config:
        from_attributes = True

class StockAdjustmentCreate(BaseModel):
    location_id: uuid.UUID
    adjustment_type: str = Field(..., regex="^(cycle_count|physical_count|adjustment)$")
    reason: Optional[str] = None
    notes: Optional[str] = None
    adjustment_lines: List[Dict[str, Any]]

class StockAdjustmentResponse(BaseModel):
    id: uuid.UUID
    adjustment_number: str
    location_id: uuid.UUID
    adjustment_date: datetime
    adjustment_type: str
    status: str
    total_items: int
    total_variance_value: Decimal
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReplenishmentRuleCreate(BaseModel):
    product_id: uuid.UUID
    location_id: uuid.UUID
    rule_name: str = Field(..., min_length=1, max_length=200)
    replenishment_method: ReplenishmentMethod
    reorder_point: Optional[Decimal] = None
    minimum_order_quantity: Optional[Decimal] = None
    maximum_order_quantity: Optional[Decimal] = None
    lead_time_days: int = 0
    safety_stock_days: int = 0
    preferred_supplier_id: Optional[uuid.UUID] = None
    auto_create_po: bool = False
    is_active: bool = True

class DemandForecastRequest(BaseModel):
    product_id: uuid.UUID
    location_id: Optional[uuid.UUID] = None
    forecast_method: ForecastMethod
    forecast_periods: int = Field(..., ge=1, le=365)
    historical_periods: int = Field(90, ge=30, le=730)
    confidence_level: Decimal = Field(Decimal("95.0"), ge=50, le=99)

class DemandForecastResponse(BaseModel):
    forecasts: List[Dict[str, Any]]
    model_accuracy: Decimal
    model_parameters: Dict[str, Any]
    confidence_intervals: Dict[str, Any]
    recommendations: List[str]

class InventoryReportRequest(BaseModel):
    report_type: str = Field(..., regex="^(valuation|aging|movement|turnover|abc)$")
    location_ids: Optional[List[uuid.UUID]] = None
    product_ids: Optional[List[uuid.UUID]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_zero_stock: bool = False
    group_by: Optional[str] = None

# ============================================================================
# Service Classes
# ============================================================================

class InventoryManagementService:
    """Comprehensive inventory management service"""
    
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client
    
    # Location Management
    async def create_location(self, location_data: LocationCreate) -> Location:
        """Create new inventory location"""
        # Check code uniqueness
        existing_query = select(Location).where(Location.code == location_data.code)
        existing_result = await self.db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Location code already exists")
        
        # Calculate level and path
        level = 0
        path = location_data.code
        
        if location_data.parent_id:
            parent_query = select(Location).where(Location.id == location_data.parent_id)
            parent_result = await self.db.execute(parent_query)
            parent = parent_result.scalar_one_or_none()
            if not parent:
                raise HTTPException(status_code=400, detail="Parent location not found")
            
            level = parent.level + 1
            path = f"{parent.path}/{location_data.code}"
        
        location = Location(
            **location_data.dict(),
            level=level,
            path=path
        )
        
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        
        # Clear cache
        await self.redis.delete("locations:*")
        
        return location
    
    async def get_locations(
        self,
        location_type: Optional[LocationType] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[uuid.UUID] = None,
        page: int = 1,
        size: int = 50
    ) -> Dict[str, Any]:
        """Get locations with filtering"""
        query = select(Location)
        
        if location_type:
            query = query.where(Location.location_type == location_type)
        if is_active is not None:
            query = query.where(Location.is_active == is_active)
        if parent_id:
            query = query.where(Location.parent_id == parent_id)
        
        # Count total
        count_query = select(func.count(Location.id))
        if location_type:
            count_query = count_query.where(Location.location_type == location_type)
        if is_active is not None:
            count_query = count_query.where(Location.is_active == is_active)
        if parent_id:
            count_query = count_query.where(Location.parent_id == parent_id)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get locations
        query = query.order_by(Location.path).offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        locations = result.scalars().all()
        
        # Calculate capacity utilization
        location_responses = []
        for location in locations:
            location_dict = location.__dict__.copy()
            if location.total_capacity and location.total_capacity > 0:
                location_dict["capacity_utilization"] = (
                    location.used_capacity / location.total_capacity * 100
                )
            location_responses.append(location_dict)
        
        return {
            "locations": location_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    # Inventory Balance Management
    async def get_inventory_balance(
        self,
        product_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        status: Optional[InventoryStatus] = None,
        include_zero: bool = False
    ) -> List[InventoryBalance]:
        """Get inventory balances with filtering"""
        query = select(InventoryBalance).options(selectinload(InventoryBalance.location))
        
        if product_id:
            query = query.where(InventoryBalance.product_id == product_id)
        if location_id:
            query = query.where(InventoryBalance.location_id == location_id)
        if status:
            query = query.where(InventoryBalance.status == status)
        if not include_zero:
            query = query.where(InventoryBalance.quantity_on_hand > 0)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_inventory_balance(
        self,
        product_id: uuid.UUID,
        location_id: uuid.UUID,
        quantity_change: Decimal,
        movement_type: MovementType,
        unit_cost: Optional[Decimal] = None,
        lot_number: Optional[str] = None,
        reference_data: Optional[Dict[str, Any]] = None
    ) -> InventoryBalance:
        """Update inventory balance with movement tracking"""
        # Get or create inventory balance
        balance_query = select(InventoryBalance).where(
            and_(
                InventoryBalance.product_id == product_id,
                InventoryBalance.location_id == location_id,
                InventoryBalance.lot_number == lot_number
            )
        )
        balance_result = await self.db.execute(balance_query)
        balance = balance_result.scalar_one_or_none()
        
        if not balance:
            balance = InventoryBalance(
                product_id=product_id,
                location_id=location_id,
                lot_number=lot_number,
                quantity_on_hand=Decimal("0"),
                quantity_available=Decimal("0")
            )
            self.db.add(balance)
        
        # Calculate new quantities
        old_quantity = balance.quantity_on_hand
        new_quantity = old_quantity + quantity_change
        
        if new_quantity < 0 and movement_type in [MovementType.SHIPMENT, MovementType.CONSUMPTION]:
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        
        # Update balance
        balance.quantity_on_hand = max(new_quantity, Decimal("0"))
        balance.quantity_available = balance.quantity_on_hand - balance.quantity_reserved
        balance.last_movement = datetime.utcnow()
        
        # Update costs if provided
        if unit_cost:
            if movement_type in [MovementType.RECEIPT, MovementType.PRODUCTION]:
                # Weighted average cost calculation
                old_total_cost = balance.average_cost * old_quantity if balance.average_cost else Decimal("0")
                new_total_cost = old_total_cost + (unit_cost * abs(quantity_change))
                balance.average_cost = new_total_cost / balance.quantity_on_hand if balance.quantity_on_hand > 0 else unit_cost
            
            balance.unit_cost = unit_cost
            balance.total_cost = balance.quantity_on_hand * balance.average_cost if balance.average_cost else Decimal("0")
        
        # Create movement record
        movement_number = await self._generate_movement_number()
        movement = InventoryMovement(
            movement_number=movement_number,
            product_id=product_id,
            location_id=location_id,
            inventory_balance_id=balance.id,
            movement_type=movement_type,
            quantity=quantity_change,
            unit_cost=unit_cost,
            total_cost=unit_cost * abs(quantity_change) if unit_cost else None,
            lot_number=lot_number,
            status="completed"
        )
        
        if reference_data:
            movement.reference_type = reference_data.get("reference_type")
            movement.reference_id = reference_data.get("reference_id")
            movement.reference_number = reference_data.get("reference_number")
            movement.reason = reference_data.get("reason")
            movement.notes = reference_data.get("notes")
        
        self.db.add(movement)
        await self.db.commit()
        await self.db.refresh(balance)
        
        # Check for alerts
        await self._check_inventory_alerts(balance)
        
        # Clear cache
        await self.redis.delete(f"inventory:{product_id}:{location_id}")
        
        return balance
    
    async def _generate_movement_number(self) -> str:
        """Generate unique movement number"""
        today = datetime.utcnow().strftime("%Y%m%d")
        counter_key = f"movement_counter:{today}"
        
        counter = await self.redis.incr(counter_key)
        await self.redis.expire(counter_key, 86400)  # Expire after 1 day
        
        return f"MOV-{today}-{counter:06d}"
    
    # Stock Transfer Management
    async def create_stock_transfer(
        self,
        product_id: uuid.UUID,
        from_location_id: uuid.UUID,
        to_location_id: uuid.UUID,
        quantity: Decimal,
        reason: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create stock transfer between locations"""
        # Validate locations
        locations_query = select(Location).where(
            Location.id.in_([from_location_id, to_location_id])
        )
        locations_result = await self.db.execute(locations_query)
        locations = {loc.id: loc for loc in locations_result.scalars().all()}
        
        if len(locations) != 2:
            raise HTTPException(status_code=400, detail="Invalid location(s)")
        
        from_location = locations[from_location_id]
        to_location = locations[to_location_id]
        
        if not from_location.accepts_shipments:
            raise HTTPException(status_code=400, detail="From location does not accept shipments")
        if not to_location.accepts_receipts:
            raise HTTPException(status_code=400, detail="To location does not accept receipts")
        
        # Check available inventory
        from_balance_query = select(InventoryBalance).where(
            and_(
                InventoryBalance.product_id == product_id,
                InventoryBalance.location_id == from_location_id
            )
        )
        from_balance_result = await self.db.execute(from_balance_query)
        from_balance = from_balance_result.scalar_one_or_none()
        
        if not from_balance or from_balance.quantity_available < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory at source location")
        
        # Create outbound movement (shipment)
        await self.update_inventory_balance(
            product_id=product_id,
            location_id=from_location_id,
            quantity_change=-quantity,
            movement_type=MovementType.TRANSFER,
            unit_cost=from_balance.unit_cost,
            reference_data={
                "reference_type": "transfer",
                "reference_id": str(to_location_id),
                "reason": reason,
                "notes": notes
            }
        )
        
        # Create inbound movement (receipt)
        await self.update_inventory_balance(
            product_id=product_id,
            location_id=to_location_id,
            quantity_change=quantity,
            movement_type=MovementType.TRANSFER,
            unit_cost=from_balance.unit_cost,
            reference_data={
                "reference_type": "transfer",
                "reference_id": str(from_location_id),
                "reason": reason,
                "notes": notes
            }
        )
        
        return {
            "transfer_id": str(uuid.uuid4()),
            "product_id": product_id,
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "quantity": quantity,
            "status": "completed",
            "message": "Stock transfer completed successfully"
        }
    
    # Stock Adjustment Management
    async def create_stock_adjustment(self, adjustment_data: StockAdjustmentCreate) -> StockAdjustment:
        """Create stock adjustment"""
        adjustment_number = await self._generate_adjustment_number()
        
        adjustment = StockAdjustment(
            adjustment_number=adjustment_number,
            location_id=adjustment_data.location_id,
            adjustment_type=adjustment_data.adjustment_type,
            reason=adjustment_data.reason,
            notes=adjustment_data.notes,
            total_items=len(adjustment_data.adjustment_lines)
        )
        
        self.db.add(adjustment)
        await self.db.flush()  # Get the ID
        
        total_variance = Decimal("0")
        
        for line_data in adjustment_data.adjustment_lines:
            # Get current balance
            balance_query = select(InventoryBalance).where(
                and_(
                    InventoryBalance.product_id == line_data["product_id"],
                    InventoryBalance.location_id == adjustment_data.location_id
                )
            )
            balance_result = await self.db.execute(balance_query)
            balance = balance_result.scalar_one_or_none()
            
            system_qty = balance.quantity_on_hand if balance else Decimal("0")
            counted_qty = Decimal(str(line_data["counted_quantity"]))
            variance_qty = counted_qty - system_qty
            
            # Create adjustment line
            adj_line = StockAdjustmentLine(
                adjustment_id=adjustment.id,
                product_id=line_data["product_id"],
                system_quantity=system_qty,
                counted_quantity=counted_qty,
                variance_quantity=variance_qty,
                unit_cost=balance.unit_cost if balance else None,
                variance_value=variance_qty * balance.unit_cost if balance and balance.unit_cost else Decimal("0"),
                reason=line_data.get("reason"),
                notes=line_data.get("notes")
            )
            
            self.db.add(adj_line)
            total_variance += adj_line.variance_value
            
            # Update inventory balance if variance exists
            if variance_qty != 0:
                await self.update_inventory_balance(
                    product_id=line_data["product_id"],
                    location_id=adjustment_data.location_id,
                    quantity_change=variance_qty,
                    movement_type=MovementType.ADJUSTMENT,
                    unit_cost=balance.unit_cost if balance else None,
                    reference_data={
                        "reference_type": "adjustment",
                        "reference_id": str(adjustment.id),
                        "reference_number": adjustment_number,
                        "reason": adjustment_data.reason
                    }
                )
        
        adjustment.total_variance_value = total_variance
        adjustment.status = "completed"
        
        await self.db.commit()
        await self.db.refresh(adjustment)
        
        return adjustment
    
    async def _generate_adjustment_number(self) -> str:
        """Generate unique adjustment number"""
        today = datetime.utcnow().strftime("%Y%m%d")
        counter_key = f"adjustment_counter:{today}"
        
        counter = await self.redis.incr(counter_key)
        await self.redis.expire(counter_key, 86400)
        
        return f"ADJ-{today}-{counter:06d}"
    
    # Alert Management
    async def _check_inventory_alerts(self, balance: InventoryBalance):
        """Check and create inventory alerts"""
        alerts = []
        
        # Low stock alert
        if balance.reorder_point and balance.quantity_available <= balance.reorder_point:
            alerts.append({
                "alert_type": "low_stock",
                "severity": "high" if balance.quantity_available <= balance.minimum_stock else "medium",
                "title": "Low Stock Alert",
                "message": f"Product inventory is below reorder point. Available: {balance.quantity_available}, Reorder Point: {balance.reorder_point}",
                "trigger_value": balance.quantity_available,
                "threshold_value": balance.reorder_point
            })
        
        # Expiry alert
        if balance.expiry_date:
            days_to_expiry = (balance.expiry_date - datetime.utcnow()).days
            if days_to_expiry <= 30:
                severity = "critical" if days_to_expiry <= 7 else "high" if days_to_expiry <= 14 else "medium"
                alerts.append({
                    "alert_type": "expiry_warning",
                    "severity": severity,
                    "title": "Product Expiry Warning",
                    "message": f"Product will expire in {days_to_expiry} days. Lot: {balance.lot_number}",
                    "trigger_value": days_to_expiry,
                    "threshold_value": 30
                })
        
        # Create alert records
        for alert_data in alerts:
            # Check if similar alert already exists
            existing_query = select(InventoryAlert).where(
                and_(
                    InventoryAlert.product_id == balance.product_id,
                    InventoryAlert.location_id == balance.location_id,
                    InventoryAlert.alert_type == alert_data["alert_type"],
                    InventoryAlert.status == "active"
                )
            )
            existing_result = await self.db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                continue  # Alert already exists
            
            alert = InventoryAlert(
                product_id=balance.product_id,
                location_id=balance.location_id,
                **alert_data
            )
            self.db.add(alert)
        
        if alerts:
            await self.db.commit()
    
    # Forecasting
    async def generate_demand_forecast(
        self,
        request: DemandForecastRequest
    ) -> DemandForecastResponse:
        """Generate demand forecast using specified method"""
        # Get historical data
        historical_data = await self._get_historical_demand(
            request.product_id,
            request.location_id,
            request.historical_periods
        )
        
        if len(historical_data) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient historical data for forecasting"
            )
        
        # Apply forecasting method
        if request.forecast_method == ForecastMethod.MOVING_AVERAGE:
            forecasts = await self._moving_average_forecast(
                historical_data, request.forecast_periods
            )
        elif request.forecast_method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            forecasts = await self._exponential_smoothing_forecast(
                historical_data, request.forecast_periods
            )
        elif request.forecast_method == ForecastMethod.LINEAR_REGRESSION:
            forecasts = await self._linear_regression_forecast(
                historical_data, request.forecast_periods
            )
        else:
            forecasts = await self._simple_forecast(
                historical_data, request.forecast_periods
            )
        
        # Calculate accuracy metrics
        accuracy = await self._calculate_forecast_accuracy(historical_data, forecasts[:len(historical_data)])
        
        # Store forecasts in database
        for i, forecast in enumerate(forecasts):
            forecast_date = datetime.utcnow() + timedelta(days=i+1)
            
            db_forecast = DemandForecast(
                product_id=request.product_id,
                location_id=request.location_id,
                forecast_date=forecast_date,
                forecast_period="daily",
                forecast_method=request.forecast_method,
                forecasted_demand=forecast["demand"],
                lower_bound=forecast.get("lower_bound"),
                upper_bound=forecast.get("upper_bound"),
                confidence_level=request.confidence_level,
                model_parameters=forecast.get("model_params", {}),
                created_by_model=f"inventory_management_v67_{request.forecast_method}"
            )
            self.db.add(db_forecast)
        
        await self.db.commit()
        
        return DemandForecastResponse(
            forecasts=forecasts,
            model_accuracy=accuracy,
            model_parameters={"method": request.forecast_method.value},
            confidence_intervals={"level": request.confidence_level},
            recommendations=await self._generate_forecast_recommendations(forecasts, historical_data)
        )
    
    async def _get_historical_demand(
        self,
        product_id: uuid.UUID,
        location_id: Optional[uuid.UUID],
        periods: int
    ) -> List[Dict[str, Any]]:
        """Get historical demand data for forecasting"""
        # This would typically query sales/movement data
        # For now, return simulated data
        import random
        
        base_demand = 100
        data = []
        
        for i in range(periods):
            date = datetime.utcnow() - timedelta(days=periods - i)
            # Add seasonality and trend
            seasonal_factor = 1 + 0.2 * math.sin(2 * math.pi * i / 30)  # Monthly cycle
            trend_factor = 1 + 0.001 * i  # Slight upward trend
            noise = random.uniform(0.8, 1.2)
            
            demand = base_demand * seasonal_factor * trend_factor * noise
            
            data.append({
                "date": date,
                "demand": round(demand, 2),
                "day_of_week": date.weekday(),
                "month": date.month
            })
        
        return data
    
    async def _moving_average_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        periods: int,
        window: int = 7
    ) -> List[Dict[str, Any]]:
        """Generate forecast using moving average"""
        forecasts = []
        recent_demands = [d["demand"] for d in historical_data[-window:]]
        
        for i in range(periods):
            avg_demand = sum(recent_demands) / len(recent_demands)
            std_dev = (sum((x - avg_demand) ** 2 for x in recent_demands) / len(recent_demands)) ** 0.5
            
            forecasts.append({
                "period": i + 1,
                "demand": round(avg_demand, 2),
                "lower_bound": round(avg_demand - 1.96 * std_dev, 2),
                "upper_bound": round(avg_demand + 1.96 * std_dev, 2),
                "method": "moving_average",
                "model_params": {"window": window}
            })
            
            # Update recent demands (simple approach)
            recent_demands = recent_demands[1:] + [avg_demand]
        
        return forecasts
    
    async def _exponential_smoothing_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        periods: int,
        alpha: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Generate forecast using exponential smoothing"""
        demands = [d["demand"] for d in historical_data]
        forecasts = []
        
        # Initialize
        last_smooth = demands[0]
        
        # Calculate smoothed values
        for demand in demands[1:]:
            last_smooth = alpha * demand + (1 - alpha) * last_smooth
        
        # Generate forecasts
        for i in range(periods):
            forecasts.append({
                "period": i + 1,
                "demand": round(last_smooth, 2),
                "lower_bound": round(last_smooth * 0.8, 2),
                "upper_bound": round(last_smooth * 1.2, 2),
                "method": "exponential_smoothing",
                "model_params": {"alpha": alpha}
            })
        
        return forecasts
    
    async def _linear_regression_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        periods: int
    ) -> List[Dict[str, Any]]:
        """Generate forecast using linear regression"""
        demands = [d["demand"] for d in historical_data]
        n = len(demands)
        
        # Calculate linear regression coefficients
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(demands) / n
        
        numerator = sum((i - x_mean) * (demands[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Generate forecasts
        forecasts = []
        for i in range(periods):
            x_val = n + i
            predicted_demand = slope * x_val + intercept
            
            forecasts.append({
                "period": i + 1,
                "demand": round(max(predicted_demand, 0), 2),
                "lower_bound": round(max(predicted_demand * 0.85, 0), 2),
                "upper_bound": round(predicted_demand * 1.15, 2),
                "method": "linear_regression",
                "model_params": {"slope": slope, "intercept": intercept}
            })
        
        return forecasts
    
    async def _simple_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        periods: int
    ) -> List[Dict[str, Any]]:
        """Simple forecast using average of recent data"""
        recent_demands = [d["demand"] for d in historical_data[-30:]]  # Last 30 days
        avg_demand = sum(recent_demands) / len(recent_demands)
        
        forecasts = []
        for i in range(periods):
            forecasts.append({
                "period": i + 1,
                "demand": round(avg_demand, 2),
                "lower_bound": round(avg_demand * 0.8, 2),
                "upper_bound": round(avg_demand * 1.2, 2),
                "method": "simple_average"
            })
        
        return forecasts
    
    async def _calculate_forecast_accuracy(
        self,
        historical_data: List[Dict[str, Any]],
        forecasts: List[Dict[str, Any]]
    ) -> Decimal:
        """Calculate forecast accuracy using MAPE"""
        if not forecasts or len(forecasts) != len(historical_data):
            return Decimal("0")
        
        total_ape = 0
        count = 0
        
        for i, actual in enumerate(historical_data):
            if i < len(forecasts) and actual["demand"] > 0:
                forecast_val = forecasts[i]["demand"]
                ape = abs((actual["demand"] - forecast_val) / actual["demand"]) * 100
                total_ape += ape
                count += 1
        
        if count == 0:
            return Decimal("0")
        
        mape = 100 - (total_ape / count)  # Convert to accuracy percentage
        return Decimal(str(round(max(mape, 0), 2)))
    
    async def _generate_forecast_recommendations(
        self,
        forecasts: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on forecast"""
        recommendations = []
        
        if not forecasts:
            return recommendations
        
        avg_historical = sum(d["demand"] for d in historical_data) / len(historical_data)
        avg_forecast = sum(f["demand"] for f in forecasts[:7]) / min(7, len(forecasts))
        
        if avg_forecast > avg_historical * 1.2:
            recommendations.append("Demand is expected to increase significantly. Consider increasing safety stock.")
        elif avg_forecast < avg_historical * 0.8:
            recommendations.append("Demand is expected to decrease. Consider reducing inventory levels.")
        
        # Check for seasonality
        if len(forecasts) >= 7:
            weekly_variation = max(f["demand"] for f in forecasts[:7]) - min(f["demand"] for f in forecasts[:7])
            if weekly_variation > avg_forecast * 0.3:
                recommendations.append("High demand variability detected. Implement dynamic safety stock.")
        
        return recommendations

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory Management v67"])

@router.post("/locations", response_model=LocationResponse)
async def create_location(
    location_data: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new inventory location"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = InventoryManagementService(db, redis_client)
    location = await service.create_location(location_data)
    return location

@router.get("/locations", response_model=Dict[str, Any])
async def get_locations(
    location_type: Optional[LocationType] = Query(None),
    is_active: Optional[bool] = Query(None),
    parent_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get inventory locations"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = InventoryManagementService(db, redis_client)
    return await service.get_locations(location_type, is_active, parent_id, page, size)

@router.get("/balances", response_model=List[InventoryBalanceResponse])
async def get_inventory_balances(
    product_id: Optional[uuid.UUID] = Query(None),
    location_id: Optional[uuid.UUID] = Query(None),
    status: Optional[InventoryStatus] = Query(None),
    include_zero: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get inventory balances"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = InventoryManagementService(db, redis_client)
    balances = await service.get_inventory_balance(product_id, location_id, status, include_zero)
    return balances

@router.post("/movements", response_model=InventoryMovementResponse)
async def create_inventory_movement(
    movement_data: InventoryMovementCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create inventory movement"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = InventoryManagementService(db, redis_client)
    
    balance = await service.update_inventory_balance(
        product_id=movement_data.product_id,
        location_id=movement_data.location_id,
        quantity_change=movement_data.quantity if movement_data.movement_type in [MovementType.RECEIPT, MovementType.PRODUCTION] else -movement_data.quantity,
        movement_type=movement_data.movement_type,
        unit_cost=movement_data.unit_cost,
        lot_number=movement_data.lot_number,
        reference_data={
            "reference_type": movement_data.reference_type,
            "reference_id": movement_data.reference_id,
            "reference_number": movement_data.reference_number,
            "reason": movement_data.reason,
            "notes": movement_data.notes
        }
    )
    
    # Get the created movement
    movement_query = select(InventoryMovement).where(
        InventoryMovement.inventory_balance_id == balance.id
    ).order_by(InventoryMovement.created_at.desc()).limit(1)
    
    movement_result = await db.execute(movement_query)
    movement = movement_result.scalar_one()
    
    return movement

@router.post("/transfers", response_model=Dict[str, Any])
async def create_stock_transfer(
    product_id: uuid.UUID,
    from_location_id: uuid.UUID,
    to_location_id: uuid.UUID,
    quantity: Decimal,
    reason: Optional[str] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create stock transfer between locations"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = InventoryManagementService(db, redis_client)
    
    return await service.create_stock_transfer(
        product_id, from_location_id, to_location_id, quantity, reason, notes
    )

@router.post("/adjustments", response_model=StockAdjustmentResponse)
async def create_stock_adjustment(
    adjustment_data: StockAdjustmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create stock adjustment"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = InventoryManagementService(db, redis_client)
    adjustment = await service.create_stock_adjustment(adjustment_data)
    return adjustment

@router.post("/forecast", response_model=DemandForecastResponse)
async def generate_demand_forecast(
    request: DemandForecastRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate demand forecast"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    service = InventoryManagementService(db, redis_client)
    return await service.generate_demand_forecast(request)

@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_inventory_alerts(
    location_id: Optional[uuid.UUID] = Query(None),
    severity: Optional[str] = Query(None),
    status: str = Query("active"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get inventory alerts"""
    query = select(InventoryAlert).options(selectinload(InventoryAlert.location))
    
    if location_id:
        query = query.where(InventoryAlert.location_id == location_id)
    if severity:
        query = query.where(InventoryAlert.severity == severity)
    if status:
        query = query.where(InventoryAlert.status == status)
    
    query = query.order_by(InventoryAlert.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        {
            "id": alert.id,
            "product_id": alert.product_id,
            "location_id": alert.location_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "status": alert.status,
            "created_at": alert.created_at,
            "location_name": alert.location.name if alert.location else None
        }
        for alert in alerts
    ]

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Inventory management service health check"""
    return {
        "status": "healthy",
        "service": "inventory_management_v67",
        "version": "67.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "multi_location_inventory",
            "real_time_tracking",
            "stock_transfers",
            "adjustments",
            "demand_forecasting",
            "automated_alerts",
            "cycle_counting",
            "replenishment_rules"
        ]
    }