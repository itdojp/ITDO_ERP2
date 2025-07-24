import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(default=0.1, ge=0, le=1)
    commission_rate: Optional[Decimal] = Field(default=0.0, ge=0, le=1)

    @validator("code")
    def code_valid(cls, v) -> dict:
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Code must contain only uppercase letters, numbers, hyphens and underscores"
            )
        return v


class ProductCategoryCreate(ProductCategoryBase):
    parent_id: Optional[str] = None
    metadata_json: Dict[str, Any] = {}


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ProductCategoryResponse(ProductCategoryBase):
    id: str
    parent_id: Optional[str]
    level: int
    path: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    products_count: int = 0

    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    brand: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)

    # 価格情報
    cost_price: Optional[Decimal] = Field(None, ge=0)
    selling_price: Decimal = Field(..., ge=0)
    list_price: Optional[Decimal] = Field(None, ge=0)
    min_price: Optional[Decimal] = Field(None, ge=0)

    # 物理属性
    weight: Optional[Decimal] = Field(None, ge=0)
    length: Optional[Decimal] = Field(None, ge=0)
    width: Optional[Decimal] = Field(None, ge=0)
    height: Optional[Decimal] = Field(None, ge=0)

    # 在庫設定
    track_inventory: bool = True
    reorder_point: int = Field(default=0, ge=0)
    reorder_quantity: int = Field(default=0, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)

    # 単位・状態
    unit_of_measure: str = Field(default="piece", max_length=20)
    product_type: str = Field(default="physical", regex="^(physical|digital|service)$")
    product_status: str = Field(
        default="active", regex="^(active|inactive|discontinued)$"
    )

    @validator("sku")
    def sku_valid(cls, v) -> dict:
        if not re.match(r"^[A-Z0-9_-]+$", v.upper()):
            raise ValueError(
                "SKU must contain only letters, numbers, hyphens and underscores"
            )
        return v.upper()


class ProductCreate(ProductBase):
    category_id: Optional[str] = None
    supplier_id: Optional[str] = None

    # 詳細設定
    quality_grade: Optional[str] = None
    certification: Optional[str] = None
    warranty_period: Optional[int] = Field(None, ge=0)
    expiry_period: Optional[int] = Field(None, ge=0)

    # 販売設定
    is_purchaseable: bool = True
    is_sellable: bool = True
    min_order_quantity: int = Field(default=1, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)

    # SEO・識別
    search_keywords: Optional[str] = None
    barcode: Optional[str] = None
    tax_category: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)

    # カスタム属性
    attributes: Dict[str, Any] = {}
    specifications: Dict[str, Any] = {}


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    brand: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    category_id: Optional[str] = None
    supplier_id: Optional[str] = None

    # 価格更新
    cost_price: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    list_price: Optional[Decimal] = Field(None, ge=0)
    min_price: Optional[Decimal] = Field(None, ge=0)

    # 在庫設定
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)

    # ステータス
    product_status: Optional[str] = Field(
        None, regex="^(active|inactive|discontinued)$"
    )
    is_purchaseable: Optional[bool] = None
    is_sellable: Optional[bool] = None

    # カスタム属性
    attributes: Optional[Dict[str, Any]] = None
    specifications: Optional[Dict[str, Any]] = None


class ProductResponse(ProductBase):
    id: str
    category_id: Optional[str]
    supplier_id: Optional[str]

    # 在庫情報
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int

    # 計算フィールド
    volume: Optional[Decimal]

    # メタデータ
    lifecycle_stage: str
    quality_grade: Optional[str]
    certification: Optional[str]
    warranty_period: Optional[int]

    # 販売設定
    is_purchaseable: bool
    is_sellable: bool
    min_order_quantity: int
    max_order_quantity: Optional[int]

    # 識別情報
    barcode: Optional[str]
    search_keywords: Optional[str]

    # 税金設定
    tax_category: Optional[str]
    tax_rate: Optional[Decimal]

    # カスタム属性
    attributes: Dict[str, Any]
    specifications: Dict[str, Any]

    # タイムスタンプ
    created_at: datetime
    updated_at: Optional[datetime]
    last_sold_at: Optional[datetime]
    last_purchased_at: Optional[datetime]

    class Config:
        orm_mode = True


class ProductListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[ProductResponse]


class ProductVariantBase(BaseModel):
    variant_sku: str = Field(..., min_length=1, max_length=100)
    variant_name: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    style: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)


class ProductVariantCreate(ProductVariantBase):
    price_adjustment: Decimal = Field(default=0)
    cost_adjustment: Decimal = Field(default=0)
    stock_quantity: int = Field(default=0, ge=0)
    weight_adjustment: Decimal = Field(default=0)
    attributes: Dict[str, Any] = {}


class ProductVariantResponse(ProductVariantBase):
    id: str
    parent_product_id: str
    price_adjustment: Decimal
    cost_adjustment: Decimal
    stock_quantity: int
    weight_adjustment: Decimal
    is_active: bool
    attributes: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ProductImageBase(BaseModel):
    filename: str = Field(..., max_length=200)
    url: str = Field(..., max_length=500)
    alt_text: Optional[str] = Field(None, max_length=200)
    caption: Optional[str] = Field(None, max_length=500)
    image_type: str = Field(
        default="product", regex="^(product|variant|detail|lifestyle)$"
    )
    sort_order: int = Field(default=0, ge=0)


class ProductImageCreate(ProductImageBase):
    is_primary: bool = False
    file_size: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=0)
    height: Optional[int] = Field(None, ge=0)
    format: Optional[str] = Field(None, max_length=10)


class ProductImageResponse(ProductImageBase):
    id: str
    product_id: str
    is_primary: bool
    file_size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    format: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    # 住所
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "Japan"

    # サプライヤー情報
    supplier_type: Optional[str] = Field(
        None, regex="^(manufacturer|distributor|wholesaler)$"
    )
    payment_terms: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)

    @validator("code")
    def code_valid(cls, v) -> dict:
        if not re.match(r"^[A-Z0-9_-]+$", v):
            raise ValueError(
                "Code must contain only uppercase letters, numbers, hyphens and underscores"
            )
        return v


class SupplierCreate(SupplierBase):
    fax: Optional[str] = None
    address_line2: Optional[str] = None
    state: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    metadata_json: Dict[str, Any] = {}


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    supplier_type: Optional[str] = Field(
        None, regex="^(manufacturer|distributor|wholesaler)$"
    )
    payment_terms: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_preferred: Optional[bool] = None
    notes: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: str
    fax: Optional[str]
    address_line2: Optional[str]
    state: Optional[str]
    tax_id: Optional[str]
    quality_rating: Optional[Decimal]
    delivery_rating: Optional[Decimal]
    price_rating: Optional[Decimal]
    overall_rating: Optional[Decimal]
    is_active: bool
    is_preferred: bool
    notes: Optional[str]
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    products_count: int = 0

    class Config:
        orm_mode = True


class InventoryMovementBase(BaseModel):
    movement_type: str = Field(..., regex="^(in|out|adjustment|transfer)$")
    quantity: int = Field(..., ne=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    reason: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class InventoryMovementCreate(InventoryMovementBase):
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    warehouse_from: Optional[str] = None
    warehouse_to: Optional[str] = None
    location: Optional[str] = None
    movement_date: datetime = Field(default_factory=datetime.utcnow)


class InventoryMovementResponse(InventoryMovementBase):
    id: str
    product_id: str
    total_cost: Optional[Decimal]
    stock_before: Optional[int]
    stock_after: Optional[int]
    reference_type: Optional[str]
    reference_id: Optional[str]
    warehouse_from: Optional[str]
    warehouse_to: Optional[str]
    location: Optional[str]
    created_by: Optional[str]
    approved_by: Optional[str]
    movement_date: datetime
    created_at: datetime

    class Config:
        orm_mode = True


class ProductPriceHistoryResponse(BaseModel):
    id: str
    product_id: str
    cost_price: Optional[Decimal]
    selling_price: Optional[Decimal]
    list_price: Optional[Decimal]
    change_reason: Optional[str]
    changed_by: Optional[str]
    effective_from: datetime
    effective_to: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True


class ProductStatsResponse(BaseModel):
    total_products: int
    active_products: int
    inactive_products: int
    discontinued_products: int
    by_category: Dict[str, int]
    by_brand: Dict[str, int]
    by_supplier: Dict[str, int]
    low_stock_count: int
    out_of_stock_count: int
    total_inventory_value: Decimal


class BulkPriceUpdateRequest(BaseModel):
    product_ids: List[str]
    price_type: str = Field(..., regex="^(cost_price|selling_price|list_price)$")
    adjustment_type: str = Field(..., regex="^(amount|percentage)$")
    adjustment_value: Decimal
    reason: str = Field(..., max_length=200)


class BulkPriceUpdateResponse(BaseModel):
    success_count: int
    error_count: int
    updated_products: List[str]
    errors: List[Dict[str, Any]]
