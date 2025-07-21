"""Order processing models."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Order(BaseModel):
    """Order model for processing customer orders."""
    
    __tablename__ = "orders"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True, index=True
    )
    
    # Order details
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )  # 'pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'
    order_type: Mapped[str] = mapped_column(
        String(50), default="sales", index=True
    )  # 'sales', 'purchase', 'transfer', 'return'
    priority: Mapped[str] = mapped_column(
        String(50), default="normal"
    )  # 'low', 'normal', 'high', 'urgent'
    
    # Financial information
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00")
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00")
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00")
    )
    
    # Addresses and delivery
    billing_address: Mapped[Optional[str]] = mapped_column(Text)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Dates
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    required_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    shipped_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Tracking and references
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Organization and user tracking
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    assigned_to_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory", back_populates="order", cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_orders_customer_date", "customer_id", "order_date"),
        Index("idx_orders_status_date", "status", "order_date"),
        Index("idx_orders_org_status", "organization_id", "status"),
        Index("idx_orders_created_by", "created_by", "order_date"),
    )


class OrderItem(BaseModel):
    """Order line item model."""
    
    __tablename__ = "order_items"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False, index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True, index=True
    )
    
    # Item details
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Quantities and pricing
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2), default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), default=Decimal("0.00")
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    
    # Fulfillment tracking
    quantity_shipped: Mapped[int] = mapped_column(Integer, default=0)
    quantity_delivered: Mapped[int] = mapped_column(Integer, default=0)
    quantity_returned: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status and metadata
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled'
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    product: Mapped[Optional["Product"]] = relationship("Product")
    
    # Indexes
    __table_args__ = (
        Index("idx_order_items_order_product", "order_id", "product_id"),
        Index("idx_order_items_status", "status"),
    )


class OrderStatusHistory(BaseModel):
    """Order status change history."""
    
    __tablename__ = "order_status_history"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False, index=True
    )
    
    # Status change details
    previous_status: Mapped[Optional[str]] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Tracking
    changed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="status_history")
    changed_by_user: Mapped[Optional["User"]] = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_status_history_order_date", "order_id", "changed_at"),
        Index("idx_status_history_status", "new_status", "changed_at"),
    )


class OrderPayment(BaseModel):
    """Order payment tracking."""
    
    __tablename__ = "order_payments"
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False, index=True
    )
    
    # Payment details
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'cash', 'credit_card', 'bank_transfer', 'check', 'other'
    payment_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # 'pending', 'processing', 'completed', 'failed', 'refunded'
    
    # Amounts
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    
    # Transaction details
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    gateway_response: Mapped[Optional[str]] = mapped_column(Text)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Dates
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Notes and tracking
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order")
    created_by_user: Mapped[Optional["User"]] = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_payments_order_status", "order_id", "payment_status"),
        Index("idx_payments_method_status", "payment_method", "payment_status"),
        Index("idx_payments_transaction", "transaction_id"),
    )