"""
CC02 v53.0 Inventory API Endpoints - Issue #568
10-Day ERP Business API Implementation Sprint - Day 3-4
Enhanced Inventory Management API Implementation
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, date
from decimal import Decimal
import uuid
import asyncio
import json
import time

# Import database and core dependencies
from app.core.database import get_db
from app.schemas.inventory_v53 import (
    LocationCreate, LocationUpdate, LocationResponse, LocationListResponse,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse, InventoryItemListResponse,
    InventoryMovementCreate, InventoryMovementResponse, InventoryMovementListResponse,
    StockAdjustmentCreate, StockAdjustmentResponse,
    StockTransferCreate, StockTransferResponse,
    InventoryValuationResponse, LocationStockLevel, InventoryAlert,
    InventoryStatistics, BulkInventoryOperation, BulkInventoryResult,
    InventoryError, InventoryAPIResponse,
    InventoryMovementType, InventoryStatus, LocationType, MovementReason
)

# Create router
router = APIRouter(prefix="/inventory-v53", tags=["Inventory v53.0"])

# In-memory storage for TDD implementation (will be replaced with database)
locations_store: Dict[str, Dict[str, Any]] = {}
inventory_items_store: Dict[str, Dict[str, Any]] = {}
movements_store: Dict[str, Dict[str, Any]] = {}
adjustments_store: Dict[str, Dict[str, Any]] = {}
transfers_store: Dict[str, Dict[str, Any]] = {}


# Location Management Endpoints
@router.post("/locations/", response_model=LocationResponse, status_code=201)
async def create_location(
    location_data: LocationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> LocationResponse:
    """Create a new inventory location"""
    
    # Check for duplicate code
    for existing_location in locations_store.values():
        if existing_location["code"] == location_data.code:
            raise HTTPException(
                status_code=400,
                detail=f"Location with code '{location_data.code}' already exists"
            )
    
    # Validate parent location if provided
    if location_data.parent_location_id:
        if location_data.parent_location_id not in locations_store:
            raise HTTPException(
                status_code=404,
                detail=f"Parent location with ID '{location_data.parent_location_id}' not found"
            )
    
    # Create location
    location_id = str(uuid.uuid4())
    now = datetime.now()
    
    location = {
        "id": location_id,
        "name": location_data.name,
        "code": location_data.code,
        "location_type": location_data.location_type.value,
        "address": location_data.address,
        "contact_person": location_data.contact_person,
        "contact_phone": location_data.contact_phone,
        "contact_email": location_data.contact_email,
        "is_active": location_data.is_active,
        "capacity_limit": location_data.capacity_limit,
        "current_utilization": 0,
        "parent_location_id": location_data.parent_location_id,
        "attributes": location_data.attributes,
        "created_at": now,
        "updated_at": now
    }
    
    locations_store[location_id] = location
    
    # Schedule background tasks
    background_tasks.add_task(log_location_creation, location_id)
    
    return LocationResponse(**location)


@router.get("/locations/", response_model=LocationListResponse)
async def list_locations(
    # Search parameters
    search: Optional[str] = Query(None, description="Search in name, code"),
    location_type: Optional[LocationType] = Query(None),
    is_active: Optional[bool] = Query(None),
    parent_location_id: Optional[str] = Query(None),
    
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    
    # Sorting
    sort_by: str = Query("created_at", pattern="^(name|code|location_type|created_at|updated_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    db: AsyncSession = Depends(get_db)
) -> LocationListResponse:
    """List locations with filtering, searching, and pagination"""
    
    all_locations = list(locations_store.values())
    
    # Apply search
    if search:
        search_lower = search.lower()
        all_locations = [
            l for l in all_locations
            if (search_lower in l["name"].lower() or
                search_lower in l["code"].lower())
        ]
    
    # Apply filters
    if location_type:
        all_locations = [l for l in all_locations if l.get("location_type") == location_type.value]
    
    if is_active is not None:
        all_locations = [l for l in all_locations if l.get("is_active") == is_active]
    
    if parent_location_id:
        all_locations = [l for l in all_locations if l.get("parent_location_id") == parent_location_id]
    
    # Apply sorting
    reverse = (sort_order == "desc")
    if sort_by == "name":
        all_locations.sort(key=lambda x: x.get("name", ""), reverse=reverse)
    elif sort_by == "code":
        all_locations.sort(key=lambda x: x.get("code", ""), reverse=reverse)
    elif sort_by == "location_type":
        all_locations.sort(key=lambda x: x.get("location_type", ""), reverse=reverse)
    elif sort_by == "updated_at":
        all_locations.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=reverse)
    else:  # created_at
        all_locations.sort(key=lambda x: x.get("created_at", datetime.min), reverse=reverse)
    
    # Apply pagination
    total = len(all_locations)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_locations = all_locations[start_idx:end_idx]
    
    # Convert to response format
    items = [LocationResponse(**location) for location in paginated_locations]
    
    # Build filters applied dictionary
    filters_applied = {}
    if search: filters_applied["search"] = search
    if location_type: filters_applied["location_type"] = location_type.value
    if is_active is not None: filters_applied["is_active"] = is_active
    
    return LocationListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied=filters_applied
    )


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    db: AsyncSession = Depends(get_db)
) -> LocationResponse:
    """Get location by ID"""
    
    if location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = locations_store[location_id]
    return LocationResponse(**location)


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: str,
    location_data: LocationUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> LocationResponse:
    """Update location"""
    
    if location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = locations_store[location_id].copy()
    
    # Update fields
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ["id", "code", "created_at"]:  # Prevent updating immutable fields
            if field == "location_type" and value:
                location[field] = value.value
            else:
                location[field] = value
    
    location["updated_at"] = datetime.now()
    
    # Validate parent location if updated
    if "parent_location_id" in update_data and update_data["parent_location_id"]:
        if update_data["parent_location_id"] not in locations_store:
            raise HTTPException(
                status_code=404,
                detail=f"Parent location with ID '{update_data['parent_location_id']}' not found"
            )
    
    locations_store[location_id] = location
    
    # Schedule background task
    background_tasks.add_task(log_location_update, location_id)
    
    return LocationResponse(**location)


@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: str,
    hard_delete: bool = Query(False, description="Permanently delete the location"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete location (soft delete by default, hard delete if specified)"""
    
    if location_id not in locations_store:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if location has inventory items
    has_inventory = any(
        item["location_id"] == location_id 
        for item in inventory_items_store.values()
    )
    
    if has_inventory and hard_delete:
        raise HTTPException(
            status_code=400,
            detail="Cannot hard delete location with existing inventory items"
        )
    
    if hard_delete:
        # Hard delete - remove from storage
        del locations_store[location_id]
        return {"message": "Location permanently deleted", "id": location_id}
    else:
        # Soft delete - mark as inactive
        locations_store[location_id]["is_active"] = False
        locations_store[location_id]["updated_at"] = datetime.now()
        return {"message": "Location deactivated", "id": location_id}


# Inventory Item Management Endpoints
@router.post("/items/", response_model=InventoryItemResponse, status_code=201)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> InventoryItemResponse:
    """Create a new inventory item"""
    
    # Validate location exists
    if item_data.location_id not in locations_store:
        raise HTTPException(
            status_code=404,
            detail=f"Location with ID '{item_data.location_id}' not found"
        )
    
    # Check for existing item with same product and location
    existing_item = None
    for item in inventory_items_store.values():
        if (item["product_id"] == item_data.product_id and 
            item["location_id"] == item_data.location_id):
            existing_item = item
            break
    
    if existing_item:
        raise HTTPException(
            status_code=400,
            detail=f"Inventory item for product '{item_data.product_id}' already exists in location '{item_data.location_id}'"
        )
    
    # Create inventory item
    item_id = str(uuid.uuid4())
    now = datetime.now()
    
    # Calculate available quantity
    available_quantity = item_data.quantity - item_data.reserved_quantity - item_data.allocated_quantity
    
    # Calculate total value if cost is provided
    total_value = None
    if item_data.cost_per_unit:
        total_value = float(item_data.cost_per_unit) * float(item_data.quantity)
    
    item = {
        "id": item_id,
        "product_id": item_data.product_id,
        "product_name": f"Product {item_data.product_id}",  # Mock - will be populated from product service
        "product_sku": f"SKU-{item_data.product_id[:8]}",   # Mock
        "location_id": item_data.location_id,
        "location_name": locations_store[item_data.location_id]["name"],
        "quantity": float(item_data.quantity),
        "available_quantity": float(available_quantity),
        "reserved_quantity": float(item_data.reserved_quantity),
        "allocated_quantity": float(item_data.allocated_quantity),
        "minimum_level": float(item_data.minimum_level) if item_data.minimum_level else None,
        "maximum_level": float(item_data.maximum_level) if item_data.maximum_level else None,
        "reorder_point": float(item_data.reorder_point) if item_data.reorder_point else None,
        "reorder_quantity": float(item_data.reorder_quantity) if item_data.reorder_quantity else None,
        "status": item_data.status.value,
        "cost_per_unit": float(item_data.cost_per_unit) if item_data.cost_per_unit else None,
        "total_value": total_value,
        "lot_number": item_data.lot_number,
        "serial_number": item_data.serial_number,
        "expiry_date": item_data.expiry_date.isoformat() if item_data.expiry_date else None,
        "manufacture_date": item_data.manufacture_date.isoformat() if item_data.manufacture_date else None,
        "supplier_id": item_data.supplier_id,
        "notes": item_data.notes,
        "attributes": item_data.attributes,
        "created_at": now,
        "updated_at": now
    }
    
    inventory_items_store[item_id] = item
    
    # Schedule background tasks
    background_tasks.add_task(log_inventory_creation, item_id)
    background_tasks.add_task(check_stock_levels, item_id)
    
    return InventoryItemResponse(**item)


@router.get("/items/", response_model=InventoryItemListResponse)
async def list_inventory_items(
    # Search parameters
    search: Optional[str] = Query(None, description="Search in product name, SKU"),
    product_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    status: Optional[InventoryStatus] = Query(None),
    
    # Stock filters
    low_stock_only: bool = Query(False),
    out_of_stock_only: bool = Query(False),
    expiring_soon: bool = Query(False),
    expired_only: bool = Query(False),
    
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    
    # Sorting
    sort_by: str = Query("created_at", pattern="^(product_name|quantity|created_at|updated_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    db: AsyncSession = Depends(get_db)
) -> InventoryItemListResponse:
    """List inventory items with advanced filtering"""
    
    all_items = list(inventory_items_store.values())
    
    # Apply search
    if search:
        search_lower = search.lower()
        all_items = [
            item for item in all_items
            if (search_lower in item.get("product_name", "").lower() or
                search_lower in item.get("product_sku", "").lower())
        ]
    
    # Apply filters
    if product_id:
        all_items = [item for item in all_items if item.get("product_id") == product_id]
    
    if location_id:
        all_items = [item for item in all_items if item.get("location_id") == location_id]
    
    if status:
        all_items = [item for item in all_items if item.get("status") == status.value]
    
    if low_stock_only:
        all_items = [
            item for item in all_items
            if item.get("reorder_point") and item.get("quantity", 0) <= item["reorder_point"]
        ]
    
    if out_of_stock_only:
        all_items = [item for item in all_items if item.get("quantity", 0) == 0]
    
    if expiring_soon:
        cutoff_date = datetime.now() + timedelta(days=30)
        all_items = [
            item for item in all_items
            if (item.get("expiry_date") and 
                datetime.fromisoformat(item["expiry_date"]) <= cutoff_date)
        ]
    
    if expired_only:
        current_date = datetime.now()
        all_items = [
            item for item in all_items
            if (item.get("expiry_date") and 
                datetime.fromisoformat(item["expiry_date"]) < current_date)
        ]
    
    # Apply sorting
    reverse = (sort_order == "desc")
    if sort_by == "product_name":
        all_items.sort(key=lambda x: x.get("product_name", ""), reverse=reverse)
    elif sort_by == "quantity":
        all_items.sort(key=lambda x: x.get("quantity", 0), reverse=reverse)
    elif sort_by == "updated_at":
        all_items.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=reverse)
    else:  # created_at
        all_items.sort(key=lambda x: x.get("created_at", datetime.min), reverse=reverse)
    
    # Apply pagination
    total = len(all_items)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_items = all_items[start_idx:end_idx]
    
    # Convert to response format
    items = [InventoryItemResponse(**item) for item in paginated_items]
    
    # Build filters applied dictionary
    filters_applied = {}
    if search: filters_applied["search"] = search
    if product_id: filters_applied["product_id"] = product_id
    if location_id: filters_applied["location_id"] = location_id
    
    return InventoryItemListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied=filters_applied
    )


@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: str,
    db: AsyncSession = Depends(get_db)
) -> InventoryItemResponse:
    """Get inventory item by ID"""
    
    if item_id not in inventory_items_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item = inventory_items_store[item_id]
    return InventoryItemResponse(**item)


@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item_data: InventoryItemUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> InventoryItemResponse:
    """Update inventory item"""
    
    if item_id not in inventory_items_store:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    item = inventory_items_store[item_id].copy()
    old_quantity = item["quantity"]
    
    # Update fields
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ["id", "product_id", "location_id", "created_at"]:
            if field in ["quantity", "reserved_quantity", "allocated_quantity", 
                        "minimum_level", "maximum_level", "reorder_point", 
                        "reorder_quantity", "cost_per_unit"]:
                item[field] = float(value) if value is not None else None
            elif field == "status" and value:
                item[field] = value.value
            elif field in ["expiry_date", "manufacture_date"] and value:
                item[field] = value.isoformat()
            else:
                item[field] = value
    
    # Recalculate available quantity
    if any(field in update_data for field in ["quantity", "reserved_quantity", "allocated_quantity"]):
        quantity = item.get("quantity", 0)
        reserved = item.get("reserved_quantity", 0)
        allocated = item.get("allocated_quantity", 0)
        item["available_quantity"] = quantity - reserved - allocated
    
    # Recalculate total value
    if "cost_per_unit" in update_data or "quantity" in update_data:
        cost = item.get("cost_per_unit")
        quantity = item.get("quantity", 0)
        if cost is not None:
            item["total_value"] = cost * quantity
    
    item["updated_at"] = datetime.now()
    inventory_items_store[item_id] = item
    
    # Create movement record if quantity changed
    if "quantity" in update_data and float(update_data["quantity"]) != old_quantity:
        quantity_change = float(update_data["quantity"]) - old_quantity
        movement_type = InventoryMovementType.INBOUND if quantity_change > 0 else InventoryMovementType.OUTBOUND
        
        await create_movement_record(
            product_id=item["product_id"],
            location_id=item["location_id"],
            movement_type=movement_type,
            quantity=abs(quantity_change),
            reason=MovementReason.ADJUSTMENT,
            reference_id=item_id,
            notes=f"Inventory adjustment via update API"
        )
    
    # Schedule background tasks
    background_tasks.add_task(check_stock_levels, item_id)
    
    return InventoryItemResponse(**item)


# Stock Adjustment Endpoints  
@router.post("/adjustments/", response_model=StockAdjustmentResponse, status_code=201)
async def create_stock_adjustment(
    adjustment_data: StockAdjustmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> StockAdjustmentResponse:
    """Create stock adjustment"""
    
    # Find inventory item
    inventory_item = None
    for item in inventory_items_store.values():
        if (item["product_id"] == adjustment_data.product_id and
            item["location_id"] == adjustment_data.location_id):
            inventory_item = item
            break
    
    if not inventory_item:
        raise HTTPException(
            status_code=404,
            detail="Inventory item not found for the specified product and location"
        )
    
    # Validate adjustment won't result in negative stock
    old_quantity = inventory_item["quantity"]
    new_quantity = old_quantity + float(adjustment_data.adjustment_quantity)
    
    if new_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Adjustment would result in negative stock. Current: {old_quantity}, Adjustment: {adjustment_data.adjustment_quantity}"
        )
    
    # Create adjustment record
    adjustment_id = str(uuid.uuid4())
    now = adjustment_data.effective_date or datetime.now()
    
    # Calculate value changes
    old_value = None
    adjustment_value = None
    new_value = None
    
    if inventory_item.get("cost_per_unit"):
        cost_per_unit = inventory_item["cost_per_unit"]
        old_value = old_quantity * cost_per_unit
        adjustment_value = float(adjustment_data.adjustment_quantity) * cost_per_unit
        new_value = new_quantity * cost_per_unit
        
        if adjustment_data.cost_adjustment:
            adjustment_value = float(adjustment_data.cost_adjustment)
            new_value = old_value + adjustment_value
    
    adjustment = {
        "id": adjustment_id,
        "product_id": adjustment_data.product_id,
        "product_name": inventory_item["product_name"],
        "location_id": adjustment_data.location_id,
        "location_name": inventory_item["location_name"],
        "old_quantity": old_quantity,
        "adjustment_quantity": float(adjustment_data.adjustment_quantity),
        "new_quantity": new_quantity,
        "old_value": old_value,
        "adjustment_value": adjustment_value,
        "new_value": new_value,
        "reason": adjustment_data.reason,
        "reference_id": adjustment_data.reference_id,
        "notes": adjustment_data.notes,
        "effective_date": now,
        "processed_by": None,  # Will be populated with user info when auth is implemented
        "created_at": datetime.now()
    }
    
    adjustments_store[adjustment_id] = adjustment
    
    # Update inventory item
    item_id = None
    for id, item in inventory_items_store.items():
        if (item["product_id"] == adjustment_data.product_id and
            item["location_id"] == adjustment_data.location_id):
            item_id = id
            break
    
    if item_id:
        inventory_items_store[item_id]["quantity"] = new_quantity
        inventory_items_store[item_id]["updated_at"] = now
        
        # Recalculate available quantity
        item = inventory_items_store[item_id]
        reserved = item.get("reserved_quantity", 0)
        allocated = item.get("allocated_quantity", 0)
        item["available_quantity"] = new_quantity - reserved - allocated
        
        # Update total value
        if item.get("cost_per_unit"):
            item["total_value"] = new_quantity * item["cost_per_unit"]
    
    # Create movement record
    movement_type = InventoryMovementType.INBOUND if adjustment_data.adjustment_quantity > 0 else InventoryMovementType.OUTBOUND
    await create_movement_record(
        product_id=adjustment_data.product_id,
        location_id=adjustment_data.location_id,
        movement_type=movement_type,
        quantity=abs(float(adjustment_data.adjustment_quantity)),
        reason=MovementReason.ADJUSTMENT,
        reference_id=adjustment_id,
        notes=f"Stock adjustment: {adjustment_data.reason}"
    )
    
    # Schedule background tasks
    background_tasks.add_task(log_stock_adjustment, adjustment_id)
    if item_id:
        background_tasks.add_task(check_stock_levels, item_id)
    
    return StockAdjustmentResponse(**adjustment)


# Stock Transfer Endpoints
@router.post("/transfers/", response_model=StockTransferResponse, status_code=201)
async def create_stock_transfer(
    transfer_data: StockTransferCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> StockTransferResponse:
    """Create stock transfer between locations"""
    
    # Validate locations exist
    if transfer_data.from_location_id not in locations_store:
        raise HTTPException(
            status_code=404,
            detail=f"Source location '{transfer_data.from_location_id}' not found"
        )
    
    if transfer_data.to_location_id not in locations_store:
        raise HTTPException(
            status_code=404,
            detail=f"Destination location '{transfer_data.to_location_id}' not found"
        )
    
    # Find source inventory item
    source_item = None
    source_item_id = None
    for item_id, item in inventory_items_store.items():
        if (item["product_id"] == transfer_data.product_id and
            item["location_id"] == transfer_data.from_location_id):
            source_item = item
            source_item_id = item_id
            break
    
    if not source_item:
        raise HTTPException(
            status_code=404,
            detail="Source inventory item not found"
        )
    
    # Validate sufficient stock
    available_quantity = source_item["available_quantity"]
    if available_quantity < float(transfer_data.quantity):
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {available_quantity}, Requested: {transfer_data.quantity}"
        )
    
    # Create transfer record
    transfer_id = str(uuid.uuid4())
    now = transfer_data.effective_date or datetime.now()
    
    transfer = {
        "id": transfer_id,
        "product_id": transfer_data.product_id,
        "product_name": source_item["product_name"],
        "from_location_id": transfer_data.from_location_id,
        "from_location_name": locations_store[transfer_data.from_location_id]["name"],
        "to_location_id": transfer_data.to_location_id,
        "to_location_name": locations_store[transfer_data.to_location_id]["name"],
        "quantity": float(transfer_data.quantity),
        "reason": transfer_data.reason,
        "reference_id": transfer_data.reference_id,
        "lot_number": transfer_data.lot_number,
        "serial_number": transfer_data.serial_number,
        "notes": transfer_data.notes,
        "effective_date": now,
        "processed_by": None,
        "created_at": datetime.now()
    }
    
    transfers_store[transfer_id] = transfer
    
    # Update source inventory item
    new_source_quantity = source_item["quantity"] - float(transfer_data.quantity)
    inventory_items_store[source_item_id]["quantity"] = new_source_quantity
    inventory_items_store[source_item_id]["available_quantity"] = (
        new_source_quantity - 
        source_item.get("reserved_quantity", 0) - 
        source_item.get("allocated_quantity", 0)
    )
    inventory_items_store[source_item_id]["updated_at"] = now
    
    # Find or create destination inventory item
    dest_item = None
    dest_item_id = None
    for item_id, item in inventory_items_store.items():
        if (item["product_id"] == transfer_data.product_id and
            item["location_id"] == transfer_data.to_location_id):
            dest_item = item
            dest_item_id = item_id
            break
    
    if dest_item:
        # Update existing destination item
        new_dest_quantity = dest_item["quantity"] + float(transfer_data.quantity)
        inventory_items_store[dest_item_id]["quantity"] = new_dest_quantity
        inventory_items_store[dest_item_id]["available_quantity"] = (
            new_dest_quantity - 
            dest_item.get("reserved_quantity", 0) - 
            dest_item.get("allocated_quantity", 0)
        )
        inventory_items_store[dest_item_id]["updated_at"] = now
    else:
        # Create new destination item
        dest_item_id = str(uuid.uuid4())
        dest_item = {
            "id": dest_item_id,
            "product_id": transfer_data.product_id,
            "product_name": source_item["product_name"],
            "product_sku": source_item["product_sku"],
            "location_id": transfer_data.to_location_id,
            "location_name": locations_store[transfer_data.to_location_id]["name"],
            "quantity": float(transfer_data.quantity),
            "available_quantity": float(transfer_data.quantity),
            "reserved_quantity": 0,
            "allocated_quantity": 0,
            "minimum_level": None,
            "maximum_level": None,
            "reorder_point": None,
            "reorder_quantity": None,
            "status": InventoryStatus.AVAILABLE.value,
            "cost_per_unit": source_item.get("cost_per_unit"),
            "total_value": source_item.get("cost_per_unit", 0) * float(transfer_data.quantity) if source_item.get("cost_per_unit") else None,
            "lot_number": transfer_data.lot_number,
            "serial_number": transfer_data.serial_number,
            "expiry_date": None,
            "manufacture_date": None,
            "supplier_id": None,
            "notes": f"Transferred from {locations_store[transfer_data.from_location_id]['name']}",
            "attributes": {},
            "created_at": now,
            "updated_at": now
        }
        inventory_items_store[dest_item_id] = dest_item
    
    # Create movement records
    await create_movement_record(
        product_id=transfer_data.product_id,
        location_id=transfer_data.from_location_id,
        movement_type=InventoryMovementType.OUTBOUND,
        quantity=float(transfer_data.quantity),
        reason=MovementReason.TRANSFER,
        reference_id=transfer_id,
        notes=f"Transfer to {locations_store[transfer_data.to_location_id]['name']}"
    )
    
    await create_movement_record(
        product_id=transfer_data.product_id,
        location_id=transfer_data.to_location_id,
        movement_type=InventoryMovementType.INBOUND,
        quantity=float(transfer_data.quantity),
        reason=MovementReason.TRANSFER,
        reference_id=transfer_id,
        notes=f"Transfer from {locations_store[transfer_data.from_location_id]['name']}"
    )
    
    # Schedule background tasks
    background_tasks.add_task(log_stock_transfer, transfer_id)
    background_tasks.add_task(check_stock_levels, source_item_id)
    if dest_item_id:
        background_tasks.add_task(check_stock_levels, dest_item_id)
    
    return StockTransferResponse(**transfer)


# Statistics and Analytics
@router.get("/statistics", response_model=InventoryStatistics)
async def get_inventory_statistics(
    location_id: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> InventoryStatistics:
    """Get comprehensive inventory statistics"""
    
    start_time = time.time()
    
    # Get all data
    all_locations = list(locations_store.values())
    all_items = list(inventory_items_store.values())
    all_movements = list(movements_store.values())
    
    # Filter by location if specified
    if location_id:
        all_items = [item for item in all_items if item.get("location_id") == location_id]
        all_movements = [
            movement for movement in all_movements
            if (movement.get("from_location_id") == location_id or 
                movement.get("to_location_id") == location_id)
        ]
    
    # Filter active/inactive locations
    if not include_inactive:
        all_locations = [loc for loc in all_locations if loc.get("is_active", True)]
    
    # Basic counts
    total_locations = len(all_locations)
    active_locations = len([loc for loc in all_locations if loc.get("is_active", True)])
    
    # Product and item counts
    unique_products = set(item["product_id"] for item in all_items)
    total_products_tracked = len(unique_products)
    total_inventory_items = len(all_items)
    
    # Stock statistics
    total_stock_quantity = sum(Decimal(str(item.get("quantity", 0))) for item in all_items)
    
    # Calculate total inventory value
    total_inventory_value = Decimal("0")
    for item in all_items:
        if item.get("total_value"):
            total_inventory_value += Decimal(str(item["total_value"]))
    
    average_stock_value = (
        total_inventory_value / total_inventory_items 
        if total_inventory_items > 0 else Decimal("0")
    )
    
    # Status breakdown
    status_counts = {}
    for status in InventoryStatus:
        status_counts[status.value] = len([
            item for item in all_items 
            if item.get("status") == status.value
        ])
    
    # Alert statistics (mock implementation)
    low_stock_alerts = len([
        item for item in all_items
        if item.get("reorder_point") and item.get("quantity", 0) <= item["reorder_point"]
    ])
    
    out_of_stock_alerts = len([item for item in all_items if item.get("quantity", 0) == 0])
    
    expired_alerts = len([
        item for item in all_items
        if (item.get("expiry_date") and 
            datetime.fromisoformat(item["expiry_date"]) < datetime.now())
    ])
    
    reorder_alerts = low_stock_alerts  # Same as low stock for now
    
    # Movement statistics for today
    today = datetime.now().date()
    today_movements = [
        movement for movement in all_movements
        if movement.get("created_at", datetime.min).date() == today
    ]
    
    total_movements_today = len(today_movements)
    inbound_movements_today = len([
        movement for movement in today_movements
        if movement.get("movement_type") == InventoryMovementType.INBOUND.value
    ])
    outbound_movements_today = len([
        movement for movement in today_movements
        if movement.get("movement_type") == InventoryMovementType.OUTBOUND.value
    ])
    
    # Locations by type breakdown
    locations_by_type = {}
    for location_type in LocationType:
        locations_by_type[location_type.value] = len([
            loc for loc in all_locations
            if loc.get("location_type") == location_type.value
        ])
    
    # Top value products
    product_values = {}
    for item in all_items:
        product_id = item["product_id"]
        if product_id not in product_values:
            product_values[product_id] = {
                "product_id": product_id,
                "product_name": item.get("product_name", "Unknown"),
                "total_quantity": 0,
                "total_value": 0
            }
        
        product_values[product_id]["total_quantity"] += item.get("quantity", 0)
        if item.get("total_value"):
            product_values[product_id]["total_value"] += float(item["total_value"])
    
    top_value_products = sorted(
        list(product_values.values()),
        key=lambda x: x["total_value"],
        reverse=True
    )[:10]
    
    # Movement summary
    movement_summary = {}
    for movement_type in InventoryMovementType:
        movement_summary[movement_type.value] = len([
            movement for movement in all_movements
            if movement.get("movement_type") == movement_type.value
        ])
    
    end_time = time.time()
    calculation_time_ms = (end_time - start_time) * 1000
    
    return InventoryStatistics(
        total_locations=total_locations,
        active_locations=active_locations,
        total_products_tracked=total_products_tracked,
        total_inventory_items=total_inventory_items,
        total_stock_quantity=total_stock_quantity,
        total_inventory_value=total_inventory_value,
        average_stock_value=average_stock_value,
        available_items=status_counts.get(InventoryStatus.AVAILABLE.value, 0),
        reserved_items=status_counts.get(InventoryStatus.RESERVED.value, 0),
        allocated_items=status_counts.get(InventoryStatus.ALLOCATED.value, 0),
        on_hold_items=status_counts.get(InventoryStatus.ON_HOLD.value, 0),
        damaged_items=status_counts.get(InventoryStatus.DAMAGED.value, 0),
        expired_items=status_counts.get(InventoryStatus.EXPIRED.value, 0),
        low_stock_alerts=low_stock_alerts,
        out_of_stock_alerts=out_of_stock_alerts,
        expired_alerts=expired_alerts,
        reorder_alerts=reorder_alerts,
        total_movements_today=total_movements_today,
        inbound_movements_today=inbound_movements_today,
        outbound_movements_today=outbound_movements_today,
        locations_by_type=locations_by_type,
        top_value_products=top_value_products,
        movement_summary=movement_summary,
        last_updated=datetime.now(),
        calculation_time_ms=calculation_time_ms
    )


# Movement History
@router.get("/movements/", response_model=InventoryMovementListResponse)
async def list_inventory_movements(
    # Search parameters
    product_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    movement_type: Optional[InventoryMovementType] = Query(None),
    reason: Optional[MovementReason] = Query(None),
    
    # Date filters
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    
    # Sorting
    sort_by: str = Query("created_at", pattern="^(created_at|effective_date|product_name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    db: AsyncSession = Depends(get_db)
) -> InventoryMovementListResponse:
    """List inventory movements with filtering"""
    
    all_movements = list(movements_store.values())
    
    # Apply filters
    if product_id:
        all_movements = [m for m in all_movements if m.get("product_id") == product_id]
    
    if location_id:
        all_movements = [
            m for m in all_movements
            if (m.get("from_location_id") == location_id or 
                m.get("to_location_id") == location_id)
        ]
    
    if movement_type:
        all_movements = [m for m in all_movements if m.get("movement_type") == movement_type.value]
    
    if reason:
        all_movements = [m for m in all_movements if m.get("reason") == reason.value]
    
    if from_date:
        all_movements = [
            m for m in all_movements
            if m.get("effective_date", datetime.min) >= from_date
        ]
    
    if to_date:
        all_movements = [
            m for m in all_movements
            if m.get("effective_date", datetime.max) <= to_date
        ]
    
    # Apply sorting
    reverse = (sort_order == "desc")
    if sort_by == "product_name":
        all_movements.sort(key=lambda x: x.get("product_name", ""), reverse=reverse)
    elif sort_by == "effective_date":
        all_movements.sort(key=lambda x: x.get("effective_date", datetime.min), reverse=reverse)
    else:  # created_at
        all_movements.sort(key=lambda x: x.get("created_at", datetime.min), reverse=reverse)
    
    # Apply pagination
    total = len(all_movements)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_movements = all_movements[start_idx:end_idx]
    
    # Convert to response format
    items = [InventoryMovementResponse(**movement) for movement in paginated_movements]
    
    # Build filters applied dictionary
    filters_applied = {}
    if product_id: filters_applied["product_id"] = product_id
    if location_id: filters_applied["location_id"] = location_id
    if movement_type: filters_applied["movement_type"] = movement_type.value
    
    return InventoryMovementListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied=filters_applied
    )


# Health and Performance
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for inventory API"""
    start_time = time.time()
    
    # Simulate some processing
    location_count = len(locations_store)
    item_count = len(inventory_items_store)
    movement_count = len(movements_store)
    
    end_time = time.time()
    response_time_ms = (end_time - start_time) * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "location_count": location_count,
        "inventory_item_count": item_count,
        "movement_count": movement_count,
        "memory_usage": "simulated",
        "timestamp": datetime.now().isoformat(),
        "version": "v53.0"
    }


# Helper Functions
async def create_movement_record(
    product_id: str,
    location_id: str,
    movement_type: InventoryMovementType,
    quantity: float,
    reason: MovementReason,
    reference_id: Optional[str] = None,
    notes: Optional[str] = None
):
    """Create inventory movement record"""
    movement_id = str(uuid.uuid4())
    now = datetime.now()
    
    # Get product and location names
    product_name = f"Product {product_id}"  # Mock
    location_name = locations_store.get(location_id, {}).get("name", "Unknown Location")
    
    movement = {
        "id": movement_id,
        "product_id": product_id,
        "product_name": product_name,
        "product_sku": f"SKU-{product_id[:8]}",
        "from_location_id": location_id if movement_type == InventoryMovementType.OUTBOUND else None,
        "from_location_name": location_name if movement_type == InventoryMovementType.OUTBOUND else None,
        "to_location_id": location_id if movement_type == InventoryMovementType.INBOUND else None,
        "to_location_name": location_name if movement_type == InventoryMovementType.INBOUND else None,
        "movement_type": movement_type.value,
        "quantity": quantity,
        "unit_cost": None,
        "total_cost": None,
        "reason": reason.value,
        "reference_id": reference_id,
        "reference_type": None,
        "lot_number": None,
        "serial_number": None,
        "expiry_date": None,
        "notes": notes,
        "effective_date": now,
        "processed_by": None,
        "attributes": {},
        "created_at": now,
        "updated_at": now
    }
    
    movements_store[movement_id] = movement


# Background Tasks
async def log_location_creation(location_id: str):
    """Background task to log location creation"""
    print(f"Location created: {location_id} at {datetime.now()}")


async def log_location_update(location_id: str):
    """Background task to log location update"""
    print(f"Location updated: {location_id} at {datetime.now()}")


async def log_inventory_creation(item_id: str):
    """Background task to log inventory item creation"""
    print(f"Inventory item created: {item_id} at {datetime.now()}")


async def log_stock_adjustment(adjustment_id: str):
    """Background task to log stock adjustment"""
    print(f"Stock adjustment created: {adjustment_id} at {datetime.now()}")


async def log_stock_transfer(transfer_id: str):
    """Background task to log stock transfer"""
    print(f"Stock transfer created: {transfer_id} at {datetime.now()}")


async def check_stock_levels(item_id: str):
    """Background task to check stock levels and generate alerts"""
    if item_id not in inventory_items_store:
        return
    
    item = inventory_items_store[item_id]
    quantity = item.get("quantity", 0)
    reorder_point = item.get("reorder_point")
    
    if reorder_point and quantity <= reorder_point:
        print(f"LOW STOCK ALERT: Item {item_id} is at or below reorder point. Current: {quantity}, Reorder point: {reorder_point}")
    
    if quantity == 0:
        print(f"OUT OF STOCK ALERT: Item {item_id} is out of stock")