"""
Minimal FastAPI App for Testing Core ERP Functions
Simple approach for product and inventory management
"""

from fastapi import FastAPI
from app.api.v1.health_simple import router as health_router
from app.api.v1.products_basic import router as products_router
from app.api.v1.inventory_basic import router as inventory_router
from app.api.v1.test_minimal import router as test_router

# Create minimal app with essential routes only
app = FastAPI(
    title="ITDO ERP API - Minimal",
    description="Core ERP functionality for product and inventory management",
    version="v21.0-minimal"
)

# Include only working routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(test_router, prefix="/api/v1", tags=["test"])
app.include_router(products_router, prefix="/api/v1", tags=["products"])
app.include_router(inventory_router, prefix="/api/v1", tags=["inventory"])

@app.get("/")
async def root():
    """Root endpoint for minimal ERP API."""
    return {
        "message": "ITDO ERP API - Minimal Mode",
        "version": "v21.0-minimal",
        "status": "working_over_perfect",
        "available_endpoints": [
            "/api/v1/health",
            "/api/v1/test",
            "/api/v1/products-basic/",
            "/api/v1/inventory-basic/"
        ]
    }