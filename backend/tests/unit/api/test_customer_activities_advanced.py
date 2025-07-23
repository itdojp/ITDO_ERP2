"""Advanced API tests for customer_activities endpoints."""

from fastapi.testclient import TestClient

from app.main import app


class TestCustomerActivitiesAPI:
    """Comprehensive tests for customer_activities API endpoints."""

    def setup_method(self):
        """Setup test environment."""
        self.client = TestClient(app)
        self.headers = {"Content-Type": "application/json"}


    def test_get___success(self):
        """Test GET / successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get___validation_error(self):
        """Test GET / validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get___unauthorized(self):
        """Test GET / without authentication."""
        # Make request without auth
        response = self.client.get("/")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__activity_id_success(self):
        """Test GET /{activity_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/{activity_id}", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__activity_id_validation_error(self):
        """Test GET /{activity_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/{activity_id}", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__activity_id_unauthorized(self):
        """Test GET /{activity_id} without authentication."""
        # Make request without auth
        response = self.client.get("/{activity_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_post___success(self):
        """Test POST / successful response."""
        # Setup test data
        test_data = self.get_test_data_for_post()

        # Make request
        response = self.client.post("/", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_post___validation_error(self):
        """Test POST / validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.post("/", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_post___unauthorized(self):
        """Test POST / without authentication."""
        # Make request without auth
        response = self.client.post("/")

        # Should return unauthorized
        assert response.status_code == 401

    def test_put__activity_id_success(self):
        """Test PUT /{activity_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_put()

        # Make request
        response = self.client.put("/{activity_id}", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_put__activity_id_validation_error(self):
        """Test PUT /{activity_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.put("/{activity_id}", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_put__activity_id_unauthorized(self):
        """Test PUT /{activity_id} without authentication."""
        # Make request without auth
        response = self.client.put("/{activity_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_delete__activity_id_success(self):
        """Test DELETE /{activity_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_delete()

        # Make request
        response = self.client.delete("/{activity_id}", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_delete__activity_id_validation_error(self):
        """Test DELETE /{activity_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.delete("/{activity_id}", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_delete__activity_id_unauthorized(self):
        """Test DELETE /{activity_id} without authentication."""
        # Make request without auth
        response = self.client.delete("/{activity_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__reports_activity_summary_success(self):
        """Test GET /reports/activity-summary successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/reports/activity-summary", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__reports_activity_summary_validation_error(self):
        """Test GET /reports/activity-summary validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/reports/activity-summary", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__reports_activity_summary_unauthorized(self):
        """Test GET /reports/activity-summary without authentication."""
        # Make request without auth
        response = self.client.get("/reports/activity-summary")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__upcoming_next_actions_success(self):
        """Test GET /upcoming/next-actions successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/upcoming/next-actions", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__upcoming_next_actions_validation_error(self):
        """Test GET /upcoming/next-actions validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/upcoming/next-actions", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__upcoming_next_actions_unauthorized(self):
        """Test GET /upcoming/next-actions without authentication."""
        # Make request without auth
        response = self.client.get("/upcoming/next-actions")

        # Should return unauthorized
        assert response.status_code == 401

    def test_put__activity_id_complete_success(self):
        """Test PUT /{activity_id}/complete successful response."""
        # Setup test data
        test_data = self.get_test_data_for_put()

        # Make request
        response = self.client.put("/{activity_id}/complete", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_put__activity_id_complete_validation_error(self):
        """Test PUT /{activity_id}/complete validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.put("/{activity_id}/complete", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_put__activity_id_complete_unauthorized(self):
        """Test PUT /{activity_id}/complete without authentication."""
        # Make request without auth
        response = self.client.put("/{activity_id}/complete")

        # Should return unauthorized
        assert response.status_code == 401

    def get_test_data_for_get(self):
        """Get test data for GET requests."""
        return {}

    def get_test_data_for_post(self):
        """Get test data for POST requests."""
        return {"test": "data"}

    def get_test_data_for_put(self):
        """Get test data for PUT requests."""
        return {"test": "updated_data"}

    def get_test_data_for_delete(self):
        """Get test data for DELETE requests."""
        return {}

    def get_test_data_for_patch(self):
        """Get test data for PATCH requests."""
        return {"test": "patched_data"}
