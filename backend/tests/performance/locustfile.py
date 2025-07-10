"""Performance testing with Locust for ITDO ERP API endpoints."""

import random
from typing import Dict

from locust import HttpUser, between, events, task
from locust.exception import RescheduleTask


class ERPAPIUser(HttpUser):
    """Simulates a user of the ERP system API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.user_id = None
        self.organization_id = None
        self.department_id = None
        self.role_id = None

    def on_start(self):
        """Called when a user starts."""
        self.login()
        self.setup_test_data()

    def login(self):
        """Authenticate and get access token."""
        # Use admin credentials for testing
        login_data = {"username": "admin@example.com", "password": "AdminPassword123!"}

        response = self.client.post(
            "/api/v1/auth/login", json=login_data, catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.user_id = data.get("user_id")
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
            raise RescheduleTask()

    def setup_test_data(self):
        """Setup test data for performance testing."""
        if not self.auth_token:
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Create test organization
        org_data = {
            "code": f"PERF-ORG-{random.randint(1000, 9999)}",
            "name": f"Performance Test Org {random.randint(1000, 9999)}",
            "industry": "IT",
        }

        response = self.client.post(
            "/api/v1/organizations", json=org_data, headers=headers, catch_response=True
        )

        if response.status_code == 201:
            self.organization_id = response.json().get("id")
            response.success()
        else:
            response.failure(f"Organization creation failed: {response.status_code}")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.auth_token:
            self.login()
        return {"Authorization": f"Bearer {self.auth_token}"}

    @task(5)
    def list_organizations(self):
        """Test listing organizations."""
        self.client.get(
            "/api/v1/organizations",
            headers=self.get_auth_headers(),
            name="GET /organizations",
        )

    @task(3)
    def get_organization_tree(self):
        """Test organization tree endpoint."""
        self.client.get(
            "/api/v1/organizations/tree",
            headers=self.get_auth_headers(),
            name="GET /organizations/tree",
        )

    @task(4)
    def list_departments(self):
        """Test listing departments."""
        params = {"limit": 50}
        if self.organization_id:
            params["organization_id"] = self.organization_id

        self.client.get(
            "/api/v1/departments",
            params=params,
            headers=self.get_auth_headers(),
            name="GET /departments",
        )

    @task(2)
    def get_department_tree(self):
        """Test department tree endpoint."""
        if self.organization_id:
            self.client.get(
                f"/api/v1/departments/organization/{self.organization_id}/tree",
                headers=self.get_auth_headers(),
                name="GET /departments/tree",
            )

    @task(3)
    def list_roles(self):
        """Test listing roles."""
        params = {"limit": 50}
        if self.organization_id:
            params["organization_id"] = self.organization_id

        self.client.get(
            "/api/v1/roles",
            params=params,
            headers=self.get_auth_headers(),
            name="GET /roles",
        )

    @task(2)
    def get_role_tree(self):
        """Test role tree endpoint."""
        if self.organization_id:
            self.client.get(
                f"/api/v1/roles/organization/{self.organization_id}/tree",
                headers=self.get_auth_headers(),
                name="GET /roles/tree",
            )

    @task(2)
    def list_permissions(self):
        """Test listing permissions."""
        self.client.get(
            "/api/v1/roles/permissions",
            headers=self.get_auth_headers(),
            name="GET /permissions",
        )

    @task(1)
    def create_organization(self):
        """Test creating organization."""
        org_data = {
            "code": f"LOAD-{random.randint(10000, 99999)}",
            "name": f"Load Test Org {random.randint(1000, 9999)}",
            "industry": random.choice(["IT", "製造業", "小売業", "金融業"]),
        }

        self.client.post(
            "/api/v1/organizations",
            json=org_data,
            headers=self.get_auth_headers(),
            name="POST /organizations",
        )

    @task(1)
    def create_department(self):
        """Test creating department."""
        if not self.organization_id:
            return

        dept_data = {
            "code": f"DEPT-{random.randint(100, 999)}",
            "name": f"Load Test Department {random.randint(100, 999)}",
            "organization_id": self.organization_id,
            "department_type": random.choice(["operational", "support", "management"]),
        }

        self.client.post(
            "/api/v1/departments",
            json=dept_data,
            headers=self.get_auth_headers(),
            name="POST /departments",
        )

    @task(1)
    def create_role(self):
        """Test creating role."""
        if not self.organization_id:
            return

        role_data = {
            "name": f"Load Test Role {random.randint(100, 999)}",
            "organization_id": self.organization_id,
            "role_type": random.choice(["system", "custom", "department"]),
        }

        self.client.post(
            "/api/v1/roles",
            json=role_data,
            headers=self.get_auth_headers(),
            name="POST /roles",
        )

    @task(2)
    def search_organizations(self):
        """Test organization search."""
        search_terms = ["Test", "Corp", "Inc", "Ltd", "Company"]
        search_term = random.choice(search_terms)

        self.client.get(
            "/api/v1/organizations",
            params={"search": search_term, "limit": 20},
            headers=self.get_auth_headers(),
            name="GET /organizations (search)",
        )

    @task(2)
    def search_departments(self):
        """Test department search."""
        search_terms = ["部門", "事業部", "チーム", "グループ"]
        search_term = random.choice(search_terms)

        self.client.get(
            "/api/v1/departments",
            params={"search": search_term, "limit": 20},
            headers=self.get_auth_headers(),
            name="GET /departments (search)",
        )

    @task(1)
    def get_user_profile(self):
        """Test getting current user profile."""
        self.client.get(
            "/api/v1/users/me", headers=self.get_auth_headers(), name="GET /users/me"
        )


class HighLoadUser(ERPAPIUser):
    """High-frequency user for stress testing."""

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task(10)
    def rapid_organization_list(self):
        """Rapid organization listing."""
        self.client.get(
            "/api/v1/organizations?limit=10",
            headers=self.get_auth_headers(),
            name="Rapid GET /organizations",
        )

    @task(8)
    def rapid_department_list(self):
        """Rapid department listing."""
        self.client.get(
            "/api/v1/departments?limit=10",
            headers=self.get_auth_headers(),
            name="Rapid GET /departments",
        )

    @task(6)
    def rapid_role_list(self):
        """Rapid role listing."""
        self.client.get(
            "/api/v1/roles?limit=10",
            headers=self.get_auth_headers(),
            name="Rapid GET /roles",
        )


class ReadOnlyUser(HttpUser):
    """Read-only user for testing read performance."""

    wait_time = between(0.5, 2)

    def on_start(self):
        """Login with read-only credentials."""
        login_data = {
            "username": "readonly@example.com",
            "password": "ReadOnlyPassword123!",
        }

        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.auth_token}"}

    @task(8)
    def view_organizations(self):
        """View organizations."""
        self.client.get(
            "/api/v1/organizations",
            headers=self.get_auth_headers(),
            name="ReadOnly GET /organizations",
        )

    @task(6)
    def view_departments(self):
        """View departments."""
        self.client.get(
            "/api/v1/departments",
            headers=self.get_auth_headers(),
            name="ReadOnly GET /departments",
        )

    @task(4)
    def view_roles(self):
        """View roles."""
        self.client.get(
            "/api/v1/roles", headers=self.get_auth_headers(), name="ReadOnly GET /roles"
        )


# Event listeners for custom metrics
@events.request.add_listener
def on_request(
    request_type, name, response_time, response_length, exception, context, **kwargs
):
    """Custom request handler for additional metrics."""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 1000:  # Log slow requests (>1s)
        print(f"Slow request detected: {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("Performance test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("Performance test completed!")

    # Print summary statistics
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
