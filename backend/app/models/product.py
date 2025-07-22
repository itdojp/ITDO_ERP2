"""
Product model implementation for ERP system
"""

from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeletableModel

if TYPE_CHECKING:
    from app.models.product_category import ProductCategory
    from app.models.organization import Organization


class ProductStatus(str, Enum):
    """Product status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"


class ProductType(str, Enum):
    """Product type enumeration"""
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    BUNDLE = "bundle"


class Product(SoftDeletableModel):
    """Product model for ERP system with comprehensive product management"""

    __tablename__ = "products"

    # Basic product information
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_kana: Mapped[str | None] = mapped_column(String(200), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Organization relationship
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Category relationship
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("product_categories.id"), nullable=True)
    
    # Product specifications
    product_type: Mapped[str] = mapped_column(String(20), default=ProductType.PHYSICAL.value, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ProductStatus.ACTIVE.value, nullable=False)
    
    # SKU and identification
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    qr_code: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Pricing information
    base_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    discount_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="JPY")
    
    # Tax information
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # Percentage
    tax_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Physical attributes
    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)  # kg
    weight_unit: Mapped[str | None] = mapped_column(String(10), nullable=True, default="kg")
    length: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # cm
    width: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # cm
    height: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)  # cm
    dimension_unit: Mapped[str | None] = mapped_column(String(10), nullable=True, default="cm")
    
    # Inventory tracking
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    min_stock_level: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    max_stock_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reorder_point: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reorder_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Product lifecycle
    launch_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    discontinue_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Vendor and supplier information
    supplier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    supplier_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Quality and compliance
    quality_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)  # A, B, C, etc.
    compliance_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Media and documentation
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    manual_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    specification_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # SEO and online presence
    meta_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Internal tracking
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # Comma-separated tags
    
    # Business metrics
    popularity_score: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)  # 0.00-5.00
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    
    # Status flags
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_digital_download: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_subscription: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_shipping: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    category: Mapped["ProductCategory | None"] = relationship("ProductCategory", back_populates="products")
    
    @property
    def profit_margin(self) -> Decimal | None:
        """Calculate profit margin percentage"""
        if not self.cost_price or self.cost_price == 0:
            return None
        profit = self.selling_price - self.cost_price
        return (profit / self.cost_price) * 100
    
    @property
    def volume(self) -> Decimal | None:
        """Calculate volume in cubic cm"""
        if not all([self.length, self.width, self.height]):
            return None
        return self.length * self.width * self.height
    
    @property
    def is_low_stock(self) -> bool:
        """Check if product is low stock (requires inventory integration)"""
        # This would require inventory integration to check actual stock
        # For now, return False as placeholder
        return False
    
    @property
    def display_price(self) -> Decimal:
        """Get the price to display (discount price if available, otherwise selling price)"""
        return self.discount_price if self.discount_price else self.selling_price
    
    @property
    def price_with_tax(self) -> Decimal:
        """Calculate price including tax"""
        base_price = self.display_price
        if self.is_taxable and self.tax_rate:
            tax_amount = base_price * (self.tax_rate / 100)
            return base_price + tax_amount
        return base_price
    
    def is_discontinued(self) -> bool:
        """Check if product is discontinued"""
        return self.status == ProductStatus.DISCONTINUED.value
    
    def is_available(self) -> bool:
        """Check if product is available for sale"""
        return (
            self.is_active and 
            self.status == ProductStatus.ACTIVE.value and 
            not self.is_discontinued()
        )
    
    def get_dimension_string(self) -> str:
        """Get formatted dimension string"""
        if not all([self.length, self.width, self.height]):
            return ""
        unit = self.dimension_unit or "cm"
        return f"{self.length} x {self.width} x {self.height} {unit}"
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, code='{self.code}', name='{self.name}')>"


class ProductPriceHistory(SoftDeletableModel):
    """Track product price changes over time"""

    __tablename__ = "product_price_history"

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Price information
    old_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    price_type: Mapped[str] = mapped_column(String(20), nullable=False)  # base_price, selling_price, cost_price
    
    # Change information
    change_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    effective_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    product: Mapped[Product] = relationship("Product")
    organization: Mapped["Organization"] = relationship("Organization")
    
    def __repr__(self) -> str:
        return f"<ProductPriceHistory(product_id={self.product_id}, old={self.old_price}, new={self.new_price})>"