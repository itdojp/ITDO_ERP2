"""Tests for file upload service."""

import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile

from app.services.file_upload import FileUploadService


class TestFileUploadService:
    """Test cases for FileUploadService."""

    @pytest.fixture
    def upload_service(self) -> FileUploadService:
        """Create file upload service instance."""
        return FileUploadService()

    @pytest.fixture
    def sample_image_file(self) -> AsyncGenerator[UploadFile, None]:
        """Create a sample image file for testing."""
        # Create a temporary file with image content
        with tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        ) as temp_file:
            # Write sample JPEG header to make it a valid image
            temp_file.write(b"\xff\xd8\xff\xe0\x00\x10JFIF")
            temp_file.write(b"\x00" * 1000)  # Add some content
            temp_file.flush()

            # Create UploadFile instance
            with open(temp_file.name, "rb") as f:
                upload_file = UploadFile(
                    filename="test_image.jpg",
                    file=f,
                    content_type="image/jpeg",
                    size=1024
                )
                yield upload_file

            # Cleanup
            os.unlink(temp_file.name)

    @pytest.fixture
    def large_file(self) -> AsyncGenerator[UploadFile, None]:
        """Create a large file for testing size limits."""
        with tempfile.NamedTemporaryFile(
            suffix=".jpg", delete=False
        ) as temp_file:
            # Write 6MB of data (exceeds 5MB limit)
            temp_file.write(b"\xff\xd8\xff\xe0\x00\x10JFIF")
            temp_file.write(b"\x00" * (6 * 1024 * 1024))
            temp_file.flush()

            with open(temp_file.name, "rb") as f:
                upload_file = UploadFile(
                    filename="large_image.jpg",
                    file=f,
                    content_type="image/jpeg",
                    size=6 * 1024 * 1024
                )
                yield upload_file

            os.unlink(temp_file.name)

    def test_validate_file_type_valid_image(self, upload_service: FileUploadService) -> None:
        """Test file type validation with valid image."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = "image/jpeg"
        upload_file.filename = "test.jpg"

        # Should not raise exception
        upload_service.validate_file_type(upload_file, ["image/jpeg", "image/png"])

    def test_validate_file_type_invalid_type(self, upload_service: FileUploadService) -> None:
        """Test file type validation with invalid type."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = "application/pdf"
        upload_file.filename = "test.pdf"

        with pytest.raises(ValueError, match="Invalid file type"):
            upload_service.validate_file_type(upload_file, ["image/jpeg", "image/png"])

    def test_validate_file_type_no_content_type(self, upload_service: FileUploadService) -> None:
        """Test file type validation when content type is None."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = None
        upload_file.filename = "test.jpg"

        with pytest.raises(ValueError, match="File content type not provided"):
            upload_service.validate_file_type(upload_file, ["image/jpeg"])

    def test_validate_file_size_valid(self, upload_service: FileUploadService) -> None:
        """Test file size validation with valid size."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.size = 1024  # 1KB

        # Should not raise exception
        upload_service.validate_file_size(upload_file, max_size_mb=5)

    def test_validate_file_size_too_large(self, upload_service: FileUploadService) -> None:
        """Test file size validation with oversized file."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.size = 10 * 1024 * 1024  # 10MB

        with pytest.raises(ValueError, match="File size exceeds maximum"):
            upload_service.validate_file_size(upload_file, max_size_mb=5)

    def test_validate_file_size_no_size(self, upload_service: FileUploadService) -> None:
        """Test file size validation when size is None."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.size = None

        with pytest.raises(ValueError, match="File size not provided"):
            upload_service.validate_file_size(upload_file, max_size_mb=5)

    def test_generate_unique_filename(self, upload_service: FileUploadService) -> None:
        """Test unique filename generation."""
        original_filename = "test_image.jpg"
        user_id = 123

        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "abcd1234"

            filename = upload_service.generate_unique_filename(original_filename, user_id)

            assert filename.startswith("123_abcd1234_")
            assert filename.endswith(".jpg")
            assert "test_image" in filename

    def test_generate_unique_filename_no_extension(self, upload_service: FileUploadService) -> None:
        """Test unique filename generation without extension."""
        original_filename = "test_file"
        user_id = 456

        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "efgh5678"

            filename = upload_service.generate_unique_filename(original_filename, user_id)

            assert filename == "456_efgh5678_test_file"

    @pytest.mark.asyncio
    async def test_save_file_success(self, upload_service: FileUploadService) -> None:
        """Test successful file saving."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "test.jpg"

        # Create async mock for read()
        async def mock_read():
            return b"fake image data"
        upload_file.read = mock_read

        with patch('aiofiles.open') as mock_open:
            # Create async mock for file write
            async def mock_write(data):
                pass

            mock_file = MagicMock()
            mock_file.write = mock_write
            mock_open.return_value.__aenter__.return_value = mock_file

            with patch.object(upload_service, 'ensure_upload_directory') as mock_ensure_dir:
                file_path = await upload_service.save_file(upload_file, "saved_file.jpg")

                mock_ensure_dir.assert_called_once()
                mock_open.assert_called_once()

                assert isinstance(file_path, Path)
                assert file_path.name == "saved_file.jpg"

    def test_ensure_upload_directory(self, upload_service: FileUploadService) -> None:
        """Test upload directory creation."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('pathlib.Path.exists', return_value=False):
                upload_service.ensure_upload_directory()
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_ensure_upload_directory_exists(self, upload_service: FileUploadService) -> None:
        """Test upload directory when it already exists."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('pathlib.Path.exists', return_value=True):
                upload_service.ensure_upload_directory()
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @pytest.mark.asyncio
    async def test_upload_profile_image_success(self, upload_service: FileUploadService) -> None:
        """Test successful profile image upload."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "profile.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.size = 1024
        user_id = 123

        with patch.object(upload_service, 'validate_file_type') as mock_validate_type:
            with patch.object(upload_service, 'validate_file_size') as mock_validate_size:
                with patch.object(upload_service, 'generate_unique_filename', return_value="unique_profile.jpg") as mock_filename:
                    with patch.object(upload_service, 'save_file', return_value=Path("/uploads/unique_profile.jpg")) as mock_save:

                        result = await upload_service.upload_profile_image(upload_file, user_id)

                        mock_validate_type.assert_called_once_with(
                            upload_file, ["image/jpeg", "image/png", "image/gif", "image/webp"]
                        )
                        mock_validate_size.assert_called_once_with(upload_file, 5)
                        mock_filename.assert_called_once_with("profile.jpg", user_id)
                        mock_save.assert_called_once_with(upload_file, "unique_profile.jpg")

                        assert result["success"] is True
                        assert result["file_path"] == "/uploads/unique_profile.jpg"
                        assert result["filename"] == "unique_profile.jpg"

    @pytest.mark.asyncio
    async def test_upload_profile_image_validation_error(self, upload_service: FileUploadService) -> None:
        """Test profile image upload with validation error."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "profile.pdf"
        upload_file.content_type = "application/pdf"
        user_id = 123

        with patch.object(upload_service, 'validate_file_type', side_effect=ValueError("Invalid file type")):

            result = await upload_service.upload_profile_image(upload_file, user_id)

            assert result["success"] is False
            assert "Invalid file type" in result["error"]

    def test_delete_file_success(self, upload_service: FileUploadService) -> None:
        """Test successful file deletion."""
        file_path = "/uploads/test_file.jpg"

        with patch('pathlib.Path.exists', return_value=True) as mock_exists:
            with patch('pathlib.Path.unlink') as mock_unlink:

                result = upload_service.delete_file(file_path)

                mock_exists.assert_called_once()
                mock_unlink.assert_called_once()
                assert result is True

    def test_delete_file_not_exists(self, upload_service: FileUploadService) -> None:
        """Test file deletion when file doesn't exist."""
        file_path = "/uploads/nonexistent.jpg"

        with patch('pathlib.Path.exists', return_value=False):

            result = upload_service.delete_file(file_path)

            assert result is False

    def test_delete_file_permission_error(self, upload_service: FileUploadService) -> None:
        """Test file deletion with permission error."""
        file_path = "/uploads/protected.jpg"

        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.unlink', side_effect=PermissionError("Permission denied")):

                result = upload_service.delete_file(file_path)

                assert result is False

    def test_get_file_url(self, upload_service: FileUploadService) -> None:
        """Test file URL generation."""
        filename = "test_image.jpg"

        # Mock the settings directly on the service instance
        upload_service.settings.BASE_URL = "https://api.example.com"
        url = upload_service.get_file_url(filename)

        assert url == "https://api.example.com/uploads/test_image.jpg"

    def test_allowed_image_types(self, upload_service: FileUploadService) -> None:
        """Test allowed image types constant."""
        expected_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        assert upload_service.ALLOWED_IMAGE_TYPES == expected_types

    def test_max_file_size_mb(self, upload_service: FileUploadService) -> None:
        """Test maximum file size constant."""
        assert upload_service.MAX_FILE_SIZE_MB == 5
