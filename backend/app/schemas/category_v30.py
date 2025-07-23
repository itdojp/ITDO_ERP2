import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class CategoryBase(BaseModel):
    category_code: str = Field(
        ..., min_length=1, max_length=50, description="カテゴリコード"
    )
    category_name: str = Field(
        ..., min_length=1, max_length=200, description="カテゴリ名"
    )
    category_name_en: Optional[str] = Field(
        None, max_length=200, description="英語カテゴリ名"
    )
    description: Optional[str] = Field(None, description="説明")

    @validator("category_code")
    def validate_category_code(cls, v):
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Category code must contain only uppercase letters, numbers, underscores, and hyphens"
            )
        return v


class CategoryCreate(CategoryBase):
    parent_id: Optional[str] = None

    # 分類設定
    category_type: str = Field(
        default="product", regex="^(product|service|expense|asset|customer|supplier)$"
    )
    industry_vertical: Optional[str] = Field(None, max_length=100)
    business_unit: Optional[str] = Field(None, max_length=100)

    # 表示設定
    display_name: Optional[str] = Field(None, max_length=200)
    display_order: int = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)

    # 税務・会計設定
    tax_category: Optional[str] = Field(
        None, regex="^(standard|reduced|exempt|zero_rated)$"
    )
    measurement_unit: Optional[str] = Field(None, max_length=20)
    weight_unit: Optional[str] = Field(None, max_length=10)
    dimension_unit: Optional[str] = Field(None, max_length=10)

    # 機能フラグ
    allow_sales: bool = True
    allow_purchase: bool = True
    allow_inventory: bool = True
    requires_serial_number: bool = False
    requires_lot_tracking: bool = False
    requires_expiry_tracking: bool = False
    quality_control_required: bool = False

    # 財務設定
    default_income_account: Optional[str] = Field(None, max_length=100)
    default_expense_account: Optional[str] = Field(None, max_length=100)
    default_asset_account: Optional[str] = Field(None, max_length=100)

    # 価格・コスト設定
    suggested_markup_percentage: Optional[Decimal] = Field(None, ge=0, le=1000)
    standard_cost_method: Optional[str] = Field(
        None, regex="^(standard|average|fifo|lifo)$"
    )
    valuation_method: Optional[str] = Field(None, regex="^(periodic|perpetual)$")
    safety_stock_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    # 分析設定
    abc_analysis_class: Optional[str] = Field(None, regex="^[ABC]$")
    vendor_managed_inventory: bool = False
    seasonality_pattern: Optional[str] = Field(
        None, regex="^(none|seasonal|promotional)$"
    )
    demand_pattern: Optional[str] = Field(
        None, regex="^(stable|volatile|declining|growing)$"
    )
    lifecycle_stage: Optional[str] = Field(
        None, regex="^(introduction|growth|maturity|decline)$"
    )
    profitability_rating: Optional[str] = Field(None, regex="^(high|medium|low)$")

    # 承認設定
    approval_required: bool = False

    # メタデータ
    attributes: Dict[str, Any] = {}
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    translations: Dict[str, Dict[str, str]] = {}

    # SEO設定
    seo_title: Optional[str] = Field(None, max_length=200)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = Field(None, max_length=500)
    url_slug: Optional[str] = Field(None, max_length=200)

    # アラート設定
    low_stock_alert_enabled: bool = False
    price_change_alert_enabled: bool = False
    new_product_alert_enabled: bool = False

    @validator("url_slug")
    def validate_url_slug(cls, v):
        if v and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "URL slug must contain only lowercase letters, numbers, and hyphens"
            )
        return v


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category_name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    display_name: Optional[str] = Field(None, max_length=200)
    display_order: Optional[int] = Field(None, ge=0)
    sort_order: Optional[int] = Field(None, ge=0)

    # ステータス更新
    is_active: Optional[bool] = None

    # 分類更新
    category_type: Optional[str] = Field(
        None, regex="^(product|service|expense|asset|customer|supplier)$"
    )
    industry_vertical: Optional[str] = Field(None, max_length=100)
    business_unit: Optional[str] = Field(None, max_length=100)

    # 税務・会計更新
    tax_category: Optional[str] = Field(
        None, regex="^(standard|reduced|exempt|zero_rated)$"
    )
    measurement_unit: Optional[str] = Field(None, max_length=20)

    # 機能フラグ更新
    allow_sales: Optional[bool] = None
    allow_purchase: Optional[bool] = None
    allow_inventory: Optional[bool] = None
    requires_serial_number: Optional[bool] = None
    requires_lot_tracking: Optional[bool] = None
    requires_expiry_tracking: Optional[bool] = None
    quality_control_required: Optional[bool] = None

    # 財務設定更新
    default_income_account: Optional[str] = Field(None, max_length=100)
    default_expense_account: Optional[str] = Field(None, max_length=100)
    default_asset_account: Optional[str] = Field(None, max_length=100)

    # 価格・コスト更新
    suggested_markup_percentage: Optional[Decimal] = Field(None, ge=0, le=1000)
    standard_cost_method: Optional[str] = Field(
        None, regex="^(standard|average|fifo|lifo)$"
    )
    valuation_method: Optional[str] = Field(None, regex="^(periodic|perpetual)$")
    safety_stock_percentage: Optional[Decimal] = Field(None, ge=0, le=100)

    # 分析更新
    abc_analysis_class: Optional[str] = Field(None, regex="^[ABC]$")
    vendor_managed_inventory: Optional[bool] = None
    seasonality_pattern: Optional[str] = Field(
        None, regex="^(none|seasonal|promotional)$"
    )
    demand_pattern: Optional[str] = Field(
        None, regex="^(stable|volatile|declining|growing)$"
    )
    lifecycle_stage: Optional[str] = Field(
        None, regex="^(introduction|growth|maturity|decline)$"
    )
    profitability_rating: Optional[str] = Field(None, regex="^(high|medium|low)$")

    # メタデータ更新
    attributes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    translations: Optional[Dict[str, Dict[str, str]]] = None

    # SEO更新
    seo_title: Optional[str] = Field(None, max_length=200)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = Field(None, max_length=500)
    url_slug: Optional[str] = Field(None, max_length=200)

    # アラート設定更新
    low_stock_alert_enabled: Optional[bool] = None
    price_change_alert_enabled: Optional[bool] = None
    new_product_alert_enabled: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: str
    parent_id: Optional[str]
    level: int
    sort_order: int
    path: Optional[str]
    path_ids: Optional[str]

    # 分類情報
    category_type: str
    industry_vertical: Optional[str]
    business_unit: Optional[str]

    # ステータス
    is_active: bool
    is_leaf: bool
    display_name: Optional[str]
    display_order: int

    # 税務・会計
    tax_category: Optional[str]
    measurement_unit: Optional[str]
    weight_unit: Optional[str]
    dimension_unit: Optional[str]

    # 機能設定
    allow_sales: bool
    allow_purchase: bool
    allow_inventory: bool
    requires_serial_number: bool
    requires_lot_tracking: bool
    requires_expiry_tracking: bool
    quality_control_required: bool

    # 財務設定
    default_income_account: Optional[str]
    default_expense_account: Optional[str]
    default_asset_account: Optional[str]

    # 価格・コスト
    suggested_markup_percentage: Optional[Decimal]
    standard_cost_method: Optional[str]
    valuation_method: Optional[str]
    safety_stock_percentage: Optional[Decimal]

    # 分析情報
    abc_analysis_class: Optional[str]
    vendor_managed_inventory: bool
    seasonality_pattern: Optional[str]
    demand_pattern: Optional[str]
    lifecycle_stage: Optional[str]
    profitability_rating: Optional[str]

    # 承認情報
    approval_required: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    approval_status: str

    # メタデータ
    attributes: Dict[str, Any]
    tags: List[str]
    custom_fields: Dict[str, Any]
    translations: Dict[str, Dict[str, str]]

    # 統計情報
    product_count: int
    total_sales_amount: Decimal
    avg_margin_percentage: Optional[Decimal]
    last_activity_date: Optional[datetime]

    # SEO
    seo_title: Optional[str]
    seo_description: Optional[str]
    seo_keywords: Optional[str]
    url_slug: Optional[str]

    # アラート設定
    low_stock_alert_enabled: bool
    price_change_alert_enabled: bool
    new_product_alert_enabled: bool

    # タイムスタンプ
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class CategoryAttributeBase(BaseModel):
    attribute_name: str = Field(..., min_length=1, max_length=100)
    attribute_name_en: Optional[str] = Field(None, max_length=100)
    attribute_code: str = Field(..., min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, max_length=150)

    @validator("attribute_code")
    def validate_attribute_code(cls, v):
        if not re.match(r"^[A-Za-z0-9_]+$", v):
            raise ValueError(
                "Attribute code must contain only letters, numbers, and underscores"
            )
        return v


class CategoryAttributeCreate(CategoryAttributeBase):
    category_id: str

    # データ型・制約
    data_type: str = Field(
        default="text", regex="^(text|number|date|boolean|select|multi_select)$"
    )
    is_required: bool = False
    is_unique: bool = False
    is_searchable: bool = True
    is_filterable: bool = True
    is_visible_in_list: bool = True

    # 表示設定
    display_order: int = Field(default=0, ge=0)
    group_name: Optional[str] = Field(None, max_length=50)
    help_text: Optional[str] = None
    placeholder_text: Optional[str] = Field(None, max_length=200)

    # 値制約
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    min_length: Optional[int] = Field(None, ge=0)
    max_length: Optional[int] = Field(None, ge=0)
    regex_pattern: Optional[str] = Field(None, max_length=500)
    default_value: Optional[str] = None

    # 選択肢
    option_values: List[Dict[str, Any]] = []

    # 計測単位
    unit: Optional[str] = Field(None, max_length=20)
    unit_type: Optional[str] = Field(
        None, regex="^(length|weight|volume|currency|percentage|count|time)$"
    )

    # バリデーション
    validation_rules: Dict[str, Any] = {}
    business_rules: Dict[str, Any] = {}

    # 多言語・継承設定
    translations: Dict[str, Dict[str, str]] = {}
    inherit_from_parent: bool = False
    shared_across_categories: bool = False

    @validator("min_length", "max_length")
    def validate_length_constraints(cls, v, values, field):
        if field.name == "max_length" and v is not None:
            min_length = values.get("min_length")
            if min_length is not None and v < min_length:
                raise ValueError(
                    "max_length must be greater than or equal to min_length"
                )
        return v

    @validator("max_value")
    def validate_value_constraints(cls, v, values):
        if v is not None:
            min_value = values.get("min_value")
            if min_value is not None and v < min_value:
                raise ValueError("max_value must be greater than or equal to min_value")
        return v


class CategoryAttributeUpdate(BaseModel):
    attribute_name: Optional[str] = Field(None, min_length=1, max_length=100)
    attribute_name_en: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=150)

    # 設定更新
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    is_searchable: Optional[bool] = None
    is_filterable: Optional[bool] = None
    is_visible_in_list: Optional[bool] = None

    # 表示更新
    display_order: Optional[int] = Field(None, ge=0)
    group_name: Optional[str] = Field(None, max_length=50)
    help_text: Optional[str] = None
    placeholder_text: Optional[str] = Field(None, max_length=200)

    # 制約更新
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    min_length: Optional[int] = Field(None, ge=0)
    max_length: Optional[int] = Field(None, ge=0)
    regex_pattern: Optional[str] = Field(None, max_length=500)
    default_value: Optional[str] = None

    # 選択肢更新
    option_values: Optional[List[Dict[str, Any]]] = None

    # 計測単位更新
    unit: Optional[str] = Field(None, max_length=20)
    unit_type: Optional[str] = Field(
        None, regex="^(length|weight|volume|currency|percentage|count|time)$"
    )

    # その他更新
    validation_rules: Optional[Dict[str, Any]] = None
    business_rules: Optional[Dict[str, Any]] = None
    translations: Optional[Dict[str, Dict[str, str]]] = None
    inherit_from_parent: Optional[bool] = None
    shared_across_categories: Optional[bool] = None


class CategoryAttributeResponse(CategoryAttributeBase):
    id: str
    category_id: str
    data_type: str
    is_required: bool
    is_unique: bool
    is_searchable: bool
    is_filterable: bool
    is_visible_in_list: bool
    display_order: int
    group_name: Optional[str]
    help_text: Optional[str]
    placeholder_text: Optional[str]
    min_value: Optional[Decimal]
    max_value: Optional[Decimal]
    min_length: Optional[int]
    max_length: Optional[int]
    regex_pattern: Optional[str]
    default_value: Optional[str]
    option_values: List[Dict[str, Any]]
    unit: Optional[str]
    unit_type: Optional[str]
    validation_rules: Dict[str, Any]
    business_rules: Dict[str, Any]
    translations: Dict[str, Dict[str, str]]
    inherit_from_parent: bool
    shared_across_categories: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        orm_mode = True


class CategoryPricingRuleBase(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=200)
    rule_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class CategoryPricingRuleCreate(CategoryPricingRuleBase):
    category_id: str

    # ルール設定
    rule_type: str = Field(
        default="markup", regex="^(markup|discount|fixed_price|cost_plus|competitive)$"
    )
    priority: int = Field(default=0, ge=0)
    is_active: bool = True

    # 適用期間
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

    # 適用条件
    customer_segments: List[str] = []
    minimum_quantity: Optional[Decimal] = Field(None, ge=0)
    maximum_quantity: Optional[Decimal] = Field(None, ge=0)
    minimum_amount: Optional[Decimal] = Field(None, ge=0)

    # 価格計算パラメータ
    markup_percentage: Optional[Decimal] = Field(None, ge=0, le=1000)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    fixed_amount: Optional[Decimal] = Field(None, ge=0)
    cost_multiplier: Optional[Decimal] = Field(None, ge=0)

    # 価格帯設定
    price_tiers: List[Dict[str, Any]] = []
    volume_discounts: List[Dict[str, Any]] = []

    # 地域・通貨
    currency: str = Field(default="JPY", regex="^[A-Z]{3}$")
    region_codes: List[str] = []
    exchange_rate_factor: Optional[Decimal] = Field(None, gt=0)

    # 競合・市場
    competitor_price_factor: Optional[Decimal] = Field(None, gt=0)
    market_position: Optional[str] = Field(None, regex="^(premium|standard|budget)$")
    price_elasticity: Optional[Decimal] = Field(None, ge=0)

    # 承認
    approval_required: bool = False

    @validator("maximum_quantity")
    def validate_quantity_range(cls, v, values):
        if v is not None:
            min_qty = values.get("minimum_quantity")
            if min_qty is not None and v < min_qty:
                raise ValueError(
                    "maximum_quantity must be greater than or equal to minimum_quantity"
                )
        return v

    @validator("expiry_date")
    def validate_date_range(cls, v, values):
        if v is not None:
            effective_date = values.get("effective_date")
            if effective_date is not None and v <= effective_date:
                raise ValueError("expiry_date must be later than effective_date")
        return v


class CategoryPricingRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(
        None, regex="^(markup|discount|fixed_price|cost_plus|competitive)$"
    )
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    customer_segments: Optional[List[str]] = None
    minimum_quantity: Optional[Decimal] = Field(None, ge=0)
    maximum_quantity: Optional[Decimal] = Field(None, ge=0)
    minimum_amount: Optional[Decimal] = Field(None, ge=0)
    markup_percentage: Optional[Decimal] = Field(None, ge=0, le=1000)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    fixed_amount: Optional[Decimal] = Field(None, ge=0)
    cost_multiplier: Optional[Decimal] = Field(None, ge=0)
    price_tiers: Optional[List[Dict[str, Any]]] = None
    volume_discounts: Optional[List[Dict[str, Any]]] = None
    currency: Optional[str] = Field(None, regex="^[A-Z]{3}$")
    region_codes: Optional[List[str]] = None
    exchange_rate_factor: Optional[Decimal] = Field(None, gt=0)
    competitor_price_factor: Optional[Decimal] = Field(None, gt=0)
    market_position: Optional[str] = Field(None, regex="^(premium|standard|budget)$")
    price_elasticity: Optional[Decimal] = Field(None, ge=0)


class CategoryPricingRuleResponse(CategoryPricingRuleBase):
    id: str
    category_id: str
    rule_type: str
    priority: int
    is_active: bool
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    customer_segments: List[str]
    minimum_quantity: Optional[Decimal]
    maximum_quantity: Optional[Decimal]
    minimum_amount: Optional[Decimal]
    markup_percentage: Optional[Decimal]
    discount_percentage: Optional[Decimal]
    fixed_amount: Optional[Decimal]
    cost_multiplier: Optional[Decimal]
    price_tiers: List[Dict[str, Any]]
    volume_discounts: List[Dict[str, Any]]
    currency: str
    region_codes: List[str]
    exchange_rate_factor: Optional[Decimal]
    competitor_price_factor: Optional[Decimal]
    market_position: Optional[str]
    price_elasticity: Optional[Decimal]
    approval_required: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    usage_count: int
    last_applied_date: Optional[datetime]
    effectiveness_rating: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        orm_mode = True


class CategoryHierarchyResponse(BaseModel):
    id: str
    category_id: str
    level_1_id: Optional[str]
    level_1_name: Optional[str]
    level_2_id: Optional[str]
    level_2_name: Optional[str]
    level_3_id: Optional[str]
    level_3_name: Optional[str]
    level_4_id: Optional[str]
    level_4_name: Optional[str]
    level_5_id: Optional[str]
    level_5_name: Optional[str]
    hierarchy_level: int
    full_path: Optional[str]
    full_path_ids: Optional[str]
    descendant_count: int
    product_count_direct: int
    product_count_total: int
    total_sales_amount: Decimal
    total_profit_amount: Decimal
    avg_margin_percentage: Optional[Decimal]
    total_inventory_value: Decimal
    total_inventory_quantity: Decimal
    last_updated: datetime

    class Config:
        orm_mode = True


class CategoryAnalyticsResponse(BaseModel):
    total_categories: int
    active_categories: int
    inactive_categories: int
    leaf_categories: int
    avg_hierarchy_depth: float
    max_hierarchy_depth: int
    categories_by_type: Dict[str, int]
    categories_by_level: Dict[int, int]
    top_categories_by_product_count: List[Dict[str, Any]]
    top_categories_by_sales: List[Dict[str, Any]]
    categories_needing_attention: List[Dict[str, Any]]
    taxonomy_completeness: Dict[str, Any]


class CategoryMoveRequest(BaseModel):
    category_id: str
    new_parent_id: Optional[str] = None
    new_position: Optional[int] = Field(None, ge=0)


class CategoryBulkOperationRequest(BaseModel):
    category_ids: List[str] = Field(..., min_items=1)
    operation: str = Field(
        ..., regex="^(activate|deactivate|delete|move|update_attributes)$"
    )
    operation_data: Optional[Dict[str, Any]] = {}


class CategoryImportRequest(BaseModel):
    import_format: str = Field(..., regex="^(csv|json|xml)$")
    data_mapping: Dict[str, str]  # field mapping
    import_options: Dict[str, Any] = {}
    validate_only: bool = False


class CategoryExportRequest(BaseModel):
    export_format: str = Field(default="csv", regex="^(csv|json|xml|excel)$")
    category_filters: Dict[str, Any] = {}
    include_hierarchy: bool = True
    include_attributes: bool = False
    include_pricing_rules: bool = False


# List Response Models
class CategoryListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[CategoryResponse]


class CategoryAttributeListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[CategoryAttributeResponse]


class CategoryPricingRuleListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[CategoryPricingRuleResponse]


class CategoryHierarchyListResponse(BaseModel):
    total: int
    items: List[CategoryHierarchyResponse]
