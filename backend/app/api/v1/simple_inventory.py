"""
Simple Inventory Management API - No Database Dependencies
Pure business logic for inventory operations
Working over perfect approach
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter(prefix="/simple-inventory", tags=["Simple Inventory"])

# In-memory storage for demonstration
inventory_store: Dict[str, Dict[str, Any]] = {}
movements_store: Dict[str, Dict[str, Any]] = {}

class SimpleInventoryItem(BaseModel):
    """Simple inventory item model without database dependencies."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_code: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=200)
    warehouse: str = Field(..., min_length=1, max_length=100)
    quantity_on_hand: float = Field(default=0.0, ge=0)
    quantity_available: float = Field(default=0.0, ge=0)
    quantity_reserved: float = Field(default=0.0, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=50)
    minimum_level: Optional[float] = Field(None, ge=0)
    maximum_level: Optional[float] = Field(None, ge=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class InventoryItemCreate(BaseModel):
    """Schema for creating inventory item."""
    product_code: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=200)
    warehouse: str = Field(..., min_length=1, max_length=100)
    quantity_on_hand: float = Field(default=0.0, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=50)
    minimum_level: Optional[float] = Field(None, ge=0)
    maximum_level: Optional[float] = Field(None, ge=0)

class StockMovement(BaseModel):
    """Simple stock movement model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inventory_item_id: str
    movement_type: str = Field(..., description="IN, OUT, ADJUSTMENT")
    quantity: float = Field(..., description="Positive for IN, negative for OUT")
    reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)

class StockMovementCreate(BaseModel):
    """Schema for creating stock movement."""
    inventory_item_id: str
    movement_type: str = Field(..., description="IN, OUT, ADJUSTMENT")
    quantity: float = Field(...)
    reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

@router.post("/items/", response_model=SimpleInventoryItem)
async def create_inventory_item(item_data: InventoryItemCreate) -> SimpleInventoryItem:
    """Create a new inventory item."""
    # Check if item already exists for this product in this warehouse
    for existing_item in inventory_store.values():
        if (existing_item["product_code"] == item_data.product_code and 
            existing_item["warehouse"] == item_data.warehouse):
            raise HTTPException(
                status_code=400,
                detail=f"Inventory item for product '{item_data.product_code}' already exists in warehouse '{item_data.warehouse}'"
            )
    
    # Create inventory item
    item = SimpleInventoryItem(
        product_code=item_data.product_code,
        product_name=item_data.product_name,
        warehouse=item_data.warehouse,
        quantity_on_hand=item_data.quantity_on_hand,
        quantity_available=item_data.quantity_on_hand,
        unit_cost=item_data.unit_cost,
        location=item_data.location,
        minimum_level=item_data.minimum_level,
        maximum_level=item_data.maximum_level
    )
    
    inventory_store[item.id] = item.model_dump()
    return item

@router.get("/items/", response_model=List[SimpleInventoryItem])
async def list_inventory_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    warehouse: Optional[str] = Query(None),
    product_code: Optional[str] = Query(None),
    low_stock_only: bool = Query(False, description="Show only low stock items")
) -> List[SimpleInventoryItem]:
    """List inventory items with filtering."""
    all_items = list(inventory_store.values())
    
    # Apply filters
    filtered_items = []
    for item_data in all_items:
        if not item_data["is_active"]:
            continue
            
        # Warehouse filter
        if warehouse and item_data["warehouse"] != warehouse:
            continue
            
        # Product code filter
        if product_code and item_data["product_code"] != product_code:
            continue
            
        # Low stock filter
        if low_stock_only:
            min_level = item_data.get("minimum_level", 0)
            if min_level and item_data["quantity_available"] > min_level:
                continue
        
        filtered_items.append(item_data)
    
    # Apply pagination
    paginated_items = filtered_items[skip:skip + limit]
    return [SimpleInventoryItem(**item_data) for item_data in paginated_items]

@router.get("/items/{item_id}", response_model=SimpleInventoryItem)
async def get_inventory_item(item_id: str) -> SimpleInventoryItem:
    """Get inventory item by ID."""
    if item_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item_data = inventory_store[item_id]
    return SimpleInventoryItem(**item_data)

@router.post("/movements/", response_model=StockMovement)
async def create_stock_movement(movement_data: StockMovementCreate) -> StockMovement:
    """Create a stock movement and update inventory."""
    # Validate inventory item exists
    if movement_data.inventory_item_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Validate movement type and quantity
    movement_type = movement_data.movement_type.upper()
    if movement_type not in ["IN", "OUT", "ADJUSTMENT"]:
        raise HTTPException(status_code=400, detail="Invalid movement type. Use IN, OUT, or ADJUSTMENT")
    
    # Create movement record
    movement = StockMovement(
        inventory_item_id=movement_data.inventory_item_id,
        movement_type=movement_type,
        quantity=movement_data.quantity,
        reference=movement_data.reference,
        notes=movement_data.notes
    )
    
    # Update inventory quantities
    item_data = inventory_store[movement_data.inventory_item_id]
    
    if movement_type == "IN":
        item_data["quantity_on_hand"] += abs(movement_data.quantity)
        item_data["quantity_available"] += abs(movement_data.quantity)
    elif movement_type == "OUT":
        quantity_to_remove = abs(movement_data.quantity)
        if item_data["quantity_available"] < quantity_to_remove:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Available: {item_data['quantity_available']}, Requested: {quantity_to_remove}"
            )
        item_data["quantity_on_hand"] -= quantity_to_remove
        item_data["quantity_available"] -= quantity_to_remove
    elif movement_type == "ADJUSTMENT":
        # Adjustment can be positive or negative
        new_quantity = item_data["quantity_on_hand"] + movement_data.quantity
        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Adjustment would result in negative inventory")
        item_data["quantity_on_hand"] = new_quantity
        item_data["quantity_available"] = new_quantity - item_data["quantity_reserved"]
    
    item_data["updated_at"] = datetime.now()
    
    # Store movement
    movements_store[movement.id] = movement.model_dump()
    
    return movement

@router.get("/movements/", response_model=List[StockMovement])
async def list_stock_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    inventory_item_id: Optional[str] = Query(None),
    movement_type: Optional[str] = Query(None)
) -> List[StockMovement]:
    """List stock movements with filtering."""
    all_movements = list(movements_store.values())
    
    # Apply filters
    filtered_movements = []
    for movement_data in all_movements:
        # Inventory item filter
        if inventory_item_id and movement_data["inventory_item_id"] != inventory_item_id:
            continue
            
        # Movement type filter
        if movement_type and movement_data["movement_type"] != movement_type.upper():
            continue
        
        filtered_movements.append(movement_data)
    
    # Sort by creation date (newest first)
    filtered_movements.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    paginated_movements = filtered_movements[skip:skip + limit]
    return [StockMovement(**movement_data) for movement_data in paginated_movements]

@router.post("/reserve/{item_id}")
async def reserve_stock(
    item_id: str,
    quantity: float = Query(..., gt=0, description="Quantity to reserve")
) -> Dict[str, Any]:
    """Reserve stock for order fulfillment."""
    if item_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item_data = inventory_store[item_id]
    
    if item_data["quantity_available"] < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock available. Available: {item_data['quantity_available']}, Requested: {quantity}"
        )
    
    # Update quantities
    item_data["quantity_available"] -= quantity
    item_data["quantity_reserved"] += quantity
    item_data["updated_at"] = datetime.now()
    
    return {
        "message": "Stock reserved successfully",
        "item_id": item_id,
        "reserved_quantity": quantity,
        "remaining_available": item_data["quantity_available"]
    }

@router.post("/release/{item_id}")
async def release_reservation(
    item_id: str,
    quantity: float = Query(..., gt=0, description="Quantity to release")
) -> Dict[str, Any]:
    """Release reserved stock."""
    if item_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item_data = inventory_store[item_id]
    
    if item_data["quantity_reserved"] < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot release more than reserved. Reserved: {item_data['quantity_reserved']}, Requested: {quantity}"
        )
    
    # Update quantities
    item_data["quantity_available"] += quantity
    item_data["quantity_reserved"] -= quantity
    item_data["updated_at"] = datetime.now()
    
    return {
        "message": "Reservation released successfully",
        "item_id": item_id,
        "released_quantity": quantity,
        "available_quantity": item_data["quantity_available"]
    }

@router.get("/stats/summary")
async def get_inventory_summary() -> Dict[str, Any]:
    """Get inventory summary statistics."""
    all_items = [item for item in inventory_store.values() if item["is_active"]]
    
    if not all_items:
        return {
            "total_items": 0,
            "total_value": 0.0,
            "low_stock_items": 0,
            "warehouses": [],
            "last_updated": datetime.now().isoformat()
        }
    
    total_value = sum(
        item["quantity_on_hand"] * (item["unit_cost"] or 0)
        for item in all_items
    )
    
    low_stock_items = sum(
        1 for item in all_items
        if item.get("minimum_level") and item["quantity_available"] <= item["minimum_level"]
    )
    
    warehouses = list(set(item["warehouse"] for item in all_items))
    
    return {
        "total_items": len(all_items),
        "total_value": round(total_value, 2),
        "low_stock_items": low_stock_items,
        "total_movements": len(movements_store),
        "warehouses": warehouses,
        "last_updated": datetime.now().isoformat()
    }

@router.get("/alerts/low-stock")
async def get_low_stock_alerts() -> List[Dict[str, Any]]:
    """Get low stock alerts."""
    alerts = []
    
    for item_data in inventory_store.values():
        if not item_data["is_active"]:
            continue
            
        min_level = item_data.get("minimum_level")
        if min_level and item_data["quantity_available"] <= min_level:
            alerts.append({
                "item_id": item_data["id"],
                "product_code": item_data["product_code"],
                "product_name": item_data["product_name"],
                "warehouse": item_data["warehouse"],
                "current_quantity": item_data["quantity_available"],
                "minimum_level": min_level,
                "shortage": min_level - item_data["quantity_available"]
            })
    
    return alerts