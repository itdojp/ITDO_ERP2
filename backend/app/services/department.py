"""Department service implementation."""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.department import Department
from app.models.user import User
from app.models.role import UserRole
from app.repositories.department import DepartmentRepository
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentSummary,
    DepartmentTree,
    DepartmentWithUsers
)
from app.schemas.user import UserBasic, UserSummary
from app.types import DepartmentId, UserId, OrganizationId


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
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
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
        organization_id: Optional[OrganizationId] = None
    ) -> Tuple[List[Department], int]:
        """Search departments by name."""
        # Build search conditions
        search_condition = or_(
            Department.name.ilike(f"%{query}%"),
            Department.name_en.ilike(f"%{query}%"),
            Department.code.ilike(f"%{query}%")
        )
        
        conditions = [search_condition]
        if organization_id:
            conditions.append(Department.organization_id == organization_id)
        
        # Get all matching departments
        all_results = self.db.query(Department).filter(
            and_(*conditions),
            Department.is_deleted == False
        ).order_by(Department.updated_at.desc()).all()
        
        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[skip:skip + limit]
        
        return paginated_results, total
    
    def create_department(
        self,
        department_data: DepartmentCreate,
        created_by: Optional[UserId] = None
    ) -> Department:
        """Create a new department."""
        # Validate unique code within organization
        existing = self.db.query(Department).filter(
            Department.organization_id == department_data.organization_id,
            Department.code == department_data.code,
            Department.is_deleted == False
        ).first()
        
        if existing:
            raise ValueError(f"Department code '{department_data.code}' already exists in this organization")
        
        # Add audit fields
        data = department_data.model_dump()
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by
        
        # Create department
        return self.repository.create(DepartmentCreate(**data))
    
    def update_department(
        self,
        department_id: DepartmentId,
        department_data: DepartmentUpdate,
        updated_by: Optional[UserId] = None
    ) -> Optional[Department]:
        """Update department details."""
        # Check if department exists
        department = self.repository.get(department_id)
        if not department:
            return None
        
        # Validate unique code if being changed
        if department_data.code and department_data.code != department.code:
            existing = self.db.query(Department).filter(
                Department.organization_id == department.organization_id,
                Department.code == department_data.code,
                Department.id != department_id,
                Department.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError(f"Department code '{department_data.code}' already exists in this organization")
        
        # Add audit fields
        data = department_data.model_dump(exclude_unset=True)
        if updated_by:
            data["updated_by"] = updated_by
        
        # Update department
        return self.repository.update(department_id, DepartmentUpdate(**data))
    
    def delete_department(
        self,
        department_id: DepartmentId,
        deleted_by: Optional[UserId] = None
    ) -> bool:
        """Soft delete a department."""
        department = self.repository.get(department_id)
        if not department:
            return False
        
        # Perform soft delete
        department.soft_delete(deleted_by=deleted_by)
        self.db.commit()
        return True
    
    def get_department_tree(self, organization_id: OrganizationId) -> List[DepartmentTree]:
        """Get department hierarchy tree for an organization."""
        # Get root departments
        roots = self.db.query(Department).filter(
            Department.organization_id == organization_id,
            Department.parent_id == None,
            Department.is_deleted == False
        ).order_by(Department.display_order, Department.name).all()
        
        def build_tree(dept: Department, level: int = 0) -> DepartmentTree:
            """Build tree recursively."""
            children = []
            sub_depts = self.db.query(Department).filter(
                Department.parent_id == dept.id,
                Department.is_deleted == False
            ).order_by(Department.display_order, Department.name).all()
            
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
                children=children
            )
        
        return [build_tree(root) for root in roots]
    
    def get_department_summary(self, department: Department) -> DepartmentSummary:
        """Get department summary with counts."""
        parent_name = department.parent.name if department.parent else None
        manager_name = None
        
        if department.manager_id:
            manager = self.db.query(User).filter(User.id == department.manager_id).first()
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
            sub_department_count=sub_department_count
        )
    
    def get_department_response(self, department: Department) -> DepartmentResponse:
        """Get full department response."""
        # Load related data if needed
        if department.parent_id and not department.parent:
            department = self.repository.get_with_parent(department.id)
        
        # Get manager info
        manager = None
        if department.manager_id:
            manager_obj = self.db.query(User).filter(User.id == department.manager_id).first()
            if manager_obj:
                manager = UserSummary(
                    id=manager_obj.id,
                    email=manager_obj.email,
                    full_name=manager_obj.full_name,
                    employee_code=manager_obj.employee_code,
                    is_active=manager_obj.is_active
                )
        
        # Build response
        data = department.to_dict()
        data["parent"] = department.parent.to_dict() if department.parent else None
        data["manager"] = manager.model_dump() if manager else None
        data["full_path"] = department.full_path
        data["is_leaf"] = department.is_leaf
        
        return DepartmentResponse.model_validate(data)
    
    def get_department_with_users(
        self,
        department: Department,
        include_sub_departments: bool = False
    ) -> DepartmentWithUsers:
        """Get department with user list."""
        # Get department IDs to include
        department_ids = [department.id]
        if include_sub_departments:
            sub_depts = self.get_all_sub_departments(department.id)
            department_ids.extend([d.id for d in sub_depts])
        
        # Get users
        users = self.db.query(User).filter(
            # Get users from user_roles that have department_id in department_ids
            User.id.in_(
                self.db.query(UserRole.user_id).filter(
                    UserRole.department_id.in_(department_ids),
                    UserRole.is_active == True
                ).subquery()
            ),
            User.is_active == True
        ).order_by(User.full_name).all()
        
        # Convert to UserSummary
        user_summaries = [
            UserSummary(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                employee_code=user.employee_code,
                is_active=user.is_active
            )
            for user in users
        ]
        
        # Get department response
        dept_response = self.get_department_response(department)
        
        return DepartmentWithUsers(
            **dept_response.model_dump(),
            users=user_summaries,
            total_users=len(user_summaries)
        )
    
    def get_direct_sub_departments(self, parent_id: DepartmentId) -> List[Department]:
        """Get direct sub-departments."""
        return self.db.query(Department).filter(
            Department.parent_id == parent_id,
            Department.is_deleted == False
        ).order_by(Department.display_order, Department.name).all()
    
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
        return self.db.query(Department).filter(
            Department.parent_id == department_id,
            Department.is_deleted == False,
            Department.is_active == True
        ).first() is not None
    
    def get_department_user_count(self, department_id: DepartmentId) -> int:
        """Get count of active users in department."""
        return self.db.query(User).filter(
            User.id.in_(
                self.db.query(UserRole.user_id).filter(
                    UserRole.department_id == department_id,
                    UserRole.is_active == True
                ).subquery()
            ),
            User.is_active == True
        ).count()
    
    def get_sub_department_count(self, parent_id: DepartmentId) -> int:
        """Get count of direct sub-departments."""
        return self.db.query(Department).filter(
            Department.parent_id == parent_id,
            Department.is_deleted == False
        ).count()
    
    def update_display_order(self, department_ids: List[DepartmentId]) -> None:
        """Update display order for departments."""
        for i, dept_id in enumerate(department_ids):
            dept = self.repository.get(dept_id)
            if dept:
                dept.display_order = i
        self.db.commit()
    
    def user_has_permission(
        self,
        user_id: UserId,
        permission: str,
        organization_id: OrganizationId
    ) -> bool:
        """Check if user has permission for departments in an organization."""
        # Get user roles for the organization
        user_roles = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == organization_id,
            UserRole.is_active == True
        ).all()
        
        # Check permissions
        for user_role in user_roles:
            if user_role.is_valid and user_role.role.has_permission(permission):
                return True
        
        return False