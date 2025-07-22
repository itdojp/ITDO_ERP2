"""
Warehouse and Inventory models for ERP system
"""

from datetime import datetime, date
from typing import TYPE_CHECKING
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.product import Product
    from app.models.user import User


class MovementType(str, Enum):
    """Stock movement types"""
    IN = "in"
    OUT = "out"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DAMAGE = "damage"
    LOSS = "loss"
    FOUND = "found"


class InventoryStatus(str, Enum):
    """Inventory status enumeration"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    DAMAGED = "damaged"
    QUARANTINE = "quarantine"
    EXPIRED = "expired"


class Warehouse(SoftDeletableModel):
    """Warehouse model for inventory management"""

    __tablename__ = "warehouses"

    # Basic warehouse information
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Organization relationship
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Location information
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prefecture: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="Japan")
    
    # Contact information
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Warehouse specifications
    total_area: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # square meters
    storage_capacity: Mapped[Decimal | None] = mapped_column(Numeric(15, 3), nullable=True)  # cubic meters
    max_weight_capacity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)  # kg
    
    # Climate control
    temperature_controlled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_temperature: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # Celsius
    max_temperature: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # Celsius
    humidity_controlled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Operating information
    operating_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)  # "9:00-17:00"
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Tokyo")
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    inventory_items: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="warehouse")
    stock_movements: Mapped[list["StockMovement"]] = relationship("StockMovement", back_populates="warehouse")
    
    @property
    def full_address(self) -> str:
        """Get formatted full address"""
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
        """Calculate total value of stock in warehouse"""
        total = Decimal(0)
        for item in self.inventory_items:
            if item.cost_per_unit and item.quantity_on_hand > 0:
                total += item.cost_per_unit * item.quantity_on_hand
        return total
    
    def get_utilization_percentage(self) -> Decimal | None:
        """Get warehouse utilization percentage"""
        if not self.storage_capacity:
            return None
        
        used_capacity = sum(
            item.volume_occupied for item in self.inventory_items 
            if item.volume_occupied
        )
        return (used_capacity / self.storage_capacity) * 100 if used_capacity else Decimal(0)
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
    
    def __repr__(self) -> str:
        return f"<Warehouse(id={self.id}, code='{self.code}', name='{self.name}')>"


class InventoryItem(SoftDeletableModel):
    """Inventory item tracking"""

    __tablename__ = "inventory_items"

    # Relationships
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Quantity information
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    quantity_available: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    quantity_in_transit: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    
    # Cost information
    cost_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    average_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Location in warehouse
    location_code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Aisle-Shelf-Bin
    bin_location: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(20), nullable=True)  # A, B, C zones
    
    # Physical properties
    unit_weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)  # kg per unit
    unit_volume: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)  # cubic meters per unit
    volume_occupied: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)  # total volume
    
    # Stock levels and reorder points
    minimum_level: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    maximum_level: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    reorder_point: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    reorder_quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    
    # Dates and expiry
    last_received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Batch and serial tracking
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_numbers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of serial numbers
    
    # Status and condition
    status: Mapped[str] = mapped_column(String(20), default=InventoryStatus.AVAILABLE.value, nullable=False)
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Cycle counting
    last_count_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cycle_count_frequency: Mapped[int | None] = mapped_column(Integer, nullable=True)  # days
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_expiry_tracking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_batch_tracking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_serial_tracking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped[Warehouse] = relationship("Warehouse", back_populates="inventory_items")
    organization: Mapped["Organization"] = relationship("Organization")
    movements: Mapped[list["StockMovement"]] = relationship("StockMovement", back_populates="inventory_item")
    
    @property
    def is_low_stock(self) -> bool:
        """Check if inventory is below minimum level"""
        if not self.minimum_level:
            return False
        return self.quantity_available < self.minimum_level
    
    @property
    def is_overstocked(self) -> bool:
        """Check if inventory exceeds maximum level"""
        if not self.maximum_level:
            return False
        return self.quantity_on_hand > self.maximum_level
    
    @property
    def needs_reorder(self) -> bool:
        """Check if inventory needs reordering"""
        if not self.reorder_point:
            return False
        return self.quantity_available <= self.reorder_point
    
    @property
    def days_until_expiry(self) -> int | None:
        """Get days until expiry"""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - date.today()
        return delta.days
    
    @property
    def is_expired(self) -> bool:
        """Check if inventory is expired"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date
    
    @property
    def is_near_expiry(self, days_threshold: int = 30) -> bool:
        """Check if inventory is near expiry"""
        days = self.days_until_expiry
        return days is not None and 0 <= days <= days_threshold
    
    @property
    def total_weight(self) -> Decimal | None:
        """Calculate total weight of inventory"""
        if not self.unit_weight:
            return None
        return self.unit_weight * self.quantity_on_hand
    
    def calculate_available_quantity(self):
        """Calculate and update available quantity"""
        self.quantity_available = max(0, self.quantity_on_hand - self.quantity_reserved)
    
    def update_average_cost(self, new_cost: Decimal, new_quantity: Decimal):
        """Update average cost using weighted average method"""
        if self.quantity_on_hand == 0:
            self.average_cost = new_cost
        else:
            total_value = (self.average_cost or 0) * self.quantity_on_hand + new_cost * new_quantity
            total_quantity = self.quantity_on_hand + new_quantity
            self.average_cost = total_value / total_quantity if total_quantity > 0 else Decimal(0)
        
        self.total_cost = self.average_cost * (self.quantity_on_hand + new_quantity)
    
    def __str__(self) -> str:
        return f"{self.product.code if self.product else 'Unknown'} @ {self.warehouse.code if self.warehouse else 'Unknown'}"
    
    def __repr__(self) -> str:
        return f"<InventoryItem(id={self.id}, product_id={self.product_id}, warehouse_id={self.warehouse_id}, qty={self.quantity_on_hand})>"


class StockMovement(SoftDeletableModel):
    """Stock movement transactions"""

    __tablename__ = "stock_movements"

    # Transaction identification
    transaction_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Relationships
    inventory_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Movement details
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    movement_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    
    # Cost information
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Reference information
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # purchase_order, sales_order, adjustment
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Batch and serial information
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_numbers: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Location information
    from_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    to_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Additional information
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # User who performed the movement
    performed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status flags
    is_posted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reversed_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("stock_movements.id"), nullable=True)
    
    # Relationships
    inventory_item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="movements")
    product: Mapped["Product"] = relationship("Product")
    warehouse: Mapped[Warehouse] = relationship("Warehouse", back_populates="stock_movements")
    organization: Mapped["Organization"] = relationship("Organization")
    performed_by_user: Mapped["User | None"] = relationship("User")
    reversed_by: Mapped["StockMovement | None"] = relationship("StockMovement", remote_side="StockMovement.id")
    
    @property
    def is_inbound(self) -> bool:
        """Check if movement is inbound (increases stock)"""
        return self.movement_type in [MovementType.IN.value, MovementType.RETURN.value, MovementType.FOUND.value]
    
    @property
    def is_outbound(self) -> bool:
        """Check if movement is outbound (decreases stock)"""
        return self.movement_type in [MovementType.OUT.value, MovementType.DAMAGE.value, MovementType.LOSS.value]
    
    @property
    def quantity_change(self) -> Decimal:
        """Get the net quantity change (positive for inbound, negative for outbound)"""
        if self.is_inbound:
            return self.quantity
        elif self.is_outbound:
            return -self.quantity
        else:  # Transfer or adjustment
            return self.quantity_after - self.quantity_before
    
    def can_be_reversed(self) -> bool:
        """Check if movement can be reversed"""
        return self.is_posted and not self.is_reversed and self.movement_type != MovementType.ADJUSTMENT.value
    
    def reverse_movement(self, reason: str, performed_by: int) -> "StockMovement":
        """Create a reversal movement"""
        if not self.can_be_reversed():
            raise ValueError("This movement cannot be reversed")
        
        # Create reverse movement
        reverse_movement = StockMovement(
            transaction_number=f"REV-{self.transaction_number}",
            inventory_item_id=self.inventory_item_id,
            product_id=self.product_id,
            warehouse_id=self.warehouse_id,
            organization_id=self.organization_id,
            movement_type=MovementType.OUT.value if self.is_inbound else MovementType.IN.value,
            quantity=self.quantity,
            quantity_before=self.quantity_after,
            quantity_after=self.quantity_before,
            unit_cost=self.unit_cost,
            total_cost=-self.total_cost if self.total_cost else None,
            reference_type="reversal",
            reference_id=self.id,
            reference_number=self.transaction_number,
            reason=f"Reversal: {reason}",
            performed_by=performed_by
        )
        
        # Mark original as reversed
        self.is_reversed = True
        self.reversed_by_id = reverse_movement.id
        
        return reverse_movement
    
    def __str__(self) -> str:
        return f"{self.transaction_number} - {self.movement_type} ({self.quantity})"
    
    def __repr__(self) -> str:
        return f"<StockMovement(id={self.id}, type='{self.movement_type}', qty={self.quantity})>"