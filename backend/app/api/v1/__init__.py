"""
ITDO ERP v2 API Router Integration
"""
from fastapi import APIRouter

# Import new shipping router
from app.api.v1.shipping import router as shipping_router

# Simple integration for v25
api_router = APIRouter()

# Include shipping management endpoints
api_router.include_router(shipping_router)

# APIバージョン情報
@api_router.get("/version")
async def get_api_version():
    return {
        "version": "2.0.0",
        "name": "ITDO ERP API v61",
        "status": "active",
        "endpoints": [
            "/health",
            "/products",
            "/inventory", 
            "/sales",
            "/reports",
            "/permissions",
            "/organizations",
            "/shipping"
        ]
    }
