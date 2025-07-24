"""
Simple Product Management API - No Database Dependencies
Pure business logic for product operations
Working over perfect approach
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter(prefix="/simple-products", tags=["Simple Products"])

# In-memory storage for demonstration
products_store: Dict[str, Dict[str, Any]] = {}

class SimpleProduct(BaseModel):
    """Simple product model without database dependencies."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    category: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProductCreate(BaseModel):
    """Schema for creating a product."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    category: Optional[str] = Field(None, max_length=100)

class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

@router.post("/", response_model=SimpleProduct)
async def create_product(product_data: ProductCreate) -> SimpleProduct:
    """Create a new product - simple approach."""
    # Check if code already exists
    for existing_product in products_store.values():
        if existing_product["code"] == product_data.code:
            raise HTTPException(
                status_code=400, 
                detail=f"Product with code '{product_data.code}' already exists"
            )
    
    # Create new product
    product = SimpleProduct(
        code=product_data.code,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        category=product_data.category
    )
    
    # Store in memory
    products_store[product.id] = product.model_dump()
    
    return product

@router.get("/", response_model=List[SimpleProduct])
async def list_products(
    skip: int = Query(0, ge=0, description="Skip items"),
    limit: int = Query(50, ge=1, le=100, description="Limit items"),
    search: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> List[SimpleProduct]:
    """List products with filtering."""
    all_products = list(products_store.values())
    
    # Apply filters
    filtered_products = []
    for product_data in all_products:
        # Active filter
        if is_active is not None and product_data["is_active"] != is_active:
            continue
            
        # Category filter
        if category and product_data.get("category") != category:
            continue
            
        # Search filter
        if search:
            search_lower = search.lower()
            if not (
                search_lower in product_data["name"].lower() or
                search_lower in product_data["code"].lower() or
                (product_data.get("description") and search_lower in product_data["description"].lower())
            ):
                continue
        
        filtered_products.append(product_data)
    
    # Apply pagination
    paginated_products = filtered_products[skip:skip + limit]
    
    return [SimpleProduct(**product_data) for product_data in paginated_products]

@router.get("/{product_id}", response_model=SimpleProduct)
async def get_product(product_id: str) -> SimpleProduct:
    """Get product by ID."""
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = products_store[product_id]
    return SimpleProduct(**product_data)

@router.put("/{product_id}", response_model=SimpleProduct)
async def update_product(product_id: str, product_data: ProductUpdate) -> SimpleProduct:
    """Update product information."""
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get existing product
    existing_product = products_store[product_id].copy()
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        existing_product[field] = value
    
    # Update timestamp
    existing_product["updated_at"] = datetime.now()
    
    # Save updated product
    products_store[product_id] = existing_product
    
    return SimpleProduct(**existing_product)

@router.delete("/{product_id}")
async def delete_product(product_id: str) -> Dict[str, str]:
    """Delete product (soft delete - mark as inactive)."""
    if product_id not in products_store:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete - mark as inactive
    products_store[product_id]["is_active"] = False
    products_store[product_id]["updated_at"] = datetime.now()
    
    return {"message": "Product deactivated successfully", "product_id": product_id}

@router.get("/code/{product_code}", response_model=SimpleProduct)
async def get_product_by_code(product_code: str) -> SimpleProduct:
    """Get product by code."""
    for product_data in products_store.values():
        if product_data["code"] == product_code and product_data["is_active"]:
            return SimpleProduct(**product_data)
    
    raise HTTPException(status_code=404, detail=f"Product with code '{product_code}' not found")

@router.get("/stats/summary")
async def get_products_summary() -> Dict[str, Any]:
    """Get products summary statistics."""
    all_products = list(products_store.values())
    active_products = [p for p in all_products if p["is_active"]]
    
    categories = {}
    for product in active_products:
        category = product.get("category", "Uncategorized")
        categories[category] = categories.get(category, 0) + 1
    
    return {
        "total_products": len(all_products),
        "active_products": len(active_products),
        "inactive_products": len(all_products) - len(active_products),
        "categories_breakdown": categories,
        "last_updated": datetime.now().isoformat()
    }

@router.post("/bulk/create", response_model=List[SimpleProduct])
async def bulk_create_products(products: List[ProductCreate]) -> List[SimpleProduct]:
    """Bulk create products."""
    created_products = []
    errors = []
    
    for i, product_data in enumerate(products):
        try:
            # Check if code already exists
            code_exists = any(
                existing["code"] == product_data.code 
                for existing in products_store.values()
            )
            
            if code_exists:
                errors.append(f"Product {i+1}: Code '{product_data.code}' already exists")
                continue
            
            # Create product
            product = SimpleProduct(
                code=product_data.code,
                name=product_data.name,
                description=product_data.description,
                price=product_data.price,
                category=product_data.category
            )
            
            products_store[product.id] = product.model_dump()
            created_products.append(product)
            
        except Exception as e:
            errors.append(f"Product {i+1}: {str(e)}")
    
    if errors and not created_products:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    return created_products