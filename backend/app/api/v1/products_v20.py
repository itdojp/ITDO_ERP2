from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.core.database_simple import get_db
from app.models.product_v20 import Product
from pydantic import BaseModel

router = APIRouter()

class ProductCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    unit_price: float
    stock_quantity: int = 0
    reorder_level: int = 10

class ProductResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    unit_price: float
    stock_quantity: int
    reorder_level: int
    is_active: bool

    class Config:
        orm_mode = True

@router.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Check if code exists
    if db.query(Product).filter(Product.code == product.code).first():
        raise HTTPException(status_code=400, detail="Product code already exists")

    db_product = Product(
        id=str(uuid.uuid4()),
        code=product.code,
        name=product.name,
        description=product.description,
        unit_price=product.unit_price,
        stock_quantity=product.stock_quantity,
        reorder_level=product.reorder_level
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/products", response_model=List[ProductResponse])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).offset(skip).limit(limit).all()
    return products

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}/stock")
def update_stock(product_id: str, new_quantity: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_quantity = product.stock_quantity
    product.stock_quantity = new_quantity
    db.commit()
    
    return {
        "product_id": product_id,
        "old_quantity": old_quantity,
        "new_quantity": new_quantity,
        "message": "Stock updated successfully"
    }