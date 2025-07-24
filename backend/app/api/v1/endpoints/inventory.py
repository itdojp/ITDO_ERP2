"""
Inventory API Endpoints - CC02 v49.0 Implementation Overdrive Phase 2
48-Hour Backend Blitz - Inventory Management TDD Implementation
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
import uuid

# Import database and models
from app.core.database import get_db

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# Response models for TDD tests
class InventoryItemResponse(BaseModel):
    id: str
    product_id: str
    location: str
    quantity: int
    minimum_stock: Optional[int] = None
    maximum_stock: Optional[int] = None
    reserved_quantity: int = 0
    available_quantity: int
    created_at: datetime
    updated_at: datetime

class InventoryListResponse(BaseModel):
    items: List[InventoryItemResponse]
    total: int
    page: int = 1
    size: int = 50

class StockMovementResponse(BaseModel):
    id: str
    product_id: str
    location: str
    movement_type: str  # "in", "out", "transfer"
    quantity: int
    reason: Optional[str] = None
    reference: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None

class LowStockAlert(BaseModel):
    product_id: str
    product_name: str
    location: str
    current_quantity: int
    minimum_stock: int
    shortage: int

class LowStockAlertsResponse(BaseModel):
    alerts: List[LowStockAlert]
    total_alerts: int

class InventoryValuationItem(BaseModel):
    product_id: str
    product_name: str
    location: str
    quantity: int
    unit_price: float
    total_value: float

class InventoryValuationResponse(BaseModel):
    items: List[InventoryValuationItem]
    total_value: float
    items_count: int
    locations_count: int

class TransferResponse(BaseModel):
    id: str
    product_id: str
    from_location: str
    to_location: str
    quantity: int
    reason: Optional[str] = None
    created_at: datetime

class LocationResponse(BaseModel):
    name: str
    total_items: int
    total_quantity: int
    total_value: float

class LocationsListResponse(BaseModel):
    locations: List[LocationResponse]
    total_locations: int

# In-memory storage for TDD (will be replaced with database)
inventory_store: Dict[str, Dict[str, Any]] = {}
movements_store: Dict[str, Dict[str, Any]] = {}
transfers_store: Dict[str, Dict[str, Any]] = {}

# Import products store from products endpoint
from app.api.v1.endpoints.products import products_store

@router.post("/", response_model=InventoryItemResponse, status_code=201)
async def create_inventory_item(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> InventoryItemResponse:
    """Create a new inventory item"""
    
    try:
        inventory_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["product_id", "location", "quantity"]
    for field in required_fields:
        if field not in inventory_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate product exists
    product_id = inventory_data["product_id"]
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check for duplicate product-location combination
    for existing_item in inventory_store.values():
        if (existing_item["product_id"] == product_id and 
            existing_item["location"] == inventory_data["location"]):
            raise HTTPException(
                status_code=400,
                detail=f"Inventory item already exists for product {product_id} at location {inventory_data['location']}"
            )
    
    # Create inventory item
    item_id = str(uuid.uuid4())
    now = datetime.now()
    
    quantity = int(inventory_data["quantity"])
    reserved_quantity = inventory_data.get("reserved_quantity", 0)
    
    item = {
        "id": item_id,
        "product_id": product_id,
        "location": inventory_data["location"],
        "quantity": quantity,
        "minimum_stock": inventory_data.get("minimum_stock"),
        "maximum_stock": inventory_data.get("maximum_stock"),
        "reserved_quantity": reserved_quantity,
        "available_quantity": quantity - reserved_quantity,
        "created_at": now,
        "updated_at": now
    }
    
    inventory_store[item_id] = item
    return InventoryItemResponse(**item)

@router.get("/valuation", response_model=InventoryValuationResponse)
async def get_inventory_valuation(
    location: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> InventoryValuationResponse:
    """Get inventory valuation"""
    
    items = []
    total_value = 0.0
    locations = set()
    
    for item in inventory_store.values():
        if location and item["location"] != location:
            continue
            
        product = products_store.get(item["product_id"])
        if product:
            unit_price = product["price"]
            item_total_value = item["quantity"] * unit_price
            
            valuation_item = InventoryValuationItem(
                product_id=item["product_id"],
                product_name=product["name"],
                location=item["location"],
                quantity=item["quantity"],
                unit_price=unit_price,
                total_value=item_total_value
            )
            items.append(valuation_item)
            total_value += item_total_value
            locations.add(item["location"])
    
    return InventoryValuationResponse(
        items=items,
        total_value=round(total_value, 2),
        items_count=len(items),
        locations_count=len(locations)
    )

@router.get("/locations", response_model=LocationsListResponse)
async def get_inventory_locations(
    db: AsyncSession = Depends(get_db)
) -> LocationsListResponse:
    """Get all inventory locations with summary"""
    
    locations_data = {}
    
    for item in inventory_store.values():
        location = item["location"]
        if location not in locations_data:
            locations_data[location] = {
                "name": location,
                "total_items": 0,
                "total_quantity": 0,
                "total_value": 0.0
            }
        
        locations_data[location]["total_items"] += 1
        locations_data[location]["total_quantity"] += item["quantity"]
        
        # Calculate value
        product = products_store.get(item["product_id"])
        if product:
            locations_data[location]["total_value"] += item["quantity"] * product["price"]
    
    locations = [
        LocationResponse(
            name=data["name"],
            total_items=data["total_items"],
            total_quantity=data["total_quantity"],
            total_value=round(data["total_value"], 2)
        )
        for data in locations_data.values()
    ]
    
    return LocationsListResponse(
        locations=locations,
        total_locations=len(locations)
    )

@router.get("/alerts/low-stock", response_model=LowStockAlertsResponse)
async def get_low_stock_alerts(
    db: AsyncSession = Depends(get_db)
) -> LowStockAlertsResponse:
    """Get low stock alerts"""
    
    alerts = []
    for item in inventory_store.values():
        if (item["minimum_stock"] is not None and 
            item["quantity"] < item["minimum_stock"]):
            
            product = products_store.get(item["product_id"])
            if product:
                alert = LowStockAlert(
                    product_id=item["product_id"],
                    product_name=product["name"],
                    location=item["location"],
                    current_quantity=item["quantity"],
                    minimum_stock=item["minimum_stock"],
                    shortage=item["minimum_stock"] - item["quantity"]
                )
                alerts.append(alert)
    
    return LowStockAlertsResponse(
        alerts=alerts,
        total_alerts=len(alerts)
    )

@router.get("/product/{product_id}", response_model=InventoryListResponse)
async def get_inventory_by_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> InventoryListResponse:
    """Get inventory for a specific product"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    items = [
        InventoryItemResponse(**item) 
        for item in inventory_store.values() 
        if item["product_id"] == product_id
    ]
    
    return InventoryListResponse(
        items=items,
        total=len(items)
    )

@router.get("/{inventory_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    inventory_id: str,
    db: AsyncSession = Depends(get_db)
) -> InventoryItemResponse:
    """Get inventory item by ID"""
    
    if inventory_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item = inventory_store[inventory_id]
    return InventoryItemResponse(**item)

@router.put("/{inventory_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    inventory_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> InventoryItemResponse:
    """Update inventory item"""
    
    if inventory_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    item = inventory_store[inventory_id].copy()
    
    # Update fields
    for field, value in update_data.items():
        if field not in ["id", "product_id", "created_at"]:  # Prevent updating immutable fields
            if field == "quantity":
                item[field] = int(value)
                # Recalculate available quantity
                item["available_quantity"] = int(value) - item["reserved_quantity"]
            else:
                item[field] = value
    
    item["updated_at"] = datetime.now()
    inventory_store[inventory_id] = item
    
    return InventoryItemResponse(**item)

@router.post("/movements", response_model=StockMovementResponse, status_code=201)
async def create_stock_movement(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> StockMovementResponse:
    """Create a stock movement"""
    
    try:
        movement_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["product_id", "location", "movement_type", "quantity"]
    for field in required_fields:
        if field not in movement_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate product exists
    product_id = movement_data["product_id"]
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate movement type
    if movement_data["movement_type"] not in ["in", "out", "transfer"]:
        raise HTTPException(status_code=422, detail="Invalid movement type")
    
    # Create movement
    movement_id = str(uuid.uuid4())
    now = datetime.now()
    
    movement = {
        "id": movement_id,
        "product_id": product_id,
        "location": movement_data["location"],
        "movement_type": movement_data["movement_type"],
        "quantity": int(movement_data["quantity"]),
        "reason": movement_data.get("reason"),
        "reference": movement_data.get("reference"),
        "created_at": now,
        "created_by": movement_data.get("created_by")
    }
    
    movements_store[movement_id] = movement
    
    # Update inventory if item exists
    for item_id, item in inventory_store.items():
        if (item["product_id"] == product_id and 
            item["location"] == movement_data["location"]):
            
            if movement_data["movement_type"] == "in":
                item["quantity"] += int(movement_data["quantity"])
            elif movement_data["movement_type"] == "out":
                item["quantity"] -= int(movement_data["quantity"])
                if item["quantity"] < 0:
                    item["quantity"] = 0
            
            item["available_quantity"] = item["quantity"] - item["reserved_quantity"]
            item["updated_at"] = now
            break
    else:
        # Create new inventory item if movement is "in" and no existing item
        if movement_data["movement_type"] == "in":
            item_id = str(uuid.uuid4())
            item = {
                "id": item_id,
                "product_id": product_id,
                "location": movement_data["location"],
                "quantity": int(movement_data["quantity"]),
                "minimum_stock": None,
                "maximum_stock": None,
                "reserved_quantity": 0,
                "available_quantity": int(movement_data["quantity"]),
                "created_at": now,
                "updated_at": now
            }
            inventory_store[item_id] = item
    
    return StockMovementResponse(**movement)

@router.post("/transfer", response_model=TransferResponse, status_code=201)
async def create_inventory_transfer(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TransferResponse:
    """Create an inventory transfer between locations"""
    
    try:
        transfer_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["product_id", "from_location", "to_location", "quantity"]
    for field in required_fields:
        if field not in transfer_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    product_id = transfer_data["product_id"]
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    quantity = int(transfer_data["quantity"])
    from_location = transfer_data["from_location"]
    to_location = transfer_data["to_location"]
    
    # Find source inventory item
    source_item = None
    for item in inventory_store.values():
        if (item["product_id"] == product_id and 
            item["location"] == from_location):
            source_item = item
            break
    
    if not source_item:
        raise HTTPException(status_code=404, detail="Source inventory not found")
    
    if source_item["available_quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock for transfer")
    
    # Create transfer record
    transfer_id = str(uuid.uuid4())
    now = datetime.now()
    
    transfer = {
        "id": transfer_id,
        "product_id": product_id,
        "from_location": from_location,
        "to_location": to_location,
        "quantity": quantity,
        "reason": transfer_data.get("reason"),
        "created_at": now
    }
    
    transfers_store[transfer_id] = transfer
    
    # Update source inventory
    source_item["quantity"] -= quantity
    source_item["available_quantity"] -= quantity
    source_item["updated_at"] = now
    
    # Update or create destination inventory
    destination_item = None
    for item in inventory_store.values():
        if (item["product_id"] == product_id and 
            item["location"] == to_location):
            destination_item = item
            break
    
    if destination_item:
        destination_item["quantity"] += quantity
        destination_item["available_quantity"] += quantity
        destination_item["updated_at"] = now
    else:
        # Create new inventory item at destination
        dest_item_id = str(uuid.uuid4())
        dest_item = {
            "id": dest_item_id,
            "product_id": product_id,
            "location": to_location,
            "quantity": quantity,
            "minimum_stock": None,
            "maximum_stock": None,
            "reserved_quantity": 0,
            "available_quantity": quantity,
            "created_at": now,
            "updated_at": now
        }
        inventory_store[dest_item_id] = dest_item
    
    return TransferResponse(**transfer)

@router.get("/locations", response_model=LocationsListResponse)
async def get_inventory_locations(
    db: AsyncSession = Depends(get_db)
) -> LocationsListResponse:
    """Get all inventory locations with summary"""
    
    locations_data = {}
    
    for item in inventory_store.values():
        location = item["location"]
        if location not in locations_data:
            locations_data[location] = {
                "name": location,
                "total_items": 0,
                "total_quantity": 0,
                "total_value": 0.0
            }
        
        locations_data[location]["total_items"] += 1
        locations_data[location]["total_quantity"] += item["quantity"]
        
        # Calculate value
        product = products_store.get(item["product_id"])
        if product:
            locations_data[location]["total_value"] += item["quantity"] * product["price"]
    
    locations = [
        LocationResponse(
            name=data["name"],
            total_items=data["total_items"],
            total_quantity=data["total_quantity"],
            total_value=round(data["total_value"], 2)
        )
        for data in locations_data.values()
    ]
    
    return LocationsListResponse(
        locations=locations,
        total_locations=len(locations)
    )

# Health check endpoint for performance testing
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for inventory"""
    start_time = datetime.now()
    
    # Simulate some processing
    inventory_count = len(inventory_store)
    movements_count = len(movements_store)
    
    end_time = datetime.now()
    response_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "inventory_count": inventory_count,
        "movements_count": movements_count,
        "timestamp": start_time.isoformat()
    }