"""Test fixtures for task management unit tests."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.organization import Organization, Project
from app.models.user import User
from app.models.role import Role
from tests.factories.organization import OrganizationFactory, ProjectFactory
from tests.factories.user import UserFactory
from tests.factories.role import RoleFactory


@pytest.fixture
def test_organization(db: Session) -> Organization:
    """Create test organization."""
    org = OrganizationFactory(
        code="TEST-ORG",
        name="Test Organization"
    )
    db.add(org)
    db.commit()
    return org


@pytest.fixture
def test_project(db: Session, test_organization: Organization) -> Project:
    """Create test project."""
    project = ProjectFactory(
        code="TEST-PROJ",
        name="Test Project",
        organization_id=test_organization.id
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def test_users(db: Session, test_organization: Organization) -> dict:
    """Create test users with different roles."""
    # Create roles
    project_manager_role = RoleFactory(
        code="PROJECT_MANAGER",
        name="Project Manager",
        permissions=["task.create", "task.update", "task.delete", "task.assign"]
    )
    developer_role = RoleFactory(
        code="DEVELOPER", 
        name="Developer",
        permissions=["task.view", "task.update"]
    )
    
    db.add_all([project_manager_role, developer_role])
    db.commit()
    
    # Create users
    manager = UserFactory(
        email="manager@example.com",
        full_name="Test Manager"
    )
    developer1 = UserFactory(
        email="dev1@example.com",
        full_name="Developer One"
    )
    developer2 = UserFactory(
        email="dev2@example.com",
        full_name="Developer Two"
    )
    
    db.add_all([manager, developer1, developer2])
    db.commit()
    
    # Assign roles
    from app.models.role import UserRole
    
    manager_role = UserRole(
        user_id=manager.id,
        role_id=project_manager_role.id,
        organization_id=test_organization.id,
        assigned_by=manager.id
    )
    dev1_role = UserRole(
        user_id=developer1.id,
        role_id=developer_role.id,
        organization_id=test_organization.id,
        assigned_by=manager.id
    )
    dev2_role = UserRole(
        user_id=developer2.id,
        role_id=developer_role.id,
        organization_id=test_organization.id,
        assigned_by=manager.id
    )
    
    db.add_all([manager_role, dev1_role, dev2_role])
    db.commit()
    
    return {
        "manager": manager,
        "developer1": developer1,
        "developer2": developer2
    }


@pytest.fixture
def test_data(db: Session) -> dict:
    """Create comprehensive test data."""
    # Test data for edge cases
    return {
        "max_title": "あ" * 200,  # Maximum length title
        "special_chars": "'; DROP TABLE tasks; --",  # SQL injection attempt
        "edge_dates": [
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),  # Year start
            datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),  # Year end
            datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)  # Leap year
        ]
    }