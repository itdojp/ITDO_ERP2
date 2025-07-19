"""Tests for file upload service."""

import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.models.file_metadata import FileMetadata
from app.services.file_upload import FileUploadService


class TestFileUploadService:
    """Test cases for FileUploadService."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> FileUploadService:
        """Create FileUploadService instance."""
        with patch.object(FileUploadService, "__init__", lambda x, db: setattr(x, "db", db)):
            service = FileUploadService(mock_db)
            service.upload_dir = Path(tempfile.gettempdir()) / "test_uploads"
            service.upload_dir.mkdir(exist_ok=True)
        return service

    @pytest.fixture
    def mock_upload_file(self) -> UploadFile:
        """Create mock upload file."""
        file_content = b"test file content"
        file = UploadFile(
            filename="test.txt",
            file=BytesIO(file_content),
            size=len(file_content),
            headers={"content-type": "text/plain"},
        )
        file.content_type = "text/plain"
        return file

    @pytest.mark.asyncio
    async def test_upload_file_success(
        self, service: FileUploadService, mock_upload_file: UploadFile, mock_db: MagicMock
    ) -> None:
        """Test successful file upload."""
        # Setup
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Mock file metadata instance
        mock_file_metadata = MagicMock()
        mock_file_metadata.id = 1
        mock_file_metadata.original_filename = "test.txt"
        mock_file_metadata.stored_filename = "uuid-filename.txt"
        mock_file_metadata.file_size = 17
        mock_file_metadata.mime_type = "text/plain"
        mock_file_metadata.file_hash = "test-hash"
        mock_file_metadata.category = "general"
        mock_file_metadata.created_at = "2024-01-01T00:00:00Z"

        # Configure db.refresh to set the mock metadata
        def mock_refresh(obj: FileMetadata) -> None:
            for attr in dir(mock_file_metadata):
                if not attr.startswith("_"):
                    setattr(obj, attr, getattr(mock_file_metadata, attr))

        mock_db.refresh.side_effect = mock_refresh

        # Execute
        result = await service.upload_file(
            file=mock_upload_file,
            uploaded_by=1,
            organization_id=1,
            category="document",
            description="Test file",
        )

        # Verify
        assert result.filename == "test.txt"
        assert result.category == "general"  # From mock
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_file_no_filename(self, service: FileUploadService) -> None:
        """Test file validation with no filename."""
        file = UploadFile(filename=None, file=BytesIO(b"content"))

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_file(file)

        assert exc_info.value.status_code == 400
        assert "Filename is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_file_too_large(self, service: FileUploadService) -> None:
        """Test file validation with oversized file."""
        large_size = max(service.MAX_FILE_SIZES.values()) + 1
        file = UploadFile(
            filename="large.txt",
            file=BytesIO(b"content"),
            size=large_size,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_file(file)

        assert exc_info.value.status_code == 413
        assert "File too large" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_file_invalid_mime_type(self, service: FileUploadService) -> None:
        """Test file validation with invalid MIME type."""
        file = UploadFile(
            filename="test.exe",
            file=BytesIO(b"content"),
            size=100,
        )
        file.content_type = "application/x-executable"

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_file(file)

        assert exc_info.value.status_code == 400
        assert "not allowed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_file_path_traversal(self, service: FileUploadService) -> None:
        """Test file validation prevents path traversal."""
        file = UploadFile(
            filename="../../../etc/passwd",
            file=BytesIO(b"content"),
            size=100,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service._validate_file(file)

        assert exc_info.value.status_code == 400
        assert "path traversal not allowed" in str(exc_info.value.detail)

    def test_determine_file_category(self, service: FileUploadService) -> None:
        """Test file category determination from MIME type."""
        assert service._determine_file_category("image/jpeg") == "image"
        assert service._determine_file_category("application/pdf") == "document"
        assert service._determine_file_category("application/zip") == "archive"
        assert service._determine_file_category("application/unknown") == "unknown"

    @pytest.mark.asyncio
    async def test_get_file_metadata_not_found(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test getting file metadata when file doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.get_file_metadata(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_file_metadata_success(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test successful file metadata retrieval."""
        # Setup mock file metadata
        mock_file = MagicMock()
        mock_file.id = 1
        mock_file.original_filename = "test.txt"
        mock_file.stored_filename = "uuid-test.txt"
        mock_file.file_size = 100
        mock_file.mime_type = "text/plain"
        mock_file.file_hash = "abcd1234"
        mock_file.category = "document"
        mock_file.description = "Test file"
        mock_file.uploaded_by = 1
        mock_file.organization_id = 1
        mock_file.metadata = {}
        mock_file.created_at = "2024-01-01T00:00:00Z"
        mock_file.updated_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_file

        result = await service.get_file_metadata(1)

        assert result is not None
        assert result.id == 1
        assert result.original_filename == "test.txt"
        assert result.download_url == "/api/v1/files/1/download"

    @pytest.mark.asyncio
    async def test_delete_file_not_found(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test deleting file that doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_file(999, 1)

        assert exc_info.value.status_code == 404
        assert "File not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_file_success(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test successful file deletion."""
        # Setup mock file metadata
        mock_file = MagicMock()
        mock_file.id = 1
        mock_file.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_file
        mock_db.commit = MagicMock()

        result = await service.delete_file(1, 1)

        assert result.id == 1
        assert result.message == "File deleted successfully"
        assert mock_file.is_active is False
        assert mock_file.deleted_by == 1
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_files_with_filters(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test listing files with filters."""
        # Setup mock files
        mock_files = [MagicMock(), MagicMock()]
        for i, mock_file in enumerate(mock_files):
            mock_file.id = i + 1
            mock_file.original_filename = f"test{i + 1}.txt"
            mock_file.stored_filename = f"uuid-test{i + 1}.txt"
            mock_file.file_size = 100
            mock_file.mime_type = "text/plain"
            mock_file.file_hash = f"hash{i + 1}"
            mock_file.category = "document"
            mock_file.description = f"Test file {i + 1}"
            mock_file.uploaded_by = 1
            mock_file.organization_id = 1
            mock_file.metadata = {}
            mock_file.created_at = "2024-01-01T00:00:00Z"
            mock_file.updated_at = None

        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_files

        result = await service.list_files(
            organization_id=1,
            category="document",
            uploaded_by=1,
            skip=0,
            limit=10,
        )

        assert len(result) == 2
        assert result[0].original_filename == "test1.txt"
        assert result[1].original_filename == "test2.txt"

    @pytest.mark.asyncio
    async def test_get_file_statistics(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test getting file statistics."""
        # Setup mock files
        mock_files = []
        for i in range(3):
            mock_file = MagicMock()
            mock_file.file_size = 100 * (i + 1)  # 100, 200, 300
            mock_file.category = "document" if i < 2 else "image"
            mock_files.append(mock_file)

        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_files

        result = await service.get_file_statistics(organization_id=1)

        assert result["total_files"] == 3
        assert result["total_size_bytes"] == 600  # 100 + 200 + 300
        assert result["total_size_mb"] == 0.57  # ~600/1024/1024 rounded
        assert result["category_breakdown"]["document"]["count"] == 2
        assert result["category_breakdown"]["image"]["count"] == 1
        assert result["average_file_size"] == 200  # 600 // 3

    @pytest.mark.asyncio
    async def test_validate_file_integrity_file_not_found(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test file integrity validation when file doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.validate_file_integrity(999)

        assert result["valid"] is False
        assert result["error"] == "File not found"

    @pytest.mark.asyncio
    async def test_validate_file_integrity_file_missing_on_disk(
        self, service: FileUploadService, mock_db: MagicMock
    ) -> None:
        """Test file integrity validation when file missing on disk."""
        mock_file = MagicMock()
        mock_file.file_path = "/nonexistent/path/file.txt"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_file

        result = await service.validate_file_integrity(1)

        assert result["valid"] is False
        assert "does not exist on disk" in result["error"]