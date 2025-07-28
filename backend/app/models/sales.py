"""
Sales models for ERP v17.0
Basic sales order management with customers, orders, and billing
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
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


class CustomerStatus(str, Enum):
    """Customer status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class CustomerType(str, Enum):
    """Customer type enumeration."""

    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class OrderStatus(str, Enum):
    """Sales order status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""

    CASH = "cash"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTO = "crypto"


class Customer(SoftDeletableModel):
    """Customer model for sales management."""

    __tablename__ = "customers"

    # Basic identification
    customer_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(300))
    customer_type: Mapped[str] = mapped_column(
        String(20), default=CustomerType.CORPORATE.value
    )

    # Organization
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )

    # Contact information
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    mobile: Mapped[str | None] = mapped_column(String(20))
    fax: Mapped[str | None] = mapped_column(String(20))
    website: Mapped[str | None] = mapped_column(String(255))

    # Address information
    billing_address: Mapped[str | None] = mapped_column(String(500))
    billing_postal_code: Mapped[str | None] = mapped_column(String(10))
    billing_city: Mapped[str | None] = mapped_column(String(100))
    billing_prefecture: Mapped[str | None] = mapped_column(String(50))
    billing_country: Mapped[str] = mapped_column(String(50), default="Japan")

    shipping_address: Mapped[str | None] = mapped_column(String(500))
    shipping_postal_code: Mapped[str | None] = mapped_column(String(10))
    shipping_city: Mapped[str | None] = mapped_column(String(100))
    shipping_prefecture: Mapped[str | None] = mapped_column(String(50))
    shipping_country: Mapped[str] = mapped_column(String(50), default="Japan")

    # Business details
    tax_registration_number: Mapped[str | None] = mapped_column(String(50))  # 法人番号
    business_registration_number: Mapped[str | None] = mapped_column(String(50))
    industry: Mapped[str | None] = mapped_column(String(100))

    # Credit management
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    payment_terms: Mapped[int] = mapped_column(Integer, default=30)  # days

    # Status and preferences
    status: Mapped[str] = mapped_column(String(20), default=CustomerStatus.ACTIVE.value)
    preferred_payment_method: Mapped[str | None] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), default="JPY")

    # Sales information
    first_order_date: Mapped[date | None] = mapped_column(Date)
    last_order_date: Mapped[date | None] = mapped_column(Date)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_sales_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Contact person information
    contact_person_name: Mapped[str | None] = mapped_column(String(100))
    contact_person_title: Mapped[str | None] = mapped_column(String(100))
    contact_person_email: Mapped[str | None] = mapped_column(String(255))
    contact_person_phone: Mapped[str | None] = mapped_column(String(20))

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    sales_orders: Mapped[list["SalesOrder"]] = relationship(
        "SalesOrder", back_populates="customer"
    )

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        if self.name_en:
            return f"{self.name} ({self.name_en})"
        return self.name

    @property
    def full_billing_address(self) -> str:
        """Get full formatted billing address."""
        parts = []
        if self.billing_postal_code:
            parts.append(f"〒{self.billing_postal_code}")
        if self.billing_prefecture:
            parts.append(self.billing_prefecture)
        if self.billing_city:
            parts.append(self.billing_city)
        if self.billing_address:
            parts.append(self.billing_address)
        return " ".join(parts) if parts else ""

    @property
    def full_shipping_address(self) -> str:
        """Get full formatted shipping address."""
        parts = []
        if self.shipping_postal_code:
            parts.append(f"〒{self.shipping_postal_code}")
        if self.shipping_prefecture:
            parts.append(self.shipping_prefecture)
        if self.shipping_city:
            parts.append(self.shipping_city)
        if self.shipping_address:
            parts.append(self.shipping_address)
        return " ".join(parts) if parts else ""

    @property
    def credit_available(self) -> Decimal:
        """Calculate available credit."""
        if self.credit_limit:
            return max(Decimal(0), self.credit_limit - self.current_balance)
        return Decimal(0)

    @property
    def is_over_credit_limit(self) -> bool:
        """Check if customer is over credit limit."""
        if self.credit_limit:
            return self.current_balance > self.credit_limit
        return False

    def update_sales_statistics(self, db) -> None:
        """Update sales statistics based on orders."""
        from sqlalchemy import func

        # Get order statistics
        stats = (
            db.query(
                func.count(SalesOrder.id).label("total_orders"),
                func.sum(SalesOrder.total_amount).label("total_sales"),
                func.min(SalesOrder.order_date).label("first_order"),
                func.max(SalesOrder.order_date).label("last_order"),
            )
            .filter(
                SalesOrder.customer_id == self.id,
                SalesOrder.deleted_at.is_(None),
                SalesOrder.status != OrderStatus.CANCELLED.value,
            )
            .first()
        )

        if stats:
            self.total_orders = stats.total_orders or 0
            self.total_sales_amount = stats.total_sales or Decimal(0)
            self.first_order_date = stats.first_order
            self.last_order_date = stats.last_order

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, number='{self.customer_number}', name='{self.name}')>"


class SalesOrder(SoftDeletableModel):
    """Sales order model."""

    __tablename__ = "sales_orders"

    # Order identification
    order_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )

    # Customer and organization
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )

    # Order details
    order_date: Mapped[date] = mapped_column(Date, default=lambda: date.today())
    required_date: Mapped[date | None] = mapped_column(Date)
    shipped_date: Mapped[date | None] = mapped_column(Date)
    delivery_date: Mapped[date | None] = mapped_column(Date)

    # Status
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.DRAFT.value)

    # Financial information
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)

    # Payment information
    payment_status: Mapped[str] = mapped_column(
        String(20), default=PaymentStatus.PENDING.value
    )
    payment_method: Mapped[str | None] = mapped_column(String(20))
    payment_terms: Mapped[int] = mapped_column(Integer, default=30)  # days
    payment_due_date: Mapped[date | None] = mapped_column(Date)

    # Shipping information
    shipping_address: Mapped[str | None] = mapped_column(String(500))
    shipping_postal_code: Mapped[str | None] = mapped_column(String(10))
    shipping_city: Mapped[str | None] = mapped_column(String(100))
    shipping_prefecture: Mapped[str | None] = mapped_column(String(50))
    shipping_country: Mapped[str] = mapped_column(String(50), default="Japan")
    shipping_method: Mapped[str | None] = mapped_column(String(100))
    tracking_number: Mapped[str | None] = mapped_column(String(100))

    # Reference information
    customer_po_number: Mapped[str | None] = mapped_column(String(100))
    sales_rep_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="JPY")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=1.0)

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="sales_orders"
    )
    organization: Mapped["Organization"] = relationship("Organization")
    sales_rep: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[sales_rep_id]
    )
    order_items: Mapped[list["SalesOrderItem"]] = relationship(
        "SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan"
    )

    @property
    def full_shipping_address(self) -> str:
        """Get full formatted shipping address."""
        parts = []
        if self.shipping_postal_code:
            parts.append(f"〒{self.shipping_postal_code}")
        if self.shipping_prefecture:
            parts.append(self.shipping_prefecture)
        if self.shipping_city:
            parts.append(self.shipping_city)
        if self.shipping_address:
            parts.append(self.shipping_address)
        return " ".join(parts) if parts else ""

    @property
    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        if self.payment_due_date and self.payment_status not in [
            PaymentStatus.PAID.value,
            PaymentStatus.CANCELLED.value,
        ]:
            return date.today() > self.payment_due_date
        return False

    @property
    def days_until_due(self) -> int | None:
        """Get days until payment due."""
        if self.payment_due_date:
            delta = self.payment_due_date - date.today()
            return delta.days
        return None

    def calculate_totals(self) -> None:
        """Calculate order totals from line items."""
        subtotal = Decimal(0)

        for item in self.order_items:
            subtotal += item.total_amount

        self.subtotal_amount = subtotal

        # Calculate tax (assuming tax is included in item totals)
        # This could be customized based on business rules
        self.tax_amount = subtotal * Decimal("0.1")  # 10% tax

        # Calculate total
        self.total_amount = (
            self.subtotal_amount
            + self.tax_amount
            + self.shipping_amount
            - self.discount_amount
        )

    def set_payment_due_date(self) -> None:
        """Set payment due date based on payment terms."""
        if self.order_date and self.payment_terms:
            from datetime import timedelta

            self.payment_due_date = self.order_date + timedelta(days=self.payment_terms)

    def __repr__(self) -> str:
        return f"<SalesOrder(id={self.id}, number='{self.order_number}', customer_id={self.customer_id})>"


class SalesOrderItem(SoftDeletableModel):
    """Sales order item (line item)."""

    __tablename__ = "sales_order_items"

    # Order and product reference
    sales_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales_orders.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )

    # Line item details
    line_number: Mapped[int] = mapped_column(Integer, default=1)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Discount information
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Product information (snapshot at time of order)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name: Mapped[str] = mapped_column(String(300), nullable=False)
    product_description: Mapped[str | None] = mapped_column(Text)

    # Tax information
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.1000"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Delivery information
    requested_delivery_date: Mapped[date | None] = mapped_column(Date)
    confirmed_delivery_date: Mapped[date | None] = mapped_column(Date)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship(
        "SalesOrder", back_populates="order_items"
    )
    product: Mapped["Product"] = relationship("Product")
    organization: Mapped["Organization"] = relationship("Organization")

    def calculate_total_amount(self) -> None:
        """Calculate total amount including discounts and tax."""
        # Base amount
        base_amount = self.quantity * self.unit_price

        # Apply discount
        if self.discount_percent > 0:
            self.discount_amount = base_amount * (self.discount_percent / 100)

        # Amount after discount
        discounted_amount = base_amount - self.discount_amount

        # Calculate tax
        self.tax_amount = discounted_amount * self.tax_rate

        # Total amount
        self.total_amount = discounted_amount + self.tax_amount

    def update_product_snapshot(self, product) -> None:
        """Update product information snapshot."""
        self.product_code = product.code
        self.product_name = product.name
        self.product_description = product.description

    def __repr__(self) -> str:
        return f"<SalesOrderItem(id={self.id}, order_id={self.sales_order_id}, product_id={self.product_id})>"
