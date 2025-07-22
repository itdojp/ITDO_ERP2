"""
Sales models implementation for ERP system
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


class CustomerType(str, Enum):
    """Customer type enumeration"""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerStatus(str, Enum):
    """Customer status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    BLACKLISTED = "blacklisted"


class SalesOrderStatus(str, Enum):
    """Sales order status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    REFUNDED = "refunded"


class Customer(SoftDeletableModel):
    """Customer model for sales management"""

    __tablename__ = "customers"

    # Basic customer information
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_kana: Mapped[str | None] = mapped_column(String(200), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Organization relationship
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Customer type and status
    customer_type: Mapped[str] = mapped_column(String(20), default=CustomerType.INDIVIDUAL.value, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=CustomerStatus.ACTIVE.value, nullable=False)
    
    # Contact information
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fax: Mapped[str | None] = mapped_column(String(20), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Address information
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    prefecture: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Business information (for corporate customers)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)  # small, medium, large
    annual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Contact person (for corporate customers)
    contact_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Financial information
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Net 30, COD, etc.
    discount_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # Percentage
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="JPY")
    
    # Relationship dates
    first_purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    
    # Customer metrics
    total_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    average_order_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    
    # Preferences and notes
    preferred_language: Mapped[str | None] = mapped_column(String(10), nullable=True, default="ja")
    preferred_communication: Mapped[str | None] = mapped_column(String(50), nullable=True)  # email, phone, mail
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    newsletter_subscription: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    sales_orders: Mapped[list["SalesOrder"]] = relationship("SalesOrder", back_populates="customer")
    
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
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        return " ".join(parts) if parts else ""
    
    @property
    def is_corporate(self) -> bool:
        """Check if customer is corporate"""
        return self.customer_type == CustomerType.CORPORATE.value
    
    @property
    def display_name(self) -> str:
        """Get display name with contact person if corporate"""
        if self.is_corporate and self.contact_person:
            return f"{self.name} ({self.contact_person})"
        return self.name
    
    def get_credit_available(self) -> Decimal:
        """Get available credit (requires integration with accounting)"""
        if not self.credit_limit:
            return Decimal(0)
        # This would require integration with accounting to get current balance
        # For now, return credit limit as placeholder
        return self.credit_limit
    
    def update_metrics(self, order_amount: Decimal):
        """Update customer metrics after a new order"""
        self.total_orders += 1
        self.total_spent += order_amount
        self.average_order_value = self.total_spent / self.total_orders
        self.last_purchase_date = date.today()
        
        if not self.first_purchase_date:
            self.first_purchase_date = date.today()
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, code='{self.code}', name='{self.name}')>"


class SalesOrder(SoftDeletableModel):
    """Sales order model"""

    __tablename__ = "sales_orders"

    # Order identification
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Relationships
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    sales_rep_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Order details
    status: Mapped[str] = mapped_column(String(20), default=SalesOrderStatus.DRAFT.value, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING.value, nullable=False)
    
    # Important dates
    order_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    required_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    shipped_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivered_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Financial information
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="JPY")
    
    # Shipping information
    shipping_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Additional information
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    terms_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status flags
    is_rush_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dropship: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    customer: Mapped[Customer] = relationship("Customer", back_populates="sales_orders")
    sales_rep: Mapped["User | None"] = relationship("User")
    order_items: Mapped[list["SalesOrderItem"]] = relationship("SalesOrderItem", back_populates="sales_order")
    
    @property
    def is_overdue(self) -> bool:
        """Check if order is overdue"""
        if not self.required_date:
            return False
        return date.today() > self.required_date and self.status not in [
            SalesOrderStatus.DELIVERED.value,
            SalesOrderStatus.CANCELLED.value,
            SalesOrderStatus.REFUNDED.value
        ]
    
    @property
    def days_until_due(self) -> int | None:
        """Get days until order is due"""
        if not self.required_date:
            return None
        delta = self.required_date - date.today()
        return delta.days
    
    def calculate_totals(self):
        """Calculate order totals from line items"""
        self.subtotal = sum(item.line_total for item in self.order_items)
        # Tax calculation would be more complex in real scenario
        self.tax_amount = self.subtotal * Decimal('0.1')  # Assuming 10% tax
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount + self.shipping_cost
    
    def can_be_shipped(self) -> bool:
        """Check if order can be shipped"""
        return (
            self.status == SalesOrderStatus.CONFIRMED.value and
            self.payment_status in [PaymentStatus.PAID.value, PaymentStatus.PARTIAL.value]
        )
    
    def __str__(self) -> str:
        return f"{self.order_number} - {self.customer.name if self.customer else 'Unknown'}"
    
    def __repr__(self) -> str:
        return f"<SalesOrder(id={self.id}, number='{self.order_number}', status='{self.status}')>"


class SalesOrderItem(SoftDeletableModel):
    """Sales order line items"""

    __tablename__ = "sales_order_items"

    # Relationships
    sales_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Item details
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Product details (snapshot at time of order)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Fulfillment information
    quantity_shipped: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    quantity_returned: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    
    # Additional information
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    sales_order: Mapped[SalesOrder] = relationship("SalesOrder", back_populates="order_items")
    product: Mapped["Product"] = relationship("Product")
    organization: Mapped["Organization"] = relationship("Organization")
    
    @property
    def quantity_pending(self) -> Decimal:
        """Get quantity pending shipment"""
        return self.quantity - self.quantity_shipped
    
    @property
    def is_fully_shipped(self) -> bool:
        """Check if item is fully shipped"""
        return self.quantity_shipped >= self.quantity
    
    @property
    def discount_applied(self) -> Decimal:
        """Get total discount applied"""
        return self.discount_amount or (self.unit_price * self.quantity * (self.discount_percentage / 100))
    
    def calculate_line_total(self):
        """Calculate line total with discounts"""
        gross_total = self.unit_price * self.quantity
        discount = self.discount_applied
        self.line_total = gross_total - discount
    
    def __str__(self) -> str:
        return f"{self.product_code} - {self.product_name} (Qty: {self.quantity})"
    
    def __repr__(self) -> str:
        return f"<SalesOrderItem(id={self.id}, product='{self.product_code}', qty={self.quantity})>"