"""Department service implementation."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.department import Department
from app.models.department_collaboration import DepartmentCollaboration
from app.models.department_task import DepartmentTask
from app.models.role import UserRole, RolePermission
from app.models.task import Task
from app.models.user import User
from app.repositories.department import DepartmentRepository
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentSummary,
    DepartmentTree,
    DepartmentUpdate,
    DepartmentWithUsers,
)
from app.types import DepartmentId, OrganizationId, UserId


class DepartmentService:
    """Service for department business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.repository = DepartmentRepository(Department, db)

    def get_department(self, department_id: DepartmentId) -> Optional[Department]:
        """Get department by ID."""
        return self.repository.get(department_id)

    def list_departments(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Department], int]:
        """List departments with pagination."""
        departments = self.repository.get_multi(skip=skip, limit=limit, filters=filters)
        total = self.repository.get_count(filters=filters)
        return departments, total

    def search_departments(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[OrganizationId] = None,
    ) -> Tuple[List[Department], int]:
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
        self, department_data: DepartmentCreate, created_by: Optional[UserId] = None
    ) -> Department:
        """Create a new department."""
        # Validate unique code within organization
        existing = (
            self.db.query(Department)
            .filter(
                Department.organization_id == department_data.organization_id,
                Department.code == department_data.code,
                ~Department.is_deleted,
            )
            .first()
        )

        if existing:
            raise ValueError(
                f"Department code '{department_data.code}' "
                "already exists in this organization"
            )
        
        # Check depth limit if creating under a parent
        if department_data.parent_id:
            parent = self.repository.get(department_data.parent_id)
            if parent and hasattr(parent, 'depth') and parent.depth >= 4:
                raise BusinessLogicError(
                    "Cannot exceed maximum depth of 5 levels"
                )

        # Add audit fields
        data = department_data.model_dump()
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by

        # Create department
        department = self.repository.create(DepartmentCreate(**data))
        
        # Flush to get the ID
        self.db.flush()
        
        # Set hierarchical path and depth
        department.update_path()
        self.db.commit()
        
        return department

    def update_department(
        self,
        department_id: DepartmentId,
        department_data: DepartmentUpdate,
        updated_by: Optional[UserId] = None,
    ) -> Optional[Department]:
        """Update department details."""
        # Check if department exists
        department = self.repository.get(department_id)
        if not department:
            return None

        # Validate unique code if being changed
        if department_data.code and department_data.code != department.code:
            existing = (
                self.db.query(Department)
                .filter(
                    Department.organization_id == department.organization_id,
                    Department.code == department_data.code,
                    Department.id != department_id,
                    ~Department.is_deleted,
                )
                .first()
            )

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
        self, department_id: DepartmentId, deleted_by: Optional[UserId] = None
    ) -> bool:
        """Soft delete a department."""
        department = self.repository.get(department_id)
        if not department:
            return False
        
        # Validate deletion
        self.validate_department_deletion(department_id)

        # Perform soft delete
        department.soft_delete(deleted_by=deleted_by)
        self.db.commit()
        return True

    def get_department_tree(
        self, organization_id: OrganizationId
    ) -> List[DepartmentTree]:
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
            .all()
        )

        def build_tree(dept: Department, level: int = 0) -> DepartmentTree:
            """Build tree recursively."""
            children = []
            sub_depts = (
                self.db.query(Department)
                .filter(Department.parent_id == dept.id, ~Department.is_deleted)
                .order_by(Department.display_order, Department.name)
                .all()
            )

            for sub in sub_depts:
                children.append(build_tree(sub, level + 1))

            manager_name = None
            if dept.manager_id:
                manager = self.db.query(User).filter(User.id == dept.manager_id).first()
                if manager:
                    manager_name = manager.full_name

            return DepartmentTree(
                id=dept.id,
                code=dept.code,
                name=dept.name,
                name_en=dept.name_en,
                is_active=dept.is_active,
                level=level,
                parent_id=dept.parent_id,
                manager_id=dept.manager_id,
                manager_name=manager_name,
                user_count=self.get_department_user_count(dept.id),
                children=children,
            )

        return [build_tree(root) for root in roots]

    def get_department_summary(self, department: Department) -> DepartmentSummary:
        """Get department summary with counts."""
        parent_name = department.parent.name if department.parent else None
        manager_name = None

        if department.manager_id:
            from sqlalchemy import select

            manager = self.db.scalar(
                select(User).where(User.id == department.manager_id)
            )
            if manager:
                manager_name = manager.full_name

        user_count = self.get_department_user_count(department.id)
        sub_department_count = self.get_sub_department_count(department.id)

        return DepartmentSummary(
            id=department.id,
            code=department.code,
            name=department.name,
            name_en=department.name_en,
            organization_id=department.organization_id,
            is_active=department.is_active,
            parent_id=department.parent_id,
            parent_name=parent_name,
            manager_id=department.manager_id,
            manager_name=manager_name,
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

    def get_direct_sub_departments(self, parent_id: DepartmentId) -> List[Department]:
        """Get direct sub-departments."""
        return (
            self.db.query(Department)
            .filter(Department.parent_id == parent_id, ~Department.is_deleted)
            .order_by(Department.display_order, Department.name)
            .all()
        )

    def get_all_sub_departments(self, parent_id: DepartmentId) -> List[Department]:
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
            self.db.query(Department)
            .filter(
                Department.parent_id == department_id,
                ~Department.is_deleted,
                Department.is_active,
            )
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

    def update_display_order(self, department_ids: List[DepartmentId]) -> None:
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
            .all()
        )

        # Check permissions
        for user_role in user_roles:
            if user_role.is_valid and user_role.role.has_permission(permission):
                return True

        return False
    
    def move_department(
        self, department_id: DepartmentId, new_parent_id: Optional[DepartmentId]
    ) -> Department:
        """Move department to a new parent with circular reference prevention."""
        department = self.repository.get(department_id)
        if not department:
            raise ValueError(f"Department {department_id} not found")
        
        # Check if moving to self
        if new_parent_id == department_id:
            raise BusinessLogicError("Department cannot be its own parent")
        
        # Check for circular reference
        if new_parent_id:
            new_parent = self.repository.get(new_parent_id)
            if not new_parent:
                raise ValueError(f"Parent department {new_parent_id} not found")
            
            # Check if new parent is a descendant of the department
            if new_parent.path.startswith(f"{department.path}."):
                raise BusinessLogicError(
                    "Cannot create circular reference: target parent is a descendant"
                )
            
            # Check depth limit (max 5 levels = depth 4)
            if new_parent.depth >= 4:
                raise BusinessLogicError(
                    "Cannot exceed maximum depth of 5 levels"
                )
        
        # Update parent
        old_path = department.path
        department.parent_id = new_parent_id
        department.update_path()
        
        # Update all descendants
        department.update_subtree_paths()
        
        self.db.commit()
        return department
    
    def get_ancestors(self, department_id: DepartmentId) -> List[Department]:
        """Get all ancestor departments from root to parent."""
        department = self.repository.get(department_id)
        if not department:
            return []
        
        ancestor_ids = department.get_ancestors_ids()
        if not ancestor_ids:
            return []
        
        # Get ancestors ordered by depth
        ancestors = (
            self.db.query(Department)
            .filter(Department.id.in_(ancestor_ids))
            .order_by(Department.depth)
            .all()
        )
        
        return ancestors
    
    def get_descendants(
        self, department_id: DepartmentId, recursive: bool = True
    ) -> List[Department]:
        """Get descendant departments."""
        department = self.repository.get(department_id)
        if not department:
            return []
        
        if not recursive:
            # Direct children only
            return self.get_direct_sub_departments(department_id)
        
        # All descendants using path
        descendants = (
            self.db.query(Department)
            .filter(
                Department.path.like(f"{department.path}.%"),
                ~Department.is_deleted
            )
            .order_by(Department.depth, Department.display_order)
            .all()
        )
        
        return descendants
    
    def get_subtree(self, department_id: DepartmentId) -> List[Department]:
        """Get department and all its descendants."""
        department = self.repository.get(department_id)
        if not department:
            return []
        
        # Get self and all descendants
        subtree = (
            self.db.query(Department)
            .filter(
                or_(
                    Department.id == department_id,
                    Department.path.like(f"{department.path}.%")
                ),
                ~Department.is_deleted
            )
            .order_by(Department.depth, Department.display_order)
            .all()
        )
        
        return subtree
    
    def get_departments_at_depth(
        self, depth: int, organization_id: OrganizationId
    ) -> List[Department]:
        """Get all departments at a specific depth level."""
        departments = (
            self.db.query(Department)
            .filter(
                Department.organization_id == organization_id,
                Department.depth == depth,
                ~Department.is_deleted
            )
            .order_by(Department.display_order, Department.name)
            .all()
        )
        
        return departments
    
    def validate_department_deletion(self, department_id: DepartmentId) -> None:
        """Validate if department can be deleted."""
        department = self.repository.get(department_id)
        if not department:
            raise ValueError(f"Department {department_id} not found")
        
        # Check for active sub-departments
        if self.has_sub_departments(department_id):
            raise BusinessLogicError(
                "Cannot delete department that has active sub-departments"
            )
        
        # Check for active users
        active_users = self.get_department_user_count(department_id)
        if active_users > 0:
            raise BusinessLogicError(
                f"Cannot delete department with {active_users} active users. "
                "Please reassign users before deletion."
            )
        
        # Check for active task assignments
        task_assignments = self.get_task_assignments_for_department(department_id)
        active_assignments = [a for a in task_assignments if a.is_active]
        if active_assignments:
            raise BusinessLogicError(
                f"Cannot delete department with {len(active_assignments)} active task assignments. "
                "Please remove or reassign tasks before deletion."
            )

    # Permission Inheritance Methods
    
    def get_user_department_permissions(
        self, user_id: UserId, department_id: DepartmentId
    ) -> List[str]:
        """Get permissions for user in specific department."""
        # Get user roles for the department
        user_roles = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.department_id == department_id,
                UserRole.is_active
            )
            .all()
        )
        
        permissions = []
        for user_role in user_roles:
            if user_role.role:
                # Get permissions from role
                role_permissions = (
                    self.db.query(RolePermission)
                    .filter(RolePermission.role_id == user_role.role_id)
                    .all()
                )
                for role_perm in role_permissions:
                    if role_perm.permission:
                        permissions.append(role_perm.permission.code)
        
        return list(set(permissions))  # Remove duplicates
    
    def get_user_effective_permissions(
        self, user_id: UserId, department_id: DepartmentId, use_most_specific: bool = False
    ) -> List[str]:
        """Get effective permissions for user considering inheritance."""
        department = self.repository.get(department_id)
        if not department:
            return []
        
        # Get direct permissions for the department
        permissions = set(self.get_user_department_permissions(user_id, department_id))
        
        # If inheritance is enabled, get permissions from parent departments
        if department.inherit_permissions and not use_most_specific:
            inheritance_chain = self.get_permission_inheritance_chain(department_id)
            for dept in inheritance_chain:
                if dept.id != department_id:  # Don't double-count current department
                    parent_permissions = self.get_user_department_permissions(user_id, dept.id)
                    permissions.update(parent_permissions)
        
        return list(permissions)
    
    def user_has_permission_for_department(
        self, user_id: UserId, permission: str, department_id: DepartmentId
    ) -> bool:
        """Check if user has specific permission for department."""
        effective_permissions = self.get_user_effective_permissions(user_id, department_id)
        return permission in effective_permissions
    
    def get_permission_inheritance_chain(self, department_id: DepartmentId) -> List[Department]:
        """Get the chain of departments for permission inheritance."""
        department = self.repository.get(department_id)
        if not department:
            return []
        
        chain = [department]
        
        # If inheritance is disabled, return only the current department
        if not department.inherit_permissions:
            return chain
        
        # Get all ancestors through the path
        if hasattr(department, 'path') and department.path:
            ancestor_ids = [int(id_str) for id_str in department.path.split('.')[:-1]]
            
            if ancestor_ids:
                ancestors = (
                    self.db.query(Department)
                    .filter(Department.id.in_(ancestor_ids))
                    .order_by(Department.depth)
                    .all()
                )
                
                # Only include ancestors that have inheritance enabled
                for ancestor in ancestors:
                    if ancestor.inherit_permissions:
                        chain.insert(0, ancestor)
                    else:
                        # If inheritance is broken at any level, stop
                        break
        
        return chain

    # Inter-Department Collaboration Methods
    
    def create_collaboration_agreement(
        self,
        department_a_id: DepartmentId,
        department_b_id: DepartmentId,
        collaboration_type: str,
        description: str = None,
        created_by: UserId = None,
        effective_from: datetime = None,
        effective_until: datetime = None,
    ) -> DepartmentCollaboration:
        """Create a collaboration agreement between two departments."""
        # Validate departments exist
        dept_a = self.repository.get(department_a_id)
        dept_b = self.repository.get(department_b_id)
        
        if not dept_a:
            raise ValueError(f"Department {department_a_id} not found")
        if not dept_b:
            raise ValueError(f"Department {department_b_id} not found")
        
        # Prevent self-collaboration
        if department_a_id == department_b_id:
            raise BusinessLogicError("Department cannot collaborate with itself")
        
        # Check if collaboration already exists
        existing = (
            self.db.query(DepartmentCollaboration)
            .filter(
                or_(
                    and_(
                        DepartmentCollaboration.department_a_id == department_a_id,
                        DepartmentCollaboration.department_b_id == department_b_id,
                    ),
                    and_(
                        DepartmentCollaboration.department_a_id == department_b_id,
                        DepartmentCollaboration.department_b_id == department_a_id,
                    ),
                ),
                DepartmentCollaboration.is_active == True,
                ~DepartmentCollaboration.is_deleted,
            )
            .first()
        )
        
        if existing:
            raise BusinessLogicError(
                "Active collaboration agreement already exists between these departments"
            )
        
        # Create collaboration agreement
        collaboration = DepartmentCollaboration(
            department_a_id=department_a_id,
            department_b_id=department_b_id,
            collaboration_type=collaboration_type,
            description=description,
            effective_from=effective_from,
            effective_until=effective_until,
            approval_status="approved",  # Auto-approve for simplicity
            created_by=created_by,
            updated_by=created_by,
        )
        
        self.db.add(collaboration)
        self.db.commit()
        
        return collaboration
    
    def get_collaboration_agreements(self, department_id: DepartmentId) -> List[DepartmentCollaboration]:
        """Get all collaboration agreements for a department."""
        agreements = (
            self.db.query(DepartmentCollaboration)
            .filter(
                or_(
                    DepartmentCollaboration.department_a_id == department_id,
                    DepartmentCollaboration.department_b_id == department_id,
                ),
                ~DepartmentCollaboration.is_deleted,
            )
            .all()
        )
        
        return agreements
    
    def get_collaborating_departments(self, department_id: DepartmentId) -> List[Department]:
        """Get all departments that have active collaboration with given department."""
        agreements = (
            self.db.query(DepartmentCollaboration)
            .filter(
                or_(
                    DepartmentCollaboration.department_a_id == department_id,
                    DepartmentCollaboration.department_b_id == department_id,
                ),
                DepartmentCollaboration.is_active == True,
                ~DepartmentCollaboration.is_deleted,
            )
            .all()
        )
        
        collaborating_dept_ids = []
        for agreement in agreements:
            other_dept_id = agreement.get_other_department_id(department_id)
            if other_dept_id:
                collaborating_dept_ids.append(other_dept_id)
        
        # Get the department objects
        if collaborating_dept_ids:
            departments = (
                self.db.query(Department)
                .filter(Department.id.in_(collaborating_dept_ids))
                .all()
            )
            return departments
        
        return []
    
    def can_departments_collaborate(
        self, department_a_id: DepartmentId, department_b_id: DepartmentId
    ) -> bool:
        """Check if two departments can collaborate (have active agreement)."""
        agreement = (
            self.db.query(DepartmentCollaboration)
            .filter(
                or_(
                    and_(
                        DepartmentCollaboration.department_a_id == department_a_id,
                        DepartmentCollaboration.department_b_id == department_b_id,
                    ),
                    and_(
                        DepartmentCollaboration.department_a_id == department_b_id,
                        DepartmentCollaboration.department_b_id == department_a_id,
                    ),
                ),
                DepartmentCollaboration.is_active == True,
                ~DepartmentCollaboration.is_deleted,
            )
            .first()
        )
        
        return agreement is not None
    
    def get_cross_department_permissions(
        self, user_id: UserId, source_department_id: DepartmentId, target_department_id: DepartmentId
    ) -> List[str]:
        """Get permissions user has in target department through collaboration."""
        # Check if departments can collaborate
        if not self.can_departments_collaborate(source_department_id, target_department_id):
            return []
        
        # Get user's permissions in source department
        source_permissions = self.get_user_department_permissions(user_id, source_department_id)
        
        # For full collaboration, return all permissions
        # For specific collaboration types, filter permissions
        agreement = (
            self.db.query(DepartmentCollaboration)
            .filter(
                or_(
                    and_(
                        DepartmentCollaboration.department_a_id == source_department_id,
                        DepartmentCollaboration.department_b_id == target_department_id,
                    ),
                    and_(
                        DepartmentCollaboration.department_a_id == target_department_id,
                        DepartmentCollaboration.department_b_id == source_department_id,
                    ),
                ),
                DepartmentCollaboration.is_active == True,
                ~DepartmentCollaboration.is_deleted,
            )
            .first()
        )
        
        if not agreement:
            return []
        
        # Filter permissions based on collaboration type
        if agreement.collaboration_type == "full_access":
            return source_permissions
        elif agreement.collaboration_type == "project_sharing":
            return [p for p in source_permissions if "project" in p.lower()]
        elif agreement.collaboration_type == "data_sharing":
            return [p for p in source_permissions if any(
                word in p.lower() for word in ["view", "read", "report"]
            )]
        else:
            # For other collaboration types, return limited permissions
            return [p for p in source_permissions if "view" in p.lower()]
    
    def activate_collaboration_agreement(
        self, agreement_id: int, updated_by: UserId = None
    ) -> DepartmentCollaboration:
        """Activate a collaboration agreement."""
        agreement = self.db.query(DepartmentCollaboration).filter(
            DepartmentCollaboration.id == agreement_id
        ).first()
        
        if not agreement:
            raise ValueError(f"Collaboration agreement {agreement_id} not found")
        
        agreement.is_active = True
        agreement.updated_by = updated_by
        self.db.commit()
        
        return agreement
    
    def deactivate_collaboration_agreement(
        self, agreement_id: int, updated_by: UserId = None
    ) -> DepartmentCollaboration:
        """Deactivate a collaboration agreement."""
        agreement = self.db.query(DepartmentCollaboration).filter(
            DepartmentCollaboration.id == agreement_id
        ).first()
        
        if not agreement:
            raise ValueError(f"Collaboration agreement {agreement_id} not found")
        
        agreement.is_active = False
        agreement.updated_by = updated_by
        self.db.commit()
        
        return agreement

    # Task Management Integration Methods
    
    def assign_task_to_department(
        self,
        task_id: int,
        department_id: DepartmentId,
        assignment_type: str = "department",
        visibility_scope: str = "department",
        assigned_by: UserId = None,
        notes: str = None,
    ) -> DepartmentTask:
        """Assign a task to a department."""
        # Validate task exists
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Validate department exists
        department = self.repository.get(department_id)
        if not department:
            raise ValueError(f"Department {department_id} not found")
        
        # Check if assignment already exists
        existing = (
            self.db.query(DepartmentTask)
            .filter(
                DepartmentTask.task_id == task_id,
                DepartmentTask.department_id == department_id,
                DepartmentTask.is_active == True,
                ~DepartmentTask.is_deleted,
            )
            .first()
        )
        
        if existing:
            raise BusinessLogicError(
                f"Task {task_id} is already assigned to department {department_id}"
            )
        
        # Create assignment
        assignment = DepartmentTask(
            task_id=task_id,
            department_id=department_id,
            assignment_type=assignment_type,
            visibility_scope=visibility_scope,
            assignment_notes=notes,
            created_by=assigned_by,
            updated_by=assigned_by,
        )
        
        self.db.add(assignment)
        self.db.commit()
        
        return assignment
    
    def get_department_tasks(
        self,
        department_id: DepartmentId,
        include_inherited: bool = True,
        include_delegated: bool = True,
        status_filter: List[str] = None,
        priority_filter: List[str] = None,
    ) -> List[Task]:
        """Get all tasks assigned to a department."""
        department = self.repository.get(department_id)
        if not department:
            return []
        
        # Start with direct assignments
        query = (
            self.db.query(Task)
            .join(DepartmentTask)
            .filter(
                DepartmentTask.department_id == department_id,
                DepartmentTask.is_active == True,
                ~DepartmentTask.is_deleted,
                ~Task.is_deleted,
            )
        )
        
        # Build assignment type filter
        assignment_types = ["department"]
        if include_inherited:
            assignment_types.append("inherited")
        if include_delegated:
            assignment_types.append("delegated")
        
        query = query.filter(DepartmentTask.assignment_type.in_(assignment_types))
        
        # Apply task filters
        if status_filter:
            query = query.filter(Task.status.in_(status_filter))
        
        if priority_filter:
            query = query.filter(Task.priority.in_(priority_filter))
        
        tasks = query.distinct().all()
        
        # If including inherited tasks, get tasks from parent departments
        if include_inherited and department.inherit_permissions:
            ancestors = self.get_ancestors(department_id)
            for ancestor in ancestors:
                if ancestor.inherit_permissions:
                    parent_tasks = self._get_inheritable_tasks(ancestor.id, status_filter, priority_filter)
                    # Create inherited assignments if not already exist
                    for task in parent_tasks:
                        if not self._has_department_task_assignment(task.id, department_id):
                            self._create_inherited_assignment(task.id, department_id, ancestor.id)
                            tasks.append(task)
        
        return tasks
    
    def delegate_task(
        self,
        task_id: int,
        from_department_id: DepartmentId,
        to_department_id: DepartmentId,
        delegated_by: UserId,
        notes: str = None,
    ) -> DepartmentTask:
        """Delegate a task from one department to another."""
        # Validate departments
        from_dept = self.repository.get(from_department_id)
        to_dept = self.repository.get(to_department_id)
        
        if not from_dept:
            raise ValueError(f"Source department {from_department_id} not found")
        if not to_dept:
            raise ValueError(f"Target department {to_department_id} not found")
        
        # Check if source department has the task
        source_assignment = (
            self.db.query(DepartmentTask)
            .filter(
                DepartmentTask.task_id == task_id,
                DepartmentTask.department_id == from_department_id,
                DepartmentTask.is_active == True,
                ~DepartmentTask.is_deleted,
            )
            .first()
        )
        
        if not source_assignment:
            raise BusinessLogicError(
                f"Task {task_id} is not assigned to department {from_department_id}"
            )
        
        # Check if departments can collaborate or if it's within hierarchy
        can_delegate = (
            self.can_departments_collaborate(from_department_id, to_department_id) or
            to_dept.is_descendant_of(from_department_id) or
            to_dept.is_ancestor_of(from_department_id)
        )
        
        if not can_delegate:
            raise BusinessLogicError(
                "Departments must have collaboration agreement or be in same hierarchy to delegate tasks"
            )
        
        # Create delegation assignment
        delegation = DepartmentTask(
            task_id=task_id,
            department_id=to_department_id,
            assignment_type="delegated",
            visibility_scope=source_assignment.visibility_scope,
            delegated_from_department_id=from_department_id,
            delegated_by=delegated_by,
            assignment_notes=notes,
            created_by=delegated_by,
            updated_by=delegated_by,
        )
        
        self.db.add(delegation)
        self.db.commit()
        
        return delegation
    
    def get_task_assignments_for_department(
        self, department_id: DepartmentId
    ) -> List[DepartmentTask]:
        """Get all task assignments for a department."""
        assignments = (
            self.db.query(DepartmentTask)
            .filter(
                DepartmentTask.department_id == department_id,
                DepartmentTask.is_active == True,
                ~DepartmentTask.is_deleted,
            )
            .all()
        )
        
        return assignments
    
    def remove_task_from_department(
        self, task_id: int, department_id: DepartmentId, removed_by: UserId = None
    ) -> bool:
        """Remove task assignment from department."""
        assignment = (
            self.db.query(DepartmentTask)
            .filter(
                DepartmentTask.task_id == task_id,
                DepartmentTask.department_id == department_id,
                DepartmentTask.is_active == True,
                ~DepartmentTask.is_deleted,
            )
            .first()
        )
        
        if not assignment:
            return False
        
        # Soft delete the assignment
        assignment.soft_delete(deleted_by=removed_by)
        self.db.commit()
        
        return True
    
    def get_department_task_statistics(self, department_id: DepartmentId) -> Dict[str, Any]:
        """Get task statistics for a department."""
        assignments = self.get_task_assignments_for_department(department_id)
        
        if not assignments:
            return {
                "total_tasks": 0,
                "by_status": {},
                "by_priority": {},
                "by_assignment_type": {},
                "overdue_tasks": 0,
            }
        
        task_ids = [a.task_id for a in assignments]
        tasks = (
            self.db.query(Task)
            .filter(Task.id.in_(task_ids), ~Task.is_deleted)
            .all()
        )
        
        # Calculate statistics
        total_tasks = len(tasks)
        by_status = {}
        by_priority = {}
        by_assignment_type = {}
        overdue_tasks = 0
        
        now = datetime.utcnow()
        
        for task in tasks:
            # Status statistics
            status = task.status
            by_status[status] = by_status.get(status, 0) + 1
            
            # Priority statistics
            priority = task.priority
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            # Check if overdue
            if task.due_date and task.due_date < now and task.status not in ["completed", "cancelled"]:
                overdue_tasks += 1
        
        # Assignment type statistics
        for assignment in assignments:
            assignment_type = assignment.assignment_type
            by_assignment_type[assignment_type] = by_assignment_type.get(assignment_type, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_assignment_type": by_assignment_type,
            "overdue_tasks": overdue_tasks,
        }
    
    def _get_inheritable_tasks(
        self, department_id: DepartmentId, status_filter: List[str] = None, priority_filter: List[str] = None
    ) -> List[Task]:
        """Get tasks from a department that can be inherited."""
        query = (
            self.db.query(Task)
            .join(DepartmentTask)
            .filter(
                DepartmentTask.department_id == department_id,
                DepartmentTask.is_active == True,
                DepartmentTask.visibility_scope.in_(["department", "organization"]),
                ~DepartmentTask.is_deleted,
                ~Task.is_deleted,
            )
        )
        
        if status_filter:
            query = query.filter(Task.status.in_(status_filter))
        
        if priority_filter:
            query = query.filter(Task.priority.in_(priority_filter))
        
        return query.all()
    
    def _has_department_task_assignment(self, task_id: int, department_id: DepartmentId) -> bool:
        """Check if department already has an assignment for the task."""
        assignment = (
            self.db.query(DepartmentTask)
            .filter(
                DepartmentTask.task_id == task_id,
                DepartmentTask.department_id == department_id,
                DepartmentTask.is_active == True,
                ~DepartmentTask.is_deleted,
            )
            .first()
        )
        
        return assignment is not None
    
    def _create_inherited_assignment(
        self, task_id: int, department_id: DepartmentId, inherited_from_id: DepartmentId
    ) -> DepartmentTask:
        """Create an inherited task assignment."""
        assignment = DepartmentTask(
            task_id=task_id,
            department_id=department_id,
            assignment_type="inherited",
            visibility_scope="department",
            assignment_notes=f"Inherited from department {inherited_from_id}",
        )
        
        self.db.add(assignment)
        self.db.flush()  # Don't commit yet, let the caller decide
        
        return assignment

    def cascade_delete_department(self, department_id: DepartmentId, deleted_by: UserId) -> bool:
        """Cascade delete department and handle sub-departments."""
        department = self.get_department(department_id)
        if not department:
            return False
        
        # Get all sub-departments
        sub_departments = self.get_all_sub_departments(department_id)
        
        # Delete sub-departments first (deepest first)
        for sub_dept in reversed(sub_departments):
            # Remove task assignments
            self.db.query(DepartmentTask).filter(
                DepartmentTask.department_id == sub_dept.id,
                DepartmentTask.is_active == True
            ).update({"is_active": False, "updated_by": deleted_by})
            
            # Soft delete sub-department
            sub_dept.is_deleted = True
            sub_dept.deleted_by = deleted_by
            sub_dept.deleted_at = datetime.utcnow()
        
        # Remove task assignments from main department
        self.db.query(DepartmentTask).filter(
            DepartmentTask.department_id == department_id,
            DepartmentTask.is_active == True
        ).update({"is_active": False, "updated_by": deleted_by})
        
        # Delete main department
        department.is_deleted = True
        department.deleted_by = deleted_by
        department.deleted_at = datetime.utcnow()
        
        self.db.commit()
        return True

    def promote_sub_departments(self, department_id: DepartmentId, promoted_by: UserId) -> List[Department]:
        """Promote sub-departments to parent level when deleting a department."""
        department = self.get_department(department_id)
        if not department:
            return []
        
        # Get direct sub-departments
        sub_departments = self.get_direct_sub_departments(department_id)
        
        # Promote each sub-department to parent level
        for sub_dept in sub_departments:
            sub_dept.parent_id = department.parent_id
            sub_dept.updated_by = promoted_by
            sub_dept.updated_at = datetime.utcnow()
            
            # Update materialized path if using it
            if hasattr(sub_dept, 'path'):
                if department.parent_id:
                    parent = self.get_department(department.parent_id)
                    sub_dept.path = f"{parent.path}.{sub_dept.id}"
                else:
                    sub_dept.path = str(sub_dept.id)
        
        self.db.commit()
        return sub_departments

    def get_department_health_status(self, department_id: DepartmentId) -> Dict[str, Any]:
        """Get comprehensive health status of a department."""
        department = self.get_department(department_id)
        if not department:
            return {"status": "not_found"}
        
        # Get basic metrics
        user_count = self.get_department_user_count(department_id)
        task_stats = self.get_department_task_statistics(department_id)
        sub_dept_count = len(self.get_direct_sub_departments(department_id))
        
        # Calculate health metrics
        health_score = 100
        issues = []
        
        # Check for inactive manager
        if department.manager_id:
            manager = self.db.query(User).filter(User.id == department.manager_id).first()
            if not manager or not manager.is_active:
                health_score -= 20
                issues.append("inactive_manager")
        else:
            health_score -= 10
            issues.append("no_manager")
        
        # Check for overdue tasks
        if task_stats.get("overdue_tasks", 0) > 0:
            overdue_ratio = task_stats["overdue_tasks"] / max(task_stats.get("total_tasks", 1), 1)
            health_score -= min(30, int(overdue_ratio * 100))
            issues.append("overdue_tasks")
        
        # Check for inactive status
        if not department.is_active:
            health_score -= 50
            issues.append("inactive_department")
        
        # Check for empty department
        if user_count == 0:
            health_score -= 15
            issues.append("no_users")
        
        # Determine status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "warning"
        elif health_score >= 40:
            status = "critical"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "health_score": max(0, health_score),
            "issues": issues,
            "metrics": {
                "user_count": user_count,
                "sub_department_count": sub_dept_count,
                "total_tasks": task_stats.get("total_tasks", 0),
                "overdue_tasks": task_stats.get("overdue_tasks", 0),
            }
        }

    def bulk_update_department_status(
        self, department_ids: List[DepartmentId], is_active: bool, updated_by: UserId
    ) -> Dict[str, Any]:
        """Bulk update status for multiple departments."""
        results = {"success": [], "failed": [], "skipped": []}
        
        for dept_id in department_ids:
            department = self.get_department(dept_id)
            if not department:
                results["failed"].append({"id": dept_id, "reason": "not_found"})
                continue
            
            # Skip if already in desired state
            if department.is_active == is_active:
                results["skipped"].append({"id": dept_id, "reason": "already_in_state"})
                continue
            
            # Check if deactivation is allowed
            if not is_active:
                # Check for active users
                if self.get_department_user_count(dept_id) > 0:
                    results["failed"].append({"id": dept_id, "reason": "has_active_users"})
                    continue
                
                # Check for active tasks
                task_stats = self.get_department_task_statistics(dept_id)
                if task_stats.get("total_tasks", 0) > 0:
                    results["failed"].append({"id": dept_id, "reason": "has_active_tasks"})
                    continue
            
            # Update status
            department.is_active = is_active
            department.updated_by = updated_by
            department.updated_at = datetime.utcnow()
            
            results["success"].append({"id": dept_id, "name": department.name})
        
        self.db.commit()
        return results

    def validate_department_hierarchy(self, organization_id: OrganizationId) -> Dict[str, Any]:
        """Validate department hierarchy integrity for an organization."""
        issues = []
        
        # Get all departments for organization
        departments = self.db.query(Department).filter(
            Department.organization_id == organization_id,
            ~Department.is_deleted
        ).all()
        
        dept_dict = {dept.id: dept for dept in departments}
        
        # Check for circular references
        for dept in departments:
            if dept.parent_id:
                visited = set()
                current = dept
                while current.parent_id:
                    if current.parent_id in visited:
                        issues.append({
                            "type": "circular_reference",
                            "department_id": dept.id,
                            "department_name": dept.name
                        })
                        break
                    visited.add(current.id)
                    current = dept_dict.get(current.parent_id)
                    if not current:
                        issues.append({
                            "type": "missing_parent",
                            "department_id": dept.id,
                            "department_name": dept.name,
                            "parent_id": dept.parent_id
                        })
                        break
        
        # Check for orphaned departments
        for dept in departments:
            if dept.parent_id and dept.parent_id not in dept_dict:
                issues.append({
                    "type": "orphaned_department",
                    "department_id": dept.id,
                    "department_name": dept.name,
                    "missing_parent_id": dept.parent_id
                })
        
        # Check for depth violations
        MAX_DEPTH = 10
        for dept in departments:
            if not dept.parent_id:  # Root department
                depth = self._calculate_depth(dept, dept_dict)
                if depth > MAX_DEPTH:
                    issues.append({
                        "type": "max_depth_exceeded",
                        "department_id": dept.id,
                        "department_name": dept.name,
                        "depth": depth
                    })
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "total_departments": len(departments),
            "total_issues": len(issues)
        }

    def _calculate_depth(self, department: Department, dept_dict: Dict[int, Department]) -> int:
        """Calculate maximum depth of department hierarchy."""
        max_depth = 0
        
        def calculate_subtree_depth(dept: Department, current_depth: int) -> int:
            children = [d for d in dept_dict.values() if d.parent_id == dept.id]
            if not children:
                return current_depth
            
            max_child_depth = current_depth
            for child in children:
                child_depth = calculate_subtree_depth(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
            
            return max_child_depth
        
        return calculate_subtree_depth(department, 1)
