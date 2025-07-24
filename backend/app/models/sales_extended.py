import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Decimal,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_code = Column(String(50), unique=True, nullable=False)
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

    # 顧客分類
    customer_type = Column(String(50), default="individual")  # individual, business
    industry = Column(String(100))
    customer_group = Column(String(50), default="standard")
    priority_level = Column(String(20), default="normal")  # high, normal, low

    # 財務情報
    credit_limit = Column(Decimal(15, 2), default=0)
    credit_balance = Column(Decimal(15, 2), default=0)
    payment_terms = Column(String(50), default="net_30")
    tax_id = Column(String(50))
    tax_exempt = Column(Boolean, default=False)

    # 営業情報
    sales_rep_id = Column(String, ForeignKey("users.id"))
    acquisition_source = Column(String(100))
    acquisition_date = Column(DateTime)

    # 統計情報
    total_orders = Column(Integer, default=0)
    total_sales = Column(Decimal(15, 2), default=0)
    avg_order_value = Column(Decimal(12, 2), default=0)
    last_order_date = Column(DateTime)

    # ステータス
    is_active = Column(Boolean, default=True)
    is_vip = Column(Boolean, default=False)

    # メタデータ
    notes = Column(Text)
    preferences = Column(JSON, default={})

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])
    sales_orders = relationship("SalesOrder", back_populates="customer")
    quotes = relationship("Quote", back_populates="customer")


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(100), unique=True, nullable=False)
    quote_id = Column(String, ForeignKey("quotes.id"))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)

    # 注文情報
    order_date = Column(DateTime(timezone=True), default=func.now())
    requested_delivery_date = Column(DateTime)
    promised_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)

    # ステータス
    status = Column(
        String(50), default="draft"
    )  # draft, confirmed, processing, shipped, delivered, cancelled
    priority = Column(String(20), default="normal")  # high, normal, low

    # 金額情報
    subtotal = Column(Decimal(15, 2), default=0)
    discount_amount = Column(Decimal(12, 2), default=0)
    discount_percentage = Column(Decimal(5, 2), default=0)
    tax_amount = Column(Decimal(12, 2), default=0)
    shipping_cost = Column(Decimal(10, 2), default=0)
    total_amount = Column(Decimal(15, 2), default=0)

    # 支払情報
    payment_status = Column(
        String(50), default="pending"
    )  # pending, partial, paid, overdue
    payment_terms = Column(String(50))
    payment_due_date = Column(DateTime)
    paid_amount = Column(Decimal(15, 2), default=0)

    # 配送情報
    shipping_method = Column(String(100))
    shipping_address_line1 = Column(String(200))
    shipping_address_line2 = Column(String(200))
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_postal_code = Column(String(20))
    shipping_country = Column(String(100))
    tracking_number = Column(String(100))

    # 営業情報
    sales_rep_id = Column(String, ForeignKey("users.id"))
    sales_channel = Column(String(50), default="direct")  # direct, online, partner
    referral_source = Column(String(100))

    # メタデータ
    internal_notes = Column(Text)
    customer_notes = Column(Text)
    custom_fields = Column(JSON, default={})

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    customer = relationship("Customer", back_populates="sales_orders")
    quote = relationship("Quote", back_populates="sales_orders")
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])
    order_items = relationship(
        "SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan"
    )
    invoices = relationship("Invoice", back_populates="sales_order")
    shipments = relationship("Shipment", back_populates="sales_order")


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_order_id = Column(String, ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    # 商品情報
    product_sku = Column(String(100))
    product_name = Column(String(300))
    product_description = Column(Text)

    # 数量・価格
    quantity = Column(Decimal(10, 3), nullable=False)
    unit_price = Column(Decimal(12, 2), nullable=False)
    line_discount_amount = Column(Decimal(12, 2), default=0)
    line_discount_percentage = Column(Decimal(5, 2), default=0)
    line_total = Column(Decimal(15, 2), nullable=False)

    # 在庫・配送
    reserved_inventory_id = Column(String)
    shipped_quantity = Column(Decimal(10, 3), default=0)
    delivered_quantity = Column(Decimal(10, 3), default=0)

    # ステータス
    item_status = Column(
        String(50), default="pending"
    )  # pending, reserved, shipped, delivered, cancelled

    # メタデータ
    custom_attributes = Column(JSON, default={})
    notes = Column(Text)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    sales_order = relationship("SalesOrder", back_populates="order_items")
    product = relationship("Product")


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_number = Column(String(100), unique=True, nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)

    # 見積情報
    quote_date = Column(DateTime(timezone=True), default=func.now())
    valid_until = Column(DateTime(timezone=True))

    # ステータス
    status = Column(
        String(50), default="draft"
    )  # draft, sent, accepted, rejected, expired

    # 金額情報
    subtotal = Column(Decimal(15, 2), default=0)
    discount_amount = Column(Decimal(12, 2), default=0)
    tax_amount = Column(Decimal(12, 2), default=0)
    total_amount = Column(Decimal(15, 2), default=0)

    # 営業情報
    sales_rep_id = Column(String, ForeignKey("users.id"))

    # 確率情報
    win_probability = Column(Decimal(5, 2), default=0)  # 0-100%
    expected_close_date = Column(DateTime)

    # メタデータ
    description = Column(Text)
    terms_conditions = Column(Text)
    internal_notes = Column(Text)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    customer = relationship("Customer", back_populates="quotes")
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])
    quote_items = relationship(
        "QuoteItem", back_populates="quote", cascade="all, delete-orphan"
    )
    sales_orders = relationship("SalesOrder", back_populates="quote")


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    # 商品情報
    product_sku = Column(String(100))
    product_name = Column(String(300))
    product_description = Column(Text)

    # 数量・価格
    quantity = Column(Decimal(10, 3), nullable=False)
    unit_price = Column(Decimal(12, 2), nullable=False)
    line_discount_amount = Column(Decimal(12, 2), default=0)
    line_total = Column(Decimal(15, 2), nullable=False)

    # メタデータ
    notes = Column(Text)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    quote = relationship("Quote", back_populates="quote_items")
    product = relationship("Product")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String(100), unique=True, nullable=False)
    sales_order_id = Column(String, ForeignKey("sales_orders.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)

    # 請求情報
    invoice_date = Column(DateTime(timezone=True), default=func.now())
    due_date = Column(DateTime(timezone=True))

    # ステータス
    status = Column(
        String(50), default="draft"
    )  # draft, sent, paid, overdue, cancelled

    # 金額情報
    subtotal = Column(Decimal(15, 2), nullable=False)
    tax_amount = Column(Decimal(12, 2), default=0)
    total_amount = Column(Decimal(15, 2), nullable=False)
    paid_amount = Column(Decimal(15, 2), default=0)
    balance_due = Column(Decimal(15, 2), nullable=False)

    # 支払情報
    payment_terms = Column(String(50))

    # メタデータ
    notes = Column(Text)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    sales_order = relationship("SalesOrder", back_populates="invoices")
    customer = relationship("Customer")
    payments = relationship("Payment", back_populates="invoice")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)

    # 支払情報
    payment_date = Column(DateTime(timezone=True), default=func.now())
    amount = Column(Decimal(15, 2), nullable=False)
    payment_method = Column(String(50))  # cash, check, credit_card, bank_transfer

    # 参照情報
    reference_number = Column(String(100))
    transaction_id = Column(String(100))

    # ステータス
    status = Column(
        String(50), default="completed"
    )  # pending, completed, failed, refunded

    # メタデータ
    notes = Column(Text)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    invoice = relationship("Invoice", back_populates="payments")
    customer = relationship("Customer")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_number = Column(String(100), unique=True, nullable=False)
    sales_order_id = Column(String, ForeignKey("sales_orders.id"), nullable=False)

    # 配送情報
    shipped_date = Column(DateTime(timezone=True))
    delivered_date = Column(DateTime(timezone=True))
    estimated_delivery_date = Column(DateTime(timezone=True))

    # ステータス
    status = Column(
        String(50), default="pending"
    )  # pending, shipped, in_transit, delivered, returned

    # 配送業者情報
    carrier = Column(String(100))
    tracking_number = Column(String(100))
    shipping_method = Column(String(100))
    shipping_cost = Column(Decimal(10, 2))

    # 配送先情報
    delivery_address_line1 = Column(String(200))
    delivery_address_line2 = Column(String(200))
    delivery_city = Column(String(100))
    delivery_state = Column(String(100))
    delivery_postal_code = Column(String(20))
    delivery_country = Column(String(100))

    # メタデータ
    notes = Column(Text)

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    sales_order = relationship("SalesOrder", back_populates="shipments")
    shipment_items = relationship(
        "ShipmentItem", back_populates="shipment", cascade="all, delete-orphan"
    )


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String, ForeignKey("shipments.id"), nullable=False)
    sales_order_item_id = Column(
        String, ForeignKey("sales_order_items.id"), nullable=False
    )
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    # 配送数量
    quantity_shipped = Column(Decimal(10, 3), nullable=False)
    quantity_delivered = Column(Decimal(10, 3), default=0)

    # メタデータ
    serial_numbers = Column(JSON, default=[])

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション
    shipment = relationship("Shipment", back_populates="shipment_items")
    sales_order_item = relationship("SalesOrderItem")
    product = relationship("Product")
