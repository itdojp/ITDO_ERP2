"""Test factories for creating test data."""

from datetime import date, datetime
from typing import Optional

from app.models.user import User
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role, UserRole
from app.models.project import Project
from app.models.task import Task


def create_test_user(
    email: str = "test@example.com",
    password: str = "testpass123",
    full_name: str = "Test User",
    is_active: bool = True,
    is_superuser: bool = False,
    **kwargs
) -> User:
    """Create a test user."""
    return User(
        email=email,
        hashed_password=password,  # In real tests, this should be hashed
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
        **kwargs
    )


def create_test_organization(
    code: str = "TEST_ORG",
    name: str = "Test Organization",
    is_active: bool = True,
    **kwargs
) -> Organization:
    """Create a test organization."""
    return Organization(
        code=code,
        name=name,
        is_active=is_active,
        **kwargs
    )


def create_test_department(
    code: str = "TEST_DEPT",
    name: str = "Test Department",
    organization_id: Optional[int] = None,
    is_active: bool = True,
    **kwargs
) -> Department:
    """Create a test department."""
    return Department(
        code=code,
        name=name,
        organization_id=organization_id,
        is_active=is_active,
        **kwargs
    )


def create_test_role(
    code: str = "TEST_ROLE",
    name: str = "Test Role",
    description: str = "Test role description",
    is_active: bool = True,
    **kwargs
) -> Role:
    """Create a test role."""
    return Role(
        code=code,
        name=name,
        description=description,
        is_active=is_active,
        **kwargs
    )


def create_test_user_role(
    user: User,
    role: Role,
    organization: Organization,
    department: Optional[Department] = None,
    assigned_by: Optional[int] = None,
    expires_at: Optional[datetime] = None,
    **kwargs
) -> UserRole:
    """Create a test user role assignment."""
    return UserRole(
        user_id=user.id,
        role_id=role.id,
        organization_id=organization.id,
        department_id=department.id if department else None,
        assigned_by=assigned_by,
        expires_at=expires_at,
        **kwargs
    )


def create_test_project(
    name: str = "Test Project",
    description: str = "Test project description",
    status: str = "planning",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    organization_id: Optional[int] = None,
    created_by: Optional[int] = None,
    **kwargs
) -> Project:
    """Create a test project."""
    if start_date is None:
        start_date = date(2025, 7, 1)
    
    return Project(
        name=name,
        description=description,
        status=status,
        start_date=start_date,
        end_date=end_date,
        organization_id=organization_id,
        created_by=created_by,
        **kwargs
    )


def create_test_task(
    title: str = "Test Task",
    description: str = "Test task description",
    status: str = "not_started",
    priority: str = "medium",
    project_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    estimated_start_date: Optional[date] = None,
    estimated_end_date: Optional[date] = None,
    created_by: Optional[int] = None,
    **kwargs
) -> Task:
    """Create a test task."""
    return Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        project_id=project_id,
        assigned_to=assigned_to,
        estimated_start_date=estimated_start_date,
        estimated_end_date=estimated_end_date,
        created_by=created_by,
        **kwargs
    )