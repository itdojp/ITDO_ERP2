"""
Basic organization CRUD operations for ERP v17.0
Simplified organization management focusing on essential ERP functionality
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.organization import Organization
from app.schemas.organization_basic import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)


def create_organization(
    db: Session, org_data: OrganizationCreate, created_by: int
) -> Organization:
    """Create a new organization with validation."""
    # Check if organization code exists
    existing_org = (
        db.query(Organization).filter(Organization.code == org_data.code).first()
    )

    if existing_org:
        raise BusinessLogicError("Organization with this code already exists")

    # Create organization
    org_dict = org_data.dict()
    org_dict["created_by"] = created_by

    organization = Organization(**org_dict)

    # Validate
    organization.validate()

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization


def get_organization_by_id(db: Session, org_id: int) -> Optional[Organization]:
    """Get organization by ID."""
    return (
        db.query(Organization)
        .filter(and_(Organization.id == org_id, Organization.deleted_at.is_(None)))
        .first()
    )


def get_organization_by_code(db: Session, code: str) -> Optional[Organization]:
    """Get organization by code."""
    return (
        db.query(Organization)
        .filter(and_(Organization.code == code, Organization.deleted_at.is_(None)))
        .first()
    )


def get_organizations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
) -> tuple[List[Organization], int]:
    """Get organizations with filtering and pagination."""
    query = db.query(Organization).filter(Organization.deleted_at.is_(None))

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Organization.name.ilike(search_term),
                Organization.code.ilike(search_term),
                Organization.name_en.ilike(search_term),
            )
        )

    # Parent organization filter
    if parent_id is not None:
        if parent_id == 0:  # Root organizations
            query = query.filter(Organization.parent_id.is_(None))
        else:
            query = query.filter(Organization.parent_id == parent_id)

    # Active status filter
    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)

    # Sorting
    sort_column = getattr(Organization, sort_by, Organization.name)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Count for pagination
    total = query.count()

    # Apply pagination
    organizations = query.offset(skip).limit(limit).all()

    return organizations, total


def update_organization(
    db: Session, org_id: int, org_data: OrganizationUpdate, updated_by: int
) -> Optional[Organization]:
    """Update organization information."""
    organization = get_organization_by_id(db, org_id)
    if not organization:
        return None

    # Check for code conflicts if updating code
    if org_data.code and org_data.code != organization.code:
        existing_org = (
            db.query(Organization)
            .filter(
                and_(
                    Organization.code == org_data.code,
                    Organization.id != org_id,
                    Organization.deleted_at.is_(None),
                )
            )
            .first()
        )
        if existing_org:
            raise BusinessLogicError("Organization with this code already exists")

    # Update fields
    update_dict = org_data.dict(exclude_unset=True)
    organization.update(db, updated_by, **update_dict)

    return organization


def deactivate_organization(
    db: Session, org_id: int, deactivated_by: int
) -> Optional[Organization]:
    """Deactivate organization."""
    organization = get_organization_by_id(db, org_id)
    if not organization:
        return None

    # Check if can be deactivated
    can_delete, reason = organization.can_be_deleted()
    if not can_delete:
        raise BusinessLogicError(f"Cannot deactivate organization: {reason}")

    organization.is_active = False
    organization.update(db, deactivated_by)

    return organization


def get_organization_hierarchy(db: Session, org_id: int) -> Optional[Dict[str, Any]]:
    """Get organization with full hierarchy information."""
    organization = get_organization_by_id(db, org_id)
    if not organization:
        return None

    # Get hierarchy path
    hierarchy_path = organization.get_hierarchy_path()

    # Get direct children
    children = (\
        db.query(Organization)
        .filter(
            and_(
                Organization.parent_id == org_id,
                Organization.deleted_at.is_(None),
                Organization.is_active,
            )
        )
        .all()
    )

    return {
        "organization": organization,
        "hierarchy_path": [
            {"id": org.id, "code": org.code, "name": org.name} for org in hierarchy_path
        ],
        "children": [
            {"id": child.id, "code": child.code, "name": child.name}
            for child in children
        ],
        "level": len(hierarchy_path) - 1,
    }


def get_root_organizations(db: Session) -> List[Organization]:
    """Get all root organizations (no parent)."""
    return (
        db.query(Organization)
        .filter(
            and_(
                Organization.parent_id.is_(None),
                Organization.deleted_at.is_(None),
                Organization.is_active,
            )
        )
        .order_by(Organization.name)
        .all()
    )


def get_organization_statistics(db: Session) -> Dict[str, Any]:
    """Get basic organization statistics."""
    total_orgs = (
        db.query(Organization).filter(Organization.deleted_at.is_(None)).count()
    )

    active_orgs = (
        db.query(Organization)
        .filter(and_(Organization.deleted_at.is_(None), Organization.is_active))
        .count()
    )

    root_orgs = (
        db.query(Organization)
        .filter(
            and_(Organization.parent_id.is_(None), Organization.deleted_at.is_(None))
        )
        .count()
    )

    subsidiary_orgs = (
        db.query(Organization)
        .filter(
            and_(Organization.parent_id.isnot(None), Organization.deleted_at.is_(None))
        )
        .count()
    )

    return {
        "total_organizations": total_orgs,
        "active_organizations": active_orgs,
        "inactive_organizations": total_orgs - active_orgs,
        "root_organizations": root_orgs,
        "subsidiary_organizations": subsidiary_orgs,
    }


def convert_to_response(organization: Organization) -> OrganizationResponse:
    """Convert Organization model to response schema."""
    return OrganizationResponse(
        id=organization.id,
        code=organization.code,
        name=organization.name,
        name_kana=organization.name_kana,
        name_en=organization.name_en,
        display_name=organization.get_display_name(),
        phone=organization.phone,
        email=organization.email,
        website=organization.website,
        full_address=organization.full_address,
        business_type=organization.business_type,
        industry=organization.industry,
        employee_count=organization.employee_count,
        parent_id=organization.parent_id,
        is_active=organization.is_active,
        is_subsidiary=organization.is_subsidiary,
        is_parent=organization.is_parent,
        created_at=organization.created_at,
        updated_at=organization.updated_at,
    )
