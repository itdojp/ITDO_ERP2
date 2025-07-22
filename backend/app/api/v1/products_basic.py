"""
Basic Product Management API for ERP v17.0
Focused on essential product operations with simplified endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.product_basic import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse, 
    ProductBasic,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCategoryResponse
)
from app.models.user import User
from app.models.product import ProductStatus, ProductType
from app.crud.product_basic import (
    create_product,
    get_product_by_id,
    get_product_by_code,
    get_product_by_sku,
    get_products,
    update_product,
    deactivate_product,
    get_products_by_category,
    create_category,
    get_category_by_id,
    get_categories,
    get_product_statistics,
    convert_to_response,
    convert_category_to_response
)

router = APIRouter(prefix="/products-basic", tags=["Products Basic"])


# Product endpoints
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_new_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product - ERP v17.0."""
    try:
        product = create_product(db, product_data, created_by=current_user.id)
        return convert_to_response(product)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    organization_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    status: Optional[ProductStatus] = Query(None),
    product_type: Optional[ProductType] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List products with filtering and pagination."""
    products, total = get_products(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        organization_id=organization_id,
        category_id=category_id,
        status=status,
        product_type=product_type,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Convert to response format
    return [convert_to_response(product) for product in products]


@router.get("/statistics")
async def get_product_stats(
    organization_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product statistics."""
    return get_product_statistics(db, organization_id)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product by ID."""
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return convert_to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product_info(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update product information."""
    # Check if product exists
    existing_product = get_product_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    try:
        updated_product = update_product(db, product_id, product_data, updated_by=current_user.id)
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product"
            )
        
        return convert_to_response(updated_product)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{product_id}/deactivate", response_model=ProductResponse)
async def deactivate_product_item(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate product."""
    # Check if product exists
    existing_product = get_product_by_id(db, product_id)
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    try:
        deactivated_product = deactivate_product(db, product_id, deactivated_by=current_user.id)
        if not deactivated_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate product"
            )
        
        return convert_to_response(deactivated_product)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/code/{code}", response_model=ProductBasic)
async def get_product_by_code_endpoint(
    code: str,
    organization_id: int = Query(..., description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product by code within organization."""
    product = get_product_by_code(db, code, organization_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductBasic(
        id=product.id,
        code=product.code,
        name=product.name,
        display_name=product.display_name,
        sku=product.sku,
        standard_price=product.standard_price,
        is_active=product.is_active
    )


@router.get("/sku/{sku}", response_model=ProductBasic)
async def get_product_by_sku_endpoint(
    sku: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product by SKU."""
    product = get_product_by_sku(db, sku)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductBasic(
        id=product.id,
        code=product.code,
        name=product.name,
        display_name=product.display_name,
        sku=product.sku,
        standard_price=product.standard_price,
        is_active=product.is_active
    )


@router.get("/{product_id}/context")
async def get_product_erp_context(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ERP-specific context for product."""
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product.get_erp_context()


# Product Category endpoints
@router.post("/categories/", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_product_category(
    category_data: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product category."""
    try:
        category = create_category(db, category_data, created_by=current_user.id)
        return convert_category_to_response(category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/categories/", response_model=List[ProductCategoryResponse])
async def list_product_categories(
    organization_id: Optional[int] = Query(None),
    parent_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List product categories."""
    categories = get_categories(
        db=db,
        organization_id=organization_id,
        parent_id=parent_id,
        is_active=is_active
    )
    
    return [convert_category_to_response(category) for category in categories]


@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
async def get_product_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product category by ID."""
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return convert_category_to_response(category)


@router.get("/categories/{category_id}/products", response_model=List[ProductBasic])
async def get_products_in_category(
    category_id: int,
    include_subcategories: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products in a category."""
    products = get_products_by_category(db, category_id, include_subcategories)
    
    return [
        ProductBasic(
            id=product.id,
            code=product.code,
            name=product.name,
            display_name=product.display_name,
            sku=product.sku,
            standard_price=product.standard_price,
            is_active=product.is_active
        )
        for product in products
    ]