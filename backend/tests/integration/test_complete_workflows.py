"""Integration tests for end-to-end workflows."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.base import BaseModel


class TestIntegration:
    """Integration tests for complete workflows."""

    def setup_method(self):
        """Setup test environment with test database."""
        # Create test database
        test_engine = create_engine("sqlite:///./test_integration.db")
        BaseModel.metadata.create_all(bind=test_engine)

        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def teardown_method(self):
        """Cleanup test environment."""
        # Clean up test database
        import os
        if os.path.exists("./test_integration.db"):
            os.remove("./test_integration.db")

    def test_user_registration_workflow(self):
        """Test complete user registration workflow."""
        # Step 1: Register new user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = self.client.post("/api/v1/users", json=user_data)
        assert response.status_code == 201

        created_user = response.json()
        assert created_user["username"] == user_data["username"]
        assert created_user["email"] == user_data["email"]

        # Step 2: Login with new user
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }

        login_response = self.client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200

        token_data = login_response.json()
        assert "access_token" in token_data

        # Step 3: Access protected endpoint
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = self.client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == 200

        profile_data = profile_response.json()
        assert profile_data["username"] == user_data["username"]

    def test_organization_management_workflow(self):
        """Test complete organization management workflow."""
        # This would test creating org, adding users, managing permissions, etc.
        pass

    def test_financial_workflow(self):
        """Test complete financial management workflow."""
        # This would test budget creation, expense tracking, report generation
        pass

    def test_audit_trail_workflow(self):
        """Test audit trail is properly maintained across operations."""
        # Test that all operations create proper audit logs
        pass
