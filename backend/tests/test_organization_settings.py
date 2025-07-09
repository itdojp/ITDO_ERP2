"""Test OrganizationResponse settings field validation."""

import json
import pytest
from pydantic import ValidationError

from app.schemas.organization import OrganizationResponse


class TestOrganizationResponseSettings:
    """Test settings field validation in OrganizationResponse."""

    def test_settings_dict_input(self):
        """Test settings field with dict input."""
        # Arrange
        data = {
            "id": 1,
            "code": "TEST-ORG",
            "name": "Test Organization",
            "is_active": True,
            "settings": {"fiscal_year_start": "01-04", "currency": "JPY"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Act
        response = OrganizationResponse(**data)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings["fiscal_year_start"] == "01-04"
        assert response.settings["currency"] == "JPY"

    def test_settings_json_string_input(self):
        """Test settings field with JSON string input."""
        # Arrange
        data = {
            "id": 1,
            "code": "TEST-ORG",
            "name": "Test Organization",
            "is_active": True,
            "settings": '{"fiscal_year_start": "01-04", "currency": "JPY"}',
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Act
        response = OrganizationResponse(**data)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings["fiscal_year_start"] == "01-04"
        assert response.settings["currency"] == "JPY"

    def test_settings_empty_string_input(self):
        """Test settings field with empty string input."""
        # Arrange
        data = {
            "id": 1,
            "code": "TEST-ORG",
            "name": "Test Organization",
            "is_active": True,
            "settings": "",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Act
        response = OrganizationResponse(**data)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings == {}

    def test_settings_none_input(self):
        """Test settings field with None input."""
        # Arrange
        data = {
            "id": 1,
            "code": "TEST-ORG",
            "name": "Test Organization",
            "is_active": True,
            "settings": None,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Act
        response = OrganizationResponse(**data)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings == {}

    def test_settings_invalid_json_string(self):
        """Test settings field with invalid JSON string."""
        # Arrange
        data = {
            "id": 1,
            "code": "TEST-ORG",
            "name": "Test Organization",
            "is_active": True,
            "settings": '{"invalid": json}',  # Invalid JSON
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Act
        response = OrganizationResponse(**data)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings == {}  # Should default to empty dict

    def test_settings_missing_field(self):
        """Test settings field when not provided."""
        # Arrange
        data = {
            "id": 1,
            "code": "TEST-ORG",
            "name": "Test Organization",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Act
        response = OrganizationResponse(**data)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings == {}

    def test_from_attributes_with_organization_model(self):
        """Test creating OrganizationResponse from Organization model attributes."""
        # Arrange - Mock organization model
        class MockOrganization:
            id = 1
            code = "TEST-ORG"
            name = "Test Organization"
            name_kana = None
            name_en = None
            is_active = True
            phone = None
            fax = None
            email = None
            website = None
            postal_code = None
            prefecture = None
            city = None
            address_line1 = None
            address_line2 = None
            business_type = None
            industry = None
            capital = None
            employee_count = None
            fiscal_year_end = None
            parent_id = None
            parent = None
            description = None
            logo_url = None
            settings = '{"fiscal_year_start": "01-04", "currency": "JPY"}'  # JSON string
            full_address = None
            is_subsidiary = False
            is_parent = False
            subsidiary_count = 0
            created_at = "2024-01-01T00:00:00"
            updated_at = "2024-01-01T00:00:00"
            created_by = None
            updated_by = None
            deleted_at = None
            deleted_by = None
            is_deleted = False
        
        mock_org = MockOrganization()
        
        # Act
        response = OrganizationResponse.model_validate(mock_org, from_attributes=True)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings["fiscal_year_start"] == "01-04"
        assert response.settings["currency"] == "JPY"

    def test_complex_settings_parsing(self):
        """Test complex settings object parsing."""
        # Arrange
        complex_settings = {
            "fiscal_year_start": "04-01",
            "currency": "JPY",
            "working_hours": {
                "start": "09:00",
                "end": "17:00",
                "break_start": "12:00",
                "break_end": "13:00"
            },
            "departments": ["IT", "HR", "Finance"],
            "max_employees": 1000,
            "multi_tenant": True
        }
        
        data = {
            "id": 1,
            "code": "TEST-ORG",
            "name": "Test Organization",
            "is_active": True,
            "settings": json.dumps(complex_settings),
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        
        # Act
        response = OrganizationResponse(**data)
        
        # Assert
        assert isinstance(response.settings, dict)
        assert response.settings["fiscal_year_start"] == "04-01"
        assert response.settings["currency"] == "JPY"
        assert response.settings["working_hours"]["start"] == "09:00"
        assert response.settings["departments"] == ["IT", "HR", "Finance"]
        assert response.settings["max_employees"] == 1000
        assert response.settings["multi_tenant"] is True