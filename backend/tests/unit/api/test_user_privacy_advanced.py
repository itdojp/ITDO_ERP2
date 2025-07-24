"""Advanced API tests for user_privacy endpoints."""

from fastapi.testclient import TestClient

from app.main import app


class TestUserPrivacyAPI:
    """Comprehensive tests for user_privacy API endpoints."""

    def setup_method(self):
        """Setup test environment."""
        self.client = TestClient(app)
        self.headers = {"Content-Type": "application/json"}

    def test_get__me_success(self):
        """Test GET /me successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get("/me", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__me_validation_error(self):
        """Test GET /me validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get("/me", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_get__me_unauthorized(self):
        """Test GET /me without authentication."""
        # Make request without auth
        response = self.client.get("/me")

        # Should return unauthorized
        assert response.status_code == 401

    def test_put__me_success(self):
        """Test PUT /me successful response."""
        # Setup test data
        test_data = self.get_test_data_for_put()

        # Make request
        response = self.client.put("/me", json=test_data, headers=self.headers)

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_put__me_validation_error(self):
        """Test PUT /me validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.put("/me", json=invalid_data, headers=self.headers)

        # Should return validation error
        assert response.status_code == 422

    def test_put__me_unauthorized(self):
        """Test PUT /me without authentication."""
        # Make request without auth
        response = self.client.put("/me")

        # Should return unauthorized
        assert response.status_code == 401

    def test_post__me_set_all_private_success(self):
        """Test POST /me/set-all-private successful response."""
        # Setup test data
        test_data = self.get_test_data_for_post()

        # Make request
        response = self.client.post(
            "/me/set-all-private", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_post__me_set_all_private_validation_error(self):
        """Test POST /me/set-all-private validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.post(
            "/me/set-all-private", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_post__me_set_all_private_unauthorized(self):
        """Test POST /me/set-all-private without authentication."""
        # Make request without auth
        response = self.client.post("/me/set-all-private")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__check_profile_user_id_success(self):
        """Test GET /check/profile/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/check/profile/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__check_profile_user_id_validation_error(self):
        """Test GET /check/profile/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/check/profile/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__check_profile_user_id_unauthorized(self):
        """Test GET /check/profile/{user_id} without authentication."""
        # Make request without auth
        response = self.client.get("/check/profile/{user_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__check_email_user_id_success(self):
        """Test GET /check/email/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/check/email/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__check_email_user_id_validation_error(self):
        """Test GET /check/email/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/check/email/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__check_email_user_id_unauthorized(self):
        """Test GET /check/email/{user_id} without authentication."""
        # Make request without auth
        response = self.client.get("/check/email/{user_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__check_phone_user_id_success(self):
        """Test GET /check/phone/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/check/phone/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__check_phone_user_id_validation_error(self):
        """Test GET /check/phone/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/check/phone/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__check_phone_user_id_unauthorized(self):
        """Test GET /check/phone/{user_id} without authentication."""
        # Make request without auth
        response = self.client.get("/check/phone/{user_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__check_activity_user_id_success(self):
        """Test GET /check/activity/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/check/activity/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__check_activity_user_id_validation_error(self):
        """Test GET /check/activity/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/check/activity/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__check_activity_user_id_unauthorized(self):
        """Test GET /check/activity/{user_id} without authentication."""
        # Make request without auth
        response = self.client.get("/check/activity/{user_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__check_online_status_user_id_success(self):
        """Test GET /check/online-status/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/check/online-status/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__check_online_status_user_id_validation_error(self):
        """Test GET /check/online-status/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/check/online-status/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__check_online_status_user_id_unauthorized(self):
        """Test GET /check/online-status/{user_id} without authentication."""
        # Make request without auth
        response = self.client.get("/check/online-status/{user_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__check_direct_message_user_id_success(self):
        """Test GET /check/direct-message/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/check/direct-message/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__check_direct_message_user_id_validation_error(self):
        """Test GET /check/direct-message/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/check/direct-message/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__check_direct_message_user_id_unauthorized(self):
        """Test GET /check/direct-message/{user_id} without authentication."""
        # Make request without auth
        response = self.client.get("/check/direct-message/{user_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__filter_user_data_user_id_success(self):
        """Test GET /filter-user-data/{user_id} successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/filter-user-data/{user_id}", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__filter_user_data_user_id_validation_error(self):
        """Test GET /filter-user-data/{user_id} validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/filter-user-data/{user_id}", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__filter_user_data_user_id_unauthorized(self):
        """Test GET /filter-user-data/{user_id} without authentication."""
        # Make request without auth
        response = self.client.get("/filter-user-data/{user_id}")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__searchable_email_success(self):
        """Test GET /searchable/email successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/searchable/email", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__searchable_email_validation_error(self):
        """Test GET /searchable/email validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/searchable/email", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__searchable_email_unauthorized(self):
        """Test GET /searchable/email without authentication."""
        # Make request without auth
        response = self.client.get("/searchable/email")

        # Should return unauthorized
        assert response.status_code == 401

    def test_get__searchable_name_success(self):
        """Test GET /searchable/name successful response."""
        # Setup test data
        test_data = self.get_test_data_for_get()

        # Make request
        response = self.client.get(
            "/searchable/name", json=test_data, headers=self.headers
        )

        # Assertions
        assert response.status_code in [200, 201, 204]
        if response.content:
            data = response.json()
            assert isinstance(data, (dict, list))

    def test_get__searchable_name_validation_error(self):
        """Test GET /searchable/name validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}

        response = self.client.get(
            "/searchable/name", json=invalid_data, headers=self.headers
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get__searchable_name_unauthorized(self):
        """Test GET /searchable/name without authentication."""
        # Make request without auth
        response = self.client.get("/searchable/name")

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
