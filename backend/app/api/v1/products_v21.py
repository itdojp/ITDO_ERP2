<<<<<<< HEAD
from typing import Any, Dict, List

from fastapi import APIRouter

=======
from typing import Any, Dict, List

from fastapi import APIRouter

>>>>>>> origin/main

router = APIRouter()

# Simple in-memory storage for v21.0
products_db: List[Dict[str, Any]] = []

<<<<<<< HEAD

@router.post("/products-v21")
async def create_product(name: str, price: float) -> Dict[str, Any]:
    product = {"id": len(products_db) + 1, "name": name, "price": price}
    products_db.append(product)
    return product


@router.get("/products-v21")
async def list_products() -> List[Dict[str, Any]]:
    return products_db
=======
@router.post("/products-v21")
async def create_product(name: str, price: float) -> Dict[str, Any]:
    product = {
        "id": len(products_db) + 1,
        "name": name,
        "price": price
    }
    products_db.append(product)
    return product

@router.get("/products-v21")
async def list_products() -> List[Dict[str, Any]]:
    return products_db
>>>>>>> origin/main
