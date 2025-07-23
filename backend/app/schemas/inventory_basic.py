"""
Basic inventory schemas for ERP v17.0
Comprehensive inventory management schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.inventory import InventoryStatus, MovementType


class WarehouseBase(BaseModel):
    """Base warehouse schema."""

    code: str = Field(..., min_length=1, max_length=50, description="Warehouse code")
    name: str = Field(..., min_length=1, max_length=200, description="Warehouse name")
    description: Optional[str] = Field(None, description="Warehouse description")
    organization_id: int = Field(..., description="Organization ID")

    # Location details
    address: Optional[str] = Field(None, max_length=500, description="Street address")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    city: Optional[str] = Field(None, max_length=100, description="City")
    prefecture: Optional[str] = Field(None, max_length=50, description="Prefecture")

    # Contact information
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    manager_name: Optional[str] = Field(None, max_length=100, description="Manager name")

    # Specifications
    total_area: Optional[Decimal] = Field(None, ge=0, description="Total area in m²")
    storage_capacity: Optional[Decimal] = Field(None, ge=0, description="Storage capacity")
    temperature_controlled: bool = Field(False, description="Temperature controlled facility")

    # Status
    is_default: bool = Field(False, description="Default warehouse")
    is_active: bool = Field(True, description="Active status")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Warehouse code cannot be empty")
        return v.strip().upper()


class WarehouseCreate(WarehouseBase):
    """Warehouse creation schema."""



class WarehouseUpdate(BaseModel):
    """Warehouse update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    prefecture: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    manager_name: Optional[str] = Field(None, max_length=100)
    total_area: Optional[Decimal] = Field(None, ge=0)
    storage_capacity: Optional[Decimal] = Field(None, ge=0)
    temperature_controlled: Optional[bool] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    """Warehouse response schema."""

    id: int = Field(..., description="Warehouse ID")
    full_address: str = Field(..., description="Full formatted address")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class InventoryItemBase(BaseModel):
    """Base inventory item schema."""

    product_id: int = Field(..., description="Product ID")
    warehouse_id: int = Field(..., description="Warehouse ID")
    organization_id: int = Field(..., description="Organization ID")

    # Quantities
    quantity_on_hand: Decimal = Field(0, ge=0, description="Quantity on hand")
    quantity_reserved: Decimal = Field(0, ge=0, description="Quantity reserved")
    quantity_in_transit: Decimal = Field(0, ge=0, description="Quantity in transit")

    # Cost information
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, description="Cost per unit")
    average_cost: Optional[Decimal] = Field(None, ge=0, description="Average cost")

    # Location within warehouse
    location_code: Optional[str] = Field(
        None, max_length=50, description="Location code"
    )
    zone: Optional[str] = Field(None, max_length=50, description="Zone")

    # Stock levels
    minimum_level: Optional[Decimal] = Field(
        None, ge=0, description="Minimum stock level"
    )
    reorder_point: Optional[Decimal] = Field(None, ge=0, description="Reorder point")

    # Status
    status: str = Field(InventoryStatus.AVAILABLE.value, description="Inventory status")

    # Dates for tracking
    expiry_date: Optional[date] = Field(None, description="Expiry date")

    # Batch tracking
    lot_number: Optional[str] = Field(None, max_length=100, description="Lot number")
    batch_number: Optional[str] = Field(
        None, max_length=100, description="Batch number"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in [s.value for s in InventoryStatus]:
            raise ValueError("Invalid inventory status")
        return v


class InventoryItemCreate(InventoryItemBase):
    """Inventory item creation schema."""



class InventoryItemUpdate(BaseModel):
    """Inventory item update schema."""

    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    location_code: Optional[str] = Field(None, max_length=50)
    zone: Optional[str] = Field(None, max_length=50)
    minimum_level: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = None
    expiry_date: Optional[date] = None
    lot_number: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v and v not in [s.value for s in InventoryStatus]:
            raise ValueError("Invalid inventory status")
        return v


class InventoryItemResponse(InventoryItemBase):
    """Inventory item response schema."""

    id: int = Field(..., description="Inventory item ID")
    quantity_available: Decimal = Field(..., description="Quantity available")
    total_cost: Optional[Decimal] = Field(None, description="Total cost value")
    last_received_date: Optional[datetime] = Field(
        None, description="Last received date"
    )
    last_issued_date: Optional[datetime] = Field(None, description="Last issued date")
    is_low_stock: bool = Field(..., description="Is stock level low")
    needs_reorder: bool = Field(..., description="Needs reorder")
    is_expired: bool = Field(..., description="Is expired")
    days_until_expiry: Optional[int] = Field(None, description="Days until expiry")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class StockMovementBase(BaseModel):
    """Base stock movement schema."""

    inventory_item_id: int = Field(..., description="Inventory item ID")
    product_id: int = Field(..., description="Product ID")
    warehouse_id: int = Field(..., description="Warehouse ID")
    organization_id: int = Field(..., description="Organization ID")

    # Movement details
    movement_type: str = Field(..., description="Movement type")
    quantity: Decimal = Field(..., description="Movement quantity")

    # Cost information
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost")

    # Reference information
    reference_type: Optional[str] = Field(
        None, max_length=50, description="Reference type"
    )
    reference_number: Optional[str] = Field(
        None, max_length=100, description="Reference number"
    )
    reference_id: Optional[int] = Field(None, description="Reference ID")

    # Movement details
    reason: Optional[str] = Field(None, max_length=200, description="Movement reason")
    notes: Optional[str] = Field(None, description="Additional notes")

    # Location details
    from_location: Optional[str] = Field(
        None, max_length=100, description="From location"
    )
    to_location: Optional[str] = Field(None, max_length=100, description="To location")
    lot_number: Optional[str] = Field(None, max_length=100, description="Lot number")

    @field_validator("movement_type")
    @classmethod
    def validate_movement_type(cls, v):
        if v not in [t.value for t in MovementType]:
            raise ValueError("Invalid movement type")
        return v


class StockMovementCreate(StockMovementBase):
    """Stock movement creation schema."""



class StockMovementResponse(StockMovementBase):
    """Stock movement response schema."""

    id: int = Field(..., description="Stock movement ID")
    transaction_number: str = Field(..., description="Transaction number")
    movement_date: datetime = Field(..., description="Movement date")
    quantity_before: Decimal = Field(..., description="Quantity before movement")
    quantity_after: Decimal = Field(..., description="Quantity after movement")
    total_cost: Optional[Decimal] = Field(None, description="Total cost")
    performed_by: Optional[int] = Field(None, description="Performed by user ID")
    is_posted: bool = Field(..., description="Is posted")
    is_reversed: bool = Field(..., description="Is reversed")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class StockAdjustmentCreate(BaseModel):
    """Stock adjustment creation schema."""

    inventory_item_id: int = Field(..., description="Inventory item ID")
    new_quantity: Decimal = Field(
        ..., ge=0, description="New quantity after adjustment"
    )
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost")
    reason: str = Field(
        ..., min_length=1, max_length=200, description="Adjustment reason"
    )
    notes: Optional[str] = Field(None, description="Additional notes")


class StockReservationCreate(BaseModel):
    """Stock reservation creation schema."""

    inventory_item_id: int = Field(..., description="Inventory item ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity to reserve")
    reference_type: Optional[str] = Field(
        None, max_length=50, description="Reference type"
    )
    reference_number: Optional[str] = Field(
        None, max_length=100, description="Reference number"
    )
    reference_id: Optional[int] = Field(None, description="Reference ID")


class StockTransferCreate(BaseModel):
    """Stock transfer creation schema."""

    from_inventory_item_id: int = Field(..., description="Source inventory item ID")
    to_warehouse_id: int = Field(..., description="Destination warehouse ID")
    quantity: Decimal = Field(..., gt=0, description="Quantity to transfer")
    reason: Optional[str] = Field(None, max_length=200, description="Transfer reason")
    notes: Optional[str] = Field(None, description="Additional notes")


class InventoryValueResponse(BaseModel):
    """Inventory value response schema."""

    product_id: int = Field(..., description="Product ID")
    product_code: str = Field(..., description="Product code")
    product_name: str = Field(..., description="Product name")
    warehouse_id: int = Field(..., description="Warehouse ID")
    warehouse_name: str = Field(..., description="Warehouse name")
    quantity_on_hand: Decimal = Field(..., description="Quantity on hand")
    average_cost: Optional[Decimal] = Field(None, description="Average cost per unit")
    total_value: Optional[Decimal] = Field(None, description="Total inventory value")


class InventoryStatistics(BaseModel):
    """Inventory statistics schema."""

    total_items: int = Field(..., description="Total inventory items")
    active_items: int = Field(..., description="Active inventory items")
    total_stock_value: float = Field(..., description="Total stock value")
    low_stock_items: int = Field(..., description="Low stock items count")
    by_status: dict = Field(..., description="Items count by status")
    warehouses_count: int = Field(..., description="Number of warehouses")


class LowStockAlert(BaseModel):
    """Low stock alert schema."""

    product_id: int = Field(..., description="Product ID")
    product_code: str = Field(..., description="Product code")
    product_name: str = Field(..., description="Product name")
    warehouse_id: int = Field(..., description="Warehouse ID")
    warehouse_name: str = Field(..., description="Warehouse name")
    current_quantity: Decimal = Field(..., description="Current quantity")
    minimum_level: Decimal = Field(..., description="Minimum stock level")
    reorder_point: Optional[Decimal] = Field(None, description="Reorder point")
    needs_reorder: bool = Field(..., description="Needs reorder")


class ExpiryAlert(BaseModel):
    """Expiry alert schema."""

    product_id: int = Field(..., description="Product ID")
    product_code: str = Field(..., description="Product code")
    product_name: str = Field(..., description="Product name")
    warehouse_id: int = Field(..., description="Warehouse ID")
    warehouse_name: str = Field(..., description="Warehouse name")
    quantity: Decimal = Field(..., description="Quantity that will expire")
    expiry_date: date = Field(..., description="Expiry date")
    days_until_expiry: int = Field(..., description="Days until expiry")
    lot_number: Optional[str] = Field(None, description="Lot number")
    batch_number: Optional[str] = Field(None, description="Batch number")


class InventoryItemBasic(BaseModel):
    """Basic inventory item information."""

    id: int = Field(..., description="Inventory item ID")
    product_id: int = Field(..., description="Product ID")
    product_code: str = Field(..., description="Product code")
    product_name: str = Field(..., description="Product name")
    warehouse_id: int = Field(..., description="Warehouse ID")
    warehouse_name: str = Field(..., description="Warehouse name")
    quantity_on_hand: Decimal = Field(..., description="Quantity on hand")
    quantity_available: Decimal = Field(..., description="Available quantity")
    status: str = Field(..., description="Inventory status")

    class Config:
        from_attributes = True
