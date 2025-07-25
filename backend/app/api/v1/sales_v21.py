<<<<<<< HEAD
from typing import Any, Dict, List

from fastapi import APIRouter

=======
from typing import Any, Dict, List

from fastapi import APIRouter

>>>>>>> origin/main

router = APIRouter()

# Simple in-memory storage for v21.0
sales_db: List[Dict[str, Any]] = []

<<<<<<< HEAD

=======
>>>>>>> origin/main
@router.post("/sales-v21")
async def create_sale(product_id: int, quantity: int, total: float) -> Dict[str, Any]:
    sale = {
        "id": len(sales_db) + 1,
        "product_id": product_id,
        "quantity": quantity,
<<<<<<< HEAD
        "total": total,
=======
        "total": total
>>>>>>> origin/main
    }
    sales_db.append(sale)
    return sale

<<<<<<< HEAD

@router.get("/sales-v21")
async def list_sales() -> List[Dict[str, Any]]:
    return sales_db
=======
@router.get("/sales-v21")
async def list_sales() -> List[Dict[str, Any]]:
    return sales_db
>>>>>>> origin/main
