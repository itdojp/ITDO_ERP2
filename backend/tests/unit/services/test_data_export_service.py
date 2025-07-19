"""Tests for data export service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.export_job import ExportJob, ExportStatus
from app.schemas.data_export import ExportJobCreate
from app.services.data_export import DataExportService


class TestDataExportService:
    """Test cases for DataExportService."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> DataExportService:
        """Create DataExportService instance."""
        return DataExportService(mock_db)

    @pytest.fixture
    def sample_export_data(self) -> ExportJobCreate:
        """Create sample export job data."""
        return ExportJobCreate(
            entity_type="users",
            format="csv",
            filters={"is_active": True},
            columns=["id", "email", "first_name", "last_name"],
            organization_id=1,
        )

    @pytest.fixture
    def sample_data(self) -> list[dict]:
        """Create sample data for export."""
        return [
            {
                "id": 1,
                "email": "user1@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": 2,
                "email": "user2@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "created_at": "2024-01-02T00:00:00Z",
            },
        ]

    @pytest.mark.asyncio
    async def test_create_export_job_success(
        self,
        service: DataExportService,
        sample_export_data: ExportJobCreate,
        mock_db: MagicMock,
    ) -> None:
        """Test successful export job creation."""
        # Setup
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Mock the estimate method
        with patch.object(service, "_estimate_export_size", return_value=500):
            # Execute
            result = await service.create_export_job(
                export_data=sample_export_data,
                created_by=1,
            )

            # Verify
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            assert isinstance(result, type(service._job_to_response(MagicMock())))

    @pytest.mark.asyncio
    async def test_create_export_job_invalid_format(
        self,
        service: DataExportService,
        sample_export_data: ExportJobCreate,
        mock_db: MagicMock,
    ) -> None:
        """Test export job creation with invalid format."""
        # Setup invalid format
        sample_export_data.format = "invalid_format"

        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await service.create_export_job(
                export_data=sample_export_data,
                created_by=1,
            )

        assert "Unsupported format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_export_job_not_found(
        self, service: DataExportService, mock_db: MagicMock
    ) -> None:
        """Test getting export job that doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.get_export_job(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_export_job_success(
        self, service: DataExportService, mock_db: MagicMock
    ) -> None:
        """Test successful export job retrieval."""
        # Setup mock job
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.entity_type = "users"
        mock_job.format = "csv"
        mock_job.status = ExportStatus.COMPLETED
        mock_job.progress_percentage = 100
        mock_job.rows_processed = 100
        mock_job.total_rows = 100
        mock_job.file_path = "/path/to/export.csv"
        mock_job.error_message = None
        mock_job.created_at = "2024-01-01T00:00:00Z"
        mock_job.started_at = "2024-01-01T00:01:00Z"
        mock_job.completed_at = "2024-01-01T00:02:00Z"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_job

        result = await service.get_export_job(1)

        assert result is not None
        assert result.id == 1
        assert result.entity_type == "users"
        assert result.format == "csv"

    @pytest.mark.asyncio
    async def test_export_to_csv(
        self, service: DataExportService, sample_data: list[dict]
    ) -> None:
        """Test CSV export functionality."""
        result = await service.export_to_csv(
            entity_type="users",
            data=sample_data,
            columns=["id", "email", "first_name"],
        )

        assert isinstance(result, str)
        assert "id,email,first_name" in result
        assert "user1@example.com" in result
        assert "user2@example.com" in result
        # Should not include last_name since it's not in columns
        assert "Doe" not in result

    @pytest.mark.asyncio
    async def test_export_to_csv_empty_data(self, service: DataExportService) -> None:
        """Test CSV export with empty data."""
        result = await service.export_to_csv(
            entity_type="users",
            data=[],
            columns=["id", "email"],
        )

        assert result == ""

    @pytest.mark.asyncio
    async def test_export_to_excel(
        self, service: DataExportService, sample_data: list[dict]
    ) -> None:
        """Test Excel export functionality."""
        result = await service.export_to_excel(
            entity_type="users",
            data=sample_data,
            columns=["id", "email"],
        )

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_export_to_pdf(
        self, service: DataExportService, sample_data: list[dict]
    ) -> None:
        """Test PDF export functionality."""
        result = await service.export_to_pdf(
            entity_type="users",
            data=sample_data,
            columns=["id", "email"],
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF should start with PDF header
        assert result.startswith(b"%PDF")

    @pytest.mark.asyncio
    async def test_export_to_json(
        self, service: DataExportService, sample_data: list[dict]
    ) -> None:
        """Test JSON export functionality."""
        result = await service.export_to_json(
            entity_type="users",
            data=sample_data,
            columns=["id", "email"],
        )

        assert isinstance(result, str)
        
        # Parse and verify JSON structure
        parsed = json.loads(result)
        assert "metadata" in parsed
        assert "data" in parsed
        assert parsed["metadata"]["entity_type"] == "users"
        assert parsed["metadata"]["total_records"] == 2
        assert len(parsed["data"]) == 2
        
        # Check that only specified columns are included
        for item in parsed["data"]:
            assert "id" in item
            assert "email" in item
            assert "first_name" not in item  # Not in columns list

    @pytest.mark.asyncio
    async def test_validate_import_data_csv(self, service: DataExportService) -> None:
        """Test import data validation for CSV."""
        csv_content = b"id,name,email\n1,John,john@example.com\n2,Jane,jane@example.com"

        with patch.object(service, "_parse_csv_data") as mock_parse:
            mock_parse.return_value = [
                {"id": "1", "name": "John", "email": "john@example.com"},
                {"id": "2", "name": "Jane", "email": "jane@example.com"},
            ]
            
            with patch.object(service, "_validate_row", return_value=[]):
                result = await service.validate_import_data(
                    entity_type="users",
                    file_content=csv_content,
                    file_format="csv",
                )

                assert result.valid is True
                assert result.total_rows == 2
                assert result.valid_rows == 2
                assert len(result.errors) == 0
                mock_parse.assert_called_once_with(csv_content)

    @pytest.mark.asyncio
    async def test_validate_import_data_invalid_format(
        self, service: DataExportService
    ) -> None:
        """Test import data validation with invalid format."""
        result = await service.validate_import_data(
            entity_type="users",
            file_content=b"some content",
            file_format="invalid",
        )

        assert result.valid is False
        assert result.error == "Unsupported file format"
        assert result.total_rows == 0

    @pytest.mark.asyncio
    async def test_validate_import_data_with_errors(
        self, service: DataExportService
    ) -> None:
        """Test import data validation with validation errors."""
        csv_content = b"id,name,email\n1,John,invalid-email\n2,,jane@example.com"

        with patch.object(service, "_parse_csv_data") as mock_parse:
            mock_parse.return_value = [
                {"id": "1", "name": "John", "email": "invalid-email"},
                {"id": "2", "name": "", "email": "jane@example.com"},
            ]
            
            def mock_validate_row(entity_type, row, row_num):
                errors = []
                if row.get("email") == "invalid-email":
                    errors.append(f"Row {row_num}: Invalid email format")
                if not row.get("name"):
                    errors.append(f"Row {row_num}: Name is required")
                return errors
            
            with patch.object(service, "_validate_row", side_effect=mock_validate_row):
                result = await service.validate_import_data(
                    entity_type="users",
                    file_content=csv_content,
                    file_format="csv",
                )

                assert result.valid is False
                assert result.total_rows == 2
                assert result.valid_rows == 0
                assert len(result.errors) == 2
                assert "Invalid email format" in result.errors[0]
                assert "Name is required" in result.errors[1]

    def test_get_mime_type(self, service: DataExportService) -> None:
        """Test MIME type determination."""
        assert service._get_mime_type("csv") == "text/csv"
        assert service._get_mime_type("excel") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert service._get_mime_type("pdf") == "application/pdf"
        assert service._get_mime_type("json") == "application/json"
        assert service._get_mime_type("unknown") == "application/octet-stream"

    def test_parse_csv_data(self, service: DataExportService) -> None:
        """Test CSV data parsing."""
        csv_content = b"id,name,email\n1,John,john@example.com\n2,Jane,jane@example.com"
        
        result = service._parse_csv_data(csv_content)
        
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[0]["name"] == "John"
        assert result[1]["email"] == "jane@example.com"

    def test_parse_json_data_list(self, service: DataExportService) -> None:
        """Test JSON data parsing with list format."""
        json_content = b'[{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]'
        
        result = service._parse_json_data(json_content)
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["name"] == "Jane"

    def test_parse_json_data_dict_with_data_key(self, service: DataExportService) -> None:
        """Test JSON data parsing with data key structure."""
        json_content = b'{"data": [{"id": 1, "name": "John"}], "metadata": {}}'
        
        result = service._parse_json_data(json_content)
        
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_parse_json_data_single_object(self, service: DataExportService) -> None:
        """Test JSON data parsing with single object."""
        json_content = b'{"id": 1, "name": "John"}'
        
        result = service._parse_json_data(json_content)
        
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_validate_row_empty(self, service: DataExportService) -> None:
        """Test row validation with empty row."""
        errors = service._validate_row("users", {}, 1)
        
        assert len(errors) == 1
        assert "Empty row" in errors[0]

    def test_validate_row_valid(self, service: DataExportService) -> None:
        """Test row validation with valid row."""
        row = {"id": 1, "name": "John", "email": "john@example.com"}
        errors = service._validate_row("users", row, 1)
        
        assert len(errors) == 0