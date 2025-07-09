#!/usr/bin/env python3
"""Setup test data for E2E tests."""

import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.base import Base
from app.models.user import User, PasswordHistory
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role, UserRole
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.core.security import hash_password
from datetime import datetime, timezone


def setup_test_data():
    """Create test data for E2E tests."""
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test organization
        org = Organization(
            name="Test Organization",
            code="TEST_ORG",
            description="Test organization for E2E tests"
        )
        session.add(org)
        session.flush()
        
        # Create test department
        dept = Department(
            name="Test Department",
            code="TEST_DEPT",
            organization_id=org.id,
            description="Test department for E2E tests"
        )
        session.add(dept)
        session.flush()
        
        # Create test roles
        admin_role = Role(
            name="Administrator",
            code="admin",
            description="Administrator role",
            permissions=["user:read", "user:write", "user:delete", "org:read", "org:write"]
        )
        user_role = Role(
            name="User",
            code="user", 
            description="Standard user role",
            permissions=["user:read"]
        )
        session.add_all([admin_role, user_role])
        session.flush()
        
        # Create test users
        test_user = User(
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
            department_id=dept.id,
            password_changed_at=datetime.now(timezone.utc)
        )
        
        admin_user = User(
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
            department_id=dept.id,
            password_changed_at=datetime.now(timezone.utc)
        )
        
        session.add_all([test_user, admin_user])
        session.flush()
        
        # Assign roles
        test_user_role = UserRole(
            user_id=test_user.id,
            role_id=user_role.id,
            organization_id=org.id,
            department_id=dept.id,
            assigned_by=admin_user.id
        )
        
        admin_user_role = UserRole(
            user_id=admin_user.id,
            role_id=admin_role.id,
            organization_id=org.id,
            assigned_by=admin_user.id
        )
        
        session.add_all([test_user_role, admin_user_role])
        session.flush()
        
        # Create test project
        project = Project(
            code="TEST_PROJ",
            name="Test Project",
            description="Test project for E2E tests",
            organization_id=org.id,
            department_id=dept.id,
            owner_id=admin_user.id,
            status="planning",
            priority="medium"
        )
        session.add(project)
        session.flush()
        
        # Create test tasks
        tasks = [
            Task(
                title="Test Task 1",
                description="First test task",
                project_id=project.id,
                created_by=admin_user.id,
                assigned_to=test_user.id,
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM
            ),
            Task(
                title="Test Task 2", 
                description="Second test task",
                project_id=project.id,
                created_by=admin_user.id,
                assigned_to=test_user.id,
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH
            ),
            Task(
                title="Test Task 3",
                description="Third test task",
                project_id=project.id,
                created_by=admin_user.id,
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.LOW
            )
        ]
        session.add_all(tasks)
        
        session.commit()
        print("✅ Test data created successfully!")
        print(f"Organization: {org.name} (ID: {org.id})")
        print(f"Department: {dept.name} (ID: {dept.id})")
        print(f"Test User: {test_user.email}")
        print(f"Admin User: {admin_user.email}")
        print(f"Project: {project.name} (ID: {project.id})")
        print(f"Tasks created: {len(tasks)}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating test data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    setup_test_data()