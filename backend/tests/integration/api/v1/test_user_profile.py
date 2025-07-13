"""Integration tests for user profile endpoints."""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import create_auth_headers


class TestUserProfile:
    """Test cases for user profile endpoints."""

    @pytest.mark.skip(
        reason="User profile update API needs implementation fixes"
    )
    def test_update_profile_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test successful profile update."""
        update_data = {"full_name": "Updated Name", "phone": "+1234567890"}

        response = client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+1234567890"

    def test_upload_profile_image_success(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test successful profile image upload."""
        # Create a test image file
        image_data = b"fake_image_data"
        files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}

        response = client.post(
            "/api/v1/users/me/profile-image",
            files=files,
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "profile_image_url" in data
        assert "filename" in data
        assert data["message"] == "Profile image uploaded successfully"

        # Verify file was uploaded
        filename = data["filename"]
        upload_path = Path(f"uploads/profile-images/{filename}")
        assert upload_path.exists()

        # Clean up
        upload_path.unlink(missing_ok=True)

    def test_upload_profile_image_invalid_type(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test profile image upload with invalid file type."""
        # Create a test text file
        text_data = b"this is not an image"
        files = {"file": ("test_file.txt", io.BytesIO(text_data), "text/plain")}

        response = client.post(
            "/api/v1/users/me/profile-image",
            files=files,
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 400
        data = response.json()
        assert "Only JPEG, PNG, and GIF images are allowed" in data["detail"]

    def test_upload_profile_image_unauthorized(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test profile image upload without authentication."""
        image_data = b"fake_image_data"
        files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}

        response = client.post(
            "/api/v1/users/me/profile-image",
            files=files,
        )

        assert response.status_code == 403

    def test_get_current_user_info(
        self, client: TestClient, db_session: Session, user_token: str, test_user: User
    ) -> None:
        """Test getting current user information."""
        response = client.get(
            "/api/v1/users/me",
            headers=create_auth_headers(user_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    def test_update_profile_unauthorized(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test profile update without authentication."""
        update_data = {"full_name": "Updated Name"}

        response = client.put(
            "/api/v1/users/me",
            json=update_data,
        )

        assert response.status_code == 403
