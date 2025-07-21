"""Inventory management Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class CategoryBase(BaseModel):
    """Base category schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class Category(CategoryBase):
    """Category response schema."""
    
    id: int
    organization_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CategoryWithChildren(Category):
    """Category with children."""
    
    children: List[Category] = []


class ProductBase(BaseModel):
    """Base product schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    track_quantity: bool = True
    minimum_stock: int = Field(default=0, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[str] = Field(None, max_length=100)
    unit_of_measure: str = Field(default="each", max_length=50)
    is_active: bool = True
    is_serialized: bool = False

    @validator('maximum_stock')
    def validate_maximum_stock(cls, v, values):
        """Validate maximum stock is greater than minimum stock."""
        if v is not None and 'minimum_stock' in values:
            minimum = values['minimum_stock']
            if v < minimum:
                raise ValueError('Maximum stock must be greater than or equal to minimum stock')
        return v


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    track_quantity: Optional[bool] = None
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[str] = Field(None, max_length=100)
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_serialized: Optional[bool] = None


class Product(ProductBase):
    """Product response schema."""
    
    id: int
    organization_id: Optional[int]
    current_stock: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProductWithCategory(Product):
    """Product with category information."""
    
    category: Optional[Category] = None


class StockMovementBase(BaseModel):
    """Base stock movement schema."""
    
    product_id: int
    movement_type: str = Field(..., regex="^(in|out|adjustment|transfer|return)$")
    quantity: int = Field(..., ne=0)  # Cannot be zero
    reference_number: Optional[str] = Field(None, max_length=100)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

    @validator('quantity')
    def validate_quantity(cls, v, values):
        """Validate quantity based on movement type."""
        if 'movement_type' in values:
            movement_type = values['movement_type']
            if movement_type in ['in', 'return'] and v < 0:
                raise ValueError('Quantity must be positive for incoming movements')
            elif movement_type == 'out' and v > 0:
                raise ValueError('Quantity must be negative for outgoing movements')
        return v


class StockMovementCreate(StockMovementBase):
    """Schema for creating a stock movement."""
    pass


class StockMovement(StockMovementBase):
    """Stock movement response schema."""
    
    id: int
    previous_stock: int
    new_stock: int
    total_cost: Optional[Decimal]
    organization_id: Optional[int]
    user_id: Optional[int]
    movement_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockMovementWithProduct(StockMovement):
    """Stock movement with product information."""
    
    product: Product


class ProductSerialBase(BaseModel):
    """Base product serial schema."""
    
    product_id: int
    serial_number: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="available", regex="^(available|sold|reserved|defective|returned)$")
    location: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[str] = Field(None, max_length=255)
    manufactured_date: Optional[datetime] = None
    warranty_expires: Optional[datetime] = None


class ProductSerialCreate(ProductSerialBase):
    """Schema for creating a product serial."""
    pass


class ProductSerialUpdate(BaseModel):
    """Schema for updating a product serial."""
    
    status: Optional[str] = Field(None, regex="^(available|sold|reserved|defective|returned)$")
    location: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[str] = Field(None, max_length=255)
    manufactured_date: Optional[datetime] = None
    warranty_expires: Optional[datetime] = None


class ProductSerial(ProductSerialBase):
    """Product serial response schema."""
    
    id: int
    organization_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class InventoryLocationBase(BaseModel):
    """Base inventory location schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    location_type: str = Field(default="warehouse", regex="^(warehouse|aisle|rack|shelf|bin)$")
    address: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: bool = True


class InventoryLocationCreate(InventoryLocationBase):
    """Schema for creating an inventory location."""
    pass


class InventoryLocationUpdate(BaseModel):
    """Schema for updating an inventory location."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    location_type: Optional[str] = Field(None, regex="^(warehouse|aisle|rack|shelf|bin)$")
    address: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class InventoryLocation(InventoryLocationBase):
    """Inventory location response schema."""
    
    id: int
    organization_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class InventoryLocationWithChildren(InventoryLocation):
    """Inventory location with children."""
    
    children: List[InventoryLocation] = []


# Inventory Reports and Analytics
class InventoryReport(BaseModel):
    """Inventory summary report."""
    
    total_products: int
    total_value: Decimal
    low_stock_products: int
    out_of_stock_products: int
    categories_count: int
    movements_today: int
    organization_id: Optional[int]
    generated_at: datetime


class ProductStockSummary(BaseModel):
    """Product stock summary."""
    
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    minimum_stock: int
    maximum_stock: Optional[int]
    stock_status: str  # 'ok', 'low', 'out', 'excess'
    last_movement_date: Optional[datetime]
    total_value: Decimal


class StockMovementFilters(BaseModel):
    """Filters for stock movement queries."""
    
    product_id: Optional[int] = None
    movement_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    user_id: Optional[int] = None
    organization_id: Optional[int] = None


class ProductFilters(BaseModel):
    """Filters for product queries."""
    
    category_id: Optional[int] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    is_active: Optional[bool] = None
    track_quantity: Optional[bool] = None
    low_stock: Optional[bool] = None  # Products below minimum stock
    out_of_stock: Optional[bool] = None  # Products with zero stock
    search: Optional[str] = None  # Search in name, sku, description