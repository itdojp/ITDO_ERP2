from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter()

# Simple in-memory storage for v21.0
inventory_db: List[Dict[str, Any]] = []


@router.post("/inventory-v21")
async def add_stock(product_id: int, quantity: int) -> Dict[str, Any]:
    stock = {
        "id": len(inventory_db) + 1,
        "product_id": product_id,
        "quantity": quantity,
    }
    inventory_db.append(stock)
    return stock


@router.get("/inventory-v21")
async def list_inventory() -> List[Dict[str, Any]]:
    return inventory_db
