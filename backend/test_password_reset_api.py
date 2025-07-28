#!/usr/bin/env python
"""Test password reset API endpoints."""

import os

os.environ["DATABASE_URL"] = "sqlite:///test_password_reset_api.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.deps import get_db

# Import the app components
from app.models.base import Base

# Create test app
app = FastAPI()

# Database setup
engine = create_engine("sqlite:///test_password_reset_api.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)


# Override the dependency
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Add routers
from app.api.v1 import auth, password_reset, users

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    password_reset.router, prefix="/api/v1/password-reset", tags=["password-reset"]
)
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

client = TestClient(app)


def test_password_reset_api():
    """Test password reset API endpoints."""
    print("Testing Password Reset API...\n")

    # Create a user first
    print("1. Creating test user...")
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "test@example.com",
            "password": "OldPassword123!",
            "full_name": "Test User",
        },
    )
    if response.status_code != 200:
        print(f"Registration response: {response.status_code} - {response.text}")
    assert response.status_code == 200
    user_data = response.json()
    print(f"✓ User created: {user_data['email']}")

    # Test 1: Request password reset
    print("\n2. Testing password reset request...")
    response = client.post(
        "/api/v1/password-reset/request", json={"email": "test@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "送信しました" in data["message"]
    print("✓ Password reset requested")

    # Test 2: Request for non-existent user
    print("\n3. Testing reset for non-existent user...")
    response = client.post(
        "/api/v1/password-reset/request", json={"email": "nonexistent@example.com"}
    )
    assert response.status_code == 200  # Should still return 200
    data = response.json()
    assert data["success"] is True  # To prevent user enumeration
    print("✓ Non-existent user handled correctly")

    # Test 3: Rate limiting
    print("\n4. Testing rate limiting...")
    response = client.post(
        "/api/v1/password-reset/request", json={"email": "test@example.com"}
    )
    assert response.status_code == 200
    # Even if rate limited, returns success to prevent enumeration
    print("✓ Rate limiting response correct")

    # For actual testing, we need to get the token from the database
    # In production, this would be sent via email
    from app.models.password_reset import PasswordResetToken
    from app.models.user import User

    db = SessionLocal()
    user = db.query(User).filter(User.email == "test@example.com").first()
    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == user.id)
        .first()
    )

    token = reset_token.token
    code = reset_token.verification_code
    print(f"\n[Debug] Token: {token[:20]}...")
    print(f"[Debug] Code: {code}")

    # Test 4: Verify token
    print("\n5. Testing token verification...")
    response = client.post(
        "/api/v1/password-reset/verify",
        json={
            "token": token,
            "verification_code": code,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_email"] == "test@example.com"
    print("✓ Token verified successfully")

    # Test 5: Verify with wrong code
    print("\n6. Testing wrong verification code...")
    response = client.post(
        "/api/v1/password-reset/verify",
        json={
            "token": token,
            "verification_code": "000000",
        },
    )
    assert response.status_code == 400
    print("✓ Wrong code rejected")

    # Test 6: Reset with weak password
    print("\n7. Testing weak password rejection...")
    response = client.post(
        "/api/v1/password-reset/reset",
        json={
            "token": token,
            "new_password": "weak",
            "verification_code": code,
        },
    )
    assert response.status_code == 400
    print("✓ Weak password rejected")

    # Test 7: Reset with valid password
    print("\n8. Testing successful password reset...")
    response = client.post(
        "/api/v1/password-reset/reset",
        json={
            "token": token,
            "new_password": "NewPassword456!",
            "verification_code": code,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "リセットされました" in data["message"]
    print("✓ Password reset successful")

    # Test 8: Login with new password
    print("\n9. Testing login with new password...")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "NewPassword456!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    print("✓ Login with new password successful")

    # Test 9: Login with old password should fail
    print("\n10. Testing old password rejection...")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "OldPassword123!",
        },
    )
    assert response.status_code == 400
    print("✓ Old password correctly rejected")

    print("\n✅ All password reset API tests passed!")
    print("\nAPI features tested:")
    print("  - Password reset request endpoint")
    print("  - User enumeration prevention")
    print("  - Token verification endpoint")
    print("  - Password reset endpoint")
    print("  - Integration with auth system")
    print("  - Proper error handling")

    # Cleanup
    db.close()
    os.remove("test_password_reset_api.db")


if __name__ == "__main__":
    test_password_reset_api()
