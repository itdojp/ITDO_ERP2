from locust import HttpUser, task, between
import random
import json

class ERPUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login when test starts."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test@example.com",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task(3)
    def view_dashboard(self):
        """Most common operation."""
        self.client.get("/api/v1/dashboard", headers=self.headers)

    @task(2)
    def list_users(self):
        """Moderate frequency operation."""
        self.client.get("/api/v1/users", headers=self.headers)

    @task(1)
    def create_user(self):
        """Less frequent operation."""
        user_data = {
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "full_name": "Load Test User",
            "password": "TestPass123!"
        }
        self.client.post("/api/v1/users", json=user_data, headers=self.headers)

class AdminUser(HttpUser):
    wait_time = between(2, 5)

    @task
    def generate_report(self):
        """Heavy operation."""
        self.client.get("/api/v1/reports/generate?type=monthly",
                       headers=self.headers,
                       timeout=30)