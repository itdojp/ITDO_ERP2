"""
Advanced Product Management API - CC02 v48.0
Complete CRUD operations with advanced search, filtering, pagination, and business features
Test-driven implementation with comprehensive validation
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from decimal import Decimal
import uuid
import json
import csv
import io
from enum import Enum

# Import existing stores for compatibility
from app.api.v1.simple_products import products_store

router = APIRouter(prefix="/products", tags=["Advanced Product Management"])

# Enhanced models for advanced features
class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    DRAFT = "draft"

class ProductType(str, Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    BUNDLE = "bundle"

class ProductAdvanced(BaseModel):
    """Advanced product model with extended attributes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., min_length=1, max_length=50, description="Unique product code")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    short_description: Optional[str] = Field(None, max_length=500, description="Short description")
    price: Decimal = Field(..., gt=0, description="Product price")
    cost_price: Optional[Decimal] = Field(None, ge=0, description="Cost price")
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Product subcategory")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    manufacturer: Optional[str] = Field(None, max_length=200, description="Manufacturer")
    product_type: ProductType = Field(default=ProductType.PHYSICAL, description="Product type")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Product status")
    weight: Optional[Decimal] = Field(None, ge=0, description="Product weight in kg")
    dimensions: Optional[Dict[str, Decimal]] = Field(None, description="Dimensions (length, width, height)")
    color: Optional[str] = Field(None, max_length=50, description="Product color")
    size: Optional[str] = Field(None, max_length=50, description="Product size")
    material: Optional[str] = Field(None, max_length=100, description="Product material")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    image_urls: List[str] = Field(default_factory=list, description="Product image URLs")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    warranty_period: Optional[int] = Field(None, ge=0, description="Warranty period in months")
    min_order_quantity: Optional[int] = Field(None, ge=1, description="Minimum order quantity")
    max_order_quantity: Optional[int] = Field(None, ge=1, description="Maximum order quantity")
    reorder_point: Optional[int] = Field(None, ge=0, description="Reorder point")
    is_featured: bool = Field(default=False, description="Featured product flag")
    is_digital_download: bool = Field(default=False, description="Digital download flag")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")

    @field_validator('dimensions')
    @classmethod
    def validate_dimensions(cls, v):
        if v is not None:
            required_keys = {'length', 'width', 'height'}
            if not all(key in v for key in required_keys):
                raise ValueError('Dimensions must include length, width, and height')
            if not all(isinstance(val, (int, float, Decimal)) and val >= 0 for val in v.values()):
                raise ValueError('All dimension values must be non-negative numbers')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return [tag.strip().lower() for tag in v if tag.strip()]

class ProductCreate(BaseModel):
    """Schema for creating advanced products"""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    short_description: Optional[str] = Field(None, max_length=500)
    price: Decimal = Field(..., gt=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    product_type: ProductType = Field(default=ProductType.PHYSICAL)
    status: ProductStatus = Field(default=ProductStatus.ACTIVE)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Decimal]] = None
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    warranty_period: Optional[int] = Field(None, ge=0)
    min_order_quantity: Optional[int] = Field(None, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)
    reorder_point: Optional[int] = Field(None, ge=0)
    is_featured: bool = Field(default=False)
    is_digital_download: bool = Field(default=False)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class ProductUpdate(BaseModel):
    """Schema for updating products with optional fields"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    short_description: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, gt=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    product_type: Optional[ProductType] = None
    status: Optional[ProductStatus] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Decimal]] = None
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    warranty_period: Optional[int] = Field(None, ge=0)
    min_order_quantity: Optional[int] = Field(None, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)
    reorder_point: Optional[int] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    is_digital_download: Optional[bool] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    custom_fields: Optional[Dict[str, Any]] = None

class ProductSearchFilters(BaseModel):
    """Advanced search filters for products"""
    search: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    product_type: Optional[ProductType] = None
    status: Optional[ProductStatus] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    weight_min: Optional[Decimal] = None
    weight_max: Optional[Decimal] = None
    tags: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    has_images: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# Enhanced storage with advanced features
advanced_products_store: Dict[str, Dict[str, Any]] = {}

# Helper functions
def convert_legacy_to_advanced(legacy_product: Dict[str, Any]) -> ProductAdvanced:
    """Convert legacy simple product to advanced product format"""
    return ProductAdvanced(
        id=legacy_product.get("id", str(uuid.uuid4())),
        code=legacy_product["code"],
        name=legacy_product["name"],
        description=legacy_product.get("description"),
        price=Decimal(str(legacy_product["price"])),
        category=legacy_product.get("category"),
        status=ProductStatus.ACTIVE if legacy_product.get("is_active", True) else ProductStatus.INACTIVE,
        created_at=datetime.fromisoformat(legacy_product.get("created_at", datetime.now().isoformat())),
        updated_at=datetime.fromisoformat(legacy_product.get("updated_at", datetime.now().isoformat()))
    )

def apply_search_filters(products: List[Dict[str, Any]], filters: ProductSearchFilters) -> List[Dict[str, Any]]:
    """Apply advanced search filters to product list"""
    filtered_products = products.copy()
    
    if filters.search:
        search_lower = filters.search.lower()
        filtered_products = [
            p for p in filtered_products
            if (search_lower in p["name"].lower() or
                search_lower in p["code"].lower() or
                (p.get("description") and search_lower in p["description"].lower()) or
                (p.get("sku") and search_lower in p["sku"].lower()) or
                (p.get("barcode") and search_lower in p["barcode"].lower()))
        ]
    
    if filters.category:
        filtered_products = [p for p in filtered_products if p.get("category") == filters.category]
    
    if filters.subcategory:
        filtered_products = [p for p in filtered_products if p.get("subcategory") == filters.subcategory]
    
    if filters.brand:
        filtered_products = [p for p in filtered_products if p.get("brand") == filters.brand]
    
    if filters.manufacturer:
        filtered_products = [p for p in filtered_products if p.get("manufacturer") == filters.manufacturer]
    
    if filters.product_type:
        filtered_products = [p for p in filtered_products if p.get("product_type") == filters.product_type]
    
    if filters.status:
        filtered_products = [p for p in filtered_products if p.get("status") == filters.status]
    
    if filters.price_min is not None:
        filtered_products = [p for p in filtered_products if Decimal(str(p["price"])) >= filters.price_min]
    
    if filters.price_max is not None:
        filtered_products = [p for p in filtered_products if Decimal(str(p["price"])) <= filters.price_max]
    
    if filters.is_featured is not None:
        filtered_products = [p for p in filtered_products if p.get("is_featured", False) == filters.is_featured]
    
    if filters.has_images is not None:
        if filters.has_images:
            filtered_products = [p for p in filtered_products if p.get("image_urls") and len(p["image_urls"]) > 0]
        else:
            filtered_products = [p for p in filtered_products if not p.get("image_urls") or len(p["image_urls"]) == 0]
    
    if filters.tags:
        for tag in filters.tags:
            filtered_products = [p for p in filtered_products if tag.lower() in [t.lower() for t in p.get("tags", [])]]
    
    return filtered_products

# API Endpoints

@router.post("/", response_model=ProductAdvanced)
async def create_advanced_product(product_data: ProductCreate) -> ProductAdvanced:
    """Create a new advanced product with comprehensive validation"""
    
    # Check for duplicate code in both stores
    all_products = {**products_store, **advanced_products_store}
    for existing_product in all_products.values():
        if existing_product["code"] == product_data.code:
            raise HTTPException(
                status_code=400,
                detail=f"Product with code '{product_data.code}' already exists"
            )
    
    # Check for duplicate SKU if provided
    if product_data.sku:
        for existing_product in advanced_products_store.values():
            if existing_product.get("sku") == product_data.sku:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product with SKU '{product_data.sku}' already exists"
                )
    
    # Check for duplicate barcode if provided
    if product_data.barcode:
        for existing_product in advanced_products_store.values():
            if existing_product.get("barcode") == product_data.barcode:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product with barcode '{product_data.barcode}' already exists"
                )
    
    # Create advanced product
    product = ProductAdvanced(**product_data.dict())
    
    # Store in advanced products store
    advanced_products_store[product.id] = product.dict()
    
    return product

@router.get("/", response_model=List[ProductAdvanced])
async def list_advanced_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    product_type: Optional[ProductType] = Query(None, description="Filter by product type"),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    price_min: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    price_max: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured flag"),
    has_images: Optional[bool] = Query(None, description="Filter by image presence"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order")
) -> List[ProductAdvanced]:
    """List products with advanced filtering, search, and pagination"""
    
    # Combine legacy and advanced products
    all_products = []
    
    # Add legacy products (converted to advanced format)
    for legacy_product in products_store.values():
        if legacy_product.get("is_active", True):  # Only include active legacy products
            all_products.append(convert_legacy_to_advanced(legacy_product).dict())
    
    # Add advanced products
    all_products.extend(list(advanced_products_store.values()))
    
    # Parse tags if provided
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Apply filters
    filters = ProductSearchFilters(
        search=search,
        category=category,
        subcategory=subcategory,
        brand=brand,
        manufacturer=manufacturer,
        product_type=product_type,
        status=status,
        price_min=price_min,
        price_max=price_max,
        is_featured=is_featured,
        has_images=has_images,
        tags=tag_list if tag_list else None
    )
    
    filtered_products = apply_search_filters(all_products, filters)
    
    # Sort products
    reverse_order = sort_order == "desc"
    try:
        if sort_by == "price":
            filtered_products.sort(key=lambda x: Decimal(str(x.get("price", 0))), reverse=reverse_order)
        elif sort_by == "created_at":
            filtered_products.sort(key=lambda x: datetime.fromisoformat(x.get("created_at", datetime.now().isoformat())), reverse=reverse_order)
        elif sort_by == "updated_at":
            filtered_products.sort(key=lambda x: datetime.fromisoformat(x.get("updated_at", datetime.now().isoformat())), reverse=reverse_order)
        else:
            filtered_products.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse_order)
    except (ValueError, TypeError):
        # Fallback to name sorting if sort_by field is invalid
        filtered_products.sort(key=lambda x: x.get("name", ""), reverse=reverse_order)
    
    # Apply pagination
    paginated_products = filtered_products[skip:skip + limit]
    
    return [ProductAdvanced(**product_data) for product_data in paginated_products]

@router.get("/{product_id}", response_model=ProductAdvanced)
async def get_advanced_product(product_id: str) -> ProductAdvanced:
    """Get product by ID from both advanced and legacy stores"""
    
    # Check advanced products first
    if product_id in advanced_products_store:
        product_data = advanced_products_store[product_id]
        return ProductAdvanced(**product_data)
    
    # Check legacy products
    if product_id in products_store:
        legacy_product = products_store[product_id]
        return convert_legacy_to_advanced(legacy_product)
    
    raise HTTPException(status_code=404, detail="Product not found")

@router.put("/{product_id}", response_model=ProductAdvanced)
async def update_advanced_product(product_id: str, product_data: ProductUpdate) -> ProductAdvanced:
    """Update advanced product information"""
    
    # Find product in advanced store
    if product_id not in advanced_products_store:
        # Check if it's a legacy product that needs to be migrated
        if product_id in products_store:
            # Migrate legacy product to advanced store
            legacy_product = products_store[product_id]
            advanced_product = convert_legacy_to_advanced(legacy_product)
            advanced_products_store[product_id] = advanced_product.dict()
            # Remove from legacy store
            del products_store[product_id]
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    
    # Get existing product
    existing_product = advanced_products_store[product_id].copy()
    
    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            existing_product[field] = value
    
    # Update timestamp
    existing_product["updated_at"] = datetime.now()
    
    # Save updated product
    advanced_products_store[product_id] = existing_product
    
    return ProductAdvanced(**existing_product)

@router.delete("/{product_id}")
async def delete_advanced_product(product_id: str) -> Dict[str, str]:
    """Delete (deactivate) advanced product"""
    
    # Check advanced products
    if product_id in advanced_products_store:
        advanced_products_store[product_id]["status"] = ProductStatus.INACTIVE
        advanced_products_store[product_id]["updated_at"] = datetime.now()
        return {"message": "Product deactivated successfully", "product_id": product_id}
    
    # Check legacy products
    if product_id in products_store:
        products_store[product_id]["is_active"] = False
        products_store[product_id]["updated_at"] = datetime.now()
        return {"message": "Product deactivated successfully", "product_id": product_id}
    
    raise HTTPException(status_code=404, detail="Product not found")

@router.get("/code/{product_code}", response_model=ProductAdvanced)
async def get_product_by_code(product_code: str) -> ProductAdvanced:
    """Get product by code from both stores"""
    
    # Check advanced products
    for product_data in advanced_products_store.values():
        if product_data["code"] == product_code and product_data.get("status") != ProductStatus.INACTIVE:
            return ProductAdvanced(**product_data)
    
    # Check legacy products
    for product_data in products_store.values():
        if product_data["code"] == product_code and product_data.get("is_active", True):
            return convert_legacy_to_advanced(product_data)
    
    raise HTTPException(status_code=404, detail=f"Product with code '{product_code}' not found")

@router.get("/sku/{sku}", response_model=ProductAdvanced)
async def get_product_by_sku(sku: str) -> ProductAdvanced:
    """Get product by SKU"""
    
    for product_data in advanced_products_store.values():
        if product_data.get("sku") == sku and product_data.get("status") != ProductStatus.INACTIVE:
            return ProductAdvanced(**product_data)
    
    raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")

@router.get("/barcode/{barcode}", response_model=ProductAdvanced)
async def get_product_by_barcode(barcode: str) -> ProductAdvanced:
    """Get product by barcode"""
    
    for product_data in advanced_products_store.values():
        if product_data.get("barcode") == barcode and product_data.get("status") != ProductStatus.INACTIVE:
            return ProductAdvanced(**product_data)
    
    raise HTTPException(status_code=404, detail=f"Product with barcode '{barcode}' not found")

@router.post("/bulk/create", response_model=List[ProductAdvanced])
async def bulk_create_advanced_products(products: List[ProductCreate]) -> List[ProductAdvanced]:
    """Bulk create advanced products with validation"""
    
    created_products = []
    errors = []
    
    # Check for duplicates within the batch
    codes_in_batch = set()
    skus_in_batch = set()
    barcodes_in_batch = set()
    
    for i, product_data in enumerate(products):
        # Check for duplicates within batch
        if product_data.code in codes_in_batch:
            errors.append(f"Product {i+1}: Duplicate code '{product_data.code}' in batch")
            continue
        codes_in_batch.add(product_data.code)
        
        if product_data.sku:
            if product_data.sku in skus_in_batch:
                errors.append(f"Product {i+1}: Duplicate SKU '{product_data.sku}' in batch")
                continue
            skus_in_batch.add(product_data.sku)
        
        if product_data.barcode:
            if product_data.barcode in barcodes_in_batch:
                errors.append(f"Product {i+1}: Duplicate barcode '{product_data.barcode}' in batch")
                continue
            barcodes_in_batch.add(product_data.barcode)
        
        try:
            # Check for existing products
            all_products = {**products_store, **advanced_products_store}
            
            # Check code uniqueness
            code_exists = any(existing["code"] == product_data.code for existing in all_products.values())
            if code_exists:
                errors.append(f"Product {i+1}: Code '{product_data.code}' already exists")
                continue
            
            # Check SKU uniqueness
            if product_data.sku:
                sku_exists = any(existing.get("sku") == product_data.sku for existing in advanced_products_store.values())
                if sku_exists:
                    errors.append(f"Product {i+1}: SKU '{product_data.sku}' already exists")
                    continue
            
            # Check barcode uniqueness
            if product_data.barcode:
                barcode_exists = any(existing.get("barcode") == product_data.barcode for existing in advanced_products_store.values())
                if barcode_exists:
                    errors.append(f"Product {i+1}: Barcode '{product_data.barcode}' already exists")
                    continue
            
            # Create product
            product = ProductAdvanced(**product_data.dict())
            advanced_products_store[product.id] = product.dict()
            created_products.append(product)
            
        except Exception as e:
            errors.append(f"Product {i+1}: {str(e)}")
    
    if errors and not created_products:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    return created_products

# Test utility endpoint for clearing data
@router.delete("/test/clear-all")
async def clear_all_products_for_testing():
    """Clear all products for testing purposes - DO NOT USE IN PRODUCTION"""
    products_store.clear()
    advanced_products_store.clear()
    return {"message": "All products cleared for testing"}

@router.get("/stats/advanced-summary")
async def get_advanced_product_statistics() -> Dict[str, Any]:
    """Get comprehensive product statistics"""
    
    # Combine all products
    all_products = []
    
    # Legacy products
    for legacy_product in products_store.values():
        all_products.append({
            "status": "active" if legacy_product.get("is_active", True) else "inactive",
            "category": legacy_product.get("category", "Uncategorized"),
            "price": Decimal(str(legacy_product["price"])),
            "product_type": "physical",  # Default for legacy
            "is_featured": False,  # Default for legacy
            "created_at": legacy_product.get("created_at", datetime.now().isoformat())
        })
    
    # Advanced products
    for advanced_product in advanced_products_store.values():
        all_products.append({
            "status": advanced_product.get("status", "active"),
            "category": advanced_product.get("category", "Uncategorized"),
            "price": Decimal(str(advanced_product["price"])),
            "product_type": advanced_product.get("product_type", "physical"),
            "is_featured": advanced_product.get("is_featured", False),
            "created_at": advanced_product.get("created_at", datetime.now().isoformat())
        })
    
    # Calculate statistics
    total_products = len(all_products)
    active_products = len([p for p in all_products if p["status"] == "active"])
    inactive_products = total_products - active_products
    
    # Category breakdown
    categories = {}
    for product in all_products:
        category = product["category"]
        categories[category] = categories.get(category, 0) + 1
    
    # Product type breakdown
    product_types = {}
    for product in all_products:
        ptype = product["product_type"]
        product_types[ptype] = product_types.get(ptype, 0) + 1
    
    # Featured products
    featured_count = len([p for p in all_products if p["is_featured"]])
    
    # Price statistics
    prices = [p["price"] for p in all_products if p["status"] == "active"]
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "inactive_products": inactive_products,
        "featured_products": featured_count,
        "categories_breakdown": categories,
        "product_types_breakdown": product_types,
        "price_statistics": {
            "average_price": float(avg_price),
            "minimum_price": float(min_price),
            "maximum_price": float(max_price)
        },
        "last_updated": datetime.now().isoformat()
    }