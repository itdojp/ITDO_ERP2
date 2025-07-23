import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database_simple import get_db
from app.models.product_simple import Product
from app.schemas.product_simple import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StockAdjustment,
)

router = APIRouter()

@router.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new product - v19.0 practical approach"""
    # Check if code exists
    if db.query(Product).filter(Product.code == product.code).first():  # type: ignore[misc]
        raise HTTPException(status_code=400, detail="Product code already exists")

    db_product = Product(
        id=str(uuid.uuid4()),
        code=product.code,
        name=product.name,
        description=product.description,
        price=product.price,
        cost=product.cost,
        stock_quantity=product.stock_quantity,
        category=product.category,
        organization_id=product.organization_id
    )
    db.add(db_product)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    db.refresh(db_product)  # type: ignore[misc]
    return db_product  # type: ignore[return-value]

@router.get("/products", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in name and code"),
    category: Optional[str] = Query(None, description="Filter by category"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    db: Session = Depends(get_db)
) -> Any:
    """List products - v19.0 practical approach"""
    query = db.query(Product).filter(Product.is_active == True)  # type: ignore[misc]

    if search:
        query = query.filter(  # type: ignore[misc]
            (Product.name.like(f"%{search}%")) |  # type: ignore[misc]
            (Product.code.like(f"%{search}%"))  # type: ignore[misc]
        )

    if category:
        query = query.filter(Product.category == category)  # type: ignore[misc]

    if organization_id:
        query = query.filter(Product.organization_id == organization_id)  # type: ignore[misc]

    products = query.offset(skip).limit(limit).all()  # type: ignore[misc]
    return products  # type: ignore[return-value]

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)) -> Any:
    """Get product by ID - v19.0 practical approach"""
    product = db.query(Product).filter(Product.id == product_id).first()  # type: ignore[misc]
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product  # type: ignore[return-value]

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, product_update: ProductUpdate, db: Session = Depends(get_db)) -> Any:
    """Update product - v19.0 practical approach"""
    product = db.query(Product).filter(Product.id == product_id).first()  # type: ignore[misc]
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update fields
    update_data = product_update.dict(exclude_unset=True)  # type: ignore[misc]
    for field, value in update_data.items():
        setattr(product, field, value)  # type: ignore[misc]

    db.add(product)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    db.refresh(product)  # type: ignore[misc]
    return product  # type: ignore[return-value]

@router.post("/products/{product_id}/adjust-stock")
def adjust_stock(product_id: str, adjustment: StockAdjustment, db: Session = Depends(get_db)) -> Any:
    """Adjust product stock - v19.0 practical approach"""
    product = db.query(Product).filter(Product.id == product_id).first()  # type: ignore[misc]
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Simple stock adjustment
    new_quantity = product.stock_quantity + adjustment.quantity_change  # type: ignore[misc]
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")

    product.stock_quantity = new_quantity  # type: ignore[misc]
    db.add(product)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    db.refresh(product)  # type: ignore[misc]

    return {
        "message": "Stock adjusted successfully",
        "old_quantity": product.stock_quantity - adjustment.quantity_change,
        "new_quantity": product.stock_quantity,
        "adjustment": adjustment.quantity_change,
        "reason": adjustment.reason
    }  # type: ignore[return-value]

@router.get("/products/{product_id}/stock")
def get_stock_info(product_id: str, db: Session = Depends(get_db)) -> Any:
    """Get stock information - v19.0 practical approach"""
    product = db.query(Product).filter(Product.id == product_id).first()  # type: ignore[misc]
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Simple stock status
    stock_status = "in_stock" if product.stock_quantity > 0 else "out_of_stock"  # type: ignore[misc]
    if product.stock_quantity > 0 and product.stock_quantity <= 10:  # type: ignore[misc]
        stock_status = "low_stock"

    return {
        "product_id": product.id,
        "product_name": product.name,
        "current_stock": product.stock_quantity,
        "stock_status": stock_status,
        "stock_value": (product.cost or 0) * product.stock_quantity if product.cost else 0
    }  # type: ignore[return-value]

@router.delete("/products/{product_id}")
def deactivate_product(product_id: str, db: Session = Depends(get_db)) -> Any:
    """Deactivate product - v19.0 practical approach"""
    product = db.query(Product).filter(Product.id == product_id).first()  # type: ignore[misc]
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False  # type: ignore[misc]
    db.add(product)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    return {"message": "Product deactivated successfully"}  # type: ignore[return-value]

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> Any:
    """List all unique categories - v19.0 practical approach"""
    categories = db.query(Product.category).distinct().filter(Product.category.isnot(None)).all()  # type: ignore[misc]
    return [cat[0] for cat in categories if cat[0]]  # type: ignore[return-value]
