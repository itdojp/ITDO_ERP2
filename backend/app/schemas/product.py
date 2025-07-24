"""
Product Schemas - CC02 v49.0 TDD Implementation
Pydantic schemas for API request/response validation
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """Schema for creating a product"""

    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    sku: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = Field(default=True)


class ProductUpdate(BaseModel):
    """Schema for updating a product"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Schema for product API responses"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price: float
    sku: str
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """Schema for paginated product list responses"""

    items: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class BulkProductCreate(BaseModel):
    """Schema for bulk product creation"""

    products: List[ProductCreate]


class BulkProductUpdate(BaseModel):
    """Schema for bulk product updates"""

    updates: List[dict]  # List of update objects with id and fields to update


class CategoryResponse(BaseModel):
    """Schema for category statistics"""

    name: str
    count: int


class ProductStatistics(BaseModel):
    """Schema for product statistics"""

    total_products: int
    active_products: int
    inactive_products: int
    categories: List[CategoryResponse]
    average_price: float
    total_value: float


class PriceHistoryItem(BaseModel):
    """Schema for price history items"""

    price: float
    changed_at: datetime
    changed_by: Optional[str] = None


class PriceHistoryResponse(BaseModel):
    """Schema for price history response"""

    product_id: str
    history: List[PriceHistoryItem]


class BulkCreateResponse(BaseModel):
    """Schema for bulk creation response"""

    created: int
    failed: int
    details: List[dict]


class BulkUpdateResponse(BaseModel):
    """Schema for bulk update response"""

    updated: int
    failed: int
    details: List[dict]


class InventoryResponse(BaseModel):
    """Schema for inventory response"""

    total_stock: int
    available_stock: int
    reserved_stock: int
    locations: List[dict]
