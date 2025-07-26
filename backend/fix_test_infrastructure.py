#!/usr/bin/env python3
"""Fix test infrastructure by simplifying conftest.py imports"""

import shutil
from pathlib import Path

def backup_and_fix_conftest():
    """Backup and fix the conftest.py file"""
    
    conftest_path = Path("tests/conftest.py")
    backup_path = Path("tests/conftest.py.backup")
    
    # Create backup
    if conftest_path.exists():
        shutil.copy2(conftest_path, backup_path)
        print(f"Backup created: {backup_path}")
    
    # Create simplified conftest.py
    simplified_conftest = '''"""
Test configuration and fixtures.
Simplified to avoid import conflicts.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import only essential models to avoid conflicts
from app.models.base import Base
from app.models.organization import Organization
from app.models.user import User
from app.models.role import Role
from app.models.department import Department

# Simple test database setup
TEST_DATABASE_URL = "sqlite:///test.db"

def pytest_configure(config):
    """Configure pytest settings"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine"""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def sample_organization(db_session):
    """Create a sample organization for testing"""
    org = Organization(
        code="TEST_ORG",
        name="Test Organization",
        email="test@example.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture
def sample_user(db_session, sample_organization):
    """Create a sample user for testing"""
    user = User(
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        organization_id=sample_organization.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_role(db_session, sample_organization):
    """Create a sample role for testing"""
    role = Role(
        code="TEST_ROLE",
        name="Test Role",
        organization_id=sample_organization.id
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role

@pytest.fixture
def sample_department(db_session, sample_organization):
    """Create a sample department for testing"""
    dept = Department(
        code="TEST_DEPT",
        name="Test Department",
        organization_id=sample_organization.id
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept

# Test data factories (simple versions)
class TestDataFactory:
    """Simple test data factory"""
    
    @staticmethod
    def create_organization(db_session, **kwargs):
        """Create test organization"""
        defaults = {
            "code": "ORG001",
            "name": "Test Organization",
            "email": "test@org.com"
        }
        defaults.update(kwargs)
        
        org = Organization(**defaults)
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        return org
    
    @staticmethod
    def create_user(db_session, organization_id=None, **kwargs):
        """Create test user"""
        defaults = {
            "username": "testuser",
            "email": "test@user.com",
            "full_name": "Test User"
        }
        if organization_id:
            defaults["organization_id"] = organization_id
        defaults.update(kwargs)
        
        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

@pytest.fixture
def test_factory():
    """Provide test data factory"""
    return TestDataFactory
'''
    
    # Write simplified conftest.py
    with open(conftest_path, 'w', encoding='utf-8') as f:
        f.write(simplified_conftest)
    
    print(f"Simplified conftest.py created: {conftest_path}")

def main():
    """Fix test infrastructure"""
    print("Fixing test infrastructure...")
    backup_and_fix_conftest()
    print("Test infrastructure fixes completed!")
    print("\nNext steps:")
    print("1. Run simple test: uv run pytest tests/unit/models/test_organization.py::TestOrganization::test_organization_creation -v")
    print("2. If successful, gradually add more model imports")
    print("3. Fix individual test files as needed")

if __name__ == "__main__":
    main()