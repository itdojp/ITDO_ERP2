"""Organization service."""

from typing import List, Optional, Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.models.organization import Organization
from app.models.role import UserRole
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationList,
    OrganizationResponse,
    OrganizationUpdate,
)


class OrganizationService:
    """Organization service class."""

    def create_organization(
        self, data: OrganizationCreate, user: User, db: Session
    ) -> Organization:
        """Create a new organization."""
        # Check if user is system admin
        if not user.is_superuser:
            raise PermissionDenied("システム管理者権限が必要です")

        # Create organization
        org = Organization.create(
            db=db,
            code=data.code,
            name=data.name,
            name_kana=data.name_kana,
            postal_code=data.postal_code,
            address=data.address,
            phone=data.phone,
            email=data.email,
            website=data.website,
            fiscal_year_start=data.fiscal_year_start,
            created_by=user.id,
        )

        # Log audit
        self._log_audit(
            "create",
            "organization",
            org.id,
            user,
            {"code": data.code, "name": data.name},
        )

        return org

    def get_organizations(
        self,
        user: User,
        db: Session,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
    ) -> OrganizationList:
        """Get organizations accessible by user."""
        query = db.query(Organization).filter(Organization.is_active == True)

        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.code.ilike(f"%{search}%"),
                )
            )

        # Apply access control
        if not user.is_superuser:
            # Get organizations user belongs to
            user_org_ids = [
                ur.organization_id for ur in user.user_roles if not ur.is_expired()
            ]

            if user_org_ids:
                query = query.filter(Organization.id.in_(user_org_ids))
            else:
                # User has no organization access
                query = query.filter(Organization.id == -1)  # No results

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        items = query.order_by(Organization.code).offset(offset).limit(limit).all()

        return OrganizationList(
            items=[OrganizationResponse.from_orm(org) for org in items],
            total=total,
            page=page,
            limit=limit,
        )

    def get_organization(self, org_id: int, user: User, db: Session) -> Organization:
        """Get organization by ID."""
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise NotFound("組織が見つかりません")

        # Check access
        if not user.is_superuser and not self._has_organization_access(user, org_id):
            raise PermissionDenied("この組織へのアクセス権限がありません")

        return org

    def update_organization(
        self, org_id: int, data: OrganizationUpdate, user: User, db: Session
    ) -> Organization:
        """Update organization."""
        org = self.get_organization(org_id, user, db)

        # Check permission
        if not self._has_organization_admin_permission(user, org_id):
            raise PermissionDenied("組織管理者権限が必要です")

        # Update organization
        update_data = data.dict(exclude_unset=True)
        org.update(db=db, updated_by=user.id, **update_data)

        # Log audit
        self._log_audit("update", "organization", org.id, user, update_data)

        return org

    def delete_organization(self, org_id: int, user: User, db: Session) -> None:
        """Delete organization (soft delete)."""
        org = self.get_organization(org_id, user, db)

        # Check permission - only system admin can delete
        if not user.is_superuser:
            raise PermissionDenied("システム管理者権限が必要です")

        # Soft delete
        org.soft_delete(db=db, deleted_by=user.id)

        # Log audit
        self._log_audit("delete", "organization", org.id, user, {})

    def _has_organization_access(self, user: User, org_id: int) -> bool:
        """Check if user has access to organization."""
        if user.is_superuser:
            return True

        for user_role in user.user_roles:
            if user_role.organization_id == org_id and not user_role.is_expired():
                return True

        return False

    def _has_organization_admin_permission(self, user: User, org_id: int) -> bool:
        """Check if user has admin permission for organization."""
        if user.is_superuser:
            return True

        for user_role in user.user_roles:
            if (
                user_role.organization_id == org_id
                and not user_role.is_expired()
                and user_role.role.has_permission("org:*")
            ):
                return True

        return False

    def _log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: int,
        user: User,
        changes: dict,
    ) -> None:
        """Log audit event."""
        # Mock implementation for now
        # In real implementation, this would use AuditLogger
        pass
