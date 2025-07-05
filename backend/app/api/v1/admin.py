"""
Admin-only endpoints for testing RBAC.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import require_admin
from app.models.user import User
from app.schemas.user import UserResponse


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_admin)])
async def list_all_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[UserResponse]:
    """
    List all users (admin only).
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]