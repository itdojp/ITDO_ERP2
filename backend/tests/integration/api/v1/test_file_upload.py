"""Integration tests for file upload API endpoints."""

import io

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import create_auth_headers


class TestFileUploadAPI:
    """Test cases for file upload API endpoints."""

    def create_test_image_file(self, filename: str = "test.jpg", content_type: str = "image/jpeg", size: int = 1024) -> tuple[str, io.BytesIO, str]:
        """Create a test image file for upload."""
        # Create fake JPEG content
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * (size - 16)
        file_obj = io.BytesIO(content)
        return filename, file_obj, content_type

    def test_upload_profile_image_success(
        self, client: TestClient, db_session: Session, admin_token: str
    ) -> None:
        """Test successful profile image upload."""
        filename, file_obj, content_type = self.create_test_image_file()

        response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename, file_obj, content_type)},
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "file_path" in data
        assert "filename" in data
        assert data["filename"].endswith(".jpg")

    def test_upload_profile_image_invalid_type(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test profile image upload with invalid file type."""
        # Create a PDF file
        content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj"
        file_obj = io.BytesIO(content)

        response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": ("test.pdf", file_obj, "application/pdf")},
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid file type" in data["detail"]

    def test_upload_profile_image_too_large(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test profile image upload with oversized file."""
        # Create a large file (6MB)
        filename, file_obj, content_type = self.create_test_image_file(
            size=6 * 1024 * 1024
        )

        response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename, file_obj, content_type)},
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 400
        data = response.json()
        assert "File size exceeds maximum" in data["detail"]

    def test_upload_profile_image_no_file(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test profile image upload without file."""
        response = client.post(
            "/api/v1/users/me/profile-image",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 422  # Validation error

    def test_upload_profile_image_unauthorized(self, client: TestClient) -> None:
        """Test profile image upload without authentication."""
        filename, file_obj, content_type = self.create_test_image_file()

        response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename, file_obj, content_type)},
        )

        assert response.status_code == 401

    def test_upload_profile_image_empty_file(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test profile image upload with empty file."""
        file_obj = io.BytesIO(b"")

        response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": ("empty.jpg", file_obj, "image/jpeg")},
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower()

    def test_get_uploaded_file(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test retrieving uploaded file."""
        # First upload a file
        filename, file_obj, content_type = self.create_test_image_file()

        upload_response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename, file_obj, content_type)},
            headers=create_auth_headers(admin_token),
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        uploaded_filename = upload_data["filename"]

        # Then retrieve the file
        response = client.get(f"/uploads/{uploaded_filename}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

    def test_get_nonexistent_file(self, client: TestClient) -> None:
        """Test retrieving non-existent file."""
        response = client.get("/uploads/nonexistent.jpg")

        assert response.status_code == 404

    def test_delete_profile_image(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test deleting profile image."""
        # First upload a file
        filename, file_obj, content_type = self.create_test_image_file()

        upload_response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename, file_obj, content_type)},
            headers=create_auth_headers(admin_token),
        )

        assert upload_response.status_code == 200

        # Then delete the profile image
        response = client.delete(
            "/api/v1/users/me/profile-image",
            headers=create_auth_headers(admin_token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_profile_image_unauthorized(self, client: TestClient) -> None:
        """Test deleting profile image without authentication."""
        response = client.delete("/api/v1/users/me/profile-image")

        assert response.status_code == 401

    def test_upload_multiple_formats(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test uploading different supported image formats."""
        formats = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.gif", "image/gif"),
            ("test.webp", "image/webp"),
        ]

        for filename, content_type in formats:
            _, file_obj, _ = self.create_test_image_file(filename, content_type)

            response = client.post(
                "/api/v1/users/me/profile-image",
                files={"file": (filename, file_obj, content_type)},
                headers=create_auth_headers(admin_token),
            )

            assert response.status_code == 200, f"Failed for {content_type}"
            data = response.json()
            assert data["success"] is True

    def test_concurrent_uploads(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test handling concurrent uploads."""
        import concurrent.futures

        def upload_file():
            filename, file_obj, content_type = self.create_test_image_file()
            return client.post(
                "/api/v1/users/me/profile-image",
                files={"file": (filename, file_obj, content_type)},
                headers=create_auth_headers(admin_token),
            )

        # Execute multiple uploads concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(upload_file) for _ in range(3)]
            responses = [future.result() for future in futures]

        # All uploads should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_upload_profile_image_replaces_existing(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test that uploading a new profile image replaces the existing one."""
        # Upload first image
        filename1, file_obj1, content_type = self.create_test_image_file("first.jpg")

        response1 = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename1, file_obj1, content_type)},
            headers=create_auth_headers(admin_token),
        )

        assert response1.status_code == 200
        first_filename = response1.json()["filename"]

        # Upload second image
        filename2, file_obj2, content_type = self.create_test_image_file("second.jpg")

        response2 = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename2, file_obj2, content_type)},
            headers=create_auth_headers(admin_token),
        )

        assert response2.status_code == 200
        second_filename = response2.json()["filename"]

        # Filenames should be different
        assert first_filename != second_filename

        # First file should no longer be accessible (optional test)
        # This depends on whether we implement cleanup of old files


class TestFileUploadSecurity:
    """Security tests for file upload functionality."""

    def test_upload_malicious_filename(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test upload with potentially malicious filename."""
        malicious_names = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "<script>alert('xss')</script>.jpg",
            "'; DROP TABLE users; --.jpg",
        ]

        for malicious_name in malicious_names:
            content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 1000
            file_obj = io.BytesIO(content)

            response = client.post(
                "/api/v1/users/me/profile-image",
                files={"file": (malicious_name, file_obj, "image/jpeg")},
                headers=create_auth_headers(admin_token),
            )

            # Should either succeed with sanitized filename or reject
            if response.status_code == 200:
                data = response.json()
                # Ensure filename is sanitized
                returned_filename = data["filename"]
                assert "../" not in returned_filename
                assert "..\\" not in returned_filename
                assert "<script>" not in returned_filename

    def test_upload_with_null_bytes(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Test upload with null bytes in filename."""
        filename = "test\x00.jpg"
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 1000
        file_obj = io.BytesIO(content)

        response = client.post(
            "/api/v1/users/me/profile-image",
            files={"file": (filename, file_obj, "image/jpeg")},
            headers=create_auth_headers(admin_token),
        )

        # Should handle null bytes safely
        if response.status_code == 200:
            data = response.json()
            assert "\x00" not in data["filename"]
