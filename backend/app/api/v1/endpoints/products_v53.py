"""
CC02 v53.0 Products API Endpoints - Issue #568
10-Day ERP Business API Implementation Sprint - Day 1-2
Enhanced Product Management API Implementation
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import asyncio
import json
import time

# Import database and core dependencies
from app.core.database import get_db
from app.schemas.product_v53 import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CategoryCreate, CategoryResponse, BulkProductOperation, BulkOperationResult,
    ProductStatistics, ProductPriceHistory, ProductInventoryResponse,
    ProductSearchRequest, ProductAPIResponse, ProductError
)

# Create router
router = APIRouter(prefix="/products-v53", tags=["Products v53.0"])

# In-memory storage for TDD implementation (will be replaced with database)
products_store: Dict[str, Dict[str, Any]] = {}
categories_store: Dict[str, Dict[str, Any]] = {}
price_history_store: Dict[str, List[Dict[str, Any]]] = {}


# Category Management Endpoints
@router.post("/categories/", response_model=CategoryResponse, status_code=201)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db)
) -> CategoryResponse:
    """Create a new product category"""
    
    # Check for duplicate code
    for existing_category in categories_store.values():
        if existing_category["code"] == category_data.code:
            raise HTTPException(
                status_code=400,
                detail=f"Category with code '{category_data.code}' already exists"
            )
    
    # Create category
    category_id = str(uuid.uuid4())
    now = datetime.now()
    
    category = {
        "id": category_id,
        "name": category_data.name,
        "code": category_data.code,
        "description": category_data.description,
        "parent_id": category_data.parent_id,
        "is_active": category_data.is_active,
        "sort_order": category_data.sort_order,
        "created_at": now,
        "updated_at": now
    }
    
    categories_store[category_id] = category
    return CategoryResponse(**category)


@router.get("/categories/", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> List[CategoryResponse]:
    """List product categories with optional filtering"""
    
    categories = list(categories_store.values())
    
    # Apply filters
    if parent_id is not None:
        categories = [c for c in categories if c.get("parent_id") == parent_id]
    
    if is_active is not None:
        categories = [c for c in categories if c.get("is_active") == is_active]
    
    # Sort by sort_order, then name
    categories.sort(key=lambda x: (x.get("sort_order", 0), x.get("name", "")))
    
    return [CategoryResponse(**category) for category in categories]


# Core Product CRUD Endpoints
@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Create a new product with comprehensive validation"""
    
    # Check for duplicate SKU
    for existing_product in products_store.values():
        if existing_product["sku"] == product_data.sku:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )
    
    # Validate category if provided
    if product_data.category_id:
        if product_data.category_id not in categories_store:
            raise HTTPException(
                status_code=404,
                detail=f"Category with ID '{product_data.category_id}' not found"
            )
    
    # Create product
    product_id = str(uuid.uuid4())
    now = datetime.now()
    
    # Get category name for response
    category_name = None
    if product_data.category_id:
        category_name = categories_store[product_data.category_id]["name"]
    
    product = {
        "id": product_id,
        "name": product_data.name,
        "sku": product_data.sku,
        "description": product_data.description,
        "category_id": product_data.category_id,
        "category_name": category_name,
        "brand": product_data.brand,
        "model": product_data.model,
        "product_type": product_data.product_type.value,
        "price": float(product_data.price),
        "cost": float(product_data.cost) if product_data.cost else None,
        "currency": product_data.currency,
        "dimensions": product_data.dimensions.model_dump() if product_data.dimensions else None,
        "weight": float(product_data.weight) if product_data.weight else None,
        "color": product_data.color,
        "material": product_data.material,
        "unit_of_measure": product_data.unit_of_measure.value,
        "min_order_quantity": product_data.min_order_quantity,
        "max_order_quantity": product_data.max_order_quantity,
        "lead_time_days": product_data.lead_time_days,
        "track_inventory": product_data.track_inventory,
        "min_stock_level": product_data.min_stock_level,
        "max_stock_level": product_data.max_stock_level,
        "reorder_point": product_data.reorder_point,
        "current_stock": 0,  # Initial stock
        "status": product_data.status.value,
        "is_active": product_data.is_active,
        "is_featured": product_data.is_featured,
        "is_digital": product_data.is_digital,
        "warranty_months": product_data.warranty_months,
        "requires_shipping": product_data.requires_shipping,
        "is_taxable": product_data.is_taxable,
        "tax_category": product_data.tax_category,
        "barcode": product_data.barcode,
        "internal_code": product_data.internal_code,
        "manufacturer_code": product_data.manufacturer_code,
        "tags": product_data.tags,
        "attributes": product_data.attributes,
        "created_at": now,
        "updated_at": now
    }
    
    products_store[product_id] = product
    
    # Initialize price history
    price_history_store[product_id] = [{
        "price": float(product_data.price),
        "cost": float(product_data.cost) if product_data.cost else None,
        "changed_at": now,
        "changed_by": None,
        "reason": "Initial price"
    }]
    
    # Schedule background tasks
    background_tasks.add_task(log_product_creation, product_id)
    
    return ProductResponse(**product)


# Statistics and Analytics - Must be before {product_id} route
@router.get("/statistics", response_model=ProductStatistics)
async def get_product_statistics(
    category_id: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> ProductStatistics:
    """Get comprehensive product statistics"""
    
    start_time = time.time()
    
    all_products = list(products_store.values())
    
    # Filter by category if specified
    if category_id:
        all_products = [p for p in all_products if p.get("category_id") == category_id]
    
    # Filter active/inactive
    if not include_inactive:
        all_products = [p for p in all_products if p.get("is_active", True)]
    
    # Basic counts
    total_products = len(all_products)
    active_products = len([p for p in all_products if p.get("is_active", True)])
    inactive_products = total_products - active_products
    featured_products = len([p for p in all_products if p.get("is_featured", False)])
    digital_products = len([p for p in all_products if p.get("is_digital", False)])
    physical_products = total_products - digital_products
    
    # Price statistics
    prices = [p["price"] for p in all_products if p.get("price")]
    if prices:
        total_inventory_value = Decimal(str(sum(prices)))
        average_price = Decimal(str(sum(prices) / len(prices)))
        highest_price = Decimal(str(max(prices)))
        lowest_price = Decimal(str(min(prices)))
    else:
        total_inventory_value = Decimal("0")
        average_price = Decimal("0")
        highest_price = Decimal("0")
        lowest_price = Decimal("0")
    
    # Category breakdown
    category_stats = {}
    for product in all_products:
        category_id = product.get("category_id")
        category_name = product.get("category_name") or "Uncategorized"
        
        if category_name not in category_stats:
            category_stats[category_name] = {
                "category_id": category_id,
                "category_name": category_name,
                "product_count": 0,
                "total_value": Decimal("0"),
                "prices": []
            }
        
        category_stats[category_name]["product_count"] += 1
        category_stats[category_name]["total_value"] += Decimal(str(product["price"]))
        category_stats[category_name]["prices"].append(product["price"])
    
    # Convert to response format
    categories = []
    for cat_name, stats in category_stats.items():
        avg_price = stats["total_value"] / stats["product_count"] if stats["product_count"] > 0 else Decimal("0")
        categories.append({
            "category_id": stats["category_id"],
            "category_name": cat_name,
            "product_count": stats["product_count"],
            "total_value": stats["total_value"],
            "average_price": avg_price
        })
    
    # Stock statistics (mock data for now)
    out_of_stock_products = len([p for p in all_products if p.get("current_stock", 0) == 0])
    low_stock_products = len([
        p for p in all_products 
        if p.get("reorder_point") and p.get("current_stock", 0) <= p["reorder_point"]
    ])
    overstocked_products = len([
        p for p in all_products 
        if p.get("max_stock_level") and p.get("current_stock", 0) > p["max_stock_level"]
    ])
    
    end_time = time.time()
    calculation_time_ms = (end_time - start_time) * 1000
    
    return ProductStatistics(
        total_products=total_products,
        active_products=active_products,
        inactive_products=inactive_products,
        featured_products=featured_products,
        digital_products=digital_products,
        physical_products=physical_products,
        total_inventory_value=total_inventory_value,
        average_product_price=average_price,
        highest_price=highest_price,
        lowest_price=lowest_price,
        categories=categories,
        total_categories=len(categories),
        out_of_stock_products=out_of_stock_products,
        low_stock_products=low_stock_products,
        overstocked_products=overstocked_products,
        last_updated=datetime.now(),
        calculation_time_ms=calculation_time_ms
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    include_inventory: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Get product by ID with optional inventory information"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_store[product_id].copy()
    
    # Include current inventory if requested
    if include_inventory and product.get("track_inventory"):
        # Mock inventory data (will be integrated with inventory system)
        product["current_stock"] = 100  # Mock current stock
    
    return ProductResponse(**product)


@router.get("/", response_model=ProductListResponse)
async def list_products(
    # Search parameters
    search: Optional[str] = Query(None, description="Search in name, SKU, description"),
    category_id: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    
    # Price filters
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    
    # Stock filters
    in_stock_only: bool = Query(False),
    low_stock_only: bool = Query(False),
    
    # Feature filters
    is_active: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    is_digital: Optional[bool] = Query(None),
    
    # Tags filter
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    
    # Sorting
    sort_by: str = Query("created_at", pattern="^(name|price|created_at|updated_at|sku)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    db: AsyncSession = Depends(get_db)
) -> ProductListResponse:
    """List products with advanced filtering, searching, and pagination"""
    
    all_products = list(products_store.values())
    
    # Apply search
    if search:
        search_lower = search.lower()
        all_products = [
            p for p in all_products
            if (search_lower in p["name"].lower() or
                search_lower in p["sku"].lower() or
                (p.get("description") and search_lower in p["description"].lower()) or
                (p.get("brand") and search_lower in p["brand"].lower()))
        ]
    
    # Apply filters
    if category_id:
        all_products = [p for p in all_products if p.get("category_id") == category_id]
    
    if brand:
        all_products = [p for p in all_products if p.get("brand") == brand]
    
    if product_type:
        all_products = [p for p in all_products if p.get("product_type") == product_type]
    
    if status:
        all_products = [p for p in all_products if p.get("status") == status]
    
    if min_price is not None:
        all_products = [p for p in all_products if p["price"] >= min_price]
    
    if max_price is not None:
        all_products = [p for p in all_products if p["price"] <= max_price]
    
    if in_stock_only:
        all_products = [p for p in all_products if p.get("current_stock", 0) > 0]
    
    if low_stock_only:
        all_products = [
            p for p in all_products 
            if p.get("reorder_point") and p.get("current_stock", 0) <= p["reorder_point"]
        ]
    
    if is_active is not None:
        all_products = [p for p in all_products if p.get("is_active") == is_active]
    
    if is_featured is not None:
        all_products = [p for p in all_products if p.get("is_featured") == is_featured]
    
    if is_digital is not None:
        all_products = [p for p in all_products if p.get("is_digital") == is_digital]
    
    # Tags filter
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        all_products = [
            p for p in all_products
            if any(tag in p.get("tags", []) for tag in tag_list)
        ]
    
    # Apply sorting
    reverse = (sort_order == "desc")
    if sort_by == "name":
        all_products.sort(key=lambda x: x.get("name", ""), reverse=reverse)
    elif sort_by == "price":
        all_products.sort(key=lambda x: x.get("price", 0), reverse=reverse)
    elif sort_by == "sku":
        all_products.sort(key=lambda x: x.get("sku", ""), reverse=reverse)
    elif sort_by == "updated_at":
        all_products.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=reverse)
    else:  # created_at
        all_products.sort(key=lambda x: x.get("created_at", datetime.min), reverse=reverse)
    
    # Apply pagination
    total = len(all_products)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_products = all_products[start_idx:end_idx]
    
    # Convert to response format
    items = [ProductResponse(**product) for product in paginated_products]
    
    # Build filters applied dictionary
    filters_applied = {}
    if search: filters_applied["search"] = search
    if category_id: filters_applied["category_id"] = category_id
    if brand: filters_applied["brand"] = brand
    if min_price is not None: filters_applied["min_price"] = min_price
    if max_price is not None: filters_applied["max_price"] = max_price
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
        filters_applied=filters_applied
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Update product with comprehensive validation and price history tracking"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_store[product_id].copy()
    old_price = product["price"]
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ["id", "sku", "created_at"]:  # Prevent updating immutable fields
            if field == "dimensions" and value:
                product[field] = value
            elif field in ["price", "cost", "weight"]:
                product[field] = float(value) if value is not None else None
            elif field in ["product_type", "unit_of_measure", "status"]:
                product[field] = value.value if value is not None else None
            else:
                product[field] = value
    
    product["updated_at"] = datetime.now()
    
    # Validate category if updated
    if "category_id" in update_data and update_data["category_id"]:
        if update_data["category_id"] not in categories_store:
            raise HTTPException(
                status_code=404,
                detail=f"Category with ID '{update_data['category_id']}' not found"
            )
        product["category_name"] = categories_store[update_data["category_id"]]["name"]
    
    products_store[product_id] = product
    
    # Track price changes
    if "price" in update_data and float(update_data["price"]) != old_price:
        if product_id not in price_history_store:
            price_history_store[product_id] = []
        
        price_history_store[product_id].append({
            "price": float(update_data["price"]),
            "cost": float(update_data.get("cost")) if update_data.get("cost") else None,
            "changed_at": datetime.now(),
            "changed_by": None,  # Will be populated with user info when auth is implemented
            "reason": "Price update"
        })
        
        # Schedule price change notification
        background_tasks.add_task(notify_price_change, product_id, old_price, float(update_data["price"]))
    
    return ProductResponse(**product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    hard_delete: bool = Query(False, description="Permanently delete the product"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Delete product (soft delete by default, hard delete if specified)"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if hard_delete:
        # Hard delete - remove from storage
        del products_store[product_id]
        if product_id in price_history_store:
            del price_history_store[product_id]
        return {"message": "Product permanently deleted", "id": product_id}
    else:
        # Soft delete - mark as inactive
        products_store[product_id]["is_active"] = False
        products_store[product_id]["status"] = "inactive"
        products_store[product_id]["updated_at"] = datetime.now()
        return {"message": "Product deactivated", "id": product_id}


# Bulk Operations
@router.post("/bulk", response_model=BulkOperationResult, status_code=201)
async def bulk_create_products(
    bulk_operation: BulkProductOperation,
    db: AsyncSession = Depends(get_db)
) -> BulkOperationResult:
    """Bulk create products with detailed result tracking"""
    
    start_time = time.time()
    
    created_items = []
    failed_items = []
    
    for i, product_data in enumerate(bulk_operation.products):
        try:
            # Validate and create product
            if bulk_operation.validate_only:
                # Just validate without creating
                continue
            
            # Check for duplicate SKU
            sku_exists = any(p["sku"] == product_data.sku for p in products_store.values())
            if sku_exists and not bulk_operation.stop_on_error:
                failed_items.append({
                    "index": i,
                    "sku": product_data.sku,
                    "error": f"SKU '{product_data.sku}' already exists",
                    "data": product_data.model_dump()
                })
                continue
            elif sku_exists and bulk_operation.stop_on_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Bulk operation stopped: SKU '{product_data.sku}' already exists at index {i}"
                )
            
            # Create product (similar to single create logic)
            product_id = str(uuid.uuid4())
            now = datetime.now()
            
            category_name = None
            if product_data.category_id and product_data.category_id in categories_store:
                category_name = categories_store[product_data.category_id]["name"]
            
            product = {
                "id": product_id,
                "name": product_data.name,
                "sku": product_data.sku,
                "description": product_data.description,
                "category_id": product_data.category_id,
                "category_name": category_name,
                "brand": product_data.brand,
                "model": product_data.model,
                "product_type": product_data.product_type.value,
                "price": float(product_data.price),
                "cost": float(product_data.cost) if product_data.cost else None,
                "currency": product_data.currency,
                "dimensions": product_data.dimensions.model_dump() if product_data.dimensions else None,
                "weight": float(product_data.weight) if product_data.weight else None,
                "color": product_data.color,
                "material": product_data.material,
                "unit_of_measure": product_data.unit_of_measure.value,
                "min_order_quantity": product_data.min_order_quantity,
                "max_order_quantity": product_data.max_order_quantity,
                "lead_time_days": product_data.lead_time_days,
                "track_inventory": product_data.track_inventory,
                "min_stock_level": product_data.min_stock_level,
                "max_stock_level": product_data.max_stock_level,
                "reorder_point": product_data.reorder_point,
                "current_stock": 0,
                "status": product_data.status.value,
                "is_active": product_data.is_active,
                "is_featured": product_data.is_featured,
                "is_digital": product_data.is_digital,
                "warranty_months": product_data.warranty_months,
                "requires_shipping": product_data.requires_shipping,
                "is_taxable": product_data.is_taxable,
                "tax_category": product_data.tax_category,
                "barcode": product_data.barcode,
                "internal_code": product_data.internal_code,
                "manufacturer_code": product_data.manufacturer_code,
                "tags": product_data.tags,
                "attributes": product_data.attributes,
                "created_at": now,
                "updated_at": now
            }
            
            products_store[product_id] = product
            
            # Initialize price history
            price_history_store[product_id] = [{
                "price": float(product_data.price),
                "cost": float(product_data.cost) if product_data.cost else None,
                "changed_at": now,
                "changed_by": None,
                "reason": "Initial price (bulk)"
            }]
            
            created_items.append(ProductResponse(**product))
            
        except Exception as e:
            failed_items.append({
                "index": i,
                "sku": product_data.sku if hasattr(product_data, 'sku') else None,
                "error": str(e),
                "data": product_data.model_dump()
            })
            
            if bulk_operation.stop_on_error:
                break
    
    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000
    
    result = BulkOperationResult(
        created_count=len(created_items),
        failed_count=len(failed_items),
        created_items=created_items,
        failed_items=failed_items,
        execution_time_ms=execution_time_ms
    )
    
    # Return appropriate status code
    if len(failed_items) > 0 and len(created_items) > 0:
        # Partial success
        return JSONResponse(status_code=207, content=result.model_dump())
    elif len(failed_items) > 0:
        # All failed
        raise HTTPException(status_code=400, detail=result.model_dump())
    
    return result




# Price History
@router.get("/{product_id}/price-history", response_model=ProductPriceHistory)
async def get_product_price_history(
    product_id: str,
    limit: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> ProductPriceHistory:
    """Get product price history"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_store[product_id]
    history = price_history_store.get(product_id, [])
    
    # Sort by date descending and apply limit
    history_sorted = sorted(history, key=lambda x: x["changed_at"], reverse=True)[:limit]
    
    return ProductPriceHistory(
        product_id=product_id,
        product_name=product["name"],
        current_price=Decimal(str(product["price"])),
        price_changes=history_sorted,
        total_changes=len(history)
    )


# Inventory Integration
@router.get("/{product_id}/inventory", response_model=ProductInventoryResponse)
async def get_product_inventory(
    product_id: str,
    db: AsyncSession = Depends(get_db)
) -> ProductInventoryResponse:
    """Get product inventory information"""
    
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Mock inventory data (will be integrated with inventory system)
    mock_inventory = {
        "product_id": product_id,
        "total_stock": 100,
        "available_stock": 85,
        "reserved_stock": 15,
        "locations": [
            {"location_id": "WH001", "location_name": "Main Warehouse", "stock": 60},
            {"location_id": "ST001", "location_name": "Store 1", "stock": 25},
            {"location_id": "ST002", "location_name": "Store 2", "stock": 15}
        ],
        "movements": [
            {"type": "inbound", "quantity": 50, "date": datetime.now().isoformat()},
            {"type": "outbound", "quantity": -25, "date": (datetime.now() - timedelta(days=1)).isoformat()}
        ],
        "last_updated": datetime.now()
    }
    
    return ProductInventoryResponse(**mock_inventory)


# Performance and Health Endpoints
@router.get("/health/performance")
async def performance_check() -> Dict[str, Any]:
    """Performance health check for products API"""
    start_time = time.time()
    
    # Simulate some processing
    product_count = len(products_store)
    category_count = len(categories_store)
    
    end_time = time.time()
    response_time_ms = (end_time - start_time) * 1000
    
    return {
        "status": "healthy",
        "response_time_ms": round(response_time_ms, 3),
        "product_count": product_count,
        "category_count": category_count,
        "memory_usage": "simulated",
        "timestamp": datetime.now().isoformat(),
        "version": "v53.0"
    }


# Background Tasks
async def log_product_creation(product_id: str):
    """Background task to log product creation"""
    # Mock logging (will be replaced with actual logging system)
    print(f"Product created: {product_id} at {datetime.now()}")


async def notify_price_change(product_id: str, old_price: float, new_price: float):
    """Background task to notify about price changes"""
    # Mock notification (will be replaced with actual notification system)
    print(f"Price changed for product {product_id}: {old_price} -> {new_price}")