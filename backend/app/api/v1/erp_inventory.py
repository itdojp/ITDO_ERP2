"""
ERP Inventory Management API
Enhanced inventory management with stock movements, warehouse operations, and adjustments
"""

import logging
from datetime import datetime, UTC, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel, Field, validator

from app.core.dependencies import get_current_active_user, get_db
from app.core.tenant_deps import TenantDep, RequireApiAccess
from app.models.user import User
from app.models.organization import Organization
from app.models.product import Product
from app.models.warehouse import Warehouse, InventoryItem, StockMovement, MovementType, InventoryStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp-inventory", tags=["ERP Inventory Management"])


# Pydantic schemas
class WarehouseCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    organization_id: int = Field(..., description="Organization ID")
    
    # Location
    address: Optional[str] = None
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    prefecture: Optional[str] = Field(None, max_length=50)
    
    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    manager_name: Optional[str] = Field(None, max_length=100)
    
    # Specifications
    total_area: Optional[Decimal] = Field(None, ge=0)
    storage_capacity: Optional[Decimal] = Field(None, ge=0)
    temperature_controlled: bool = False
    is_default: bool = False
    is_active: bool = True


class StockAdjustmentRequest(BaseModel):
    product_id: int = Field(..., description="Product ID")
    warehouse_id: int = Field(..., description="Warehouse ID")
    adjustment_type: str = Field(..., regex="^(increase|decrease|set)$")
    quantity: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=200)
    cost_per_unit: Optional[Decimal] = Field(None, ge=0)
    location_code: Optional[str] = Field(None, max_length=50)
    lot_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None


class StockTransferRequest(BaseModel):
    product_id: int = Field(..., description="Product ID")
    from_warehouse_id: int = Field(..., description="Source warehouse ID")
    to_warehouse_id: int = Field(..., description="Destination warehouse ID")
    quantity: Decimal = Field(..., gt=0)
    reason: Optional[str] = Field(None, max_length=200)
    from_location: Optional[str] = Field(None, max_length=100)
    to_location: Optional[str] = Field(None, max_length=100)


class StockReservationRequest(BaseModel):
    product_id: int = Field(..., description="Product ID")
    warehouse_id: int = Field(..., description="Warehouse ID")
    quantity: Decimal = Field(..., gt=0)
    reference_type: str = Field(..., max_length=50)  # e.g., "sales_order"
    reference_id: int = Field(..., description="Reference ID")
    notes: Optional[str] = Field(None, max_length=500)


class WarehouseResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    organization_id: int
    organization_name: Optional[str]
    full_address: str
    phone: Optional[str]
    email: Optional[str]
    manager_name: Optional[str]
    total_area: Optional[Decimal]
    storage_capacity: Optional[Decimal]
    temperature_controlled: bool
    is_default: bool
    is_active: bool
    created_at: str
    
    # Computed fields
    inventory_count: int = 0
    total_stock_value: Decimal = Decimal(0)
    utilization_percentage: Optional[Decimal] = None


class InventoryItemResponse(BaseModel):
    id: int
    product_id: int
    product_code: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    
    # Quantities
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    quantity_in_transit: Decimal
    
    # Cost
    cost_per_unit: Optional[Decimal]
    average_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    
    # Location
    location_code: Optional[str]
    zone: Optional[str]
    
    # Stock levels
    minimum_level: Optional[Decimal]
    reorder_point: Optional[Decimal]
    
    # Status
    status: str
    is_low_stock: bool
    needs_reorder: bool
    
    # Dates
    last_received_date: Optional[str]
    last_issued_date: Optional[str]
    expiry_date: Optional[str]
    days_until_expiry: Optional[int]
    is_expired: bool
    
    # Batch tracking
    lot_number: Optional[str]
    batch_number: Optional[str]
    
    created_at: str
    updated_at: Optional[str]


class StockMovementResponse(BaseModel):
    id: int
    transaction_number: str
    product_id: int
    product_code: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    
    movement_type: str
    movement_date: str
    quantity: Decimal
    quantity_before: Decimal
    quantity_after: Decimal
    
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    
    reference_type: Optional[str]
    reference_number: Optional[str]
    reason: Optional[str]
    notes: Optional[str]
    
    performed_by: Optional[str]
    is_posted: bool
    is_reversed: bool
    
    created_at: str


class InventoryListResponse(BaseModel):
    inventory_items: List[InventoryItemResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class MovementListResponse(BaseModel):
    movements: List[StockMovementResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class InventoryStatsResponse(BaseModel):
    total_products: int
    total_warehouses: int
    total_stock_value: float
    low_stock_items: int
    expired_items: int
    near_expiry_items: int
    stock_by_warehouse: Dict[str, Dict[str, Any]]
    top_products_by_value: List[Dict[str, Any]]


# Warehouse Management
@router.post("/warehouses", response_model=WarehouseResponse)
async def create_warehouse(
    warehouse_request: WarehouseCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new warehouse"""
    try:
        # Check if warehouse code exists
        existing_warehouse = db.query(Warehouse).filter(
            and_(
                Warehouse.code == warehouse_request.code,
                Warehouse.organization_id == warehouse_request.organization_id
            )
        ).first()
        
        if existing_warehouse:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Warehouse with this code already exists in the organization"
            )
        
        # Validate organization
        organization = db.query(Organization).filter(Organization.id == warehouse_request.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Create warehouse
        warehouse_data = warehouse_request.dict()
        warehouse_data["created_by"] = current_user.id
        
        warehouse = Warehouse(**warehouse_data)
        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)
        
        logger.info(f"Warehouse created: {warehouse.id} by {current_user.id}")
        
        return WarehouseResponse(
            id=warehouse.id,
            code=warehouse.code,
            name=warehouse.name,
            description=warehouse.description,
            organization_id=warehouse.organization_id,
            organization_name=organization.name,
            full_address=warehouse.full_address,
            phone=warehouse.phone,
            email=warehouse.email,
            manager_name=warehouse.manager_name,
            total_area=warehouse.total_area,
            storage_capacity=warehouse.storage_capacity,
            temperature_controlled=warehouse.temperature_controlled,
            is_default=warehouse.is_default,
            is_active=warehouse.is_active,
            created_at=warehouse.created_at.isoformat(),
            inventory_count=len(warehouse.inventory_items),
            total_stock_value=warehouse.get_total_stock_value(),
            utilization_percentage=warehouse.get_utilization_percentage()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Warehouse creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create warehouse"
        )


# Inventory Operations
@router.post("/stock-adjustments")
async def adjust_stock(
    adjustment_request: StockAdjustmentRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Adjust inventory stock levels"""
    try:
        # Validate product and warehouse
        product = db.query(Product).filter(Product.id == adjustment_request.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        warehouse = db.query(Warehouse).filter(Warehouse.id == adjustment_request.warehouse_id).first()
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found"
            )
        
        # Get or create inventory item
        inventory_item = db.query(InventoryItem).filter(
            and_(
                InventoryItem.product_id == adjustment_request.product_id,
                InventoryItem.warehouse_id == adjustment_request.warehouse_id
            )
        ).first()
        
        if not inventory_item:
            inventory_item = InventoryItem(
                product_id=adjustment_request.product_id,
                warehouse_id=adjustment_request.warehouse_id,
                organization_id=product.organization_id,
                quantity_on_hand=Decimal(0),
                quantity_reserved=Decimal(0),
                quantity_available=Decimal(0),
                location_code=adjustment_request.location_code,
                cost_per_unit=adjustment_request.cost_per_unit,
                expiry_date=adjustment_request.expiry_date,
                lot_number=adjustment_request.lot_number,
                created_by=current_user.id
            )
            db.add(inventory_item)
            db.flush()
        
        # Calculate new quantity
        old_quantity = inventory_item.quantity_on_hand
        
        if adjustment_request.adjustment_type == "increase":
            new_quantity = old_quantity + adjustment_request.quantity
            movement_type = MovementType.IN
        elif adjustment_request.adjustment_type == "decrease":
            new_quantity = max(Decimal(0), old_quantity - adjustment_request.quantity)
            movement_type = MovementType.OUT
        else:  # set
            new_quantity = adjustment_request.quantity
            movement_type = MovementType.ADJUSTMENT
        
        # Update inventory
        inventory_item.quantity_on_hand = new_quantity
        inventory_item.calculate_available_quantity()
        
        if adjustment_request.cost_per_unit and adjustment_request.adjustment_type == "increase":
            inventory_item.update_average_cost(adjustment_request.cost_per_unit, adjustment_request.quantity)
        
        inventory_item.updated_by = current_user.id
        inventory_item.updated_at = datetime.now(UTC)
        
        # Create stock movement record
        transaction_number = f"ADJ-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        stock_movement = StockMovement(
            transaction_number=transaction_number,
            inventory_item_id=inventory_item.id,
            product_id=adjustment_request.product_id,
            warehouse_id=adjustment_request.warehouse_id,
            organization_id=product.organization_id,
            movement_type=movement_type.value,
            quantity=adjustment_request.quantity,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            unit_cost=adjustment_request.cost_per_unit,
            total_cost=adjustment_request.cost_per_unit * adjustment_request.quantity if adjustment_request.cost_per_unit else None,
            reference_type="adjustment",
            reason=adjustment_request.reason,
            lot_number=adjustment_request.lot_number,
            to_location=adjustment_request.location_code,
            performed_by=current_user.id,
            created_by=current_user.id
        )
        
        db.add(stock_movement)
        db.commit()
        
        logger.info(f"Stock adjusted: Product {product.code} in warehouse {warehouse.code} by {current_user.id}")
        
        return {
            "message": "Stock adjustment completed successfully",
            "transaction_number": transaction_number,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "change": new_quantity - old_quantity
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Stock adjustment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust stock"
        )


@router.get("/inventory", response_model=InventoryListResponse)
async def list_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    status: Optional[InventoryStatus] = Query(None),
    low_stock_only: bool = Query(False),
    expired_only: bool = Query(False),
    near_expiry_days: Optional[int] = Query(None, ge=1, le=365),
    sort_by: str = Query("product_name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List inventory items with filtering"""
    try:
        query = db.query(InventoryItem).filter(InventoryItem.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.join(Product).filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.code.ilike(search_term),
                    Product.sku.ilike(search_term),
                    InventoryItem.location_code.ilike(search_term)
                )
            )
        
        if organization_id:
            query = query.filter(InventoryItem.organization_id == organization_id)
        
        if warehouse_id:
            query = query.filter(InventoryItem.warehouse_id == warehouse_id)
        
        if product_id:
            query = query.filter(InventoryItem.product_id == product_id)
        
        if status:
            query = query.filter(InventoryItem.status == status.value)
        
        # Apply special filters
        if low_stock_only:
            query = query.filter(InventoryItem.quantity_available <= InventoryItem.minimum_level)
        
        if expired_only:
            query = query.filter(InventoryItem.expiry_date < date.today())
        
        if near_expiry_days:
            from datetime import timedelta
            near_expiry_date = date.today() + timedelta(days=near_expiry_days)
            query = query.filter(
                and_(
                    InventoryItem.expiry_date.isnot(None),
                    InventoryItem.expiry_date <= near_expiry_date,
                    InventoryItem.expiry_date >= date.today()
                )
            )
        
        # Join related tables for sorting and response
        query = query.join(Product).join(Warehouse)
        
        # Apply sorting
        if sort_by == "product_name":
            sort_column = Product.name
        elif sort_by == "warehouse_name":
            sort_column = Warehouse.name
        else:
            sort_column = getattr(InventoryItem, sort_by, InventoryItem.id)
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        total_count = query.count()
        inventory_items = query.offset(skip).limit(limit).all()
        
        # Prepare response
        item_responses = []
        for item in inventory_items:
            item_responses.append(InventoryItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_code=item.product.code,
                product_name=item.product.name,
                warehouse_id=item.warehouse_id,
                warehouse_name=item.warehouse.name,
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
                is_low_stock=item.is_low_stock,
                needs_reorder=item.needs_reorder,
                last_received_date=item.last_received_date.isoformat() if item.last_received_date else None,
                last_issued_date=item.last_issued_date.isoformat() if item.last_issued_date else None,
                expiry_date=item.expiry_date.isoformat() if item.expiry_date else None,
                days_until_expiry=item.days_until_expiry,
                is_expired=item.is_expired,
                lot_number=item.lot_number,
                batch_number=item.batch_number,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat() if item.updated_at else None
            ))
        
        return InventoryListResponse(
            inventory_items=item_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list inventory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inventory"
        )


@router.get("/stock-movements", response_model=MovementListResponse)
async def list_stock_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    movement_type: Optional[MovementType] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List stock movements with filtering"""
    try:
        query = db.query(StockMovement).filter(StockMovement.deleted_at.is_(None))
        
        # Apply filters
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        
        if warehouse_id:
            query = query.filter(StockMovement.warehouse_id == warehouse_id)
        
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type.value)
        
        if date_from:
            query = query.filter(StockMovement.movement_date >= datetime.combine(date_from, datetime.min.time()))
        
        if date_to:
            query = query.filter(StockMovement.movement_date <= datetime.combine(date_to, datetime.max.time()))
        
        # Join related tables
        query = query.join(Product).join(Warehouse)
        query = query.order_by(desc(StockMovement.movement_date))
        
        total_count = query.count()
        movements = query.offset(skip).limit(limit).all()
        
        # Get user names for performed_by
        user_ids = [m.performed_by for m in movements if m.performed_by]
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        user_names = {user.id: user.full_name for user in users}
        
        # Prepare response
        movement_responses = []
        for movement in movements:
            movement_responses.append(StockMovementResponse(
                id=movement.id,
                transaction_number=movement.transaction_number,
                product_id=movement.product_id,
                product_code=movement.product.code,
                product_name=movement.product.name,
                warehouse_id=movement.warehouse_id,
                warehouse_name=movement.warehouse.name,
                movement_type=movement.movement_type,
                movement_date=movement.movement_date.isoformat(),
                quantity=movement.quantity,
                quantity_before=movement.quantity_before,
                quantity_after=movement.quantity_after,
                unit_cost=movement.unit_cost,
                total_cost=movement.total_cost,
                reference_type=movement.reference_type,
                reference_number=movement.reference_number,
                reason=movement.reason,
                notes=movement.notes,
                performed_by=user_names.get(movement.performed_by) if movement.performed_by else None,
                is_posted=movement.is_posted,
                is_reversed=movement.is_reversed,
                created_at=movement.created_at.isoformat()
            ))
        
        return MovementListResponse(
            movements=movement_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list stock movements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stock movements"
        )


@router.post("/stock-transfer")
async def transfer_stock(
    transfer_request: StockTransferRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Transfer stock between warehouses"""
    try:
        # Validate product and warehouses
        product = db.query(Product).filter(Product.id == transfer_request.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        from_warehouse = db.query(Warehouse).filter(Warehouse.id == transfer_request.from_warehouse_id).first()
        to_warehouse = db.query(Warehouse).filter(Warehouse.id == transfer_request.to_warehouse_id).first()
        
        if not from_warehouse or not to_warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source or destination warehouse not found"
            )
        
        if from_warehouse.id == to_warehouse.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and destination warehouses must be different"
            )
        
        # Get source inventory
        source_inventory = db.query(InventoryItem).filter(
            and_(
                InventoryItem.product_id == transfer_request.product_id,
                InventoryItem.warehouse_id == transfer_request.from_warehouse_id
            )
        ).first()
        
        if not source_inventory or source_inventory.quantity_available < transfer_request.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock available for transfer"
            )
        
        # Get or create destination inventory
        dest_inventory = db.query(InventoryItem).filter(
            and_(
                InventoryItem.product_id == transfer_request.product_id,
                InventoryItem.warehouse_id == transfer_request.to_warehouse_id
            )
        ).first()
        
        if not dest_inventory:
            dest_inventory = InventoryItem(
                product_id=transfer_request.product_id,
                warehouse_id=transfer_request.to_warehouse_id,
                organization_id=product.organization_id,
                quantity_on_hand=Decimal(0),
                quantity_reserved=Decimal(0),
                quantity_available=Decimal(0),
                cost_per_unit=source_inventory.cost_per_unit,
                average_cost=source_inventory.average_cost,
                created_by=current_user.id
            )
            db.add(dest_inventory)
            db.flush()
        
        # Update inventories
        old_source_qty = source_inventory.quantity_on_hand
        old_dest_qty = dest_inventory.quantity_on_hand
        
        source_inventory.quantity_on_hand -= transfer_request.quantity
        source_inventory.calculate_available_quantity()
        
        dest_inventory.quantity_on_hand += transfer_request.quantity
        if source_inventory.average_cost:
            dest_inventory.update_average_cost(source_inventory.average_cost, transfer_request.quantity)
        dest_inventory.calculate_available_quantity()
        
        # Create movement records
        transaction_number = f"TRF-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
        
        # Outbound movement
        out_movement = StockMovement(
            transaction_number=f"{transaction_number}-OUT",
            inventory_item_id=source_inventory.id,
            product_id=transfer_request.product_id,
            warehouse_id=transfer_request.from_warehouse_id,
            organization_id=product.organization_id,
            movement_type=MovementType.TRANSFER.value,
            quantity=transfer_request.quantity,
            quantity_before=old_source_qty,
            quantity_after=source_inventory.quantity_on_hand,
            unit_cost=source_inventory.average_cost,
            reference_type="transfer",
            reference_number=transaction_number,
            reason=transfer_request.reason,
            from_location=transfer_request.from_location,
            to_location=f"Transfer to {to_warehouse.name}",
            performed_by=current_user.id,
            created_by=current_user.id
        )
        
        # Inbound movement
        in_movement = StockMovement(
            transaction_number=f"{transaction_number}-IN",
            inventory_item_id=dest_inventory.id,
            product_id=transfer_request.product_id,
            warehouse_id=transfer_request.to_warehouse_id,
            organization_id=product.organization_id,
            movement_type=MovementType.TRANSFER.value,
            quantity=transfer_request.quantity,
            quantity_before=old_dest_qty,
            quantity_after=dest_inventory.quantity_on_hand,
            unit_cost=source_inventory.average_cost,
            reference_type="transfer",
            reference_number=transaction_number,
            reason=transfer_request.reason,
            from_location=f"Transfer from {from_warehouse.name}",
            to_location=transfer_request.to_location,
            performed_by=current_user.id,
            created_by=current_user.id
        )
        
        db.add(out_movement)
        db.add(in_movement)
        db.commit()
        
        logger.info(f"Stock transferred: Product {product.code} from {from_warehouse.code} to {to_warehouse.code} by {current_user.id}")
        
        return {
            "message": "Stock transfer completed successfully",
            "transaction_number": transaction_number,
            "from_warehouse": from_warehouse.name,
            "to_warehouse": to_warehouse.name,
            "quantity_transferred": transfer_request.quantity
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Stock transfer failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transfer stock"
        )


@router.get("/statistics", response_model=InventoryStatsResponse)
async def get_inventory_statistics(
    organization_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get comprehensive inventory statistics"""
    try:
        query = db.query(InventoryItem).filter(InventoryItem.deleted_at.is_(None))
        
        if organization_id:
            query = query.filter(InventoryItem.organization_id == organization_id)
        
        if warehouse_id:
            query = query.filter(InventoryItem.warehouse_id == warehouse_id)
        
        # Basic counts
        inventory_items = query.all()
        total_products = len(set(item.product_id for item in inventory_items))
        
        warehouse_query = db.query(Warehouse).filter(Warehouse.deleted_at.is_(None))
        if organization_id:
            warehouse_query = warehouse_query.filter(Warehouse.organization_id == organization_id)
        total_warehouses = warehouse_query.count()
        
        # Calculate totals
        total_stock_value = sum(
            item.total_cost for item in inventory_items 
            if item.total_cost and item.quantity_on_hand > 0
        ) or 0
        
        low_stock_items = sum(1 for item in inventory_items if item.is_low_stock)
        expired_items = sum(1 for item in inventory_items if item.is_expired)
        near_expiry_items = sum(1 for item in inventory_items if item.is_near_expiry(30))
        
        # Stock by warehouse
        stock_by_warehouse = {}
        warehouses = warehouse_query.all()
        
        for warehouse in warehouses:
            warehouse_items = [item for item in inventory_items if item.warehouse_id == warehouse.id]
            stock_by_warehouse[warehouse.name] = {
                "total_items": len(warehouse_items),
                "total_value": sum(
                    item.total_cost for item in warehouse_items 
                    if item.total_cost and item.quantity_on_hand > 0
                ) or 0,
                "low_stock_items": sum(1 for item in warehouse_items if item.is_low_stock)
            }
        
        # Top products by value
        product_values = {}
        for item in inventory_items:
            if item.total_cost and item.quantity_on_hand > 0:
                if item.product_id not in product_values:
                    product_values[item.product_id] = {
                        "product_code": item.product.code,
                        "product_name": item.product.name,
                        "total_value": 0,
                        "total_quantity": 0
                    }
                product_values[item.product_id]["total_value"] += float(item.total_cost)
                product_values[item.product_id]["total_quantity"] += float(item.quantity_on_hand)
        
        top_products_by_value = sorted(
            product_values.values(),
            key=lambda x: x["total_value"],
            reverse=True
        )[:10]
        
        return InventoryStatsResponse(
            total_products=total_products,
            total_warehouses=total_warehouses,
            total_stock_value=float(total_stock_value),
            low_stock_items=low_stock_items,
            expired_items=expired_items,
            near_expiry_items=near_expiry_items,
            stock_by_warehouse=stock_by_warehouse,
            top_products_by_value=top_products_by_value
        )
    
    except Exception as e:
        logger.error(f"Failed to get inventory statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inventory statistics"
        )