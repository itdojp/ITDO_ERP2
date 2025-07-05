"""
Manager endpoints for testing RBAC.
"""

from typing import Dict
from fastapi import APIRouter, Depends

from app.core.rbac import require_manager


router = APIRouter(prefix="/manager", tags=["manager"])


@router.get("/reports", dependencies=[Depends(require_manager)])
async def get_reports() -> Dict[str, str]:
    """
    Get manager reports (manager or admin only).
    
    Returns:
        Mock report data
    """
    return {
        "message": "Manager reports",
        "data": "This is accessible to managers and admins only"
    }