<<<<<<< HEAD
from typing import Any, Dict, List

from fastapi import APIRouter

=======
from typing import Any, Dict, List

from fastapi import APIRouter

>>>>>>> origin/main

router = APIRouter()

# Simple in-memory storage for v21.0
inventory_db: List[Dict[str, Any]] = []

<<<<<<< HEAD

=======
>>>>>>> origin/main
@router.post("/inventory-v21")
async def add_stock(product_id: int, quantity: int) -> Dict[str, Any]:
    stock = {
        "id": len(inventory_db) + 1,
        "product_id": product_id,
<<<<<<< HEAD
        "quantity": quantity,
=======
        "quantity": quantity
>>>>>>> origin/main
    }
    inventory_db.append(stock)
    return stock

<<<<<<< HEAD

@router.get("/inventory-v21")
async def list_inventory() -> List[Dict[str, Any]]:
    return inventory_db
=======
@router.get("/inventory-v21")
async def list_inventory() -> List[Dict[str, Any]]:
    return inventory_db
>>>>>>> origin/main
