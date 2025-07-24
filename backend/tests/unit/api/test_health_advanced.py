"""Advanced API tests for health endpoints."""

from fastapi.testclient import TestClient

from app.main import app


class TestHealthAPI:
    """Comprehensive tests for health API endpoints."""

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

    def test_get__live_success(self):
        """Test GET /live successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/live", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__live_validation_error(self):
        """Test GET /live validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/live", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__ready_success(self):
        """Test GET /ready successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/ready", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__ready_validation_error(self):
        """Test GET /ready validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/ready", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__database_success(self):
        """Test GET /database successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/database", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__database_validation_error(self):
        """Test GET /database validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/database", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__metrics_endpoint_success(self):
        """Test GET /metrics-endpoint successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/metrics-endpoint", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__metrics_endpoint_validation_error(self):
        """Test GET /metrics-endpoint validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/metrics-endpoint", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__system_success(self):
        """Test GET /system successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/system", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__system_validation_error(self):
        """Test GET /system validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/system", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__startup_success(self):
        """Test GET /startup successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/startup", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__startup_validation_error(self):
        """Test GET /startup validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/startup", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__agent_success(self):
        """Test GET /agent successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/agent", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__agent_validation_error(self):
        """Test GET /agent validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/agent", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

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
