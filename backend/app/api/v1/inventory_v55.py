"""
CC02 v55.0 Inventory Management API
Enterprise-grade Inventory Management System
Day 1 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, text, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel, Field, validator, root_validator

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.exceptions import ValidationError, NotFoundError, InsufficientStockError
from app.models.inventory import (
    InventoryLocation, InventoryItem, InventoryMovement, InventoryAdjustment,
    StockAlert, InventorySnapshot, InventoryReservation, InventoryTransfer
)
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.common import PaginationParams, SortParams, FilterParams

router = APIRouter(prefix="/inventory", tags=["inventory-v55"])

# Enums
class MovementType(str, Enum):
    IN = "in"                    # Stock received
    OUT = "out"                  # Stock sold/used
    TRANSFER = "transfer"        # Transfer between locations
    ADJUSTMENT = "adjustment"    # Manual adjustment
    RETURN = "return"           # Customer return
    DAMAGE = "damage"           # Damaged goods
    LOSS = "loss"              # Lost inventory
    FOUND = "found"            # Found inventory
    PRODUCTION = "production"   # Manufacturing input/output
    PURCHASE = "purchase"       # Purchase order received
    SALE = "sale"              # Sale order fulfilled

class MovementReason(str, Enum):
    SALE = "sale"
    PURCHASE = "purchase"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DAMAGE = "damage"
    THEFT = "theft"
    EXPIRY = "expiry"
    PRODUCTION = "production"
    CORRECTION = "correction"
    RECOUNT = "recount"
    OTHER = "other"

class AlertType(str, Enum):
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCK = "overstock"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    NEGATIVE_STOCK = "negative_stock"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"

class TransferStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    STORE = "store"
    DISTRIBUTION_CENTER = "distribution_center"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    VIRTUAL = "virtual"
    QUARANTINE = "quarantine"
    RETURNS = "returns"

# Request/Response Models
class InventoryLocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    location_type: LocationType = Field(default=LocationType.WAREHOUSE)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[UUID] = None
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    capacity: Optional[int] = Field(None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, decimal_places=4)

class InventoryLocationResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    location_type: LocationType
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    manager_id: Optional[UUID]
    manager_name: Optional[str]
    is_active: bool
    is_default: bool
    capacity: Optional[int]
    cost_per_unit: Optional[Decimal]
    total_items: int
    total_value: Decimal
    utilization_percentage: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryItemCreate(BaseModel):
    product_variant_id: UUID
    location_id: UUID
    quantity: int = Field(default=0)
    reserved_quantity: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=0, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    reorder_point: int = Field(default=10, ge=0)
    reorder_quantity: int = Field(default=100, ge=1)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    expiry_date: Optional[date] = None
    batch_number: Optional[str] = Field(None, max_length=100)
    supplier_id: Optional[UUID] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('maximum_stock')
    def validate_maximum_stock(cls, v, values):
        if v is not None and 'minimum_stock' in values and v < values['minimum_stock']:
            raise ValueError('maximum_stock must be greater than or equal to minimum_stock')
        return v

    @validator('reserved_quantity')
    def validate_reserved_quantity(cls, v, values):
        if 'quantity' in values and v > values['quantity']:
            raise ValueError('reserved_quantity cannot exceed total quantity')
        return v

class InventoryItemUpdate(BaseModel):
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, ge=1)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    expiry_date: Optional[date] = None
    batch_number: Optional[str] = Field(None, max_length=100)
    supplier_id: Optional[UUID] = None
    notes: Optional[str] = Field(None, max_length=1000)

class InventoryItemResponse(BaseModel):
    id: UUID
    product_variant_id: UUID
    product_name: str
    variant_name: Optional[str]
    sku: str
    location_id: UUID
    location_name: str
    quantity: int
    reserved_quantity: int
    available_quantity: int
    minimum_stock: int
    maximum_stock: Optional[int]
    reorder_point: int
    reorder_quantity: int
    cost_per_unit: Optional[Decimal]
    total_value: Decimal
    expiry_date: Optional[date]
    batch_number: Optional[str]
    supplier_id: Optional[UUID]
    supplier_name: Optional[str]
    notes: Optional[str]
    stock_status: str
    days_until_expiry: Optional[int]
    last_movement_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryMovementCreate(BaseModel):
    item_id: UUID
    movement_type: MovementType
    quantity: int = Field(..., ne=0)
    reason: MovementReason = Field(default=MovementReason.OTHER)
    reference_number: Optional[str] = Field(None, max_length=100)
    unit_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    notes: Optional[str] = Field(None, max_length=500)
    from_location_id: Optional[UUID] = None
    to_location_id: Optional[UUID] = None

    @validator('quantity')
    def validate_quantity(cls, v, values):
        movement_type = values.get('movement_type')
        if movement_type in [MovementType.OUT, MovementType.DAMAGE, MovementType.LOSS] and v > 0:
            raise ValueError(f'Quantity must be negative for {movement_type} movements')
        elif movement_type in [MovementType.IN, MovementType.FOUND, MovementType.RETURN] and v < 0:
            raise ValueError(f'Quantity must be positive for {movement_type} movements')
        return v

class InventoryMovementResponse(BaseModel):
    id: UUID
    item_id: UUID
    product_name: str
    sku: str
    location_name: str
    movement_type: MovementType
    quantity: int
    reason: MovementReason
    reference_number: Optional[str]
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    notes: Optional[str]
    from_location_id: Optional[UUID]
    from_location_name: Optional[str]
    to_location_id: Optional[UUID]
    to_location_name: Optional[str]
    balance_after: int
    created_by: UUID
    created_by_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryAdjustmentCreate(BaseModel):
    adjustments: List[Dict[str, Any]] = Field(..., min_items=1)
    reason: str = Field(..., max_length=500)
    reference_number: Optional[str] = Field(None, max_length=100)
    approved_by: Optional[UUID] = None

class StockAlertResponse(BaseModel):
    id: UUID
    item_id: UUID
    product_name: str
    sku: str
    location_name: str
    alert_type: AlertType
    current_quantity: int
    threshold_quantity: Optional[int]
    message: str
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[UUID]
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True

class InventoryTransferCreate(BaseModel):
    from_location_id: UUID
    to_location_id: UUID
    items: List[Dict[str, Any]] = Field(..., min_items=1)  # {item_id, quantity}
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    expected_delivery_date: Optional[date] = None

class InventoryTransferResponse(BaseModel):
    id: UUID
    from_location_id: UUID
    from_location_name: str
    to_location_id: UUID
    to_location_name: str
    status: TransferStatus
    reference_number: Optional[str]
    notes: Optional[str]
    items_count: int
    total_value: Decimal
    expected_delivery_date: Optional[date]
    shipped_date: Optional[datetime]
    received_date: Optional[datetime]
    created_by: UUID
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryReportRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location_ids: Optional[List[UUID]] = None
    product_variant_ids: Optional[List[UUID]] = None
    include_movements: bool = Field(default=True)
    include_valuations: bool = Field(default=True)
    group_by: Optional[str] = Field(None, regex="^(location|product|category)$")

# Helper Functions
async def calculate_stock_status(item) -> str:
    """Calculate stock status based on current inventory levels"""
    available = item.quantity - item.reserved_quantity
    
    if available <= 0:
        return "out_of_stock"
    elif available <= item.reorder_point:
        return "low_stock"
    elif item.maximum_stock and available >= item.maximum_stock:
        return "overstock"
    else:
        return "in_stock"

async def validate_location_exists(db: AsyncSession, location_id: UUID) -> bool:
    """Validate that a location exists and is active"""
    result = await db.execute(
        select(InventoryLocation).where(
            and_(InventoryLocation.id == location_id, InventoryLocation.is_active == True)
        )
    )
    return result.scalar_one_or_none() is not None

async def validate_product_variant_exists(db: AsyncSession, variant_id: UUID) -> bool:
    """Validate that a product variant exists"""
    result = await db.execute(
        select(ProductVariant).where(ProductVariant.id == variant_id)
    )
    return result.scalar_one_or_none() is not None

async def create_stock_alert(
    db: AsyncSession,
    item: InventoryItem,
    alert_type: AlertType,
    message: str
) -> None:
    """Create a stock alert for an inventory item"""
    # Check if alert already exists
    existing_alert = await db.execute(
        select(StockAlert).where(
            and_(
                StockAlert.item_id == item.id,
                StockAlert.alert_type == alert_type,
                StockAlert.status == AlertStatus.ACTIVE
            )
        )
    )
    
    if existing_alert.scalar_one_or_none():
        return  # Alert already exists
    
    alert = StockAlert(
        id=uuid4(),
        item_id=item.id,
        alert_type=alert_type,
        current_quantity=item.quantity,
        threshold_quantity=item.reorder_point if alert_type == AlertType.LOW_STOCK else None,
        message=message,
        status=AlertStatus.ACTIVE,
        created_at=datetime.utcnow()
    )
    
    db.add(alert)

async def check_and_create_alerts(db: AsyncSession, item: InventoryItem) -> None:
    """Check inventory levels and create alerts if necessary"""
    available = item.quantity - item.reserved_quantity
    
    # Check for low stock
    if available <= item.reorder_point and available > 0:
        await create_stock_alert(
            db, item, AlertType.LOW_STOCK,
            f"Stock level ({available}) is below reorder point ({item.reorder_point})"
        )
    
    # Check for out of stock
    elif available <= 0:
        await create_stock_alert(
            db, item, AlertType.OUT_OF_STOCK,
            f"Item is out of stock"
        )
    
    # Check for overstock
    elif item.maximum_stock and available >= item.maximum_stock:
        await create_stock_alert(
            db, item, AlertType.OVERSTOCK,
            f"Stock level ({available}) exceeds maximum ({item.maximum_stock})"
        )
    
    # Check for expiring items
    if item.expiry_date:
        days_until_expiry = (item.expiry_date - date.today()).days
        if days_until_expiry <= 0:
            await create_stock_alert(
                db, item, AlertType.EXPIRED,
                f"Item has expired on {item.expiry_date}"
            )
        elif days_until_expiry <= 30:
            await create_stock_alert(
                db, item, AlertType.EXPIRING_SOON,
                f"Item expires in {days_until_expiry} days"
            )

# Location Endpoints
@router.post("/locations", response_model=InventoryLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location: InventoryLocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new inventory location"""
    
    # Check if setting as default location
    if location.is_default:
        # Unset existing default location
        await db.execute(
            update(InventoryLocation).values(is_default=False)
        )
    
    # Create location
    db_location = InventoryLocation(
        id=uuid4(),
        name=location.name,
        description=location.description,
        location_type=location.location_type,
        address=location.address,
        city=location.city,
        state=location.state,
        postal_code=location.postal_code,
        country=location.country,
        manager_id=location.manager_id,
        is_active=location.is_active,
        is_default=location.is_default,
        capacity=location.capacity,
        cost_per_unit=location.cost_per_unit,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    
    # Calculate computed fields
    db_location.total_items = 0
    db_location.total_value = Decimal('0')
    db_location.utilization_percentage = None
    db_location.manager_name = None
    
    return db_location

@router.get("/locations", response_model=List[InventoryLocationResponse])
async def list_locations(
    location_type: Optional[LocationType] = Query(None, description="Filter by location type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    include_stats: bool = Query(True, description="Include inventory statistics"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of inventory locations"""
    
    query = select(InventoryLocation)
    
    if location_type:
        query = query.where(InventoryLocation.location_type == location_type)
    
    if is_active is not None:
        query = query.where(InventoryLocation.is_active == is_active)
    
    query = query.order_by(InventoryLocation.name)
    
    result = await db.execute(query)
    locations = result.scalars().all()
    
    # Add computed fields
    for location in locations:
        if include_stats:
            # Count total items
            items_count = await db.execute(
                select(func.count(InventoryItem.id)).where(InventoryItem.location_id == location.id)
            )
            location.total_items = items_count.scalar() or 0
            
            # Calculate total value
            value_result = await db.execute(
                select(func.sum(InventoryItem.quantity * InventoryItem.cost_per_unit))
                .where(
                    and_(
                        InventoryItem.location_id == location.id,
                        InventoryItem.cost_per_unit.isnot(None)
                    )
                )
            )
            location.total_value = value_result.scalar() or Decimal('0')
            
            # Calculate utilization
            if location.capacity and location.total_items > 0:
                location.utilization_percentage = round((location.total_items / location.capacity) * 100, 2)
            else:
                location.utilization_percentage = None
        else:
            location.total_items = 0
            location.total_value = Decimal('0')
            location.utilization_percentage = None
        
        location.manager_name = None  # TODO: Fetch from user table
    
    return locations

@router.get("/locations/{location_id}", response_model=InventoryLocationResponse)
async def get_location(
    location_id: UUID = Path(..., description="Location ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific inventory location"""
    
    result = await db.execute(
        select(InventoryLocation).where(InventoryLocation.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Add computed fields
    items_count = await db.execute(
        select(func.count(InventoryItem.id)).where(InventoryItem.location_id == location.id)
    )
    location.total_items = items_count.scalar() or 0
    
    value_result = await db.execute(
        select(func.sum(InventoryItem.quantity * InventoryItem.cost_per_unit))
        .where(
            and_(
                InventoryItem.location_id == location.id,
                InventoryItem.cost_per_unit.isnot(None)
            )
        )
    )
    location.total_value = value_result.scalar() or Decimal('0')
    
    if location.capacity and location.total_items > 0:
        location.utilization_percentage = round((location.total_items / location.capacity) * 100, 2)
    else:
        location.utilization_percentage = None
    
    location.manager_name = None  # TODO: Fetch from user table
    
    return location

@router.put("/locations/{location_id}", response_model=InventoryLocationResponse)
async def update_location(
    location_id: UUID = Path(..., description="Location ID"),
    location_update: InventoryLocationCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an inventory location"""
    
    # Get existing location
    result = await db.execute(
        select(InventoryLocation).where(InventoryLocation.id == location_id)
    )
    db_location = result.scalar_one_or_none()
    
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if setting as default location
    if location_update.is_default and not db_location.is_default:
        # Unset existing default location
        await db.execute(
            update(InventoryLocation)
            .where(InventoryLocation.id != location_id)
            .values(is_default=False)
        )
    
    # Update fields
    for field, value in location_update.dict(exclude_unset=True).items():
        setattr(db_location, field, value)
    
    db_location.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_location)
    
    # Add computed fields
    db_location.total_items = 0
    db_location.total_value = Decimal('0')
    db_location.utilization_percentage = None
    db_location.manager_name = None
    
    return db_location

@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID = Path(..., description="Location ID"),
    force: bool = Query(False, description="Force delete even if inventory items exist"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an inventory location"""
    
    # Get location
    result = await db.execute(
        select(InventoryLocation).where(InventoryLocation.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check for inventory items unless force delete
    if not force:
        items_count = await db.execute(
            select(func.count(InventoryItem.id)).where(InventoryItem.location_id == location_id)
        )
        count = items_count.scalar() or 0
        
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete location with {count} inventory items. Use force=true to delete anyway."
            )
    
    # Delete location and related records
    await db.execute(delete(InventoryItem).where(InventoryItem.location_id == location_id))
    await db.execute(delete(InventoryLocation).where(InventoryLocation.id == location_id))
    
    await db.commit()

# Inventory Item Endpoints
@router.post("/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new inventory item"""
    
    # Validate location exists
    if not await validate_location_exists(db, item.location_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found or inactive"
        )
    
    # Validate product variant exists
    if not await validate_product_variant_exists(db, item.product_variant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found"
        )
    
    # Check if item already exists for this variant-location combination
    existing = await db.execute(
        select(InventoryItem).where(
            and_(
                InventoryItem.product_variant_id == item.product_variant_id,
                InventoryItem.location_id == item.location_id
            )
        )
    )
    
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory item already exists for this product variant at this location"
        )
    
    # Create inventory item
    db_item = InventoryItem(
        id=uuid4(),
        product_variant_id=item.product_variant_id,
        location_id=item.location_id,
        quantity=item.quantity,
        reserved_quantity=item.reserved_quantity,
        minimum_stock=item.minimum_stock,
        maximum_stock=item.maximum_stock,
        reorder_point=item.reorder_point,
        reorder_quantity=item.reorder_quantity,
        cost_per_unit=item.cost_per_unit,
        expiry_date=item.expiry_date,
        batch_number=item.batch_number,
        supplier_id=item.supplier_id,
        notes=item.notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_item)
    await db.flush()
    
    # Create initial movement if quantity > 0
    if item.quantity > 0:
        movement = InventoryMovement(
            id=uuid4(),
            item_id=db_item.id,
            movement_type=MovementType.IN,
            quantity=item.quantity,
            reason=MovementReason.ADJUSTMENT,
            reference_number="INITIAL_STOCK",
            unit_cost=item.cost_per_unit,
            notes="Initial stock entry",
            balance_after=item.quantity,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        db.add(movement)
    
    # Check for alerts
    await check_and_create_alerts(db, db_item)
    
    await db.commit()
    
    # Return complete item with relationships
    return await get_inventory_item(db_item.id, db)

@router.get("/items", response_model=List[InventoryItemResponse])
async def list_inventory_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of items to return"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    product_variant_id: Optional[UUID] = Query(None, description="Filter by product variant"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    expired_only: bool = Query(False, description="Show only expired items"),
    search: Optional[str] = Query(None, min_length=1, description="Search in product name or SKU"),
    sort_by: str = Query("updated_at", regex="^(name|quantity|expiry_date|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of inventory items with filtering and pagination"""
    
    # Build query with joins
    query = select(InventoryItem).options(
        joinedload(InventoryItem.product_variant).joinedload(ProductVariant.product),
        joinedload(InventoryItem.location)
    )
    
    # Apply filters
    if location_id:
        query = query.where(InventoryItem.location_id == location_id)
    
    if product_variant_id:
        query = query.where(InventoryItem.product_variant_id == product_variant_id)
    
    if low_stock_only:
        query = query.where(
            InventoryItem.quantity - InventoryItem.reserved_quantity <= InventoryItem.reorder_point
        )
    
    if expired_only:
        query = query.where(
            and_(
                InventoryItem.expiry_date.isnot(None),
                InventoryItem.expiry_date <= date.today()
            )
        )
    
    if search:
        # Join with Product table for search
        query = query.join(ProductVariant).join(Product)
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Product.name.ilike(search_term),
                ProductVariant.sku.ilike(search_term)
            )
        )
    
    # Apply sorting
    if sort_by == "name":
        # Sort by product name - need to join
        query = query.join(ProductVariant).join(Product)
        order_column = Product.name
    elif sort_by == "quantity":
        order_column = InventoryItem.quantity
    elif sort_by == "expiry_date":
        order_column = InventoryItem.expiry_date
    else:
        order_column = InventoryItem.updated_at
    
    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    items = result.unique().scalars().all()
    
    # Build response list
    response_list = []
    for item in items:
        # Calculate computed fields
        available_quantity = item.quantity - item.reserved_quantity
        stock_status = await calculate_stock_status(item)
        total_value = (item.quantity * item.cost_per_unit) if item.cost_per_unit else Decimal('0')
        
        days_until_expiry = None
        if item.expiry_date:
            days_until_expiry = (item.expiry_date - date.today()).days
        
        # Get last movement date
        last_movement = await db.execute(
            select(InventoryMovement.created_at)
            .where(InventoryMovement.item_id == item.id)
            .order_by(InventoryMovement.created_at.desc())
            .limit(1)
        )
        last_movement_date = last_movement.scalar_one_or_none()
        
        response_item = InventoryItemResponse(
            id=item.id,
            product_variant_id=item.product_variant_id,
            product_name=item.product_variant.product.name,
            variant_name=item.product_variant.name,
            sku=item.product_variant.sku,
            location_id=item.location_id,
            location_name=item.location.name,
            quantity=item.quantity,
            reserved_quantity=item.reserved_quantity,
            available_quantity=available_quantity,
            minimum_stock=item.minimum_stock,
            maximum_stock=item.maximum_stock,
            reorder_point=item.reorder_point,
            reorder_quantity=item.reorder_quantity,
            cost_per_unit=item.cost_per_unit,
            total_value=total_value,
            expiry_date=item.expiry_date,
            batch_number=item.batch_number,
            supplier_id=item.supplier_id,
            supplier_name=None,  # TODO: Fetch from supplier table
            notes=item.notes,
            stock_status=stock_status,
            days_until_expiry=days_until_expiry,
            last_movement_date=last_movement_date,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        response_list.append(response_item)
    
    return response_list

@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: UUID = Path(..., description="Inventory item ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific inventory item with all details"""
    
    result = await db.execute(
        select(InventoryItem)
        .options(
            joinedload(InventoryItem.product_variant).joinedload(ProductVariant.product),
            joinedload(InventoryItem.location)
        )
        .where(InventoryItem.id == item_id)
    )
    
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    # Calculate computed fields
    available_quantity = item.quantity - item.reserved_quantity
    stock_status = await calculate_stock_status(item)
    total_value = (item.quantity * item.cost_per_unit) if item.cost_per_unit else Decimal('0')
    
    days_until_expiry = None
    if item.expiry_date:
        days_until_expiry = (item.expiry_date - date.today()).days
    
    # Get last movement date
    last_movement = await db.execute(
        select(InventoryMovement.created_at)
        .where(InventoryMovement.item_id == item.id)
        .order_by(InventoryMovement.created_at.desc())
        .limit(1)
    )
    last_movement_date = last_movement.scalar_one_or_none()
    
    return InventoryItemResponse(
        id=item.id,
        product_variant_id=item.product_variant_id,
        product_name=item.product_variant.product.name,
        variant_name=item.product_variant.name,
        sku=item.product_variant.sku,
        location_id=item.location_id,
        location_name=item.location.name,
        quantity=item.quantity,
        reserved_quantity=item.reserved_quantity,
        available_quantity=available_quantity,
        minimum_stock=item.minimum_stock,
        maximum_stock=item.maximum_stock,
        reorder_point=item.reorder_point,
        reorder_quantity=item.reorder_quantity,
        cost_per_unit=item.cost_per_unit,
        total_value=total_value,
        expiry_date=item.expiry_date,
        batch_number=item.batch_number,
        supplier_id=item.supplier_id,
        supplier_name=None,  # TODO: Fetch from supplier table
        notes=item.notes,
        stock_status=stock_status,
        days_until_expiry=days_until_expiry,
        last_movement_date=last_movement_date,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: UUID = Path(..., description="Inventory item ID"),
    item_update: InventoryItemUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an inventory item's settings (not quantity)"""
    
    # Get existing item
    result = await db.execute(
        select(InventoryItem).where(InventoryItem.id == item_id)
    )
    db_item = result.scalar_one_or_none()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    # Update fields
    for field, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, field, value)
    
    db_item.updated_at = datetime.utcnow()
    
    # Check for alerts after update
    await check_and_create_alerts(db, db_item)
    
    await db.commit()
    
    # Return updated item
    return await get_inventory_item(item_id, db)

# Movement Endpoints
@router.post("/movements", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_movement(
    movement: InventoryMovementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new inventory movement"""
    
    # Get inventory item
    result = await db.execute(
        select(InventoryItem)
        .options(
            joinedload(InventoryItem.product_variant).joinedload(ProductVariant.product),
            joinedload(InventoryItem.location)
        )
        .where(InventoryItem.id == movement.item_id)
    )
    
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    # Validate stock availability for outbound movements
    if movement.quantity < 0:  # Outbound movement
        available_quantity = item.quantity - item.reserved_quantity
        if abs(movement.quantity) > available_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {available_quantity}, Requested: {abs(movement.quantity)}"
            )
    
    # Update inventory quantity
    new_quantity = item.quantity + movement.quantity
    if new_quantity < 0:
        new_quantity = 0  # Prevent negative inventory
    
    item.quantity = new_quantity
    item.updated_at = datetime.utcnow()
    
    # Create movement record
    db_movement = InventoryMovement(
        id=uuid4(),
        item_id=movement.item_id,
        movement_type=movement.movement_type,
        quantity=movement.quantity,
        reason=movement.reason,
        reference_number=movement.reference_number,
        unit_cost=movement.unit_cost,
        notes=movement.notes,
        from_location_id=movement.from_location_id,
        to_location_id=movement.to_location_id,
        balance_after=new_quantity,
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    
    db.add(db_movement)
    
    # Check for alerts after movement
    await check_and_create_alerts(db, item)
    
    await db.commit()
    await db.refresh(db_movement)
    
    # Build response
    total_cost = None
    if movement.unit_cost:
        total_cost = abs(movement.quantity) * movement.unit_cost
    
    return InventoryMovementResponse(
        id=db_movement.id,
        item_id=db_movement.item_id,
        product_name=item.product_variant.product.name,
        sku=item.product_variant.sku,
        location_name=item.location.name,
        movement_type=db_movement.movement_type,
        quantity=db_movement.quantity,
        reason=db_movement.reason,
        reference_number=db_movement.reference_number,
        unit_cost=db_movement.unit_cost,
        total_cost=total_cost,
        notes=db_movement.notes,
        from_location_id=db_movement.from_location_id,
        from_location_name=None,  # TODO: Fetch location name
        to_location_id=db_movement.to_location_id,
        to_location_name=None,    # TODO: Fetch location name
        balance_after=db_movement.balance_after,
        created_by=db_movement.created_by,
        created_by_name=current_user.full_name or current_user.email,
        created_at=db_movement.created_at
    )

@router.get("/movements", response_model=List[InventoryMovementResponse])
async def list_inventory_movements(
    skip: int = Query(0, ge=0, description="Number of movements to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of movements to return"),
    item_id: Optional[UUID] = Query(None, description="Filter by inventory item"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    movement_type: Optional[MovementType] = Query(None, description="Filter by movement type"),
    start_date: Optional[date] = Query(None, description="Filter movements after this date"),
    end_date: Optional[date] = Query(None, description="Filter movements before this date"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of inventory movements with filtering and pagination"""
    
    # Build query with joins
    query = select(InventoryMovement).options(
        joinedload(InventoryMovement.item)
        .joinedload(InventoryItem.product_variant)
        .joinedload(ProductVariant.product),
        joinedload(InventoryMovement.item).joinedload(InventoryItem.location)
    )
    
    # Apply filters
    if item_id:
        query = query.where(InventoryMovement.item_id == item_id)
    
    if location_id:
        query = query.join(InventoryItem).where(InventoryItem.location_id == location_id)
    
    if movement_type:
        query = query.where(InventoryMovement.movement_type == movement_type)
    
    if start_date:
        query = query.where(InventoryMovement.created_at >= start_date)
    
    if end_date:
        query = query.where(InventoryMovement.created_at <= end_date)
    
    # Apply sorting and pagination
    query = query.order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    movements = result.unique().scalars().all()
    
    # Build response list
    response_list = []
    for movement in movements:
        total_cost = None
        if movement.unit_cost:
            total_cost = abs(movement.quantity) * movement.unit_cost
        
        response_item = InventoryMovementResponse(
            id=movement.id,
            item_id=movement.item_id,
            product_name=movement.item.product_variant.product.name,
            sku=movement.item.product_variant.sku,
            location_name=movement.item.location.name,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            reason=movement.reason,
            reference_number=movement.reference_number,
            unit_cost=movement.unit_cost,
            total_cost=total_cost,
            notes=movement.notes,
            from_location_id=movement.from_location_id,
            from_location_name=None,  # TODO: Fetch location name
            to_location_id=movement.to_location_id,
            to_location_name=None,    # TODO: Fetch location name
            balance_after=movement.balance_after,
            created_by=movement.created_by,
            created_by_name="Unknown",  # TODO: Fetch user name
            created_at=movement.created_at
        )
        response_list.append(response_item)
    
    return response_list

# Stock Alerts
@router.get("/alerts", response_model=List[StockAlertResponse])
async def list_stock_alerts(
    alert_type: Optional[AlertType] = Query(None, description="Filter by alert type"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    limit: int = Query(50, ge=1, le=500, description="Number of alerts to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of stock alerts"""
    
    query = select(StockAlert).options(
        joinedload(StockAlert.item)
        .joinedload(InventoryItem.product_variant)
        .joinedload(ProductVariant.product),
        joinedload(StockAlert.item).joinedload(InventoryItem.location)
    )
    
    # Apply filters
    if alert_type:
        query = query.where(StockAlert.alert_type == alert_type)
    
    if status:
        query = query.where(StockAlert.status == status)
    
    if location_id:
        query = query.join(InventoryItem).where(InventoryItem.location_id == location_id)
    
    # Order by creation date (newest first) and apply limit
    query = query.order_by(StockAlert.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    alerts = result.unique().scalars().all()
    
    # Build response list
    response_list = []
    for alert in alerts:
        response_item = StockAlertResponse(
            id=alert.id,
            item_id=alert.item_id,
            product_name=alert.item.product_variant.product.name,
            sku=alert.item.product_variant.sku,
            location_name=alert.item.location.name,
            alert_type=alert.alert_type,
            current_quantity=alert.current_quantity,
            threshold_quantity=alert.threshold_quantity,
            message=alert.message,
            status=alert.status,
            created_at=alert.created_at,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at
        )
        response_list.append(response_item)
    
    return response_list

@router.put("/alerts/{alert_id}/acknowledge", response_model=StockAlertResponse)
async def acknowledge_alert(
    alert_id: UUID = Path(..., description="Alert ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Acknowledge a stock alert"""
    
    result = await db.execute(
        select(StockAlert).where(StockAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.id
    
    await db.commit()
    
    # Return updated alert (simplified response)
    return StockAlertResponse(
        id=alert.id,
        item_id=alert.item_id,
        product_name="Unknown",  # Would need to load item
        sku="Unknown",
        location_name="Unknown",
        alert_type=alert.alert_type,
        current_quantity=alert.current_quantity,
        threshold_quantity=alert.threshold_quantity,
        message=alert.message,
        status=alert.status,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by=alert.acknowledged_by,
        resolved_at=alert.resolved_at
    )

# Analytics and Reports
@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_inventory_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    db: AsyncSession = Depends(get_db)
):
    """Get inventory analytics and statistics"""
    
    # Base query filters
    base_filters = []
    if location_id:
        base_filters.append(InventoryItem.location_id == location_id)
    
    # Total items and value
    if base_filters:
        items_query = select(func.count(InventoryItem.id), func.sum(InventoryItem.quantity * InventoryItem.cost_per_unit))
        for filter_clause in base_filters:
            items_query = items_query.where(filter_clause)
    else:
        items_query = select(func.count(InventoryItem.id), func.sum(InventoryItem.quantity * InventoryItem.cost_per_unit))
    
    result = await db.execute(items_query)
    total_items, total_value = result.one()
    total_value = total_value or Decimal('0')
    
    # Stock status counts
    stock_status_counts = {
        "in_stock": 0,
        "low_stock": 0,
        "out_of_stock": 0,
        "overstock": 0
    }
    
    # Get all items for status calculation
    items_query = select(InventoryItem)
    if base_filters:
        for filter_clause in base_filters:
            items_query = items_query.where(filter_clause)
    
    items_result = await db.execute(items_query)
    items = items_result.scalars().all()
    
    for item in items:
        status = await calculate_stock_status(item)
        if status in stock_status_counts:
            stock_status_counts[status] += 1
    
    # Movement analytics
    movement_filters = []
    if start_date:
        movement_filters.append(InventoryMovement.created_at >= start_date)
    if end_date:
        movement_filters.append(InventoryMovement.created_at <= end_date)
    if location_id:
        movement_filters.append(InventoryItem.location_id == location_id)
    
    movements_query = select(
        InventoryMovement.movement_type,
        func.count(InventoryMovement.id),
        func.sum(func.abs(InventoryMovement.quantity))
    ).join(InventoryItem)
    
    for filter_clause in movement_filters:
        movements_query = movements_query.where(filter_clause)
    
    movements_query = movements_query.group_by(InventoryMovement.movement_type)
    
    movements_result = await db.execute(movements_query)
    movement_stats = {
        "by_type": {},
        "total_movements": 0,
        "total_quantity_moved": 0
    }
    
    for movement_type, count, quantity in movements_result.fetchall():
        movement_stats["by_type"][movement_type] = {
            "count": count,
            "quantity": quantity or 0
        }
        movement_stats["total_movements"] += count
        movement_stats["total_quantity_moved"] += quantity or 0
    
    # Active alerts count
    alerts_query = select(func.count(StockAlert.id)).where(StockAlert.status == AlertStatus.ACTIVE)
    if location_id:
        alerts_query = alerts_query.join(InventoryItem).where(InventoryItem.location_id == location_id)
    
    alerts_result = await db.execute(alerts_query)
    active_alerts = alerts_result.scalar() or 0
    
    # Top products by value
    top_products_query = select(
        Product.name,
        ProductVariant.sku,
        func.sum(InventoryItem.quantity * InventoryItem.cost_per_unit).label('total_value')
    ).join(ProductVariant).join(Product).join(InventoryItem)
    
    if base_filters:
        for filter_clause in base_filters:
            top_products_query = top_products_query.where(filter_clause)
    
    top_products_query = top_products_query.group_by(Product.name, ProductVariant.sku).order_by(desc('total_value')).limit(10)
    
    top_products_result = await db.execute(top_products_query)
    top_products = [
        {"name": name, "sku": sku, "value": float(value or 0)}
        for name, sku, value in top_products_result.fetchall()
    ]
    
    return {
        "summary": {
            "total_items": total_items,
            "total_value": float(total_value),
            "active_alerts": active_alerts
        },
        "stock_status": stock_status_counts,
        "movements": movement_stats,
        "top_products_by_value": top_products,
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "location_id": location_id
        }
    }

# Bulk Operations
@router.post("/bulk/adjustment", response_model=Dict[str, Any])
async def bulk_inventory_adjustment(
    adjustment: InventoryAdjustmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Perform bulk inventory adjustments"""
    
    processed_items = []
    failed_items = []
    
    for adj_data in adjustment.adjustments:
        try:
            item_id = UUID(adj_data["item_id"])
            quantity_change = int(adj_data["quantity_change"])
            
            # Get inventory item
            result = await db.execute(
                select(InventoryItem).where(InventoryItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                failed_items.append({
                    "item_id": str(item_id),
                    "error": "Item not found"
                })
                continue
            
            # Update quantity
            new_quantity = item.quantity + quantity_change
            if new_quantity < 0:
                new_quantity = 0
            
            old_quantity = item.quantity
            item.quantity = new_quantity
            item.updated_at = datetime.utcnow()
            
            # Create movement record
            movement = InventoryMovement(
                id=uuid4(),
                item_id=item_id,
                movement_type=MovementType.ADJUSTMENT,
                quantity=quantity_change,
                reason=MovementReason.ADJUSTMENT,
                reference_number=adjustment.reference_number,
                notes=adjustment.reason,
                balance_after=new_quantity,
                created_by=current_user.id,
                created_at=datetime.utcnow()
            )
            db.add(movement)
            
            # Check for alerts
            await check_and_create_alerts(db, item)
            
            processed_items.append({
                "item_id": str(item_id),
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "change": quantity_change
            })
            
        except Exception as e:
            failed_items.append({
                "item_id": adj_data.get("item_id", "unknown"),
                "error": str(e)
            })
    
    await db.commit()
    
    return {
        "processed_count": len(processed_items),
        "failed_count": len(failed_items),
        "processed_items": processed_items,
        "failed_items": failed_items,
        "reference_number": adjustment.reference_number
    }