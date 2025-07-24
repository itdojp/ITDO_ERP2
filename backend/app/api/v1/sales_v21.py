from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter()

# Simple in-memory storage for v21.0
sales_db: List[Dict[str, Any]] = []


@router.post("/sales-v21")
async def create_sale(product_id: int, quantity: int, total: float) -> Dict[str, Any]:
    sale = {
        "id": len(sales_db) + 1,
        "product_id": product_id,
        "quantity": quantity,
        "total": total,
    }
    sales_db.append(sale)
    return sale


@router.get("/sales-v21")
async def list_sales() -> List[Dict[str, Any]]:
    return sales_db
