import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database_simple import get_db
from app.models.organization_simple import Organization
from app.schemas.organization_simple import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter()


@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(org: OrganizationCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new organization - v19.0 practical approach"""
    # Check if code exists
    if db.query(Organization).filter(Organization.code == org.code).first():  # type: ignore[misc]
        raise HTTPException(status_code=400, detail="Organization code already exists")

    db_org = Organization(
        id=str(uuid.uuid4()), name=org.name, code=org.code, description=org.description
    )
    db.add(db_org)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    db.refresh(db_org)  # type: ignore[misc]
    return db_org  # type: ignore[return-value]


@router.get("/organizations", response_model=List[OrganizationResponse])
def list_organizations(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> Any:
    """List organizations - v19.0 practical approach"""
    orgs = db.query(Organization).filter(Organization.is_active).offset(skip).limit(limit).all()  # type: ignore[misc]
    return orgs  # type: ignore[return-value]


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization(org_id: str, db: Session = Depends(get_db)) -> Any:
    """Get organization by ID - v19.0 practical approach"""
    org = db.query(Organization).filter(Organization.id == org_id).first()  # type: ignore[misc]
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org  # type: ignore[return-value]


@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: str, org_update: OrganizationUpdate, db: Session = Depends(get_db)
) -> Any:
    """Update organization - v19.0 practical approach"""
    org = db.query(Organization).filter(Organization.id == org_id).first()  # type: ignore[misc]
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Update fields
    update_data = org_update.dict(exclude_unset=True)  # type: ignore[misc]
    for field, value in update_data.items():
        setattr(org, field, value)  # type: ignore[misc]

    db.add(org)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    db.refresh(org)  # type: ignore[misc]
    return org  # type: ignore[return-value]


@router.delete("/organizations/{org_id}")
def deactivate_organization(org_id: str, db: Session = Depends(get_db)) -> Any:
    """Deactivate organization - v19.0 practical approach"""
    org = db.query(Organization).filter(Organization.id == org_id).first()  # type: ignore[misc]
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.is_active = False  # type: ignore[misc]
    db.add(org)  # type: ignore[misc]
    db.commit()  # type: ignore[misc]
    return {"message": "Organization deactivated successfully"}  # type: ignore[return-value]
