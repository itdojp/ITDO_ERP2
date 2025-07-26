"""
Consolidated Inventory API - Day 13 API Consolidation
Integrates functionality from all inventory API versions into a single, comprehensive API.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])

# =====================================
# ENUMS
# =====================================

class MovementType(str, Enum):
    """Inventory movement types"""
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"

class LocationType(str, Enum):
    """Storage location types"""
    WAREHOUSE = "warehouse"
    STORE = "store"
    PRODUCTION = "production"
    TRANSIT = "transit"

# =====================================
# SCHEMAS
# =====================================

class InventoryLocationBase(BaseModel):
    """Base inventory location schema"""
    code: str
    name: str
    type: LocationType
    address: Optional[str] = None
    is_active: bool = True

class InventoryLocationCreate(InventoryLocationBase):
    """Inventory location creation schema"""
    pass

class InventoryLocationResponse(InventoryLocationBase):
    """Inventory location response schema"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class InventoryItemBase(BaseModel):
    """Base inventory item schema"""
    product_id: str
    location_id: str
    quantity: int
    reserved_quantity: int = 0
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    reorder_point: Optional[int] = None

class InventoryItemCreate(InventoryItemBase):
    """Inventory item creation schema"""
    initial_cost: Optional[Decimal] = None

class InventoryItemUpdate(BaseModel):
    """Inventory item update schema"""
    quantity: Optional[int] = None
    reserved_quantity: Optional[int] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    reorder_point: Optional[int] = None

class InventoryItemResponse(InventoryItemBase):
    """Inventory item response schema"""
    id: str
    available_quantity: int
    last_movement_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class InventoryMovementBase(BaseModel):
    """Base inventory movement schema"""
    product_id: str
    location_id: str
    movement_type: MovementType
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class InventoryMovementCreate(InventoryMovementBase):
    """Inventory movement creation schema"""
    cost_per_unit: Optional[Decimal] = None

class InventoryMovementResponse(InventoryMovementBase):
    """Inventory movement response schema"""
    id: str
    movement_date: datetime
    cost_per_unit: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    created_by: Optional[str] = None
    created_at: datetime

class StockAdjustmentRequest(BaseModel):
    """Stock adjustment request"""
    product_id: str
    location_id: str
    new_quantity: int
    reason: str
    notes: Optional[str] = None

class StockTransferRequest(BaseModel):
    """Stock transfer request"""
    product_id: str
    from_location_id: str
    to_location_id: str
    quantity: int
    notes: Optional[str] = None

class InventoryReportRequest(BaseModel):
    """Inventory report request"""
    location_ids: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None
    include_movements: bool = False
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class InventoryReportResponse(BaseModel):
    """Inventory report response"""
    items: List[InventoryItemResponse]
    movements: Optional[List[InventoryMovementResponse]] = None
    summary: Dict[str, Any]
    generated_at: datetime

class LowStockAlert(BaseModel):
    """Low stock alert"""
    product_id: str
    location_id: str
    current_quantity: int
    min_stock_level: int
    reorder_point: Optional[int] = None
    suggested_order_quantity: Optional[int] = None

# Legacy schemas for backward compatibility
class LegacyInventoryV21(BaseModel):
    """Legacy v21 inventory format"""
    id: int
    product_id: str
    quantity: int
    location: str

# =====================================
# MOCK DATA STORES
# =====================================

# Mock databases
inventory_locations_db: Dict[str, Dict[str, Any]] = {}
inventory_items_db: Dict[str, Dict[str, Any]] = {}
inventory_movements_db: Dict[str, Dict[str, Any]] = {}
legacy_inventory_db: List[Dict[str, Any]] = []

# =====================================
# UTILITY FUNCTIONS
# =====================================

def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())

def calculate_available_quantity(item: Dict[str, Any]) -> int:
    """Calculate available quantity"""
    return max(0, item["quantity"] - item["reserved_quantity"])

async def get_current_user():
    """Mock current user"""
    return {"id": "current-user", "is_admin": True}

def validate_location_exists(location_id: str) -> bool:
    """Validate that location exists"""
    return location_id in inventory_locations_db

def validate_product_exists(product_id: str) -> bool:
    """Mock product validation - in real app, check product service"""
    return True  # Mock validation

# =====================================
# LOCATION MANAGEMENT
# =====================================

@router.post("/locations", response_model=InventoryLocationResponse, status_code=201)
async def create_location(
    location: InventoryLocationCreate,
    current_user = Depends(get_current_user)
) -> InventoryLocationResponse:
    """Create a new inventory location"""
    # Check for duplicate code
    for existing_location in inventory_locations_db.values():
        if existing_location["code"] == location.code:
            raise HTTPException(
                status_code=400,
                detail=f"Location with code '{location.code}' already exists"
            )
    
    location_id = generate_id()
    now = datetime.utcnow()
    
    new_location = {
        "id": location_id,
        "code": location.code,
        "name": location.name,
        "type": location.type,
        "address": location.address,
        "is_active": location.is_active,
        "created_at": now,
        "updated_at": now
    }
    
    inventory_locations_db[location_id] = new_location
    return InventoryLocationResponse(**new_location)

@router.get("/locations", response_model=List[InventoryLocationResponse])
async def list_locations(
    is_active: Optional[bool] = None,
    location_type: Optional[LocationType] = None,
    current_user = Depends(get_current_user)
) -> List[InventoryLocationResponse]:
    """List inventory locations"""
    filtered_locations = []
    
    for location_data in inventory_locations_db.values():
        if is_active is not None and location_data["is_active"] != is_active:
            continue
        if location_type and location_data["type"] != location_type:
            continue
        
        filtered_locations.append(InventoryLocationResponse(**location_data))
    
    return filtered_locations

# =====================================
# INVENTORY ITEM MANAGEMENT
# =====================================

@router.post("/items", response_model=InventoryItemResponse, status_code=201)
async def create_inventory_item(
    item: InventoryItemCreate,
    current_user = Depends(get_current_user)
) -> InventoryItemResponse:
    """Create a new inventory item"""
    # Validate location exists
    if not validate_location_exists(item.location_id):
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Validate product exists
    if not validate_product_exists(item.product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check for duplicate product-location combination
    for existing_item in inventory_items_db.values():
        if (existing_item["product_id"] == item.product_id and 
            existing_item["location_id"] == item.location_id):
            raise HTTPException(
                status_code=400,
                detail="Inventory item already exists for this product-location combination"
            )
    
    item_id = generate_id()
    now = datetime.utcnow()
    
    new_item = {
        "id": item_id,
        "product_id": item.product_id,
        "location_id": item.location_id,
        "quantity": item.quantity,
        "reserved_quantity": item.reserved_quantity,
        "min_stock_level": item.min_stock_level,
        "max_stock_level": item.max_stock_level,
        "reorder_point": item.reorder_point,
        "available_quantity": calculate_available_quantity({
            "quantity": item.quantity,
            "reserved_quantity": item.reserved_quantity
        }),
        "last_movement_date": now if item.quantity > 0 else None,
        "created_at": now,
        "updated_at": now
    }
    
    inventory_items_db[item_id] = new_item
    
    # Create initial movement if quantity > 0
    if item.quantity > 0:
        await create_movement(InventoryMovementCreate(
            product_id=item.product_id,
            location_id=item.location_id,
            movement_type=MovementType.IN,
            quantity=item.quantity,
            cost_per_unit=item.initial_cost,
            reference_number="INITIAL_STOCK",
            notes="Initial stock entry"
        ))
    
    return InventoryItemResponse(**new_item)

@router.get("/items", response_model=List[InventoryItemResponse])
async def list_inventory_items(
    location_id: Optional[str] = None,
    product_id: Optional[str] = None,
    low_stock_only: bool = False,
    current_user = Depends(get_current_user)
) -> List[InventoryItemResponse]:
    """List inventory items with filtering"""
    filtered_items = []
    
    for item_data in inventory_items_db.values():
        if location_id and item_data["location_id"] != location_id:
            continue
        if product_id and item_data["product_id"] != product_id:
            continue
        if low_stock_only:
            if (item_data["min_stock_level"] is None or 
                item_data["quantity"] >= item_data["min_stock_level"]):
                continue
        
        # Update available quantity
        item_data["available_quantity"] = calculate_available_quantity(item_data)
        filtered_items.append(InventoryItemResponse(**item_data))
    
    return filtered_items

@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: str,
    current_user = Depends(get_current_user)
) -> InventoryItemResponse:
    """Get a specific inventory item"""
    if item_id not in inventory_items_db:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item_data = inventory_items_db[item_id]
    item_data["available_quantity"] = calculate_available_quantity(item_data)
    
    return InventoryItemResponse(**item_data)

@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item_update: InventoryItemUpdate,
    current_user = Depends(get_current_user)
) -> InventoryItemResponse:
    """Update an inventory item"""
    if item_id not in inventory_items_db:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item_data = inventory_items_db[item_id].copy()
    update_data = item_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        item_data[field] = value
    
    item_data["updated_at"] = datetime.utcnow()
    item_data["available_quantity"] = calculate_available_quantity(item_data)
    
    inventory_items_db[item_id] = item_data
    
    return InventoryItemResponse(**item_data)

# =====================================
# INVENTORY MOVEMENTS
# =====================================

async def create_movement(movement: InventoryMovementCreate) -> InventoryMovementResponse:
    """Internal function to create inventory movement"""
    movement_id = generate_id()
    now = datetime.utcnow()
    
    total_cost = None
    if movement.cost_per_unit:
        total_cost = movement.cost_per_unit * movement.quantity
    
    new_movement = {
        "id": movement_id,
        "product_id": movement.product_id,
        "location_id": movement.location_id,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
        "cost_per_unit": movement.cost_per_unit,
        "total_cost": total_cost,
        "reference_number": movement.reference_number,
        "notes": movement.notes,
        "movement_date": now,
        "created_by": "current-user",
        "created_at": now
    }
    
    inventory_movements_db[movement_id] = new_movement
    return InventoryMovementResponse(**new_movement)

@router.post("/movements", response_model=InventoryMovementResponse, status_code=201)
async def add_inventory_movement(
    movement: InventoryMovementCreate,
    current_user = Depends(get_current_user)
) -> InventoryMovementResponse:
    """Add inventory movement and update stock levels"""
    # Validate location exists
    if not validate_location_exists(movement.location_id):
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Find inventory item
    inventory_item = None
    for item_data in inventory_items_db.values():
        if (item_data["product_id"] == movement.product_id and 
            item_data["location_id"] == movement.location_id):
            inventory_item = item_data
            break
    
    if not inventory_item and movement.movement_type == MovementType.OUT:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove stock from non-existent inventory item"
        )
    
    # Create movement record
    movement_response = await create_movement(movement)
    
    # Update inventory levels
    if inventory_item:
        if movement.movement_type == MovementType.IN:
            inventory_item["quantity"] += movement.quantity
        elif movement.movement_type == MovementType.OUT:
            if inventory_item["quantity"] < movement.quantity:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock for this movement"
                )
            inventory_item["quantity"] -= movement.quantity
        elif movement.movement_type == MovementType.ADJUSTMENT:
            inventory_item["quantity"] = movement.quantity
        
        inventory_item["last_movement_date"] = datetime.utcnow()
        inventory_item["updated_at"] = datetime.utcnow()
        inventory_item["available_quantity"] = calculate_available_quantity(inventory_item)
    
    return movement_response

@router.get("/movements", response_model=List[InventoryMovementResponse])
async def list_movements(
    product_id: Optional[str] = None,
    location_id: Optional[str] = None,
    movement_type: Optional[MovementType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_user)
) -> List[InventoryMovementResponse]:
    """List inventory movements with filtering"""
    filtered_movements = []
    
    for movement_data in inventory_movements_db.values():
        if product_id and movement_data["product_id"] != product_id:
            continue
        if location_id and movement_data["location_id"] != location_id:
            continue
        if movement_type and movement_data["movement_type"] != movement_type:
            continue
        if date_from and movement_data["movement_date"] < date_from:
            continue
        if date_to and movement_data["movement_date"] > date_to:
            continue
        
        filtered_movements.append(InventoryMovementResponse(**movement_data))
    
    # Sort by movement date (newest first) and apply limit
    filtered_movements.sort(key=lambda x: x.movement_date, reverse=True)
    return filtered_movements[:limit]

# =====================================
# STOCK OPERATIONS
# =====================================

@router.post("/adjust-stock")
async def adjust_stock(
    adjustment: StockAdjustmentRequest,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Adjust stock levels with reason tracking"""
    # Create adjustment movement
    movement = InventoryMovementCreate(
        product_id=adjustment.product_id,
        location_id=adjustment.location_id,
        movement_type=MovementType.ADJUSTMENT,
        quantity=adjustment.new_quantity,
        reference_number=f"ADJ_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        notes=f"Reason: {adjustment.reason}. {adjustment.notes or ''}"
    )
    
    movement_response = await add_inventory_movement(movement)
    
    return {
        "message": "Stock adjusted successfully",
        "movement_id": movement_response.id,
        "new_quantity": adjustment.new_quantity,
        "reason": adjustment.reason
    }

@router.post("/transfer-stock")
async def transfer_stock(
    transfer: StockTransferRequest,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Transfer stock between locations"""
    # Create outbound movement
    out_movement = InventoryMovementCreate(
        product_id=transfer.product_id,
        location_id=transfer.from_location_id,
        movement_type=MovementType.OUT,
        quantity=transfer.quantity,
        reference_number=f"XFER_OUT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        notes=f"Transfer to location {transfer.to_location_id}. {transfer.notes or ''}"
    )
    
    out_response = await add_inventory_movement(out_movement)
    
    # Create inbound movement
    in_movement = InventoryMovementCreate(
        product_id=transfer.product_id,
        location_id=transfer.to_location_id,
        movement_type=MovementType.IN,
        quantity=transfer.quantity,
        reference_number=f"XFER_IN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        notes=f"Transfer from location {transfer.from_location_id}. {transfer.notes or ''}"
    )
    
    in_response = await add_inventory_movement(in_movement)
    
    return {
        "message": "Stock transferred successfully",
        "out_movement_id": out_response.id,
        "in_movement_id": in_response.id,
        "quantity_transferred": transfer.quantity
    }

# =====================================
# REPORTS AND ANALYTICS
# =====================================

@router.post("/reports", response_model=InventoryReportResponse)
async def generate_inventory_report(
    request: InventoryReportRequest,
    current_user = Depends(get_current_user)
) -> InventoryReportResponse:
    """Generate comprehensive inventory report"""
    # Filter items
    filtered_items = []
    for item_data in inventory_items_db.values():
        if request.location_ids and item_data["location_id"] not in request.location_ids:
            continue
        if request.product_ids and item_data["product_id"] not in request.product_ids:
            continue
        
        item_data["available_quantity"] = calculate_available_quantity(item_data)
        filtered_items.append(InventoryItemResponse(**item_data))
    
    # Filter movements if requested
    filtered_movements = None
    if request.include_movements:
        filtered_movements = []
        for movement_data in inventory_movements_db.values():
            if request.location_ids and movement_data["location_id"] not in request.location_ids:
                continue
            if request.product_ids and movement_data["product_id"] not in request.product_ids:
                continue
            if request.date_from and movement_data["movement_date"] < request.date_from:
                continue
            if request.date_to and movement_data["movement_date"] > request.date_to:
                continue
            
            filtered_movements.append(InventoryMovementResponse(**movement_data))
    
    # Generate summary
    summary = {
        "total_items": len(filtered_items),
        "total_value": sum(item.quantity * 10 for item in filtered_items),  # Mock pricing
        "low_stock_items": len([item for item in filtered_items 
                               if item.min_stock_level and item.quantity < item.min_stock_level]),
        "out_of_stock_items": len([item for item in filtered_items if item.quantity == 0]),
        "total_movements": len(filtered_movements) if filtered_movements else 0
    }
    
    return InventoryReportResponse(
        items=filtered_items,
        movements=filtered_movements,
        summary=summary,
        generated_at=datetime.utcnow()
    )

@router.get("/alerts/low-stock", response_model=List[LowStockAlert])
async def get_low_stock_alerts(
    location_id: Optional[str] = None,
    current_user = Depends(get_current_user)
) -> List[LowStockAlert]:
    """Get low stock alerts"""
    alerts = []
    
    for item_data in inventory_items_db.values():
        if location_id and item_data["location_id"] != location_id:
            continue
        
        min_level = item_data.get("min_stock_level")
        if min_level and item_data["quantity"] < min_level:
            suggested_order = max(
                min_level * 2 - item_data["quantity"],
                item_data.get("reorder_point", min_level) - item_data["quantity"]
            )
            
            alerts.append(LowStockAlert(
                product_id=item_data["product_id"],
                location_id=item_data["location_id"],
                current_quantity=item_data["quantity"],
                min_stock_level=min_level,
                reorder_point=item_data.get("reorder_point"),
                suggested_order_quantity=suggested_order
            ))
    
    return alerts

# =====================================
# BACKWARD COMPATIBILITY
# =====================================

@router.post("/inventory-v21", response_model=LegacyInventoryV21)
async def create_inventory_v21(
    product_id: str, 
    quantity: int, 
    location: str
) -> LegacyInventoryV21:
    """Legacy v21 endpoint for backward compatibility"""
    legacy_id = len(legacy_inventory_db) + 1
    
    # Create in new format (create location if needed)
    location_id = None
    for loc_data in inventory_locations_db.values():
        if loc_data["name"] == location:
            location_id = loc_data["id"]
            break
    
    if not location_id:
        # Create default location
        default_location = InventoryLocationCreate(
            code=f"LEGACY_{location}",
            name=location,
            type=LocationType.WAREHOUSE
        )
        location_response = await create_location(default_location)
        location_id = location_response.id
    
    # Create inventory item
    item_create = InventoryItemCreate(
        product_id=product_id,
        location_id=location_id,
        quantity=quantity
    )
    
    await create_inventory_item(item_create)
    
    # Store in legacy format
    legacy_item = {
        "id": legacy_id,
        "product_id": product_id,
        "quantity": quantity,
        "location": location
    }
    legacy_inventory_db.append(legacy_item)
    
    return LegacyInventoryV21(**legacy_item)

@router.get("/inventory-v21", response_model=List[LegacyInventoryV21])
async def list_inventory_v21() -> List[LegacyInventoryV21]:
    """Legacy v21 list endpoint for backward compatibility"""
    return [LegacyInventoryV21(**item) for item in legacy_inventory_db]

# =====================================
# HEALTH CHECK
# =====================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """API health check"""
    return {
        "status": "healthy",
        "total_locations": len(inventory_locations_db),
        "total_items": len(inventory_items_db),
        "total_movements": len(inventory_movements_db),
        "api_version": "consolidated_v1.0",
        "timestamp": datetime.utcnow().isoformat()
    }