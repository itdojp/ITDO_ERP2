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


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    # 階層構造
    parent_id = Column(String, ForeignKey("product_categories.id"))
    level = Column(Integer, default=0)
    path = Column(Text)  # /root/parent/child 形式

    # カテゴリ設定
    tax_rate = Column(Decimal(5, 4), default=0.1)  # 消費税率
    commission_rate = Column(Decimal(5, 4), default=0.0)  # 手数料率

    # ステータス
    is_active = Column(Boolean, default=True)

    # メタデータ
    metadata_json = Column(JSON, default={})

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    parent = relationship(
        "ProductCategory", remote_side=[id], back_populates="children"
    )
    children = relationship("ProductCategory", back_populates="parent")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text)
    short_description = Column(String(500))

    # カテゴリと分類
    category_id = Column(String, ForeignKey("product_categories.id"))
    brand = Column(String(100))
    manufacturer = Column(String(200))
    supplier_id = Column(String, ForeignKey("suppliers.id"))

    # 価格情報
    cost_price = Column(Decimal(12, 2))  # 原価
    selling_price = Column(Decimal(12, 2), nullable=False)  # 販売価格
    list_price = Column(Decimal(12, 2))  # 定価
    min_price = Column(Decimal(12, 2))  # 最低販売価格

    # 物理的属性
    weight = Column(Decimal(10, 3))  # 重量(kg)
    length = Column(Decimal(10, 2))  # 長さ(cm)
    width = Column(Decimal(10, 2))  # 幅(cm)
    height = Column(Decimal(10, 2))  # 高さ(cm)
    volume = Column(Decimal(10, 3))  # 体積(L)

    # 在庫管理
    track_inventory = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)
    reorder_point = Column(Integer, default=0)
    reorder_quantity = Column(Integer, default=0)
    max_stock_level = Column(Integer)

    # 単位
    unit_of_measure = Column(String(20), default="piece")  # 単位
    conversion_factor = Column(Decimal(10, 4), default=1.0)  # 換算係数

    # 商品状態
    product_type = Column(String(50), default="physical")  # physical, digital, service
    product_status = Column(
        String(50), default="active"
    )  # active, inactive, discontinued
    lifecycle_stage = Column(
        String(50), default="active"
    )  # new, active, mature, declining, discontinued

    # 品質・規格
    quality_grade = Column(String(20))
    certification = Column(String(200))
    warranty_period = Column(Integer)  # 保証期間（日）
    expiry_period = Column(Integer)  # 有効期間（日）

    # 販売・購入設定
    is_purchaseable = Column(Boolean, default=True)
    is_sellable = Column(Boolean, default=True)
    min_order_quantity = Column(Integer, default=1)
    max_order_quantity = Column(Integer)

    # SEO・検索
    search_keywords = Column(Text)
    barcode = Column(String(50), unique=True)
    qr_code = Column(Text)

    # 税金設定
    tax_category = Column(String(50))
    tax_rate = Column(Decimal(5, 4))

    # メタデータ
    attributes = Column(JSON, default={})  # カスタム属性
    specifications = Column(JSON, default={})  # 仕様
    variants = Column(JSON, default={})  # バリアント設定

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sold_at = Column(DateTime(timezone=True))
    last_purchased_at = Column(DateTime(timezone=True))

    # リレーション
    category = relationship("ProductCategory", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    images = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )
    variants_rel = relationship("ProductVariant", back_populates="parent_product")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    price_history = relationship("ProductPriceHistory", back_populates="product")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_product_id = Column(String, ForeignKey("products.id"), nullable=False)
    variant_sku = Column(String(100), unique=True, nullable=False)
    variant_name = Column(String(200))

    # バリアント属性
    color = Column(String(50))
    size = Column(String(50))
    style = Column(String(50))
    material = Column(String(100))

    # 価格・在庫（親商品からの差分）
    price_adjustment = Column(Decimal(12, 2), default=0)
    cost_adjustment = Column(Decimal(12, 2), default=0)
    stock_quantity = Column(Integer, default=0)

    # 物理属性（親商品からの差分）
    weight_adjustment = Column(Decimal(10, 3), default=0)

    # ステータス
    is_active = Column(Boolean, default=True)

    # カスタム属性
    attributes = Column(JSON, default={})

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    parent_product = relationship("Product", back_populates="variants_rel")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    # 画像情報
    filename = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    alt_text = Column(String(200))
    caption = Column(String(500))

    # 画像分類
    image_type = Column(
        String(50), default="product"
    )  # product, variant, detail, lifestyle
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    # 画像メタデータ
    file_size = Column(Integer)  # bytes
    width = Column(Integer)  # pixels
    height = Column(Integer)  # pixels
    format = Column(String(10))  # jpg, png, webp

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    product = relationship("Product", back_populates="images")


class ProductPriceHistory(Base):
    __tablename__ = "product_price_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    # 価格情報
    cost_price = Column(Decimal(12, 2))
    selling_price = Column(Decimal(12, 2))
    list_price = Column(Decimal(12, 2))

    # 変更情報
    change_reason = Column(String(200))
    changed_by = Column(String, ForeignKey("users.id"))

    # 有効期間
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション
    product = relationship("Product", back_populates="price_history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)

    # 連絡先情報
    email = Column(String(200))
    phone = Column(String(50))
    fax = Column(String(50))
    website = Column(String(200))

    # 住所情報
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Japan")

    # サプライヤー情報
    supplier_type = Column(String(50))  # manufacturer, distributor, wholesaler
    payment_terms = Column(String(100))
    credit_limit = Column(Decimal(15, 2))
    tax_id = Column(String(50))

    # 評価・品質
    quality_rating = Column(Decimal(3, 2))  # 1.00-5.00
    delivery_rating = Column(Decimal(3, 2))
    price_rating = Column(Decimal(3, 2))
    overall_rating = Column(Decimal(3, 2))

    # ステータス
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)

    # メタデータ
    notes = Column(Text)
    metadata_json = Column(JSON, default={})

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    products = relationship("Product", back_populates="supplier")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    # 在庫移動情報
    movement_type = Column(String(50), nullable=False)  # in, out, adjustment, transfer
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Decimal(12, 2))
    total_cost = Column(Decimal(12, 2))

    # 移動前後の在庫
    stock_before = Column(Integer)
    stock_after = Column(Integer)

    # 移動理由・参照
    reference_type = Column(
        String(50)
    )  # purchase_order, sale_order, adjustment, transfer
    reference_id = Column(String)
    reason = Column(String(200))
    notes = Column(Text)

    # 場所情報
    warehouse_from = Column(String(100))
    warehouse_to = Column(String(100))
    location = Column(String(100))

    # 作業者情報
    created_by = Column(String, ForeignKey("users.id"))
    approved_by = Column(String, ForeignKey("users.id"))

    # タイムスタンプ
    movement_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション
    product = relationship("Product", back_populates="inventory_movements")
    created_by_user = relationship("User", foreign_keys=[created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
