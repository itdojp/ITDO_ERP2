"""
Core Inventory API Endpoints - CC02 v50.0 Phase 2
12-Hour Core Business API Sprint - Inventory Management Implementation
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
import uuid
import json

# Import database dependencies
from app.core.database import get_db

router = APIRouter(prefix="/inventory", tags=["Core Inventory"])

# Enums for inventory management
class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    STORE = "store"
    DISTRIBUTION_CENTER = "distribution_center"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"

class MovementType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"

class AdjustmentType(str, Enum):
    MANUAL = "manual"
    SYSTEM = "system"
    CYCLE_COUNT = "cycle_count"
    DAMAGE = "damage"
    SHRINKAGE = "shrinkage"

class TransferStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Location models
class LocationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    location_type: LocationType
    is_active: bool = True
    capacity: Optional[float] = Field(None, ge=0)
    cost_center: Optional[str] = Field(None, max_length=50)

class LocationResponse(BaseModel):
    id: str
    name: str
    code: str
    address: Optional[str] = None
    location_type: LocationType
    is_active: bool = True
    capacity: Optional[float] = None
    cost_center: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LocationListResponse(BaseModel):
    items: List[LocationResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int

# Inventory item models
class InventoryItemCreateRequest(BaseModel):
    product_id: str
    location_id: str
    quantity: int = Field(ge=0)
    unit_cost: float = Field(ge=0)
    reorder_point: int = Field(10, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    
    @field_validator('max_stock')
    @classmethod
    def validate_max_stock(cls, v, info):
        if v is not None and 'reorder_point' in info.data:
            if v < info.data['reorder_point']:
                raise ValueError('max_stock must be >= reorder_point')
        return v

class InventoryItemResponse(BaseModel):
    id: str
    product_id: str
    location_id: str
    quantity: int
    unit_cost: float
    reorder_point: int
    max_stock: Optional[int] = None
    last_counted: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# Stock adjustment models
class StockAdjustmentRequest(BaseModel):
    quantity_change: int
    adjustment_type: AdjustmentType
    reason: str = Field(min_length=1, max_length=255)
    cost_adjustment: float = 0.0

class StockAdjustmentResponse(BaseModel):
    id: str
    inventory_item_id: str
    quantity: int  # New quantity after adjustment
    quantity_change: int
    adjustment_type: AdjustmentType
    reason: str
    cost_adjustment: float
    adjusted_at: datetime

# Movement models
class MovementCreateRequest(BaseModel):
    product_id: str
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    quantity: int = Field(gt=0)
    movement_type: MovementType
    reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

class MovementResponse(BaseModel):
    id: str
    product_id: str
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    quantity: int
    movement_type: MovementType
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

# Transfer models
class TransferCreateRequest(BaseModel):
    product_id: str
    from_location_id: str
    to_location_id: str
    quantity: int = Field(gt=0)
    notes: Optional[str] = Field(None, max_length=500)

class TransferResponse(BaseModel):
    id: str
    product_id: str
    from_location_id: str
    to_location_id: str
    quantity: int
    status: TransferStatus
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# Alert models
class LowStockAlert(BaseModel):
    inventory_item_id: str
    product_id: str
    location_id: str
    product_name: str
    location_name: str
    current_quantity: int
    reorder_point: int
    suggested_order_quantity: int

class LowStockAlertsResponse(BaseModel):
    items: List[LowStockAlert]
    total: int

# Valuation models
class InventoryValuationResponse(BaseModel):
    total_value: float
    total_items: int
    by_location: List[Dict[str, Any]]
    by_product: List[Dict[str, Any]]

# Real-time models
class LocationStock(BaseModel):
    location_id: str
    location_name: str
    quantity: int
    unit_cost: float
    total_value: float

class RealTimeInventoryResponse(BaseModel):
    product_id: str
    product_name: str
    total_quantity: int
    total_value: float
    locations: List[LocationStock]

# History models
class InventoryHistoryItem(BaseModel):
    id: str
    action: str
    quantity_before: int
    quantity_after: int
    quantity_change: int
    reason: str
    created_at: datetime

class InventoryHistoryResponse(BaseModel):
    inventory_item_id: str
    history: List[InventoryHistoryItem]
    total: int

# Statistics models
class InventoryStatisticsResponse(BaseModel):
    total_items: int
    total_locations: int
    total_value: float
    out_of_stock_items: int
    low_stock_items: int
    overstocked_items: int
    total_movements_today: int

# In-memory storage for core inventory TDD
locations_store: Dict[str, Dict[str, Any]] = {}
inventory_items_store: Dict[str, Dict[str, Any]] = {}
movements_store: Dict[str, Dict[str, Any]] = {}
adjustments_store: Dict[str, Dict[str, Any]] = {}
transfers_store: Dict[str, Dict[str, Any]] = {}

@router.post("/locations", response_model=LocationResponse, status_code=201)
async def create_location(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> LocationResponse:
    """Create a new inventory location"""
    
    try:
        location_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["name", "code", "location_type"]
    for field in required_fields:
        if field not in location_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Check for duplicate code
    code = location_data["code"]
    for existing_location in locations_store.values():
        if existing_location["code"] == code:
            raise HTTPException(
                status_code=400,
                detail=f"Location with code '{code}' already exists"
            )
    
    # Create location
    location_id = str(uuid.uuid4())
    now = datetime.now()
    
    location = {
        "id": location_id,
        "name": location_data["name"],
        "code": location_data["code"],
        "address": location_data.get("address"),
        "location_type": location_data["location_type"],
        "is_active": location_data.get("is_active", True),
        "capacity": location_data.get("capacity"),
        "cost_center": location_data.get("cost_center"),
        "created_at": now,
        "updated_at": now
    }
    
    locations_store[location_id] = location
    return LocationResponse(**location)

@router.get("/locations", response_model=LocationListResponse)
async def list_locations(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    location_type: Optional[LocationType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> LocationListResponse:
    """List inventory locations with filtering"""
    
    all_locations = list(locations_store.values())
    
    # Apply filters
    if location_type:
        all_locations = [loc for loc in all_locations if loc["location_type"] == location_type.value]
    
    if is_active is not None:
        all_locations = [loc for loc in all_locations if loc["is_active"] == is_active]
    
    # Sort by created_at descending
    all_locations.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(all_locations)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_locations = all_locations[start_idx:end_idx]
    
    # Convert to response format
    items = [LocationResponse(**location) for location in paginated_locations]
    
    return LocationListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )

@router.post("/items", response_model=InventoryItemResponse, status_code=201)
async def create_inventory_item(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> InventoryItemResponse:
    """Create a new inventory item"""
    
    try:
        item_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["product_id", "location_id", "quantity", "unit_cost"]
    for field in required_fields:
        if field not in item_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate product and location exist
    product_id = item_data["product_id"]
    location_id = item_data["location_id"]
    
    # Check if location exists
    if location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if product exists (import from products_core)
    try:
        from app.api.v1.endpoints.products_core import products_store
        if product_id not in products_store:
            raise HTTPException(status_code=404, detail="Product not found")
    except ImportError:
        pass  # Products module not available, skip validation
    
    # Create inventory item
    item_id = str(uuid.uuid4())
    now = datetime.now()
    
    inventory_item = {
        "id": item_id,
        "product_id": product_id,
        "location_id": location_id,
        "quantity": int(item_data["quantity"]),
        "unit_cost": float(item_data["unit_cost"]),
        "reorder_point": item_data.get("reorder_point", 10),
        "max_stock": item_data.get("max_stock"),
        "last_counted": None,
        "created_at": now,
        "updated_at": now
    }
    
    inventory_items_store[item_id] = inventory_item
    return InventoryItemResponse(**inventory_item)

@router.post("/items/{item_id}/adjust", response_model=StockAdjustmentResponse)
async def adjust_stock(
    item_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> StockAdjustmentResponse:
    """Adjust inventory stock quantity"""
    
    if item_id not in inventory_items_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    try:
        adjustment_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["quantity_change", "adjustment_type", "reason"]
    for field in required_fields:
        if field not in adjustment_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    inventory_item = inventory_items_store[item_id]
    
    # Calculate new quantity
    quantity_change = int(adjustment_data["quantity_change"])
    new_quantity = inventory_item["quantity"] + quantity_change
    
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock for adjustment")
    
    # Update inventory item
    inventory_item["quantity"] = new_quantity
    inventory_item["updated_at"] = datetime.now()
    
    # Create adjustment record
    adjustment_id = str(uuid.uuid4())
    now = datetime.now()
    
    adjustment = {
        "id": adjustment_id,
        "inventory_item_id": item_id,
        "quantity": new_quantity,
        "quantity_change": quantity_change,
        "adjustment_type": adjustment_data["adjustment_type"],
        "reason": adjustment_data["reason"],
        "cost_adjustment": adjustment_data.get("cost_adjustment", 0.0),
        "adjusted_at": now
    }
    
    adjustments_store[adjustment_id] = adjustment
    return StockAdjustmentResponse(**adjustment)

@router.post("/movements", response_model=MovementResponse, status_code=201)
async def create_movement(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> MovementResponse:
    """Create a stock movement record"""
    
    try:
        movement_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["product_id", "quantity", "movement_type"]
    for field in required_fields:
        if field not in movement_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Create movement
    movement_id = str(uuid.uuid4())
    now = datetime.now()
    
    movement = {
        "id": movement_id,
        "product_id": movement_data["product_id"],
        "from_location_id": movement_data.get("from_location_id"),
        "to_location_id": movement_data.get("to_location_id"),
        "quantity": int(movement_data["quantity"]),
        "movement_type": movement_data["movement_type"],
        "reference": movement_data.get("reference"),
        "notes": movement_data.get("notes"),
        "created_at": now
    }
    
    movements_store[movement_id] = movement
    return MovementResponse(**movement)

@router.post("/transfers", response_model=TransferResponse, status_code=201)
async def create_transfer(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TransferResponse:
    """Create an inventory transfer between locations"""
    
    try:
        transfer_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["product_id", "from_location_id", "to_location_id", "quantity"]
    for field in required_fields:
        if field not in transfer_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate locations exist
    from_location_id = transfer_data["from_location_id"]
    to_location_id = transfer_data["to_location_id"]
    
    if from_location_id not in locations_store:
        raise HTTPException(status_code=404, detail="From location not found")
    
    if to_location_id not in locations_store:
        raise HTTPException(status_code=404, detail="To location not found")
    
    if from_location_id == to_location_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same location")
    
    # Create transfer
    transfer_id = str(uuid.uuid4())
    now = datetime.now()
    
    transfer = {
        "id": transfer_id,
        "product_id": transfer_data["product_id"],
        "from_location_id": from_location_id,
        "to_location_id": to_location_id,
        "quantity": int(transfer_data["quantity"]),
        "status": TransferStatus.COMPLETED.value,  # Simplified - auto-complete for TDD
        "notes": transfer_data.get("notes"),
        "created_at": now,
        "completed_at": now
    }
    
    transfers_store[transfer_id] = transfer
    return TransferResponse(**transfer)

@router.get("/alerts/low-stock", response_model=LowStockAlertsResponse)
async def get_low_stock_alerts(
    db: AsyncSession = Depends(get_db)
) -> LowStockAlertsResponse:
    """Get low stock alerts"""
    
    alerts = []
    
    for item in inventory_items_store.values():
        if item["quantity"] <= item["reorder_point"]:
            # Get product and location names
            product_name = "Unknown Product"
            location_name = "Unknown Location"
            
            try:
                from app.api.v1.endpoints.products_core import products_store
                if item["product_id"] in products_store:
                    product_name = products_store[item["product_id"]]["name"]
            except ImportError:
                pass
            
            if item["location_id"] in locations_store:
                location_name = locations_store[item["location_id"]]["name"]
            
            suggested_quantity = max(item["max_stock"] or 100, item["reorder_point"] * 2) - item["quantity"]
            
            alert = LowStockAlert(
                inventory_item_id=item["id"],
                product_id=item["product_id"],
                location_id=item["location_id"],
                product_name=product_name,
                location_name=location_name,
                current_quantity=item["quantity"],
                reorder_point=item["reorder_point"],
                suggested_order_quantity=suggested_quantity
            )
            alerts.append(alert)
    
    return LowStockAlertsResponse(items=alerts, total=len(alerts))

@router.get("/valuation", response_model=InventoryValuationResponse)
async def get_inventory_valuation(
    db: AsyncSession = Depends(get_db)
) -> InventoryValuationResponse:
    """Calculate inventory valuation"""
    
    total_value = 0.0
    total_items = 0
    by_location = {}
    by_product = {}
    
    for item in inventory_items_store.values():
        item_value = item["quantity"] * item["unit_cost"]
        total_value += item_value
        total_items += item["quantity"]
        
        # By location
        location_id = item["location_id"]
        if location_id not in by_location:
            location_name = locations_store.get(location_id, {}).get("name", "Unknown")
            by_location[location_id] = {
                "location_id": location_id,
                "location_name": location_name,
                "total_value": 0.0,
                "total_items": 0
            }
        by_location[location_id]["total_value"] += item_value
        by_location[location_id]["total_items"] += item["quantity"]
        
        # By product
        product_id = item["product_id"]
        if product_id not in by_product:
            product_name = "Unknown Product"
            try:
                from app.api.v1.endpoints.products_core import products_store
                if product_id in products_store:
                    product_name = products_store[product_id]["name"]
            except ImportError:
                pass
            
            by_product[product_id] = {
                "product_id": product_id,
                "product_name": product_name,
                "total_value": 0.0,
                "total_quantity": 0
            }
        by_product[product_id]["total_value"] += item_value
        by_product[product_id]["total_quantity"] += item["quantity"]
    
    return InventoryValuationResponse(
        total_value=round(total_value, 2),
        total_items=total_items,
        by_location=list(by_location.values()),
        by_product=list(by_product.values())
    )

@router.get("/real-time/{product_id}", response_model=RealTimeInventoryResponse)
async def get_real_time_inventory(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> RealTimeInventoryResponse:
    """Get real-time inventory levels for a product"""
    
    product_name = "Unknown Product"
    try:
        from app.api.v1.endpoints.products_core import products_store
        if product_id in products_store:
            product_name = products_store[product_id]["name"]
    except ImportError:
        pass
    
    locations = []
    total_quantity = 0
    total_value = 0.0
    
    for item in inventory_items_store.values():
        if item["product_id"] == product_id:
            location_name = locations_store.get(item["location_id"], {}).get("name", "Unknown")
            item_value = item["quantity"] * item["unit_cost"]
            
            location_stock = LocationStock(
                location_id=item["location_id"],
                location_name=location_name,
                quantity=item["quantity"],
                unit_cost=item["unit_cost"],
                total_value=item_value
            )
            locations.append(location_stock)
            
            total_quantity += item["quantity"]
            total_value += item_value
    
    return RealTimeInventoryResponse(
        product_id=product_id,
        product_name=product_name,
        total_quantity=total_quantity,
        total_value=round(total_value, 2),
        locations=locations
    )

@router.get("/items/{item_id}/history", response_model=InventoryHistoryResponse)
async def get_inventory_history(
    item_id: str,
    db: AsyncSession = Depends(get_db)
) -> InventoryHistoryResponse:
    """Get inventory item history"""
    
    if item_id not in inventory_items_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Get all adjustments for this item
    history_items = []
    for adjustment in adjustments_store.values():
        if adjustment["inventory_item_id"] == item_id:
            quantity_before = adjustment["quantity"] - adjustment["quantity_change"]
            
            history_item = InventoryHistoryItem(
                id=adjustment["id"],
                action=f"Stock {adjustment['adjustment_type']}",
                quantity_before=quantity_before,
                quantity_after=adjustment["quantity"],
                quantity_change=adjustment["quantity_change"],
                reason=adjustment["reason"],
                created_at=adjustment["adjusted_at"]
            )
            history_items.append(history_item)
    
    # Sort by created_at descending
    history_items.sort(key=lambda x: x.created_at, reverse=True)
    
    return InventoryHistoryResponse(
        inventory_item_id=item_id,
        history=history_items,
        total=len(history_items)
    )

@router.get("/statistics", response_model=InventoryStatisticsResponse)
async def get_inventory_statistics(
    db: AsyncSession = Depends(get_db)
) -> InventoryStatisticsResponse:
    """Get comprehensive inventory statistics"""
    
    total_items = sum(item["quantity"] for item in inventory_items_store.values())
    total_locations = len(locations_store)
    total_value = sum(item["quantity"] * item["unit_cost"] for item in inventory_items_store.values())
    
    out_of_stock_items = len([item for item in inventory_items_store.values() if item["quantity"] == 0])
    low_stock_items = len([item for item in inventory_items_store.values() if item["quantity"] <= item["reorder_point"]])
    overstocked_items = len([item for item in inventory_items_store.values() 
                           if item["max_stock"] and item["quantity"] > item["max_stock"]])
    
    # Count today's movements (simplified)
    total_movements_today = len(movements_store)
    
    return InventoryStatisticsResponse(
        total_items=total_items,
        total_locations=total_locations,
        total_value=round(total_value, 2),
        out_of_stock_items=out_of_stock_items,
        low_stock_items=low_stock_items,
        overstocked_items=overstocked_items,
        total_movements_today=total_movements_today
    )

# Health check endpoint for performance testing
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for core inventory API"""
    start_time = datetime.now()
    
    # Simulate some processing
    locations_count = len(locations_store)
    items_count = len(inventory_items_store)
    movements_count = len(movements_store)
    
    end_time = datetime.now()
    response_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "locations_count": locations_count,
        "items_count": items_count,
        "movements_count": movements_count,
        "timestamp": start_time.isoformat()
    }