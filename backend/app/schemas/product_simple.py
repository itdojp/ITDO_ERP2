from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    """Product creation schema - v19.0 practical"""

    code: str
    name: str
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    stock_quantity: float = 0.0
    category: Optional[str] = None
    organization_id: Optional[str] = None


class ProductResponse(BaseModel):
    """Product response schema - v19.0 practical"""

    id: str
    code: str
    name: str
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    stock_quantity: float
    category: Optional[str] = None
    is_active: bool
    organization_id: Optional[str] = None

    class Config:
        orm_mode = True  # type: ignore[misc] - practical approach


class ProductUpdate(BaseModel):
    """Product update schema - v19.0 practical"""

    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    stock_quantity: Optional[float] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class StockAdjustment(BaseModel):
    """Stock adjustment schema - v19.0 practical"""

    quantity_change: float
    reason: Optional[str] = None
