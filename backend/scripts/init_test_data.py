#!/usr/bin/env python3
"""
Test data initialization script for E2E testing.
Creates minimal required data for E2E tests to run successfully.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import get_async_session
from app.models.organization import Organization
from app.models.user import User


async def create_test_organization(session: AsyncSession) -> Organization:
    """Create a test organization."""
    # Check if test organization already exists
    stmt = select(Organization).where(Organization.name == "Test Organization")
    result = await session.execute(stmt)
    existing_org = result.scalar_one_or_none()

    if existing_org:
        print("Test organization already exists")
        return existing_org

    org = Organization(
        name="Test Organization",
        description="Organization for E2E testing",
        email="test@example.com",
        phone="+1-555-0123",
        address="123 Test Street, Test City, TC 12345",
        is_active=True,
    )

    session.add(org)
    await session.commit()
    await session.refresh(org)

    print(f"Created test organization: {org.name} (ID: {org.id})")
    return org


async def create_test_user(session: AsyncSession, org_id: int) -> User:
    """Create a test user."""
    # Check if test user already exists
    stmt = select(User).where(User.email == "test@example.com")
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print("Test user already exists")
        return existing_user

    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        organization_id=org_id,
        is_active=True,
        is_superuser=False,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    print(f"Created test user: {user.email} (ID: {user.id})")
    return user


async def init_test_data():
    """Initialize test data for E2E testing."""
    print("Initializing test data for E2E testing...")

    try:
        settings = Settings()
        print(f"Database URL: {settings.DATABASE_URL}")
        print(f"Environment: {settings.ENVIRONMENT}")

        # Get database session
        async for session in get_async_session():
            try:
                # Create test organization
                org = await create_test_organization(session)

                # Create test user
                user = await create_test_user(session, org.id)

                print("Test data initialization completed successfully!")
                print(f"- Organization: {org.name} (ID: {org.id})")
                print(f"- User: {user.email} (ID: {user.id})")

                break  # Exit the async generator loop

            except Exception as e:
                await session.rollback()
                raise e

    except Exception as e:
        print(f"Error initializing test data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_test_data())
