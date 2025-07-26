"""
ITDO ERP Backend - Product Management API v66
Complete product management system with comprehensive features for ERP core functionality
Day 8: Product Management API Implementation
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import aioredis
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from pydantic import BaseModel, Field
from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.base import BaseTable

# ============================================================================
# Models and Schemas
# ============================================================================


class ProductStatus(str, Enum):
    """Product status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    PENDING = "pending"
    OUT_OF_STOCK = "out_of_stock"


class ProductType(str, Enum):
    """Product type enumeration"""

    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    BUNDLE = "bundle"
    VARIANT = "variant"


class PriceType(str, Enum):
    """Price type enumeration"""

    REGULAR = "regular"
    SALE = "sale"
    WHOLESALE = "wholesale"
    PROMOTIONAL = "promotional"
    MEMBER = "member"


class UnitType(str, Enum):
    """Unit type enumeration"""

    PIECE = "piece"
    KILOGRAM = "kilogram"
    GRAM = "gram"
    LITER = "liter"
    MILLILITER = "milliliter"
    METER = "meter"
    CENTIMETER = "centimeter"
    SQUARE_METER = "square_meter"
    CUBIC_METER = "cubic_meter"
    PACKAGE = "package"
    BOX = "box"
    DOZEN = "dozen"


# Database Models
class ProductCategory(BaseTable):
    """Product category model"""

    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(250), unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
    level = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    meta_title = Column(String(200))
    meta_description = Column(Text)
    image_url = Column(String(500))

    # Relationships
    parent = relationship(
        "ProductCategory", remote_side=[id], back_populates="children"
    )
    children = relationship("ProductCategory", back_populates="parent")
    products = relationship("Product", back_populates="category")

    __table_args__ = (
        Index("idx_category_slug", "slug"),
        Index("idx_category_parent", "parent_id"),
        Index("idx_category_active", "is_active"),
    )


class ProductAttribute(BaseTable):
    """Product attribute model"""

    __tablename__ = "product_attributes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, nullable=False)
    attribute_type = Column(
        String(50), nullable=False
    )  # text, number, boolean, select, multiselect
    is_required = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_filterable = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    validation_rules = Column(JSON)
    default_value = Column(Text)

    # Relationships
    attribute_values = relationship("ProductAttributeValue", back_populates="attribute")
    product_attributes = relationship(
        "ProductAttributeMapping", back_populates="attribute"
    )

    __table_args__ = (
        Index("idx_attribute_slug", "slug"),
        Index("idx_attribute_type", "attribute_type"),
    )


class ProductAttributeValue(BaseTable):
    """Product attribute value model"""

    __tablename__ = "product_attribute_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribute_id = Column(
        UUID(as_uuid=True), ForeignKey("product_attributes.id"), nullable=False
    )
    value = Column(String(500), nullable=False)
    display_value = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationships
    attribute = relationship("ProductAttribute", back_populates="attribute_values")

    __table_args__ = (
        Index("idx_attr_value_attribute", "attribute_id"),
        UniqueConstraint("attribute_id", "value", name="uq_attribute_value"),
    )


class Brand(BaseTable):
    """Brand model"""

    __tablename__ = "brands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    slug = Column(String(250), unique=True, nullable=False)
    description = Column(Text)
    logo_url = Column(String(500))
    website = Column(String(300))
    is_active = Column(Boolean, default=True)

    # Relationships
    products = relationship("Product", back_populates="brand")

    __table_args__ = (
        Index("idx_brand_slug", "slug"),
        Index("idx_brand_active", "is_active"),
    )


class Product(BaseTable):
    """Main product model"""

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False)
    name = Column(String(500), nullable=False)
    slug = Column(String(550), unique=True, nullable=False)
    short_description = Column(Text)
    description = Column(Text)

    # Product categorization
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    product_type = Column(String(50), default=ProductType.PHYSICAL)

    # Product specifications
    weight = Column(DECIMAL(10, 3))
    dimensions = Column(JSON)  # {"length": 10, "width": 5, "height": 3, "unit": "cm"}
    unit_type = Column(String(50), default=UnitType.PIECE)

    # Pricing
    base_price = Column(DECIMAL(15, 4), nullable=False)
    cost_price = Column(DECIMAL(15, 4))
    compare_at_price = Column(DECIMAL(15, 4))

    # Inventory
    track_inventory = Column(Boolean, default=True)
    inventory_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)

    # Status and visibility
    status = Column(String(50), default=ProductStatus.ACTIVE)
    is_visible = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # SEO
    meta_title = Column(String(200))
    meta_description = Column(Text)
    meta_keywords = Column(Text)

    # Additional data
    tags = Column(JSON)  # ["tag1", "tag2"]
    images = Column(JSON)  # [{"url": "...", "alt": "...", "sort_order": 1}]
    variants = Column(JSON)  # Variant configuration
    custom_fields = Column(JSON)  # Custom product fields

    # Timestamps
    published_at = Column(DateTime)

    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    prices = relationship("ProductPrice", back_populates="product")
    attributes = relationship("ProductAttributeMapping", back_populates="product")
    media_files = relationship("ProductMedia", back_populates="product")
    inventory_logs = relationship("ProductInventoryLog", back_populates="product")

    __table_args__ = (
        Index("idx_product_sku", "sku"),
        Index("idx_product_slug", "slug"),
        Index("idx_product_category", "category_id"),
        Index("idx_product_brand", "brand_id"),
        Index("idx_product_status", "status"),
        Index("idx_product_featured", "is_featured"),
        Index("idx_product_published", "published_at"),
        CheckConstraint("base_price >= 0", name="check_base_price_positive"),
        CheckConstraint("inventory_quantity >= 0", name="check_inventory_positive"),
    )


class ProductPrice(BaseTable):
    """Product pricing model with support for multiple price types"""

    __tablename__ = "product_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    price_type = Column(String(50), nullable=False)
    price = Column(DECIMAL(15, 4), nullable=False)
    currency = Column(String(3), default="USD")
    min_quantity = Column(Integer, default=1)
    max_quantity = Column(Integer)
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    product = relationship("Product", back_populates="prices")

    __table_args__ = (
        Index("idx_price_product", "product_id"),
        Index("idx_price_type", "price_type"),
        Index("idx_price_active", "is_active"),
        CheckConstraint("price >= 0", name="check_price_positive"),
        CheckConstraint("min_quantity > 0", name="check_min_quantity_positive"),
    )


class ProductAttributeMapping(BaseTable):
    """Product attribute mapping model"""

    __tablename__ = "product_attribute_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    attribute_id = Column(
        UUID(as_uuid=True), ForeignKey("product_attributes.id"), nullable=False
    )
    value = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)

    # Relationships
    product = relationship("Product", back_populates="attributes")
    attribute = relationship("ProductAttribute", back_populates="product_attributes")

    __table_args__ = (
        Index("idx_attr_mapping_product", "product_id"),
        Index("idx_attr_mapping_attribute", "attribute_id"),
        UniqueConstraint("product_id", "attribute_id", name="uq_product_attribute"),
    )


class ProductMedia(BaseTable):
    """Product media files model"""

    __tablename__ = "product_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    file_type = Column(String(50), nullable=False)  # image, video, document, 3d_model
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    alt_text = Column(String(500))
    title = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    dimensions = Column(JSON)  # {"width": 800, "height": 600}

    # Relationships
    product = relationship("Product", back_populates="media_files")

    __table_args__ = (
        Index("idx_media_product", "product_id"),
        Index("idx_media_type", "file_type"),
        Index("idx_media_primary", "is_primary"),
    )


class ProductInventoryLog(BaseTable):
    """Product inventory change log"""

    __tablename__ = "product_inventory_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    change_type = Column(
        String(50), nullable=False
    )  # adjustment, sale, purchase, return
    quantity_before = Column(Integer, nullable=False)
    quantity_change = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reason = Column(String(500))
    reference_id = Column(String(100))  # Order ID, PO ID, etc.
    user_id = Column(UUID(as_uuid=True))

    # Relationships
    product = relationship("Product", back_populates="inventory_logs")

    __table_args__ = (
        Index("idx_inventory_log_product", "product_id"),
        Index("idx_inventory_log_type", "change_type"),
        Index("idx_inventory_log_date", "created_at"),
    )


# ============================================================================
# Pydantic Schemas
# ============================================================================


class ProductCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    sort_order: int = 0
    is_active: bool = True
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)


class ProductCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    parent_id: Optional[uuid.UUID]
    level: int
    sort_order: int
    is_active: bool
    meta_title: Optional[str]
    meta_description: Optional[str]
    image_url: Optional[str]
    children_count: int = 0
    products_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=300)
    is_active: bool = True


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None


class BrandResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str]
    logo_url: Optional[str]
    website: Optional[str]
    is_active: bool
    products_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductAttributeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: Optional[str] = None
    attribute_type: str = Field(..., regex="^(text|number|boolean|select|multiselect)$")
    is_required: bool = False
    is_searchable: bool = True
    is_filterable: bool = True
    sort_order: int = 0
    validation_rules: Optional[Dict[str, Any]] = None
    default_value: Optional[str] = None


class ProductAttributeValueCreate(BaseModel):
    value: str = Field(..., min_length=1, max_length=500)
    display_value: Optional[str] = Field(None, max_length=500)
    sort_order: int = 0
    is_active: bool = True


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=500)
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    product_type: ProductType = ProductType.PHYSICAL
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Any]] = None
    unit_type: UnitType = UnitType.PIECE
    base_price: Decimal = Field(..., ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    compare_at_price: Optional[Decimal] = Field(None, ge=0)
    track_inventory: bool = True
    inventory_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    status: ProductStatus = ProductStatus.ACTIVE
    is_visible: bool = True
    is_featured: bool = False
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    short_description: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    product_type: Optional[ProductType] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Any]] = None
    unit_type: Optional[UnitType] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    compare_at_price: Optional[Decimal] = Field(None, ge=0)
    track_inventory: Optional[bool] = None
    inventory_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    status: Optional[ProductStatus] = None
    is_visible: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    slug: str
    short_description: Optional[str]
    description: Optional[str]
    category_id: Optional[uuid.UUID]
    brand_id: Optional[uuid.UUID]
    product_type: str
    weight: Optional[Decimal]
    dimensions: Optional[Dict[str, Any]]
    unit_type: str
    base_price: Decimal
    cost_price: Optional[Decimal]
    compare_at_price: Optional[Decimal]
    track_inventory: bool
    inventory_quantity: int
    low_stock_threshold: int
    status: str
    is_visible: bool
    is_featured: bool
    meta_title: Optional[str]
    meta_description: Optional[str]
    meta_keywords: Optional[str]
    tags: Optional[List[str]]
    images: Optional[List[Dict[str, Any]]]
    custom_fields: Optional[Dict[str, Any]]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Related data
    category: Optional[ProductCategoryResponse] = None
    brand: Optional[BrandResponse] = None

    class Config:
        from_attributes = True


class ProductSearchFilter(BaseModel):
    query: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    status: Optional[ProductStatus] = None
    product_type: Optional[ProductType] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    is_visible: Optional[bool] = None
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, str]] = None


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Service Classes
# ============================================================================


class ProductManagementService:
    """Product management service with comprehensive functionality"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client
        self.settings = get_settings()

    async def create_slug(
        self, name: str, model_class: Any, existing_id: Optional[uuid.UUID] = None
    ) -> str:
        """Generate unique slug from name"""
        base_slug = name.lower().replace(" ", "-").replace("_", "-")
        # Remove special characters
        import re

        base_slug = re.sub(r"[^a-z0-9-]", "", base_slug)
        base_slug = re.sub(r"-+", "-", base_slug).strip("-")

        # Check for uniqueness
        counter = 0
        slug = base_slug

        while True:
            query = select(model_class).where(model_class.slug == slug)
            if existing_id:
                query = query.where(model_class.id != existing_id)

            result = await self.db.execute(query)
            if not result.scalar_one_or_none():
                break

            counter += 1
            slug = f"{base_slug}-{counter}"

        return slug

    # Category Management
    async def create_category(
        self, category_data: ProductCategoryCreate
    ) -> ProductCategory:
        """Create new product category"""
        if not category_data.slug:
            category_data.slug = await self.create_slug(
                category_data.name, ProductCategory
            )

        # Calculate level if parent exists
        level = 0
        if category_data.parent_id:
            parent_query = select(ProductCategory).where(
                ProductCategory.id == category_data.parent_id
            )
            parent_result = await self.db.execute(parent_query)
            parent = parent_result.scalar_one_or_none()
            if parent:
                level = parent.level + 1

        category = ProductCategory(
            **category_data.dict(exclude={"slug"}), slug=category_data.slug, level=level
        )

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        # Clear cache
        await self.redis.delete("categories:*")

        return category

    async def get_categories(
        self,
        parent_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """Get product categories with pagination"""
        cache_key = f"categories:{parent_id}:{is_active}:{page}:{size}"
        cached = await self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        query = select(ProductCategory)

        if parent_id is not None:
            query = query.where(ProductCategory.parent_id == parent_id)
        if is_active is not None:
            query = query.where(ProductCategory.is_active == is_active)

        # Count total
        count_query = select(func.count(ProductCategory.id))
        if parent_id is not None:
            count_query = count_query.where(ProductCategory.parent_id == parent_id)
        if is_active is not None:
            count_query = count_query.where(ProductCategory.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get categories
        query = query.order_by(ProductCategory.sort_order, ProductCategory.name)
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        categories = result.scalars().all()

        # Add counts for children and products
        category_responses = []
        for category in categories:
            # Count children
            children_query = select(func.count(ProductCategory.id)).where(
                ProductCategory.parent_id == category.id
            )
            children_result = await self.db.execute(children_query)
            children_count = children_result.scalar()

            # Count products
            products_query = select(func.count(Product.id)).where(
                Product.category_id == category.id
            )
            products_result = await self.db.execute(products_query)
            products_count = products_result.scalar()

            category_dict = {
                **category.__dict__,
                "children_count": children_count,
                "products_count": products_count,
            }
            category_responses.append(category_dict)

        result_data = {
            "categories": category_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

        # Cache for 10 minutes
        await self.redis.setex(cache_key, 600, json.dumps(result_data, default=str))

        return result_data

    # Brand Management
    async def create_brand(self, brand_data: BrandCreate) -> Brand:
        """Create new brand"""
        if not brand_data.slug:
            brand_data.slug = await self.create_slug(brand_data.name, Brand)

        brand = Brand(**brand_data.dict(exclude={"slug"}), slug=brand_data.slug)

        self.db.add(brand)
        await self.db.commit()
        await self.db.refresh(brand)

        # Clear cache
        await self.redis.delete("brands:*")

        return brand

    async def get_brands(
        self, is_active: Optional[bool] = None, page: int = 1, size: int = 50
    ) -> Dict[str, Any]:
        """Get brands with pagination"""
        cache_key = f"brands:{is_active}:{page}:{size}"
        cached = await self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        query = select(Brand)

        if is_active is not None:
            query = query.where(Brand.is_active == is_active)

        # Count total
        count_query = select(func.count(Brand.id))
        if is_active is not None:
            count_query = count_query.where(Brand.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get brands
        query = query.order_by(Brand.name)
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        brands = result.scalars().all()

        # Add product counts
        brand_responses = []
        for brand in brands:
            products_query = select(func.count(Product.id)).where(
                Product.brand_id == brand.id
            )
            products_result = await self.db.execute(products_query)
            products_count = products_result.scalar()

            brand_dict = {**brand.__dict__, "products_count": products_count}
            brand_responses.append(brand_dict)

        result_data = {
            "brands": brand_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

        # Cache for 15 minutes
        await self.redis.setex(cache_key, 900, json.dumps(result_data, default=str))

        return result_data

    # Product Management
    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create new product"""
        # Check SKU uniqueness
        sku_query = select(Product).where(Product.sku == product_data.sku)
        sku_result = await self.db.execute(sku_query)
        if sku_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="SKU already exists")

        if not product_data.slug:
            product_data.slug = await self.create_slug(product_data.name, Product)

        # Validate category and brand exist
        if product_data.category_id:
            cat_query = select(ProductCategory).where(
                ProductCategory.id == product_data.category_id
            )
            cat_result = await self.db.execute(cat_query)
            if not cat_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Category not found")

        if product_data.brand_id:
            brand_query = select(Brand).where(Brand.id == product_data.brand_id)
            brand_result = await self.db.execute(brand_query)
            if not brand_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Brand not found")

        product = Product(
            **product_data.dict(exclude={"slug"}),
            slug=product_data.slug,
            published_at=datetime.utcnow()
            if product_data.status == ProductStatus.ACTIVE
            else None,
        )

        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)

        # Log initial inventory if tracking
        if product.track_inventory and product.inventory_quantity > 0:
            inventory_log = ProductInventoryLog(
                product_id=product.id,
                change_type="initial",
                quantity_before=0,
                quantity_change=product.inventory_quantity,
                quantity_after=product.inventory_quantity,
                reason="Initial inventory setup",
            )
            self.db.add(inventory_log)
            await self.db.commit()

        # Clear cache
        await self.redis.delete("products:*")

        return product

    async def search_products(
        self,
        filters: ProductSearchFilter,
        page: int = 1,
        size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """Advanced product search with filters"""
        # Build cache key
        filters_str = filters.json() if filters else ""
        cache_key = f"products:search:{hashlib.md5(filters_str.encode()).hexdigest()}:{page}:{size}:{sort_by}:{sort_order}"

        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Build query
        query = select(Product).options(
            selectinload(Product.category), selectinload(Product.brand)
        )

        count_query = select(func.count(Product.id))

        # Apply filters
        if filters:
            if filters.query:
                search_filter = f"%{filters.query}%"
                search_condition = or_(
                    Product.name.ilike(search_filter),
                    Product.sku.ilike(search_filter),
                    Product.description.ilike(search_filter),
                )
                query = query.where(search_condition)
                count_query = count_query.where(search_condition)

            if filters.category_id:
                query = query.where(Product.category_id == filters.category_id)
                count_query = count_query.where(
                    Product.category_id == filters.category_id
                )

            if filters.brand_id:
                query = query.where(Product.brand_id == filters.brand_id)
                count_query = count_query.where(Product.brand_id == filters.brand_id)

            if filters.status:
                query = query.where(Product.status == filters.status)
                count_query = count_query.where(Product.status == filters.status)

            if filters.product_type:
                query = query.where(Product.product_type == filters.product_type)
                count_query = count_query.where(
                    Product.product_type == filters.product_type
                )

            if filters.min_price is not None:
                query = query.where(Product.base_price >= filters.min_price)
                count_query = count_query.where(Product.base_price >= filters.min_price)

            if filters.max_price is not None:
                query = query.where(Product.base_price <= filters.max_price)
                count_query = count_query.where(Product.base_price <= filters.max_price)

            if filters.is_featured is not None:
                query = query.where(Product.is_featured == filters.is_featured)
                count_query = count_query.where(
                    Product.is_featured == filters.is_featured
                )

            if filters.is_visible is not None:
                query = query.where(Product.is_visible == filters.is_visible)
                count_query = count_query.where(
                    Product.is_visible == filters.is_visible
                )

            if filters.tags:
                for tag in filters.tags:
                    query = query.where(Product.tags.contains([tag]))
                    count_query = count_query.where(Product.tags.contains([tag]))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        products = result.scalars().all()

        # Convert to response format
        product_responses = []
        for product in products:
            product_dict = product.__dict__.copy()

            # Add related data
            if product.category:
                product_dict["category"] = product.category.__dict__
            if product.brand:
                product_dict["brand"] = product.brand.__dict__

            product_responses.append(product_dict)

        result_data = {
            "products": product_responses,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

        # Cache for 5 minutes
        await self.redis.setex(cache_key, 300, json.dumps(result_data, default=str))

        return result_data

    async def get_product_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        """Get product by ID with related data"""
        cache_key = f"product:{product_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            product_data = json.loads(cached)
            # Reconstruct Product object (simplified)
            return product_data

        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.prices),
                selectinload(Product.attributes).selectinload(
                    ProductAttributeMapping.attribute
                ),
            )
            .where(Product.id == product_id)
        )

        result = await self.db.execute(query)
        product = result.scalar_one_or_none()

        if product:
            # Cache for 10 minutes
            await self.redis.setex(
                cache_key, 600, json.dumps(product.__dict__, default=str)
            )

        return product

    async def update_inventory(
        self,
        product_id: uuid.UUID,
        quantity_change: int,
        change_type: str,
        reason: Optional[str] = None,
        reference_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """Update product inventory with logging"""
        # Get current product
        product_query = select(Product).where(Product.id == product_id)
        product_result = await self.db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if not product.track_inventory:
            raise HTTPException(
                status_code=400, detail="Product does not track inventory"
            )

        # Calculate new quantity
        old_quantity = product.inventory_quantity
        new_quantity = old_quantity + quantity_change

        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Insufficient inventory")

        # Update product inventory
        product.inventory_quantity = new_quantity

        # Log the change
        inventory_log = ProductInventoryLog(
            product_id=product_id,
            change_type=change_type,
            quantity_before=old_quantity,
            quantity_change=quantity_change,
            quantity_after=new_quantity,
            reason=reason,
            reference_id=reference_id,
            user_id=user_id,
        )

        self.db.add(inventory_log)
        await self.db.commit()

        # Clear cache
        await self.redis.delete(f"product:{product_id}")
        await self.redis.delete("products:*")

        return {
            "product_id": product_id,
            "old_quantity": old_quantity,
            "quantity_change": quantity_change,
            "new_quantity": new_quantity,
            "low_stock_alert": new_quantity <= product.low_stock_threshold,
        }


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/products", tags=["Product Management v66"])


@router.post("/categories", response_model=ProductCategoryResponse)
async def create_category(
    category_data: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create new product category"""
    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    category = await service.create_category(category_data)
    return category


@router.get("/categories", response_model=Dict[str, Any])
async def get_categories(
    parent_id: Optional[uuid.UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get product categories with pagination"""
    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    return await service.get_categories(parent_id, is_active, page, size)


@router.post("/brands", response_model=BrandResponse)
async def create_brand(
    brand_data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create new brand"""
    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    brand = await service.create_brand(brand_data)
    return brand


@router.get("/brands", response_model=Dict[str, Any])
async def get_brands(
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get brands with pagination"""
    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    return await service.get_brands(is_active, page, size)


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create new product"""
    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    product = await service.create_product(product_data)
    return product


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    query: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    brand_id: Optional[uuid.UUID] = Query(None),
    status: Optional[ProductStatus] = Query(None),
    product_type: Optional[ProductType] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    is_featured: Optional[bool] = Query(None),
    is_visible: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Advanced product search with filters"""
    filters = ProductSearchFilter(
        query=query,
        category_id=category_id,
        brand_id=brand_id,
        status=status,
        product_type=product_type,
        min_price=min_price,
        max_price=max_price,
        is_featured=is_featured,
        is_visible=is_visible,
    )

    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    return await service.search_products(filters, page, size, sort_by, sort_order)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get product by ID"""
    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    product = await service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/{product_id}/inventory", response_model=Dict[str, Any])
async def update_product_inventory(
    product_id: uuid.UUID,
    quantity_change: int,
    change_type: str = "adjustment",
    reason: Optional[str] = None,
    reference_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update product inventory"""
    service = ProductManagementService(
        db, await aioredis.from_url("redis://localhost:6379")
    )
    return await service.update_inventory(
        product_id=product_id,
        quantity_change=quantity_change,
        change_type=change_type,
        reason=reason,
        reference_id=reference_id,
        user_id=current_user.get("id") if current_user else None,
    )


# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Product management service health check"""
    return {
        "status": "healthy",
        "service": "product_management_v66",
        "version": "66.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "product_catalog",
            "category_management",
            "brand_management",
            "inventory_tracking",
            "advanced_search",
            "pricing_management",
            "attribute_system",
        ],
    }
