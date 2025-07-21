"""Inventory management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.monitoring import monitor_performance
from app.models.user import User
from app.schemas.inventory import (
    Category, CategoryCreate, CategoryUpdate, CategoryWithChildren,
    Product, ProductCreate, ProductUpdate, ProductWithCategory,
    StockMovement, StockMovementCreate,
    ProductSerial, ProductSerialCreate, ProductSerialUpdate,
    InventoryLocation, InventoryLocationCreate, InventoryLocationUpdate,
    InventoryReport, ProductStockSummary,
    StockMovementFilters, ProductFilters
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory", "stock-management"])


# Category Management
@router.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
@monitor_performance("api.inventory.create_category")
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product category."""
    inventory_service = InventoryService(db)
    
    try:
        category = await inventory_service.create_category(
            data=category_data,
            organization_id=current_user.organization_id
        )
        return category
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/categories", response_model=List[CategoryWithChildren])
@monitor_performance("api.inventory.get_categories")
async def get_categories(
    include_children: bool = Query(False, description="Include child categories"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all product categories."""
    inventory_service = InventoryService(db)
    
    categories = await inventory_service.get_categories(
        organization_id=current_user.organization_id,
        include_children=include_children
    )
    return categories


@router.get("/categories/{category_id}", response_model=Category)
@monitor_performance("api.inventory.get_category")
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific category by ID."""
    inventory_service = InventoryService(db)
    
    category = await inventory_service._get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check organization access
    if (category.organization_id and 
        category.organization_id != current_user.organization_id and
        not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return category


# Product Management
@router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
@monitor_performance("api.inventory.create_product")
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product."""
    inventory_service = InventoryService(db)
    
    try:
        product = await inventory_service.create_product(
            data=product_data,
            organization_id=current_user.organization_id
        )
        return product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/products", response_model=List[ProductWithCategory])
@monitor_performance("api.inventory.get_products")
async def get_products(
    category_id: Optional[int] = Query(None, description="Filter by category"),
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    barcode: Optional[str] = Query(None, description="Filter by barcode"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    low_stock: Optional[bool] = Query(None, description="Show low stock products"),
    out_of_stock: Optional[bool] = Query(None, description="Show out of stock products"),
    search: Optional[str] = Query(None, description="Search in name, SKU, description"),
    limit: Optional[int] = Query(100, description="Limit results", le=1000),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products with filtering and pagination."""
    inventory_service = InventoryService(db)
    
    filters = ProductFilters(
        category_id=category_id,
        sku=sku,
        barcode=barcode,
        is_active=is_active,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        search=search
    )
    
    products = await inventory_service.get_products(
        filters=filters,
        organization_id=current_user.organization_id,
        limit=limit,
        offset=offset
    )
    return products


@router.get("/products/{product_id}", response_model=ProductWithCategory)
@monitor_performance("api.inventory.get_product")
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific product by ID."""
    inventory_service = InventoryService(db)
    
    product = await inventory_service.get_by_id(
        product_id, 
        organization_id=current_user.organization_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.put("/products/{product_id}", response_model=Product)
@monitor_performance("api.inventory.update_product")
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a product."""
    inventory_service = InventoryService(db)
    
    try:
        product = await inventory_service.update_product(
            product_id=product_id,
            data=product_data,
            organization_id=current_user.organization_id
        )
        return product
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
@monitor_performance("api.inventory.delete_product")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a product (soft delete by setting is_active=False)."""
    inventory_service = InventoryService(db)
    
    success = await inventory_service.delete(
        product_id, 
        organization_id=current_user.organization_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )


# Stock Movement Management
@router.post("/stock-movements", response_model=StockMovement, status_code=status.HTTP_201_CREATED)
@monitor_performance("api.inventory.create_stock_movement")
async def create_stock_movement(
    movement_data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a stock movement (in, out, adjustment, transfer, return)."""
    inventory_service = InventoryService(db)
    
    try:
        movement = await inventory_service.create_stock_movement(
            data=movement_data,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        return movement
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stock-movements", response_model=List[StockMovement])
@monitor_performance("api.inventory.get_stock_movements")
async def get_stock_movements(
    product_id: Optional[int] = Query(None, description="Filter by product"),
    movement_type: Optional[str] = Query(None, description="Filter by movement type"),
    limit: Optional[int] = Query(100, description="Limit results", le=1000),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get stock movements with filtering."""
    inventory_service = InventoryService(db)
    
    filters = StockMovementFilters(
        product_id=product_id,
        movement_type=movement_type,
        organization_id=current_user.organization_id
    )
    
    movements = await inventory_service.get_stock_movements(
        filters=filters,
        organization_id=current_user.organization_id,
        limit=limit,
        offset=offset
    )
    return movements


# Inventory Analytics and Reports
@router.get("/reports/summary", response_model=InventoryReport)
@monitor_performance("api.inventory.get_inventory_report")
async def get_inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive inventory summary report."""
    inventory_service = InventoryService(db)
    
    report = await inventory_service.get_inventory_report(
        organization_id=current_user.organization_id
    )
    return report


@router.get("/reports/low-stock", response_model=List[ProductStockSummary])
@monitor_performance("api.inventory.get_low_stock_report")
async def get_low_stock_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products with low stock levels."""
    inventory_service = InventoryService(db)
    
    filters = ProductFilters(low_stock=True)
    products = await inventory_service.get_products(
        filters=filters,
        organization_id=current_user.organization_id
    )
    
    # Convert to stock summary format
    stock_summaries = []
    for product in products:
        # Determine stock status
        if product.current_stock == 0:
            stock_status = "out"
        elif product.current_stock <= product.minimum_stock:
            stock_status = "low"
        elif product.maximum_stock and product.current_stock > product.maximum_stock:
            stock_status = "excess"
        else:
            stock_status = "ok"
        
        total_value = product.current_stock * product.unit_price
        
        stock_summaries.append(ProductStockSummary(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            current_stock=product.current_stock,
            minimum_stock=product.minimum_stock,
            maximum_stock=product.maximum_stock,
            stock_status=stock_status,
            last_movement_date=None,  # Would need to query stock movements
            total_value=total_value
        ))
    
    return stock_summaries


@router.get("/reports/out-of-stock", response_model=List[ProductStockSummary])
@monitor_performance("api.inventory.get_out_of_stock_report")
async def get_out_of_stock_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products that are out of stock."""
    inventory_service = InventoryService(db)
    
    filters = ProductFilters(out_of_stock=True)
    products = await inventory_service.get_products(
        filters=filters,
        organization_id=current_user.organization_id
    )
    
    # Convert to stock summary format
    stock_summaries = []
    for product in products:
        stock_summaries.append(ProductStockSummary(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            current_stock=0,
            minimum_stock=product.minimum_stock,
            maximum_stock=product.maximum_stock,
            stock_status="out",
            last_movement_date=None,
            total_value=0
        ))
    
    return stock_summaries


# Bulk Operations
@router.post("/products/bulk-import", status_code=status.HTTP_202_ACCEPTED)
@monitor_performance("api.inventory.bulk_import_products")
async def bulk_import_products(
    # This would typically accept a file upload or JSON array
    # Simplified for demo
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk import products from CSV or JSON."""
    # Implementation would handle file upload and parsing
    return {"message": "Bulk import started", "status": "processing"}


@router.post("/stock-movements/bulk", status_code=status.HTTP_202_ACCEPTED)
@monitor_performance("api.inventory.bulk_stock_movements")
async def bulk_stock_movements(
    movements: List[StockMovementCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk create stock movements."""
    inventory_service = InventoryService(db)
    
    results = []
    errors = []
    
    for i, movement_data in enumerate(movements):
        try:
            movement = await inventory_service.create_stock_movement(
                data=movement_data,
                user_id=current_user.id,
                organization_id=current_user.organization_id
            )
            results.append({"index": i, "movement_id": movement.id, "status": "success"})
        except Exception as e:
            errors.append({"index": i, "error": str(e), "status": "failed"})
    
    return {
        "processed": len(movements),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }