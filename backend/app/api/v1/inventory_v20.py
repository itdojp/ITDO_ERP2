from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.core.database_simple import get_db
from app.models.inventory_v20 import InventoryTransaction, StockLevel
from pydantic import BaseModel

router = APIRouter()

class TransactionCreate(BaseModel):
    product_id: str
    transaction_type: str  # 'in', 'out', 'adjustment'
    quantity: int
    unit_cost: Optional[float] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    reference_number: Optional[str] = None

class TransactionResponse(BaseModel):
    id: str
    product_id: str
    transaction_type: str
    quantity: int
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    reason: Optional[str] = None
    reference_number: Optional[str] = None
    created_at: str

    class Config:
        orm_mode = True

class StockLevelResponse(BaseModel):
    id: str
    product_id: str
    current_stock: int
    reserved_stock: int
    available_stock: int
    reorder_point: int
    max_stock: Optional[int] = None

    class Config:
        orm_mode = True

@router.post("/inventory/transactions", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    # Calculate total cost if unit cost provided
    total_cost = None
    if transaction.unit_cost and transaction.quantity:
        total_cost = transaction.unit_cost * abs(transaction.quantity)

    db_transaction = InventoryTransaction(
        id=str(uuid.uuid4()),
        product_id=transaction.product_id,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        unit_cost=transaction.unit_cost,
        total_cost=total_cost,
        reason=transaction.reason,
        notes=transaction.notes,
        reference_number=transaction.reference_number
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/inventory/transactions", response_model=List[TransactionResponse])
def list_transactions(
    skip: int = 0, 
    limit: int = 100,
    product_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InventoryTransaction)
    
    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)
    
    if transaction_type:
        query = query.filter(InventoryTransaction.transaction_type == transaction_type)
    
    transactions = query.offset(skip).limit(limit).all()
    return transactions

@router.get("/inventory/stock-levels", response_model=List[StockLevelResponse])
def list_stock_levels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stock_levels = db.query(StockLevel).offset(skip).limit(limit).all()
    return stock_levels

@router.get("/inventory/stock-levels/{product_id}", response_model=StockLevelResponse)
def get_stock_level(product_id: str, db: Session = Depends(get_db)):
    stock_level = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if not stock_level:
        raise HTTPException(status_code=404, detail="Stock level not found")
    return stock_level