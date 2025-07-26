"""
CC02 v55.0 Products Management API
Enterprise-grade Product Management System
Day 1 of 7-day intensive backend development
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.product import (
    Product,
    ProductAttribute,
    ProductCategory,
    ProductImage,
    ProductVariant,
)
from app.models.user import User

router = APIRouter(prefix="/products", tags=["products-v55"])


# Enums
class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ProductType(str, Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    SUBSCRIPTION = "subscription"
    BUNDLE = "bundle"


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    BACKORDER = "backorder"
    PREORDER = "preorder"


# Request/Response Models
class ProductAttributeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=500)
    type: str = Field(default="text", max_length=50)
    unit: Optional[str] = Field(None, max_length=20)
    is_variant_attribute: bool = Field(default=False)


class ProductAttributeResponse(BaseModel):
    id: UUID
    name: str
    value: str
    type: str
    unit: Optional[str]
    is_variant_attribute: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductImageCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=1000)
    alt_text: Optional[str] = Field(None, max_length=200)
    is_primary: bool = Field(default=False)
    sort_order: int = Field(default=0, ge=0)


class ProductImageResponse(BaseModel):
    id: UUID
    url: str
    alt_text: Optional[str]
    is_primary: bool
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductVariantCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    compare_at_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cost_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, float]] = None
    inventory_quantity: int = Field(default=0, ge=0)
    inventory_policy: str = Field(default="deny", regex="^(deny|continue)$")
    requires_shipping: bool = Field(default=True)
    is_default: bool = Field(default=False)
    attributes: List[ProductAttributeCreate] = Field(default_factory=list)


class ProductVariantResponse(BaseModel):
    id: UUID
    sku: str
    name: Optional[str]
    price: Decimal
    compare_at_price: Optional[Decimal]
    cost_price: Optional[Decimal]
    weight: Optional[Decimal]
    dimensions: Optional[Dict[str, float]]
    inventory_quantity: int
    inventory_policy: str
    requires_shipping: bool
    is_default: bool
    stock_status: StockStatus
    attributes: List[ProductAttributeResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[UUID] = None
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = Field(None, max_length=300)
    image_url: Optional[str] = Field(None, max_length=1000)


class ProductCategoryResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    slug: str
    parent_id: Optional[UUID]
    sort_order: int
    is_active: bool
    seo_title: Optional[str]
    seo_description: Optional[str]
    image_url: Optional[str]
    product_count: int
    children_count: int
    path: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    short_description: Optional[str] = Field(None, max_length=500)
    product_type: ProductType = Field(default=ProductType.PHYSICAL)
    status: ProductStatus = Field(default=ProductStatus.DRAFT)
    category_id: Optional[UUID] = None
    brand: Optional[str] = Field(None, max_length=100)
    vendor: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = Field(None, max_length=300)
    published_at: Optional[datetime] = None
    is_featured: bool = Field(default=False)
    min_quantity: int = Field(default=1, ge=1)
    max_quantity: Optional[int] = Field(None, ge=1)
    is_taxable: bool = Field(default=True)
    tax_code: Optional[str] = Field(None, max_length=20)
    requires_shipping: bool = Field(default=True)
    track_inventory: bool = Field(default=True)
    variants: List[ProductVariantCreate] = Field(default_factory=list, min_items=1)
    images: List[ProductImageCreate] = Field(default_factory=list)
    attributes: List[ProductAttributeCreate] = Field(default_factory=list)

    @validator("max_quantity")
    def validate_max_quantity(cls, v, values) -> dict:
        if v is not None and "min_quantity" in values and v < values["min_quantity"]:
            raise ValueError(
                "max_quantity must be greater than or equal to min_quantity"
            )
        return v

    @validator("variants")
    def validate_variants(cls, v) -> dict:
        if not v:
            raise ValueError("At least one variant is required")

        # Check for duplicate SKUs
        skus = [variant.sku for variant in v]
        if len(skus) != len(set(skus)):
            raise ValueError("Duplicate SKUs in variants")

        # Ensure only one default variant
        default_count = sum(1 for variant in v if variant.is_default)
        if default_count > 1:
            raise ValueError("Only one variant can be marked as default")

        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    short_description: Optional[str] = Field(None, max_length=500)
    product_type: Optional[ProductType] = None
    status: Optional[ProductStatus] = None
    category_id: Optional[UUID] = None
    brand: Optional[str] = Field(None, max_length=100)
    vendor: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    seo_title: Optional[str] = Field(None, max_length=150)
    seo_description: Optional[str] = Field(None, max_length=300)
    published_at: Optional[datetime] = None
    is_featured: Optional[bool] = None
    min_quantity: Optional[int] = Field(None, ge=1)
    max_quantity: Optional[int] = Field(None, ge=1)
    is_taxable: Optional[bool] = None
    tax_code: Optional[str] = Field(None, max_length=20)
    requires_shipping: Optional[bool] = None
    track_inventory: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    short_description: Optional[str]
    product_type: ProductType
    status: ProductStatus
    category: Optional[ProductCategoryResponse]
    brand: Optional[str]
    vendor: Optional[str]
    tags: List[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    published_at: Optional[datetime]
    is_featured: bool
    min_quantity: int
    max_quantity: Optional[int]
    is_taxable: bool
    tax_code: Optional[str]
    requires_shipping: bool
    track_inventory: bool
    variants: List[ProductVariantResponse]
    images: List[ProductImageResponse]
    attributes: List[ProductAttributeResponse]
    total_inventory: int
    stock_status: StockStatus
    min_price: Decimal
    max_price: Decimal
    avg_rating: Optional[Decimal]
    review_count: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    id: UUID
    name: str
    short_description: Optional[str]
    product_type: ProductType
    status: ProductStatus
    category: Optional[str]
    brand: Optional[str]
    is_featured: bool
    total_inventory: int
    stock_status: StockStatus
    min_price: Decimal
    max_price: Decimal
    primary_image: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkProductOperation(BaseModel):
    product_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., regex="^(activate|deactivate|archive|delete)$")
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None


# Helper Functions
async def calculate_stock_status(
    inventory_quantity: int, min_stock: int = 10
) -> StockStatus:
    """Calculate stock status based on inventory quantity"""
    if inventory_quantity <= 0:
        return StockStatus.OUT_OF_STOCK
    elif inventory_quantity <= min_stock:
        return StockStatus.LOW_STOCK
    else:
        return StockStatus.IN_STOCK


async def validate_category_exists(db: AsyncSession, category_id: UUID) -> bool:
    """Validate that a category exists"""
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == category_id)
    )
    return result.scalar_one_or_none() is not None


async def generate_slug(name: str, db: AsyncSession, model_class) -> str:
    """Generate unique slug from name"""
    import re

    base_slug = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    base_slug = re.sub(r"\s+", "-", base_slug.strip())

    slug = base_slug
    counter = 1

    while True:
        result = await db.execute(select(model_class).where(model_class.slug == slug))
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


# Category Endpoints
@router.post(
    "/categories",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category: ProductCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new product category"""

    # Validate parent category exists if specified
    if category.parent_id:
        if not await validate_category_exists(db, category.parent_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )

    # Generate slug if not provided
    slug = category.slug or await generate_slug(category.name, db, ProductCategory)

    # Check slug uniqueness
    existing = await db.execute(
        select(ProductCategory).where(ProductCategory.slug == slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Category slug already exists"
        )

    # Create category
    db_category = ProductCategory(
        id=uuid4(),
        name=category.name,
        description=category.description,
        slug=slug,
        parent_id=category.parent_id,
        sort_order=category.sort_order,
        is_active=category.is_active,
        seo_title=category.seo_title,
        seo_description=category.seo_description,
        image_url=category.image_url,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)

    # Calculate additional fields
    db_category.product_count = 0
    db_category.children_count = 0
    db_category.path = []

    return db_category


@router.get("/categories", response_model=List[ProductCategoryResponse])
async def list_categories(
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    include_product_count: bool = Query(True, description="Include product counts"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of product categories"""

    query = select(ProductCategory)

    if parent_id is not None:
        query = query.where(ProductCategory.parent_id == parent_id)

    if is_active is not None:
        query = query.where(ProductCategory.is_active == is_active)

    query = query.order_by(ProductCategory.sort_order, ProductCategory.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    # Add computed fields
    for category in categories:
        if include_product_count:
            # Count products in this category
            count_result = await db.execute(
                select(func.count(Product.id)).where(Product.category_id == category.id)
            )
            category.product_count = count_result.scalar() or 0

            # Count child categories
            children_result = await db.execute(
                select(func.count(ProductCategory.id)).where(
                    ProductCategory.parent_id == category.id
                )
            )
            category.children_count = children_result.scalar() or 0
        else:
            category.product_count = 0
            category.children_count = 0

        # Build category path
        category.path = [category.name]

    return categories


@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
async def get_category(
    category_id: UUID = Path(..., description="Category ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific product category"""

    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Add computed fields
    count_result = await db.execute(
        select(func.count(Product.id)).where(Product.category_id == category.id)
    )
    category.product_count = count_result.scalar() or 0

    children_result = await db.execute(
        select(func.count(ProductCategory.id)).where(
            ProductCategory.parent_id == category.id
        )
    )
    category.children_count = children_result.scalar() or 0

    category.path = [category.name]

    return category


@router.put("/categories/{category_id}", response_model=ProductCategoryResponse)
async def update_category(
    category_id: UUID = Path(..., description="Category ID"),
    category_update: ProductCategoryCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a product category"""

    # Get existing category
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == category_id)
    )
    db_category = result.scalar_one_or_none()

    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Validate parent category if specified
    if category_update.parent_id and category_update.parent_id != category_id:
        if not await validate_category_exists(db, category_update.parent_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )

    # Update slug if name changed
    slug = category_update.slug
    if category_update.name != db_category.name and not slug:
        slug = await generate_slug(category_update.name, db, ProductCategory)
    elif slug and slug != db_category.slug:
        # Check slug uniqueness
        existing = await db.execute(
            select(ProductCategory).where(
                and_(ProductCategory.slug == slug, ProductCategory.id != category_id)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category slug already exists",
            )

    # Update fields
    for field, value in category_update.dict(exclude_unset=True).items():
        setattr(db_category, field, value)

    if slug:
        db_category.slug = slug

    db_category.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(db_category)

    # Add computed fields
    db_category.product_count = 0
    db_category.children_count = 0
    db_category.path = [db_category.name]

    return db_category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID = Path(..., description="Category ID"),
    force: bool = Query(False, description="Force delete even if products exist"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product category"""

    # Get category
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Check for child categories
    children_result = await db.execute(
        select(func.count(ProductCategory.id)).where(
            ProductCategory.parent_id == category_id
        )
    )
    children_count = children_result.scalar() or 0

    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete category with child categories",
        )

    # Check for products unless force delete
    if not force:
        products_result = await db.execute(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        )
        products_count = products_result.scalar() or 0

        if products_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete category with {products_count} products. Use force=true to delete anyway.",
            )

    # Delete category
    await db.execute(delete(ProductCategory).where(ProductCategory.id == category_id))
    await db.commit()


# Product Endpoints
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new product with variants"""

    # Validate category exists if specified
    if product.category_id:
        if not await validate_category_exists(db, product.category_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product category not found",
            )

    # Validate variant SKUs are unique globally
    variant_skus = [v.sku for v in product.variants]
    existing_skus = await db.execute(
        select(ProductVariant.sku).where(ProductVariant.sku.in_(variant_skus))
    )
    existing_sku_list = [row[0] for row in existing_skus.fetchall()]

    if existing_sku_list:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SKUs already exist: {', '.join(existing_sku_list)}",
        )

    # Set default variant if none specified
    if not any(v.is_default for v in product.variants):
        product.variants[0].is_default = True

    # Create product
    db_product = Product(
        id=uuid4(),
        name=product.name,
        description=product.description,
        short_description=product.short_description,
        product_type=product.product_type,
        status=product.status,
        category_id=product.category_id,
        brand=product.brand,
        vendor=product.vendor,
        tags=product.tags,
        seo_title=product.seo_title,
        seo_description=product.seo_description,
        published_at=product.published_at,
        is_featured=product.is_featured,
        min_quantity=product.min_quantity,
        max_quantity=product.max_quantity,
        is_taxable=product.is_taxable,
        tax_code=product.tax_code,
        requires_shipping=product.requires_shipping,
        track_inventory=product.track_inventory,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(db_product)
    await db.flush()  # Get the product ID

    # Create variants
    for variant_data in product.variants:
        db_variant = ProductVariant(
            id=uuid4(),
            product_id=db_product.id,
            sku=variant_data.sku,
            name=variant_data.name,
            price=variant_data.price,
            compare_at_price=variant_data.compare_at_price,
            cost_price=variant_data.cost_price,
            weight=variant_data.weight,
            dimensions=variant_data.dimensions,
            inventory_quantity=variant_data.inventory_quantity,
            inventory_policy=variant_data.inventory_policy,
            requires_shipping=variant_data.requires_shipping,
            is_default=variant_data.is_default,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(db_variant)
        await db.flush()

        # Create variant attributes
        for attr_data in variant_data.attributes:
            db_attr = ProductAttribute(
                id=uuid4(),
                variant_id=db_variant.id,
                name=attr_data.name,
                value=attr_data.value,
                type=attr_data.type,
                unit=attr_data.unit,
                is_variant_attribute=attr_data.is_variant_attribute,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(db_attr)

    # Create product images
    for img_data in product.images:
        db_image = ProductImage(
            id=uuid4(),
            product_id=db_product.id,
            url=img_data.url,
            alt_text=img_data.alt_text,
            is_primary=img_data.is_primary,
            sort_order=img_data.sort_order,
            created_at=datetime.utcnow(),
        )
        db.add(db_image)

    # Create product attributes
    for attr_data in product.attributes:
        db_attr = ProductAttribute(
            id=uuid4(),
            product_id=db_product.id,
            name=attr_data.name,
            value=attr_data.value,
            type=attr_data.type,
            unit=attr_data.unit,
            is_variant_attribute=attr_data.is_variant_attribute,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(db_attr)

    await db.commit()

    # Fetch complete product with relationships
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.variants).selectinload(ProductVariant.attributes),
            selectinload(Product.images),
            selectinload(Product.attributes),
        )
        .where(Product.id == db_product.id)
    )

    complete_product = result.scalar_one()

    # Calculate computed fields
    total_inventory = sum(v.inventory_quantity for v in complete_product.variants)
    stock_status = await calculate_stock_status(total_inventory)
    prices = [v.price for v in complete_product.variants]

    # Build response
    response_data = {
        **complete_product.__dict__,
        "total_inventory": total_inventory,
        "stock_status": stock_status,
        "min_price": min(prices) if prices else Decimal("0"),
        "max_price": max(prices) if prices else Decimal("0"),
        "avg_rating": None,
        "review_count": 0,
    }

    return ProductResponse(**response_data)


@router.get("/", response_model=List[ProductListResponse])
async def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of products to return"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    product_type: Optional[ProductType] = Query(None, description="Filter by type"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(
        None, min_length=1, description="Search in name and description"
    ),
    sort_by: str = Query("created_at", regex="^(name|created_at|updated_at|price)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get list of products with filtering and pagination"""

    # Build base query
    query = select(Product).options(
        joinedload(Product.category),
        selectinload(Product.variants),
        selectinload(Product.images),
    )

    # Apply filters
    if category_id:
        query = query.where(Product.category_id == category_id)

    if status:
        query = query.where(Product.status == status)

    if product_type:
        query = query.where(Product.product_type == product_type)

    if is_featured is not None:
        query = query.where(Product.is_featured == is_featured)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.short_description.ilike(search_term),
            )
        )

    # Apply sorting
    if sort_by == "name":
        order_column = Product.name
    elif sort_by == "price":
        # Sort by minimum variant price - this would need a subquery in real implementation
        order_column = Product.created_at  # Fallback for now
    elif sort_by == "updated_at":
        order_column = Product.updated_at
    else:
        order_column = Product.created_at

    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    products = result.unique().scalars().all()

    # Build response list
    response_list = []
    for product in products:
        total_inventory = sum(v.inventory_quantity for v in product.variants)
        stock_status = await calculate_stock_status(total_inventory)
        prices = [v.price for v in product.variants]
        primary_image = next(
            (img.url for img in product.images if img.is_primary), None
        )

        response_item = ProductListResponse(
            id=product.id,
            name=product.name,
            short_description=product.short_description,
            product_type=product.product_type,
            status=product.status,
            category=product.category.name if product.category else None,
            brand=product.brand,
            is_featured=product.is_featured,
            total_inventory=total_inventory,
            stock_status=stock_status,
            min_price=min(prices) if prices else Decimal("0"),
            max_price=max(prices) if prices else Decimal("0"),
            primary_image=primary_image,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
        response_list.append(response_item)

    return response_list


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID = Path(..., description="Product ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific product with all details"""

    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.variants).selectinload(ProductVariant.attributes),
            selectinload(Product.images),
            selectinload(Product.attributes),
        )
        .where(Product.id == product_id)
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Calculate computed fields
    total_inventory = sum(v.inventory_quantity for v in product.variants)
    stock_status = await calculate_stock_status(total_inventory)
    prices = [v.price for v in product.variants]

    # Add stock status to variants
    for variant in product.variants:
        variant.stock_status = await calculate_stock_status(variant.inventory_quantity)

    # Build response
    response_data = {
        **product.__dict__,
        "total_inventory": total_inventory,
        "stock_status": stock_status,
        "min_price": min(prices) if prices else Decimal("0"),
        "max_price": max(prices) if prices else Decimal("0"),
        "avg_rating": None,  # TODO: Calculate from reviews
        "review_count": 0,  # TODO: Count from reviews
    }

    return ProductResponse(**response_data)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID = Path(..., description="Product ID"),
    product_update: ProductUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a product"""

    # Get existing product
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Validate category exists if specified
    if product_update.category_id:
        if not await validate_category_exists(db, product_update.category_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product category not found",
            )

    # Update fields
    for field, value in product_update.dict(exclude_unset=True).items():
        setattr(db_product, field, value)

    db_product.updated_at = datetime.utcnow()

    await db.commit()

    # Return updated product
    return await get_product(product_id, db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID = Path(..., description="Product ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a product and all its variants"""

    # Check if product exists
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Delete related records (cascade should handle this, but being explicit)
    await db.execute(
        delete(ProductAttribute).where(ProductAttribute.product_id == product_id)
    )
    await db.execute(delete(ProductImage).where(ProductImage.product_id == product_id))
    await db.execute(
        delete(ProductVariant).where(ProductVariant.product_id == product_id)
    )
    await db.execute(delete(Product).where(Product.id == product_id))

    await db.commit()


# Bulk Operations
@router.post("/bulk", response_model=Dict[str, Any])
async def bulk_product_operations(
    operation: BulkProductOperation = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Perform bulk operations on products"""

    # Validate products exist
    result = await db.execute(
        select(Product.id).where(Product.id.in_(operation.product_ids))
    )
    existing_ids = [row[0] for row in result.fetchall()]

    if len(existing_ids) != len(operation.product_ids):
        missing_ids = set(operation.product_ids) - set(existing_ids)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found: {list(missing_ids)}",
        )

    updated_count = 0

    if operation.operation == "activate":
        await db.execute(
            update(Product)
            .where(Product.id.in_(operation.product_ids))
            .values(status=ProductStatus.ACTIVE, updated_at=datetime.utcnow())
        )
        updated_count = len(operation.product_ids)

    elif operation.operation == "deactivate":
        await db.execute(
            update(Product)
            .where(Product.id.in_(operation.product_ids))
            .values(status=ProductStatus.INACTIVE, updated_at=datetime.utcnow())
        )
        updated_count = len(operation.product_ids)

    elif operation.operation == "archive":
        await db.execute(
            update(Product)
            .where(Product.id.in_(operation.product_ids))
            .values(status=ProductStatus.ARCHIVED, updated_at=datetime.utcnow())
        )
        updated_count = len(operation.product_ids)

    elif operation.operation == "delete":
        # Delete products and related records
        for product_id in operation.product_ids:
            await db.execute(
                delete(ProductAttribute).where(
                    ProductAttribute.product_id == product_id
                )
            )
            await db.execute(
                delete(ProductImage).where(ProductImage.product_id == product_id)
            )
            await db.execute(
                delete(ProductVariant).where(ProductVariant.product_id == product_id)
            )

        await db.execute(delete(Product).where(Product.id.in_(operation.product_ids)))
        updated_count = len(operation.product_ids)

    # Update category if specified
    if operation.category_id:
        await db.execute(
            update(Product)
            .where(Product.id.in_(operation.product_ids))
            .values(category_id=operation.category_id, updated_at=datetime.utcnow())
        )

    # Update tags if specified
    if operation.tags:
        await db.execute(
            update(Product)
            .where(Product.id.in_(operation.product_ids))
            .values(tags=operation.tags, updated_at=datetime.utcnow())
        )

    await db.commit()

    return {
        "operation": operation.operation,
        "processed_count": updated_count,
        "product_ids": operation.product_ids,
    }


# Statistics and Analytics
@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_product_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """Get product analytics and statistics"""

    # Base query with date filters
    base_query = select(Product)

    if start_date:
        base_query = base_query.where(Product.created_at >= start_date)
    if end_date:
        base_query = base_query.where(Product.created_at <= end_date)
    if category_id:
        base_query = base_query.where(Product.category_id == category_id)

    # Total products
    total_result = await db.execute(
        select(func.count(Product.id)).select_from(base_query.subquery())
    )
    total_products = total_result.scalar()

    # Products by status
    status_result = await db.execute(
        select(Product.status, func.count(Product.id))
        .select_from(base_query.subquery())
        .group_by(Product.status)
    )
    status_counts = {status: count for status, count in status_result.fetchall()}

    # Products by type
    type_result = await db.execute(
        select(Product.product_type, func.count(Product.id))
        .select_from(base_query.subquery())
        .group_by(Product.product_type)
    )
    type_counts = {ptype: count for ptype, count in type_result.fetchall()}

    # Top categories
    category_result = await db.execute(
        select(ProductCategory.name, func.count(Product.id))
        .select_from(
            base_query.subquery().join(
                ProductCategory, Product.category_id == ProductCategory.id
            )
        )
        .group_by(ProductCategory.name)
        .order_by(func.count(Product.id).desc())
        .limit(10)
    )
    top_categories = [
        {"name": name, "count": count} for name, count in category_result.fetchall()
    ]

    # Low stock products
    low_stock_result = await db.execute(
        select(func.count(ProductVariant.id)).where(
            ProductVariant.inventory_quantity <= 10
        )
    )
    low_stock_count = low_stock_result.scalar()

    return {
        "total_products": total_products,
        "products_by_status": status_counts,
        "products_by_type": type_counts,
        "top_categories": top_categories,
        "low_stock_products": low_stock_count,
        "featured_products": status_counts.get("featured", 0),
        "analytics_period": {"start_date": start_date, "end_date": end_date},
    }
