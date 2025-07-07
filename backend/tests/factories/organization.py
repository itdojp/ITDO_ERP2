"""Factory for Organization model."""

from typing import Dict, Any, Type
from sqlalchemy.orm import Session, Optional
from datetime import datetime

from app.models.organization import Organization
from tests.factories import BaseFactory, fake


class OrganizationFactory(BaseFactory[Organization]):
    """Factory for creating Organization test instances."""
    
    @property
    def model_class(self) -> Type[Organization]:
        """Return the Organization model class."""
        return Organization
    
    @classmethod
    def _get_default_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for creating Organization instances."""
        return {
            "code": fake.unique.company_suffix(),
            "name": fake.company(),
            "name_en": fake.company(),
            "description": fake.catch_phrase(),
            "business_type": fake.random_element(elements=("株式会社", "有限会社", "合同会社", "個人事業主")),
            "industry": fake.random_element(elements=("IT", "製造業", "小売業", "金融業", "教育", "医療")),
            "postal_code": fake.postcode(),
            "prefecture": fake.prefecture(),
            "city": fake.city(),
            "address_line1": fake.street_address(),
            "address_line2": fake.building_name(),
            "phone": fake.phone_number(),
            "fax": fake.phone_number(),
            "email": fake.company_email(),
            "website": fake.url(),
            "tax_number": fake.numerify("############"),
            "registration_number": fake.numerify("############"),
            "capital": fake.random_int(min=1000000, max=100000000),
            "employee_count": fake.random_int(min=1, max=1000),
            "is_active": True,
            "settings": {
                "fiscal_year_start": "04-01",
                "timezone": "Asia/Tokyo",
                "currency": "JPY"
            }
        }
    
    @classmethod
    def _get_update_attributes(cls) -> Dict[str, Any]:
        """Get default attributes for updating Organization instances."""
        return {
            "name": fake.company(),
            "description": fake.catch_phrase(),
            "phone": fake.phone_number(),
            "email": fake.company_email(),
            "website": fake.url(),
            "employee_count": fake.random_int(min=1, max=1000),
            "is_active": fake.boolean()
        }
    
    @classmethod
    def create_with_parent(cls, db_session: Session, parent_id: int, **kwargs: Any) -> Organization:
        """Create an organization with a parent organization."""
        kwargs['parent_id'] = parent_id
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_subsidiary_tree(cls, db_session: Session, depth: int = 2, children_per_level: int = 2) -> Dict[str, Any]:
        """Create a tree of organizations with subsidiaries."""
        # Create root organization
        root = cls.create(db_session, name="Root Organization")
        
        def create_children(parent: Organization, current_depth: int) -> list[Organization]:
            if current_depth >= depth:
                return []
            
            children = []
            for i in range(children_per_level):
                child = cls.create_with_parent(
                    db_session,
                    parent.id,
                    name=f"{parent.name} - Child {i+1}",
                    code=f"{parent.code}-C{i+1}"
                )
                children.append(child)
                
                # Recursively create grandchildren
                grandchildren = create_children(child, current_depth + 1)
                children.extend(grandchildren)
            
            return children
        
        all_organizations = [root]
        all_organizations.extend(create_children(root, 0))
        
        return {
            'root': root,
            'all': all_organizations,
            'tree_depth': depth,
            'children_per_level': children_per_level
        }
    
    @classmethod
    def create_inactive(cls, db_session: Session, **kwargs: Any) -> Organization:
        """Create an inactive organization."""
        kwargs['is_active'] = False
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_with_specific_industry(cls, db_session: Session, industry: str, **kwargs: Any) -> Organization:
        """Create an organization in a specific industry."""
        kwargs['industry'] = industry
        return cls.create(db_session, **kwargs)
    
    @classmethod
    def create_minimal(cls, db_session: Session, **kwargs: Any) -> Organization:
        """Create an organization with minimal required fields."""
        minimal_attrs = {
            "code": fake.unique.company_suffix(),
            "name": fake.company(),
            "is_active": True
        }
        minimal_attrs.update(kwargs)
        return cls.create(db_session, **minimal_attrs)