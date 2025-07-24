"""
Basic inventory CRUD operations for ERP v17.0
Comprehensive inventory management with warehouses, stock tracking, and transactions
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.inventory import (
    InventoryItem,
    InventoryStatus,
    MovementType,
    StockMovement,
    Warehouse,
)
from app.schemas.inventory_basic import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    StockAdjustmentCreate,
    StockMovementCreate,
    StockMovementResponse,
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)


# Warehouse CRUD operations
def create_warehouse(
<<<<<<< HEAD
    db: Session, warehouse_data: WarehouseCreate, created_by: int
=======
    db: Session,
    warehouse_data: WarehouseCreate,
    created_by: int
>>>>>>> main
) -> Warehouse:
    """Create a new warehouse with validation."""
    # Check if warehouse code exists in organization
    existing_warehouse = (
        db.query(Warehouse)
        .filter(
            and_(
                Warehouse.code == warehouse_data.code,
                Warehouse.organization_id == warehouse_data.organization_id,
                Warehouse.deleted_at.is_(None),
            )
        )
<<<<<<< HEAD
        .first()
    )

    if existing_warehouse:
        raise BusinessLogicError(
            "Warehouse with this code already exists in the organization"
        )

    # Create warehouse
    warehouse_dict = warehouse_data.dict()
    warehouse_dict["created_by"] = created_by
=======
    ).first()

    if existing_warehouse:
        raise BusinessLogicError("Warehouse with this code already exists in the organization")

    # Create warehouse
    warehouse_dict = warehouse_data.dict()
    warehouse_dict['created_by'] = created_by
>>>>>>> main

    warehouse = Warehouse(**warehouse_dict)

    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)

    return warehouse


def get_warehouse_by_id(db: Session, warehouse_id: int) -> Optional[Warehouse]:
    """Get warehouse by ID."""
    return (
        db.query(Warehouse)
        .filter(and_(Warehouse.id == warehouse_id, Warehouse.deleted_at.is_(None)))
        .first()
    )


def get_warehouses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    organization_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> tuple[List[Warehouse], int]:
    """Get warehouses with filtering and pagination."""
    query = db.query(Warehouse).filter(Warehouse.deleted_at.is_(None))

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Warehouse.name.ilike(search_term),
                Warehouse.code.ilike(search_term),
                Warehouse.description.ilike(search_term),
                Warehouse.city.ilike(search_term),
            )
        )

    # Filters
    if organization_id:
        query = query.filter(Warehouse.organization_id == organization_id)

    if is_active is not None:
        query = query.filter(Warehouse.is_active == is_active)

    # Ordering
    query = query.order_by(Warehouse.name)

    # Count for pagination
    total = query.count()

    # Apply pagination
    warehouses = query.offset(skip).limit(limit).all()

    return warehouses, total


def update_warehouse(
    db: Session, warehouse_id: int, warehouse_data: WarehouseUpdate, updated_by: int
) -> Optional[Warehouse]:
    """Update warehouse information."""
    warehouse = get_warehouse_by_id(db, warehouse_id)
    if not warehouse:
        return None

    # Check for code conflicts if updating code
    if warehouse_data.code and warehouse_data.code != warehouse.code:
        existing_warehouse = (
            db.query(Warehouse)
            .filter(
                and_(
                    Warehouse.code == warehouse_data.code,
                    Warehouse.organization_id == warehouse.organization_id,
                    Warehouse.id != warehouse_id,
                    Warehouse.deleted_at.is_(None),
                )
            )
            .first()
        )
        if existing_warehouse:
            raise BusinessLogicError("Warehouse with this code already exists")

    # Update fields
    update_dict = warehouse_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(warehouse, key):
            setattr(warehouse, key, value)

    warehouse.updated_by = updated_by

    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)

    return warehouse


# Inventory Item CRUD operations
def create_inventory_item(
    db: Session, item_data: InventoryItemCreate, created_by: int
) -> InventoryItem:
    """Create inventory item for product in warehouse."""
    # Check if item already exists for this product/warehouse combination
    existing_item = (
        db.query(InventoryItem)
        .filter(
            and_(
                InventoryItem.product_id == item_data.product_id,
                InventoryItem.warehouse_id == item_data.warehouse_id,
                InventoryItem.deleted_at.is_(None),
            )
        )
<<<<<<< HEAD
        .first()
    )

    if existing_item:
        raise BusinessLogicError(
            "Inventory item already exists for this product in this warehouse"
        )

    # Create inventory item
    item_dict = item_data.dict()
    item_dict["created_by"] = created_by

    # Calculate available quantity
    item_dict["quantity_available"] = max(
        Decimal(0),
        item_dict.get("quantity_on_hand", 0) - item_dict.get("quantity_reserved", 0),
=======
    ).first()

    if existing_item:
        raise BusinessLogicError("Inventory item already exists for this product in this warehouse")

    # Create inventory item
    item_dict = item_data.dict()
    item_dict['created_by'] = created_by

    # Calculate available quantity
    item_dict['quantity_available'] = max(
        Decimal(0),
        item_dict.get('quantity_on_hand', 0) - item_dict.get('quantity_reserved', 0)
>>>>>>> main
    )

    inventory_item = InventoryItem(**item_dict)

    db.add(inventory_item)
    db.commit()
    db.refresh(inventory_item)

    return inventory_item


def get_inventory_item_by_id(db: Session, item_id: int) -> Optional[InventoryItem]:
    """Get inventory item by ID."""
    return (
        db.query(InventoryItem)
        .filter(and_(InventoryItem.id == item_id, InventoryItem.deleted_at.is_(None)))
        .first()
    )


def get_inventory_items(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    warehouse_id: Optional[int] = None,
    product_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    status: Optional[InventoryStatus] = None,
    low_stock_only: bool = False,
) -> tuple[List[InventoryItem], int]:
    """Get inventory items with filtering and pagination."""
    query = db.query(InventoryItem).filter(InventoryItem.deleted_at.is_(None))

    # Filters
    if warehouse_id:
        query = query.filter(InventoryItem.warehouse_id == warehouse_id)

    if product_id:
        query = query.filter(InventoryItem.product_id == product_id)

    if organization_id:
        query = query.filter(InventoryItem.organization_id == organization_id)

    if status:
        query = query.filter(InventoryItem.status == status.value)

    if low_stock_only:
        query = query.filter(
            and_(
                InventoryItem.minimum_level.isnot(None),
                InventoryItem.quantity_available <= InventoryItem.minimum_level,
            )
        )

    # Ordering
    query = query.order_by(desc(InventoryItem.updated_at))

    # Count for pagination
    total = query.count()

    # Apply pagination
    items = query.offset(skip).limit(limit).all()

    return items, total


def update_inventory_item(
    db: Session, item_id: int, item_data: InventoryItemUpdate, updated_by: int
) -> Optional[InventoryItem]:
    """Update inventory item information."""
    item = get_inventory_item_by_id(db, item_id)
    if not item:
        return None

    # Update fields
    update_dict = item_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(item, key):
            setattr(item, key, value)

    # Recalculate available quantity
    item.calculate_available_quantity()

    item.updated_by = updated_by

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# Stock Movement CRUD operations
def create_stock_movement(
    db: Session, movement_data: StockMovementCreate, performed_by: int
) -> StockMovement:
    """Create stock movement transaction."""
    # Generate transaction number
    transaction_number = generate_transaction_number(db, movement_data.movement_type)

    # Get inventory item
    inventory_item = get_inventory_item_by_id(db, movement_data.inventory_item_id)
    if not inventory_item:
        raise BusinessLogicError("Inventory item not found")

    # Create movement
    movement_dict = movement_data.dict()
<<<<<<< HEAD
    movement_dict["transaction_number"] = transaction_number
    movement_dict["performed_by"] = performed_by
    movement_dict["created_by"] = performed_by
    movement_dict["quantity_before"] = inventory_item.quantity_on_hand
=======
    movement_dict['transaction_number'] = transaction_number
    movement_dict['performed_by'] = performed_by
    movement_dict['created_by'] = performed_by
    movement_dict['quantity_before'] = inventory_item.quantity_on_hand
>>>>>>> main

    # Calculate quantity after based on movement type
    if movement_data.movement_type in [
        MovementType.IN.value,
        MovementType.RETURN.value,
    ]:
        new_quantity = inventory_item.quantity_on_hand + movement_data.quantity
    elif movement_data.movement_type in [
        MovementType.OUT.value,
        MovementType.SCRAP.value,
    ]:
        new_quantity = inventory_item.quantity_on_hand - movement_data.quantity
    else:  # ADJUSTMENT, TRANSFER
        new_quantity = inventory_item.quantity_on_hand + movement_data.quantity

<<<<<<< HEAD
    movement_dict["quantity_after"] = new_quantity
=======
    movement_dict['quantity_after'] = new_quantity
>>>>>>> main

    # Create movement record
    movement = StockMovement(**movement_dict)

    # Update inventory item quantities
    inventory_item.quantity_on_hand = new_quantity

    # Update cost if provided
    if movement_data.unit_cost and movement_data.movement_type == MovementType.IN.value:
<<<<<<< HEAD
        inventory_item.update_average_cost(
            movement_data.unit_cost, movement_data.quantity
        )
=======
        inventory_item.update_average_cost(movement_data.unit_cost, movement_data.quantity)
>>>>>>> main

    # Update dates
    if movement_data.movement_type == MovementType.IN.value:
        inventory_item.last_received_date = datetime.now(UTC)
    elif movement_data.movement_type == MovementType.OUT.value:
        inventory_item.last_issued_date = datetime.now(UTC)

    # Recalculate available quantity
    inventory_item.calculate_available_quantity()

    db.add(movement)
    db.add(inventory_item)
    db.commit()
    db.refresh(movement)

    return movement


def get_stock_movements(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    warehouse_id: Optional[int] = None,
    product_id: Optional[int] = None,
    movement_type: Optional[MovementType] = None,
    organization_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> tuple[List[StockMovement], int]:
    """Get stock movements with filtering and pagination."""
    query = db.query(StockMovement).filter(StockMovement.deleted_at.is_(None))

    # Filters
    if warehouse_id:
        query = query.filter(StockMovement.warehouse_id == warehouse_id)

    if product_id:
        query = query.filter(StockMovement.product_id == product_id)

    if organization_id:
        query = query.filter(StockMovement.organization_id == organization_id)

    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type.value)

    if from_date:
        query = query.filter(StockMovement.movement_date >= from_date)

    if to_date:
        query = query.filter(StockMovement.movement_date <= to_date)

    # Ordering - newest first
    query = query.order_by(desc(StockMovement.movement_date))

    # Count for pagination
    total = query.count()

    # Apply pagination
    movements = query.offset(skip).limit(limit).all()

    return movements, total


def create_stock_adjustment(
    db: Session, adjustment_data: StockAdjustmentCreate, performed_by: int
) -> StockMovement:
    """Create stock adjustment movement."""
    inventory_item = get_inventory_item_by_id(db, adjustment_data.inventory_item_id)
    if not inventory_item:
        raise BusinessLogicError("Inventory item not found")

    # Calculate adjustment quantity
    adjustment_quantity = adjustment_data.new_quantity - inventory_item.quantity_on_hand

    movement_data = StockMovementCreate(
        inventory_item_id=adjustment_data.inventory_item_id,
        product_id=inventory_item.product_id,
        warehouse_id=inventory_item.warehouse_id,
        organization_id=inventory_item.organization_id,
        movement_type=MovementType.ADJUSTMENT.value,
        quantity=adjustment_quantity,
        unit_cost=adjustment_data.unit_cost,
        reason=adjustment_data.reason,
        notes=adjustment_data.notes,
    )

    return create_stock_movement(db, movement_data, performed_by)


def reserve_stock(
    db: Session, inventory_item_id: int, quantity: Decimal, reserved_by: int
) -> bool:
    """Reserve stock for order fulfillment."""
    inventory_item = get_inventory_item_by_id(db, inventory_item_id)
    if not inventory_item:
        return False

    if inventory_item.reserve_stock(quantity):
        inventory_item.updated_by = reserved_by
        db.add(inventory_item)
        db.commit()
        return True

    return False


def release_reservation(
    db: Session, inventory_item_id: int, quantity: Decimal, released_by: int
) -> bool:
    """Release reserved stock."""
    inventory_item = get_inventory_item_by_id(db, inventory_item_id)
    if not inventory_item:
        return False

    inventory_item.release_reservation(quantity)
    inventory_item.updated_by = released_by

    db.add(inventory_item)
    db.commit()

    return True


def get_inventory_statistics(
    db: Session,
    organization_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Get comprehensive inventory statistics."""
    query = db.query(InventoryItem).filter(InventoryItem.deleted_at.is_(None))

    if organization_id:
        query = query.filter(InventoryItem.organization_id == organization_id)

    if warehouse_id:
        query = query.filter(InventoryItem.warehouse_id == warehouse_id)

    # Basic counts
    total_items = query.count()
<<<<<<< HEAD
    active_items = query.filter(
        InventoryItem.status == InventoryStatus.AVAILABLE.value
    ).count()
=======
    active_items = query.filter(InventoryItem.status == InventoryStatus.AVAILABLE.value).count()
>>>>>>> main

    # Stock value calculations
    total_value = db.query(func.sum(InventoryItem.total_cost)).filter(
        and_(
            InventoryItem.deleted_at.is_(None),
            InventoryItem.total_cost.isnot(None),
            InventoryItem.organization_id == organization_id
            if organization_id
            else True,
            InventoryItem.warehouse_id == warehouse_id if warehouse_id else True,
        )
    ).scalar() or Decimal(0)

    # Low stock items
    low_stock_items = query.filter(
        and_(
            InventoryItem.minimum_level.isnot(None),
            InventoryItem.quantity_available <= InventoryItem.minimum_level,
        )
    ).count()

    # Items by status
    status_counts = {}
    for status in InventoryStatus:
        count = query.filter(InventoryItem.status == status.value).count()
        status_counts[status.value] = count

    return {
        "total_items": total_items,
        "active_items": active_items,
        "total_stock_value": float(total_value),
        "low_stock_items": low_stock_items,
        "by_status": status_counts,
        "warehouses_count": db.query(Warehouse)
        .filter(
            and_(
                Warehouse.deleted_at.is_(None),
                Warehouse.organization_id == organization_id
                if organization_id
                else True,
            )
        )
        .count(),
    }


def generate_transaction_number(db: Session, movement_type: str) -> str:
    """Generate unique transaction number."""
    prefix = {
        MovementType.IN.value: "IN",
        MovementType.OUT.value: "OUT",
        MovementType.TRANSFER.value: "TRF",
        MovementType.ADJUSTMENT.value: "ADJ",
        MovementType.RETURN.value: "RET",
        MovementType.SCRAP.value: "SCR",
    }.get(movement_type, "TXN")

    # Get next sequence number
<<<<<<< HEAD
    last_movement = (
        db.query(StockMovement)
        .filter(StockMovement.transaction_number.like(f"{prefix}-%"))
        .order_by(desc(StockMovement.id))
        .first()
    )
=======
    last_movement = db.query(StockMovement).filter(
        StockMovement.transaction_number.like(f"{prefix}-%")
    ).order_by(desc(StockMovement.id)).first()
>>>>>>> main

    if last_movement and last_movement.transaction_number:
        try:
            last_number = int(last_movement.transaction_number.split("-")[1])
            next_number = last_number + 1
        except (IndexError, ValueError):
            next_number = 1
    else:
        next_number = 1

    return f"{prefix}-{next_number:06d}"


def convert_warehouse_to_response(warehouse: Warehouse) -> WarehouseResponse:
    """Convert Warehouse model to response schema."""
    return WarehouseResponse(
        id=warehouse.id,
        code=warehouse.code,
        name=warehouse.name,
        description=warehouse.description,
        organization_id=warehouse.organization_id,
        address=warehouse.address,
        postal_code=warehouse.postal_code,
        city=warehouse.city,
        prefecture=warehouse.prefecture,
        phone=warehouse.phone,
        email=warehouse.email,
        manager_name=warehouse.manager_name,
        total_area=warehouse.total_area,
        storage_capacity=warehouse.storage_capacity,
        temperature_controlled=warehouse.temperature_controlled,
        is_default=warehouse.is_default,
        is_active=warehouse.is_active,
        full_address=warehouse.full_address,
        created_at=warehouse.created_at,
        updated_at=warehouse.updated_at,
    )


def convert_inventory_item_to_response(item: InventoryItem) -> InventoryItemResponse:
    """Convert InventoryItem model to response schema."""
    return InventoryItemResponse(
        id=item.id,
        product_id=item.product_id,
        warehouse_id=item.warehouse_id,
        organization_id=item.organization_id,
        quantity_on_hand=item.quantity_on_hand,
        quantity_reserved=item.quantity_reserved,
        quantity_available=item.quantity_available,
        quantity_in_transit=item.quantity_in_transit,
        cost_per_unit=item.cost_per_unit,
        average_cost=item.average_cost,
        total_cost=item.total_cost,
        location_code=item.location_code,
        zone=item.zone,
        minimum_level=item.minimum_level,
        reorder_point=item.reorder_point,
        status=item.status,
        last_received_date=item.last_received_date,
        last_issued_date=item.last_issued_date,
        expiry_date=item.expiry_date,
        lot_number=item.lot_number,
        batch_number=item.batch_number,
        is_low_stock=item.is_low_stock,
        needs_reorder=item.needs_reorder,
        is_expired=item.is_expired,
        days_until_expiry=item.days_until_expiry,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def convert_stock_movement_to_response(
    movement: StockMovement,
) -> StockMovementResponse:
    """Convert StockMovement model to response schema."""
    return StockMovementResponse(
        id=movement.id,
        transaction_number=movement.transaction_number,
        inventory_item_id=movement.inventory_item_id,
        product_id=movement.product_id,
        warehouse_id=movement.warehouse_id,
        organization_id=movement.organization_id,
        movement_type=movement.movement_type,
        movement_date=movement.movement_date,
        quantity=movement.quantity,
        quantity_before=movement.quantity_before,
        quantity_after=movement.quantity_after,
        unit_cost=movement.unit_cost,
        total_cost=movement.total_cost,
        reference_type=movement.reference_type,
        reference_number=movement.reference_number,
        reference_id=movement.reference_id,
        reason=movement.reason,
        notes=movement.notes,
        from_location=movement.from_location,
        to_location=movement.to_location,
        lot_number=movement.lot_number,
        performed_by=movement.performed_by,
        is_posted=movement.is_posted,
        is_reversed=movement.is_reversed,
<<<<<<< HEAD
        created_at=movement.created_at,
=======
        created_at=movement.created_at
>>>>>>> main
    )
