#!/usr/bin/env python
"""Test user management API."""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"

from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.users_auth import router as users_router
from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.models.base import Base
from app.models.user import User

# Create test app
app = FastAPI()
app.include_router(users_router, prefix="/api/v1")

# Database setup
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


# Override dependencies
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Create test data
def setup_test_data():
    """Create test users."""
    db = SessionLocal()

    # Admin user
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
        password_changed_at=datetime.now(),
    )
    db.add(admin)

    # Regular user
    user = User(
        email="user@example.com",
        hashed_password=hash_password("UserPass123!"),
        full_name="Regular User",
        is_active=True,
        is_superuser=False,
        mfa_required=False,
        password_changed_at=datetime.now(),
    )
    db.add(user)

    db.commit()
    db.close()

    return admin, user


def get_auth_headers(user_id: int, email: str, is_superuser: bool = False):
    """Create auth headers for testing."""
    token = create_access_token(
        data={
            "sub": str(user_id),
            "email": email,
            "is_superuser": is_superuser,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_user_api():
    """Test user management endpoints."""
    client = TestClient(app)

    # Setup test data
    admin, user = setup_test_data()
    admin_headers = get_auth_headers(admin.id, admin.email, True)
    user_headers = get_auth_headers(user.id, user.email, False)

    print("Testing User Management API...\n")

    # Test 1: List users (admin)
    print("1. Testing list users (admin)...")
    response = client.get("/api/v1/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["users"]) == 2
    print("✓ Success")

    # Test 2: List users (non-admin) - should fail
    print("\n2. Testing list users (non-admin)...")
    response = client.get("/api/v1/users", headers=user_headers)
    assert response.status_code == 403
    print("✓ Correctly denied")

    # Test 3: Get current user profile
    print("\n3. Testing get current user profile...")
    response = client.get("/api/v1/users/me", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Regular User"
    assert data["mfa_enabled"] is False
    print("✓ Success")

    # Test 4: Update profile
    print("\n4. Testing update profile...")
    response = client.put(
        "/api/v1/users/me/profile",
        headers=user_headers,
        json={
            "full_name": "Updated User",
            "phone": "090-1234-5678",
            "bio": "Test bio",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated User"
    print("✓ Success")

    # Test 5: Change password
    print("\n5. Testing change password...")
    response = client.post(
        "/api/v1/users/me/password",
        headers=user_headers,
        json={
            "current_password": "UserPass123!",
            "new_password": "NewPass123!",
        },
    )
    assert response.status_code == 204
    print("✓ Success")

    # Test 6: Get MFA status
    print("\n6. Testing get MFA status...")
    response = client.get("/api/v1/users/me/mfa", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["mfa_enabled"] is False
    assert data["mfa_devices_count"] == 0
    print("✓ Success")

    # Test 7: Create user (admin)
    print("\n7. Testing create user (admin)...")
    response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "newuser@example.com",
            "password": "NewUserPass123!",
            "full_name": "New User",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    new_user_id = data["id"]
    print("✓ Success")

    # Test 8: Get specific user (admin)
    print("\n8. Testing get specific user (admin)...")
    response = client.get(f"/api/v1/users/{new_user_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    print("✓ Success")

    # Test 9: Update user (admin)
    print("\n9. Testing update user (admin)...")
    response = client.put(
        f"/api/v1/users/{new_user_id}", headers=admin_headers, json={"is_active": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    print("✓ Success")

    # Test 10: Delete user (admin)
    print("\n10. Testing delete user (admin)...")
    response = client.delete(f"/api/v1/users/{new_user_id}", headers=admin_headers)
    assert response.status_code == 204
    print("✓ Success")

    print("\n✅ All user API tests passed!")


if __name__ == "__main__":
    test_user_api()
