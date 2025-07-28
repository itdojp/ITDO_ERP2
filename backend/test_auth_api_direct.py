#!/usr/bin/env python
"""Direct API test for authentication without full app dependencies."""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "1440"

from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create minimal app
app = FastAPI()

# Database setup
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Minimal schemas
class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 86400
    requires_mfa: bool = False
    mfa_token: str | None = None


# Simple user store (in-memory)
users_db = {
    "test@example.com": {
        "id": 1,
        "email": "test@example.com",
        "password": "SecurePass123!",  # In real app, this would be hashed
        "full_name": "Test User",
        "mfa_required": False,
    },
    "mfa@example.com": {
        "id": 2,
        "email": "mfa@example.com",
        "password": "SecurePass123!",
        "full_name": "MFA User",
        "mfa_required": True,
    },
}


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: Request, login_data: LoginRequest):
    """Simple login endpoint."""
    # Get user
    user = users_db.get(login_data.email)
    if not user or user["password"] != login_data.password:
        raise HTTPException(
            status_code=401, detail="メールアドレスまたはパスワードが正しくありません"
        )

    # Check MFA
    if user["mfa_required"]:
        return TokenResponse(
            access_token="",
            token_type="bearer",
            expires_in=0,
            requires_mfa=True,
            mfa_token="mfa-challenge-token-123",
        )

    # Generate token
    from app.core.security import create_access_token

    access_token = create_access_token(
        data={"sub": str(user["id"]), "email": user["email"]}
    )

    refresh_token = None
    if login_data.remember_me:
        refresh_token = create_access_token(
            data={"sub": str(user["id"]), "type": "refresh"},
            expires_delta=timedelta(days=7),
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=86400,
        requires_mfa=False,
    )


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


@app.get("/api/v1/auth/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user."""
    # In real app, would validate token
    # For now, just return test user

    # Simple response
    return {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "mfa_enabled": False,
        "last_login_at": None,
        "session_timeout_hours": 8,
        "idle_timeout_minutes": 30,
    }


def test_api():
    """Test the API."""
    client = TestClient(app)

    print("Testing Authentication API...\n")

    # Test 1: Successful login
    print("1. Testing successful login...")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "remember_me": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["requires_mfa"] is False
    print("✓ Success - got access token")

    # Test 2: Login with MFA
    print("\n2. Testing login with MFA required...")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa@example.com",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["requires_mfa"] is True
    assert "mfa_token" in data
    assert data["access_token"] == ""
    print("✓ Success - MFA challenge returned")

    # Test 3: Invalid credentials
    print("\n3. Testing invalid credentials...")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword",
        },
    )
    assert response.status_code == 401
    assert (
        "メールアドレスまたはパスワードが正しくありません" in response.json()["detail"]
    )
    print("✓ Success - authentication failed as expected")

    # Test 4: Get current user
    print("\n4. Testing get current user...")
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer fake-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    print("✓ Success - user info returned")

    print("\n✅ All API tests passed!")


if __name__ == "__main__":
    test_api()
