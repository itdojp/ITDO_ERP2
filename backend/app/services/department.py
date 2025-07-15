"""Department service."""

<<<<<<< HEAD
from typing import List, Optional, Tuple
=======
from typing import Any
>>>>>>> origin/main

from sqlalchemy.orm import Session

from app.core.exceptions import NotFound, PermissionDenied
from app.models.department import Department
from app.models.user import User
from app.schemas.department import (
    DepartmentList,
    DepartmentResponse,
    DepartmentSummary,
    DepartmentTree,
)


class DepartmentService:
    """Department service class."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
<<<<<<< HEAD

    def create_department(
        self, data: dict, organization_id: int, user: User
=======
        self.repository = DepartmentRepository(Department, db)

    def get_department(self, department_id: DepartmentId) -> Department | None:
        """Get department by ID."""
        return self.repository.get(department_id)

    def list_departments(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> tuple[list[Department], int]:
        """List departments with pagination."""
        departments = self.repository.get_multi(skip=skip, limit=limit, filters=filters)
        total = self.repository.get_count(filters=filters)
        return departments, total

    def search_departments(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        organization_id: OrganizationId | None = None,
    ) -> tuple[list[Department], int]:
        """Search departments by name."""
        # Build search conditions
        search_condition = or_(
            Department.name.ilike(f"%{query}%"),
            Department.name_en.ilike(f"%{query}%"),
            Department.code.ilike(f"%{query}%"),
        )

        conditions = [search_condition, ~Department.is_deleted]
        if organization_id:
            conditions.append(Department.organization_id == organization_id)

        # Get all matching departments
        all_results = (
            self.db.query(Department)
            .filter(and_(*conditions))
            .order_by(Department.updated_at.desc())
            .all()
        )

        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[skip : skip + limit]

        return paginated_results, total

    def create_department(
        self, department_data: DepartmentCreate, created_by: UserId | None = None
>>>>>>> origin/main
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
            db=self.db,
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
<<<<<<< HEAD
        user: User,
        organization_id: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> DepartmentList:
        """Get departments accessible by user."""
        query = self.db.query(Department).filter(Department.is_active)
=======
        department_id: DepartmentId,
        department_data: DepartmentUpdate,
        updated_by: UserId | None = None,
    ) -> Department | None:
        """Update department details."""
        # Check if department exists
        department = self.repository.get(department_id)
        if not department:
            return None
>>>>>>> origin/main

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
<<<<<<< HEAD
            .offset(offset)
            .limit(limit)
=======

            if existing:
                raise ValueError(
                    f"Department code '{department_data.code}' "
                    "already exists in this organization"
                )

        # Add audit fields
        data = department_data.model_dump(exclude_unset=True)
        if updated_by:
            data["updated_by"] = updated_by

        # Update department
        return self.repository.update(department_id, DepartmentUpdate(**data))

    def delete_department(
        self, department_id: DepartmentId, deleted_by: UserId | None = None
    ) -> bool:
        """Soft delete a department."""
        department = self.repository.get(department_id)
        if not department:
            return False

        # Perform soft delete
        department.soft_delete(deleted_by=deleted_by)
        self.db.commit()
        return True

    def get_department_tree(
        self, organization_id: OrganizationId
    ) -> list[DepartmentTree]:
        """Get department hierarchy tree for an organization."""
        # Get root departments
        roots = (
            self.db.query(Department)
            .filter(
                Department.organization_id == organization_id,
                Department.parent_id.is_(None),
                ~Department.is_deleted,
            )
            .order_by(Department.display_order, Department.name)
>>>>>>> origin/main
            .all()
        )

        return DepartmentList(
            items=[DepartmentResponse.from_orm(dept) for dept in items],
            total=total,
            page=page,
            limit=limit,
        )

    def get_department(self, dept_id: int, user: User) -> Department:
        """Get department by ID."""
        dept = self.db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise NotFound("部門が見つかりません")

        # Check access
        if not self._has_department_access(user, dept):
            raise PermissionDenied("この部門へのアクセス権限がありません")

        return dept

    def update_department(self, dept_id: int, data: dict, user: User) -> Department:
        """Update department."""
        dept = self.get_department(dept_id, user)

        # Check permission
        if not self._has_department_admin_permission(
            user, dept.organization_id, dept.id
        ):
            raise PermissionDenied("部門管理者権限が必要です")

        # Update department
        dept.update(db=self.db, updated_by=user.id, **data)

        return dept

    def delete_department(self, dept_id: int, user: User) -> None:
        """Delete department (soft delete)."""
        dept = self.get_department(dept_id, user)

        # Check permission
        if not self._has_department_admin_permission(
            user, dept.organization_id, dept.id
        ):
            raise PermissionDenied("部門管理者権限が必要です")

        # Soft delete
        dept.soft_delete(db=self.db, deleted_by=user.id)

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

    def search_departments(
        self, search: str, skip: int, limit: int, organization_id: Optional[int] = None
    ) -> Tuple[List[Department], int]:
        """Search departments by name or code."""
        query = self.db.query(Department).filter(Department.is_active)

        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                Department.name.ilike(search_filter)
                | Department.code.ilike(search_filter)
            )

        # Apply organization filter
        if organization_id:
            query = query.filter(Department.organization_id == organization_id)

        # Get total count
        total = query.count()

        # Apply pagination
        departments = query.offset(skip).limit(limit).all()

        return departments, total

    def list_departments(
        self, skip: int, limit: int, filters: dict
    ) -> Tuple[List[Department], int]:
        """List departments with filters."""
        query = self.db.query(Department)

        # Apply filters
        for key, value in filters.items():
            if hasattr(Department, key):
                query = query.filter(getattr(Department, key) == value)

        # Get total count
        total = query.count()

        # Apply pagination
        departments = query.offset(skip).limit(limit).all()

        return departments, total

    def get_department_summary(self, department: Department) -> DepartmentSummary:
        """Convert Department to DepartmentSummary."""
        return DepartmentSummary(
            id=department.id,
            code=department.code,
            name=department.name,
            name_en=department.name_en,
            organization_id=department.organization_id,
            parent_id=department.parent_id,
<<<<<<< HEAD
            is_active=department.is_active,
            department_type=department.department_type,
            display_order=department.display_order,
            level=department.level,
            path=department.path,
            sort_order=department.sort_order,
        )

    def get_department_tree(self, organization_id: int) -> List[DepartmentTree]:
        """Get department hierarchy tree for an organization."""
        departments = (
=======
            parent_name=parent_name,
            manager_id=department.manager_id,
            manager_name=manager_name,
            department_type=department.department_type,
            user_count=user_count,
            sub_department_count=sub_department_count,
        )

    def get_department_response(self, department: Department) -> DepartmentResponse:
        """Get full department response."""
        # Load related data if needed
        if department.parent_id and not hasattr(department, "parent"):
            loaded_dept = self.repository.get(department.id)
            if loaded_dept:
                department = loaded_dept

        # Get manager info
        if department.manager_id:
            manager_obj = (
                self.db.query(User).filter(User.id == department.manager_id).first()
            )
            if manager_obj:
                from app.schemas.user import UserBasic

                UserBasic(
                    id=manager_obj.id,
                    email=manager_obj.email,
                    full_name=manager_obj.full_name,
                    is_active=manager_obj.is_active,
                )

        # Build response using Pydantic
        return DepartmentResponse.model_validate(department, from_attributes=True)

    def get_department_with_users(
        self, department: Department, include_sub_departments: bool = False
    ) -> DepartmentWithUsers:
        """Get department with user list."""
        # Get department IDs to include
        department_ids = [department.id]
        if include_sub_departments:
            sub_depts = self.get_all_sub_departments(department.id)
            department_ids.extend([d.id for d in sub_depts])

        # Get users
        from sqlalchemy import select

        users = list(
            self.db.scalars(
                select(User)
                .where(User.department_id.in_(department_ids), User.is_active)
                .order_by(User.full_name)
            )
        )

        # Convert to UserBasic for DepartmentWithUsers
        from app.schemas.user import UserBasic

        user_basics = [
            UserBasic(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
            )
            for user in users
        ]

        # Get department response
        dept_response = self.get_department_response(department)

        return DepartmentWithUsers(
            **dept_response.model_dump(),
            users=user_basics,
            total_users=len(user_basics),
        )

    def get_direct_sub_departments(self, parent_id: DepartmentId) -> list[Department]:
        """Get direct sub-departments."""
        return (
            self.db.query(Department)
            .filter(Department.parent_id == parent_id, ~Department.is_deleted)
            .order_by(Department.display_order, Department.name)
            .all()
        )

    def get_all_sub_departments(self, parent_id: DepartmentId) -> list[Department]:
        """Get all sub-departments recursively."""
        result = []

        def collect_children(dept_id: DepartmentId) -> None:
            children = self.get_direct_sub_departments(dept_id)
            for child in children:
                result.append(child)
                collect_children(child.id)

        collect_children(parent_id)
        return result

    def has_sub_departments(self, department_id: DepartmentId) -> bool:
        """Check if department has active sub-departments."""
        return (
>>>>>>> origin/main
            self.db.query(Department)
            .filter(
                Department.organization_id == organization_id,
                Department.is_active,
            )
<<<<<<< HEAD
            .order_by(Department.level, Department.sort_order)
=======
            .first()
            is not None
        )

    def get_department_user_count(self, department_id: DepartmentId) -> int:
        """Get count of active users in department."""
        return (
            self.db.query(User)
            .filter(User.department_id == department_id, User.is_active)
            .count()
        )

    def get_sub_department_count(self, parent_id: DepartmentId) -> int:
        """Get count of direct sub-departments."""
        return (
            self.db.query(Department)
            .filter(Department.parent_id == parent_id, ~Department.is_deleted)
            .count()
        )

    def update_display_order(self, department_ids: list[DepartmentId]) -> None:
        """Update display order for departments."""
        for i, dept_id in enumerate(department_ids):
            dept = self.repository.get(dept_id)
            if dept:
                dept.display_order = i + 1  # Changed from i to i + 1
        self.db.commit()

    def user_has_permission(
        self, user_id: UserId, permission: str, organization_id: OrganizationId
    ) -> bool:
        """Check if user has permission for departments in an organization."""
        # Get user roles for the organization
        user_roles = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.organization_id == organization_id,
                UserRole.is_active,
            )
>>>>>>> origin/main
            .all()
        )

        # Build tree structure
        tree = []
        dept_map = {dept.id: dept for dept in departments}

        for dept in departments:
            if dept.parent_id is None:
                # Root department
                tree.append(self._build_department_tree_node(dept, dept_map))

        return tree

    def _build_department_tree_node(
        self, department: Department, dept_map: dict
    ) -> DepartmentTree:
        """Build a single node in the department tree."""
        children = []
        for dept in dept_map.values():
            if dept.parent_id == department.id:
                children.append(self._build_department_tree_node(dept, dept_map))

        return DepartmentTree(
            id=department.id,
            code=department.code,
            name=department.name,
            name_en=department.name_en,
            organization_id=department.organization_id,
            parent_id=department.parent_id,
            is_active=department.is_active,
            department_type=department.department_type,
            display_order=department.display_order,
            level=department.level,
            path=department.path,
            sort_order=department.sort_order,
            children=children,
        )
