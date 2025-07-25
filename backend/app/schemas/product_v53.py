"""
CC02 v53.0 Product Schemas - Issue #568
10-Day ERP Business API Implementation Sprint - Day 1-2
Enhanced Product Management API Schemas
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class ProductStatus(str, Enum):
    """Product status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    DISCONTINUED = "discontinued"
    DRAFT = "draft"


class ProductType(str, Enum):
    """Product type enumeration"""
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    SUBSCRIPTION = "subscription"


class UnitOfMeasure(str, Enum):
    """Unit of measure enumeration"""
    PIECE = "piece"
    KG = "kg"
    LITER = "liter"
    METER = "meter"
    HOUR = "hour"
    SET = "set"


# Product Dimensions Schema
class ProductDimensions(BaseModel):
    """Product physical dimensions"""
    length: Optional[Decimal] = Field(None, ge=0, description="Length in cm")
    width: Optional[Decimal] = Field(None, ge=0, description="Width in cm")
    height: Optional[Decimal] = Field(None, ge=0, description="Height in cm")
    weight: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")


# Category Schemas
class CategoryCreate(BaseModel):
    """Schema for creating product category"""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[str] = None
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)


class CategoryResponse(BaseModel):
    """Schema for category response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime


# Enhanced Product Schemas
class ProductCreate(BaseModel):
    """Enhanced schema for creating a product"""
    # Basic Information
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    
    # Classification
    category_id: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    product_type: ProductType = Field(default=ProductType.PHYSICAL)
    
    # Pricing
    price: Decimal = Field(..., gt=0, decimal_places=2)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    
    # Physical Properties
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")
    color: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    
    # Business Properties
    unit_of_measure: UnitOfMeasure = Field(default=UnitOfMeasure.PIECE)
    min_order_quantity: int = Field(default=1, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)
    lead_time_days: Optional[int] = Field(None, ge=0)
    
    # Inventory Management
    track_inventory: bool = Field(default=True)
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    
    # Status and Features
    status: ProductStatus = Field(default=ProductStatus.ACTIVE)
    is_active: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    is_digital: bool = Field(default=False)
    
    # Compliance and Quality
    warranty_months: Optional[int] = Field(None, ge=0, le=120)
    requires_shipping: bool = Field(default=True)
    is_taxable: bool = Field(default=True)
    tax_category: Optional[str] = Field(None, max_length=50)
    
    # Identification
    barcode: Optional[str] = Field(None, max_length=50)
    internal_code: Optional[str] = Field(None, max_length=50)
    manufacturer_code: Optional[str] = Field(None, max_length=50)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('max_order_quantity')
    @classmethod
    def validate_max_order_quantity(cls, v, info):
        if v is not None and 'min_order_quantity' in info.data:
            if v < info.data['min_order_quantity']:
                raise ValueError('max_order_quantity must be >= min_order_quantity')
        return v
    
    @field_validator('max_stock_level')
    @classmethod
    def validate_max_stock_level(cls, v, info):
        if v is not None and 'min_stock_level' in info.data:
            if v < info.data['min_stock_level']:
                raise ValueError('max_stock_level must be >= min_stock_level')
        return v


class ProductUpdate(BaseModel):
    """Enhanced schema for updating a product"""
    # Basic Information
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    
    # Classification
    category_id: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    product_type: Optional[ProductType] = None
    
    # Pricing
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=3)
    
    # Physical Properties
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    color: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    
    # Business Properties
    unit_of_measure: Optional[UnitOfMeasure] = None
    min_order_quantity: Optional[int] = Field(None, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)
    lead_time_days: Optional[int] = Field(None, ge=0)
    
    # Inventory Management
    track_inventory: Optional[bool] = None
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    
    # Status and Features
    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    
    # Compliance and Quality
    warranty_months: Optional[int] = Field(None, ge=0, le=120)
    requires_shipping: Optional[bool] = None
    is_taxable: Optional[bool] = None
    tax_category: Optional[str] = Field(None, max_length=50)
    
    # Identification
    barcode: Optional[str] = Field(None, max_length=50)
    internal_code: Optional[str] = Field(None, max_length=50)
    manufacturer_code: Optional[str] = Field(None, max_length=50)
    
    # Metadata
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None


class ProductResponse(BaseModel):
    """Enhanced schema for product API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    # Basic Information
    id: str
    name: str
    sku: str
    description: Optional[str] = None
    
    # Classification
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    product_type: ProductType
    
    # Pricing
    price: Decimal
    cost: Optional[Decimal] = None
    currency: str = "USD"
    
    # Physical Properties
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[Decimal] = None
    color: Optional[str] = None
    material: Optional[str] = None
    
    # Business Properties
    unit_of_measure: UnitOfMeasure
    min_order_quantity: int = 1
    max_order_quantity: Optional[int] = None
    lead_time_days: Optional[int] = None
    
    # Inventory Management
    track_inventory: bool = True
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    reorder_point: Optional[int] = None
    current_stock: Optional[int] = None
    
    # Status and Features
    status: ProductStatus
    is_active: bool = True
    is_featured: bool = False
    is_digital: bool = False
    
    # Compliance and Quality
    warranty_months: Optional[int] = None
    requires_shipping: bool = True
    is_taxable: bool = True
    tax_category: Optional[str] = None
    
    # Identification
    barcode: Optional[str] = None
    internal_code: Optional[str] = None
    manufacturer_code: Optional[str] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """Enhanced schema for paginated product list responses"""
    items: List[ProductResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# Bulk Operations
class BulkProductOperation(BaseModel):
    """Schema for bulk product operations"""
    products: List[ProductCreate]
    validate_only: bool = Field(default=False)
    stop_on_error: bool = Field(default=False)


class BulkOperationResult(BaseModel):
    """Schema for bulk operation results"""
    created_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    created_items: List[ProductResponse] = Field(default_factory=list)
    updated_items: List[ProductResponse] = Field(default_factory=list)
    failed_items: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: Optional[float] = None


# Statistics and Analytics
class CategoryStats(BaseModel):
    """Category statistics"""
    category_id: Optional[str]
    category_name: str
    product_count: int
    total_value: Decimal
    average_price: Decimal


class ProductStatistics(BaseModel):
    """Enhanced product statistics"""
    total_products: int
    active_products: int
    inactive_products: int
    featured_products: int
    digital_products: int
    physical_products: int
    
    # Financial Statistics
    total_inventory_value: Decimal
    average_product_price: Decimal
    highest_price: Decimal
    lowest_price: Decimal
    
    # Category Breakdown
    categories: List[CategoryStats]
    total_categories: int
    
    # Stock Statistics
    out_of_stock_products: int
    low_stock_products: int
    overstocked_products: int
    
    # Performance Metrics
    last_updated: datetime
    calculation_time_ms: float


# Price History
class PriceHistoryItem(BaseModel):
    """Price history item"""
    price: Decimal
    cost: Optional[Decimal] = None
    changed_at: datetime
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class ProductPriceHistory(BaseModel):
    """Product price history response"""
    product_id: str
    product_name: str
    current_price: Decimal
    price_changes: List[PriceHistoryItem]
    total_changes: int


# Inventory Integration
class ProductInventoryLevel(BaseModel):
    """Product inventory level information"""
    product_id: str
    product_name: str
    total_stock: int
    available_stock: int
    reserved_stock: int
    committed_stock: int
    on_order_stock: int
    reorder_point: Optional[int] = None
    last_movement_date: Optional[datetime] = None


class ProductInventoryResponse(BaseModel):
    """Product inventory response"""
    product_id: str
    total_stock: int
    available_stock: int  
    reserved_stock: int
    locations: List[Dict[str, Any]]
    movements: List[Dict[str, Any]]
    last_updated: datetime


# Search and Filtering
class ProductSearchRequest(BaseModel):
    """Product search request"""
    query: Optional[str] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    status: Optional[ProductStatus] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    in_stock_only: bool = Field(default=False)
    
    # Pagination
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=1000)
    
    # Sorting
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# API Response Wrappers
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None


class ProductAPIResponse(APIResponse):
    """Product-specific API response"""
    data: Optional[Union[ProductResponse, ProductListResponse, ProductStatistics]] = None


# Error Schemas
class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    code: str
    value: Optional[Any] = None


class ProductError(BaseModel):
    """Product-specific error response"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    validation_errors: Optional[List[ValidationError]] = None
    timestamp: datetime = Field(default_factory=datetime.now)