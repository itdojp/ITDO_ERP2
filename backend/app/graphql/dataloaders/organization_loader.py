"""Organization DataLoader for batch loading organizations."""

from typing import List, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.organization import Organization as OrganizationModel


async def load_organizations_batch(
    db: Union[Session, AsyncSession], 
    organization_ids: List[int]
) -> List[OrganizationModel]:
    """Batch load organizations by IDs."""
    if hasattr(db, 'execute'):  # AsyncSession
        result = await db.execute(
            select(OrganizationModel).where(OrganizationModel.id.in_(organization_ids))
        )
        organizations = result.scalars().all()
    else:  # Session
        result = db.execute(
            select(OrganizationModel).where(OrganizationModel.id.in_(organization_ids))
        )
        organizations = result.scalars().all()
    
    # Create lookup dictionary
    org_dict = {org.id: org for org in organizations}
    
    # Return organizations in the same order as requested IDs
    return [org_dict.get(org_id) for org_id in organization_ids]