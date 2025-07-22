from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Decimal, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 住所情報
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Japan")
    
    # 連絡先
    phone = Column(String(50))
    email = Column(String(200))
    manager_id = Column(String, ForeignKey('users.id'))
    
    # 倉庫設定
    warehouse_type = Column(String(50), default="standard")  # standard, cold_storage, hazardous
    capacity_sqm = Column(Decimal(10, 2))  # 面積(㎡)
    capacity_volume = Column(Decimal(12, 3))  # 容量(m³)
    max_weight = Column(Decimal(10, 2))  # 最大重量(kg)
    
    # 位置情報
    latitude = Column(Decimal(10, 8))
    longitude = Column(Decimal(11, 8))
    
    # 営業時間
    operating_hours = Column(JSON, default={})  # {"mon": "9:00-17:00", ...}
    timezone = Column(String(50), default="Asia/Tokyo")
    
    # ステータス
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # メタデータ
    settings = Column(JSON, default={})
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    manager = relationship("User", foreign_keys=[manager_id])
    inventory_items = relationship("InventoryItem", back_populates="warehouse")
    locations = relationship("WarehouseLocation", back_populates="warehouse")

class WarehouseLocation(Base):
    __tablename__ = "warehouse_locations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(200))
    description = Column(Text)
    
    # 位置情報
    zone = Column(String(10))      # A, B, C
    aisle = Column(String(10))     # 01, 02, 03
    rack = Column(String(10))      # A, B, C
    level = Column(String(10))     # 1, 2, 3
    position = Column(String(10))  # 1, 2, 3
    
    # 容量情報
    max_capacity = Column(Integer, default=0)
    current_capacity = Column(Integer, default=0)
    max_weight = Column(Decimal(10, 2))
    
    # 設定
    location_type = Column(String(50), default="storage")  # storage, picking, receiving, shipping
    is_active = Column(Boolean, default=True)
    
    # メタデータ
    attributes = Column(JSON, default={})
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    warehouse = relationship("Warehouse", back_populates="locations")
    inventory_items = relationship("InventoryItem", back_populates="location")

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    location_id = Column(String, ForeignKey('warehouse_locations.id'))
    
    # 在庫数量
    quantity_available = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)
    quantity_allocated = Column(Integer, default=0)
    quantity_on_order = Column(Integer, default=0)
    quantity_in_transit = Column(Integer, default=0)
    
    # バッチ・シリアル管理
    batch_number = Column(String(100))
    serial_numbers = Column(JSON, default=[])  # シリアル番号リスト
    lot_number = Column(String(100))
    expiry_date = Column(DateTime)
    manufacturing_date = Column(DateTime)
    
    # コスト情報
    unit_cost = Column(Decimal(12, 4))
    average_cost = Column(Decimal(12, 4))
    fifo_cost = Column(Decimal(12, 4))
    lifo_cost = Column(Decimal(12, 4))
    
    # 品質情報
    quality_status = Column(String(50), default="good")  # good, damaged, expired, quarantine
    quality_notes = Column(Text)
    last_inspection_date = Column(DateTime)
    next_inspection_date = Column(DateTime)
    
    # 最適化情報
    reorder_point = Column(Integer, default=0)
    max_stock_level = Column(Integer)
    safety_stock = Column(Integer, default=0)
    economic_order_qty = Column(Integer)
    
    # 活動履歴
    last_movement_date = Column(DateTime)
    last_count_date = Column(DateTime)
    last_sale_date = Column(DateTime)
    
    # ステータス
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)  # 移動禁止
    
    # メタデータ
    attributes = Column(JSON, default={})
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    product = relationship("Product")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    location = relationship("WarehouseLocation", back_populates="inventory_items")
    movements = relationship("StockMovement", back_populates="inventory_item")
    reservations = relationship("InventoryReservation", back_populates="inventory_item")

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_item_id = Column(String, ForeignKey('inventory_items.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    
    # 移動情報
    movement_type = Column(String(50), nullable=False)  # inbound, outbound, adjustment, transfer
    transaction_type = Column(String(50))  # purchase, sale, adjustment, cycle_count, transfer
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Decimal(12, 4))
    total_cost = Column(Decimal(15, 2))
    
    # 移動前後の在庫
    stock_before = Column(Integer, default=0)
    stock_after = Column(Integer, default=0)
    
    # 移動元・先
    from_warehouse_id = Column(String, ForeignKey('warehouses.id'))
    to_warehouse_id = Column(String, ForeignKey('warehouses.id'))
    from_location_id = Column(String, ForeignKey('warehouse_locations.id'))
    to_location_id = Column(String, ForeignKey('warehouse_locations.id'))
    
    # 参照情報
    reference_type = Column(String(50))  # purchase_order, sales_order, transfer_order
    reference_id = Column(String(100))
    reference_line_id = Column(String(100))
    
    # 承認・作業情報
    requested_by = Column(String, ForeignKey('users.id'))
    approved_by = Column(String, ForeignKey('users.id'))
    executed_by = Column(String, ForeignKey('users.id'))
    
    # 日付情報
    movement_date = Column(DateTime(timezone=True), nullable=False)
    requested_date = Column(DateTime(timezone=True))
    approved_date = Column(DateTime(timezone=True))
    executed_date = Column(DateTime(timezone=True))
    
    # ステータス
    status = Column(String(50), default="pending")  # pending, approved, executed, cancelled
    
    # 理由・ノート
    reason = Column(String(200))
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    inventory_item = relationship("InventoryItem", back_populates="movements")
    product = relationship("Product")
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id])
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id])
    from_location = relationship("WarehouseLocation", foreign_keys=[from_location_id])
    to_location = relationship("WarehouseLocation", foreign_keys=[to_location_id])
    requested_by_user = relationship("User", foreign_keys=[requested_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    executed_by_user = relationship("User", foreign_keys=[executed_by])

class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_item_id = Column(String, ForeignKey('inventory_items.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    
    # 予約情報
    quantity_reserved = Column(Integer, nullable=False)
    reservation_type = Column(String(50), default="sales_order")  # sales_order, transfer, maintenance
    
    # 参照情報
    reference_type = Column(String(50))
    reference_id = Column(String(100))
    reference_line_id = Column(String(100))
    
    # 日付情報
    reserved_date = Column(DateTime(timezone=True), nullable=False)
    expected_release_date = Column(DateTime(timezone=True))
    actual_release_date = Column(DateTime(timezone=True))
    
    # 予約者情報
    reserved_by = Column(String, ForeignKey('users.id'))
    released_by = Column(String, ForeignKey('users.id'))
    
    # ステータス
    status = Column(String(50), default="active")  # active, released, expired, cancelled
    
    # ノート
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    inventory_item = relationship("InventoryItem", back_populates="reservations")
    product = relationship("Product")
    reserved_by_user = relationship("User", foreign_keys=[reserved_by])
    released_by_user = relationship("User", foreign_keys=[released_by])

class CycleCount(Base):
    __tablename__ = "cycle_counts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_count_number = Column(String(100), unique=True, nullable=False)
    
    # カウント情報
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    location_id = Column(String, ForeignKey('warehouse_locations.id'))
    count_type = Column(String(50), default="full")  # full, partial, abc_analysis
    
    # 計画日付
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    start_date = Column(DateTime(timezone=True))
    completion_date = Column(DateTime(timezone=True))
    
    # 担当者
    assigned_to = Column(String, ForeignKey('users.id'))
    supervised_by = Column(String, ForeignKey('users.id'))
    
    # ステータス
    status = Column(String(50), default="planned")  # planned, in_progress, completed, cancelled
    
    # 結果サマリー
    total_items_planned = Column(Integer, default=0)
    total_items_counted = Column(Integer, default=0)
    total_discrepancies = Column(Integer, default=0)
    accuracy_percentage = Column(Decimal(5, 2))
    
    # ノート
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    supervisor = relationship("User", foreign_keys=[supervised_by])
    count_items = relationship("CycleCountItem", back_populates="cycle_count")

class CycleCountItem(Base):
    __tablename__ = "cycle_count_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cycle_count_id = Column(String, ForeignKey('cycle_counts.id'), nullable=False)
    inventory_item_id = Column(String, ForeignKey('inventory_items.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    
    # カウント数量
    system_quantity = Column(Integer, nullable=False)
    counted_quantity = Column(Integer)
    variance_quantity = Column(Integer, default=0)
    variance_value = Column(Decimal(12, 2))
    
    # カウント情報
    count_date = Column(DateTime(timezone=True))
    counted_by = Column(String, ForeignKey('users.id'))
    recounted_by = Column(String, ForeignKey('users.id'))
    
    # ステータス
    status = Column(String(50), default="pending")  # pending, counted, verified, adjusted
    requires_recount = Column(Boolean, default=False)
    
    # 調整情報
    adjustment_applied = Column(Boolean, default=False)
    adjustment_reason = Column(String(200))
    
    # ノート
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    cycle_count = relationship("CycleCount", back_populates="count_items")
    inventory_item = relationship("InventoryItem")
    product = relationship("Product")
    counted_by_user = relationship("User", foreign_keys=[counted_by])
    recounted_by_user = relationship("User", foreign_keys=[recounted_by])

class StockAlert(Base):
    __tablename__ = "stock_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(String, ForeignKey('warehouses.id'), nullable=False)
    
    # アラート情報
    alert_type = Column(String(50), nullable=False)  # low_stock, out_of_stock, overstock, expiry
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    
    # 在庫情報
    current_quantity = Column(Integer, nullable=False)
    threshold_quantity = Column(Integer)
    recommended_order_quantity = Column(Integer)
    
    # ステータス
    status = Column(String(50), default="active")  # active, acknowledged, resolved, dismissed
    acknowledged_by = Column(String, ForeignKey('users.id'))
    acknowledged_date = Column(DateTime(timezone=True))
    resolved_date = Column(DateTime(timezone=True))
    
    # メッセージ
    message = Column(Text, nullable=False)
    resolution_notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    product = relationship("Product")
    warehouse = relationship("Warehouse")
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by])