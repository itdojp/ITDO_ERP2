"""
ITDO ERP Backend - Unified Products API
Day 13: API Integration - Products Management Unified API
Integrates products_v21.py and product_management_v66.py functionality
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.product import Product
from app.models.user import User

# Mock authentication dependency for unified APIs
async def get_current_user() -> User:
    """Mock current user for unified APIs"""
    from unittest.mock import Mock
    mock_user = Mock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    return mock_user

router = APIRouter(prefix="/api/v1/products", tags=["products"])


# Product Status Enum
class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    DRAFT = "draft"


# Product Category Type Enum
class CategoryType(str, Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"


# Pydantic Schemas
class ProductBase(BaseModel):
    """Base product schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category_id: Optional[uuid.UUID] = None
    status: ProductStatus = ProductStatus.ACTIVE
    price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, float]] = None
    tags: List[str] = Field(default_factory=list)

    @validator("price", "cost", "weight", pre=True)
    def validate_decimal_fields(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product"""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category_id: Optional[uuid.UUID] = None
    status: Optional[ProductStatus] = None
    price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, float]] = None
    tags: Optional[List[str]] = None

    @validator("price", "cost", "weight", pre=True)
    def validate_decimal_fields(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class ProductResponse(ProductBase):
    """Schema for product response"""

    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response"""

    products: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class ProductCategory(BaseModel):
    """Product category schema"""

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    category_type: CategoryType
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    """Schema for creating a new category"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    parent_id: Optional[uuid.UUID] = None
    category_type: CategoryType = CategoryType.PHYSICAL


class CategoryResponse(ProductCategory):
    """Schema for category response with subcategories"""

    subcategories: List[ProductCategory] = Field(default_factory=list)


# Unified Product Service
class UnifiedProductService:
    """Unified service for product management operations"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    async def create_product(
        self, product_data: ProductCreate, user_id: uuid.UUID
    ) -> ProductResponse:
        """Create a new product with unified validation and processing"""

        # Check for duplicate SKU
        if product_data.sku:
            existing = await self.db.execute(
                select(Product).where(Product.sku == product_data.sku)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with SKU '{product_data.sku}' already exists",
                )

        # Generate product ID and SKU if not provided
        product_id = uuid.uuid4()
        if not product_data.sku:
            product_data.sku = f"PRD-{datetime.utcnow().strftime('%Y%m%d')}-{str(product_id)[:8].upper()}"

        # Create product instance
        product = Product(
            id=product_id,
            name=product_data.name,
            description=product_data.description,
            sku=product_data.sku,
            barcode=product_data.barcode,
            category_id=product_data.category_id,
            status=product_data.status.value,
            price=product_data.price,
            cost=product_data.cost,
            weight=product_data.weight,
            dimensions=product_data.dimensions,
            tags=product_data.tags,
            created_by=user_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)

        # Cache the product data
        await self._cache_product(product)

        return ProductResponse.from_orm(product)

    async def get_product(self, product_id: uuid.UUID) -> Optional[ProductResponse]:
        """Get a product by ID with caching"""

        # Try cache first
        cached = await self.redis.get(f"product:{product_id}")
        if cached:
            return ProductResponse.parse_raw(cached)

        # Get from database
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            return None

        response = ProductResponse.from_orm(product)
        await self._cache_product(product)

        return response

    async def update_product(
        self, product_id: uuid.UUID, product_data: ProductUpdate, user_id: uuid.UUID
    ) -> Optional[ProductResponse]:
        """Update a product with unified validation"""

        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

        if not product:
            return None

        # Check for duplicate SKU if updating
        if product_data.sku and product_data.sku != product.sku:
            existing = await self.db.execute(
                select(Product).where(
                    and_(Product.sku == product_data.sku, Product.id != product_id)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with SKU '{product_data.sku}' already exists",
                )

        # Update fields
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        product.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(product)

        # Update cache
        await self._cache_product(product)

        return ProductResponse.from_orm(product)

    async def delete_product(self, product_id: uuid.UUID) -> bool:
        """Soft delete a product"""

        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

        if not product:
            return False

        product.status = ProductStatus.DISCONTINUED.value
        product.updated_at = datetime.utcnow()

        await self.db.commit()

        # Remove from cache
        await self.redis.delete(f"product:{product_id}")

        return True

    async def list_products(
        self,
        page: int = 1,
        size: int = 50,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        status: Optional[ProductStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ProductListResponse:
        """List products with filtering and pagination"""

        query = select(Product).options(selectinload(Product.category))

        # Apply filters
        filters = []
        if search:
            filters.append(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%"),
                )
            )

        if category_id:
            filters.append(Product.category_id == category_id)

        if status:
            filters.append(Product.status == status.value)

        if filters:
            query = query.where(and_(*filters))

        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Get total count
        count_query = select(func.count(Product.id))
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        products = result.scalars().all()

        return ProductListResponse(
            products=[ProductResponse.from_orm(p) for p in products],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    async def _cache_product(self, product):
        """Cache product data in Redis"""
        product_data = ProductResponse.from_orm(product)
        await self.redis.setex(
            f"product:{product.id}",
            3600,  # 1 hour
            product_data.json(),
        )


# API Dependencies
async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    return aioredis.Redis.from_url("redis://localhost:6379")


async def get_product_service(
    db: AsyncSession = Depends(get_db), redis: aioredis.Redis = Depends(get_redis)
) -> UnifiedProductService:
    """Get product service instance"""
    return UnifiedProductService(db, redis)


# API Endpoints - Unified Products API
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    service: UnifiedProductService = Depends(get_product_service),
):
    """Create a new product (unified from v21 and v66 APIs)"""
    return await service.create_product(product_data, current_user.id)


@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    status: Optional[ProductStatus] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    service: UnifiedProductService = Depends(get_product_service),
):
    """List products with filtering and pagination"""
    return await service.list_products(
        page=page,
        size=size,
        search=search,
        category_id=category_id,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID, service: UnifiedProductService = Depends(get_product_service)
):
    """Get a product by ID"""
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    service: UnifiedProductService = Depends(get_product_service),
):
    """Update a product"""
    product = await service.update_product(product_id, product_data, current_user.id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID, service: UnifiedProductService = Depends(get_product_service)
):
    """Delete a product (soft delete)"""
    success = await service.delete_product(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )


# Legacy endpoints for backward compatibility
@router.post("/products-v21", response_model=Dict[str, Any], deprecated=True)
async def create_product_v21(
    name: str,
    price: float,
    current_user: User = Depends(get_current_user),
    service: UnifiedProductService = Depends(get_product_service),
):
    """Legacy v21 product creation endpoint (deprecated)"""
    product_data = ProductCreate(
        name=name, price=Decimal(str(price)), status=ProductStatus.ACTIVE
    )
    result = await service.create_product(product_data, current_user.id)
    return {
        "id": str(result.id),
        "name": result.name,
        "price": float(result.price) if result.price else 0.0,
    }


@router.get("/products-v21", response_model=List[Dict[str, Any]], deprecated=True)
async def list_products_v21(
    service: UnifiedProductService = Depends(get_product_service),
):
    """Legacy v21 product listing endpoint (deprecated)"""
    result = await service.list_products(page=1, size=100)
    return [
        {"id": str(p.id), "name": p.name, "price": float(p.price) if p.price else 0.0}
        for p in result.products
    ]


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for unified products API"""
    return {
        "status": "healthy",
        "service": "unified-products-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
