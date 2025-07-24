"""
Core Products API Endpoints - CC02 v50.0
12-Hour Core Business API Sprint - Products Management Implementation
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
import uuid
import json

# Import database dependencies
from app.core.database import get_db

router = APIRouter(prefix="/products", tags=["Core Products"])

# Enhanced product models for core business functionality
class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    DRAFT = "draft"

class ProductDimensions(BaseModel):
    length: float = Field(gt=0, description="Length in cm")
    width: float = Field(gt=0, description="Width in cm") 
    height: float = Field(gt=0, description="Height in cm")

class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Selling price")
    cost: Optional[float] = Field(None, ge=0, description="Cost price")
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    weight: Optional[float] = Field(None, ge=0, description="Weight in kg")
    dimensions: Optional[ProductDimensions] = None
    is_active: bool = True
    track_inventory: bool = True
    tax_exempt: bool = False
    min_order_quantity: int = Field(1, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)
    
    @field_validator('max_order_quantity')
    @classmethod
    def validate_max_order_quantity(cls, v, info):
        if v is not None and 'min_order_quantity' in info.data:
            if v < info.data['min_order_quantity']:
                raise ValueError('max_order_quantity must be >= min_order_quantity')
        return v

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    cost: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    weight: Optional[float] = Field(None, ge=0)
    dimensions: Optional[ProductDimensions] = None
    is_active: Optional[bool] = None
    track_inventory: Optional[bool] = None
    tax_exempt: Optional[bool] = None
    min_order_quantity: Optional[int] = Field(None, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)

class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    price: float
    cost: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[ProductDimensions] = None
    is_active: bool = True
    track_inventory: bool = True
    tax_exempt: bool = False
    min_order_quantity: int = 1
    max_order_quantity: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int = 1
    size: int = 50
    pages: int

class BulkProductCreateRequest(BaseModel):
    products: List[ProductCreateRequest]

class BulkProductCreateResponse(BaseModel):
    created: List[ProductResponse]
    errors: List[Dict[str, Any]]
    success_count: int
    error_count: int

class ProductCategoriesResponse(BaseModel):
    categories: List[str]

class CategoryStats(BaseModel):
    name: str
    count: int

class ProductStatisticsResponse(BaseModel):
    total_products: int
    active_products: int
    inactive_products: int
    categories: List[CategoryStats]
    average_price: float
    total_value: float

# In-memory storage for core business TDD (will be replaced with database)
products_store: Dict[str, Dict[str, Any]] = {}

@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Create a new product with advanced business attributes"""
    
    try:
        product_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    required_fields = ["name", "sku", "price"]
    for field in required_fields:
        if field not in product_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Validate price is positive (enhanced validation)
    if "price" in product_data and product_data["price"] <= 0:
        raise HTTPException(status_code=422, detail="Price must be positive")
    
    # Check for duplicate SKU
    sku = product_data["sku"]
    for existing_product in products_store.values():
        if existing_product["sku"] == sku:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{sku}' already exists"
            )
    
    # Create product with enhanced attributes
    product_id = str(uuid.uuid4())
    now = datetime.now()
    
    product = {
        "id": product_id,
        "name": product_data["name"],
        "sku": product_data["sku"],
        "price": float(product_data["price"]),
        "cost": product_data.get("cost"),
        "description": product_data.get("description"),
        "category": product_data.get("category"),
        "brand": product_data.get("brand"),
        "weight": product_data.get("weight"),
        "dimensions": product_data.get("dimensions"),
        "is_active": product_data.get("is_active", True),
        "track_inventory": product_data.get("track_inventory", True),
        "tax_exempt": product_data.get("tax_exempt", False),
        "min_order_quantity": product_data.get("min_order_quantity", 1),
        "max_order_quantity": product_data.get("max_order_quantity"),
        "created_at": now,
        "updated_at": now
    }
    
    products_store[product_id] = product
    return ProductResponse(**product)

@router.post("/bulk", response_model=BulkProductCreateResponse, status_code=201)
async def bulk_create_products(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> BulkProductCreateResponse:
    """Bulk create products with error handling"""
    
    try:
        bulk_data = await request.json()
        products_data = bulk_data.get("products", [])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    created_products = []
    errors = []
    
    for i, product_data in enumerate(products_data):
        try:
            # Validate required fields
            required_fields = ["name", "sku", "price"]
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check for duplicate SKU
            sku = product_data["sku"]
            for existing_product in products_store.values():
                if existing_product["sku"] == sku:
                    raise ValueError(f"Product with SKU '{sku}' already exists")
            
            # Create product
            product_id = str(uuid.uuid4())
            now = datetime.now()
            
            product = {
                "id": product_id,
                "name": product_data["name"],
                "sku": product_data["sku"],
                "price": float(product_data["price"]),
                "cost": product_data.get("cost"),
                "description": product_data.get("description"),
                "category": product_data.get("category"),
                "brand": product_data.get("brand"),
                "weight": product_data.get("weight"),
                "dimensions": product_data.get("dimensions"),
                "is_active": product_data.get("is_active", True),
                "track_inventory": product_data.get("track_inventory", True),
                "tax_exempt": product_data.get("tax_exempt", False),
                "min_order_quantity": product_data.get("min_order_quantity", 1),
                "max_order_quantity": product_data.get("max_order_quantity"),
                "created_at": now,
                "updated_at": now
            }
            
            products_store[product_id] = product
            created_products.append(ProductResponse(**product))
            
        except Exception as e:
            errors.append({
                "index": i,
                "product_data": product_data,
                "error": str(e)
            })
    
    success_count = len(created_products)
    error_count = len(errors)
    
    # Return appropriate status code based on results
    if error_count > 0 and success_count > 0:
        # Some succeeded, some failed - return 207 Multi-Status
        from fastapi.responses import JSONResponse
        response_data = BulkProductCreateResponse(
            created=created_products,
            errors=errors,
            success_count=success_count,
            error_count=error_count
        )
        return JSONResponse(
            status_code=207,
            content=response_data.model_dump(mode='json')
        )
    elif error_count > 0:
        # All failed
        raise HTTPException(status_code=400, detail={
            "message": "All products failed to create",
            "errors": errors
        })
    
    # All succeeded
    return BulkProductCreateResponse(
        created=created_products,
        errors=errors,
        success_count=success_count,
        error_count=error_count
    )

@router.get("/categories", response_model=ProductCategoriesResponse)
async def get_product_categories(
    db: AsyncSession = Depends(get_db)
) -> ProductCategoriesResponse:
    """Get all product categories"""
    
    categories = set()
    for product in products_store.values():
        if product.get("category"):
            categories.add(product["category"])
    
    return ProductCategoriesResponse(categories=list(categories))

@router.get("/statistics", response_model=ProductStatisticsResponse)
async def get_product_statistics(
    db: AsyncSession = Depends(get_db)
) -> ProductStatisticsResponse:
    """Get comprehensive product statistics"""
    
    all_products = list(products_store.values())
    total_products = len(all_products)
    active_products = len([p for p in all_products if p.get("is_active", True)])
    inactive_products = total_products - active_products
    
    # Category statistics
    category_counts = {}
    total_value = 0.0
    total_price = 0.0
    
    for product in all_products:
        category = product.get("category", "Uncategorized")
        category_counts[category] = category_counts.get(category, 0) + 1
        
        price = product.get("price", 0)
        total_price += price
        total_value += price
    
    categories = [
        CategoryStats(name=cat, count=count)
        for cat, count in category_counts.items()
    ]
    
    average_price = total_price / total_products if total_products > 0 else 0.0
    
    return ProductStatisticsResponse(
        total_products=total_products,
        active_products=active_products,
        inactive_products=inactive_products,
        categories=categories,
        average_price=round(average_price, 2),
        total_value=round(total_value, 2)
    )

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Get product by ID"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_store[product_id]
    return ProductResponse(**product)

@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> ProductListResponse:
    """List products with advanced filtering and search"""
    
    all_products = list(products_store.values())
    
    # Apply filters
    if search:
        search_lower = search.lower()
        all_products = [
            p for p in all_products
            if (search_lower in p["name"].lower() or 
                search_lower in p["sku"].lower() or
                (p.get("description") and search_lower in p["description"].lower()) or
                (p.get("category") and search_lower in p["category"].lower()))
        ]
    
    if category:
        all_products = [p for p in all_products if p.get("category") == category]
    
    if min_price is not None:
        all_products = [p for p in all_products if p["price"] >= min_price]
    
    if max_price is not None:
        all_products = [p for p in all_products if p["price"] <= max_price]
    
    if is_active is not None:
        all_products = [p for p in all_products if p.get("is_active", True) == is_active]
    
    # Sort by created_at descending
    all_products.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(all_products)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_products = all_products[start_idx:end_idx]
    
    # Convert to response format
    items = [ProductResponse(**product) for product in paginated_products]
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size  # Ceiling division
    )

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Update product information"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    product = products_store[product_id].copy()
    
    # Update fields (prevent updating immutable fields)
    immutable_fields = ["id", "sku", "created_at"]
    for field, value in update_data.items():
        if field not in immutable_fields:
            product[field] = value
    
    product["updated_at"] = datetime.now()
    products_store[product_id] = product
    
    return ProductResponse(**product)

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Soft delete product"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete - mark as inactive
    products_store[product_id]["is_active"] = False
    products_store[product_id]["updated_at"] = datetime.now()
    
    return {"message": "Product deleted successfully", "id": product_id}


# Health check endpoint for performance testing
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for core products API"""
    start_time = datetime.now()
    
    # Simulate some processing
    product_count = len(products_store)
    categories_count = len(set(p.get("category") for p in products_store.values() if p.get("category")))
    
    end_time = datetime.now()
    response_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "product_count": product_count,
        "categories_count": categories_count,
        "timestamp": start_time.isoformat()
    }