import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization_simple import Organization


def create_organization(
    db: Session, name: str, code: str, description: Optional[str] = None
) -> Organization:
    db_org = Organization(
        id=str(uuid.uuid4()), name=name, code=code, description=description
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def get_organization(db: Session, org_id: str) -> Optional[Organization]:
    return db.query(Organization).filter(Organization.id == org_id).first()


def get_organization_by_code(db: Session, code: str) -> Optional[Organization]:
    return db.query(Organization).filter(Organization.code == code).first()


def get_organizations(
    db: Session, skip: int = 0, limit: int = 100, active_only: bool = True
) -> List[Organization]:
    query = db.query(Organization)
    if active_only:
        query = query.filter(Organization.is_active)
    return query.offset(skip).limit(limit).all()


def update_organization(
    db: Session,
    org_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[Organization]:
    db_org = get_organization(db, org_id)
    if not db_org:
        return None

    if name is not None:
        db_org.name = name
    if description is not None:
        db_org.description = description
    if is_active is not None:
        db_org.is_active = is_active

    db.commit()
    db.refresh(db_org)
    return db_org


def delete_organization(db: Session, org_id: str) -> bool:
    db_org = get_organization(db, org_id)
    if not db_org:
        return False

    db_org.is_active = False  # Soft delete
    db.commit()
    return True
