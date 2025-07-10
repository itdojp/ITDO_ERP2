"""Department service."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.models.department import Department
from app.models.user import User
from app.schemas.department import (
    DepartmentList,
    DepartmentResponse,
)


class DepartmentService:
    """Department service class."""

    def create_department(
        self, data: dict, organization_id: int, user: User, db: Session
    ) -> Department:
        """Create a new department."""
        # Check organization access
        if not self._has_organization_access(user, organization_id):
            raise PermissionDenied("この組織へのアクセス権限がありません")

        # Check permission
        if not self._has_department_admin_permission(user, organization_id):
            raise PermissionDenied("部門管理者権限が必要です")

        # Create department
        dept = Department.create(
            db=db,
            organization_id=organization_id,
            code=data["code"],
            name=data["name"],
            name_kana=data.get("name_kana"),
            description=data.get("description"),
            parent_id=data.get("parent_id"),
            sort_order=data.get("sort_order", 0),
            created_by=user.id,
        )

        return dept

    def get_departments(
        self,
        user: User,
        db: Session,
        organization_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> DepartmentList:
        """Get departments accessible by user."""
        query = db.query(Department).filter(Department.is_active == True)

        # Filter by organization
        if organization_id:
            query = query.filter(Department.organization_id == organization_id)

        # Apply access control
        if not user.is_superuser:
            # Get organizations user belongs to
            user_org_ids = [
                ur.organization_id for ur in user.user_roles if not ur.is_expired()
            ]

            if user_org_ids:
                query = query.filter(Department.organization_id.in_(user_org_ids))
            else:
                # User has no organization access
                query = query.filter(Department.id == -1)  # No results

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        items = (
            query.order_by(
                Department.organization_id, Department.sort_order, Department.code
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return DepartmentList(
            items=[DepartmentResponse.from_orm(dept) for dept in items],
            total=total,
            page=page,
            limit=limit,
        )

    def get_department(self, dept_id: int, user: User, db: Session) -> Department:
        """Get department by ID."""
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise NotFound("部門が見つかりません")

        # Check access
        if not self._has_department_access(user, dept):
            raise PermissionDenied("この部門へのアクセス権限がありません")

        return dept

    def update_department(
        self, dept_id: int, data: dict, user: User, db: Session
    ) -> Department:
        """Update department."""
        dept = self.get_department(dept_id, user, db)

        # Check permission
        if not self._has_department_admin_permission(
            user, dept.organization_id, dept.id
        ):
            raise PermissionDenied("部門管理者権限が必要です")

        # Update department
        dept.update(db=db, updated_by=user.id, **data)

        return dept

    def delete_department(self, dept_id: int, user: User, db: Session) -> None:
        """Delete department (soft delete)."""
        dept = self.get_department(dept_id, user, db)

        # Check permission
        if not self._has_department_admin_permission(
            user, dept.organization_id, dept.id
        ):
            raise PermissionDenied("部門管理者権限が必要です")

        # Soft delete
        dept.soft_delete(db=db, deleted_by=user.id)

    def _has_organization_access(self, user: User, org_id: int) -> bool:
        """Check if user has access to organization."""
        if user.is_superuser:
            return True

        for user_role in user.user_roles:
            if user_role.organization_id == org_id and not user_role.is_expired():
                return True

        return False

    def _has_department_access(self, user: User, dept: Department) -> bool:
        """Check if user has access to department."""
        if user.is_superuser:
            return True

        for user_role in user.user_roles:
            if (
                user_role.organization_id == dept.organization_id
                and not user_role.is_expired()
            ):
                # Check if user has access to this specific department or its parent
                if user_role.department_id is None:  # Organization level access
                    return True
                elif user_role.department_id == dept.id:  # Direct department access
                    return True
                elif (
                    dept.path and str(user_role.department_id) in dept.path
                ):  # Parent department access
                    return True

        return False

    def _has_department_admin_permission(
        self, user: User, org_id: int, dept_id: Optional[int] = None
    ) -> bool:
        """Check if user has admin permission for department."""
        if user.is_superuser:
            return True

        for user_role in user.user_roles:
            if user_role.organization_id == org_id and not user_role.is_expired():
                # Check role permissions
                if user_role.role.has_permission("org:*"):  # Organization admin
                    return True
                elif user_role.role.has_permission("dept:*"):  # Department admin
                    # Check if user has access to this department
                    if user_role.department_id is None:  # Organization level dept admin
                        return True
                    elif (
                        dept_id is None or user_role.department_id == dept_id
                    ):  # Direct access
                        return True

        return False
