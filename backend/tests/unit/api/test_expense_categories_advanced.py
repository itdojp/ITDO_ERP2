"""Advanced API tests for expense_categories endpoints."""

from fastapi.testclient import TestClient

from app.main import app


class TestExpenseCategoriesAPI:
    """Comprehensive tests for expense_categories API endpoints."""

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

    def test_get__tree_success(self):
        """Test GET /tree successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/tree", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__tree_validation_error(self):
        """Test GET /tree validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/tree", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__tree_unauthorized(self):
        """Test GET /tree without authentication."""
        # Make request without auth
        response = self.client.get("/tree")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__category_id_success(self):
        """Test GET /{category_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/{category_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__category_id_validation_error(self):
        """Test GET /{category_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/{category_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__category_id_unauthorized(self):
        """Test GET /{category_id} without authentication."""
        # Make request without auth
        response = self.client.get("/{category_id}")

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

    def test_post__bulk_success(self):
        """Test POST /bulk successful response."""
        # Setup test data
        test_data = self.get_test_data_for_post()

        # Make request
        response = self.client.post("/bulk", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_post__bulk_validation_error(self):
        """Test POST /bulk validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.post("/bulk", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_post__bulk_unauthorized(self):
        """Test POST /bulk without authentication."""
        # Make request without auth
        response = self.client.post("/bulk")

        # Should return unauthorized
        assert response.status_code == 401

    def test_put__category_id_success(self):
        """Test PUT /{category_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_put()

        # Make request
        response = self.client.put(
            "/{category_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_put__category_id_validation_error(self):
        """Test PUT /{category_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.put(
            "/{category_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_put__category_id_unauthorized(self):
        """Test PUT /{category_id} without authentication."""
        # Make request without auth
        response = self.client.put("/{category_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_delete__category_id_success(self):
        """Test DELETE /{category_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_delete()

        # Make request
        response = self.client.delete(
            "/{category_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_delete__category_id_validation_error(self):
        """Test DELETE /{category_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.delete(
            "/{category_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_delete__category_id_unauthorized(self):
        """Test DELETE /{category_id} without authentication."""
        # Make request without auth
        response = self.client.delete("/{category_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__analytics_usage_success(self):
        """Test GET /analytics/usage successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/analytics/usage", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__analytics_usage_validation_error(self):
        """Test GET /analytics/usage validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/analytics/usage", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__analytics_usage_unauthorized(self):
        """Test GET /analytics/usage without authentication."""
        # Make request without auth
        response = self.client.get("/analytics/usage")

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
