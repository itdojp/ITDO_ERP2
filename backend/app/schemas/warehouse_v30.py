import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class WarehouseBase(BaseModel):
    warehouse_code: str = Field(
        ..., min_length=1, max_length=50, description="倉庫コード"
    )
    warehouse_name: str = Field(..., min_length=1, max_length=200, description="倉庫名")
    warehouse_type: str = Field(
        default="distribution",
        regex="^(distribution|manufacturing|retail|cross_dock|3pl)$",
    )

    @validator("warehouse_code")
    def validate_warehouse_code(cls, v):
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Warehouse code must contain only uppercase letters, numbers, underscores, and hyphens"
            )
        return v


class WarehouseCreate(WarehouseBase):
    # 所在地情報
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="JP", regex="^[A-Z]{2}$")

    # 連絡先
    phone: Optional[str] = Field(None, max_length=50)
    fax: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)

    # 地理的位置
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    timezone: str = Field(default="Asia/Tokyo", max_length=50)

    # 物理的仕様
    total_area: Optional[Decimal] = Field(None, ge=0, description="総面積(m²)")
    storage_area: Optional[Decimal] = Field(None, ge=0, description="保管面積(m²)")
    office_area: Optional[Decimal] = Field(None, ge=0, description="事務所面積(m²)")
    loading_dock_count: int = Field(default=0, ge=0, description="ローディングドック数")
    ceiling_height: Optional[Decimal] = Field(None, ge=0, description="天井高(m)")
    floor_load_capacity: Optional[Decimal] = Field(
        None, ge=0, description="床荷重容量(kg/m²)"
    )

    # 環境制御
    climate_controlled: bool = False
    temperature_min: Optional[Decimal] = Field(None, ge=-50, le=50)
    temperature_max: Optional[Decimal] = Field(None, ge=-50, le=50)
    humidity_controlled: bool = False
    humidity_min: Optional[Decimal] = Field(None, ge=0, le=100)
    humidity_max: Optional[Decimal] = Field(None, ge=0, le=100)

    # 運用時間
    operating_hours_start: Optional[str] = Field(
        None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    operating_hours_end: Optional[str] = Field(
        None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    operating_days: List[str] = Field(default=["mon", "tue", "wed", "thu", "fri"])
    shift_pattern: str = Field(default="single", regex="^(single|double|continuous)$")

    # 管理者・組織
    warehouse_manager_id: Optional[str] = None
    supervisor_ids: List[str] = []
    organization_id: Optional[str] = None
    cost_center_code: Optional[str] = Field(None, max_length=50)

    # 能力・機能
    receiving_capacity: int = Field(default=0, ge=0, description="受入能力(件/日)")
    shipping_capacity: int = Field(default=0, ge=0, description="出荷能力(件/日)")
    storage_systems: List[str] = []
    handling_equipment: List[str] = []

    # セキュリティ・コンプライアンス
    security_level: str = Field(
        default="standard", regex="^(basic|standard|high|maximum)$"
    )
    access_control_system: bool = False
    camera_surveillance: bool = False
    fire_suppression_system: Optional[str] = Field(
        None, regex="^(sprinkler|gas|foam|none)$"
    )
    security_certifications: List[str] = []

    # 技術・自動化
    wms_system: Optional[str] = Field(None, max_length=100)
    automation_level: str = Field(
        default="manual", regex="^(manual|semi_automated|automated)$"
    )
    barcode_scanning: bool = True
    rfid_enabled: bool = False
    voice_picking: bool = False
    automated_sorting: bool = False

    # システム統合
    erp_integration: bool = True
    tms_integration: bool = False
    customs_bonded: bool = False
    free_trade_zone: bool = False

    # パフォーマンス目標
    utilization_target: Decimal = Field(default=85, ge=0, le=100)
    accuracy_target: Decimal = Field(default=99.5, ge=0, le=100)

    # 費用情報
    annual_operating_cost: Optional[Decimal] = Field(None, ge=0)
    lease_cost_per_month: Optional[Decimal] = Field(None, ge=0)
    labor_cost_per_hour: Optional[Decimal] = Field(None, ge=0)

    # 設定・制御
    is_default: bool = False
    allow_negative_inventory: bool = False
    require_lot_tracking: bool = False
    require_serial_tracking: bool = False

    # アラート設定
    low_space_alert_threshold: Decimal = Field(default=90, ge=0, le=100)
    high_temperature_alert: bool = False
    security_breach_alert: bool = True

    # メタデータ
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    notes: Optional[str] = None

    @validator("operating_days")
    def validate_operating_days(cls, v):
        valid_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        for day in v:
            if day not in valid_days:
                raise ValueError(f"Invalid day: {day}. Must be one of {valid_days}")
        return v

    @validator("temperature_max")
    def validate_temperature_range(cls, v, values):
        if (
            v is not None
            and "temperature_min" in values
            and values["temperature_min"] is not None
        ):
            if v <= values["temperature_min"]:
                raise ValueError("temperature_max must be greater than temperature_min")
        return v

    @validator("humidity_max")
    def validate_humidity_range(cls, v, values):
        if (
            v is not None
            and "humidity_min" in values
            and values["humidity_min"] is not None
        ):
            if v <= values["humidity_min"]:
                raise ValueError("humidity_max must be greater than humidity_min")
        return v

    @validator("storage_area")
    def validate_storage_area(cls, v, values):
        if (
            v is not None
            and "total_area" in values
            and values["total_area"] is not None
        ):
            if v > values["total_area"]:
                raise ValueError("storage_area cannot exceed total_area")
        return v


class WarehouseUpdate(BaseModel):
    warehouse_name: Optional[str] = Field(None, min_length=1, max_length=200)
    warehouse_type: Optional[str] = Field(
        None, regex="^(distribution|manufacturing|retail|cross_dock|3pl)$"
    )
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    total_area: Optional[Decimal] = Field(None, ge=0)
    storage_area: Optional[Decimal] = Field(None, ge=0)
    loading_dock_count: Optional[int] = Field(None, ge=0)
    climate_controlled: Optional[bool] = None
    temperature_min: Optional[Decimal] = Field(None, ge=-50, le=50)
    temperature_max: Optional[Decimal] = Field(None, ge=-50, le=50)
    operating_hours_start: Optional[str] = Field(
        None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    operating_hours_end: Optional[str] = Field(
        None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    warehouse_manager_id: Optional[str] = None
    receiving_capacity: Optional[int] = Field(None, ge=0)
    shipping_capacity: Optional[int] = Field(None, ge=0)
    security_level: Optional[str] = Field(None, regex="^(basic|standard|high|maximum)$")
    automation_level: Optional[str] = Field(
        None, regex="^(manual|semi_automated|automated)$"
    )
    utilization_target: Optional[Decimal] = Field(None, ge=0, le=100)
    accuracy_target: Optional[Decimal] = Field(None, ge=0, le=100)
    status: Optional[str] = Field(None, regex="^(active|inactive|maintenance|closed)$")
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class WarehouseResponse(WarehouseBase):
    id: str
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state_province: Optional[str]
    postal_code: Optional[str]
    country: str
    phone: Optional[str]
    fax: Optional[str]
    email: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    timezone: str
    total_area: Optional[Decimal]
    storage_area: Optional[Decimal]
    office_area: Optional[Decimal]
    loading_dock_count: int
    ceiling_height: Optional[Decimal]
    floor_load_capacity: Optional[Decimal]
    climate_controlled: bool
    temperature_min: Optional[Decimal]
    temperature_max: Optional[Decimal]
    humidity_controlled: bool
    humidity_min: Optional[Decimal]
    humidity_max: Optional[Decimal]
    operating_hours_start: Optional[str]
    operating_hours_end: Optional[str]
    operating_days: List[str]
    shift_pattern: str
    warehouse_manager_id: Optional[str]
    supervisor_ids: List[str]
    organization_id: Optional[str]
    cost_center_code: Optional[str]
    receiving_capacity: int
    shipping_capacity: int
    storage_systems: List[str]
    handling_equipment: List[str]
    security_level: str
    access_control_system: bool
    camera_surveillance: bool
    fire_suppression_system: Optional[str]
    security_certifications: List[str]
    wms_system: Optional[str]
    automation_level: str
    barcode_scanning: bool
    rfid_enabled: bool
    voice_picking: bool
    automated_sorting: bool
    erp_integration: bool
    tms_integration: bool
    customs_bonded: bool
    free_trade_zone: bool
    utilization_target: Decimal
    current_utilization: Decimal
    accuracy_target: Decimal
    current_accuracy: Optional[Decimal]
    annual_operating_cost: Optional[Decimal]
    lease_cost_per_month: Optional[Decimal]
    labor_cost_per_hour: Optional[Decimal]
    status: str
    is_default: bool
    allow_negative_inventory: bool
    require_lot_tracking: bool
    require_serial_tracking: bool
    low_space_alert_threshold: Decimal
    high_temperature_alert: bool
    security_breach_alert: bool
    tags: List[str]
    custom_fields: Dict[str, Any]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class WarehouseZoneBase(BaseModel):
    zone_code: str = Field(..., min_length=1, max_length=50)
    zone_name: str = Field(..., min_length=1, max_length=200)
    zone_type: str = Field(
        default="storage",
        regex="^(storage|receiving|shipping|staging|quality_control)$",
    )


class WarehouseZoneCreate(WarehouseZoneBase):
    warehouse_id: str
    area: Optional[Decimal] = Field(None, ge=0, description="面積(m²)")
    height: Optional[Decimal] = Field(None, ge=0, description="高さ(m)")
    volume: Optional[Decimal] = Field(None, ge=0, description="容積(m³)")
    floor_level: int = Field(default=1, ge=1)
    grid_coordinates: Optional[str] = Field(None, max_length=20)

    # 環境設定
    temperature_controlled: bool = False
    min_temperature: Optional[Decimal] = Field(None, ge=-50, le=50)
    max_temperature: Optional[Decimal] = Field(None, ge=-50, le=50)
    humidity_controlled: bool = False
    hazmat_approved: bool = False
    security_level: str = Field(
        default="standard", regex="^(basic|standard|high|maximum)$"
    )

    # 機能設定
    picking_zone: bool = True
    replenishment_zone: bool = False
    quarantine_zone: bool = False
    fast_moving_items: bool = False
    slow_moving_items: bool = False

    # 制約設定
    max_weight_capacity: Optional[Decimal] = Field(None, ge=0)
    allowed_product_categories: List[str] = []
    prohibited_product_categories: List[str] = []
    storage_rules: Dict[str, Any] = {}

    # アクセス制御
    restricted_access: bool = False
    authorized_personnel: List[str] = []
    access_equipment_required: List[str] = []

    # 目標設定
    max_utilization_target: Decimal = Field(default=85, ge=0, le=100)


class WarehouseZoneUpdate(BaseModel):
    zone_name: Optional[str] = Field(None, min_length=1, max_length=200)
    zone_type: Optional[str] = Field(
        None, regex="^(storage|receiving|shipping|staging|quality_control)$"
    )
    area: Optional[Decimal] = Field(None, ge=0)
    height: Optional[Decimal] = Field(None, ge=0)
    volume: Optional[Decimal] = Field(None, ge=0)
    temperature_controlled: Optional[bool] = None
    min_temperature: Optional[Decimal] = Field(None, ge=-50, le=50)
    max_temperature: Optional[Decimal] = Field(None, ge=-50, le=50)
    max_weight_capacity: Optional[Decimal] = Field(None, ge=0)
    picking_zone: Optional[bool] = None
    replenishment_zone: Optional[bool] = None
    restricted_access: Optional[bool] = None
    max_utilization_target: Optional[Decimal] = Field(None, ge=0, le=100)
    status: Optional[str] = Field(None, regex="^(active|inactive|maintenance|blocked)$")


class WarehouseZoneResponse(WarehouseZoneBase):
    id: str
    warehouse_id: str
    area: Optional[Decimal]
    height: Optional[Decimal]
    volume: Optional[Decimal]
    floor_level: int
    grid_coordinates: Optional[str]
    temperature_controlled: bool
    min_temperature: Optional[Decimal]
    max_temperature: Optional[Decimal]
    humidity_controlled: bool
    hazmat_approved: bool
    security_level: str
    picking_zone: bool
    replenishment_zone: bool
    quarantine_zone: bool
    fast_moving_items: bool
    slow_moving_items: bool
    max_weight_capacity: Optional[Decimal]
    allowed_product_categories: List[str]
    prohibited_product_categories: List[str]
    storage_rules: Dict[str, Any]
    restricted_access: bool
    authorized_personnel: List[str]
    access_equipment_required: List[str]
    current_utilization: Decimal
    max_utilization_target: Decimal
    location_count: int
    occupied_locations: int
    status: str
    last_inventory_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        orm_mode = True


class WarehouseLocationBase(BaseModel):
    location_code: str = Field(..., min_length=1, max_length=50)
    location_type: str = Field(default="bin", regex="^(bin|shelf|pallet|floor|bulk)$")


class WarehouseLocationCreate(WarehouseLocationBase):
    warehouse_id: str
    zone_id: str
    barcode: Optional[str] = Field(None, max_length=100)
    qr_code: Optional[str] = Field(None, max_length=200)

    # 物理的寸法
    length: Optional[Decimal] = Field(None, ge=0)
    width: Optional[Decimal] = Field(None, ge=0)
    height: Optional[Decimal] = Field(None, ge=0)
    volume: Optional[Decimal] = Field(None, ge=0)
    weight_capacity: Optional[Decimal] = Field(None, ge=0)

    # 座標・位置
    aisle: Optional[str] = Field(None, max_length=10)
    bay: Optional[str] = Field(None, max_length=10)
    level: Optional[str] = Field(None, max_length=10)
    position: Optional[str] = Field(None, max_length=10)
    coordinates: Optional[str] = Field(None, max_length=50)

    # 機能設定
    pickable: bool = True
    replenishable: bool = True
    mix_products_allowed: bool = False
    mix_lots_allowed: bool = False

    # 制約・要件
    product_restrictions: List[str] = []
    temperature_requirements: Dict[str, Any] = {}
    handling_requirements: List[str] = []

    # アクセス・装備
    access_method: str = Field(
        default="manual", regex="^(manual|forklift|crane|automated)$"
    )
    equipment_required: List[str] = []
    pick_priority: int = Field(default=50, ge=1, le=100)

    # メタデータ
    location_attributes: Dict[str, Any] = {}
    tags: List[str] = []
    notes: Optional[str] = None


class WarehouseLocationUpdate(BaseModel):
    location_code: Optional[str] = Field(None, min_length=1, max_length=50)
    location_type: Optional[str] = Field(None, regex="^(bin|shelf|pallet|floor|bulk)$")
    barcode: Optional[str] = Field(None, max_length=100)
    weight_capacity: Optional[Decimal] = Field(None, ge=0)
    pickable: Optional[bool] = None
    replenishable: Optional[bool] = None
    mix_products_allowed: Optional[bool] = None
    access_method: Optional[str] = Field(
        None, regex="^(manual|forklift|crane|automated)$"
    )
    pick_priority: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[str] = Field(
        None, regex="^(available|occupied|blocked|damaged|maintenance)$"
    )
    blocked_reason: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class WarehouseLocationResponse(WarehouseLocationBase):
    id: str
    warehouse_id: str
    zone_id: str
    barcode: Optional[str]
    qr_code: Optional[str]
    length: Optional[Decimal]
    width: Optional[Decimal]
    height: Optional[Decimal]
    volume: Optional[Decimal]
    weight_capacity: Optional[Decimal]
    aisle: Optional[str]
    bay: Optional[str]
    level: Optional[str]
    position: Optional[str]
    coordinates: Optional[str]
    pickable: bool
    replenishable: bool
    mix_products_allowed: bool
    mix_lots_allowed: bool
    product_restrictions: List[str]
    temperature_requirements: Dict[str, Any]
    handling_requirements: List[str]
    access_method: str
    equipment_required: List[str]
    pick_priority: int
    is_occupied: bool
    current_stock_quantity: Decimal
    current_weight: Decimal
    occupancy_percentage: Decimal
    primary_product_id: Optional[str]
    lot_number: Optional[str]
    expiration_date: Optional[datetime]
    last_pick_date: Optional[datetime]
    last_replenish_date: Optional[datetime]
    last_count_date: Optional[datetime]
    pick_frequency: int
    status: str
    blocked_reason: Optional[str]
    priority_sequence: int
    last_inspection_date: Optional[datetime]
    cleanliness_rating: Optional[int]
    damage_assessment: Optional[str]
    location_attributes: Dict[str, Any]
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        orm_mode = True


class InventoryMovementBase(BaseModel):
    movement_type: str = Field(
        ..., regex="^(receipt|shipment|adjustment|transfer|cycle_count)$"
    )
    quantity: Decimal = Field(..., description="移動数量")
    unit_of_measure: str = Field(..., min_length=1, max_length=20)


class InventoryMovementCreate(InventoryMovementBase):
    warehouse_id: str
    location_id: Optional[str] = None
    product_id: str
    movement_subtype: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    reference_line: Optional[int] = Field(None, ge=1)

    # コスト情報
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    total_cost: Optional[Decimal] = Field(None, ge=0)

    # ロット・シリアル管理
    lot_number: Optional[str] = Field(None, max_length=100)
    serial_numbers: List[str] = []
    expiration_date: Optional[datetime] = None
    manufacture_date: Optional[datetime] = None

    # 移動詳細
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    from_warehouse_id: Optional[str] = None
    to_warehouse_id: Optional[str] = None

    # 日程
    planned_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None

    # 理由・背景
    reason_code: Optional[str] = Field(None, max_length=50)
    reason_description: Optional[str] = None
    business_process: Optional[str] = Field(None, max_length=100)

    # 品質・検査
    quality_status: str = Field(
        default="approved", regex="^(approved|rejected|quarantine|pending)$"
    )
    inspection_required: bool = False

    # 運送情報
    carrier: Optional[str] = Field(None, max_length=200)
    tracking_number: Optional[str] = Field(None, max_length=100)
    freight_cost: Optional[Decimal] = Field(None, ge=0)
    delivery_method: Optional[str] = Field(None, max_length=50)

    # 税務・会計
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    duty_amount: Optional[Decimal] = Field(None, ge=0)
    accounting_period: Optional[str] = Field(None, regex="^\\d{4}-\\d{2}$")  # YYYY-MM
    cost_center: Optional[str] = Field(None, max_length=50)

    # システム情報
    source_system: Optional[str] = Field(None, max_length=100)

    # メタデータ
    custom_fields: Dict[str, Any] = {}
    tags: List[str] = []
    notes: Optional[str] = None


class InventoryMovementUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    lot_number: Optional[str] = Field(None, max_length=100)
    serial_numbers: Optional[List[str]] = None
    expiration_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    quality_status: Optional[str] = Field(
        None, regex="^(approved|rejected|quarantine|pending)$"
    )
    inspection_required: Optional[bool] = None
    reason_code: Optional[str] = Field(None, max_length=50)
    reason_description: Optional[str] = None
    status: Optional[str] = Field(
        None, regex="^(pending|in_progress|completed|cancelled|error)$"
    )
    notes: Optional[str] = None


class InventoryMovementResponse(InventoryMovementBase):
    id: str
    warehouse_id: str
    location_id: Optional[str]
    product_id: str
    movement_subtype: Optional[str]
    reference_number: Optional[str]
    reference_line: Optional[int]
    cost_per_unit: Optional[Decimal]
    total_cost: Optional[Decimal]
    lot_number: Optional[str]
    serial_numbers: List[str]
    expiration_date: Optional[datetime]
    manufacture_date: Optional[datetime]
    from_location_id: Optional[str]
    to_location_id: Optional[str]
    from_warehouse_id: Optional[str]
    to_warehouse_id: Optional[str]
    planned_date: Optional[datetime]
    actual_date: Optional[datetime]
    performed_by: Optional[str]
    approved_by: Optional[str]
    reason_code: Optional[str]
    reason_description: Optional[str]
    business_process: Optional[str]
    quality_status: str
    inspection_required: bool
    inspector_id: Optional[str]
    inspection_date: Optional[datetime]
    inspection_notes: Optional[str]
    carrier: Optional[str]
    tracking_number: Optional[str]
    freight_cost: Optional[Decimal]
    delivery_method: Optional[str]
    tax_amount: Optional[Decimal]
    duty_amount: Optional[Decimal]
    accounting_period: Optional[str]
    cost_center: Optional[str]
    source_system: Optional[str]
    integration_batch_id: Optional[str]
    sync_status: str
    error_messages: List[str]
    retry_count: int
    status: str
    is_reversed: bool
    reversal_movement_id: Optional[str]
    inventory_impact: Decimal
    value_impact: Decimal
    custom_fields: Dict[str, Any]
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        orm_mode = True


class CycleCountBase(BaseModel):
    count_name: str = Field(..., min_length=1, max_length=200)
    count_type: str = Field(default="cycle", regex="^(cycle|full|spot|exception)$")
    planned_date: datetime


class CycleCountCreate(CycleCountBase):
    warehouse_id: str
    count_scope: str = Field(
        default="zone", regex="^(zone|location|product|category|all)$"
    )
    zone_ids: List[str] = []
    location_ids: List[str] = []
    product_ids: List[str] = []
    category_ids: List[str] = []

    # 担当者設定
    count_manager_id: Optional[str] = None
    assigned_counters: List[str] = []
    supervisor_id: Optional[str] = None

    # 設定・ルール
    count_method: str = Field(default="manual", regex="^(manual|scanner|rfid)$")
    recount_required: bool = True
    tolerance_percentage: Decimal = Field(default=2.0, ge=0, le=100)
    minimum_count_value: Optional[Decimal] = Field(None, ge=0)
    exclude_zero_quantities: bool = False

    # システム設定
    freeze_inventory: bool = True
    auto_adjust: bool = False
    generate_adjustments: bool = True

    # メタデータ
    instructions: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []


class CycleCountUpdate(BaseModel):
    count_name: Optional[str] = Field(None, min_length=1, max_length=200)
    planned_date: Optional[datetime] = None
    count_manager_id: Optional[str] = None
    assigned_counters: Optional[List[str]] = None
    supervisor_id: Optional[str] = None
    tolerance_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    minimum_count_value: Optional[Decimal] = Field(None, ge=0)
    freeze_inventory: Optional[bool] = None
    auto_adjust: Optional[bool] = None
    status: Optional[str] = Field(
        None, regex="^(planned|in_progress|completed|cancelled|on_hold)$"
    )
    instructions: Optional[str] = None
    notes: Optional[str] = None


class CycleCountResponse(CycleCountBase):
    id: str
    warehouse_id: str
    count_number: str
    count_scope: str
    zone_ids: List[str]
    location_ids: List[str]
    product_ids: List[str]
    category_ids: List[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    cutoff_time: Optional[datetime]
    count_manager_id: Optional[str]
    assigned_counters: List[str]
    supervisor_id: Optional[str]
    count_method: str
    recount_required: bool
    tolerance_percentage: Decimal
    minimum_count_value: Optional[Decimal]
    exclude_zero_quantities: bool
    status: str
    completion_percentage: Decimal
    total_locations_planned: int
    locations_counted: int
    locations_remaining: int
    total_items_counted: int
    items_with_variance: int
    total_variance_value: Decimal
    accuracy_percentage: Optional[Decimal]
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    freeze_inventory: bool
    auto_adjust: bool
    generate_adjustments: bool
    instructions: Optional[str]
    notes: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        orm_mode = True


class WarehousePerformanceResponse(BaseModel):
    id: str
    warehouse_id: str
    performance_period: str
    period_type: str
    period_start: datetime
    period_end: datetime

    # 受入・出荷
    receipts_planned: int
    receipts_actual: int
    receipt_accuracy: Optional[Decimal]
    receipt_timeliness: Optional[Decimal]
    average_receipt_time: Optional[Decimal]
    shipments_planned: int
    shipments_actual: int
    shipment_accuracy: Optional[Decimal]
    shipment_timeliness: Optional[Decimal]
    average_shipment_time: Optional[Decimal]

    # ピッキング・処理
    orders_processed: int
    lines_picked: int
    pick_accuracy: Optional[Decimal]
    picks_per_hour: Optional[Decimal]

    # 在庫管理
    inventory_accuracy: Optional[Decimal]
    stock_adjustments_count: int
    stock_adjustments_value: Decimal
    stockouts_count: int

    # 利用率・容量
    storage_utilization: Optional[Decimal]
    dock_utilization: Optional[Decimal]
    equipment_utilization: Optional[Decimal]

    # 品質・損害
    damage_incidents: int
    damage_value: Decimal
    quality_holds: int
    returns_processed: int

    # 人員・労働
    total_labor_hours: Decimal
    overtime_hours: Decimal
    staff_count_average: Optional[Decimal]
    labor_cost_total: Decimal

    # 安全・コンプライアンス
    safety_incidents: int
    near_misses: int
    compliance_violations: int
    training_hours: Decimal

    # コスト・財務
    operating_cost_total: Decimal
    cost_per_shipment: Optional[Decimal]
    cost_per_receipt: Optional[Decimal]
    cost_per_pick: Optional[Decimal]

    # 顧客サービス
    order_fulfillment_rate: Optional[Decimal]
    customer_complaints: int
    service_level_achievement: Optional[Decimal]

    # 技術・システム
    automation_uptime: Optional[Decimal]
    system_downtime_hours: Decimal
    barcode_scan_accuracy: Optional[Decimal]

    # 環境
    energy_consumption: Optional[Decimal]
    waste_generated: Optional[Decimal]
    recycling_rate: Optional[Decimal]
    carbon_footprint: Optional[Decimal]

    # 計算情報
    calculation_date: Optional[datetime]
    calculated_by: Optional[str]
    data_quality_score: Optional[Decimal]
    performance_vs_target: Dict[str, Any]
    benchmark_comparison: Dict[str, Any]

    # メタデータ
    notes: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class WarehouseAnalyticsResponse(BaseModel):
    total_warehouses: int
    active_warehouses: int
    inactive_warehouses: int
    total_storage_area: Decimal
    total_utilization: Decimal
    avg_utilization: Decimal
    warehouses_by_type: Dict[str, int]
    warehouses_by_automation_level: Dict[str, int]
    top_warehouses_by_utilization: List[Dict[str, Any]]
    top_warehouses_by_throughput: List[Dict[str, Any]]
    warehouses_needing_attention: List[Dict[str, Any]]
    capacity_analysis: Dict[str, Any]
    performance_trends: List[Dict[str, Any]]


# List Response Models
class WarehouseListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[WarehouseResponse]


class WarehouseZoneListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[WarehouseZoneResponse]


class WarehouseLocationListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[WarehouseLocationResponse]


class InventoryMovementListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[InventoryMovementResponse]


class CycleCountListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[CycleCountResponse]


# Bulk Operation Models
class WarehouseBulkOperationRequest(BaseModel):
    warehouse_ids: List[str] = Field(..., min_items=1)
    operation: str = Field(
        ..., regex="^(activate|deactivate|update_status|assign_manager)$"
    )
    operation_data: Dict[str, Any] = {}


class LocationBulkOperationRequest(BaseModel):
    location_ids: List[str] = Field(..., min_items=1)
    operation: str = Field(..., regex="^(block|unblock|change_type|reassign_zone)$")
    operation_data: Dict[str, Any] = {}


# Import/Export Models
class WarehouseImportRequest(BaseModel):
    import_format: str = Field(..., regex="^(csv|json|xml|excel)$")
    data_mapping: Dict[str, str]
    import_options: Dict[str, Any] = {}
    validate_only: bool = False


class LocationImportRequest(BaseModel):
    warehouse_id: str
    import_format: str = Field(..., regex="^(csv|json|xml|excel)$")
    data_mapping: Dict[str, str]
    auto_generate_codes: bool = False
    validate_only: bool = False
