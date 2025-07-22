from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Decimal, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本情報
    warehouse_code = Column(String(50), unique=True, nullable=False)
    warehouse_name = Column(String(200), nullable=False)
    warehouse_type = Column(String(50), default="distribution")  # distribution, manufacturing, retail, cross_dock, 3pl
    
    # 所在地・連絡先
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2), default="JP")  # ISO country code
    
    # 連絡先情報
    phone = Column(String(50))
    fax = Column(String(50))
    email = Column(String(200))
    
    # 地理的情報
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String(50), default="Asia/Tokyo")
    
    # 物理的仕様
    total_area = Column(Decimal(12, 2))  # Total area in square meters
    storage_area = Column(Decimal(12, 2))  # Usable storage area
    office_area = Column(Decimal(12, 2))  # Office space
    loading_dock_count = Column(Integer, default=0)
    ceiling_height = Column(Decimal(6, 2))  # Height in meters
    floor_load_capacity = Column(Decimal(10, 2))  # kg per square meter
    
    # 環境制御
    climate_controlled = Column(Boolean, default=False)
    temperature_min = Column(Decimal(6, 2))  # Minimum temperature in Celsius
    temperature_max = Column(Decimal(6, 2))  # Maximum temperature in Celsius
    humidity_controlled = Column(Boolean, default=False)
    humidity_min = Column(Decimal(5, 2))  # Minimum humidity percentage
    humidity_max = Column(Decimal(5, 2))  # Maximum humidity percentage
    
    # 運用情報
    operating_hours_start = Column(String(10))  # "08:00"
    operating_hours_end = Column(String(10))  # "17:00"
    operating_days = Column(JSON, default=["mon", "tue", "wed", "thu", "fri"])  # Days of operation
    shift_pattern = Column(String(50), default="single")  # single, double, continuous
    
    # 管理・権限
    warehouse_manager_id = Column(String, ForeignKey('users.id'))
    supervisor_ids = Column(JSON, default=[])  # List of supervisor user IDs
    organization_id = Column(String, ForeignKey('organizations.id'))
    cost_center_code = Column(String(50))
    
    # 機能・能力
    receiving_capacity = Column(Integer, default=0)  # Orders per day
    shipping_capacity = Column(Integer, default=0)  # Orders per day
    storage_systems = Column(JSON, default=[])  # ["pallet_rack", "shelf", "floor", "bulk"]
    handling_equipment = Column(JSON, default=[])  # ["forklift", "conveyor", "crane"]
    
    # セキュリティ・コンプライアンス
    security_level = Column(String(20), default="standard")  # basic, standard, high, maximum
    access_control_system = Column(Boolean, default=False)
    camera_surveillance = Column(Boolean, default=False)
    fire_suppression_system = Column(String(50))  # sprinkler, gas, foam
    security_certifications = Column(JSON, default=[])  # ISO certifications, security standards
    
    # 自動化・テクノロジー
    wms_system = Column(String(100))  # Warehouse Management System
    automation_level = Column(String(30), default="manual")  # manual, semi_automated, automated
    barcode_scanning = Column(Boolean, default=True)
    rfid_enabled = Column(Boolean, default=False)
    voice_picking = Column(Boolean, default=False)
    automated_sorting = Column(Boolean, default=False)
    
    # 統合・連携
    erp_integration = Column(Boolean, default=True)
    tms_integration = Column(Boolean, default=False)  # Transportation Management System
    customs_bonded = Column(Boolean, default=False)  # Customs bonded warehouse
    free_trade_zone = Column(Boolean, default=False)
    
    # パフォーマンス指標
    utilization_target = Column(Decimal(5, 2), default=85)  # Target utilization percentage
    current_utilization = Column(Decimal(5, 2), default=0)  # Current utilization
    accuracy_target = Column(Decimal(5, 2), default=99.5)  # Inventory accuracy target
    current_accuracy = Column(Decimal(5, 2))  # Current inventory accuracy
    
    # 費用・予算
    annual_operating_cost = Column(Decimal(15, 2))
    lease_cost_per_month = Column(Decimal(12, 2))
    labor_cost_per_hour = Column(Decimal(8, 2))
    
    # ステータス・制御
    status = Column(String(20), default="active")  # active, inactive, maintenance, closed
    is_default = Column(Boolean, default=False)
    allow_negative_inventory = Column(Boolean, default=False)
    require_lot_tracking = Column(Boolean, default=False)
    require_serial_tracking = Column(Boolean, default=False)
    
    # 通知・アラート設定
    low_space_alert_threshold = Column(Decimal(5, 2), default=90)  # Alert when X% full
    high_temperature_alert = Column(Boolean, default=False)
    security_breach_alert = Column(Boolean, default=True)
    
    # メタデータ・カスタム
    tags = Column(JSON, default=[])
    custom_fields = Column(JSON, default={})
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    updated_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    manager = relationship("User", foreign_keys=[warehouse_manager_id])
    organization = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    zones = relationship("WarehouseZone", back_populates="warehouse", cascade="all, delete-orphan")
    locations = relationship("WarehouseLocation", back_populates="warehouse", cascade="all, delete-orphan")
    movements = relationship("InventoryMovement", back_populates="warehouse")
    cycle_counts = relationship("CycleCount", back_populates="warehouse", cascade="all, delete-orphan")


class WarehouseZone(Base):
    __tablename__ = "warehouse_zones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    
    # ゾーン基本情報
    zone_code = Column(String(50), nullable=False)
    zone_name = Column(String(200), nullable=False)
    zone_type = Column(String(50), default="storage")  # storage, receiving, shipping, staging, quality_control
    
    # 物理的仕様
    area = Column(Decimal(10, 2))  # Area in square meters
    height = Column(Decimal(6, 2))  # Height in meters
    volume = Column(Decimal(12, 3))  # Volume in cubic meters
    
    # 位置・配置
    floor_level = Column(Integer, default=1)
    grid_coordinates = Column(String(20))  # "A1-B5" format
    
    # 環境・制約条件
    temperature_controlled = Column(Boolean, default=False)
    min_temperature = Column(Decimal(6, 2))
    max_temperature = Column(Decimal(6, 2))
    humidity_controlled = Column(Boolean, default=False)
    hazmat_approved = Column(Boolean, default=False)
    security_level = Column(String(20), default="standard")
    
    # 機能・用途設定
    picking_zone = Column(Boolean, default=True)
    replenishment_zone = Column(Boolean, default=False)
    quarantine_zone = Column(Boolean, default=False)
    fast_moving_items = Column(Boolean, default=False)
    slow_moving_items = Column(Boolean, default=False)
    
    # 制約・ルール
    max_weight_capacity = Column(Decimal(12, 2))  # Maximum weight in kg
    allowed_product_categories = Column(JSON, default=[])
    prohibited_product_categories = Column(JSON, default=[])
    storage_rules = Column(JSON, default={})  # Custom storage rules
    
    # アクセス・セキュリティ
    restricted_access = Column(Boolean, default=False)
    authorized_personnel = Column(JSON, default=[])  # User IDs with access
    access_equipment_required = Column(JSON, default=[])  # Required equipment/credentials
    
    # 統計・パフォーマンス
    current_utilization = Column(Decimal(5, 2), default=0)
    max_utilization_target = Column(Decimal(5, 2), default=85)
    location_count = Column(Integer, default=0)
    occupied_locations = Column(Integer, default=0)
    
    # ステータス
    status = Column(String(20), default="active")  # active, inactive, maintenance, blocked
    last_inventory_date = Column(DateTime)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    warehouse = relationship("Warehouse", back_populates="zones")
    locations = relationship("WarehouseLocation", back_populates="zone", cascade="all, delete-orphan")
    creator = relationship("User")


class WarehouseLocation(Base):
    __tablename__ = "warehouse_locations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    zone_id = Column(String, ForeignKey('warehouse_zones.id'), nullable=False)
    
    # ロケーション識別
    location_code = Column(String(50), nullable=False)
    barcode = Column(String(100))  # Barcode for scanning
    qr_code = Column(String(200))  # QR code data
    
    # 物理的仕様
    location_type = Column(String(50), default="bin")  # bin, shelf, pallet, floor, bulk
    length = Column(Decimal(6, 2))  # Length in meters
    width = Column(Decimal(6, 2))  # Width in meters
    height = Column(Decimal(6, 2))  # Height in meters
    volume = Column(Decimal(10, 3))  # Volume in cubic meters
    weight_capacity = Column(Decimal(10, 2))  # Weight capacity in kg
    
    # 座標・配置
    aisle = Column(String(10))
    bay = Column(String(10))
    level = Column(String(10))
    position = Column(String(10))
    coordinates = Column(String(50))  # "A1-2-3" format (Aisle-Bay-Level)
    
    # 機能・特性
    pickable = Column(Boolean, default=True)
    replenishable = Column(Boolean, default=True)
    mix_products_allowed = Column(Boolean, default=False)  # Allow multiple SKUs
    mix_lots_allowed = Column(Boolean, default=False)  # Allow multiple lots
    
    # 制約・ルール
    product_restrictions = Column(JSON, default=[])  # Allowed/prohibited product types
    temperature_requirements = Column(JSON, default={})  # Min/max temperature
    handling_requirements = Column(JSON, default=[])  # Special handling needs
    
    # アクセス・装備
    access_method = Column(String(30), default="manual")  # manual, forklift, crane, automated
    equipment_required = Column(JSON, default=[])  # Required equipment for access
    pick_priority = Column(Integer, default=50)  # 1-100, higher = higher priority
    
    # 在庫・占有状況
    is_occupied = Column(Boolean, default=False)
    current_stock_quantity = Column(Decimal(15, 3), default=0)
    current_weight = Column(Decimal(10, 2), default=0)
    occupancy_percentage = Column(Decimal(5, 2), default=0)
    
    # 商品・在庫関連
    primary_product_id = Column(String, ForeignKey('products.id'))  # Primary product if single-SKU
    lot_number = Column(String(100))  # If lot-controlled
    expiration_date = Column(DateTime)  # If expiry-controlled
    
    # 運用・メンテナンス
    last_pick_date = Column(DateTime)
    last_replenish_date = Column(DateTime)
    last_count_date = Column(DateTime)
    pick_frequency = Column(Integer, default=0)  # Picks per period
    
    # ステータス・制御
    status = Column(String(20), default="available")  # available, occupied, blocked, damaged, maintenance
    blocked_reason = Column(String(200))  # Reason if blocked
    priority_sequence = Column(Integer, default=0)  # Pick sequence within zone
    
    # 品質・安全
    last_inspection_date = Column(DateTime)
    cleanliness_rating = Column(Integer)  # 1-5 rating
    damage_assessment = Column(String(500))
    
    # カスタム・メタデータ
    location_attributes = Column(JSON, default={})  # Custom attributes
    tags = Column(JSON, default=[])
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    warehouse = relationship("Warehouse", back_populates="locations")
    zone = relationship("WarehouseZone", back_populates="locations")
    primary_product = relationship("Product")
    creator = relationship("User")
    inventory_items = relationship("InventoryItem", back_populates="location")
    movements = relationship("InventoryMovement", back_populates="location")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    location_id = Column(String, ForeignKey('warehouse_locations.id'))
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    
    # 移動基本情報
    movement_type = Column(String(30), nullable=False)  # receipt, shipment, adjustment, transfer, cycle_count
    movement_subtype = Column(String(50))  # purchase_receipt, sales_shipment, internal_transfer, etc.
    reference_number = Column(String(100))  # PO, SO, Transfer order number
    reference_line = Column(Integer)  # Line number in reference document
    
    # 数量・単位
    quantity = Column(Decimal(15, 3), nullable=False)  # Movement quantity
    unit_of_measure = Column(String(20), nullable=False)
    cost_per_unit = Column(Decimal(12, 4))  # Unit cost
    total_cost = Column(Decimal(15, 2))  # Total movement cost
    
    # ロット・シリアル管理
    lot_number = Column(String(100))
    serial_numbers = Column(JSON, default=[])  # Array of serial numbers
    expiration_date = Column(DateTime)
    manufacture_date = Column(DateTime)
    
    # 移動詳細
    from_location_id = Column(String, ForeignKey('warehouse_locations.id'))  # Source location
    to_location_id = Column(String, ForeignKey('warehouse_locations.id'))  # Destination location
    from_warehouse_id = Column(String, ForeignKey('warehouses.id'))  # Source warehouse
    to_warehouse_id = Column(String, ForeignKey('warehouses.id'))  # Destination warehouse
    
    # 実行情報
    planned_date = Column(DateTime)  # Planned movement date
    actual_date = Column(DateTime)  # Actual movement date
    performed_by = Column(String, ForeignKey('users.id'))  # Who performed the movement
    approved_by = Column(String, ForeignKey('users.id'))  # Who approved the movement
    
    # 理由・背景
    reason_code = Column(String(50))  # Standardized reason codes
    reason_description = Column(Text)
    business_process = Column(String(100))  # Related business process
    
    # 品質・検査
    quality_status = Column(String(30), default="approved")  # approved, rejected, quarantine, pending
    inspection_required = Column(Boolean, default=False)
    inspector_id = Column(String, ForeignKey('users.id'))
    inspection_date = Column(DateTime)
    inspection_notes = Column(Text)
    
    # 運送・物流
    carrier = Column(String(200))
    tracking_number = Column(String(100))
    freight_cost = Column(Decimal(10, 2))
    delivery_method = Column(String(50))
    
    # 税務・会計
    tax_amount = Column(Decimal(10, 2))
    duty_amount = Column(Decimal(10, 2))
    accounting_period = Column(String(20))  # YYYY-MM format
    cost_center = Column(String(50))
    
    # システム・統合
    source_system = Column(String(100))  # System that generated the movement
    integration_batch_id = Column(String(100))
    sync_status = Column(String(20), default="pending")  # pending, synced, error
    
    # エラー・例外処理
    error_messages = Column(JSON, default=[])
    retry_count = Column(Integer, default=0)
    
    # ステータス・制御
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled, error
    is_reversed = Column(Boolean, default=False)  # If movement was reversed
    reversal_movement_id = Column(String, ForeignKey('inventory_movements.id'))  # Reference to reversal
    
    # 影響・結果
    inventory_impact = Column(Decimal(15, 3))  # Net impact on inventory (+/-)
    value_impact = Column(Decimal(15, 2))  # Net impact on inventory value
    
    # メタデータ
    custom_fields = Column(JSON, default={})
    tags = Column(JSON, default=[])
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    warehouse = relationship("Warehouse", back_populates="movements")
    location = relationship("WarehouseLocation", foreign_keys=[location_id], back_populates="movements")
    from_location = relationship("WarehouseLocation", foreign_keys=[from_location_id])
    to_location = relationship("WarehouseLocation", foreign_keys=[to_location_id])
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    product = relationship("Product")
    performer = relationship("User", foreign_keys=[performed_by])
    approver = relationship("User", foreign_keys=[approved_by])
    inspector = relationship("User", foreign_keys=[inspector_id])
    reversal_movement = relationship("InventoryMovement", foreign_keys=[reversal_movement_id], remote_side=[id])
    creator = relationship("User", foreign_keys=[created_by])


class CycleCount(Base):
    __tablename__ = "cycle_counts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    
    # 棚卸基本情報
    count_number = Column(String(50), unique=True, nullable=False)
    count_name = Column(String(200), nullable=False)
    count_type = Column(String(30), default="cycle")  # cycle, full, spot, exception
    
    # 範囲・対象
    count_scope = Column(String(30), default="zone")  # zone, location, product, category, all
    zone_ids = Column(JSON, default=[])  # Target zones
    location_ids = Column(JSON, default=[])  # Target locations
    product_ids = Column(JSON, default=[])  # Target products
    category_ids = Column(JSON, default=[])  # Target categories
    
    # 日程・実行
    planned_date = Column(DateTime, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    cutoff_time = Column(DateTime)  # Inventory cutoff time
    
    # 担当・責任
    count_manager_id = Column(String, ForeignKey('users.id'))
    assigned_counters = Column(JSON, default=[])  # User IDs of assigned counters
    supervisor_id = Column(String, ForeignKey('users.id'))
    
    # 設定・ルール
    count_method = Column(String(30), default="manual")  # manual, scanner, rfid
    recount_required = Column(Boolean, default=True)
    tolerance_percentage = Column(Decimal(5, 2), default=2.0)  # Variance tolerance
    minimum_count_value = Column(Decimal(12, 2))  # Only count items above this value
    exclude_zero_quantities = Column(Boolean, default=False)
    
    # ステータス・進捗
    status = Column(String(30), default="planned")  # planned, in_progress, completed, cancelled, on_hold
    completion_percentage = Column(Decimal(5, 2), default=0)
    total_locations_planned = Column(Integer, default=0)
    locations_counted = Column(Integer, default=0)
    locations_remaining = Column(Integer, default=0)
    
    # 結果・統計
    total_items_counted = Column(Integer, default=0)
    items_with_variance = Column(Integer, default=0)
    total_variance_value = Column(Decimal(15, 2), default=0)
    accuracy_percentage = Column(Decimal(5, 2))
    
    # 承認・確定
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    
    # システム・統合
    freeze_inventory = Column(Boolean, default=True)  # Freeze inventory during count
    auto_adjust = Column(Boolean, default=False)  # Auto-adjust variances within tolerance
    generate_adjustments = Column(Boolean, default=True)  # Generate adjustment movements
    
    # メタデータ
    instructions = Column(Text)  # Special instructions for counters
    notes = Column(Text)
    tags = Column(JSON, default=[])
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    warehouse = relationship("Warehouse", back_populates="cycle_counts")
    count_manager = relationship("User", foreign_keys=[count_manager_id])
    supervisor = relationship("User", foreign_keys=[supervisor_id])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
    count_lines = relationship("CycleCountLine", back_populates="cycle_count", cascade="all, delete-orphan")


class CycleCountLine(Base):
    __tablename__ = "cycle_count_lines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_count_id = Column(String, ForeignKey('cycle_counts.id'), nullable=False)
    location_id = Column(String, ForeignKey('warehouse_locations.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    
    # 在庫情報
    lot_number = Column(String(100))
    serial_numbers = Column(JSON, default=[])
    expiration_date = Column(DateTime)
    
    # 帳簿・実数
    book_quantity = Column(Decimal(15, 3), default=0)  # System/book quantity
    counted_quantity = Column(Decimal(15, 3))  # First count quantity
    recount_quantity = Column(Decimal(15, 3))  # Recount quantity if applicable
    final_quantity = Column(Decimal(15, 3))  # Final accepted quantity
    
    # 差異・調整
    variance_quantity = Column(Decimal(15, 3), default=0)  # Difference
    variance_percentage = Column(Decimal(8, 4), default=0)  # Percentage difference
    variance_value = Column(Decimal(12, 2), default=0)  # Value of variance
    unit_cost = Column(Decimal(12, 4))  # Unit cost for valuation
    
    # カウント詳細
    count_date = Column(DateTime)
    counter_id = Column(String, ForeignKey('users.id'))  # Who counted
    recount_date = Column(DateTime)
    recounter_id = Column(String, ForeignKey('users.id'))  # Who recounted
    count_method = Column(String(30))  # manual, scanner, rfid
    
    # ステータス・制御
    count_status = Column(String(30), default="pending")  # pending, counted, recounted, approved, adjusted
    requires_recount = Column(Boolean, default=False)
    recount_reason = Column(String(200))
    
    # 品質・検証
    verified_by = Column(String, ForeignKey('users.id'))
    verification_date = Column(DateTime)
    variance_approved_by = Column(String, ForeignKey('users.id'))
    variance_approval_date = Column(DateTime)
    
    # 調整処理
    adjustment_created = Column(Boolean, default=False)
    adjustment_movement_id = Column(String, ForeignKey('inventory_movements.id'))
    
    # エラー・例外
    count_issues = Column(JSON, default=[])  # Array of issues encountered
    resolution_notes = Column(Text)
    
    # メタデータ
    notes = Column(Text)
    tags = Column(JSON, default=[])
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    cycle_count = relationship("CycleCount", back_populates="count_lines")
    location = relationship("WarehouseLocation")
    product = relationship("Product")
    counter = relationship("User", foreign_keys=[counter_id])
    recounter = relationship("User", foreign_keys=[recounter_id])
    verifier = relationship("User", foreign_keys=[verified_by])
    variance_approver = relationship("User", foreign_keys=[variance_approved_by])
    adjustment_movement = relationship("InventoryMovement")


class WarehousePerformance(Base):
    __tablename__ = "warehouse_performance"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    
    # 期間情報
    performance_period = Column(String(20), nullable=False)  # YYYY-MM or YYYY-Wxx format
    period_type = Column(String(20), default="monthly")  # daily, weekly, monthly, quarterly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # 受取・入荷実績
    receipts_planned = Column(Integer, default=0)
    receipts_actual = Column(Integer, default=0)
    receipt_accuracy = Column(Decimal(5, 2))  # Percentage
    receipt_timeliness = Column(Decimal(5, 2))  # On-time percentage
    average_receipt_time = Column(Decimal(8, 2))  # Hours
    
    # 出荷・発送実績
    shipments_planned = Column(Integer, default=0)
    shipments_actual = Column(Integer, default=0)
    shipment_accuracy = Column(Decimal(5, 2))  # Percentage
    shipment_timeliness = Column(Decimal(5, 2))  # On-time percentage
    average_shipment_time = Column(Decimal(8, 2))  # Hours
    
    # ピッキング・処理実績
    orders_processed = Column(Integer, default=0)
    lines_picked = Column(Integer, default=0)
    pick_accuracy = Column(Decimal(5, 2))  # Percentage
    picks_per_hour = Column(Decimal(8, 2))  # Productivity metric
    
    # 在庫精度・管理
    inventory_accuracy = Column(Decimal(5, 2))  # Cycle count accuracy
    stock_adjustments_count = Column(Integer, default=0)
    stock_adjustments_value = Column(Decimal(15, 2), default=0)
    stockouts_count = Column(Integer, default=0)
    
    # 容量・利用率
    storage_utilization = Column(Decimal(5, 2))  # Space utilization percentage
    dock_utilization = Column(Decimal(5, 2))  # Loading dock utilization
    equipment_utilization = Column(Decimal(5, 2))  # Equipment utilization
    
    # 品質・損害
    damage_incidents = Column(Integer, default=0)
    damage_value = Column(Decimal(12, 2), default=0)
    quality_holds = Column(Integer, default=0)
    returns_processed = Column(Integer, default=0)
    
    # 人員・労働
    total_labor_hours = Column(Decimal(10, 2), default=0)
    overtime_hours = Column(Decimal(8, 2), default=0)
    staff_count_average = Column(Decimal(6, 2))
    labor_cost_total = Column(Decimal(12, 2), default=0)
    
    # 安全・コンプライアンス
    safety_incidents = Column(Integer, default=0)
    near_misses = Column(Integer, default=0)
    compliance_violations = Column(Integer, default=0)
    training_hours = Column(Decimal(8, 2), default=0)
    
    # コスト・財務
    operating_cost_total = Column(Decimal(15, 2), default=0)
    cost_per_shipment = Column(Decimal(10, 2))
    cost_per_receipt = Column(Decimal(10, 2))
    cost_per_pick = Column(Decimal(8, 2))
    
    # 顧客・サービス
    order_fulfillment_rate = Column(Decimal(5, 2))  # Orders fulfilled completely
    customer_complaints = Column(Integer, default=0)
    service_level_achievement = Column(Decimal(5, 2))
    
    # 自動化・テクノロジー
    automation_uptime = Column(Decimal(5, 2))  # Percentage
    system_downtime_hours = Column(Decimal(6, 2), default=0)
    barcode_scan_accuracy = Column(Decimal(5, 2))
    
    # 環境・持続可能性
    energy_consumption = Column(Decimal(12, 2))  # kWh
    waste_generated = Column(Decimal(10, 2))  # kg
    recycling_rate = Column(Decimal(5, 2))  # Percentage
    carbon_footprint = Column(Decimal(12, 2))  # CO2 equivalent
    
    # 集計・計算情報
    calculation_date = Column(DateTime)
    calculated_by = Column(String, ForeignKey('users.id'))
    data_quality_score = Column(Decimal(5, 2))  # Quality of underlying data
    
    # ベンチマーク・目標
    performance_vs_target = Column(JSON, default={})  # KPI vs target comparison
    benchmark_comparison = Column(JSON, default={})  # Industry benchmark comparison
    
    # メタデータ
    notes = Column(Text)
    tags = Column(JSON, default=[])
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    warehouse = relationship("Warehouse")
    calculator = relationship("User", foreign_keys=[calculated_by])