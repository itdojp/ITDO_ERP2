"""
Product model for ERP v17.0
Basic product management with categories, pricing, and inventory integration
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.organization import Organization


class ProductStatus(str, Enum):
    """Product status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class ProductType(str, Enum):
    """Product type enumeration."""

    PRODUCT = "product"  # Physical product
    SERVICE = "service"  # Service
    DIGITAL = "digital"  # Digital product
    SUBSCRIPTION = "subscription"  # Subscription service


class ProductCategory(SoftDeletableModel):
    """Product category for organizing products."""

    __tablename__ = "product_categories"

    # Basic fields
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    # Hierarchy
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("product_categories.id")
    )

    # Organization
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    parent: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory", remote_side="ProductCategory.id", back_populates="children"
    )
    children: Mapped[list["ProductCategory"]] = relationship(
        "ProductCategory", back_populates="parent"
    )
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="category"
    )
    organization: Mapped["Organization"] = relationship("Organization")

    def get_hierarchy_path(self) -> list["ProductCategory"]:
        """Get the full hierarchy path from root to this category."""
        path = [self]
        current = self
        while current.parent:
            path.insert(0, current.parent)
            current = current.parent
        return path

    def __repr__(self) -> str:
        return (
            f"<ProductCategory(id={self.id}, code='{self.code}', name='{self.name}')>"
        )


class Product(SoftDeletableModel):
    """Product model for ERP v17.0 - enhanced for basic functionality."""

    __tablename__ = "products"

    # Basic identification
    code: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)

    # Product details
    sku: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    product_type: Mapped[str] = mapped_column(
        String(20), default=ProductType.PRODUCT.value
    )
    status: Mapped[str] = mapped_column(String(20), default=ProductStatus.ACTIVE.value)

    # Categorization
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("product_categories.id")
    )
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )

    # Pricing
    standard_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    selling_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    minimum_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    # Physical properties
    unit: Mapped[str] = mapped_column(String(20), default="個")  # Unit of measure
    weight: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))  # kg
    length: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))  # cm
    width: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))  # cm
    height: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))  # cm

    # Stock management
    is_stock_managed: Mapped[bool] = mapped_column(Boolean, default=True)
    minimum_stock_level: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    reorder_point: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # Tax and accounting
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.1000")
    )  # 10%
    tax_included: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status and visibility
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sellable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_purchasable: Mapped[bool] = mapped_column(Boolean, default=True)

    # Additional info
    manufacturer: Mapped[str | None] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(200))
    model_number: Mapped[str | None] = mapped_column(String(100))
    warranty_period: Mapped[int | None] = mapped_column(Integer)  # months

    # Media
    image_url: Mapped[str | None] = mapped_column(String(500))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))

    # Notes
    notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Timestamps for business logic
    launch_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discontinued_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    category: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory", back_populates="products"
    )
    organization: Mapped["Organization"] = relationship("Organization")

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        if self.name_en:
            return f"{self.name} ({self.name_en})"
        return self.name

    @property
    def is_available(self) -> bool:
        """Check if product is available for sale."""
        return (
            self.is_active
            and self.is_sellable
            and self.status == ProductStatus.ACTIVE.value
        )

    @property
    def effective_selling_price(self) -> Decimal:
        """Get effective selling price."""
        if self.selling_price:
            return self.selling_price
        return self.standard_price

    @property
    def profit_margin(self) -> Decimal | None:
        """Calculate profit margin percentage."""
        if self.cost_price and self.cost_price > 0:
            selling = self.effective_selling_price
            return ((selling - self.cost_price) / self.cost_price) * 100
        return None

    def get_erp_context(self) -> dict:
        """Get ERP-specific product context - v17.0."""
        return {
            "product_id": self.id,
            "code": self.code,
            "name": self.name,
            "display_name": self.display_name,
            "sku": self.sku,
            "barcode": self.barcode,
            "product_type": self.product_type,
            "status": self.status,
            "is_available": self.is_available,
            "category_id": self.category_id,
            "organization_id": self.organization_id,
            "pricing": {
                "standard_price": float(self.standard_price),
                "selling_price": float(self.effective_selling_price),
                "cost_price": float(self.cost_price) if self.cost_price else None,
                "profit_margin": float(self.profit_margin)
                if self.profit_margin
                else None,
            },
            "stock_managed": self.is_stock_managed,
            "unit": self.unit,
            "tax_rate": float(self.tax_rate),
            "is_active": self.is_active,
        }

    def update_status(self, new_status: ProductStatus, updated_by: int, db) -> None:
        """Update product status with audit trail."""
        if new_status == ProductStatus.DISCONTINUED:
            self.discontinued_date = datetime.now(UTC)

        self.status = new_status.value
        self.updated_by = updated_by
        self.updated_at = datetime.now(UTC)

        db.add(self)
        db.flush()

    def can_be_deleted(self) -> tuple[bool, str]:
        """Check if product can be safely deleted."""
        # In real implementation, check for:
        # - Existing inventory
        # - Order history
        # - Purchase history
        # - etc.

        if self.status == ProductStatus.ACTIVE.value:
            return False, "Cannot delete active product"

        # Basic validation for now
        return True, "OK"

    def calculate_tax_amount(self, base_amount: Decimal) -> Decimal:
        """Calculate tax amount for given base amount."""
        if self.tax_included:
            # Tax is included in the price
            return base_amount - (base_amount / (1 + self.tax_rate))
        else:
            # Tax is added to the price
            return base_amount * self.tax_rate

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, code='{self.code}', name='{self.name}')>"


class ProductPriceHistory(SoftDeletableModel):
    """Product price history for tracking price changes - CC02 v49.0"""
    
    __tablename__ = "product_price_history"
    
    # References
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Price data
    old_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_type: Mapped[str] = mapped_column(String(50), default="standard_price")  # standard_price, selling_price, cost_price
    
    # Change metadata
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    changed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    change_reason: Mapped[str | None] = mapped_column(String(500))
    
    # Relationships
    product: Mapped["Product"] = relationship("Product")
    organization: Mapped["Organization"] = relationship("Organization")
    
    def __repr__(self) -> str:
        return f"<ProductPriceHistory(product_id={self.product_id}, old_price={self.old_price}, new_price={self.new_price})>"
