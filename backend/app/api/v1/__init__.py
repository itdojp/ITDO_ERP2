"""
ITDO ERP v2 API Router Integration
"""
from fastapi import APIRouter

# Simple integration for v25
api_router = APIRouter()

# APIバージョン情報
@api_router.get("/version")
async def get_api_version():
    return {
        "version": "2.0.0",
        "name": "ITDO ERP API v25",
        "status": "active",
        "endpoints": [
            "/health",
            "/products",
            "/inventory", 
            "/sales",
            "/reports",
            "/permissions",
            "/organizations"
        ]
    }
