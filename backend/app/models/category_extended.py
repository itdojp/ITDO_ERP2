from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Decimal
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String, ForeignKey('categories.id'), nullable=True)
    
    # 基本情報
    category_code = Column(String(50), unique=True, nullable=False)
    category_name = Column(String(200), nullable=False)
    category_name_en = Column(String(200))
    description = Column(Text)
    
    # 階層情報
    level = Column(Integer, default=1)  # 1=top level, 2=sub, 3=sub-sub, etc.
    sort_order = Column(Integer, default=0)
    path = Column(String(500))  # Full category path like "Electronics > Computers > Laptops"
    path_ids = Column(String(500))  # ID path like "cat1,cat2,cat3"
    
    # 分類タイプ
    category_type = Column(String(50), default="product")  # product, service, expense, asset, customer, supplier
    industry_vertical = Column(String(100))  # 業界垂直分類
    business_unit = Column(String(100))  # 事業部分類
    
    # 表示・状態管理
    is_active = Column(Boolean, default=True)
    is_leaf = Column(Boolean, default=True)  # True if no children
    display_name = Column(String(200))  # UI表示用名称
    display_order = Column(Integer, default=0)
    
    # 商品管理固有
    tax_category = Column(String(50))  # standard, reduced, exempt, zero_rated
    measurement_unit = Column(String(20))  # デフォルト計測単位
    weight_unit = Column(String(10))  # 重量単位
    dimension_unit = Column(String(10))  # 寸法単位
    
    # 販売・購買管理
    allow_sales = Column(Boolean, default=True)
    allow_purchase = Column(Boolean, default=True)
    allow_inventory = Column(Boolean, default=True)
    requires_serial_number = Column(Boolean, default=False)
    requires_lot_tracking = Column(Boolean, default=False)
    requires_expiry_tracking = Column(Boolean, default=False)
    
    # 財務管理
    default_income_account = Column(String(100))  # 売上勘定科目
    default_expense_account = Column(String(100))  # 費用勘定科目
    default_asset_account = Column(String(100))  # 資産勘定科目
    
    # 価格・コスト管理
    suggested_markup_percentage = Column(Decimal(5, 2))  # 推奨マークアップ率
    standard_cost_method = Column(String(30))  # standard, average, fifo, lifo
    valuation_method = Column(String(30))  # periodic, perpetual
    
    # 品質・コンプライアンス
    quality_control_required = Column(Boolean, default=False)
    safety_stock_percentage = Column(Decimal(5, 2))  # 安全在庫率
    abc_analysis_class = Column(String(1))  # A, B, C classification
    vendor_managed_inventory = Column(Boolean, default=False)
    
    # 分析・レポート用
    seasonality_pattern = Column(String(50))  # none, seasonal, promotional
    demand_pattern = Column(String(50))  # stable, volatile, declining, growing
    lifecycle_stage = Column(String(50))  # introduction, growth, maturity, decline
    profitability_rating = Column(String(20))  # high, medium, low
    
    # 承認・ワークフロー
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    approval_status = Column(String(20), default="approved")  # pending, approved, rejected
    
    # メタデータ・拡張
    attributes = Column(JSON, default={})  # 追加属性の動的格納
    tags = Column(JSON, default=[])  # タグ機能
    custom_fields = Column(JSON, default={})  # カスタムフィールド
    
    # 多言語対応
    translations = Column(JSON, default={})  # {"ja": {name: "", desc: ""}, "en": {...}}
    
    # 統計・パフォーマンス指標
    product_count = Column(Integer, default=0)  # このカテゴリの商品数
    total_sales_amount = Column(Decimal(15, 2), default=0)  # 総売上
    avg_margin_percentage = Column(Decimal(5, 2))  # 平均利益率
    last_activity_date = Column(DateTime)  # 最終活動日時
    
    # SEO・Web対応
    seo_title = Column(String(200))
    seo_description = Column(Text)
    seo_keywords = Column(String(500))
    url_slug = Column(String(200))
    
    # アラート・通知設定
    low_stock_alert_enabled = Column(Boolean, default=False)
    price_change_alert_enabled = Column(Boolean, default=False)
    new_product_alert_enabled = Column(Boolean, default=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    updated_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    # 商品・サービスとの関連
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
    category_attributes = relationship("CategoryAttribute", back_populates="category", cascade="all, delete-orphan")
    pricing_rules = relationship("CategoryPricingRule", back_populates="category", cascade="all, delete-orphan")


class CategoryAttribute(Base):
    __tablename__ = "category_attributes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey('categories.id'), nullable=False)
    
    # 属性基本情報
    attribute_name = Column(String(100), nullable=False)
    attribute_name_en = Column(String(100))
    attribute_code = Column(String(50), nullable=False)
    display_name = Column(String(150))
    
    # 属性設定
    data_type = Column(String(30), default="text")  # text, number, date, boolean, select, multi_select
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_filterable = Column(Boolean, default=True)
    is_visible_in_list = Column(Boolean, default=True)
    
    # 表示設定
    display_order = Column(Integer, default=0)
    group_name = Column(String(50))  # 属性グループ名
    help_text = Column(Text)
    placeholder_text = Column(String(200))
    
    # 値制約
    min_value = Column(Decimal(15, 4))
    max_value = Column(Decimal(15, 4))
    min_length = Column(Integer)
    max_length = Column(Integer)
    regex_pattern = Column(String(500))
    default_value = Column(Text)
    
    # 選択肢（select, multi_select用）
    option_values = Column(JSON, default=[])  # [{"value": "red", "label": "赤", "label_en": "Red"}]
    
    # 計測単位
    unit = Column(String(20))
    unit_type = Column(String(30))  # length, weight, volume, currency, percentage, etc.
    
    # バリデーション・業務ルール
    validation_rules = Column(JSON, default={})
    business_rules = Column(JSON, default={})
    
    # 多言語対応
    translations = Column(JSON, default={})
    
    # 継承・共有設定
    inherit_from_parent = Column(Boolean, default=False)
    shared_across_categories = Column(Boolean, default=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    category = relationship("Category", back_populates="category_attributes")
    creator = relationship("User")


class CategoryPricingRule(Base):
    __tablename__ = "category_pricing_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey('categories.id'), nullable=False)
    
    # ルール基本情報
    rule_name = Column(String(200), nullable=False)
    rule_code = Column(String(50))
    description = Column(Text)
    
    # ルール設定
    rule_type = Column(String(30), default="markup")  # markup, discount, fixed_price, cost_plus, competitive
    priority = Column(Integer, default=0)  # 複数ルール適用時の優先順位
    is_active = Column(Boolean, default=True)
    
    # 適用条件
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)
    customer_segments = Column(JSON, default=[])  # 対象顧客セグメント
    minimum_quantity = Column(Decimal(10, 2))
    maximum_quantity = Column(Decimal(10, 2))
    minimum_amount = Column(Decimal(15, 2))
    
    # 価格計算パラメータ
    markup_percentage = Column(Decimal(6, 3))  # マークアップ率
    discount_percentage = Column(Decimal(6, 3))  # 割引率
    fixed_amount = Column(Decimal(15, 2))  # 固定金額
    cost_multiplier = Column(Decimal(6, 3))  # 原価倍率
    
    # 価格帯設定
    price_tiers = Column(JSON, default=[])  # 数量別価格帯設定
    volume_discounts = Column(JSON, default=[])  # ボリュームディスカウント
    
    # 地域・通貨設定
    currency = Column(String(3), default="JPY")
    region_codes = Column(JSON, default=[])  # 適用地域
    exchange_rate_factor = Column(Decimal(8, 4))
    
    # 競合・市場データ
    competitor_price_factor = Column(Decimal(6, 3))
    market_position = Column(String(30))  # premium, standard, budget
    price_elasticity = Column(Decimal(6, 3))
    
    # 承認・監査
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    
    # 実績・分析
    usage_count = Column(Integer, default=0)
    last_applied_date = Column(DateTime)
    effectiveness_rating = Column(Decimal(3, 2))  # 1-5
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey('users.id'))
    
    # リレーション
    category = relationship("Category", back_populates="pricing_rules")
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])


class CategoryAuditLog(Base):
    __tablename__ = "category_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey('categories.id'), nullable=False)
    
    # 監査基本情報
    action = Column(String(30), nullable=False)  # create, update, delete, activate, deactivate
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # 変更内容
    field_name = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    change_reason = Column(Text)
    
    # 影響範囲
    affected_products_count = Column(Integer, default=0)
    affected_children_count = Column(Integer, default=0)
    cascade_changes = Column(JSON, default=[])
    
    # コンテキスト情報
    business_process = Column(String(100))  # 業務プロセス名
    integration_source = Column(String(100))  # API, web, batch, import
    batch_id = Column(String(100))  # バッチ処理ID
    
    # タイムスタンプ
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    category = relationship("Category")
    user = relationship("User")


class CategoryHierarchyView(Base):
    __tablename__ = "category_hierarchy_view"

    id = Column(String, primary_key=True)
    category_id = Column(String, ForeignKey('categories.id'), nullable=False)
    
    # 階層情報（非正規化）
    level_1_id = Column(String)
    level_1_name = Column(String(200))
    level_2_id = Column(String)
    level_2_name = Column(String(200))
    level_3_id = Column(String)
    level_3_name = Column(String(200))
    level_4_id = Column(String)
    level_4_name = Column(String(200))
    level_5_id = Column(String)
    level_5_name = Column(String(200))
    
    # 階層レベル
    hierarchy_level = Column(Integer)
    full_path = Column(String(1000))
    full_path_ids = Column(String(500))
    
    # 集計情報
    descendant_count = Column(Integer, default=0)
    product_count_direct = Column(Integer, default=0)
    product_count_total = Column(Integer, default=0)  # 子カテゴリ含む
    
    # 財務集計
    total_sales_amount = Column(Decimal(18, 2), default=0)
    total_profit_amount = Column(Decimal(18, 2), default=0)
    avg_margin_percentage = Column(Decimal(5, 2))
    
    # 在庫集計
    total_inventory_value = Column(Decimal(18, 2), default=0)
    total_inventory_quantity = Column(Decimal(15, 2), default=0)
    
    # 更新情報
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    category = relationship("Category")