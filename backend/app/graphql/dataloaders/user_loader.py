"""User DataLoader for batch loading users."""

from typing import List, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.user import User as UserModel


async def load_users_batch(
    db: Union[Session, AsyncSession], 
    user_ids: List[int]
) -> List[UserModel]:
    """Batch load users by IDs."""
    if hasattr(db, 'execute'):  # AsyncSession
        result = await db.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        users = result.scalars().all()
    else:  # Session
        result = db.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        users = result.scalars().all()
    
    # Create lookup dictionary
    user_dict = {user.id: user for user in users}
    
    # Return users in the same order as requested IDs
    return [user_dict.get(user_id) for user_id in user_ids]