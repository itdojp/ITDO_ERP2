"""
Inventory Integration System Schemas for CC02 v62.0
Pydantic schemas for comprehensive inventory management API
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

from app.schemas.base import TimestampedSchema


# Base schemas
class InventoryIntegrationBase(BaseModel):
    """Base schema for inventory integration entities."""
    
    model_config = ConfigDict(from_attributes=True)


# Real-time inventory tracking schemas
class RealtimeInventoryUpdate(BaseModel):
    """Real-time inventory update message."""
    
    product_id: int
    warehouse_id: int
    quantity_change: Decimal
    movement_type: str
    timestamp: datetime
    user_id: Optional[int] = None
    reference_id: Optional[str] = None
    reason: Optional[str] = None


class RealtimeInventorySnapshot(InventoryIntegrationBase):
    """Current inventory snapshot for real-time tracking."""
    
    product_id: int
    warehouse_id: int
    current_stock: Decimal
    reserved_stock: Decimal
    available_stock: Decimal
    in_transit_stock: Decimal
    last_movement_at: datetime
    alerts_count: int = 0


class RealtimeAlertCreate(InventoryIntegrationBase):
    """Schema for creating real-time alerts."""
    
    alert_type: str = Field(..., description="Type of alert (low_stock, out_of_stock, etc.)")
    severity: str = Field(default="medium", description="Alert severity level")
    title: str = Field(..., max_length=200)
    message: str = Field(..., description="Alert message")
    product_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    inventory_item_id: Optional[int] = None
    current_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    context_data: Optional[dict[str, Any]] = None
    auto_resolve_after_hours: Optional[int] = None


class RealtimeAlert(RealtimeAlertCreate, TimestampedSchema):
    """Real-time inventory alert response schema."""
    
    id: int
    organization_id: int
    difference: Optional[Decimal] = None
    is_active: bool = True
    is_acknowledged: bool = False
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    auto_resolved: bool = False
    notification_sent: bool = False
    notification_channels: Optional[list[str]] = None


# Auto-ordering system schemas
class AutoOrderRuleCreate(InventoryIntegrationBase):
    """Schema for creating auto order rules."""
    
    product_id: int
    warehouse_id: int
    rule_name: str = Field(..., max_length=200)
    trigger_level: Decimal = Field(..., gt=0, description="Reorder point quantity")
    safety_stock_level: Decimal = Field(default=0, ge=0)
    order_quantity: Decimal = Field(..., gt=0)
    minimum_order_quantity: Decimal = Field(default=1, gt=0)
    maximum_order_quantity: Optional[Decimal] = Field(default=None, gt=0)
    use_economic_order_quantity: bool = False
    lead_time_days: int = Field(default=1, ge=0)
    demand_forecast_days: int = Field(default=30, ge=1)
    preferred_supplier_id: Optional[int] = None
    supplier_part_number: Optional[str] = Field(default=None, max_length=100)
    supplier_unit_cost: Optional[Decimal] = Field(default=None, gt=0)
    auto_approve_threshold: Optional[Decimal] = Field(default=None, gt=0)
    requires_manual_approval: bool = False
    schedule_enabled: bool = False
    schedule_frequency_days: Optional[int] = Field(default=None, ge=1)
    advanced_config: Optional[dict[str, Any]] = None
    
    @validator('maximum_order_quantity')
    def validate_max_order_quantity(cls, v, values):
        if v is not None and 'order_quantity' in values and v < values['order_quantity']:
            raise ValueError('Maximum order quantity must be >= order quantity')
        return v


class AutoOrderRuleUpdate(InventoryIntegrationBase):
    """Schema for updating auto order rules."""
    
    rule_name: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = None
    trigger_level: Optional[Decimal] = Field(default=None, gt=0)
    safety_stock_level: Optional[Decimal] = Field(default=None, ge=0)
    order_quantity: Optional[Decimal] = Field(default=None, gt=0)
    minimum_order_quantity: Optional[Decimal] = Field(default=None, gt=0)
    maximum_order_quantity: Optional[Decimal] = Field(default=None, gt=0)
    use_economic_order_quantity: Optional[bool] = None
    lead_time_days: Optional[int] = Field(default=None, ge=0)
    demand_forecast_days: Optional[int] = Field(default=None, ge=1)
    preferred_supplier_id: Optional[int] = None
    supplier_part_number: Optional[str] = Field(default=None, max_length=100)
    supplier_unit_cost: Optional[Decimal] = Field(default=None, gt=0)
    auto_approve_threshold: Optional[Decimal] = Field(default=None, gt=0)
    requires_manual_approval: Optional[bool] = None
    schedule_enabled: Optional[bool] = None
    schedule_frequency_days: Optional[int] = Field(default=None, ge=1)
    advanced_config: Optional[dict[str, Any]] = None


class AutoOrderRule(AutoOrderRuleCreate, TimestampedSchema):
    """Auto order rule response schema."""
    
    id: int
    organization_id: int
    is_active: bool = True
    last_order_date: Optional[datetime] = None
    next_scheduled_check: Optional[datetime] = None
    successful_orders: int = 0
    failed_orders: int = 0
    total_order_value: Decimal = 0
    average_fulfillment_time: Optional[int] = None


class AutoOrderCreate(InventoryIntegrationBase):
    """Schema for creating auto orders."""
    
    order_rule_id: int
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_cost: Optional[Decimal] = Field(default=None, gt=0)
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = Field(default=None, max_length=200)
    expected_delivery_date: Optional[datetime] = None
    requires_approval: bool = False
    order_metadata: Optional[dict[str, Any]] = None


class AutoOrder(AutoOrderCreate, TimestampedSchema):
    """Auto order response schema."""
    
    id: int
    order_number: str
    product_id: int
    warehouse_id: int
    organization_id: int
    status: str
    total_cost: Optional[Decimal] = None
    stock_level_at_creation: Decimal = 0
    trigger_level_at_creation: Decimal = 0
    supplier_order_number: Optional[str] = None
    order_date: datetime
    actual_delivery_date: Optional[datetime] = None
    approved_by: Optional[int] = None
    approval_date: Optional[datetime] = None
    approval_notes: Optional[str] = None
    processed_by: Optional[int] = None
    processing_date: Optional[datetime] = None
    external_order_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


# Inventory analytics schemas
class InventoryAnalyticsCreate(InventoryIntegrationBase):
    """Schema for creating inventory analytics records."""
    
    product_id: int
    warehouse_id: int
    period_start: datetime
    period_end: datetime
    total_inbound: Decimal = 0
    total_outbound: Decimal = 0
    total_adjustments: Decimal = 0
    average_daily_usage: Decimal = 0
    demand_variance: Optional[Decimal] = None
    seasonal_factor: Optional[Decimal] = None
    trend_factor: Optional[Decimal] = None
    abc_classification: Optional[str] = Field(default=None, regex=r'^[ABC]$')
    revenue_contribution: Optional[Decimal] = Field(default=None, ge=0, le=1)
    predicted_demand_30d: Optional[Decimal] = None
    predicted_demand_60d: Optional[Decimal] = None
    predicted_demand_90d: Optional[Decimal] = None
    forecast_accuracy: Optional[Decimal] = Field(default=None, ge=0, le=1)
    stockout_risk_score: Optional[Decimal] = Field(default=None, ge=0, le=1)
    overstock_risk_score: Optional[Decimal] = Field(default=None, ge=0, le=1)
    obsolescence_risk_score: Optional[Decimal] = Field(default=None, ge=0, le=1)
    turnover_rate: Optional[Decimal] = Field(default=None, ge=0)
    carrying_cost: Optional[Decimal] = Field(default=None, ge=0)
    service_level: Optional[Decimal] = Field(default=None, ge=0, le=1)
    extended_metrics: Optional[dict[str, Any]] = None


class InventoryAnalytics(InventoryAnalyticsCreate, TimestampedSchema):
    """Inventory analytics response schema."""
    
    id: int
    organization_id: int


# Prediction system schemas
class PredictionModelCreate(InventoryIntegrationBase):
    """Schema for creating prediction models."""
    
    model_name: str = Field(..., max_length=200)
    model_type: str = Field(..., max_length=50)
    version: str = Field(default="1.0", max_length=20)
    product_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    prediction_horizon_days: int = Field(default=30, ge=1)
    training_window_days: int = Field(default=365, ge=30)
    features_used: list[str] = Field(..., description="List of features used in the model")
    hyperparameters: Optional[dict[str, Any]] = None
    model_path: Optional[str] = Field(default=None, max_length=500)
    model_metadata: Optional[dict[str, Any]] = None


class PredictionModel(PredictionModelCreate, TimestampedSchema):
    """Prediction model response schema."""
    
    id: int
    organization_id: int
    accuracy_score: Optional[Decimal] = None
    mae: Optional[Decimal] = None
    rmse: Optional[Decimal] = None
    mape: Optional[Decimal] = None
    last_trained_at: Optional[datetime] = None
    training_duration_seconds: Optional[int] = None
    training_data_points: Optional[int] = None
    is_active: bool = True
    is_deployed: bool = False
    deployment_date: Optional[datetime] = None
    feature_importance: Optional[dict[str, float]] = None


class InventoryPredictionCreate(InventoryIntegrationBase):
    """Schema for creating inventory predictions."""
    
    model_id: int
    product_id: int
    warehouse_id: int
    prediction_date: datetime
    forecast_date: datetime
    horizon_days: int = Field(..., ge=1)
    predicted_demand: Decimal = Field(..., ge=0)
    confidence_interval_lower: Optional[Decimal] = Field(default=None, ge=0)
    confidence_interval_upper: Optional[Decimal] = Field(default=None, ge=0)
    confidence_level: Decimal = Field(default=0.95, ge=0, le=1)
    seasonal_component: Optional[Decimal] = None
    trend_component: Optional[Decimal] = None
    external_factors: Optional[dict[str, Any]] = None


class InventoryPrediction(InventoryPredictionCreate, TimestampedSchema):
    """Inventory prediction response schema."""
    
    id: int
    organization_id: int
    actual_demand: Optional[Decimal] = None
    prediction_error: Optional[Decimal] = None
    absolute_percentage_error: Optional[Decimal] = None
    prediction_quality_score: Optional[Decimal] = None


# Shipping integration schemas
class ShippingInventorySyncCreate(InventoryIntegrationBase):
    """Schema for creating shipping inventory sync records."""
    
    sync_id: str = Field(..., max_length=100)
    shipment_id: str = Field(..., max_length=100)
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    product_id: int
    warehouse_id: int
    inventory_item_id: int
    quantity_shipped: Decimal = Field(..., gt=0)
    ship_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    carrier_name: Optional[str] = Field(default=None, max_length=100)
    service_type: Optional[str] = Field(default=None, max_length=50)
    customer_id: Optional[int] = None
    destination_address: Optional[str] = None
    shipping_metadata: Optional[dict[str, Any]] = None


class ShippingInventorySync(ShippingInventorySyncCreate, TimestampedSchema):
    """Shipping inventory sync response schema."""
    
    id: int
    organization_id: int
    status: str
    quantity_delivered: Decimal = 0
    quantity_returned: Decimal = 0
    actual_delivery_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    inventory_reserved_at_ship: bool = False
    inventory_reduced_at_ship: bool = False
    inventory_restored_on_return: bool = False
    last_sync_at: datetime
    sync_status: str = "pending"
    sync_error: Optional[str] = None
    tracking_events: Optional[list[dict[str, Any]]] = None


# Dashboard and reporting schemas
class InventoryDashboardStats(InventoryIntegrationBase):
    """Dashboard statistics for inventory management."""
    
    total_products: int
    total_warehouses: int
    total_stock_value: Decimal
    low_stock_items: int
    out_of_stock_items: int
    overstock_items: int
    pending_orders: int
    active_alerts: int
    average_turnover_rate: Optional[Decimal] = None
    service_level_percentage: Optional[Decimal] = None


class WarehousePerformanceMetrics(InventoryIntegrationBase):
    """Performance metrics for warehouse operations."""
    
    warehouse_id: int
    warehouse_name: str
    total_items: int
    utilization_percentage: Optional[Decimal] = None
    total_stock_value: Decimal
    monthly_throughput: Decimal
    average_fulfillment_time: Optional[Decimal] = None
    accuracy_rate: Optional[Decimal] = None
    cost_per_unit_handled: Optional[Decimal] = None


class ProductAnalyticsSummary(InventoryIntegrationBase):
    """Product-level analytics summary."""
    
    product_id: int
    product_name: str
    abc_classification: Optional[str] = None
    current_stock: Decimal
    available_stock: Decimal
    average_daily_usage: Decimal
    days_of_stock_remaining: Optional[int] = None
    reorder_recommended: bool = False
    predicted_stockout_date: Optional[datetime] = None
    turnover_rate: Optional[Decimal] = None
    carrying_cost: Optional[Decimal] = None


# WebSocket message schemas
class WebSocketMessage(BaseModel):
    """Base WebSocket message schema."""
    
    type: str
    timestamp: datetime
    data: dict[str, Any]


class InventoryUpdateMessage(WebSocketMessage):
    """Real-time inventory update WebSocket message."""
    
    type: str = "inventory_update"
    data: RealtimeInventorySnapshot


class AlertMessage(WebSocketMessage):
    """Real-time alert WebSocket message."""
    
    type: str = "alert"
    data: RealtimeAlert


class OrderStatusMessage(WebSocketMessage):
    """Order status update WebSocket message."""
    
    type: str = "order_status"
    data: AutoOrder


# Bulk operation schemas
class BulkInventoryUpdate(BaseModel):
    """Schema for bulk inventory updates."""
    
    updates: list[RealtimeInventoryUpdate] = Field(..., max_items=1000)
    batch_id: Optional[str] = None
    validate_before_processing: bool = True


class BulkOperationResult(BaseModel):
    """Result of bulk operations."""
    
    total_items: int
    successful_items: int
    failed_items: int
    errors: list[dict[str, Any]] = []
    batch_id: Optional[str] = None
    processing_time_seconds: float


# Search and filter schemas
class InventorySearchFilters(BaseModel):
    """Filters for inventory search operations."""
    
    product_ids: Optional[list[int]] = None
    warehouse_ids: Optional[list[int]] = None
    low_stock_only: bool = False
    out_of_stock_only: bool = False
    overstock_only: bool = False
    abc_classifications: Optional[list[str]] = Field(default=None, regex=r'^[ABC]$')
    min_stock_value: Optional[Decimal] = Field(default=None, ge=0)
    max_stock_value: Optional[Decimal] = Field(default=None, ge=0)
    expiry_within_days: Optional[int] = Field(default=None, ge=0)
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""
    
    items: list[Any]
    total: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=1000)
    pages: int
    has_next: bool
    has_prev: bool