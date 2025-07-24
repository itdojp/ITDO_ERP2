from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Decimal
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    company_name = Column(String(200))
    
    # 連絡先情報
    email = Column(String(200), index=True)
    phone = Column(String(50))
    mobile = Column(String(50))
    fax = Column(String(50))
    website = Column(String(200))
    
    # 住所情報
    billing_address_line1 = Column(String(200))
    billing_address_line2 = Column(String(200))
    billing_city = Column(String(100))
    billing_state = Column(String(100))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(100), default="Japan")
    
    shipping_address_line1 = Column(String(200))
    shipping_address_line2 = Column(String(200))
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_postal_code = Column(String(20))
    shipping_country = Column(String(100), default="Japan")
    
    # サプライヤー分類
    supplier_type = Column(String(50), default="vendor")  # vendor, manufacturer, distributor
    industry = Column(String(100))
    supplier_category = Column(String(50))  # raw_materials, finished_goods, services
    priority_level = Column(String(20), default="normal")  # critical, high, normal, low
    
    # 財務情報
    credit_limit = Column(Decimal(15, 2), default=0)
    credit_balance = Column(Decimal(15, 2), default=0)
    payment_terms = Column(String(50), default="net_30")
    tax_id = Column(String(50))
    tax_exempt = Column(Boolean, default=False)
    
    # 品質・評価情報
    quality_rating = Column(Decimal(3, 2), default=0)  # 0-5.0
    delivery_rating = Column(Decimal(3, 2), default=0)  # 0-5.0
    service_rating = Column(Decimal(3, 2), default=0)  # 0-5.0
    overall_rating = Column(Decimal(3, 2), default=0)  # 0-5.0
    
    # 購買情報
    buyer_id = Column(String, ForeignKey('users.id'))
    preferred_supplier = Column(Boolean, default=False)
    certified_supplier = Column(Boolean, default=False)
    
    # 統計情報
    total_orders = Column(Integer, default=0)
    total_purchases = Column(Decimal(15, 2), default=0)
    avg_order_value = Column(Decimal(12, 2), default=0)
    last_order_date = Column(DateTime)
    
    # ステータス
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    
    # メタデータ
    notes = Column(Text)
    certifications = Column(JSON, default=[])  # ISO, quality certs
    capabilities = Column(JSON, default=[])  # manufacturing capabilities
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    buyer = relationship("User", foreign_keys=[buyer_id])
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    supplier_products = relationship("SupplierProduct", back_populates="supplier")
    purchase_requests = relationship("PurchaseRequest", back_populates="supplier")

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_number = Column(String(100), unique=True, nullable=False)
    requester_id = Column(String, ForeignKey('users.id'), nullable=False)
    department_id = Column(String, ForeignKey('departments.id'))
    supplier_id = Column(String, ForeignKey('suppliers.id'))
    
    # リクエスト情報
    request_date = Column(DateTime(timezone=True), default=func.now())
    required_date = Column(DateTime(timezone=True))
    priority = Column(String(20), default="normal")  # urgent, high, normal, low
    
    # ステータス
    status = Column(String(50), default="draft")  # draft, submitted, approved, rejected, cancelled
    approval_status = Column(String(50), default="pending")  # pending, approved, rejected
    
    # 金額情報
    estimated_total = Column(Decimal(15, 2), default=0)
    approved_budget = Column(Decimal(15, 2))
    
    # 承認情報
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # メタデータ
    justification = Column(Text)  # 購買理由
    project_code = Column(String(50))
    cost_center = Column(String(50))
    internal_notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    requester = relationship("User", foreign_keys=[requester_id])
    approver = relationship("User", foreign_keys=[approved_by])
    department = relationship("Department")
    supplier = relationship("Supplier", back_populates="purchase_requests")
    request_items = relationship("PurchaseRequestItem", back_populates="purchase_request", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="purchase_request")

class PurchaseRequestItem(Base):
    __tablename__ = "purchase_request_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_request_id = Column(String, ForeignKey('purchase_requests.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'))
    
    # 商品情報
    product_sku = Column(String(100))
    product_name = Column(String(300), nullable=False)
    product_description = Column(Text)
    specification = Column(Text)  # 詳細仕様
    
    # 数量・価格
    quantity = Column(Decimal(10, 3), nullable=False)
    estimated_unit_price = Column(Decimal(12, 2))
    estimated_total = Column(Decimal(15, 2))
    
    # 要求事項
    required_delivery_date = Column(DateTime)
    quality_requirements = Column(Text)
    preferred_brand = Column(String(100))
    
    # メタデータ
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    purchase_request = relationship("PurchaseRequest", back_populates="request_items")
    product = relationship("Product")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    po_number = Column(String(100), unique=True, nullable=False)
    purchase_request_id = Column(String, ForeignKey('purchase_requests.id'))
    supplier_id = Column(String, ForeignKey('suppliers.id'), nullable=False)
    buyer_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # 注文情報
    order_date = Column(DateTime(timezone=True), default=func.now())
    required_delivery_date = Column(DateTime)
    promised_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    
    # ステータス
    status = Column(String(50), default="draft")  # draft, sent, acknowledged, shipped, received, cancelled
    receipt_status = Column(String(50), default="pending")  # pending, partial, complete, over_received
    
    # 金額情報
    subtotal = Column(Decimal(15, 2), default=0)
    discount_amount = Column(Decimal(12, 2), default=0)
    discount_percentage = Column(Decimal(5, 2), default=0)
    tax_amount = Column(Decimal(12, 2), default=0)
    shipping_cost = Column(Decimal(10, 2), default=0)
    total_amount = Column(Decimal(15, 2), default=0)
    
    # 支払情報
    payment_terms = Column(String(50))
    payment_due_date = Column(DateTime)
    payment_status = Column(String(50), default="pending")  # pending, partial, paid, overdue
    paid_amount = Column(Decimal(15, 2), default=0)
    
    # 配送情報
    shipping_method = Column(String(100))
    shipping_address_line1 = Column(String(200))
    shipping_address_line2 = Column(String(200))
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_postal_code = Column(String(20))
    shipping_country = Column(String(100))
    
    # 品質・契約情報
    quality_requirements = Column(Text)
    contract_terms = Column(Text)
    warranty_terms = Column(Text)
    
    # メタデータ
    internal_notes = Column(Text)
    supplier_notes = Column(Text)
    project_code = Column(String(50))
    cost_center = Column(String(50))
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    supplier = relationship("Supplier", back_populates="purchase_orders")
    buyer = relationship("User", foreign_keys=[buyer_id])
    purchase_request = relationship("PurchaseRequest", back_populates="purchase_orders")
    order_items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    receipts = relationship("PurchaseReceipt", back_populates="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id = Column(String, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'))
    
    # 商品情報
    product_sku = Column(String(100))
    product_name = Column(String(300), nullable=False)
    product_description = Column(Text)
    specification = Column(Text)
    
    # 数量・価格
    quantity = Column(Decimal(10, 3), nullable=False)
    unit_price = Column(Decimal(12, 2), nullable=False)
    line_discount_amount = Column(Decimal(12, 2), default=0)
    line_discount_percentage = Column(Decimal(5, 2), default=0)
    line_total = Column(Decimal(15, 2), nullable=False)
    
    # 受領情報
    received_quantity = Column(Decimal(10, 3), default=0)
    rejected_quantity = Column(Decimal(10, 3), default=0)
    remaining_quantity = Column(Decimal(10, 3))
    
    # 品質情報
    quality_status = Column(String(50), default="pending")  # pending, passed, failed, partial
    inspection_notes = Column(Text)
    
    # メタデータ
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    purchase_order = relationship("PurchaseOrder", back_populates="order_items")
    product = relationship("Product")

class PurchaseReceipt(Base):
    __tablename__ = "purchase_receipts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    receipt_number = Column(String(100), unique=True, nullable=False)
    purchase_order_id = Column(String, ForeignKey('purchase_orders.id'), nullable=False)
    receiver_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # 受領情報
    receipt_date = Column(DateTime(timezone=True), default=func.now())
    delivery_note_number = Column(String(100))
    carrier = Column(String(100))
    
    # ステータス
    status = Column(String(50), default="received")  # received, inspected, accepted, rejected
    
    # 品質検査
    inspection_status = Column(String(50), default="pending")  # pending, passed, failed, partial
    inspector_id = Column(String, ForeignKey('users.id'))
    inspection_date = Column(DateTime)
    inspection_notes = Column(Text)
    
    # メタデータ
    notes = Column(Text)
    attachments = Column(JSON, default=[])  # 受領書、検査報告書等
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    purchase_order = relationship("PurchaseOrder", back_populates="receipts")
    receiver = relationship("User", foreign_keys=[receiver_id])
    inspector = relationship("User", foreign_keys=[inspector_id])
    receipt_items = relationship("PurchaseReceiptItem", back_populates="purchase_receipt", cascade="all, delete-orphan")

class PurchaseReceiptItem(Base):
    __tablename__ = "purchase_receipt_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_receipt_id = Column(String, ForeignKey('purchase_receipts.id'), nullable=False)
    purchase_order_item_id = Column(String, ForeignKey('purchase_order_items.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    
    # 受領数量
    received_quantity = Column(Decimal(10, 3), nullable=False)
    accepted_quantity = Column(Decimal(10, 3), default=0)
    rejected_quantity = Column(Decimal(10, 3), default=0)
    damaged_quantity = Column(Decimal(10, 3), default=0)
    
    # 品質情報
    quality_status = Column(String(50), default="pending")  # pending, passed, failed, conditional
    defect_reason = Column(Text)
    
    # 在庫情報
    warehouse_location = Column(String(100))
    lot_number = Column(String(100))
    expiry_date = Column(DateTime)
    
    # メタデータ
    serial_numbers = Column(JSON, default=[])
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    purchase_receipt = relationship("PurchaseReceipt", back_populates="receipt_items")
    purchase_order_item = relationship("PurchaseOrderItem")
    product = relationship("Product")

class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey('suppliers.id'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    
    # 商品情報
    supplier_product_code = Column(String(100))  # サプライヤー側商品コード
    supplier_product_name = Column(String(300))
    
    # 価格情報
    unit_price = Column(Decimal(12, 2))
    currency = Column(String(3), default="JPY")
    minimum_order_quantity = Column(Decimal(10, 3), default=1)
    lead_time_days = Column(Integer, default=0)
    
    # 契約情報
    contract_start_date = Column(DateTime)
    contract_end_date = Column(DateTime)
    preferred_supplier = Column(Boolean, default=False)
    
    # 品質情報
    quality_rating = Column(Decimal(3, 2), default=0)
    delivery_performance = Column(Decimal(5, 2), default=0)  # % on-time delivery
    
    # ステータス
    is_active = Column(Boolean, default=True)
    is_discontinued = Column(Boolean, default=False)
    
    # メタデータ
    notes = Column(Text)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # リレーション
    supplier = relationship("Supplier", back_populates="supplier_products")
    product = relationship("Product")