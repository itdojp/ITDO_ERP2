from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class ProductBase(BaseModel):
    code: str
    name: str
    price: float
    stock: int
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    description: Optional[str] = None

class Product(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

# モックデータストア
products_db = {}

@router.post("/products", response_model=Product, status_code=201)
async def create_product(product: ProductCreate):
    """商品を新規作成"""
    # 商品コードの重複チェック
    for p in products_db.values():
        if p["code"] == product.code:
            raise HTTPException(status_code=400, detail="商品コードが既に存在します")

    product_id = str(uuid.uuid4())
    now = datetime.utcnow()

    new_product = {
        "id": product_id,
        "code": product.code,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "description": product.description,
        "created_at": now,
        "updated_at": now
    }

    products_db[product_id] = new_product
    return new_product

@router.get("/products", response_model=List[Product])
async def list_products(skip: int = 0, limit: int = 100):
    """商品一覧を取得"""
    products = list(products_db.values())
    return products[skip : skip + limit]

@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """商品詳細を取得"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品が見つかりません")
    return products_db[product_id]

@router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: ProductUpdate):
    """商品情報を更新"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品が見つかりません")

    product = products_db[product_id]
    update_data = product_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        product[field] = value

    product["updated_at"] = datetime.utcnow()
    return product

@router.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: str):
    """商品を削除"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品が見つかりません")

    del products_db[product_id]
    return None

@router.post("/products/{product_id}/adjust-stock")
async def adjust_stock(product_id: str, quantity: int):
    """在庫数を調整"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品が見つかりません")

    product = products_db[product_id]
    new_stock = product["stock"] + quantity

    if new_stock < 0:
        raise HTTPException(status_code=400, detail="在庫数が不足しています")

    product["stock"] = new_stock
    product["updated_at"] = datetime.utcnow()

    return {"product_id": product_id, "new_stock": new_stock, "adjusted_by": quantity}