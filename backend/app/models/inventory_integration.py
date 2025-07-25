"""
Inventory Integration System Models for CC02 v62.0
Comprehensive inventory management with real-time tracking, auto-ordering, analytics, shipping integration, and warehouse management
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.inventory import InventoryItem, Warehouse
    from app.models.organization import Organization
    from app.models.product import Product
    from app.models.user import User


class AutoOrderStatus(str, Enum):
    """Auto order status enumeration."""
    
    PENDING = "pending"
    PROCESSED = "processed"
    APPROVED = "approved"
    PLACED = "placed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PredictionModelType(str, Enum):
    """Prediction model type enumeration."""
    
    LINEAR_REGRESSION = "linear_regression"
    ARIMA = "arima"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


class AlertType(str, Enum):
    """Real-time alert type enumeration."""
    
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCK = "overstock"
    EXPIRY_WARNING = "expiry_warning"
    REORDER_POINT = "reorder_point"
    UNUSUAL_MOVEMENT = "unusual_movement"


class ShipmentStatus(str, Enum):
    """Shipment status enumeration."""
    
    PENDING = "pending"
    PICKED = "picked"
    PACKED = "packed"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"


class InventoryAnalytics(SoftDeletableModel):
    """Inventory analytics and metrics storage."""
    
    __tablename__ = "inventory_analytics"
    
    # Basic fields
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Analytics period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Movement metrics
    total_inbound: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    total_outbound: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    total_adjustments: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    average_daily_usage: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    
    # Demand metrics
    demand_variance: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    seasonal_factor: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    trend_factor: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    
    # ABC analysis
    abc_classification: Mapped[str | None] = mapped_column(String(1))  # A, B, or C
    revenue_contribution: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))  # Percentage
    
    # Forecasting
    predicted_demand_30d: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    predicted_demand_60d: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    predicted_demand_90d: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    forecast_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))  # 0-1 scale
    
    # Risk metrics
    stockout_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    overstock_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    obsolescence_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    
    # Performance metrics
    turnover_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    carrying_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    service_level: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    
    # Additional metrics as JSON
    extended_metrics: Mapped[dict | None] = mapped_column(JSON)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse") 
    organization: Mapped["Organization"] = relationship("Organization")
    
    def __repr__(self) -> str:
        return f"<InventoryAnalytics(id={self.id}, product_id={self.product_id}, period_start='{self.period_start}')>"


class AutoOrderRule(SoftDeletableModel):
    """Auto ordering rules configuration."""
    
    __tablename__ = "auto_order_rules"
    
    # Basic fields
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Rule configuration
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Trigger conditions
    trigger_level: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)  # Reorder point
    safety_stock_level: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    
    # Order quantities
    order_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    minimum_order_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=1)
    maximum_order_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    
    # Dynamic ordering parameters
    use_economic_order_quantity: Mapped[bool] = mapped_column(Boolean, default=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=1)
    demand_forecast_days: Mapped[int] = mapped_column(Integer, default=30)
    
    # Supplier information
    preferred_supplier_id: Mapped[int | None] = mapped_column(Integer)  # External supplier ID
    supplier_part_number: Mapped[str | None] = mapped_column(String(100))
    supplier_unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    
    # Auto-approval settings
    auto_approve_threshold: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))  # Max order value for auto-approval
    requires_manual_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Schedule settings
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_frequency_days: Mapped[int | None] = mapped_column(Integer)
    last_order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_scheduled_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Performance tracking
    successful_orders: Mapped[int] = mapped_column(Integer, default=0)
    failed_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_order_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    average_fulfillment_time: Mapped[int | None] = mapped_column(Integer)  # Days
    
    # Configuration as JSON
    advanced_config: Mapped[dict | None] = mapped_column(JSON)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    organization: Mapped["Organization"] = relationship("Organization")
    auto_orders: Mapped[list["AutoOrder"]] = relationship("AutoOrder", back_populates="order_rule")
    
    def calculate_eoq(self, annual_demand: Decimal, ordering_cost: Decimal, holding_cost: Decimal) -> Decimal:
        """Calculate Economic Order Quantity."""
        if holding_cost <= 0:
            return self.order_quantity
        
        import math
        eoq = math.sqrt((2 * float(annual_demand) * float(ordering_cost)) / float(holding_cost))
        return Decimal(str(eoq))
    
    def is_reorder_needed(self, current_stock: Decimal, reserved_stock: Decimal) -> bool:
        """Check if reorder is needed based on current conditions."""
        available_stock = current_stock - reserved_stock
        return available_stock <= self.trigger_level
    
    def __repr__(self) -> str:
        return f"<AutoOrderRule(id={self.id}, product_id={self.product_id}, rule_name='{self.rule_name}')>"


class AutoOrder(SoftDeletableModel):
    """Auto-generated order records."""
    
    __tablename__ = "auto_orders"
    
    # Basic fields
    order_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    order_rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("auto_order_rules.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Order details
    status: Mapped[str] = mapped_column(String(20), default=AutoOrderStatus.PENDING.value)
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    
    # Trigger conditions when order was created
    stock_level_at_creation: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    trigger_level_at_creation: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    
    # Supplier information
    supplier_id: Mapped[int | None] = mapped_column(Integer)
    supplier_name: Mapped[str | None] = mapped_column(String(200))
    supplier_order_number: Mapped[str | None] = mapped_column(String(100))
    
    # Dates
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expected_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_notes: Mapped[str | None] = mapped_column(Text)
    
    # Processing details
    processed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    processing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_order_id: Mapped[str | None] = mapped_column(String(100))  # ID in external system
    
    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    
    # Additional data
    order_metadata: Mapped[dict | None] = mapped_column(JSON)
    
    # Relationships
    order_rule: Mapped["AutoOrderRule"] = relationship("AutoOrderRule", back_populates="auto_orders")
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    organization: Mapped["Organization"] = relationship("Organization")
    approved_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])
    processed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[processed_by])
    
    def can_retry(self) -> bool:
        """Check if order can be retried."""
        return self.retry_count < self.max_retries and self.status in [AutoOrderStatus.PENDING.value, AutoOrderStatus.CANCELLED.value]
    
    def mark_processed(self, processed_by: int, external_id: str | None = None) -> None:
        """Mark order as processed."""
        self.status = AutoOrderStatus.PROCESSED.value
        self.processed_by = processed_by
        self.processing_date = datetime.now(UTC)
        if external_id:
            self.external_order_id = external_id
    
    def __repr__(self) -> str:
        return f"<AutoOrder(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class RealtimeInventoryAlert(SoftDeletableModel):
    """Real-time inventory alerts and notifications."""
    
    __tablename__ = "realtime_inventory_alerts"
    
    # Basic fields
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Related entities
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id"))
    warehouse_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("warehouses.id"))
    inventory_item_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("inventory_items.id"))
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Alert data
    current_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    difference: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    
    # Status and resolution
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    
    # Auto-resolution
    auto_resolve_after_hours: Mapped[int | None] = mapped_column(Integer)
    auto_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Notification tracking
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_channels: Mapped[list | None] = mapped_column(JSON)  # email, slack, webhook, etc.
    
    # Additional context
    context_data: Mapped[dict | None] = mapped_column(JSON)
    
    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product")
    warehouse: Mapped[Optional["Warehouse"]] = relationship("Warehouse")
    inventory_item: Mapped[Optional["InventoryItem"]] = relationship("InventoryItem")
    organization: Mapped["Organization"] = relationship("Organization")
    acknowledged_by_user: Mapped[Optional["User"]] = relationship("User")
    
    def acknowledge(self, user_id: int) -> None:
        """Acknowledge the alert."""
        self.is_acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now(UTC)
    
    def resolve(self, notes: str | None = None) -> None:
        """Resolve the alert."""
        self.is_active = False
        self.resolved_at = datetime.now(UTC)
        if notes:
            self.resolution_notes = notes
    
    def __repr__(self) -> str:
        return f"<RealtimeInventoryAlert(id={self.id}, type='{self.alert_type}', severity='{self.severity}')>"


class ShippingInventorySync(SoftDeletableModel):
    """Shipping and inventory synchronization records."""
    
    __tablename__ = "shipping_inventory_sync"
    
    # Basic fields
    sync_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    shipment_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), index=True)
    
    # Related entities
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Shipment details
    status: Mapped[str] = mapped_column(String(20), default=ShipmentStatus.PENDING.value)
    quantity_shipped: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    quantity_returned: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    
    # Dates
    ship_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    return_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Inventory impact
    inventory_reserved_at_ship: Mapped[bool] = mapped_column(Boolean, default=False)
    inventory_reduced_at_ship: Mapped[bool] = mapped_column(Boolean, default=False)
    inventory_restored_on_return: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Carrier information
    carrier_name: Mapped[str | None] = mapped_column(String(100))
    service_type: Mapped[str | None] = mapped_column(String(50))
    
    # Customer/destination info
    customer_id: Mapped[int | None] = mapped_column(Integer)
    destination_address: Mapped[str | None] = mapped_column(Text)
    
    # Sync status
    last_sync_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    sync_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, synced, failed
    sync_error: Mapped[str | None] = mapped_column(Text)
    
    # Additional tracking data
    tracking_events: Mapped[list | None] = mapped_column(JSON)
    shipping_metadata: Mapped[dict | None] = mapped_column(JSON)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    inventory_item: Mapped["InventoryItem"] = relationship("InventoryItem")
    organization: Mapped["Organization"] = relationship("Organization")
    
    def update_status(self, new_status: str, tracking_events: list | None = None) -> None:
        """Update shipment status and inventory accordingly."""
        old_status = self.status
        self.status = new_status
        self.last_sync_at = datetime.now(UTC)
        
        if tracking_events:
            self.tracking_events = tracking_events
        
        # Handle inventory updates based on status changes
        if old_status != ShipmentStatus.DELIVERED.value and new_status == ShipmentStatus.DELIVERED.value:
            self.quantity_delivered = self.quantity_shipped
            self.actual_delivery_date = datetime.now(UTC)
        
        elif old_status != ShipmentStatus.RETURNED.value and new_status == ShipmentStatus.RETURNED.value:
            self.return_date = datetime.now(UTC)
    
    def __repr__(self) -> str:
        return f"<ShippingInventorySync(id={self.id}, shipment_id='{self.shipment_id}', status='{self.status}')>"


class PredictionModel(SoftDeletableModel):
    """Machine learning models for inventory prediction."""
    
    __tablename__ = "prediction_models"
    
    # Basic fields
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    
    # Scope
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id"))
    warehouse_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("warehouses.id"))
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Model configuration
    prediction_horizon_days: Mapped[int] = mapped_column(Integer, default=30)
    training_window_days: Mapped[int] = mapped_column(Integer, default=365)
    features_used: Mapped[list] = mapped_column(JSON, nullable=False)
    hyperparameters: Mapped[dict | None] = mapped_column(JSON)
    
    # Performance metrics
    accuracy_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    mae: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))  # Mean Absolute Error
    rmse: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))  # Root Mean Square Error
    mape: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))   # Mean Absolute Percentage Error
    
    # Training information
    last_trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    training_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    training_data_points: Mapped[int | None] = mapped_column(Integer)
    
    # Model status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    deployment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Model artifacts
    model_path: Mapped[str | None] = mapped_column(String(500))  # Path to serialized model
    feature_importance: Mapped[dict | None] = mapped_column(JSON)
    model_metadata: Mapped[dict | None] = mapped_column(JSON)
    
    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product")
    warehouse: Mapped[Optional["Warehouse"]] = relationship("Warehouse")
    organization: Mapped["Organization"] = relationship("Organization")
    predictions: Mapped[list["InventoryPrediction"]] = relationship("InventoryPrediction", back_populates="model")
    
    def is_stale(self, max_age_days: int = 7) -> bool:
        """Check if model needs retraining."""
        if not self.last_trained_at:
            return True
        
        age = datetime.now(UTC) - self.last_trained_at
        return age.days > max_age_days
    
    def __repr__(self) -> str:
        return f"<PredictionModel(id={self.id}, name='{self.model_name}', type='{self.model_type}')>"


class InventoryPrediction(SoftDeletableModel):
    """Inventory demand predictions generated by ML models."""
    
    __tablename__ = "inventory_predictions"
    
    # Basic fields
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("prediction_models.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Prediction period
    prediction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forecast_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Predictions
    predicted_demand: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    confidence_interval_lower: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    confidence_interval_upper: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    confidence_level: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0.95)  # 0.95 = 95%
    
    # Actual vs predicted (filled after the fact)
    actual_demand: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    prediction_error: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    absolute_percentage_error: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    
    # Context factors
    seasonal_component: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    trend_component: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    external_factors: Mapped[dict | None] = mapped_column(JSON)
    
    # Quality metrics
    prediction_quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    
    # Relationships
    model: Mapped["PredictionModel"] = relationship("PredictionModel", back_populates="predictions")
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    organization: Mapped["Organization"] = relationship("Organization")
    
    def calculate_accuracy(self) -> Decimal | None:
        """Calculate prediction accuracy when actual data is available."""
        if self.actual_demand is None or self.predicted_demand <= 0:
            return None
        
        error = abs(self.actual_demand - self.predicted_demand)
        accuracy = 1 - (error / max(self.actual_demand, self.predicted_demand))
        return max(Decimal(0), accuracy)
    
    def is_within_confidence_interval(self) -> bool | None:
        """Check if actual demand falls within confidence interval."""
        if (self.actual_demand is None or 
            self.confidence_interval_lower is None or 
            self.confidence_interval_upper is None):
            return None
        
        return self.confidence_interval_lower <= self.actual_demand <= self.confidence_interval_upper
    
    def __repr__(self) -> str:
        return f"<InventoryPrediction(id={self.id}, product_id={self.product_id}, predicted_demand={self.predicted_demand})>"