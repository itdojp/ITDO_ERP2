"""
CC02 v53.0 Inventory Schemas - Issue #568
10-Day ERP Business API Implementation Sprint - Day 3-4
Enhanced Inventory Management API Schemas
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class InventoryMovementType(str, Enum):
    """Inventory movement type enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DAMAGED = "damaged"
    EXPIRED = "expired"


class InventoryStatus(str, Enum):
    """Inventory status enumeration"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    ALLOCATED = "allocated"
    ON_HOLD = "on_hold"
    DAMAGED = "damaged"
    EXPIRED = "expired"


class LocationType(str, Enum):
    """Location type enumeration"""
    WAREHOUSE = "warehouse"
    STORE = "store"
    VIRTUAL = "virtual"
    TRANSIT = "transit"
    QUARANTINE = "quarantine"


class MovementReason(str, Enum):
    """Movement reason enumeration"""
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DAMAGED = "damaged"
    EXPIRED = "expired"
    RECOUNT = "recount"
    PRODUCTION = "production"
    CONSUMPTION = "consumption"


# Location Schemas
class LocationCreate(BaseModel):
    """Schema for creating inventory location"""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    location_type: LocationType = Field(default=LocationType.WAREHOUSE)
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)
    capacity_limit: Optional[int] = Field(None, ge=0)
    parent_location_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class LocationUpdate(BaseModel):
    """Schema for updating inventory location"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location_type: Optional[LocationType] = None
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    capacity_limit: Optional[int] = Field(None, ge=0)
    parent_location_id: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class LocationResponse(BaseModel):
    """Schema for location API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    code: str
    location_type: LocationType
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = True
    capacity_limit: Optional[int] = None
    current_utilization: Optional[int] = None
    parent_location_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Inventory Item Schemas
class InventoryItemCreate(BaseModel):
    """Schema for creating inventory item"""
    product_id: str
    location_id: str
    quantity: Decimal = Field(..., ge=0, decimal_places=2)
    reserved_quantity: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    allocated_quantity: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    minimum_level: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    maximum_level: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    reorder_point: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    reorder_quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    status: InventoryStatus = Field(default=InventoryStatus.AVAILABLE)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    lot_number: Optional[str] = Field(None, max_length=50)
    serial_number: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    supplier_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('maximum_level')
    @classmethod
    def validate_maximum_level(cls, v, info):
        if v is not None and 'minimum_level' in info.data and info.data['minimum_level'] is not None:
            if v < info.data['minimum_level']:
                raise ValueError('maximum_level must be >= minimum_level')
        return v


class InventoryItemUpdate(BaseModel):
    """Schema for updating inventory item"""
    quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    reserved_quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    allocated_quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    minimum_level: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    maximum_level: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    reorder_point: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    reorder_quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    status: Optional[InventoryStatus] = None
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    lot_number: Optional[str] = Field(None, max_length=50)
    serial_number: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    supplier_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    attributes: Optional[Dict[str, Any]] = None


class InventoryItemResponse(BaseModel):
    """Schema for inventory item API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    location_id: str
    location_name: Optional[str] = None
    quantity: Decimal
    available_quantity: Decimal
    reserved_quantity: Decimal = Decimal("0")
    allocated_quantity: Decimal = Decimal("0")
    minimum_level: Optional[Decimal] = None
    maximum_level: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    status: InventoryStatus
    cost_per_unit: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    expiry_date: Optional[date] = None
    manufacture_date: Optional[date] = None
    supplier_id: Optional[str] = None
    notes: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Movement Schemas
class InventoryMovementCreate(BaseModel):
    """Schema for creating inventory movement"""
    product_id: str
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    movement_type: InventoryMovementType
    quantity: Decimal = Field(..., decimal_places=2)
    unit_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    reason: MovementReason
    reference_id: Optional[str] = Field(None, max_length=100)
    reference_type: Optional[str] = Field(None, max_length=50)
    lot_number: Optional[str] = Field(None, max_length=50)
    serial_number: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    effective_date: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('quantity')
    @classmethod
    def validate_quantity_sign(cls, v, info):
        movement_type = info.data.get('movement_type')
        if movement_type == InventoryMovementType.OUTBOUND and v > 0:
            return -v  # Ensure outbound is negative
        elif movement_type == InventoryMovementType.INBOUND and v < 0:
            return -v  # Ensure inbound is positive
        return v


class InventoryMovementResponse(BaseModel):
    """Schema for inventory movement API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    product_id: str
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    from_location_id: Optional[str] = None
    from_location_name: Optional[str] = None
    to_location_id: Optional[str] = None
    to_location_name: Optional[str] = None
    movement_type: InventoryMovementType
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    reason: MovementReason
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    effective_date: datetime
    processed_by: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# Stock Adjustment Schemas
class StockAdjustmentCreate(BaseModel):
    """Schema for stock adjustment"""
    product_id: str
    location_id: str
    adjustment_quantity: Decimal = Field(..., decimal_places=2)
    reason: str = Field(..., min_length=1, max_length=200)
    reference_id: Optional[str] = Field(None, max_length=100)
    cost_adjustment: Optional[Decimal] = Field(None, decimal_places=4)
    notes: Optional[str] = Field(None, max_length=1000)
    effective_date: Optional[datetime] = None


class StockAdjustmentResponse(BaseModel):
    """Schema for stock adjustment response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    product_id: str
    product_name: Optional[str] = None
    location_id: str
    location_name: Optional[str] = None
    old_quantity: Decimal
    adjustment_quantity: Decimal
    new_quantity: Decimal
    old_value: Optional[Decimal] = None
    adjustment_value: Optional[Decimal] = None
    new_value: Optional[Decimal] = None
    reason: str
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    effective_date: datetime
    processed_by: Optional[str] = None
    created_at: datetime


# Stock Transfer Schemas
class StockTransferCreate(BaseModel):
    """Schema for stock transfer"""
    product_id: str
    from_location_id: str
    to_location_id: str
    quantity: Decimal = Field(..., gt=0, decimal_places=2)
    reason: str = Field(..., min_length=1, max_length=200)
    reference_id: Optional[str] = Field(None, max_length=100)
    lot_number: Optional[str] = Field(None, max_length=50)
    serial_number: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)
    effective_date: Optional[datetime] = None

    @field_validator('to_location_id')
    @classmethod
    def validate_different_locations(cls, v, info):
        if 'from_location_id' in info.data and v == info.data['from_location_id']:
            raise ValueError('to_location_id must be different from from_location_id')
        return v


class StockTransferResponse(BaseModel):
    """Schema for stock transfer response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    product_id: str
    product_name: Optional[str] = None
    from_location_id: str
    from_location_name: Optional[str] = None
    to_location_id: str
    to_location_name: Optional[str] = None
    quantity: Decimal
    reason: str
    reference_id: Optional[str] = None
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    notes: Optional[str] = None
    effective_date: datetime
    processed_by: Optional[str] = None
    created_at: datetime


# Inventory Valuation Schemas
class InventoryValuationResponse(BaseModel):
    """Schema for inventory valuation response"""
    product_id: str
    product_name: str
    product_sku: str
    locations: List[Dict[str, Any]]
    total_quantity: Decimal
    average_cost: Decimal
    total_value: Decimal
    last_updated: datetime


class LocationStockLevel(BaseModel):
    """Schema for location stock level"""
    location_id: str
    location_name: str
    product_id: str
    product_name: str
    product_sku: str
    quantity: Decimal
    available_quantity: Decimal
    reserved_quantity: Decimal
    minimum_level: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    status: InventoryStatus
    needs_reorder: bool = False
    is_low_stock: bool = False
    is_out_of_stock: bool = False


# Alert and Notification Schemas
class InventoryAlert(BaseModel):
    """Schema for inventory alerts"""
    id: str
    alert_type: str
    severity: str
    product_id: str
    product_name: str
    location_id: str
    location_name: str
    current_quantity: Decimal
    threshold_quantity: Optional[Decimal] = None
    message: str
    is_acknowledged: bool = False
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


# Statistics and Analytics Schemas
class InventoryStatistics(BaseModel):
    """Enhanced inventory statistics"""
    total_locations: int
    active_locations: int
    total_products_tracked: int
    total_inventory_items: int
    
    # Stock Statistics
    total_stock_quantity: Decimal
    total_inventory_value: Decimal
    average_stock_value: Decimal
    
    # Status Breakdown
    available_items: int
    reserved_items: int
    allocated_items: int
    on_hold_items: int
    damaged_items: int
    expired_items: int
    
    # Alert Statistics
    low_stock_alerts: int
    out_of_stock_alerts: int
    expired_alerts: int
    reorder_alerts: int
    
    # Movement Statistics
    total_movements_today: int
    inbound_movements_today: int
    outbound_movements_today: int
    
    # Performance Metrics
    locations_by_type: Dict[str, int]
    top_value_products: List[Dict[str, Any]]
    movement_summary: Dict[str, int]
    
    last_updated: datetime
    calculation_time_ms: float


# List Response Schemas
class InventoryItemListResponse(BaseModel):
    """Schema for paginated inventory item list responses"""
    items: List[InventoryItemResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class InventoryMovementListResponse(BaseModel):
    """Schema for paginated inventory movement list responses"""
    items: List[InventoryMovementResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


class LocationListResponse(BaseModel):
    """Schema for paginated location list responses"""
    items: List[LocationResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# Bulk Operations Schemas
class BulkInventoryOperation(BaseModel):
    """Schema for bulk inventory operations"""
    items: List[InventoryItemCreate]
    validate_only: bool = Field(default=False)
    stop_on_error: bool = Field(default=False)


class BulkInventoryResult(BaseModel):
    """Schema for bulk inventory operation results"""
    created_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    created_items: List[InventoryItemResponse] = Field(default_factory=list)
    updated_items: List[InventoryItemResponse] = Field(default_factory=list)
    failed_items: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: Optional[float] = None


# Error Schemas
class InventoryError(BaseModel):
    """Inventory-specific error response"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# API Response Wrappers
class InventoryAPIResponse(BaseModel):
    """Inventory-specific API response"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Union[
        InventoryItemResponse, 
        InventoryMovementResponse, 
        LocationResponse,
        InventoryStatistics,
        InventoryItemListResponse,
        InventoryMovementListResponse
    ]] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None