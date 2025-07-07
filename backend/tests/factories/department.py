"""Factory for Department model."""

from typing import Dict, Any, Type, Optional, List
from sqlalchemy.orm import Session, List
from datetime import datetime

from app.models.department import Department
from app.models.organization import Organization
from tests.factories import BaseFactory, fake
from tests.factories.organization import OrganizationFactory


class DepartmentFactory(BaseFactory[Department]):
    """Factory for creating Department test instances."""
    
    @property
    def model_class(self) -> Type[Department]:
        """Return the Department model class."""
        return Department
    
    @classmethod
    def _get_default_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for creating Department instances."""
        return {
            "code": fake.unique.bothify(text="DEPT-####"),
            "name": fake.random_element(elements=(
                "総務部", "人事部", "経理部", "営業部", "開発部", 
                "マーケティング部", "企画部", "法務部", "情報システム部"
            )),
            "name_en": fake.random_element(elements=(
                "General Affairs", "Human Resources", "Accounting", "Sales", "Development",
                "Marketing", "Planning", "Legal", "Information Systems"
            )),
            "description": fake.text(max_nb_chars=200),
            "department_type": fake.random_element(elements=("operational", "support", "management")),
            "cost_center": fake.bothify(text="CC-####"),
            "budget": fake.random_int(min=1000000, max=50000000),
            "display_order": fake.random_int(min=1, max=100),
            "is_active": True
        }
    
    @classmethod
    def _get_update_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for updating Department instances."""
        return {
            "name": fake.random_element(elements=(
                "総務部", "人事部", "経理部", "営業部", "開発部"
            )),
            "description": fake.text(max_nb_chars=200),
            "budget": fake.random_int(min=1000000, max=50000000),
            "is_active": fake.boolean(),
            "display_order": fake.random_int(min=1, max=100)
        }
    
    @classmethod
    def create_with_organization(cls, db_session: Session, organization: Organization, **kwargs: Any) -> Department:
        """Create a department for a specific organization."""
        kwargs['organization_id'] = organization.id
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_with_parent(cls, db_session: Session, parent_department: Department, **kwargs: Any) -> Department:
        """Create a department with a parent department."""
        kwargs['parent_id'] = parent_department.id
        kwargs['organization_id'] = parent_department.organization_id
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_department_tree(cls, db_session: Session, organization: Organization, depth: int = 3, children_per_level: int = 2) -> Dict[str, Any]:
        """Create a tree of departments within an organization."""
        # Create root departments
        root_departments = []
        for i in range(children_per_level):
            root = cls.create_with_organization(
                db_session,
                organization,
                name=f"事業部{i+1}",
                name_en=f"Business Division {i+1}",
                code=f"DIV-{i+1:02d}",
                department_type="management"
            )
            root_departments.append(root)
        
        def create_children(parent_dept: Department, current_depth: int, dept_prefix: str) -> List[Department]:
            if current_depth >= depth:
                return []
            
            children = []
            for i in range(children_per_level):
                child_name = f"{dept_prefix}部門{i+1}"
                child_name_en = f"{dept_prefix} Department {i+1}"
                child_code = f"{parent_dept.code}-{i+1:02d}"
                
                child = cls.create_with_parent(
                    db_session,
                    parent_dept,
                    name=child_name,
                    name_en=child_name_en,
                    code=child_code,
                    department_type="operational" if current_depth == depth - 1 else "support"
                )
                children.append(child)
                
                # Recursively create sub-departments
                grandchildren = create_children(child, current_depth + 1, f"{dept_prefix}-{i+1}")
                children.extend(grandchildren)
            
            return children
        
        all_departments = root_departments[:]
        for i, root in enumerate(root_departments):
            children = create_children(root, 1, f"D{i+1}")
            all_departments.extend(children)
        
        return {
            'organization': organization,
            'roots': root_departments,
            'all': all_departments,
            'tree_depth': depth,
            'children_per_level': children_per_level
        }
    
    @classmethod
    def create_with_manager(cls, db_session: Session, manager_id: int, **kwargs: Any) -> Department:
        """Create a department with a specific manager."""
        kwargs['manager_id'] = manager_id
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_inactive(cls, db_session: Session, **kwargs: Any) -> Department:
        """Create an inactive department."""
        kwargs['is_active'] = False
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_by_type(cls, db_session: Session, department_type: str, **kwargs: Any) -> Department:
        """Create a department of a specific type."""
        kwargs['department_type'] = department_type
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_full_organization_structure(cls, db_session: Session) -> Dict[str, Any]:
        """Create a complete organization with departments."""
        # Create organization
        organization = OrganizationFactory.create(db_session, name="テスト株式会社")
        
        # Create department structure
        departments = cls.create_department_tree(db_session, organization, depth=3, children_per_level=2)
        
        return {
            'organization': organization,
            'departments': departments,
            'total_departments': len(departments['all'])
        }
    
    @classmethod
    def create_minimal(cls, db_session: Session, organization_id: int, **kwargs: Any) -> Department:
        """Create a department with minimal required fields."""
        minimal_attrs = {
            "code": fake.unique.bothify(text="DEPT-####"),
            "name": fake.word(),
            "organization_id": organization_id,
            "is_active": True
        }
        minimal_attrs.update(kwargs)
        return cls.create(db_session, **minimal_attrs)
    
    @classmethod
    def create_ordered_list(cls, db_session: Session, organization: Organization, count: int = 5) -> List[Department]:
        """Create a list of departments with specific display order."""
        departments = []
        for i in range(count):
            dept = cls.create_with_organization(
                db_session,
                organization,
                name=f"部門{i+1:02d}",
                code=f"DEPT-{i+1:02d}",
                display_order=i + 1
            )
            departments.append(dept)
        
        return departments