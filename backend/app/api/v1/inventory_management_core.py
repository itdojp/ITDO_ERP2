"""
Inventory Management Core API - CC02 v48.0 Phase 2
Real-time inventory tracking, adjustments, multi-location management
TDD implementation with comprehensive validation and caching
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from decimal import Decimal
import uuid
from enum import Enum
import json

# Import product stores for inventory linking
from app.api.v1.simple_products import products_store
from app.api.v1.advanced_product_management import advanced_products_store

router = APIRouter(prefix="/inventory", tags=["Inventory Management Core"])

# Enums for inventory management
class MovementType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN = "return"
    DAMAGE = "damage"
    STOCK_TAKE = "stock_take"

class InventoryStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    DAMAGED = "damaged"
    QUARANTINE = "quarantine"
    OUT_OF_STOCK = "out_of_stock"

class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    STORE = "store"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    TRANSIT = "transit"

# Core Models
class Location(BaseModel):
    """Inventory location model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., min_length=1, max_length=50, description="Location code")
    name: str = Field(..., min_length=1, max_length=200, description="Location name")
    type: LocationType = Field(..., description="Location type")
    address: Optional[str] = Field(None, max_length=500, description="Location address")
    is_active: bool = Field(default=True, description="Location active status")
    capacity: Optional[int] = Field(None, ge=0, description="Storage capacity")
    manager_id: Optional[str] = Field(None, description="Location manager ID")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class InventoryItem(BaseModel):
    """Core inventory item model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = Field(..., description="Product ID")
    location_id: str = Field(..., description="Location ID")
    quantity_available: int = Field(default=0, ge=0, description="Available quantity")
    quantity_reserved: int = Field(default=0, ge=0, description="Reserved quantity")
    quantity_damaged: int = Field(default=0, ge=0, description="Damaged quantity")
    reorder_point: int = Field(default=10, ge=0, description="Reorder point threshold")
    max_stock_level: Optional[int] = Field(None, ge=0, description="Maximum stock level")
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, description="Cost per unit")
    last_movement_date: Optional[datetime] = Field(None, description="Last stock movement date")
    status: InventoryStatus = Field(default=InventoryStatus.AVAILABLE)
    batch_number: Optional[str] = Field(None, description="Batch/lot number")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_quantity(self) -> int:
        """Calculate total quantity across all statuses"""
        return self.quantity_available + self.quantity_reserved + self.quantity_damaged

class InventoryMovement(BaseModel):
    """Inventory movement/transaction model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = Field(..., description="Product ID")
    location_id: str = Field(..., description="Location ID")
    movement_type: MovementType = Field(..., description="Type of movement")
    quantity: int = Field(..., description="Quantity moved (positive for in, negative for out)")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost")
    reference_number: Optional[str] = Field(None, description="Reference document number")
    notes: Optional[str] = Field(None, max_length=1000, description="Movement notes")
    batch_number: Optional[str] = Field(None, description="Batch/lot number")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    user_id: Optional[str] = Field(None, description="User who made the movement")
    created_at: datetime = Field(default_factory=datetime.now)

class StockAdjustmentRequest(BaseModel):
    """Request model for stock adjustments"""
    product_id: str = Field(..., description="Product ID")
    location_id: str = Field(..., description="Location ID")
    adjustment_quantity: int = Field(..., description="Adjustment quantity (positive or negative)")
    reason: str = Field(..., min_length=1, max_length=500, description="Adjustment reason")
    reference_number: Optional[str] = Field(None, description="Reference number")
    user_id: Optional[str] = Field(None, description="User making adjustment")

class TransferRequest(BaseModel):
    """Request model for inventory transfers"""
    product_id: str = Field(..., description="Product ID")
    from_location_id: str = Field(..., description="Source location ID")
    to_location_id: str = Field(..., description="Destination location ID")
    quantity: int = Field(..., gt=0, description="Quantity to transfer")
    reason: Optional[str] = Field(None, max_length=500, description="Transfer reason")
    reference_number: Optional[str] = Field(None, description="Reference number")
    user_id: Optional[str] = Field(None, description="User initiating transfer")

class InventoryAlert(BaseModel):
    """Inventory alert model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = Field(..., description="Product ID")
    location_id: str = Field(..., description="Location ID")
    alert_type: str = Field(..., description="Alert type (low_stock, out_of_stock, expiring)")
    message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Alert severity (low, medium, high, critical)")
    is_acknowledged: bool = Field(default=False, description="Alert acknowledgment status")
    created_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    acknowledged_by: Optional[str] = Field(None, description="User who acknowledged")

class ReorderSuggestion(BaseModel):
    """Automatic reorder suggestion model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = Field(..., description="Product ID")
    location_id: str = Field(..., description="Location ID")
    current_stock: int = Field(..., description="Current stock level")
    reorder_point: int = Field(..., description="Reorder point threshold")
    suggested_quantity: int = Field(..., description="Suggested reorder quantity")
    estimated_cost: Optional[Decimal] = Field(None, description="Estimated reorder cost")
    priority: str = Field(..., description="Reorder priority")
    created_at: datetime = Field(default_factory=datetime.now)

# In-memory storage
locations_store: Dict[str, Dict[str, Any]] = {}
inventory_items_store: Dict[str, Dict[str, Any]] = {}
inventory_movements_store: Dict[str, Dict[str, Any]] = {}
inventory_alerts_store: Dict[str, Dict[str, Any]] = {}
reorder_suggestions_store: Dict[str, Dict[str, Any]] = {}

# Cache for real-time inventory data
inventory_cache: Dict[str, Dict[str, Any]] = {}

# Helper functions
def get_product_info(product_id: str) -> Optional[Dict[str, Any]]:
    """Get product information from product stores"""
    if product_id in advanced_products_store:
        return advanced_products_store[product_id]
    elif product_id in products_store:
        return products_store[product_id]
    return None

def update_inventory_cache(product_id: str, location_id: str):
    """Update inventory cache for real-time access"""
    cache_key = f"{product_id}_{location_id}"
    
    # Find inventory item
    inventory_item = None
    for item_data in inventory_items_store.values():
        if item_data["product_id"] == product_id and item_data["location_id"] == location_id:
            inventory_item = item_data
            break
    
    if inventory_item:
        inventory_cache[cache_key] = {
            "product_id": product_id,
            "location_id": location_id,
            "quantity_available": inventory_item["quantity_available"],
            "quantity_reserved": inventory_item["quantity_reserved"],
            "quantity_damaged": inventory_item["quantity_damaged"],
            "total_quantity": inventory_item["quantity_available"] + inventory_item["quantity_reserved"] + inventory_item["quantity_damaged"],
            "status": inventory_item["status"],
            "last_updated": datetime.now().isoformat()
        }

def check_low_stock_alerts(product_id: str, location_id: str):
    """Check and create low stock alerts"""
    cache_key = f"{product_id}_{location_id}"
    if cache_key not in inventory_cache:
        return
    
    inventory_data = inventory_cache[cache_key]
    
    # Find inventory item to get reorder point
    for item_data in inventory_items_store.values():
        if item_data["product_id"] == product_id and item_data["location_id"] == location_id:
            reorder_point = item_data.get("reorder_point", 10)
            available_qty = inventory_data["quantity_available"]
            
            if available_qty <= 0:
                # Out of stock alert
                alert = InventoryAlert(
                    product_id=product_id,
                    location_id=location_id,
                    alert_type="out_of_stock",
                    message=f"Product is out of stock at location",
                    severity="critical"
                )
                inventory_alerts_store[alert.id] = alert.dict()
                
                # Create reorder suggestion
                suggestion = ReorderSuggestion(
                    product_id=product_id,
                    location_id=location_id,
                    current_stock=available_qty,
                    reorder_point=reorder_point,
                    suggested_quantity=reorder_point * 2,  # Simple rule
                    priority="high"
                )
                reorder_suggestions_store[suggestion.id] = suggestion.dict()
                
            elif available_qty <= reorder_point:
                # Low stock alert
                alert = InventoryAlert(
                    product_id=product_id,
                    location_id=location_id,
                    alert_type="low_stock",
                    message=f"Stock level ({available_qty}) is below reorder point ({reorder_point})",
                    severity="medium"
                )
                inventory_alerts_store[alert.id] = alert.dict()
                
                # Create reorder suggestion
                suggestion = ReorderSuggestion(
                    product_id=product_id,
                    location_id=location_id,
                    current_stock=available_qty,
                    reorder_point=reorder_point,
                    suggested_quantity=reorder_point * 2 - available_qty,
                    priority="medium"
                )
                reorder_suggestions_store[suggestion.id] = suggestion.dict()
            break

# API Endpoints

@router.post("/locations", response_model=Location)
async def create_location(location_data: Location) -> Location:
    """Create a new inventory location"""
    
    # Check for duplicate code
    for existing_location in locations_store.values():
        if existing_location["code"] == location_data.code:
            raise HTTPException(
                status_code=400,
                detail=f"Location with code '{location_data.code}' already exists"
            )
    
    location = Location(**location_data.dict())
    locations_store[location.id] = location.dict()
    
    return location

@router.get("/locations", response_model=List[Location])
async def list_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    location_type: Optional[LocationType] = Query(None),
    is_active: Optional[bool] = Query(None)
) -> List[Location]:
    """List inventory locations"""
    
    all_locations = list(locations_store.values())
    
    # Apply filters
    if location_type:
        all_locations = [loc for loc in all_locations if loc.get("type") == location_type]
    
    if is_active is not None:
        all_locations = [loc for loc in all_locations if loc.get("is_active") == is_active]
    
    # Apply pagination
    paginated_locations = all_locations[skip:skip + limit]
    
    return [Location(**location_data) for location_data in paginated_locations]

@router.get("/locations/{location_id}", response_model=Location)
async def get_location(location_id: str) -> Location:
    """Get location by ID"""
    
    if location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return Location(**locations_store[location_id])

@router.get("/items", response_model=List[InventoryItem])
async def list_inventory_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    product_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    status: Optional[InventoryStatus] = Query(None),
    low_stock_only: bool = Query(False, description="Show only low stock items")
) -> List[InventoryItem]:
    """List inventory items with filtering"""
    
    all_items = list(inventory_items_store.values())
    
    # Apply filters
    if product_id:
        all_items = [item for item in all_items if item.get("product_id") == product_id]
    
    if location_id:
        all_items = [item for item in all_items if item.get("location_id") == location_id]
    
    if status:
        all_items = [item for item in all_items if item.get("status") == status]
    
    if low_stock_only:
        all_items = [
            item for item in all_items 
            if item.get("quantity_available", 0) <= item.get("reorder_point", 10)
        ]
    
    # Apply pagination
    paginated_items = all_items[skip:skip + limit]
    
    return [InventoryItem(**item_data) for item_data in paginated_items]

@router.post("/items", response_model=InventoryItem)
async def create_inventory_item(item_data: InventoryItem) -> InventoryItem:
    """Create a new inventory item"""
    
    # Validate product exists
    product = get_product_info(item_data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate location exists
    if item_data.location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check for duplicate product-location combination
    for existing_item in inventory_items_store.values():
        if (existing_item["product_id"] == item_data.product_id and 
            existing_item["location_id"] == item_data.location_id):
            raise HTTPException(
                status_code=400,
                detail="Inventory item already exists for this product-location combination"
            )
    
    item = InventoryItem(**item_data.dict())
    inventory_items_store[item.id] = item.dict()
    
    # Update cache
    update_inventory_cache(item.product_id, item.location_id)
    
    # Check for alerts
    check_low_stock_alerts(item.product_id, item.location_id)
    
    return item

@router.get("/items/{item_id}", response_model=InventoryItem)
async def get_inventory_item(item_id: str) -> InventoryItem:
    """Get inventory item by ID"""
    
    if item_id not in inventory_items_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    return InventoryItem(**inventory_items_store[item_id])

@router.get("/real-time/{product_id}/{location_id}")
async def get_real_time_inventory(product_id: str, location_id: str) -> Dict[str, Any]:
    """Get real-time inventory data from cache"""
    
    cache_key = f"{product_id}_{location_id}"
    
    if cache_key not in inventory_cache:
        # Try to build cache from inventory items
        update_inventory_cache(product_id, location_id)
    
    if cache_key not in inventory_cache:
        raise HTTPException(status_code=404, detail="Inventory not found for this product-location combination")
    
    return inventory_cache[cache_key]

@router.post("/adjustments", response_model=InventoryMovement)
async def make_stock_adjustment(adjustment: StockAdjustmentRequest) -> InventoryMovement:
    """Make stock level adjustment"""
    
    # Validate product and location
    product = get_product_info(adjustment.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if adjustment.location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Find or create inventory item
    inventory_item = None
    for item_data in inventory_items_store.values():
        if (item_data["product_id"] == adjustment.product_id and 
            item_data["location_id"] == adjustment.location_id):
            inventory_item = item_data
            break
    
    if not inventory_item:
        # Create new inventory item
        new_item = InventoryItem(
            product_id=adjustment.product_id,
            location_id=adjustment.location_id,
            quantity_available=max(0, adjustment.adjustment_quantity)
        )
        inventory_items_store[new_item.id] = new_item.dict()
        inventory_item = new_item.dict()
    else:
        # Update existing inventory
        new_quantity = inventory_item["quantity_available"] + adjustment.adjustment_quantity
        if new_quantity < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Adjustment would result in negative stock. Current: {inventory_item['quantity_available']}, Adjustment: {adjustment.adjustment_quantity}"
            )
        
        inventory_item["quantity_available"] = new_quantity
        inventory_item["last_movement_date"] = datetime.now()
        inventory_item["updated_at"] = datetime.now()
    
    # Create movement record
    movement = InventoryMovement(
        product_id=adjustment.product_id,
        location_id=adjustment.location_id,
        movement_type=MovementType.ADJUSTMENT,
        quantity=adjustment.adjustment_quantity,
        reference_number=adjustment.reference_number,
        notes=adjustment.reason,
        user_id=adjustment.user_id
    )
    
    inventory_movements_store[movement.id] = movement.dict()
    
    # Update cache and check alerts
    update_inventory_cache(adjustment.product_id, adjustment.location_id)
    check_low_stock_alerts(adjustment.product_id, adjustment.location_id)
    
    return movement

@router.post("/transfers", response_model=Dict[str, str])
async def transfer_inventory(transfer: TransferRequest) -> Dict[str, str]:
    """Transfer inventory between locations"""
    
    # Validate product
    product = get_product_info(transfer.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate locations
    if transfer.from_location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Source location not found")
    
    if transfer.to_location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Destination location not found")
    
    if transfer.from_location_id == transfer.to_location_id:
        raise HTTPException(status_code=400, detail="Source and destination locations cannot be the same")
    
    # Find source inventory item
    source_item = None
    for item_data in inventory_items_store.values():
        if (item_data["product_id"] == transfer.product_id and 
            item_data["location_id"] == transfer.from_location_id):
            source_item = item_data
            break
    
    if not source_item or source_item["quantity_available"] < transfer.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock at source location. Available: {source_item['quantity_available'] if source_item else 0}, Requested: {transfer.quantity}"
        )
    
    # Update source inventory
    source_item["quantity_available"] -= transfer.quantity
    source_item["last_movement_date"] = datetime.now()
    source_item["updated_at"] = datetime.now()
    
    # Find or create destination inventory item
    dest_item = None
    for item_data in inventory_items_store.values():
        if (item_data["product_id"] == transfer.product_id and 
            item_data["location_id"] == transfer.to_location_id):
            dest_item = item_data
            break
    
    if not dest_item:
        # Create new inventory item at destination
        new_item = InventoryItem(
            product_id=transfer.product_id,
            location_id=transfer.to_location_id,
            quantity_available=transfer.quantity
        )
        inventory_items_store[new_item.id] = new_item.dict()
    else:
        # Update existing destination inventory
        dest_item["quantity_available"] += transfer.quantity
        dest_item["last_movement_date"] = datetime.now()
        dest_item["updated_at"] = datetime.now()
    
    # Create movement records
    # Outbound movement
    out_movement = InventoryMovement(
        product_id=transfer.product_id,
        location_id=transfer.from_location_id,
        movement_type=MovementType.TRANSFER,
        quantity=-transfer.quantity,  # Negative for outbound
        reference_number=transfer.reference_number,
        notes=f"Transfer to {transfer.to_location_id}: {transfer.reason}",
        user_id=transfer.user_id
    )
    inventory_movements_store[out_movement.id] = out_movement.dict()
    
    # Inbound movement
    in_movement = InventoryMovement(
        product_id=transfer.product_id,
        location_id=transfer.to_location_id,
        movement_type=MovementType.TRANSFER,
        quantity=transfer.quantity,  # Positive for inbound
        reference_number=transfer.reference_number,
        notes=f"Transfer from {transfer.from_location_id}: {transfer.reason}",
        user_id=transfer.user_id
    )
    inventory_movements_store[in_movement.id] = in_movement.dict()
    
    # Update cache and check alerts for both locations
    update_inventory_cache(transfer.product_id, transfer.from_location_id)
    update_inventory_cache(transfer.product_id, transfer.to_location_id)
    check_low_stock_alerts(transfer.product_id, transfer.from_location_id)
    check_low_stock_alerts(transfer.product_id, transfer.to_location_id)
    
    return {
        "message": "Transfer completed successfully",
        "transfer_id": f"{out_movement.id}-{in_movement.id}",
        "out_movement_id": out_movement.id,
        "in_movement_id": in_movement.id
    }

@router.get("/movements", response_model=List[InventoryMovement])
async def list_inventory_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    product_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    movement_type: Optional[MovementType] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
) -> List[InventoryMovement]:
    """List inventory movements with filtering"""
    
    all_movements = list(inventory_movements_store.values())
    
    # Apply filters
    if product_id:
        all_movements = [mov for mov in all_movements if mov.get("product_id") == product_id]
    
    if location_id:
        all_movements = [mov for mov in all_movements if mov.get("location_id") == location_id]
    
    if movement_type:
        all_movements = [mov for mov in all_movements if mov.get("movement_type") == movement_type]
    
    if date_from:
        all_movements = [
            mov for mov in all_movements 
            if datetime.fromisoformat(mov.get("created_at", "")).date() >= date_from
        ]
    
    if date_to:
        all_movements = [
            mov for mov in all_movements 
            if datetime.fromisoformat(mov.get("created_at", "")).date() <= date_to
        ]
    
    # Sort by created_at descending
    all_movements.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Apply pagination
    paginated_movements = all_movements[skip:skip + limit]
    
    return [InventoryMovement(**movement_data) for movement_data in paginated_movements]

@router.get("/alerts", response_model=List[InventoryAlert])
async def list_inventory_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    alert_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_acknowledged: Optional[bool] = Query(None)
) -> List[InventoryAlert]:
    """List inventory alerts"""
    
    all_alerts = list(inventory_alerts_store.values())
    
    # Apply filters
    if alert_type:
        all_alerts = [alert for alert in all_alerts if alert.get("alert_type") == alert_type]
    
    if severity:
        all_alerts = [alert for alert in all_alerts if alert.get("severity") == severity]
    
    if is_acknowledged is not None:
        all_alerts = [alert for alert in all_alerts if alert.get("is_acknowledged") == is_acknowledged]
    
    # Sort by created_at descending
    all_alerts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Apply pagination
    paginated_alerts = all_alerts[skip:skip + limit]
    
    return [InventoryAlert(**alert_data) for alert_data in paginated_alerts]

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user_id: Optional[str] = None) -> Dict[str, str]:
    """Acknowledge an inventory alert"""
    
    if alert_id not in inventory_alerts_store:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert = inventory_alerts_store[alert_id]
    alert["is_acknowledged"] = True
    alert["acknowledged_at"] = datetime.now()
    alert["acknowledged_by"] = user_id
    
    return {"message": "Alert acknowledged successfully", "alert_id": alert_id}

@router.get("/reorder-suggestions", response_model=List[ReorderSuggestion])
async def list_reorder_suggestions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    priority: Optional[str] = Query(None)
) -> List[ReorderSuggestion]:
    """List automatic reorder suggestions"""
    
    all_suggestions = list(reorder_suggestions_store.values())
    
    # Apply filters
    if priority:
        all_suggestions = [sug for sug in all_suggestions if sug.get("priority") == priority]
    
    # Sort by priority and created_at
    priority_order = {"high": 3, "medium": 2, "low": 1}
    all_suggestions.sort(
        key=lambda x: (priority_order.get(x.get("priority", "low"), 1), x.get("created_at", "")), 
        reverse=True
    )
    
    # Apply pagination
    paginated_suggestions = all_suggestions[skip:skip + limit]
    
    return [ReorderSuggestion(**suggestion_data) for suggestion_data in paginated_suggestions]

@router.get("/statistics")
async def get_inventory_statistics() -> Dict[str, Any]:
    """Get comprehensive inventory statistics"""
    
    # Basic counts
    total_locations = len(locations_store)
    active_locations = len([loc for loc in locations_store.values() if loc.get("is_active", True)])
    total_inventory_items = len(inventory_items_store)
    total_movements = len(inventory_movements_store)
    total_alerts = len(inventory_alerts_store)
    unacknowledged_alerts = len([alert for alert in inventory_alerts_store.values() if not alert.get("is_acknowledged", False)])
    
    # Stock levels
    low_stock_items = 0
    out_of_stock_items = 0
    total_stock_value = Decimal('0')
    
    for item in inventory_items_store.values():
        available_qty = item.get("quantity_available", 0)
        reorder_point = item.get("reorder_point", 10)
        cost_per_unit = Decimal(str(item.get("cost_per_unit", 0)))
        
        if available_qty <= 0:
            out_of_stock_items += 1
        elif available_qty <= reorder_point:
            low_stock_items += 1
        
        total_stock_value += Decimal(str(available_qty)) * cost_per_unit
    
    # Movement statistics
    movement_types = {}
    for movement in inventory_movements_store.values():
        mov_type = movement.get("movement_type", "unknown")
        movement_types[mov_type] = movement_types.get(mov_type, 0) + 1
    
    return {
        "locations": {
            "total_locations": total_locations,
            "active_locations": active_locations,
            "inactive_locations": total_locations - active_locations
        },
        "inventory": {
            "total_items": total_inventory_items,
            "low_stock_items": low_stock_items,
            "out_of_stock_items": out_of_stock_items,
            "total_stock_value": float(total_stock_value)
        },
        "movements": {
            "total_movements": total_movements,
            "movement_types": movement_types
        },
        "alerts": {
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "acknowledgment_rate": round((total_alerts - unacknowledged_alerts) / max(total_alerts, 1) * 100, 2)
        },
        "cache_status": {
            "cached_items": len(inventory_cache),
            "last_updated": datetime.now().isoformat()
        }
    }

# Test utility endpoint
@router.delete("/test/clear-all")
async def clear_all_inventory_for_testing():
    """Clear all inventory data for testing purposes - DO NOT USE IN PRODUCTION"""
    locations_store.clear()
    inventory_items_store.clear()
    inventory_movements_store.clear()
    inventory_alerts_store.clear()
    reorder_suggestions_store.clear()
    inventory_cache.clear()
    
    return {"message": "All inventory data cleared for testing"}