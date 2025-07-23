from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Simple health check endpoint - no complex types"""
    return {
        "status": "healthy",
        "service": "ITDO ERP API",
        "version": "v19.0-practical",
        "mode": "working_over_perfect"
    }
