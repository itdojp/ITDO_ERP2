from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import re

class WarehouseBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    
    # 住所情報
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Japan"
    
    # 連絡先
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # 倉庫設定
    warehouse_type: str = Field(default="standard", regex="^(standard|cold_storage|hazardous)$")
    capacity_sqm: Optional[Decimal] = Field(None, ge=0)
    capacity_volume: Optional[Decimal] = Field(None, ge=0)

    @validator('code')
    def code_valid(cls, v):
        if not re.match(r'^[A-Z0-9_-]+$', v):
            raise ValueError('Code must contain only uppercase letters, numbers, hyphens and underscores')
        return v

class WarehouseCreate(WarehouseBase):
    address_line2: Optional[str] = None
    state: Optional[str] = None
    manager_id: Optional[str] = None
    max_weight: Optional[Decimal] = Field(None, ge=0)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    operating_hours: Dict[str, str] = {}
    timezone: str = "Asia/Tokyo"
    is_default: bool = False
    settings: Dict[str, Any] = {}

class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[str] = None
    capacity_sqm: Optional[Decimal] = Field(None, ge=0)
    capacity_volume: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class WarehouseResponse(WarehouseBase):
    id: str
    address_line2: Optional[str]
    state: Optional[str]
    manager_id: Optional[str]
    max_weight: Optional[Decimal]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    operating_hours: Dict[str, str]
    timezone: str
    is_active: bool
    is_default: bool
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    total_locations: int = 0
    total_inventory_items: int = 0

    class Config:
        orm_mode = True

class WarehouseLocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    
    # 位置情報
    zone: Optional[str] = Field(None, max_length=10)
    aisle: Optional[str] = Field(None, max_length=10)
    rack: Optional[str] = Field(None, max_length=10)
    level: Optional[str] = Field(None, max_length=10)
    position: Optional[str] = Field(None, max_length=10)
    
    # 容量
    max_capacity: int = Field(default=0, ge=0)
    max_weight: Optional[Decimal] = Field(None, ge=0)
    location_type: str = Field(default="storage", regex="^(storage|picking|receiving|shipping)$")

class WarehouseLocationCreate(WarehouseLocationBase):
    warehouse_id: str
    attributes: Dict[str, Any] = {}

class WarehouseLocationResponse(WarehouseLocationBase):
    id: str
    warehouse_id: str
    current_capacity: int
    is_active: bool
    attributes: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class InventoryItemBase(BaseModel):
    product_id: str
    warehouse_id: str
    location_id: Optional[str] = None
    
    # バッチ・シリアル
    batch_number: Optional[str] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    manufacturing_date: Optional[datetime] = None

class InventoryItemCreate(InventoryItemBase):
    quantity_available: int = Field(default=0, ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    quality_status: str = Field(default="good", regex="^(good|damaged|expired|quarantine)$")
    reorder_point: int = Field(default=0, ge=0)
    safety_stock: int = Field(default=0, ge=0)
    attributes: Dict[str, Any] = {}

class InventoryItemUpdate(BaseModel):
    location_id: Optional[str] = None
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    quality_status: Optional[str] = Field(None, regex="^(good|damaged|expired|quarantine)$")
    quality_notes: Optional[str] = None
    reorder_point: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    safety_stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    attributes: Optional[Dict[str, Any]] = None

class InventoryItemResponse(InventoryItemBase):
    id: str
    
    # 在庫数量
    quantity_available: int
    quantity_reserved: int
    quantity_allocated: int
    quantity_on_order: int
    quantity_in_transit: int
    
    # コスト情報
    unit_cost: Optional[Decimal]
    average_cost: Optional[Decimal]
    fifo_cost: Optional[Decimal]
    
    # 品質情報
    quality_status: str
    quality_notes: Optional[str]
    last_inspection_date: Optional[datetime]
    next_inspection_date: Optional[datetime]
    
    # 最適化情報
    reorder_point: int
    max_stock_level: Optional[int]
    safety_stock: int
    economic_order_qty: Optional[int]
    
    # 活動履歴
    last_movement_date: Optional[datetime]
    last_count_date: Optional[datetime]
    last_sale_date: Optional[datetime]
    
    # ステータス
    is_active: bool
    is_locked: bool
    
    # メタデータ
    attributes: Dict[str, Any]
    serial_numbers: List[str]
    
    # タイムスタンプ
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class StockMovementBase(BaseModel):
    movement_type: str = Field(..., regex="^(inbound|outbound|adjustment|transfer)$")
    transaction_type: Optional[str] = None
    quantity: int = Field(..., ne=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    reason: Optional[str] = Field(None, max_length=200)

class StockMovementCreate(StockMovementBase):
    inventory_item_id: str
    from_warehouse_id: Optional[str] = None
    to_warehouse_id: Optional[str] = None
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    movement_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class StockMovementResponse(StockMovementBase):
    id: str
    inventory_item_id: str
    product_id: str
    total_cost: Optional[Decimal]
    stock_before: int
    stock_after: int
    
    from_warehouse_id: Optional[str]
    to_warehouse_id: Optional[str]
    from_location_id: Optional[str]
    to_location_id: Optional[str]
    
    reference_type: Optional[str]
    reference_id: Optional[str]
    reference_line_id: Optional[str]
    
    requested_by: Optional[str]
    approved_by: Optional[str]
    executed_by: Optional[str]
    
    movement_date: datetime
    requested_date: Optional[datetime]
    approved_date: Optional[datetime]
    executed_date: Optional[datetime]
    
    status: str
    notes: Optional[str]
    
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class InventoryReservationBase(BaseModel):
    quantity_reserved: int = Field(..., gt=0)
    reservation_type: str = Field(default="sales_order")
    expected_release_date: Optional[datetime] = None

class InventoryReservationCreate(InventoryReservationBase):
    inventory_item_id: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None

class InventoryReservationResponse(InventoryReservationBase):
    id: str
    inventory_item_id: str
    product_id: str
    reference_type: Optional[str]
    reference_id: Optional[str]
    reference_line_id: Optional[str]
    reserved_date: datetime
    actual_release_date: Optional[datetime]
    reserved_by: Optional[str]
    released_by: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class CycleCountBase(BaseModel):
    cycle_count_number: str = Field(..., min_length=1, max_length=100)
    count_type: str = Field(default="full", regex="^(full|partial|abc_analysis)$")
    scheduled_date: datetime

class CycleCountCreate(CycleCountBase):
    warehouse_id: str
    location_id: Optional[str] = None
    assigned_to: Optional[str] = None
    supervised_by: Optional[str] = None
    notes: Optional[str] = None

class CycleCountUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    supervised_by: Optional[str] = None
    status: Optional[str] = Field(None, regex="^(planned|in_progress|completed|cancelled)$")
    notes: Optional[str] = None

class CycleCountResponse(CycleCountBase):
    id: str
    warehouse_id: str
    location_id: Optional[str]
    start_date: Optional[datetime]
    completion_date: Optional[datetime]
    assigned_to: Optional[str]
    supervised_by: Optional[str]
    status: str
    total_items_planned: int
    total_items_counted: int
    total_discrepancies: int
    accuracy_percentage: Optional[Decimal]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class CycleCountItemBase(BaseModel):
    system_quantity: int = Field(..., ge=0)
    counted_quantity: Optional[int] = Field(None, ge=0)

class CycleCountItemCreate(CycleCountItemBase):
    cycle_count_id: str
    inventory_item_id: str

class CycleCountItemUpdate(BaseModel):
    counted_quantity: Optional[int] = Field(None, ge=0)
    requires_recount: Optional[bool] = None
    adjustment_reason: Optional[str] = None
    notes: Optional[str] = None

class CycleCountItemResponse(CycleCountItemBase):
    id: str
    cycle_count_id: str
    inventory_item_id: str
    product_id: str
    variance_quantity: int
    variance_value: Optional[Decimal]
    count_date: Optional[datetime]
    counted_by: Optional[str]
    recounted_by: Optional[str]
    status: str
    requires_recount: bool
    adjustment_applied: bool
    adjustment_reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class StockAlertBase(BaseModel):
    alert_type: str = Field(..., regex="^(low_stock|out_of_stock|overstock|expiry)$")
    severity: str = Field(default="medium", regex="^(low|medium|high|critical)$")
    current_quantity: int = Field(..., ge=0)
    message: str = Field(..., min_length=1)

class StockAlertCreate(StockAlertBase):
    product_id: str
    warehouse_id: str
    threshold_quantity: Optional[int] = None
    recommended_order_quantity: Optional[int] = None

class StockAlertResponse(StockAlertBase):
    id: str
    product_id: str
    warehouse_id: str
    threshold_quantity: Optional[int]
    recommended_order_quantity: Optional[int]
    status: str
    acknowledged_by: Optional[str]
    acknowledged_date: Optional[datetime]
    resolved_date: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class InventoryStatsResponse(BaseModel):
    total_warehouses: int
    active_warehouses: int
    total_locations: int
    total_inventory_items: int
    total_inventory_value: Decimal
    by_warehouse: Dict[str, Dict[str, Any]]
    by_status: Dict[str, int]
    low_stock_alerts: int
    out_of_stock_alerts: int
    expiring_items: int

class InventoryValuationResponse(BaseModel):
    total_value: Decimal
    by_warehouse: Dict[str, Decimal]
    by_category: Dict[str, Decimal]
    by_cost_method: Dict[str, Decimal]
    valuation_date: datetime

class StockLevelSummaryResponse(BaseModel):
    product_id: str
    product_name: str
    total_available: int
    total_reserved: int
    total_allocated: int
    by_warehouse: List[Dict[str, Any]]
    reorder_needed: bool
    low_stock_warning: bool

class BulkInventoryUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]]
    reason: str = Field(..., min_length=1, max_length=200)
    apply_immediately: bool = False

class BulkInventoryUpdateResponse(BaseModel):
    success_count: int
    error_count: int
    processed_items: List[str]
    errors: List[Dict[str, Any]]