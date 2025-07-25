"""
Product Business Schemas - CC02 v53.0 ERPビジネスAPI実装
Issue #568対応 - 商品管理API用の完全なスキーマセット

Features:
- Full CRUD schema validation
- Business rule validation
- Multi-tenant support
- Performance optimized field selection
- Comprehensive error handling
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ProductStatus(str, Enum):
    """Product status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class ProductType(str, Enum):
    """Product type enumeration"""
    PRODUCT = "product"
    SERVICE = "service"
    DIGITAL = "digital"
    SUBSCRIPTION = "subscription"


# Base Schemas
class ProductBase(BaseModel):
    """Base product schema with common fields"""
    code: str = Field(..., min_length=1, max_length=100, description="商品コード")
    name: str = Field(..., min_length=1, max_length=300, description="商品名")
    name_en: Optional[str] = Field(None, max_length=300, description="英語名")
    description: Optional[str] = Field(None, max_length=2000, description="商品説明")
    
    # Product details
    sku: Optional[str] = Field(None, max_length=100, description="SKU")
    barcode: Optional[str] = Field(None, max_length=100, description="バーコード")
    product_type: ProductType = Field(default=ProductType.PRODUCT, description="商品タイプ")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="ステータス")
    
    # Pricing
    standard_price: Decimal = Field(default=Decimal('0'), ge=0, description="標準価格")
    cost_price: Optional[Decimal] = Field(None, ge=0, description="原価")
    selling_price: Optional[Decimal] = Field(None, ge=0, description="販売価格")
    minimum_price: Optional[Decimal] = Field(None, ge=0, description="最低価格")
    
    # Physical properties
    unit: str = Field(default="個", max_length=20, description="単位")
    weight: Optional[Decimal] = Field(None, ge=0, description="重量(kg)")
    length: Optional[Decimal] = Field(None, ge=0, description="長さ(cm)")
    width: Optional[Decimal] = Field(None, ge=0, description="幅(cm)")
    height: Optional[Decimal] = Field(None, ge=0, description="高さ(cm)")
    
    # Stock management
    is_stock_managed: bool = Field(default=True, description="在庫管理対象")
    minimum_stock_level: Optional[Decimal] = Field(None, ge=0, description="最低在庫レベル")
    reorder_point: Optional[Decimal] = Field(None, ge=0, description="発注点")
    
    # Status and visibility
    is_active: bool = Field(default=True, description="アクティブ")
    is_sellable: bool = Field(default=True, description="販売可能")
    is_purchasable: bool = Field(default=True, description="購買可能")
    
    # Additional info
    manufacturer: Optional[str] = Field(None, max_length=200, description="製造元")
    brand: Optional[str] = Field(None, max_length=200, description="ブランド")
    model_number: Optional[str] = Field(None, max_length=100, description="型番")
    warranty_period: Optional[int] = Field(None, ge=0, description="保証期間(月)")
    
    # Media
    image_url: Optional[str] = Field(None, max_length=500, description="画像URL")
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="サムネイルURL")
    
    # Notes
    notes: Optional[str] = Field(None, max_length=2000, description="備考")
    internal_notes: Optional[str] = Field(None, max_length=2000, description="内部メモ")

    @validator('selling_price')
    def validate_selling_price(cls, v, values):
        """販売価格が原価より高いことを確認"""
        if v is not None and 'cost_price' in values and values['cost_price'] is not None:
            if v < values['cost_price']:
                raise ValueError('販売価格は原価以上である必要があります')
        return v

    @validator('minimum_price')
    def validate_minimum_price(cls, v, values):
        """最低価格が原価以上であることを確認"""
        if v is not None and 'cost_price' in values and values['cost_price'] is not None:
            if v < values['cost_price']:
                raise ValueError('最低価格は原価以上である必要があります')
        return v


class ProductCreate(ProductBase):
    """Product creation schema"""
    organization_id: int = Field(..., description="組織ID")
    category_id: Optional[int] = Field(None, description="カテゴリID")


class ProductUpdate(BaseModel):
    """Product update schema - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    name_en: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = Field(None, max_length=2000)
    
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    product_type: Optional[ProductType] = None
    status: Optional[ProductStatus] = None
    
    standard_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    minimum_price: Optional[Decimal] = Field(None, ge=0)
    
    unit: Optional[str] = Field(None, max_length=20)
    weight: Optional[Decimal] = Field(None, ge=0)
    length: Optional[Decimal] = Field(None, ge=0)
    width: Optional[Decimal] = Field(None, ge=0)
    height: Optional[Decimal] = Field(None, ge=0)
    
    is_stock_managed: Optional[bool] = None
    minimum_stock_level: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[Decimal] = Field(None, ge=0)
    
    is_active: Optional[bool] = None
    is_sellable: Optional[bool] = None
    is_purchasable: Optional[bool] = None
    
    manufacturer: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=200)
    model_number: Optional[str] = Field(None, max_length=100)
    warranty_period: Optional[int] = Field(None, ge=0)
    
    image_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    
    notes: Optional[str] = Field(None, max_length=2000)
    internal_notes: Optional[str] = Field(None, max_length=2000)
    
    category_id: Optional[int] = None


class ProductResponse(ProductBase):
    """Product response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    organization_id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    display_name: Optional[str] = None
    is_available: Optional[bool] = None
    effective_selling_price: Optional[Decimal] = None
    profit_margin: Optional[Decimal] = None


class ProductSearchResponse(BaseModel):
    """Optimized schema for search results"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    code: str
    name: str
    standard_price: Decimal
    status: str
    is_active: bool
    image_url: Optional[str] = None


class ProductWithCategory(ProductResponse):
    """Product response with category information"""
    category: Optional['ProductCategoryResponse'] = None


# Category Schemas
class ProductCategoryBase(BaseModel):
    """Base category schema"""
    code: str = Field(..., min_length=1, max_length=50, description="カテゴリコード")
    name: str = Field(..., min_length=1, max_length=200, description="カテゴリ名")
    name_en: Optional[str] = Field(None, max_length=200, description="英語名")
    description: Optional[str] = Field(None, max_length=1000, description="説明")
    
    is_active: bool = Field(default=True, description="アクティブ")
    sort_order: int = Field(default=0, description="ソート順")


class ProductCategoryCreate(ProductCategoryBase):
    """Category creation schema"""
    organization_id: int = Field(..., description="組織ID")
    parent_id: Optional[int] = Field(None, description="親カテゴリID")


class ProductCategoryUpdate(BaseModel):
    """Category update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    parent_id: Optional[int] = None


class ProductCategoryResponse(ProductCategoryBase):
    """Category response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    organization_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Stock Management Schemas
class StockAdjustmentRequest(BaseModel):
    """Stock adjustment request schema"""
    quantity: int = Field(..., description="調整数量 (正数=入庫、負数=出庫)")
    reason: str = Field(..., min_length=1, max_length=200, description="調整理由")
    notes: Optional[str] = Field(None, max_length=500, description="備考")


class StockAdjustmentResponse(BaseModel):
    """Stock adjustment response schema"""
    product_id: int
    old_stock: int
    new_stock: int
    adjusted_by: int
    reason: str
    notes: Optional[str] = None
    adjusted_at: datetime = Field(default_factory=datetime.utcnow)


# Filter and Search Schemas
class ProductFilterParams(BaseModel):
    """Product filtering parameters"""
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[ProductStatus] = None
    product_type: Optional[ProductType] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    manufacturer: Optional[str] = None
    brand: Optional[str] = None


class ProductSearchRequest(BaseModel):
    """Product search request schema"""
    query: str = Field(..., min_length=1, max_length=200, description="検索キーワード")
    filters: Optional[ProductFilterParams] = None
    limit: int = Field(default=50, ge=1, le=200, description="取得件数")


# Statistics Schemas
class ProductStatistics(BaseModel):
    """Product statistics response schema"""
    total_products: int
    active_products: int
    inactive_products: int
    status_breakdown: Dict[str, int]
    type_breakdown: Dict[str, int]
    category_breakdown: Optional[Dict[str, int]] = None
    price_ranges: Optional[Dict[str, int]] = None
    generated_at: datetime


class CategoryStatistics(BaseModel):
    """Category statistics response schema"""
    category_id: int
    category_name: str
    product_count: int
    active_product_count: int
    average_price: Optional[Decimal] = None
    total_value: Optional[Decimal] = None


# Price History Schemas
class PriceHistoryItem(BaseModel):
    """Price history item schema"""
    model_config = ConfigDict(from_attributes=True)
    
    old_price: Decimal
    new_price: Decimal
    price_type: str
    changed_at: datetime
    change_reason: Optional[str] = None


class PriceHistoryResponse(BaseModel):
    """Price history response schema"""
    product_id: int
    product_code: str
    product_name: str
    history: List[PriceHistoryItem]


# Bulk Operations Schemas
class BulkProductCreate(BaseModel):
    """Bulk product creation schema"""
    products: List[ProductCreate] = Field(..., min_items=1, max_items=100)


class BulkProductUpdate(BaseModel):
    """Bulk product update schema"""
    updates: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100)


class BulkOperationResult(BaseModel):
    """Bulk operation result schema"""
    total_processed: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []


class BulkImportRequest(BaseModel):
    """Bulk import request schema"""
    file_url: str = Field(..., description="Import file URL")
    file_type: str = Field(..., pattern="^(csv|xlsx)$", description="File type")
    organization_id: int = Field(..., description="Organization ID")
    mapping: Dict[str, str] = Field(..., description="Field mapping")


# Validation Schemas
class ProductValidationResult(BaseModel):
    """Product validation result schema"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class ProductCodeValidationRequest(BaseModel):
    """Product code validation request"""
    code: str = Field(..., min_length=1, max_length=100)
    organization_id: int


class ProductCodeValidationResponse(BaseModel):
    """Product code validation response"""
    code: str
    is_available: bool
    suggestion: Optional[str] = None


# Export Schemas  
class ProductExportRequest(BaseModel):
    """Product export request schema"""
    format: str = Field(..., pattern="^(csv|xlsx|pdf)$", description="Export format")
    filters: Optional[ProductFilterParams] = None
    fields: Optional[List[str]] = None
    organization_id: int


class ProductExportResponse(BaseModel):
    """Product export response schema"""
    file_url: str
    file_size: int
    record_count: int
    generated_at: datetime
    expires_at: datetime


# Update ProductCategoryResponse forward reference
ProductWithCategory.model_rebuild()