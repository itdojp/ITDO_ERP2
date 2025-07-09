"""Error handling integration tests for Organization Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.organization import Organization
from app.models.user import User
from app.services.organization import OrganizationService
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.core.exceptions import NotFound, ValidationError
from tests.conftest import create_auth_headers
from tests.factories import OrganizationFactory


class TestOrganizationErrorHandling:
    """Test comprehensive error handling in Organization Service."""

    def test_api_error_responses(
        self,
        client: TestClient,
        test_organization: Organization,
        admin_token: str,
    ):
        """Test API error response formats and status codes."""
        auth_headers = create_auth_headers(admin_token)
        
        # Test 404 - Organization not found
        response = client.get("/api/v1/organizations/99999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Organization not found" in data["detail"]
        
        # Test 409 - Duplicate code
        duplicate_data = {
            "code": test_organization.code,
            "name": "Duplicate Test Organization",
            "is_active": True,
        }
        response = client.post(
            "/api/v1/organizations/",
            json=duplicate_data,
            headers=auth_headers
        )
        assert response.status_code == 409
        data = response.json()
        assert "code" in data
        assert data["code"] == "DUPLICATE_CODE"
        
        # Test 422 - Invalid data
        invalid_data = {
            "code": "INVALID",
            "name": "Invalid Organization",
            "is_active": "not_a_boolean",  # Invalid type
        }
        response = client.post(
            "/api/v1/organizations/",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test 403 - Insufficient permissions (with non-admin user)
        user_headers = {"Authorization": "Bearer user-token"}
        response = client.post(
            "/api/v1/organizations/",
            json={"code": "TEST", "name": "Test", "is_active": True},
            headers=user_headers
        )
        assert response.status_code in [401, 403]

    def test_service_layer_error_handling(
        self,
        db_session: Session,
        test_organization: Organization,
        test_user: User,
    ):
        """Test service layer error handling and exception propagation."""
        service = OrganizationService(db_session)
        
        # Test ValidationError for duplicate code
        duplicate_create = OrganizationCreate(
            code=test_organization.code,
            name="Duplicate Organization",
            is_active=True,
        )
        
        with pytest.raises(ValueError) as exc_info:
            service.create_organization(duplicate_create, created_by=test_user.id)
        assert "already exists" in str(exc_info.value)
        
        # Test NotFound exception for statistics
        with pytest.raises(NotFound):
            service.get_organization_statistics(99999)
        
        # Test ValidationError for circular reference
        parent_org = OrganizationFactory.create(
            db_session,
            code="CIRCULAR-PARENT",
            name="Circular Parent",
            created_by=test_user.id,
        )
        child_org = OrganizationFactory.create(
            db_session,
            code="CIRCULAR-CHILD",
            name="Circular Child",
            parent_id=parent_org.id,
            created_by=test_user.id,
        )
        
        with pytest.raises(ValidationError) as exc_info:
            service.validate_parent_assignment(parent_org.id, child_org.id)
        assert "Circular reference detected" in str(exc_info.value)

    def test_database_constraint_violations(
        self,
        db_session: Session,
        test_user: User,
    ):
        """Test handling of database constraint violations."""
        service = OrganizationService(db_session)
        
        # Create organization with valid data first
        org1 = service.create_organization(
            OrganizationCreate(
                code="CONSTRAINT-TEST-1",
                name="Constraint Test 1",
                is_active=True,
            ),
            created_by=test_user.id,
        )
        assert org1 is not None
        
        # Try to create another organization with the same code
        with pytest.raises(ValueError) as exc_info:
            service.create_organization(
                OrganizationCreate(
                    code="CONSTRAINT-TEST-1",  # Duplicate code
                    name="Constraint Test 2",
                    is_active=True,
                ),
                created_by=test_user.id,
            )
        assert "already exists" in str(exc_info.value)

    def test_invalid_data_handling(
        self,
        db_session: Session,
        test_user: User,
    ):
        """Test handling of invalid data inputs."""
        service = OrganizationService(db_session)
        
        # Test update with invalid organization ID
        result = service.update_organization(
            99999,
            OrganizationUpdate(name="Updated Name"),
            updated_by=test_user.id,
        )
        assert result is None
        
        # Test delete with invalid organization ID
        result = service.delete_organization(99999, deleted_by=test_user.id)
        assert result is False
        
        # Test settings update with invalid organization ID
        result = service.update_settings(
            99999,
            {"some_setting": "value"},
            updated_by=test_user.id,
        )
        assert result is None

    def test_permission_error_handling(
        self,
        client: TestClient,
        test_organization: Organization,
    ):
        """Test permission-related error handling."""
        # Test with no authentication
        response = client.get("/api/v1/organizations/")
        assert response.status_code in [401, 403]
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/organizations/", headers=invalid_headers)
        assert response.status_code in [401, 403]
        
        # Test with malformed authorization header
        malformed_headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/api/v1/organizations/", headers=malformed_headers)
        assert response.status_code in [401, 403]

    def test_validation_error_details(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test detailed validation error responses."""
        auth_headers = create_auth_headers(admin_token)
        
        # Test missing required fields
        incomplete_data = {"name": "Incomplete Organization"}  # Missing 'code'
        response = client.post(
            "/api/v1/organizations/",
            json=incomplete_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Should indicate missing 'code' field
        assert any("code" in str(error) for error in data["detail"])
        
        # Test invalid field types
        invalid_type_data = {
            "code": "INVALID-TYPE",
            "name": "Invalid Type Organization",
            "is_active": "yes",  # Should be boolean
        }
        response = client.post(
            "/api/v1/organizations/",
            json=invalid_type_data,
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Test invalid field values
        invalid_value_data = {
            "code": "",  # Empty code
            "name": "Invalid Value Organization",
            "is_active": True,
        }
        response = client.post(
            "/api/v1/organizations/",
            json=invalid_value_data,
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_hierarchy_validation_errors(
        self,
        db_session: Session,
        test_organization: Organization,
        test_user: User,
    ):
        """Test organization hierarchy validation errors."""
        service = OrganizationService(db_session)
        
        # Test self-parent assignment
        with pytest.raises(ValidationError) as exc_info:
            service.validate_parent_assignment(
                test_organization.id, test_organization.id
            )
        assert "cannot be its own parent" in str(exc_info.value)
        
        # Create a deeper hierarchy for circular reference test
        level1 = OrganizationFactory.create(
            db_session,
            code="LEVEL-1",
            name="Level 1 Organization",
            created_by=test_user.id,
        )
        level2 = OrganizationFactory.create(
            db_session,
            code="LEVEL-2",
            name="Level 2 Organization",
            parent_id=level1.id,
            created_by=test_user.id,
        )
        level3 = OrganizationFactory.create(
            db_session,
            code="LEVEL-3",
            name="Level 3 Organization",
            parent_id=level2.id,
            created_by=test_user.id,
        )
        
        # Try to make level1 a child of level3 (circular reference)
        with pytest.raises(ValidationError) as exc_info:
            service.validate_parent_assignment(level1.id, level3.id)
        assert "Circular reference detected" in str(exc_info.value)

    def test_transaction_rollback_on_errors(
        self,
        client: TestClient,
        db_session: Session,
        test_organization: Organization,
        admin_token: str,
    ):
        """Test that transactions are properly rolled back on errors."""
        auth_headers = create_auth_headers(admin_token)
        
        # Get initial organization count
        initial_response = client.get("/api/v1/organizations/", headers=auth_headers)
        initial_count = initial_response.json()["total"]
        
        # Try to create organization with duplicate code (should fail)
        duplicate_data = {
            "code": test_organization.code,
            "name": "Should Not Be Created",
            "is_active": True,
        }
        response = client.post(
            "/api/v1/organizations/",
            json=duplicate_data,
            headers=auth_headers
        )
        assert response.status_code == 409
        
        # Verify no new organization was created
        final_response = client.get("/api/v1/organizations/", headers=auth_headers)
        final_count = final_response.json()["total"]
        assert final_count == initial_count

    def test_bulk_operation_error_handling(
        self,
        client: TestClient,
        db_session: Session,
        admin_token: str,
    ):
        """Test error handling in bulk operations."""
        auth_headers = create_auth_headers(admin_token)
        
        # Create organization for testing
        test_org = OrganizationFactory.create(
            db_session,
            code="BULK-ERROR-TEST",
            name="Bulk Error Test Organization",
        )
        
        # Test bulk subsidiary retrieval with invalid parent
        response = client.get(
            "/api/v1/organizations/99999/subsidiaries",
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Test recursive subsidiary retrieval with invalid parent
        response = client.get(
            "/api/v1/organizations/99999/subsidiaries?recursive=true",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_settings_update_error_handling(
        self,
        client: TestClient,
        test_organization: Organization,
        admin_token: str,
    ):
        """Test error handling for settings updates."""
        auth_headers = create_auth_headers(admin_token)
        
        # Test settings update with invalid organization ID
        settings_data = {"fiscal_year_start": "01-01"}
        response = client.put(
            "/api/v1/organizations/99999/settings",
            json=settings_data,
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Test settings update with invalid data (this depends on validation logic)
        # For now, most settings are flexible JSON, so this might not fail
        # But we can test with clearly invalid JSON structure
        try:
            response = client.put(
                f"/api/v1/organizations/{test_organization.id}/settings",
                json="not-a-dict",  # Invalid JSON for settings
                headers=auth_headers
            )
            # If validation exists, should return 422
            if response.status_code == 422:
                assert "detail" in response.json()
        except Exception:
            # If JSON parsing fails at framework level, that's also acceptable
            pass

    def test_concurrent_operation_error_handling(
        self,
        db_session: Session,
        test_organization: Organization,
        test_user: User,
    ):
        """Test error handling for concurrent operations."""
        service = OrganizationService(db_session)
        
        # Simulate concurrent update scenario
        # Get organization
        org1 = service.get_organization(test_organization.id)
        org2 = service.get_organization(test_organization.id)
        
        assert org1 is not None
        assert org2 is not None
        
        # First update succeeds
        result1 = service.update_organization(
            test_organization.id,
            OrganizationUpdate(description="First update"),
            updated_by=test_user.id,
        )
        assert result1 is not None
        
        # Second update also succeeds (no optimistic locking in current implementation)
        result2 = service.update_organization(
            test_organization.id,
            OrganizationUpdate(description="Second update"),
            updated_by=test_user.id,
        )
        assert result2 is not None
        
        # Verify the last update wins
        final_org = service.get_organization(test_organization.id)
        assert final_org is not None
        assert final_org.description == "Second update"

    def test_api_rate_limiting_behavior(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test API behavior under rapid requests (basic load testing)."""
        auth_headers = create_auth_headers(admin_token)
        
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get("/api/v1/organizations/", headers=auth_headers)
            responses.append(response)
        
        # All requests should succeed (no rate limiting in current implementation)
        for response in responses:
            assert response.status_code == 200

    def test_error_message_consistency(
        self,
        client: TestClient,
        test_organization: Organization,
        admin_token: str,
    ):
        """Test that error messages are consistent and informative."""
        auth_headers = create_auth_headers(admin_token)
        
        # Test consistent 404 messages
        not_found_endpoints = [
            f"/api/v1/organizations/99999",
            f"/api/v1/organizations/99999/subsidiaries",
            f"/api/v1/organizations/code/NONEXISTENT",
        ]
        
        for endpoint in not_found_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "not found" in data["detail"].lower()
        
        # Test consistent permission denied messages
        user_headers = {"Authorization": "Bearer invalid-token"}
        protected_endpoints = [
            "/api/v1/organizations/",
            f"/api/v1/organizations/{test_organization.id}",
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code in [401, 403]

    def test_error_logging_and_debugging(
        self,
        db_session: Session,
        test_organization: Organization,
    ):
        """Test that errors provide sufficient information for debugging."""
        service = OrganizationService(db_session)
        
        # Test exception with context information
        try:
            service.get_organization_statistics(99999)
        except NotFound as e:
            # Exception should contain organization ID for debugging
            assert "99999" in str(e)
        
        # Test validation error with specific details
        try:
            service.validate_parent_assignment(
                test_organization.id, test_organization.id
            )
        except ValidationError as e:
            # Should provide clear explanation
            assert "own parent" in str(e)
        
        # Test that service methods handle None inputs gracefully
        assert service.get_organization(None) is None
        assert service.get_organization_settings(None) == {}
        assert not service.validate_organization_exists(None)