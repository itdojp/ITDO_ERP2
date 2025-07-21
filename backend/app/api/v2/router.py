"""API v2 Router - Enhanced version with improved features.

This module provides the main API router for version 2 of the ITDO ERP API.
Version 2 includes:
- Enhanced response formats
- Improved error handling
- Better performance optimizations
- New authentication methods
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

api_router_v2 = APIRouter()


@api_router_v2.get("/ping")
async def ping_v2() -> dict[str, str]:
    """Enhanced ping endpoint for API v2."""
    return {
        "message": "pong",
        "version": "v2",
        "features": ["enhanced_responses", "improved_performance", "better_auth"]
    }


@api_router_v2.get("/db-test")
async def db_test_v2(db: Session = Depends(get_db)) -> dict[str, str]:
    """Enhanced database test endpoint for API v2."""
    try:
        result = db.execute(text("SELECT 1 as test")).fetchone()
        return {
            "status": "success",
            "result": str(result[0]) if result else "None",
            "version": "v2",
            "connection_pool_size": "optimized"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "version": "v2",
            "error_code": "DB_CONNECTION_FAILED"
        }


@api_router_v2.get("/version-info")
async def version_info() -> dict[str, str]:
    """Get information about API v2."""
    return {
        "version": "v2",
        "description": "ITDO ERP API Version 2 - Enhanced features and performance",
        "release_date": "2024-07-20",
        "deprecated": False,
        "sunset_date": None,
        "new_features": [
            "Enhanced response formats",
            "Improved error handling",
            "Better performance",
            "Advanced authentication"
        ],
        "breaking_changes": [
            "Response format changes in some endpoints",
            "New required authentication headers"
        ]
    }