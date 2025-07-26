"""
ITDO ERP Backend - Unified Inventory API
Day 13: API Integration - Inventory Management Unified API
Integrates inventory_v21.py and inventory_management_v67.py functionality
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.inventory import InventoryBalance, InventoryLocation, InventoryMovement
from app.models.user import User

# Mock authentication dependency for unified APIs
async def get_current_user() -> User:
    """Mock current user for unified APIs"""
    from unittest.mock import Mock
    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


# Inventory Status Enums
class MovementType(str, Enum):
    RECEIPT = "receipt"
    SHIPMENT = "shipment"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"


class InventoryStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    DAMAGED = "damaged"
    EXPIRED = "expired"


class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    STORE = "store"
    TRANSIT = "transit"
    VIRTUAL = "virtual"


# Pydantic Schemas
class InventoryLocationBase(BaseModel):
    """Base inventory location schema"""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    location_type: LocationType
    address: Optional[Dict[str, str]] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: bool = True
    accepts_receipts: bool = True
    accepts_shipments: bool = True
    total_capacity: Optional[Decimal] = Field(None, ge=0)
    capacity_unit: Optional[str] = None


class LocationCreate(InventoryLocationBase):
    """Schema for creating a new location"""

    pass


class LocationResponse(InventoryLocationBase):
    """Schema for location response"""

    id: uuid.UUID
    level: int = 0
    path: str
    created_at: datetime
    capacity_utilization: Optional[float] = None

    class Config:
        from_attributes = True


class InventoryBalanceBase(BaseModel):
    """Base inventory balance schema"""

    product_id: uuid.UUID
    location_id: uuid.UUID
    quantity_on_hand: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_available: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_reserved: Decimal = Field(default=Decimal("0"), ge=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    average_cost: Optional[Decimal] = Field(None, ge=0)
    minimum_stock: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[Decimal] = Field(None, ge=0)
    maximum_stock: Optional[Decimal] = Field(None, ge=0)


class InventoryBalanceResponse(InventoryBalanceBase):
    """Schema for inventory balance response"""

    id: uuid.UUID
    status: InventoryStatus
    last_movement_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MovementCreate(BaseModel):
    """Schema for creating inventory movement"""

    product_id: uuid.UUID
    location_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    reference_number: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class MovementResponse(BaseModel):
    """Schema for movement response"""

    id: uuid.UUID
    movement_number: str
    product_id: uuid.UUID
    location_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    reference_number: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: datetime
    created_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class StockTransferRequest(BaseModel):
    """Schema for stock transfer request"""

    product_id: uuid.UUID
    from_location_id: uuid.UUID
    to_location_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    reason: Optional[str] = None
    notes: Optional[str] = None


# Unified Inventory Service
class UnifiedInventoryService:
    """Unified service for inventory management operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def create_location(
        self, location_data: LocationCreate, user_id: uuid.UUID
    ) -> LocationResponse:
        """Create a new inventory location"""

        # Check for duplicate code
        existing = await self.db.execute(
            select(InventoryLocation).where(
                InventoryLocation.code == location_data.code
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Location with code '{location_data.code}' already exists",
            )

        # Calculate level and path
        level = 0
        path = location_data.code

        if location_data.parent_id:
            parent_result = await self.db.execute(
                select(InventoryLocation).where(
                    InventoryLocation.id == location_data.parent_id
                )
            )
            parent = parent_result.scalar_one_or_none()
            if parent:
                level = parent.level + 1
                path = f"{parent.path}/{location_data.code}"

        # Create location
        location = InventoryLocation(
            id=uuid.uuid4(),
            code=location_data.code,
            name=location_data.name,
            location_type=location_data.location_type.value,
            address=location_data.address,
            parent_id=location_data.parent_id,
            level=level,
            path=path,
            is_active=location_data.is_active,
            accepts_receipts=location_data.accepts_receipts,
            accepts_shipments=location_data.accepts_shipments,
            total_capacity=location_data.total_capacity,
            capacity_unit=location_data.capacity_unit,
            created_at=datetime.utcnow(),
        )

        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)

        return LocationResponse.from_orm(location)

    async def get_inventory_balance(
        self,
        product_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
    ) -> List[InventoryBalanceResponse]:
        """Get inventory balances with optional filtering"""

        query = select(InventoryBalance).options(
            selectinload(InventoryBalance.product),
            selectinload(InventoryBalance.location),
        )

        filters = []
        if product_id:
            filters.append(InventoryBalance.product_id == product_id)
        if location_id:
            filters.append(InventoryBalance.location_id == location_id)

        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        balances = result.scalars().all()

        return [InventoryBalanceResponse.from_orm(balance) for balance in balances]

    async def update_inventory_balance(
        self,
        product_id: uuid.UUID,
        location_id: uuid.UUID,
        quantity_change: Decimal,
        movement_type: MovementType,
        unit_cost: Optional[Decimal] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> InventoryBalanceResponse:
        """Update inventory balance with movement tracking"""

        # Get or create balance record
        result = await self.db.execute(
            select(InventoryBalance).where(
                and_(
                    InventoryBalance.product_id == product_id,
                    InventoryBalance.location_id == location_id,
                )
            )
        )
        balance = result.scalar_one_or_none()

        if not balance:
            balance = InventoryBalance(
                id=uuid.uuid4(),
                product_id=product_id,
                location_id=location_id,
                quantity_on_hand=Decimal("0"),
                quantity_available=Decimal("0"),
                quantity_reserved=Decimal("0"),
                status=InventoryStatus.AVAILABLE.value,
                created_at=datetime.utcnow(),
            )
            self.db.add(balance)

        # Validate movement
        if movement_type in [MovementType.SHIPMENT, MovementType.TRANSFER]:
            if balance.quantity_available < abs(quantity_change):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient inventory for this operation",
                )

        # Update quantities
        if movement_type == MovementType.RECEIPT:
            balance.quantity_on_hand += quantity_change
            balance.quantity_available += quantity_change
        elif movement_type == MovementType.SHIPMENT:
            balance.quantity_on_hand -= abs(quantity_change)
            balance.quantity_available -= abs(quantity_change)
        elif movement_type == MovementType.ADJUSTMENT:
            balance.quantity_on_hand += quantity_change
            balance.quantity_available += quantity_change
        elif movement_type == MovementType.TRANSFER:
            balance.quantity_on_hand -= abs(quantity_change)
            balance.quantity_available -= abs(quantity_change)

        # Update cost information
        if unit_cost and movement_type == MovementType.RECEIPT:
            if balance.quantity_on_hand > 0:
                total_cost = (balance.average_cost or Decimal("0")) * (
                    balance.quantity_on_hand - quantity_change
                )
                total_cost += unit_cost * quantity_change
                balance.average_cost = total_cost / balance.quantity_on_hand
            else:
                balance.average_cost = unit_cost
            balance.unit_cost = unit_cost

        balance.last_movement_at = datetime.utcnow()
        balance.updated_at = datetime.utcnow()

        # Generate movement number
        movement_counter = await self.redis.incr(
            f"movement_counter:{datetime.utcnow().strftime('%Y%m%d')}"
        )
        await self.redis.expire(
            f"movement_counter:{datetime.utcnow().strftime('%Y%m%d')}", 86400
        )
        movement_number = (
            f"MOV-{datetime.utcnow().strftime('%Y%m%d')}-{movement_counter:06d}"
        )

        # Create movement record
        movement = InventoryMovement(
            id=uuid.uuid4(),
            movement_number=movement_number,
            product_id=product_id,
            location_id=location_id,
            movement_type=movement_type.value,
            quantity=abs(quantity_change),
            unit_cost=unit_cost,
            status="completed",
            created_at=datetime.utcnow(),
            created_by=user_id,
        )

        self.db.add(movement)
        await self.db.commit()
        await self.db.refresh(balance)

        return InventoryBalanceResponse.from_orm(balance)

    async def create_stock_transfer(
        self, transfer_data: StockTransferRequest, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Create stock transfer between locations"""

        # Validate locations
        locations_result = await self.db.execute(
            select(InventoryLocation).where(
                InventoryLocation.id.in_(
                    [transfer_data.from_location_id, transfer_data.to_location_id]
                )
            )
        )
        locations = {loc.id: loc for loc in locations_result.scalars().all()}

        from_location = locations.get(transfer_data.from_location_id)
        to_location = locations.get(transfer_data.to_location_id)

        if not from_location or not to_location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both locations not found",
            )

        if not from_location.accepts_shipments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From location does not accept shipments",
            )

        if not to_location.accepts_receipts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="To location does not accept receipts",
            )

        # Check source inventory
        from_balance_result = await self.db.execute(
            select(InventoryBalance).where(
                and_(
                    InventoryBalance.product_id == transfer_data.product_id,
                    InventoryBalance.location_id == transfer_data.from_location_id,
                )
            )
        )
        from_balance = from_balance_result.scalar_one_or_none()

        if not from_balance or from_balance.quantity_available < transfer_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient inventory for transfer",
            )

        # Perform transfer (shipment from source, receipt to destination)
        await self.update_inventory_balance(
            product_id=transfer_data.product_id,
            location_id=transfer_data.from_location_id,
            quantity_change=-transfer_data.quantity,
            movement_type=MovementType.TRANSFER,
            unit_cost=from_balance.unit_cost,
            user_id=user_id,
        )

        await self.update_inventory_balance(
            product_id=transfer_data.product_id,
            location_id=transfer_data.to_location_id,
            quantity_change=transfer_data.quantity,
            movement_type=MovementType.RECEIPT,
            unit_cost=from_balance.unit_cost,
            user_id=user_id,
        )

        # Generate transfer ID
        transfer_id = uuid.uuid4()

        return {
            "transfer_id": str(transfer_id),
            "product_id": transfer_data.product_id,
            "from_location_id": transfer_data.from_location_id,
            "to_location_id": transfer_data.to_location_id,
            "quantity": transfer_data.quantity,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "message": "Stock transfer completed successfully",
        }


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_inventory_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> UnifiedInventoryService:
    """Get inventory service instance"""
    return UnifiedInventoryService(db, redis)


# API Endpoints - Unified Inventory API
@router.post(
    "/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED
)
async def create_location(
    location_data: LocationCreate,
    current_user: User = Depends(get_current_user),
    service: UnifiedInventoryService = Depends(get_inventory_service),
):
    """Create a new inventory location"""
    return await service.create_location(location_data, current_user.id)


@router.get("/balances", response_model=List[InventoryBalanceResponse])
async def get_inventory_balances(
    product_id: Optional[uuid.UUID] = Query(None),
    location_id: Optional[uuid.UUID] = Query(None),
    service: UnifiedInventoryService = Depends(get_inventory_service),
):
    """Get inventory balances with optional filtering"""
    return await service.get_inventory_balance(
        product_id=product_id, location_id=location_id
    )


@router.post("/movements", response_model=InventoryBalanceResponse)
async def create_inventory_movement(
    movement_data: MovementCreate,
    current_user: User = Depends(get_current_user),
    service: UnifiedInventoryService = Depends(get_inventory_service),
):
    """Create an inventory movement"""
    return await service.update_inventory_balance(
        product_id=movement_data.product_id,
        location_id=movement_data.location_id,
        quantity_change=movement_data.quantity
        if movement_data.movement_type == MovementType.RECEIPT
        else -movement_data.quantity,
        movement_type=movement_data.movement_type,
        unit_cost=movement_data.unit_cost,
        user_id=current_user.id,
    )


@router.post("/transfers", response_model=Dict[str, Any])
async def create_stock_transfer(
    transfer_data: StockTransferRequest,
    current_user: User = Depends(get_current_user),
    service: UnifiedInventoryService = Depends(get_inventory_service),
):
    """Create a stock transfer between locations"""
    return await service.create_stock_transfer(transfer_data, current_user.id)


# Legacy endpoints for backward compatibility
@router.post("/inventory-v21", response_model=Dict[str, Any], deprecated=True)
async def add_stock_v21(
    product_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    service: UnifiedInventoryService = Depends(get_inventory_service),
):
    """Legacy v21 inventory addition endpoint (deprecated)"""
    # For backward compatibility, assume a default location
    default_location_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    try:
        result = await service.update_inventory_balance(
            product_id=uuid.UUID(int=product_id),
            location_id=default_location_id,
            quantity_change=Decimal(str(quantity)),
            movement_type=MovementType.RECEIPT,
            user_id=current_user.id,
        )

        return {
            "id": len(await service.get_inventory_balance()) + 1,
            "product_id": product_id,
            "quantity": quantity,
            "status": "success",
        }
    except Exception as e:
        return {
            "id": product_id,
            "product_id": product_id,
            "quantity": quantity,
            "status": "error",
            "message": str(e),
        }


@router.get("/inventory-v21", response_model=List[Dict[str, Any]], deprecated=True)
async def list_inventory_v21(
    service: UnifiedInventoryService = Depends(get_inventory_service),
):
    """Legacy v21 inventory listing endpoint (deprecated)"""
    balances = await service.get_inventory_balance()
    return [
        {
            "id": str(balance.id),
            "product_id": str(balance.product_id),
            "quantity": float(balance.quantity_on_hand),
        }
        for balance in balances
    ]


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for unified inventory API"""
    return {
        "status": "healthy",
        "service": "unified-inventory-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
