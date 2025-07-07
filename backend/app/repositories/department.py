"""Department repository implementation."""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_, func, update
from app.repositories.base import BaseRepository
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.types import DepartmentId, OrganizationId, UserId


class DepartmentRepository(BaseRepository[Department, DepartmentCreate, DepartmentUpdate]):
    """Repository for department operations."""
    
    def get_by_code(self, code: str, organization_id: OrganizationId) -> Optional[Department]:
        """Get department by code within organization."""
        return self.db.scalar(
            select(self.model)
            .where(self.model.code == code)
            .where(self.model.organization_id == organization_id)
        )
    
    def get_by_organization(
        self,
        organization_id: OrganizationId,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Department]:
        """Get departments by organization."""
        query = select(self.model).where(self.model.organization_id == organization_id)
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        query = query.where(self.model.is_deleted == False)
        query = query.order_by(self.model.display_order, self.model.name)
        query = query.offset(skip).limit(limit)
        
        return list(self.db.scalars(query))
    
    def get_root_departments(self, organization_id: OrganizationId) -> List[Department]:
        """Get root departments (without parent) in organization."""
        return list(self.db.scalars(
            select(self.model)
            .where(self.model.organization_id == organization_id)
            .where(self.model.parent_id == None)
            .where(self.model.is_deleted == False)
            .order_by(self.model.display_order, self.model.name)
        ))
    
    def get_sub_departments(self, parent_id: DepartmentId) -> List[Department]:
        """Get direct sub-departments."""
        return list(self.db.scalars(
            select(self.model)
            .where(self.model.parent_id == parent_id)
            .where(self.model.is_deleted == False)
            .order_by(self.model.display_order, self.model.name)
        ))
    
    def get_by_manager(self, manager_id: UserId) -> List[Department]:
        """Get departments managed by a user."""
        return list(self.db.scalars(
            select(self.model)
            .where(self.model.manager_id == manager_id)
            .where(self.model.is_deleted == False)
            .order_by(self.model.name)
        ))
    
    def get_with_relations(self, id: int) -> Optional[Department]:
        """Get department with all relations loaded."""
        return self.db.scalar(
            select(self.model)
            .options(
                joinedload(self.model.organization),
                joinedload(self.model.parent),
                joinedload(self.model.manager)
            )
            .where(self.model.id == id)
        )
    
    def search_by_name(
        self,
        query: str,
        organization_id: Optional[OrganizationId] = None
    ) -> List[Department]:
        """Search departments by name."""
        search_term = f"%{query}%"
        q = select(self.model).where(
            or_(
                self.model.name.ilike(search_term),
                self.model.name_kana.ilike(search_term),
                self.model.name_en.ilike(search_term),
                self.model.short_name.ilike(search_term),
                self.model.code.ilike(search_term)
            )
        )
        
        if organization_id:
            q = q.where(self.model.organization_id == organization_id)
        
        q = q.where(self.model.is_deleted == False)
        q = q.order_by(self.model.name)
        
        return list(self.db.scalars(q))
    
    def get_by_type(
        self,
        department_type: str,
        organization_id: Optional[OrganizationId] = None
    ) -> List[Department]:
        """Get departments by type."""
        query = select(self.model).where(self.model.department_type == department_type)
        
        if organization_id:
            query = query.where(self.model.organization_id == organization_id)
        
        query = query.where(self.model.is_deleted == False)
        query = query.order_by(self.model.name)
        
        return list(self.db.scalars(query))
    
    def get_by_cost_center(self, cost_center_code: str) -> Optional[Department]:
        """Get department by cost center code."""
        return self.db.scalar(
            select(self.model)
            .where(self.model.cost_center_code == cost_center_code)
            .where(self.model.is_deleted == False)
        )
    
    def get_with_parent(self, department_id: DepartmentId) -> Optional[Department]:
        """Get department with parent eager loaded."""
        return self.db.scalar(
            select(self.model)
            .options(joinedload(self.model.parent))
            .where(self.model.id == department_id)
            .where(self.model.is_deleted == False)
        )
    
    def validate_unique_code(
        self,
        code: str,
        organization_id: OrganizationId,
        exclude_id: Optional[int] = None
    ) -> bool:
        """Validate if department code is unique within organization."""
        query = select(func.count(self.model.id))
        query = query.where(self.model.code == code)
        query = query.where(self.model.organization_id == organization_id)
        
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        
        count = self.db.scalar(query) or 0
        return count == 0
    
    def get_headcount_stats(self, department_id: DepartmentId) -> Dict[str, int]:
        """Get headcount statistics for department."""
        from app.models.role import UserRole
        
        # Current headcount
        current = self.db.scalar(
            select(func.count(func.distinct(UserRole.user_id)))
            .where(UserRole.department_id == department_id)
            .where(UserRole.is_active == True)
        ) or 0
        
        dept = self.get(department_id)
        limit = dept.headcount_limit if dept else None
        
        return {
            "current": current,
            "limit": limit,
            "available": (limit - current) if limit else None,
            "is_over": current > limit if limit else False
        }
    
    def update_display_order(self, department_ids: List[DepartmentId]) -> None:
        """Update display order for multiple departments."""
        for index, dept_id in enumerate(department_ids):
            self.db.execute(
                update(self.model)
                .where(self.model.id == dept_id)
                .values(display_order=index)
            )
        self.db.commit()