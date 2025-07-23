"""
Basic product schemas for ERP v17.0
Simplified product management schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.product import ProductStatus, ProductType


class ProductCategoryBase(BaseModel):
    """Base product category schema."""

    code: str = Field(..., min_length=1, max_length=50, description="Category code")
    name: str = Field(..., min_length=1, max_length=200, description="Category name")
    name_en: Optional[str] = Field(None, max_length=200, description="Name in English")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    organization_id: int = Field(..., description="Organization ID")
    is_active: bool = Field(True, description="Active status")
    sort_order: int = Field(0, description="Sort order")


class ProductCategoryCreate(ProductCategoryBase):
    """Product category creation schema."""



class ProductCategoryUpdate(BaseModel):
    """Product category update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ProductCategoryResponse(ProductCategoryBase):
    """Product category response schema."""

    id: int = Field(..., description="Category ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Base product schema."""

    code: str = Field(..., min_length=1, max_length=100, description="Product code")
    name: str = Field(..., min_length=1, max_length=300, description="Product name")
    name_en: Optional[str] = Field(None, max_length=300, description="Name in English")
    description: Optional[str] = Field(None, description="Product description")
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, max_length=100, description="Barcode")
    product_type: str = Field(ProductType.PRODUCT.value, description="Product type")
    status: str = Field(ProductStatus.ACTIVE.value, description="Product status")

    # Organization and category
    category_id: Optional[int] = Field(None, description="Category ID")
    organization_id: int = Field(..., description="Organization ID")

    # Pricing
    standard_price: Decimal = Field(0, ge=0, description="Standard price")
    cost_price: Optional[Decimal] = Field(None, ge=0, description="Cost price")
    selling_price: Optional[Decimal] = Field(None, ge=0, description="Selling price")
    minimum_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price")

    # Physical properties
    unit: str = Field("個", max_length=20, description="Unit of measure")
    weight: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")

    # Stock management
    is_stock_managed: bool = Field(True, description="Is stock managed")
    minimum_stock_level: Optional[Decimal] = Field(
        None, ge=0, description="Minimum stock level"
    )
    reorder_point: Optional[Decimal] = Field(None, ge=0, description="Reorder point")

    # Tax
    tax_rate: Decimal = Field(Decimal("0.1000"), ge=0, le=1, description="Tax rate")
    tax_included: bool = Field(False, description="Tax included in price")

    # Status flags
    is_active: bool = Field(True, description="Active status")
    is_sellable: bool = Field(True, description="Can be sold")
    is_purchasable: bool = Field(True, description="Can be purchased")

    # Additional info
    manufacturer: Optional[str] = Field(
        None, max_length=200, description="Manufacturer"
    )
    brand: Optional[str] = Field(None, max_length=200, description="Brand")
    model_number: Optional[str] = Field(None, max_length=100, description="Model number")
    warranty_period: Optional[int] = Field(None, ge=0, description="Warranty period in months")

    # Media
    image_url: Optional[str] = Field(None, max_length=500, description="Image URL")
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="Thumbnail URL")

    # Notes
    notes: Optional[str] = Field(None, description="Public notes")
    internal_notes: Optional[str] = Field(None, description="Internal notes")

    @field_validator('product_type')
    @classmethod
    def validate_product_type(cls, v):
        if v not in [t.value for t in ProductType]:
            raise ValueError("Invalid product type")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in [s.value for s in ProductStatus]:
            raise ValueError("Invalid product status")
        return v

    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Product code cannot be empty")
        return v.strip().upper()


class ProductCreate(ProductBase):
    """Product creation schema."""



class ProductUpdate(BaseModel):
    """Product update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=300)
    name_en: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    product_type: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
    standard_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    minimum_price: Optional[Decimal] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    weight: Optional[Decimal] = Field(None, ge=0)
    is_stock_managed: Optional[bool] = None
    minimum_stock_level: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    tax_included: Optional[bool] = None
    is_active: Optional[bool] = None
    is_sellable: Optional[bool] = None
    is_purchasable: Optional[bool] = None
    manufacturer: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=200)
    model_number: Optional[str] = Field(None, max_length=100)
    warranty_period: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

    @field_validator('product_type')
    @classmethod
    def validate_product_type(cls, v):
        if v and v not in [t.value for t in ProductType]:
            raise ValueError("Invalid product type")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in [s.value for s in ProductStatus]:
            raise ValueError("Invalid product status")
        return v


class ProductResponse(ProductBase):
    """Product response schema."""

    id: int = Field(..., description="Product ID")
    display_name: str = Field(..., description="Display name")
    effective_selling_price: Decimal = Field(..., description="Effective selling price")
    is_available: bool = Field(..., description="Available for sale")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class ProductBasic(BaseModel):
    """Basic product information."""

    id: int = Field(..., description="Product ID")
    code: str = Field(..., description="Product code")
    name: str = Field(..., description="Product name")
    display_name: str = Field(..., description="Display name")
    sku: Optional[str] = Field(None, description="SKU")
    standard_price: Decimal = Field(..., description="Standard price")
    is_active: bool = Field(..., description="Active status")

    class Config:
        from_attributes = True


class ProductContext(BaseModel):
    """ERP product context - v17.0."""

    product_id: int
    code: str
    name: str
    display_name: str
    sku: Optional[str]
    barcode: Optional[str]
    product_type: str
    status: str
    is_available: bool
    category_id: Optional[int]
    organization_id: int
    pricing: dict
    stock_managed: bool
    unit: str
    tax_rate: float
    is_active: bool
