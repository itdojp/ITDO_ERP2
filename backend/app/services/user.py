"""User management service."""

import random
import string
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BusinessLogicError, NotFound, PermissionDenied
from app.models.role import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user_extended import (
    BulkImportResponse,
    UserCreateExtended,
    UserListResponse,
    UserResponseExtended,
    UserSearchParams,
    UserUpdate,
)
from app.services.audit import AuditLogger


@dataclass
class ExportData:
    """Export data container."""

    content_type: str
    headers: List[str]
    rows: List[List[str]]


class UserService:
    """User management service class with type-safe operations."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = UserRepository(db)
        self.audit_logger = AuditLogger()

    def create_user(self, data: UserCreateExtended, creator: User, db: Session) -> User:
        """Create a new user with organization and role assignment."""
        # Check permissions
        if not creator.is_superuser:
            # Organization admin can create users in their org
            creator_orgs = [o.id for o in creator.get_organizations()]
            if data.organization_id not in creator_orgs:
                raise PermissionDenied("組織へのアクセス権限がありません")

            # Check if creator has org admin role
            if not any(
                r.code == "ORG_ADMIN"
                for r in creator.get_roles_in_organization(data.organization_id)
            ):
                raise PermissionDenied("組織管理者権限が必要です")

        # Create user
        user = User.create(
            db,
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            phone=data.phone,
            is_active=data.is_active,
        )
        user.created_by = creator.id

        # Assign to organization with roles
        from app.models.organization import Organization
        from app.models.role import Role

        org = (
            db.query(Organization)
            .filter(Organization.id == data.organization_id)
            .first()
        )
        if not org:
            raise NotFound("組織が見つかりません")

        # Assign department if specified
        department = None
        if data.department_id:
            from app.models.department import Department

            department = (
                db.query(Department)
                .filter(
                    Department.id == data.department_id,
                    Department.organization_id == data.organization_id,
                )
                .first()
            )
            if not department:
                raise NotFound("部門が見つかりません")

        # Assign roles
        for role_id in data.role_ids:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                continue

            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
                organization_id=org.id,
                department_id=department.id if department else None,
                assigned_by=creator.id,
            )
            db.add(user_role)

        db.flush()

        # Log audit
        self._log_audit(
            "create",
            "user",
            user.id,
            creator,
            {"email": user.email, "organization_id": data.organization_id},
            db,
        )

        return user

    def search_users(
        self, params: UserSearchParams, searcher: User, db: Session
    ) -> UserListResponse:
        """Search users with filters and multi-tenant isolation."""
        query = db.query(User).options(
            joinedload(User.user_roles).joinedload(UserRole.role),
            joinedload(User.user_roles).joinedload(UserRole.organization),
            joinedload(User.user_roles).joinedload(UserRole.department),
        )

        # Multi-tenant isolation
        if not searcher.is_superuser:
            # Get searcher's organizations
            searcher_org_ids = [o.id for o in searcher.get_organizations()]

            # Filter to users in same organizations
            query = (
                query.join(User.user_roles)
                .filter(UserRole.organization_id.in_(searcher_org_ids))
                .distinct()
            )

        # Apply filters
        if params.search:
            search_term = f"%{params.search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                )
            )

        if params.organization_id is not None:
            query = query.join(User.user_roles).filter(
                UserRole.organization_id == params.organization_id
            )

        if params.department_id is not None:
            query = query.join(User.user_roles).filter(
                UserRole.department_id == params.department_id
            )

        if params.role_id is not None:
            query = query.join(User.user_roles).filter(
                UserRole.role_id == params.role_id
            )

        if params.is_active is not None:
            query = query.filter(User.is_active == params.is_active)

        # Count total
        total = query.count()

        # Default pagination
        page = 1
        limit = 20
        offset = (page - 1) * limit

        # Execute query
        users = query.offset(offset).limit(limit).all()

        return UserListResponse(
            items=[self._user_to_extended_response(u, db) for u in users],
            total=total,
            page=page,
            limit=limit,
        )

    def get_user_detail(
        self, user_id: int, viewer: User, db: Session
    ) -> UserResponseExtended:
        """Get user details with permission check."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Permission check
        if not viewer.can_access_user(user):
            raise PermissionDenied("このユーザーへのアクセス権限がありません")

        return self._user_to_extended_response(user, db)

    def update_user(
        self, user_id: int, data: UserUpdate, updater: User, db: Session
    ) -> User:
        """Update user information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Permission check
        if not updater.can_access_user(user):
            raise PermissionDenied("このユーザーを更新する権限がありません")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        user.update(db, **update_data)

        # Log audit
        self._log_audit("update", "user", user.id, updater, update_data, db)

        return user

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        changer: User,
        db: Session,
    ) -> None:
        """Change user password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Permission check (only self or admin)
        if changer.id != user.id and not changer.is_superuser:
            raise PermissionDenied("パスワードを変更する権限がありません")

        # Change password
        user.change_password(db, current_password, new_password)

        # Log audit
        self._log_audit(
            "password_change", "user", user.id, changer, {"user_id": user.id}, db
        )

    def reset_password(self, user_id: int, resetter: User, db: Session) -> str:
        """Reset user password (admin only)."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Permission check
        if not resetter.is_superuser:
            # Check if resetter is org admin for user's org
            user_orgs = [o.id for o in user.get_organizations()]
            resetter_admin_orgs = [
                o.id
                for o in resetter.get_organizations()
                if any(
                    r.code == "ORG_ADMIN"
                    for r in resetter.get_roles_in_organization(int(o.id))
                )
            ]

            if not any(org_id in resetter_admin_orgs for org_id in user_orgs):
                raise PermissionDenied("パスワードをリセットする権限がありません")

        # Generate temporary password
        temp_password = self._generate_temp_password()

        # Set password and mark for change
        user.update(db, password=temp_password)
        user.password_must_change = True
        user.failed_login_attempts = 0
        user.locked_until = None
        db.add(user)

        # Log audit
        self._log_audit(
            "password_reset", "user", user.id, resetter, {"user_id": user.id}, db
        )

        return temp_password

    def assign_role(
        self,
        user_id: int,
        role_id: int,
        organization_id: int,
        assigner: User,
        db: Session,
        department_id: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserRole:
        """Assign role to user."""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Permission check
        if not assigner.is_superuser:
            # Must be org admin in target organization
            assigner_roles = assigner.get_roles_in_organization(organization_id)
            if not any(r.code == "ORG_ADMIN" for r in assigner_roles):
                raise PermissionDenied("ロールを割り当てる権限がありません")

        # Check role exists
        from app.models.role import Role

        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFound("ロールが見つかりません")

        # Create assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            department_id=department_id,
            assigned_by=assigner.id,
            expires_at=expires_at,
        )
        db.add(user_role)
        db.flush()

        # Log audit
        self._log_audit(
            "role_assign",
            "user",
            user.id,
            assigner,
            {
                "role_id": role_id,
                "organization_id": organization_id,
                "department_id": department_id,
            },
            db,
        )

        return user_role

    def remove_role(
        self,
        user_id: int,
        role_id: int,
        organization_id: int,
        remover: User,
        db: Session,
    ) -> None:
        """Remove role from user."""
        # Permission check
        if not remover.is_superuser:
            remover_roles = remover.get_roles_in_organization(organization_id)
            if not any(r.code == "ORG_ADMIN" for r in remover_roles):
                raise PermissionDenied("ロールを削除する権限がありません")

        # Find and remove role
        user_role = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.organization_id == organization_id,
            )
            .first()
        )

        if user_role:
            db.delete(user_role)
            db.flush()

            # Log audit
            self._log_audit(
                "role_remove",
                "user",
                user_id,
                remover,
                {"role_id": role_id, "organization_id": organization_id},
                db,
            )

    def delete_user(self, user_id: int, deleter: User, db: Session) -> None:
        """Soft delete user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        # Permission check
        if not deleter.is_superuser:
            raise PermissionDenied("ユーザーを削除する権限がありません")

        # Cannot delete self
        if deleter.id == user.id:
            raise BusinessLogicError("自分自身を削除することはできません")

        # Check if last system admin
        if user.is_superuser:
            admin_count = (
                db.query(User)
                .filter(User.is_superuser, User.is_active, User.id != user.id)
                .count()
            )

            if admin_count == 0:
                raise BusinessLogicError("最後のシステム管理者は削除できません")

        # Soft delete
        user.soft_delete(deleted_by=deleter.id)

        # Log audit
        self._log_audit("delete", "user", user.id, deleter, {}, db)

    def get_user_permissions(
        self, user_id: int, organization_id: int, db: Session
    ) -> List[str]:
        """Get user's effective permissions in organization."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFound("ユーザーが見つかりません")

        return user.get_effective_permissions(organization_id)

    def bulk_import_users(
        self,
        data: List[Dict[str, Any]],
        organization_id: int,
        role_id: int,
        importer: User,
        db: Session,
    ) -> BulkImportResponse:
        """Bulk import users."""
        # Permission check
        if not importer.is_superuser:
            importer_roles = importer.get_roles_in_organization(organization_id)
            if not any(r.code == "ORG_ADMIN" for r in importer_roles):
                raise PermissionDenied("ユーザーをインポートする権限がありません")

        created_users = []
        errors = []

        for user_data in data:
            try:
                # Generate temporary password
                temp_password = self._generate_temp_password()

                # Create user
                user = User.create(
                    db,
                    email=user_data["email"],
                    password=temp_password,
                    full_name=user_data["full_name"],
                    phone=user_data.get("phone"),
                )
                user.password_must_change = True
                user.created_by = importer.id

                # Assign role
                from app.models.role import UserRole

                user_role = UserRole(
                    user_id=user.id,
                    role_id=role_id,
                    organization_id=organization_id,
                    assigned_by=importer.id,
                )
                db.add(user_role)

                created_users.append(user)

            except Exception as e:
                errors.append({"email": user_data.get("email"), "error": str(e)})

        db.flush()

        return BulkImportResponse(
            success_count=len(created_users),
            error_count=len(errors),
            created_users=[
                self._user_to_extended_response(u, db) for u in created_users
            ],
            errors=errors,
        )

    def export_users(
        self, organization_id: int, format: str, exporter: User, db: Session
    ) -> ExportData:
        """Export user list."""
        # Permission check
        if not exporter.is_superuser:
            exporter_roles = exporter.get_roles_in_organization(organization_id)
            if not any(r.code == "ORG_ADMIN" for r in exporter_roles):
                raise PermissionDenied("ユーザーをエクスポートする権限がありません")

        # Get users
        users = (
            db.query(User)
            .join(User.user_roles)
            .filter(UserRole.organization_id == organization_id)
            .all()
        )

        # Prepare data
        headers = ["email", "full_name", "phone", "is_active", "created_at"]
        rows = []

        for user in users:
            rows.append(
                [
                    user.email,
                    user.full_name,
                    user.phone or "",
                    "Yes" if user.is_active else "No",
                    user.created_at.isoformat(),
                ]
            )

        return ExportData(
            content_type=f"text/{format}",
            headers=headers,
            rows=rows,
        )

    def _user_to_extended_response(
        self, user: User, db: Session
    ) -> UserResponseExtended:
        """Convert user to extended response."""
        from app.schemas.department_basic import DepartmentBasic
        from app.schemas.organization_basic import OrganizationBasic
        from app.schemas.role_basic import RoleBasic
        from app.schemas.user_extended import UserRoleInfo

        # Get user roles with organizations/departments
        role_infos = []
        for ur in user.user_roles:
            if not ur.is_expired:
                # Type assertions for SQLAlchemy 1.x style models
                role = ur.role
                org = ur.organization
                dept = ur.department

                role_info = UserRoleInfo(
                    role=RoleBasic(
                        id=int(role.id), code=str(role.code), name=str(role.name)
                    ),
                    organization=OrganizationBasic(
                        id=int(org.id), code=str(org.code), name=str(org.name)
                    ),
                    department=DepartmentBasic(
                        id=int(dept.id), code=str(dept.code), name=str(dept.name)
                    )
                    if dept
                    else None,
                    assigned_at=ur.assigned_at,
                    expires_at=ur.expires_at,
                )
                role_infos.append(role_info)

        # Convert organizations to OrganizationBasic
        organizations_set = set()
        for ur in user.user_roles:
            if ur.organization:
                org = ur.organization
                organizations_set.add((int(org.id), str(org.code), str(org.name)))

        organizations = [
            OrganizationBasic(id=org[0], code=org[1], name=org[2])
            for org in organizations_set
        ]

        # Convert departments to DepartmentBasic
        departments_set = set()
        for ur in user.user_roles:
            if ur.department:
                dept = ur.department
                departments_set.add((int(dept.id), str(dept.code), str(dept.name)))

        departments = [
            DepartmentBasic(id=dept[0], code=dept[1], name=dept[2])
            for dept in departments_set
        ]

        return UserResponseExtended(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            profile_image_url=user.profile_image_url,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            organizations=organizations,
            departments=departments,
            roles=role_infos,
        )

    def _generate_temp_password(self) -> str:
        """Generate temporary password."""
        # Ensure password meets validation requirements
        # Must have at least 3 of: uppercase, lowercase, digit, special char
        password_parts = [
            random.choice(string.ascii_uppercase),  # At least 1 uppercase
            random.choice(string.ascii_lowercase),  # At least 1 lowercase
            random.choice(string.digits),  # At least 1 digit
            random.choice("!@#$%"),  # At least 1 special char
        ]

        # Fill remaining chars randomly
        all_chars = string.ascii_letters + string.digits + "!@#$%"
        for _ in range(8):  # Total length will be 12
            password_parts.append(random.choice(all_chars))

        # Shuffle to avoid predictable pattern
        random.shuffle(password_parts)
        return "".join(password_parts)

    def _log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: int,
        user: User,
        changes: Dict[str, Any],
        db: Session,
    ) -> None:
        """Log audit trail."""
        from app.services.audit import AuditLogger

        AuditLogger.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user=user,
            changes=changes,
            db=db,
        )
