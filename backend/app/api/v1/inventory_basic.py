"""
Basic inventory management API endpoints for ERP v17.0
Comprehensive inventory tracking, warehouse management, and stock operations
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import BusinessLogicError
from app.crud import inventory_basic as crud
from app.models.inventory import InventoryStatus, MovementType
from app.schemas.inventory_basic import (
    ExpiryAlert,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryStatistics,
    LowStockAlert,
    StockAdjustmentCreate,
    StockMovementCreate,
    StockMovementResponse,
    StockReservationCreate,
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)

router = APIRouter(prefix="/inventory-basic", tags=["inventory-basic"])


# Warehouse Management Endpoints
@router.post("/warehouses/", response_model=WarehouseResponse)
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> WarehouseResponse:
    """Create a new warehouse."""
    try:
        warehouse = crud.create_warehouse(db, warehouse_data, current_user.id)
        return crud.convert_warehouse_to_response(warehouse)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/warehouses/", response_model=List[WarehouseResponse])
async def get_warehouses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[WarehouseResponse]:
    """Get warehouses with filtering and pagination."""
    warehouses, total = crud.get_warehouses(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        organization_id=organization_id,
        is_active=is_active,
    )

    return [crud.convert_warehouse_to_response(warehouse) for warehouse in warehouses]


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> WarehouseResponse:
    """Get warehouse by ID."""
    warehouse = crud.get_warehouse_by_id(db, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    return crud.convert_warehouse_to_response(warehouse)


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int,
    warehouse_data: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> WarehouseResponse:
    """Update warehouse information."""
    try:
        warehouse = crud.update_warehouse(
            db, warehouse_id, warehouse_data, current_user.id
        )
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        return crud.convert_warehouse_to_response(warehouse)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Inventory Item Management Endpoints
@router.post("/items/", response_model=InventoryItemResponse)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> InventoryItemResponse:
    """Create a new inventory item."""
    try:
        item = crud.create_inventory_item(db, item_data, current_user.id)
        return crud.convert_inventory_item_to_response(item)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/items/", response_model=List[InventoryItemResponse])
async def get_inventory_items(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    product_id: Optional[int] = Query(None, description="Filter by product"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    status: Optional[str] = Query(None, description="Filter by status"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[InventoryItemResponse]:
    """Get inventory items with filtering and pagination."""
    inventory_status = None
    if status:
        try:
            inventory_status = InventoryStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")

    items, total = crud.get_inventory_items(
        db=db,
        skip=skip,
        limit=limit,
        warehouse_id=warehouse_id,
        product_id=product_id,
        organization_id=organization_id,
        status=inventory_status,
        low_stock_only=low_stock_only,
    )

    return [crud.convert_inventory_item_to_response(item) for item in items]


@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
) -> InventoryItemResponse:
    """Get inventory item by ID."""
    item = crud.get_inventory_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return crud.convert_inventory_item_to_response(item)


@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    item_data: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> InventoryItemResponse:
    """Update inventory item information."""
    item = crud.update_inventory_item(db, item_id, item_data, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return crud.convert_inventory_item_to_response(item)


# Stock Movement Endpoints
@router.post("/movements/", response_model=StockMovementResponse)
async def create_stock_movement(
    movement_data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> StockMovementResponse:
    """Create a stock movement transaction."""
    try:
        movement = crud.create_stock_movement(db, movement_data, current_user.id)
        return crud.convert_stock_movement_to_response(movement)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/movements/", response_model=List[StockMovementResponse])
async def get_stock_movements(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    product_id: Optional[int] = Query(None, description="Filter by product"),
    movement_type: Optional[str] = Query(None, description="Filter by movement type"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[StockMovementResponse]:
    """Get stock movements with filtering and pagination."""
    movement_type_enum = None
    if movement_type:
        try:
            movement_type_enum = MovementType(movement_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid movement type")

    movements, total = crud.get_stock_movements(
        db=db,
        skip=skip,
        limit=limit,
        warehouse_id=warehouse_id,
        product_id=product_id,
        movement_type=movement_type_enum,
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
    )

    return [crud.convert_stock_movement_to_response(movement) for movement in movements]


# Stock Adjustment Endpoint
@router.post("/adjustments/", response_model=StockMovementResponse)
async def create_stock_adjustment(
    adjustment_data: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> StockMovementResponse:
    """Create a stock adjustment."""
    try:
        movement = crud.create_stock_adjustment(db, adjustment_data, current_user.id)
        return crud.convert_stock_movement_to_response(movement)
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Stock Reservation Endpoints
@router.post("/reservations/")
async def reserve_stock(
    reservation_data: StockReservationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Reserve stock for order fulfillment."""
    success = crud.reserve_stock(
        db=db,
        inventory_item_id=reservation_data.inventory_item_id,
        quantity=reservation_data.quantity,
        reserved_by=current_user.id,
    )

    if not success:
        raise HTTPException(
<<<<<<< HEAD
            status_code=400, detail="Insufficient stock available for reservation"
=======
            status_code=400,
            detail="Insufficient stock available for reservation"
>>>>>>> main
        )

    return {"message": "Stock reserved successfully", "success": True}


@router.delete("/reservations/{item_id}")
async def release_reservation(
    item_id: int,
    quantity: Decimal = Query(..., gt=0, description="Quantity to release"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Release reserved stock."""
    success = crud.release_reservation(
        db=db, inventory_item_id=item_id, quantity=quantity, released_by=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return {"message": "Reservation released successfully", "success": True}


# Analytics and Reporting Endpoints
@router.get("/statistics/", response_model=InventoryStatistics)
async def get_inventory_statistics(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> InventoryStatistics:
    """Get comprehensive inventory statistics."""
    stats = crud.get_inventory_statistics(
        db=db, organization_id=organization_id, warehouse_id=warehouse_id
    )

    return InventoryStatistics(**stats)


@router.get("/alerts/low-stock/", response_model=List[LowStockAlert])
async def get_low_stock_alerts(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[LowStockAlert]:
    """Get low stock alerts."""
    items, _ = crud.get_inventory_items(
        db=db,
        skip=0,
        limit=1000,
        warehouse_id=warehouse_id,
        organization_id=organization_id,
        low_stock_only=True,
    )

    alerts = []
    for item in items:
        # Get product and warehouse info
        from app.models.product import Product

        product = db.query(Product).filter(Product.id == item.product_id).first()
        warehouse = crud.get_warehouse_by_id(db, item.warehouse_id)

        if product and warehouse:
<<<<<<< HEAD
            alerts.append(
                LowStockAlert(
                    product_id=item.product_id,
                    product_code=product.code,
                    product_name=product.name,
                    warehouse_id=item.warehouse_id,
                    warehouse_name=warehouse.name,
                    current_quantity=item.quantity_available,
                    minimum_level=item.minimum_level or Decimal(0),
                    reorder_point=item.reorder_point,
                    needs_reorder=item.needs_reorder,
                )
            )
=======
            alerts.append(LowStockAlert(
                product_id=item.product_id,
                product_code=product.code,
                product_name=product.name,
                warehouse_id=item.warehouse_id,
                warehouse_name=warehouse.name,
                current_quantity=item.quantity_available,
                minimum_level=item.minimum_level or Decimal(0),
                reorder_point=item.reorder_point,
                needs_reorder=item.needs_reorder
            ))
>>>>>>> main

    return alerts


@router.get("/alerts/expiry/", response_model=List[ExpiryAlert])
async def get_expiry_alerts(
    days_ahead: int = Query(30, ge=1, le=365, description="Days ahead to check"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[ExpiryAlert]:
    """Get expiry alerts for items nearing expiration."""
    items, _ = crud.get_inventory_items(
        db=db,
        skip=0,
        limit=1000,
        warehouse_id=warehouse_id,
        organization_id=organization_id,
    )

    alerts = []
    for item in items:
        if item.is_near_expiry(days_ahead) and item.expiry_date:
            # Get product and warehouse info
            from app.models.product import Product

            product = db.query(Product).filter(Product.id == item.product_id).first()
            warehouse = crud.get_warehouse_by_id(db, item.warehouse_id)

            if product and warehouse:
<<<<<<< HEAD
                alerts.append(
                    ExpiryAlert(
                        product_id=item.product_id,
                        product_code=product.code,
                        product_name=product.name,
                        warehouse_id=item.warehouse_id,
                        warehouse_name=warehouse.name,
                        quantity=item.quantity_on_hand,
                        expiry_date=item.expiry_date,
                        days_until_expiry=item.days_until_expiry or 0,
                        lot_number=item.lot_number,
                        batch_number=item.batch_number,
                    )
                )
=======
                alerts.append(ExpiryAlert(
                    product_id=item.product_id,
                    product_code=product.code,
                    product_name=product.name,
                    warehouse_id=item.warehouse_id,
                    warehouse_name=warehouse.name,
                    quantity=item.quantity_on_hand,
                    expiry_date=item.expiry_date,
                    days_until_expiry=item.days_until_expiry or 0,
                    lot_number=item.lot_number,
                    batch_number=item.batch_number
                ))
>>>>>>> main

    return alerts


# Inventory Valuation Endpoint
@router.get("/valuation/")
async def get_inventory_valuation(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    as_of_date: Optional[date] = Query(None, description="Valuation as of date"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Get inventory valuation report."""
    items, _ = crud.get_inventory_items(
        db=db,
        skip=0,
        limit=10000,  # Large limit for valuation
        warehouse_id=warehouse_id,
        organization_id=organization_id,
    )

    total_value = Decimal(0)
    item_count = 0
    valuation_items = []

    for item in items:
        if item.total_cost and item.quantity_on_hand > 0:
            # Get product info
            from app.models.product import Product

            product = db.query(Product).filter(Product.id == item.product_id).first()
            warehouse = crud.get_warehouse_by_id(db, item.warehouse_id)

            if product and warehouse:
                item_value = item.total_cost
                total_value += item_value
                item_count += 1

<<<<<<< HEAD
                valuation_items.append(
                    {
                        "product_id": item.product_id,
                        "product_code": product.code,
                        "product_name": product.name,
                        "warehouse_id": item.warehouse_id,
                        "warehouse_name": warehouse.name,
                        "quantity_on_hand": float(item.quantity_on_hand),
                        "average_cost": float(item.average_cost)
                        if item.average_cost
                        else None,
                        "total_value": float(item_value),
                    }
                )
=======
                valuation_items.append({
                    "product_id": item.product_id,
                    "product_code": product.code,
                    "product_name": product.name,
                    "warehouse_id": item.warehouse_id,
                    "warehouse_name": warehouse.name,
                    "quantity_on_hand": float(item.quantity_on_hand),
                    "average_cost": float(item.average_cost) if item.average_cost else None,
                    "total_value": float(item_value)
                })
>>>>>>> main

    return {
        "as_of_date": as_of_date or date.today(),
        "total_items": item_count,
        "total_value": float(total_value),
        "items": valuation_items,
    }


# ERP Context Endpoint
@router.get("/context/{item_id}")
async def get_inventory_context(
    item_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
) -> dict:
    """Get ERP-specific inventory context for item."""
    item = crud.get_inventory_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Get related entities
    from app.models.product import Product

    product = db.query(Product).filter(Product.id == item.product_id).first()
    warehouse = crud.get_warehouse_by_id(db, item.warehouse_id)

    return {
        "inventory_item_id": item.id,
        "product": product.get_erp_context() if product else None,
        "warehouse": {
            "warehouse_id": warehouse.id,
            "code": warehouse.code,
            "name": warehouse.name,
            "is_active": warehouse.is_active,
        }
        if warehouse
        else None,
        "stock_info": {
            "quantity_on_hand": float(item.quantity_on_hand),
            "quantity_available": float(item.quantity_available),
            "quantity_reserved": float(item.quantity_reserved),
            "is_low_stock": item.is_low_stock,
            "needs_reorder": item.needs_reorder,
            "status": item.status,
        },
        "cost_info": {
            "average_cost": float(item.average_cost) if item.average_cost else None,
            "total_cost": float(item.total_cost) if item.total_cost else None,
        },
        "location": {"location_code": item.location_code, "zone": item.zone},
        "tracking": {
            "lot_number": item.lot_number,
            "batch_number": item.batch_number,
            "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
            "is_expired": item.is_expired,
<<<<<<< HEAD
            "days_until_expiry": item.days_until_expiry,
        },
=======
            "days_until_expiry": item.days_until_expiry
        }
>>>>>>> main
    }
