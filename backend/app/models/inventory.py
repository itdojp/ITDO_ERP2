"""
Inventory models for ERP v17.0
Basic inventory management with warehouses, stock items, and transactions
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.product import Product
    from app.models.user import User


class MovementType(str, Enum):
    """Stock movement type enumeration."""
    IN = "in"              # Stock in (receipt)
    OUT = "out"            # Stock out (issue)
    TRANSFER = "transfer"   # Transfer between warehouses
    ADJUSTMENT = "adjustment"  # Inventory adjustment
    RETURN = "return"      # Return to supplier
    SCRAP = "scrap"        # Scrapped/damaged


class InventoryStatus(str, Enum):
    """Inventory status enumeration."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    ON_HOLD = "on_hold"
    DAMAGED = "damaged"
    EXPIRED = "expired"


class Warehouse(SoftDeletableModel):
    """Warehouse model for storing inventory."""

    __tablename__ = "warehouses"

    # Basic fields
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Organization
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Location details
    address: Mapped[str | None] = mapped_column(String(500))
    postal_code: Mapped[str | None] = mapped_column(String(10))
    city: Mapped[str | None] = mapped_column(String(100))
    prefecture: Mapped[str | None] = mapped_column(String(50))

    # Contact information
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    manager_name: Mapped[str | None] = mapped_column(String(100))

    # Specifications
    total_area: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # m²
    storage_capacity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))  # capacity units
    temperature_controlled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="warehouse"
    )
    stock_movements: Mapped[list["StockMovement"]] = relationship(
        "StockMovement", back_populates="warehouse"
    )

    @property
    def full_address(self) -> str:
        """Get full formatted address."""
        parts = []
        if self.postal_code:
            parts.append(f"〒{self.postal_code}")
        if self.prefecture:
            parts.append(self.prefecture)
        if self.city:
            parts.append(self.city)
        if self.address:
            parts.append(self.address)
        return " ".join(parts) if parts else ""

    def get_total_stock_value(self) -> Decimal:
        """Calculate total stock value in warehouse."""
        total = Decimal(0)
        for item in self.inventory_items:
            if item.total_cost and item.quantity_on_hand > 0:
                total += item.total_cost
        return total

    def get_utilization_percentage(self) -> Decimal | None:
        """Calculate storage utilization percentage."""
        if not self.storage_capacity or self.storage_capacity <= 0:
            return None

        used_capacity = sum(
            item.quantity_on_hand for item in self.inventory_items
            if item.quantity_on_hand > 0
        )

        return (used_capacity / self.storage_capacity) * 100

    def __repr__(self) -> str:
        return f"<Warehouse(id={self.id}, code='{self.code}', name='{self.name}')>"


class InventoryItem(SoftDeletableModel):
    """Inventory item representing stock of a product in a warehouse."""

    __tablename__ = "inventory_items"

    # Product and location
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Quantities
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    quantity_available: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    quantity_in_transit: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)

    # Cost information
    cost_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    average_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Location within warehouse
    location_code: Mapped[str | None] = mapped_column(String(50))
    zone: Mapped[str | None] = mapped_column(String(50))

    # Stock levels
    minimum_level: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    reorder_point: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))

    # Status
    status: Mapped[str] = mapped_column(String(20), default=InventoryStatus.AVAILABLE.value)

    # Dates for tracking
    last_received_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_issued_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[date | None] = mapped_column(Date)

    # Batch tracking
    lot_number: Mapped[str | None] = mapped_column(String(100))
    batch_number: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="inventory_items")
    organization: Mapped["Organization"] = relationship("Organization")
    stock_movements: Mapped[list["StockMovement"]] = relationship(
        "StockMovement", back_populates="inventory_item"
    )

    @property
    def is_low_stock(self) -> bool:
        """Check if stock level is low."""
        if self.minimum_level and self.minimum_level > 0:
            return self.quantity_available <= self.minimum_level
        return False

    @property
    def needs_reorder(self) -> bool:
        """Check if reorder is needed."""
        if self.reorder_point and self.reorder_point > 0:
            return self.quantity_available <= self.reorder_point
        return False

    @property
    def is_expired(self) -> bool:
        """Check if inventory is expired."""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False

    @property
    def days_until_expiry(self) -> int | None:
        """Get days until expiry."""
        if self.expiry_date:
            delta = self.expiry_date - date.today()
            return delta.days
        return None

    def is_near_expiry(self, days_threshold: int = 30) -> bool:
        """Check if near expiry within threshold."""
        if self.days_until_expiry is not None:
            return 0 <= self.days_until_expiry <= days_threshold
        return False

    def calculate_available_quantity(self) -> None:
        """Calculate available quantity (on_hand - reserved)."""
        self.quantity_available = max(Decimal(0), self.quantity_on_hand - self.quantity_reserved)

    def update_average_cost(self, new_unit_cost: Decimal, new_quantity: Decimal) -> None:
        """Update average cost based on weighted average."""
        if self.quantity_on_hand == 0:
            self.average_cost = new_unit_cost
            self.cost_per_unit = new_unit_cost
        else:
            total_value = (self.average_cost * self.quantity_on_hand) + (new_unit_cost * new_quantity)
            total_quantity = self.quantity_on_hand + new_quantity
            self.average_cost = total_value / total_quantity

        # Update total cost
        self.total_cost = self.average_cost * (self.quantity_on_hand + new_quantity)

    def reserve_stock(self, quantity: Decimal) -> bool:
        """Reserve stock for order."""
        if self.quantity_available >= quantity:
            self.quantity_reserved += quantity
            self.calculate_available_quantity()
            return True
        return False

    def release_reservation(self, quantity: Decimal) -> None:
        """Release reserved stock."""
        self.quantity_reserved = max(Decimal(0), self.quantity_reserved - quantity)
        self.calculate_available_quantity()

    def __repr__(self) -> str:
        return f"<InventoryItem(id={self.id}, product_id={self.product_id}, warehouse_id={self.warehouse_id})>"


class StockMovement(SoftDeletableModel):
    """Stock movement transaction record."""

    __tablename__ = "stock_movements"

    # Transaction identification
    transaction_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Related entities
    inventory_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Movement details
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    movement_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)

    # Cost information
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    # Reference information
    reference_type: Mapped[str | None] = mapped_column(String(50))  # 'sales_order', 'purchase_order', etc.
    reference_number: Mapped[str | None] = mapped_column(String(100))
    reference_id: Mapped[int | None] = mapped_column(Integer)

    # Movement details
    reason: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)

    # Location details
    from_location: Mapped[str | None] = mapped_column(String(100))
    to_location: Mapped[str | None] = mapped_column(String(100))
    lot_number: Mapped[str | None] = mapped_column(String(100))

    # User tracking
    performed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))

    # Status
    is_posted: Mapped[bool] = mapped_column(Boolean, default=True)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversed_by_movement_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("stock_movements.id"))

    # Relationships
    inventory_item: Mapped["InventoryItem"] = relationship("InventoryItem", back_populates="stock_movements")
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="stock_movements")
    organization: Mapped["Organization"] = relationship("Organization")
    performed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[performed_by])

    # Self-referential for reversals
    reversed_by_movement: Mapped[Optional["StockMovement"]] = relationship(
        "StockMovement", remote_side="StockMovement.id"
    )

    def reverse_movement(self, reversed_by: int, reason: str) -> "StockMovement":
        """Create a reversal movement."""
        reversal = StockMovement(
            transaction_number=f"REV-{self.transaction_number}",
            inventory_item_id=self.inventory_item_id,
            product_id=self.product_id,
            warehouse_id=self.warehouse_id,
            organization_id=self.organization_id,
            movement_type=self.movement_type,
            quantity=-self.quantity,  # Negative quantity for reversal
            quantity_before=self.quantity_after,
            quantity_after=self.quantity_before,
            unit_cost=self.unit_cost,
            total_cost=-self.total_cost if self.total_cost else None,
            reference_type="reversal",
            reference_number=self.transaction_number,
            reference_id=self.id,
            reason=reason,
            performed_by=reversed_by,
            created_by=reversed_by,
            reversed_by_movement_id=self.id
        )

        # Mark original as reversed
        self.is_reversed = True

        return reversal

    def __repr__(self) -> str:
        return f"<StockMovement(id={self.id}, transaction_number='{self.transaction_number}', type='{self.movement_type}')>"
