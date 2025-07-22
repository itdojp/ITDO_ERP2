"""
ERP Product Management API
Enhanced product and category management with price history tracking
"""

import logging
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from pydantic import BaseModel, Field, validator

from app.core.dependencies import get_current_active_user, get_db
from app.core.tenant_deps import TenantDep, RequireApiAccess
from app.models.user import User
from app.models.organization import Organization
from app.models.product import Product, ProductPriceHistory, ProductType, ProductStatus
from app.models.product_category import ProductCategory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp-products", tags=["ERP Product Management"])


# Pydantic schemas
class ProductCategoryCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    organization_id: int = Field(..., description="Organization ID")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    is_active: bool = True


class ProductCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    organization_id: int = Field(..., description="Organization ID")
    category_id: Optional[int] = None
    
    # Product specifications
    product_type: ProductType = ProductType.PHYSICAL
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    
    # Pricing
    base_price: Decimal = Field(0, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    selling_price: Decimal = Field(0, ge=0)
    currency: str = Field("JPY", max_length=3)
    
    # Tax
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    is_taxable: bool = True
    
    # Physical attributes
    weight: Optional[Decimal] = Field(None, ge=0)
    length: Optional[Decimal] = Field(None, ge=0)
    width: Optional[Decimal] = Field(None, ge=0)
    height: Optional[Decimal] = Field(None, ge=0)
    
    # Inventory
    track_inventory: bool = True
    min_stock_level: Optional[int] = Field(0, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    
    # Additional info
    supplier_name: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    
    # Product specifications
    product_type: Optional[ProductType] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    
    # Pricing
    base_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    
    # Tax
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    is_taxable: Optional[bool] = None
    
    # Physical attributes
    weight: Optional[Decimal] = Field(None, ge=0)
    length: Optional[Decimal] = Field(None, ge=0)
    width: Optional[Decimal] = Field(None, ge=0)
    height: Optional[Decimal] = Field(None, ge=0)
    
    # Inventory
    track_inventory: Optional[bool] = None
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    
    # Additional info
    supplier_name: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None


class PriceUpdateRequest(BaseModel):
    price_type: str = Field(..., regex="^(base_price|selling_price|cost_price)$")
    new_price: Decimal = Field(..., ge=0)
    change_reason: Optional[str] = Field(None, max_length=200)
    effective_date: Optional[datetime] = None


class ProductCategoryResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    organization_id: int
    organization_name: Optional[str]
    parent_id: Optional[int]
    parent_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    
    # Computed fields
    product_count: int = 0
    subcategory_count: int = 0
    hierarchy_level: int = 0


class ProductResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    organization_id: int
    organization_name: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str]
    
    # Specifications
    product_type: str
    status: str
    sku: Optional[str]
    barcode: Optional[str]
    
    # Pricing
    base_price: Decimal
    cost_price: Optional[Decimal]
    selling_price: Decimal
    display_price: Decimal
    profit_margin: Optional[Decimal]
    currency: str
    
    # Tax
    tax_rate: Optional[Decimal]
    is_taxable: bool
    price_with_tax: Decimal
    
    # Physical
    weight: Optional[Decimal]
    dimensions: Optional[str]
    volume: Optional[Decimal]
    
    # Inventory
    track_inventory: bool
    min_stock_level: Optional[int]
    reorder_point: Optional[int]
    is_low_stock: bool
    
    # Additional
    supplier_name: Optional[str]
    brand: Optional[str]
    image_url: Optional[str]
    is_active: bool
    is_available: bool
    created_at: str
    updated_at: Optional[str]


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class CategoryListResponse(BaseModel):
    categories: List[ProductCategoryResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    price_type: str
    old_price: Decimal
    new_price: Decimal
    change_reason: Optional[str]
    effective_date: str
    created_by: Optional[str]
    created_at: str


class ProductStatsResponse(BaseModel):
    total_products: int
    active_products: int
    low_stock_products: int
    products_by_category: Dict[str, int]
    products_by_type: Dict[str, int]
    average_price: float
    total_inventory_value: float


# Product Category Management
@router.post("/categories", response_model=ProductCategoryResponse)
async def create_category(
    category_request: ProductCategoryCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new product category"""
    try:
        # Check if category code exists in organization
        existing_category = db.query(ProductCategory).filter(
            and_(
                ProductCategory.code == category_request.code,
                ProductCategory.organization_id == category_request.organization_id
            )
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this code already exists in the organization"
            )
        
        # Validate organization
        organization = db.query(Organization).filter(Organization.id == category_request.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate parent category if provided
        if category_request.parent_id:
            parent_category = db.query(ProductCategory).filter(
                and_(
                    ProductCategory.id == category_request.parent_id,
                    ProductCategory.organization_id == category_request.organization_id
                )
            ).first()
            
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found in the same organization"
                )
        
        # Create category
        category_data = category_request.dict()
        category_data["created_by"] = current_user.id
        
        category = ProductCategory(**category_data)
        db.add(category)
        db.commit()
        db.refresh(category)
        
        # Get related data for response
        parent_name = None
        if category.parent_id:
            parent = db.query(ProductCategory).filter(ProductCategory.id == category.parent_id).first()
            parent_name = parent.name if parent else None
        
        logger.info(f"Product category created: {category.id} by {current_user.id}")
        
        return ProductCategoryResponse(
            id=category.id,
            code=category.code,
            name=category.name,
            description=category.description,
            organization_id=category.organization_id,
            organization_name=organization.name,
            parent_id=category.parent_id,
            parent_name=parent_name,
            is_active=category.is_active,
            created_at=category.created_at.isoformat(),
            updated_at=category.updated_at.isoformat() if category.updated_at else None,
            product_count=len(category.products),
            subcategory_count=len(category.children),
            hierarchy_level=0  # Would need calculation
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Category creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    parent_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List product categories with filtering"""
    try:
        query = db.query(ProductCategory).filter(ProductCategory.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    ProductCategory.name.ilike(search_term),
                    ProductCategory.code.ilike(search_term),
                    ProductCategory.description.ilike(search_term)
                )
            )
        
        if organization_id is not None:
            query = query.filter(ProductCategory.organization_id == organization_id)
        
        if parent_id is not None:
            query = query.filter(ProductCategory.parent_id == parent_id)
        
        if is_active is not None:
            query = query.filter(ProductCategory.is_active == is_active)
        
        query = query.order_by(ProductCategory.name)
        total_count = query.count()
        categories = query.offset(skip).limit(limit).all()
        
        # Prepare response
        category_responses = []
        for category in categories:
            organization_name = category.organization.name if category.organization else None
            parent_name = None
            
            if category.parent_id:
                parent = db.query(ProductCategory).filter(ProductCategory.id == category.parent_id).first()
                parent_name = parent.name if parent else None
            
            category_responses.append(ProductCategoryResponse(
                id=category.id,
                code=category.code,
                name=category.name,
                description=category.description,
                organization_id=category.organization_id,
                organization_name=organization_name,
                parent_id=category.parent_id,
                parent_name=parent_name,
                is_active=category.is_active,
                created_at=category.created_at.isoformat(),
                updated_at=category.updated_at.isoformat() if category.updated_at else None,
                product_count=len(category.products),
                subcategory_count=len(category.children),
                hierarchy_level=0
            ))
        
        return CategoryListResponse(
            categories=category_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


# Product Management
@router.post("/products", response_model=ProductResponse)
async def create_product(
    product_request: ProductCreateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Create a new product"""
    try:
        # Check if product code exists in organization
        existing_product = db.query(Product).filter(
            and_(
                Product.code == product_request.code,
                Product.organization_id == product_request.organization_id
            )
        ).first()
        
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this code already exists in the organization"
            )
        
        # Validate organization
        organization = db.query(Organization).filter(Organization.id == product_request.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Validate category if provided
        category_name = None
        if product_request.category_id:
            category = db.query(ProductCategory).filter(
                and_(
                    ProductCategory.id == product_request.category_id,
                    ProductCategory.organization_id == product_request.organization_id
                )
            ).first()
            
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found in the same organization"
                )
            category_name = category.name
        
        # Create product
        product_data = product_request.dict()
        product_data["created_by"] = current_user.id
        
        product = Product(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        
        logger.info(f"Product created: {product.id} by {current_user.id}")
        
        return ProductResponse(
            id=product.id,
            code=product.code,
            name=product.name,
            description=product.description,
            organization_id=product.organization_id,
            organization_name=organization.name,
            category_id=product.category_id,
            category_name=category_name,
            product_type=product.product_type,
            status=product.status,
            sku=product.sku,
            barcode=product.barcode,
            base_price=product.base_price,
            cost_price=product.cost_price,
            selling_price=product.selling_price,
            display_price=product.display_price,
            profit_margin=product.profit_margin,
            currency=product.currency,
            tax_rate=product.tax_rate,
            is_taxable=product.is_taxable,
            price_with_tax=product.price_with_tax,
            weight=product.weight,
            dimensions=product.get_dimension_string(),
            volume=product.volume,
            track_inventory=product.track_inventory,
            min_stock_level=product.min_stock_level,
            reorder_point=product.reorder_point,
            is_low_stock=product.is_low_stock,
            supplier_name=product.supplier_name,
            brand=product.brand,
            image_url=product.image_url,
            is_active=product.is_active,
            is_available=product.is_available(),
            created_at=product.created_at.isoformat(),
            updated_at=product.updated_at.isoformat() if product.updated_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    product_type: Optional[ProductType] = Query(None),
    status: Optional[ProductStatus] = Query(None),
    is_active: Optional[bool] = Query(None),
    low_stock_only: bool = Query(False),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """List products with advanced filtering"""
    try:
        query = db.query(Product).filter(Product.deleted_at.is_(None))
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.code.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.barcode.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        if organization_id is not None:
            query = query.filter(Product.organization_id == organization_id)
        
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        
        if product_type is not None:
            query = query.filter(Product.product_type == product_type.value)
        
        if status is not None:
            query = query.filter(Product.status == status.value)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        total_count = query.count()
        products = query.offset(skip).limit(limit).all()
        
        # Prepare response
        product_responses = []
        for product in products:
            organization_name = product.organization.name if product.organization else None
            category_name = product.category.name if product.category else None
            
            # Skip low stock filter products if needed
            if low_stock_only and not product.is_low_stock:
                continue
            
            product_responses.append(ProductResponse(
                id=product.id,
                code=product.code,
                name=product.name,
                description=product.description,
                organization_id=product.organization_id,
                organization_name=organization_name,
                category_id=product.category_id,
                category_name=category_name,
                product_type=product.product_type,
                status=product.status,
                sku=product.sku,
                barcode=product.barcode,
                base_price=product.base_price,
                cost_price=product.cost_price,
                selling_price=product.selling_price,
                display_price=product.display_price,
                profit_margin=product.profit_margin,
                currency=product.currency,
                tax_rate=product.tax_rate,
                is_taxable=product.is_taxable,
                price_with_tax=product.price_with_tax,
                weight=product.weight,
                dimensions=product.get_dimension_string(),
                volume=product.volume,
                track_inventory=product.track_inventory,
                min_stock_level=product.min_stock_level,
                reorder_point=product.reorder_point,
                is_low_stock=product.is_low_stock,
                supplier_name=product.supplier_name,
                brand=product.brand,
                image_url=product.image_url,
                is_active=product.is_active,
                is_available=product.is_available(),
                created_at=product.created_at.isoformat(),
                updated_at=product.updated_at.isoformat() if product.updated_at else None
            ))
        
        return ProductListResponse(
            products=product_responses,
            total_count=total_count,
            page=(skip // limit) + 1,
            limit=limit,
            has_next=skip + limit < total_count,
            has_prev=skip > 0
        )
    
    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@router.put("/products/{product_id}/price", response_model=PriceHistoryResponse)
async def update_product_price(
    product_id: int,
    price_request: PriceUpdateRequest,
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Update product price with history tracking"""
    try:
        product = db.query(Product).filter(
            and_(Product.id == product_id, Product.deleted_at.is_(None))
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Get current price
        current_price = getattr(product, price_request.price_type)
        
        # Create price history record
        price_history = ProductPriceHistory(
            product_id=product.id,
            organization_id=product.organization_id,
            old_price=current_price,
            new_price=price_request.new_price,
            price_type=price_request.price_type,
            change_reason=price_request.change_reason,
            effective_date=price_request.effective_date or datetime.now(UTC),
            created_by=current_user.id
        )
        
        # Update product price
        setattr(product, price_request.price_type, price_request.new_price)
        product.updated_by = current_user.id
        product.updated_at = datetime.now(UTC)
        
        db.add(price_history)
        db.commit()
        db.refresh(price_history)
        
        logger.info(f"Product price updated: {product.id} - {price_request.price_type} by {current_user.id}")
        
        return PriceHistoryResponse(
            id=price_history.id,
            product_id=price_history.product_id,
            price_type=price_history.price_type,
            old_price=price_history.old_price,
            new_price=price_history.new_price,
            change_reason=price_history.change_reason,
            effective_date=price_history.effective_date.isoformat(),
            created_by=current_user.full_name,
            created_at=price_history.created_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product price"
        )


@router.get("/products/{product_id}/price-history", response_model=List[PriceHistoryResponse])
async def get_price_history(
    product_id: int,
    price_type: Optional[str] = Query(None, regex="^(base_price|selling_price|cost_price)$"),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get product price history"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        query = db.query(ProductPriceHistory).filter(ProductPriceHistory.product_id == product_id)
        
        if price_type:
            query = query.filter(ProductPriceHistory.price_type == price_type)
        
        history = query.order_by(desc(ProductPriceHistory.effective_date)).all()
        
        # Get creator names
        user_ids = [h.created_by for h in history if h.created_by]
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        user_names = {user.id: user.full_name for user in users}
        
        response = []
        for h in history:
            response.append(PriceHistoryResponse(
                id=h.id,
                product_id=h.product_id,
                price_type=h.price_type,
                old_price=h.old_price,
                new_price=h.new_price,
                change_reason=h.change_reason,
                effective_date=h.effective_date.isoformat(),
                created_by=user_names.get(h.created_by, "Unknown") if h.created_by else None,
                created_at=h.created_at.isoformat()
            ))
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get price history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve price history"
        )


@router.get("/statistics", response_model=ProductStatsResponse)
async def get_product_statistics(
    organization_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    tenant: TenantDep = TenantDep,
    current_user: User = Depends(get_current_active_user),
    _: RequireApiAccess = RequireApiAccess
):
    """Get product statistics"""
    try:
        query = db.query(Product).filter(Product.deleted_at.is_(None))
        
        if organization_id:
            query = query.filter(Product.organization_id == organization_id)
        
        total_products = query.count()
        active_products = query.filter(Product.is_active == True).count()
        
        # Low stock products (would need inventory integration for real implementation)
        low_stock_products = 0  # Placeholder
        
        # Products by category
        category_stats = db.query(
            ProductCategory.name.label('category_name'),
            func.count(Product.id).label('product_count')
        ).join(
            Product, Product.category_id == ProductCategory.id
        ).filter(
            Product.deleted_at.is_(None)
        )
        
        if organization_id:
            category_stats = category_stats.filter(Product.organization_id == organization_id)
        
        category_stats = category_stats.group_by(ProductCategory.name).all()
        products_by_category = {stat.category_name: stat.product_count for stat in category_stats}
        
        # Products by type
        type_stats = query.group_by(Product.product_type).with_entities(
            Product.product_type,
            func.count(Product.id)
        ).all()
        products_by_type = {stat[0]: stat[1] for stat in type_stats}
        
        # Average price
        avg_price = query.with_entities(func.avg(Product.selling_price)).scalar() or 0
        
        # Total inventory value (would need inventory integration)
        total_inventory_value = 0  # Placeholder
        
        return ProductStatsResponse(
            total_products=total_products,
            active_products=active_products,
            low_stock_products=low_stock_products,
            products_by_category=products_by_category,
            products_by_type=products_by_type,
            average_price=float(avg_price),
            total_inventory_value=total_inventory_value
        )
    
    except Exception as e:
        logger.error(f"Failed to get product statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product statistics"
        )