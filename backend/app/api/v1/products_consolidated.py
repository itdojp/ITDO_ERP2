"""
Consolidated Products API - Day 13 API Consolidation
Integrates functionality from all product API versions into a single, comprehensive API.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/products", tags=["products"])

# =====================================
# SCHEMAS (Consolidated from all versions)
# =====================================

class ProductBase(BaseModel):
    """Base product schema"""
    code: str
    name: str
    price: float
    stock: int = 0
    description: Optional[str] = None

class ProductCreate(ProductBase):
    """Product creation schema"""
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    cost_price: Optional[Decimal] = None
    min_stock_level: Optional[int] = None

class ProductUpdate(BaseModel):
    """Product update schema"""
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    cost_price: Optional[Decimal] = None
    min_stock_level: Optional[int] = None

class Product(ProductBase):
    """Product response schema"""
    id: Union[str, int]
    created_at: datetime
    updated_at: Optional[datetime] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    cost_price: Optional[Decimal] = None
    min_stock_level: Optional[int] = None

class ProductListResponse(BaseModel):
    """Product list response"""
    products: List[Product]
    total: int
    page: int
    size: int

class ProductFilter(BaseModel):
    """Product filtering schema"""
    name: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None

class BulkCreateRequest(BaseModel):
    """Bulk product creation"""
    products: List[ProductCreate]

class BulkCreateResponse(BaseModel):
    """Bulk creation response"""
    created: List[Product]
    failed: List[Dict[str, Any]]
    total_created: int
    total_failed: int

# Legacy schemas for backward compatibility
class LegacyProductV21(BaseModel):
    """Legacy v21 product format"""
    id: int
    name: str
    price: float

class SimpleProduct(BaseModel):
    """Simple product format"""
    code: str
    name: str
    price: float

# =====================================
# MOCK DATA STORES (for development)
# =====================================

# Mock database - will be replaced with actual database operations
products_db: Dict[str, Dict[str, Any]] = {}
products_counter = 0

# Legacy v21 mock store
legacy_products_db: List[Dict[str, Any]] = []

# =====================================
# UTILITY FUNCTIONS
# =====================================

def generate_product_id() -> str:
    """Generate unique product ID"""
    return str(uuid.uuid4())

def get_next_legacy_id() -> int:
    """Get next legacy ID for v21 compatibility"""
    return len(legacy_products_db) + 1

async def get_current_user():
    """Mock current user - replace with actual implementation"""
    return {"id": "current-user", "is_admin": True}

# =====================================
# CORE API ENDPOINTS
# =====================================

@router.post("/", response_model=Product, status_code=201)
async def create_product(
    product: ProductCreate,
    current_user = Depends(get_current_user)
) -> Product:
    """
    Create a new product
    Consolidates functionality from all API versions
    """
    # Check for duplicate product code
    for existing_product in products_db.values():
        if existing_product["code"] == product.code:
            raise HTTPException(
                status_code=400, 
                detail=f"Product with code '{product.code}' already exists"
            )
    
    # Create new product
    product_id = generate_product_id()
    now = datetime.utcnow()
    
    new_product = {
        "id": product_id,
        "code": product.code,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "description": product.description,
        "category_id": product.category_id,
        "supplier_id": product.supplier_id,
        "cost_price": product.cost_price,
        "min_stock_level": product.min_stock_level,
        "created_at": now,
        "updated_at": now
    }
    
    products_db[product_id] = new_product
    
    return Product(**new_product)

@router.get("/", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    current_user = Depends(get_current_user)
) -> ProductListResponse:
    """
    List products with filtering and pagination
    Enhanced from multiple API versions
    """
    # Filter products based on criteria
    filtered_products = []
    
    for product_data in products_db.values():
        # Apply filters
        if search and search.lower() not in product_data["name"].lower():
            continue
        if category_id and product_data.get("category_id") != category_id:
            continue
        if supplier_id and product_data.get("supplier_id") != supplier_id:
            continue
        if min_price and product_data["price"] < min_price:
            continue
        if max_price and product_data["price"] > max_price:
            continue
            
        filtered_products.append(Product(**product_data))
    
    # Apply pagination
    total = len(filtered_products)
    paginated_products = filtered_products[skip:skip + limit]
    
    return ProductListResponse(
        products=paginated_products,
        total=total,
        page=skip // limit + 1,
        size=len(paginated_products)
    )

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    current_user = Depends(get_current_user)
) -> Product:
    """Get a specific product by ID"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return Product(**products_db[product_id])

@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user = Depends(get_current_user)
) -> Product:
    """Update a product"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update product data
    product_data = products_db[product_id].copy()
    update_data = product_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        product_data[field] = value
    
    product_data["updated_at"] = datetime.utcnow()
    products_db[product_id] = product_data
    
    return Product(**product_data)

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a product"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    del products_db[product_id]
    return {"message": "Product deleted successfully"}

# =====================================
# ADVANCED FEATURES
# =====================================

@router.post("/bulk", response_model=BulkCreateResponse)
async def bulk_create_products(
    request: BulkCreateRequest,
    current_user = Depends(get_current_user)
) -> BulkCreateResponse:
    """
    Bulk create products
    Enhanced from products_complete_v30.py
    """
    created_products = []
    failed_products = []
    
    for product_data in request.products:
        try:
            # Check for duplicate code
            duplicate_found = False
            for existing_product in products_db.values():
                if existing_product["code"] == product_data.code:
                    duplicate_found = True
                    break
            
            if duplicate_found:
                failed_products.append({
                    "product": product_data.dict(),
                    "error": f"Product code '{product_data.code}' already exists"
                })
                continue
            
            # Create product
            product_id = generate_product_id()
            now = datetime.utcnow()
            
            new_product = {
                "id": product_id,
                "code": product_data.code,
                "name": product_data.name,
                "price": product_data.price,
                "stock": product_data.stock,
                "description": product_data.description,
                "category_id": product_data.category_id,
                "supplier_id": product_data.supplier_id,
                "cost_price": product_data.cost_price,
                "min_stock_level": product_data.min_stock_level,
                "created_at": now,
                "updated_at": now
            }
            
            products_db[product_id] = new_product
            created_products.append(Product(**new_product))
            
        except Exception as e:
            failed_products.append({
                "product": product_data.dict(),
                "error": str(e)
            })
    
    return BulkCreateResponse(
        created=created_products,
        failed=failed_products,
        total_created=len(created_products),
        total_failed=len(failed_products)
    )

@router.post("/search", response_model=ProductListResponse)
async def advanced_search(
    filters: ProductFilter,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(get_current_user)
) -> ProductListResponse:
    """
    Advanced product search with complex filters
    Enhanced search functionality
    """
    filtered_products = []
    
    for product_data in products_db.values():
        # Apply all filters
        if filters.name and filters.name.lower() not in product_data["name"].lower():
            continue
        if filters.category_id and product_data.get("category_id") != filters.category_id:
            continue
        if filters.supplier_id and product_data.get("supplier_id") != filters.supplier_id:
            continue
        if filters.min_price and product_data["price"] < filters.min_price:
            continue
        if filters.max_price and product_data["price"] > filters.max_price:
            continue
        if filters.min_stock and product_data["stock"] < filters.min_stock:
            continue
        if filters.max_stock and product_data["stock"] > filters.max_stock:
            continue
            
        filtered_products.append(Product(**product_data))
    
    # Apply pagination
    total = len(filtered_products)
    paginated_products = filtered_products[skip:skip + limit]
    
    return ProductListResponse(
        products=paginated_products,
        total=total,
        page=skip // limit + 1,
        size=len(paginated_products)
    )

@router.post("/{product_id}/upload-image")
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload product image
    From products_v21.py enhanced functionality
    """
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # In a real implementation, you would save the file to storage
    # For now, we'll just simulate the upload
    image_url = f"/images/products/{product_id}/{file.filename}"
    
    # Update product with image URL
    products_db[product_id]["image_url"] = image_url
    products_db[product_id]["updated_at"] = datetime.utcnow()
    
    return {
        "message": "Image uploaded successfully",
        "image_url": image_url,
        "filename": file.filename
    }

# =====================================
# BACKWARD COMPATIBILITY ENDPOINTS
# =====================================

@router.post("/products-v21", response_model=LegacyProductV21)
async def create_product_v21(name: str, price: float) -> LegacyProductV21:
    """
    Legacy v21 endpoint for backward compatibility
    Redirects to new API while maintaining old format
    """
    legacy_id = get_next_legacy_id()
    
    # Create in new format
    product_create = ProductCreate(
        code=f"LEGACY_{legacy_id}",
        name=name,
        price=price,
        stock=0
    )
    
    # Create using main API
    new_product = await create_product(product_create)
    
    # Store in legacy format for backward compatibility
    legacy_product = {
        "id": legacy_id,
        "name": name,
        "price": price
    }
    legacy_products_db.append(legacy_product)
    
    return LegacyProductV21(**legacy_product)

@router.get("/products-v21", response_model=List[LegacyProductV21])
async def list_products_v21() -> List[LegacyProductV21]:
    """
    Legacy v21 list endpoint for backward compatibility
    """
    return [LegacyProductV21(**product) for product in legacy_products_db]

# Simple API compatibility endpoints
@router.post("/simple", response_model=SimpleProduct)
async def create_simple_product(product: SimpleProduct) -> SimpleProduct:
    """Simple product creation for basic use cases"""
    product_create = ProductCreate(
        code=product.code,
        name=product.name,
        price=product.price,
        stock=0
    )
    
    await create_product(product_create)
    return product

@router.get("/simple", response_model=List[SimpleProduct])
async def list_simple_products() -> List[SimpleProduct]:
    """Simple product listing"""
    simple_products = []
    for product_data in products_db.values():
        simple_products.append(SimpleProduct(
            code=product_data["code"],
            name=product_data["name"],
            price=product_data["price"]
        ))
    return simple_products

# =====================================
# HEALTH CHECK
# =====================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """API health check"""
    return {
        "status": "healthy",
        "total_products": len(products_db),
        "api_version": "consolidated_v1.0",
        "timestamp": datetime.utcnow().isoformat()
    }