"""
Products API Endpoints - CC02 v49.0 Implementation Overdrive
48-Hour Backend Blitz - TDD-First Implementation
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal
import uuid
import asyncio
import json

# Import database and models (TDD implementation complete)
from app.core.database import get_db
from app.models.product import Product, ProductPriceHistory, ProductCategory
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    BulkProductCreate, BulkProductUpdate, ProductStatistics, PriceHistoryResponse
)

router = APIRouter(prefix="/products", tags=["Products"])

# Response models for TDD tests
class ProductCreateResponse(BaseModel):
    id: str
    name: str
    price: float
    sku: str
    category: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class ProductListItem(BaseModel):
    id: str
    name: str
    price: float
    sku: str
    category: Optional[str] = None
    is_active: bool = True
    created_at: datetime

class ProductListResponse(BaseModel):
    items: List[ProductListItem]
    total: int
    page: int
    size: int
    pages: int

class BulkCreateResponse(BaseModel):
    created: int
    failed: int
    details: List[Dict[str, Any]]

class BulkUpdateResponse(BaseModel):
    updated: int
    failed: int
    details: List[Dict[str, Any]]

class CategoryResponse(BaseModel):
    name: str
    count: int

class StatisticsResponse(BaseModel):
    total_products: int
    active_products: int
    inactive_products: int
    categories: List[CategoryResponse]
    average_price: float
    total_value: float

class PriceHistoryItem(BaseModel):
    price: float
    changed_at: datetime
    changed_by: Optional[str] = None

class PriceHistoryResponse(BaseModel):
    product_id: str
    history: List[PriceHistoryItem]

class InventoryResponse(BaseModel):
    total_stock: int
    available_stock: int
    reserved_stock: int
    locations: List[Dict[str, Any]]

# In-memory storage for TDD (will be replaced with database)
products_store: Dict[str, Dict[str, Any]] = {}
price_history_store: Dict[str, List[Dict[str, Any]]] = {}

@router.post("/", response_model=ProductCreateResponse, status_code=201)
async def create_product(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ProductCreateResponse:
    """Create a new product"""
    
    # Get JSON data from request
    try:
        product_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    # Validate required fields
    if "name" not in product_data or "price" not in product_data or "sku" not in product_data:
        raise HTTPException(status_code=422, detail="Missing required fields: name, price, sku")
    
    # Check for duplicate SKU
    for existing_product in products_store.values():
        if existing_product["sku"] == product_data["sku"]:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{product_data['sku']}' already exists"
            )
    
    # Create product
    product_id = str(uuid.uuid4())
    now = datetime.now()
    
    product = {
        "id": product_id,
        "name": product_data["name"],
        "price": float(product_data["price"]),
        "sku": product_data["sku"],
        "category": product_data.get("category"),
        "description": product_data.get("description"),
        "is_active": product_data.get("is_active", True),
        "created_at": now,
        "updated_at": now
    }
    
    products_store[product_id] = product
    
    # Initialize price history
    price_history_store[product_id] = [{
        "price": float(product_data["price"]),
        "changed_at": now,
        "changed_by": None
    }]
    
    return ProductCreateResponse(**product)

@router.get("/statistics", response_model=StatisticsResponse)
async def get_product_statistics(
    db: AsyncSession = Depends(get_db)
) -> StatisticsResponse:
    """Get product statistics"""
    
    all_products = list(products_store.values())
    total_products = len(all_products)
    active_products = len([p for p in all_products if p["is_active"]])
    inactive_products = total_products - active_products
    
    # Category breakdown
    category_counts = {}
    for product in all_products:
        if product.get("category"):
            category = product["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
    
    categories = [
        CategoryResponse(name=name, count=count)
        for name, count in sorted(category_counts.items())
    ]
    
    # Price statistics
    active_prices = [p["price"] for p in all_products if p["is_active"]]
    average_price = sum(active_prices) / len(active_prices) if active_prices else 0
    total_value = sum(active_prices)
    
    return StatisticsResponse(
        total_products=total_products,
        active_products=active_products,
        inactive_products=inactive_products,
        categories=categories,
        average_price=round(average_price, 2),
        total_value=round(total_value, 2)
    )

@router.get("/{product_id}", response_model=ProductCreateResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> ProductCreateResponse:
    """Get product by ID"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_store[product_id]
    return ProductCreateResponse(**product)

@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> ProductListResponse:
    """List products with pagination and filtering"""
    
    all_products = list(products_store.values())
    
    # Apply filters
    if search:
        search_lower = search.lower()
        all_products = [
            p for p in all_products
            if (search_lower in p["name"].lower() or 
                search_lower in p["sku"].lower() or
                (p.get("description") and search_lower in p["description"].lower()))
        ]
    
    if category:
        all_products = [p for p in all_products if p.get("category") == category]
    
    if is_active is not None:
        all_products = [p for p in all_products if p["is_active"] == is_active]
    
    # Sort by created_at descending
    all_products.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply pagination
    total = len(all_products)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_products = all_products[start_idx:end_idx]
    
    # Convert to response format
    items = [ProductListItem(**product) for product in paginated_products]
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size  # Ceiling division
    )

@router.put("/{product_id}", response_model=ProductCreateResponse)
async def update_product(
    product_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ProductCreateResponse:
    """Update product"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get JSON data from request
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    product = products_store[product_id].copy()
    old_price = product["price"]
    
    # Update fields
    for field, value in update_data.items():
        if field not in ["id", "created_at"]:  # Prevent updating immutable fields
            product[field] = value
    
    product["updated_at"] = datetime.now()
    products_store[product_id] = product
    
    # Track price changes
    if "price" in update_data and float(update_data["price"]) != old_price:
        if product_id not in price_history_store:
            price_history_store[product_id] = []
        
        price_history_store[product_id].append({
            "price": float(update_data["price"]),
            "changed_at": datetime.now(),
            "changed_by": None
        })
    
    return ProductCreateResponse(**product)

@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete product (soft delete)"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete
    products_store[product_id]["is_active"] = False
    products_store[product_id]["updated_at"] = datetime.now()
    
    return {"message": "Product deleted successfully", "id": product_id}

@router.post("/bulk", response_model=BulkCreateResponse, status_code=201)
async def bulk_create_products(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> BulkCreateResponse:
    """Bulk create products"""
    
    # Get JSON data from request
    try:
        bulk_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    products = bulk_data.get("products", [])
    created = 0
    failed = 0
    details = []
    
    for i, product_data in enumerate(products):
        try:
            # Check required fields
            if not all(field in product_data for field in ["name", "price", "sku"]):
                failed += 1
                details.append({
                    "index": i,
                    "error": "Missing required fields",
                    "data": product_data
                })
                continue
            
            # Check for duplicate SKU
            sku_exists = any(p["sku"] == product_data["sku"] for p in products_store.values())
            if sku_exists:
                failed += 1
                details.append({
                    "index": i,
                    "error": f"SKU '{product_data['sku']}' already exists",
                    "data": product_data
                })
                continue
            
            # Create product
            product_id = str(uuid.uuid4())
            now = datetime.now()
            
            product = {
                "id": product_id,
                "name": product_data["name"],
                "price": float(product_data["price"]),
                "sku": product_data["sku"],
                "category": product_data.get("category"),
                "description": product_data.get("description"),
                "is_active": product_data.get("is_active", True),
                "created_at": now,
                "updated_at": now
            }
            
            products_store[product_id] = product
            
            # Initialize price history
            price_history_store[product_id] = [{
                "price": float(product_data["price"]),
                "changed_at": now,
                "changed_by": None
            }]
            
            created += 1
            details.append({
                "index": i,
                "id": product_id,
                "status": "created"
            })
            
        except Exception as e:
            failed += 1
            details.append({
                "index": i,
                "error": str(e),
                "data": product_data
            })
    
    return BulkCreateResponse(created=created, failed=failed, details=details)

@router.put("/bulk", response_model=BulkUpdateResponse)
async def bulk_update_products(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> BulkUpdateResponse:
    """Bulk update products"""
    
    # Get JSON data from request
    try:
        bulk_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    
    updates = bulk_data.get("updates", [])
    updated = 0
    failed = 0
    details = []
    
    for i, update_data in enumerate(updates):
        try:
            product_id = update_data.get("id")
            if not product_id:
                failed += 1
                details.append({
                    "index": i,
                    "error": "Missing product ID",
                    "data": update_data
                })
                continue
            
            if product_id not in products_store:
                failed += 1
                details.append({
                    "index": i,
                    "error": "Product not found",
                    "data": update_data
                })
                continue
            
            # Update product
            product = products_store[product_id].copy()
            old_price = product["price"]
            
            for field, value in update_data.items():
                if field not in ["id", "created_at"]:
                    product[field] = value
            
            product["updated_at"] = datetime.now()
            products_store[product_id] = product
            
            # Track price changes
            if "price" in update_data and float(update_data["price"]) != old_price:
                if product_id not in price_history_store:
                    price_history_store[product_id] = []
                
                price_history_store[product_id].append({
                    "price": float(update_data["price"]),
                    "changed_at": datetime.now(),
                    "changed_by": None
                })
            
            updated += 1
            details.append({
                "index": i,
                "id": product_id,
                "status": "updated"
            })
            
        except Exception as e:
            failed += 1
            details.append({
                "index": i,
                "error": str(e),
                "data": update_data
            })
    
    return BulkUpdateResponse(updated=updated, failed=failed, details=details)

@router.get("/categories", response_model=List[CategoryResponse])
async def get_product_categories(
    db: AsyncSession = Depends(get_db)
) -> List[CategoryResponse]:
    """Get all product categories with counts"""
    
    category_counts = {}
    for product in products_store.values():
        if product.get("category"):
            category = product["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
    
    categories = [
        CategoryResponse(name=name, count=count)
        for name, count in sorted(category_counts.items())
    ]
    
    return categories

@router.get("/{product_id}/price-history", response_model=PriceHistoryResponse)
async def get_product_price_history(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> PriceHistoryResponse:
    """Get product price history"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    history = price_history_store.get(product_id, [])
    history_items = [PriceHistoryItem(**item) for item in history]
    
    return PriceHistoryResponse(
        product_id=product_id,
        history=history_items
    )

@router.get("/{product_id}/inventory", response_model=InventoryResponse)
async def get_product_inventory(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> InventoryResponse:
    """Get product inventory levels"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Mock inventory data (will be integrated with inventory system)
    return InventoryResponse(
        total_stock=100,
        available_stock=85,
        reserved_stock=15,
        locations=[
            {"location": "Warehouse A", "stock": 60},
            {"location": "Store B", "stock": 25},
            {"location": "Store C", "stock": 15}
        ]
    )

# Health check endpoint for performance testing
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check"""
    start_time = datetime.now()
    
    # Simulate some processing
    product_count = len(products_store)
    
    end_time = datetime.now()
    response_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "product_count": product_count,
        "timestamp": start_time.isoformat()
    }