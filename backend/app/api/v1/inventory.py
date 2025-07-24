from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class InventoryTransactionBase(BaseModel):
    product_id: str
    transaction_type: str  # "in", "out", "adjustment"
    quantity: int
    reason: Optional[str] = None
    reference_id: Optional[str] = None  # 注文ID、調整IDなど

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransaction(InventoryTransactionBase):
    id: str
    created_at: datetime
    created_by: Optional[str] = None

class InventoryLevel(BaseModel):
    product_id: str
    current_stock: int
    reserved_stock: int
    available_stock: int
    last_updated: datetime

# モックデータストア
inventory_transactions_db = {}
inventory_levels_db = {}

@router.post("/inventory/transactions", response_model=InventoryTransaction, status_code=201)
async def create_inventory_transaction(transaction: InventoryTransactionCreate):
    """在庫取引を記録"""
    transaction_id = str(uuid.uuid4())
    now = datetime.utcnow()

    new_transaction = {
        "id": transaction_id,
        "product_id": transaction.product_id,
        "transaction_type": transaction.transaction_type,
        "quantity": transaction.quantity,
        "reason": transaction.reason,
        "reference_id": transaction.reference_id,
        "created_at": now,
        "created_by": None
    }

    inventory_transactions_db[transaction_id] = new_transaction

    # 在庫レベルを更新
    await update_inventory_level(transaction.product_id, transaction.transaction_type, transaction.quantity)

    return new_transaction

@router.get("/inventory/transactions", response_model=List[InventoryTransaction])
async def list_inventory_transactions(
    product_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """在庫取引一覧を取得"""
    transactions = list(inventory_transactions_db.values())
    
    if product_id:
        transactions = [t for t in transactions if t["product_id"] == product_id]
    
    if transaction_type:
        transactions = [t for t in transactions if t["transaction_type"] == transaction_type]
    
    return transactions[skip : skip + limit]

@router.get("/inventory/levels", response_model=List[InventoryLevel])
async def list_inventory_levels():
    """全商品の在庫レベルを取得"""
    return list(inventory_levels_db.values())

@router.get("/inventory/levels/{product_id}", response_model=InventoryLevel)
async def get_inventory_level(product_id: str):
    """特定商品の在庫レベルを取得"""
    if product_id not in inventory_levels_db:
        # 在庫レベルが存在しない場合は初期化
        await initialize_inventory_level(product_id)
    
    return inventory_levels_db[product_id]

@router.post("/inventory/adjust/{product_id}")
async def adjust_inventory(product_id: str, quantity: int, reason: str):
    """在庫調整"""
    transaction_data = InventoryTransactionCreate(
        product_id=product_id,
        transaction_type="adjustment",
        quantity=quantity,
        reason=reason
    )
    
    transaction = await create_inventory_transaction(transaction_data)
    level = await get_inventory_level(product_id)
    
    return {
        "transaction": transaction,
        "new_level": level,
        "message": f"在庫調整完了: {quantity}個{'増加' if quantity > 0 else '減少'}"
    }

@router.post("/inventory/reserve/{product_id}")
async def reserve_inventory(product_id: str, quantity: int, reference_id: str):
    """在庫予約"""
    level = await get_inventory_level(product_id)
    
    if level["available_stock"] < quantity:
        raise HTTPException(status_code=400, detail="利用可能在庫が不足しています")
    
    # 予約在庫を増加
    inventory_levels_db[product_id]["reserved_stock"] += quantity
    inventory_levels_db[product_id]["available_stock"] -= quantity
    inventory_levels_db[product_id]["last_updated"] = datetime.utcnow()
    
    # 予約取引を記録
    transaction_data = InventoryTransactionCreate(
        product_id=product_id,
        transaction_type="reserve",
        quantity=quantity,
        reason="在庫予約",
        reference_id=reference_id
    )
    
    transaction = await create_inventory_transaction(transaction_data)
    
    return {
        "transaction": transaction,
        "reserved_quantity": quantity,
        "remaining_available": inventory_levels_db[product_id]["available_stock"]
    }

async def update_inventory_level(product_id: str, transaction_type: str, quantity: int):
    """在庫レベルを更新（内部関数）"""
    if product_id not in inventory_levels_db:
        await initialize_inventory_level(product_id)
    
    level = inventory_levels_db[product_id]
    
    if transaction_type == "in":
        level["current_stock"] += quantity
        level["available_stock"] += quantity
    elif transaction_type == "out":
        level["current_stock"] -= quantity
        level["available_stock"] -= quantity
    elif transaction_type == "adjustment":
        level["current_stock"] += quantity
        level["available_stock"] += quantity
    
    # 負の在庫は許可しない
    if level["current_stock"] < 0:
        raise HTTPException(status_code=400, detail="在庫数が負になることはできません")
    
    level["last_updated"] = datetime.utcnow()

async def initialize_inventory_level(product_id: str):
    """在庫レベルを初期化（内部関数）"""
    inventory_levels_db[product_id] = {
        "product_id": product_id,
        "current_stock": 0,
        "reserved_stock": 0,
        "available_stock": 0,
        "last_updated": datetime.utcnow()
    }