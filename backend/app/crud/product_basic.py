"""
Basic product CRUD operations for ERP v17.0
Simplified product management focusing on essential ERP functionality
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.product import Product, ProductCategory, ProductStatus, ProductType
from app.schemas.product_basic import (
    ProductCreate, 
    ProductUpdate, 
    ProductResponse,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCategoryResponse
)
from app.core.exceptions import BusinessLogicError


# Product CRUD operations
def create_product(
    db: Session, 
    product_data: ProductCreate, 
    created_by: int
) -> Product:
    """Create a new product with validation."""
    # Check if product code exists
    existing_product = db.query(Product).filter(
        and_(
            Product.code == product_data.code,
            Product.organization_id == product_data.organization_id
        )
    ).first()
    
    if existing_product:
        raise BusinessLogicError("Product with this code already exists in the organization")
    
    # Check SKU uniqueness if provided
    if product_data.sku:
        existing_sku = db.query(Product).filter(Product.sku == product_data.sku).first()
        if existing_sku:
            raise BusinessLogicError("Product with this SKU already exists")
    
    # Create product
    product_dict = product_data.dict()
    product_dict['created_by'] = created_by
    
    product = Product(**product_dict)
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Get product by ID."""
    return db.query(Product).filter(
        and_(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        )
    ).first()


def get_product_by_code(db: Session, code: str, organization_id: int) -> Optional[Product]:
    """Get product by code within organization."""
    return db.query(Product).filter(
        and_(
            Product.code == code,
            Product.organization_id == organization_id,
            Product.deleted_at.is_(None)
        )
    ).first()


def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    """Get product by SKU."""
    return db.query(Product).filter(
        and_(
            Product.sku == sku,
            Product.deleted_at.is_(None)
        )
    ).first()


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    organization_id: Optional[int] = None,
    category_id: Optional[int] = None,
    status: Optional[ProductStatus] = None,
    product_type: Optional[ProductType] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "name",
    sort_order: str = "asc"
) -> tuple[List[Product], int]:
    """Get products with filtering and pagination."""
    query = db.query(Product).filter(Product.deleted_at.is_(None))
    
    # Search filter
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
    
    # Filters
    if organization_id:
        query = query.filter(Product.organization_id == organization_id)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if status:
        query = query.filter(Product.status == status.value)
    
    if product_type:
        query = query.filter(Product.product_type == product_type.value)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    # Sorting
    sort_column = getattr(Product, sort_by, Product.name)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Count for pagination
    total = query.count()
    
    # Apply pagination
    products = query.offset(skip).limit(limit).all()
    
    return products, total


def update_product(
    db: Session,
    product_id: int,
    product_data: ProductUpdate,
    updated_by: int
) -> Optional[Product]:
    """Update product information."""
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    
    # Check for code conflicts if updating code
    if product_data.code and product_data.code != product.code:
        existing_product = db.query(Product).filter(
            and_(
                Product.code == product_data.code,
                Product.organization_id == product.organization_id,
                Product.id != product_id,
                Product.deleted_at.is_(None)
            )
        ).first()
        if existing_product:
            raise BusinessLogicError("Product with this code already exists")
    
    # Check for SKU conflicts if updating SKU
    if product_data.sku and product_data.sku != product.sku:
        existing_sku = db.query(Product).filter(
            and_(
                Product.sku == product_data.sku,
                Product.id != product_id,
                Product.deleted_at.is_(None)
            )
        ).first()
        if existing_sku:
            raise BusinessLogicError("Product with this SKU already exists")
    
    # Update fields
    update_dict = product_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(product, key):
            setattr(product, key, value)
    
    product.updated_by = updated_by
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product


def deactivate_product(
    db: Session,
    product_id: int,
    deactivated_by: int
) -> Optional[Product]:
    """Deactivate product."""
    product = get_product_by_id(db, product_id)
    if not product:
        return None
    
    product.is_active = False
    product.status = ProductStatus.INACTIVE.value
    product.updated_by = deactivated_by
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product


def get_products_by_category(
    db: Session, 
    category_id: int,
    include_subcategories: bool = False
) -> List[Product]:
    """Get products by category."""
    if include_subcategories:
        # Get category and all its subcategories
        category = get_category_by_id(db, category_id)
        if not category:
            return []
        
        category_ids = [category_id]
        # This would need recursive implementation for deep hierarchies
        subcategories = db.query(ProductCategory).filter(
            ProductCategory.parent_id == category_id
        ).all()
        category_ids.extend([cat.id for cat in subcategories])
        
        return db.query(Product).filter(
            and_(
                Product.category_id.in_(category_ids),
                Product.deleted_at.is_(None),
                Product.is_active == True
            )
        ).all()
    else:
        return db.query(Product).filter(
            and_(
                Product.category_id == category_id,
                Product.deleted_at.is_(None),
                Product.is_active == True
            )
        ).all()


# Product Category CRUD operations
def create_category(
    db: Session, 
    category_data: ProductCategoryCreate, 
    created_by: int
) -> ProductCategory:
    """Create a new product category."""
    # Check if category code exists in organization
    existing_category = db.query(ProductCategory).filter(
        and_(
            ProductCategory.code == category_data.code,
            ProductCategory.organization_id == category_data.organization_id,
            ProductCategory.deleted_at.is_(None)
        )
    ).first()
    
    if existing_category:
        raise BusinessLogicError("Category with this code already exists in the organization")
    
    # Create category
    category_dict = category_data.dict()
    category_dict['created_by'] = created_by
    
    category = ProductCategory(**category_dict)
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


def get_category_by_id(db: Session, category_id: int) -> Optional[ProductCategory]:
    """Get category by ID."""
    return db.query(ProductCategory).filter(
        and_(
            ProductCategory.id == category_id,
            ProductCategory.deleted_at.is_(None)
        )
    ).first()


def get_categories(
    db: Session,
    organization_id: Optional[int] = None,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None
) -> List[ProductCategory]:
    """Get product categories."""
    query = db.query(ProductCategory).filter(ProductCategory.deleted_at.is_(None))
    
    if organization_id:
        query = query.filter(ProductCategory.organization_id == organization_id)
    
    if parent_id is not None:
        if parent_id == 0:  # Root categories
            query = query.filter(ProductCategory.parent_id.is_(None))
        else:
            query = query.filter(ProductCategory.parent_id == parent_id)
    
    if is_active is not None:
        query = query.filter(ProductCategory.is_active == is_active)
    
    return query.order_by(ProductCategory.sort_order, ProductCategory.name).all()


def get_product_statistics(db: Session, organization_id: Optional[int] = None) -> Dict[str, Any]:
    """Get basic product statistics."""
    query = db.query(Product).filter(Product.deleted_at.is_(None))
    
    if organization_id:
        query = query.filter(Product.organization_id == organization_id)
    
    total_products = query.count()
    active_products = query.filter(Product.is_active == True).count()
    
    # Products by status
    status_counts = {}
    for status in ProductStatus:
        count = query.filter(Product.status == status.value).count()
        status_counts[status.value] = count
    
    # Products by type
    type_counts = {}
    for ptype in ProductType:
        count = query.filter(Product.product_type == ptype.value).count()
        type_counts[ptype.value] = count
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "inactive_products": total_products - active_products,
        "by_status": status_counts,
        "by_type": type_counts
    }


def convert_to_response(product: Product) -> ProductResponse:
    """Convert Product model to response schema."""
    return ProductResponse(
        id=product.id,
        code=product.code,
        name=product.name,
        name_en=product.name_en,
        display_name=product.display_name,
        description=product.description,
        sku=product.sku,
        barcode=product.barcode,
        product_type=product.product_type,
        status=product.status,
        category_id=product.category_id,
        organization_id=product.organization_id,
        standard_price=product.standard_price,
        cost_price=product.cost_price,
        selling_price=product.selling_price,
        effective_selling_price=product.effective_selling_price,
        minimum_price=product.minimum_price,
        unit=product.unit,
        is_stock_managed=product.is_stock_managed,
        minimum_stock_level=product.minimum_stock_level,
        tax_rate=product.tax_rate,
        is_active=product.is_active,
        is_sellable=product.is_sellable,
        is_purchasable=product.is_purchasable,
        is_available=product.is_available,
        manufacturer=product.manufacturer,
        brand=product.brand,
        image_url=product.image_url,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


def convert_category_to_response(category: ProductCategory) -> ProductCategoryResponse:
    """Convert ProductCategory model to response schema."""
    return ProductCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        name_en=category.name_en,
        description=category.description,
        parent_id=category.parent_id,
        organization_id=category.organization_id,
        is_active=category.is_active,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at
    )