"""Advanced API tests for users_simple endpoints."""

from fastapi.testclient import TestClient

from app.main import app


class TestUsersSimpleAPI:
    """Comprehensive tests for users_simple API endpoints."""

    def setup_method(self):
        """Setup test environment."""
        self.client = TestClient(app)
        self.headers = {"Content-Type": "application/json"}

    def test_post__users_success(self):
        """Test POST /users successful response."""
        # Setup test data
        test_data = self.get_test_data_for_post()

        # Make request
        response = self.client.post("/users", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_post__users_validation_error(self):
        """Test POST /users validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.post("/users", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__users_success(self):
        """Test GET /users successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/users", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__users_validation_error(self):
        """Test GET /users validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/users", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__users_user_id_success(self):
        """Test GET /users/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/users/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__users_user_id_validation_error(self):
        """Test GET /users/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/users/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_put__users_user_id_success(self):
        """Test PUT /users/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_put()

        # Make request
        response = self.client.put(
            "/users/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_put__users_user_id_validation_error(self):
        """Test PUT /users/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.put(
            "/users/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_delete__users_user_id_success(self):
        """Test DELETE /users/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_delete()

        # Make request
        response = self.client.delete(
            "/users/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_delete__users_user_id_validation_error(self):
        """Test DELETE /users/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.delete(
            "/users/{user_id}", json=invalid_data, headers=self.headers
        )

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
