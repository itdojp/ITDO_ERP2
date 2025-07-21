"""Inventory management models."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Category(BaseModel):
    """Product category model."""
    
    __tablename__ = "categories"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="category"
    )
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    
    # Indexes
    __table_args__ = (
        Index("idx_categories_org_code", "organization_id", "code"),
        Index("idx_categories_parent_active", "parent_id", "is_active"),
    )


class Product(BaseModel):
    """Product model for inventory management."""
    
    __tablename__ = "products"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Classification
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), index=True
    )
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    
    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00")
    )
    cost_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2)
    )
    
    # Inventory tracking
    track_quantity: Mapped[bool] = mapped_column(Boolean, default=True)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=0)
    maximum_stock: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Physical properties
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=10, scale=3))
    dimensions: Mapped[Optional[str]] = mapped_column(String(100))
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="each")
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    stock_movements: Mapped[List["StockMovement"]] = relationship(
        "StockMovement", back_populates="product", cascade="all, delete-orphan"
    )
    serial_numbers: Mapped[List["ProductSerial"]] = relationship(
        "ProductSerial", back_populates="product", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_products_org_sku", "organization_id", "sku"),
        Index("idx_products_category_active", "category_id", "is_active"),
        Index("idx_products_stock_level", "current_stock", "minimum_stock"),
        Index("idx_products_barcode", "barcode"),
    )


class StockMovement(BaseModel):
    """Stock movement tracking for inventory changes."""
    
    __tablename__ = "stock_movements"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    movement_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'in', 'out', 'adjustment', 'transfer', 'return'
    
    # Quantity and reference
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    new_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Transaction details
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2))
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=15, scale=2))
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Tracking
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    
    # Metadata
    movement_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="stock_movements")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    user: Mapped[Optional["User"]] = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_stock_movements_product_date", "product_id", "movement_date"),
        Index("idx_stock_movements_type_date", "movement_type", "movement_date"),
        Index("idx_stock_movements_org_date", "organization_id", "movement_date"),
    )


class ProductSerial(BaseModel):
    """Serial number tracking for serialized products."""
    
    __tablename__ = "product_serials"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    serial_number: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="available", index=True
    )  # 'available', 'sold', 'reserved', 'defective', 'returned'
    
    # Location and assignment
    location: Mapped[Optional[str]] = mapped_column(String(255))
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Tracking
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    
    # Metadata
    manufactured_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    warranty_expires: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="serial_numbers")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    
    # Indexes
    __table_args__ = (
        Index("idx_product_serials_product_status", "product_id", "status"),
        Index("idx_product_serials_org_status", "organization_id", "status"),
    )


class InventoryLocation(BaseModel):
    """Inventory storage location model."""
    
    __tablename__ = "inventory_locations"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("inventory_locations.id"), nullable=True
    )
    location_type: Mapped[str] = mapped_column(
        String(50), default="warehouse"
    )  # 'warehouse', 'aisle', 'rack', 'shelf', 'bin'
    
    # Address and contact
    address: Mapped[Optional[str]] = mapped_column(Text)
    manager_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    # Organization
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    parent: Mapped[Optional["InventoryLocation"]] = relationship(
        "InventoryLocation", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["InventoryLocation"]] = relationship(
        "InventoryLocation", back_populates="parent", cascade="all, delete-orphan"
    )
    manager: Mapped[Optional["User"]] = relationship("User")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    
    # Indexes
    __table_args__ = (
        Index("idx_locations_org_code", "organization_id", "code"),
        Index("idx_locations_parent_active", "parent_id", "is_active"),
    )