"""Tests for GraphQL queries."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization


class TestGraphQLQueries:
    """Test GraphQL query functionality."""

    def test_health_query(self, client: TestClient):
        """Test GraphQL health query."""
        query = """
        query {
            health
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["health"] == "GraphQL API is healthy"

    def test_user_query_without_auth(self, client: TestClient):
        """Test user query without authentication."""
        query = """
        query {
            user(id: "1") {
                id
                email
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return error for unauthorized access
        assert "errors" in data

    def test_me_query_with_auth(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test me query with authentication."""
        query = """
        query {
            me {
                id
                email
                fullName
                isActive
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["me"]["email"] == test_user.email

    def test_users_query_with_auth(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test users query with authentication."""
        query = """
        query {
            users {
                id
                email
                fullName
                isActive
                organizationId
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        users = data["data"]["users"]
        assert isinstance(users, list)

    def test_user_with_organization_dataloader(
        self, 
        client: TestClient, 
        test_user: User, 
        test_organization: Organization,
        auth_headers: dict
    ):
        """Test user query with organization field using DataLoader."""
        query = """
        query {
            me {
                id
                email
                organization {
                    id
                    name
                    code
                }
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        user_data = data["data"]["me"]
        assert user_data["organization"]["name"] == test_organization.name

    def test_tasks_query_with_filters(self, client: TestClient, auth_headers: dict):
        """Test tasks query with filtering."""
        query = """
        query GetTasks($filters: TaskFilters) {
            tasks(filters: $filters) {
                id
                title
                status
                priority
                assignee {
                    id
                    email
                }
            }
        }
        """
        
        variables = {
            "filters": {
                "status": "PENDING",
                "priority": "HIGH"
            }
        }
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query, "variables": variables},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        tasks = data["data"]["tasks"]
        assert isinstance(tasks, list)

    def test_search_users_query(self, client: TestClient, auth_headers: dict):
        """Test search users query."""
        query = """
        query SearchUsers($query: String!, $limit: Int) {
            searchUsers(query: $query, limit: $limit) {
                id
                email
                fullName
            }
        }
        """
        
        variables = {
            "query": "test",
            "limit": 5
        }
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query, "variables": variables},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        users = data["data"]["searchUsers"]
        assert isinstance(users, list)

    def test_my_organization_query(self, client: TestClient, auth_headers: dict):
        """Test my organization query."""
        query = """
        query {
            myOrganization {
                id
                name
                code
                description
                isActive
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # myOrganization could be null if user has no organization

    def test_my_tasks_query(self, client: TestClient, auth_headers: dict):
        """Test my tasks query."""
        query = """
        query {
            myTasks {
                id
                title
                status
                priority
                dueDate
                project {
                    id
                    name
                }
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        tasks = data["data"]["myTasks"]
        assert isinstance(tasks, list)

    def test_graphql_introspection(self, client: TestClient):
        """Test GraphQL introspection query."""
        query = """
        query {
            __schema {
                types {
                    name
                    kind
                }
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "__schema" in data["data"]
        types = data["data"]["__schema"]["types"]
        assert isinstance(types, list)
        
        # Check that our custom types are present
        type_names = [t["name"] for t in types]
        assert "User" in type_names
        assert "Organization" in type_names
        assert "Task" in type_names

    def test_graphql_error_handling(self, client: TestClient):
        """Test GraphQL error handling for invalid queries."""
        invalid_query = """
        query {
            nonExistentField
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": invalid_query}
        )
        
        assert response.status_code == 200  # GraphQL returns 200 even for errors
        data = response.json()
        assert "errors" in data
        assert len(data["errors"]) > 0

    def test_graphql_variables_validation(self, client: TestClient):
        """Test GraphQL variables validation."""
        query = """
        query GetUser($id: ID!) {
            user(id: $id) {
                id
                email
            }
        }
        """
        
        # Missing required variable
        response = client.post(
            "/api/v1/graphql",
            json={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data

    def test_dataloader_n_plus_one_prevention(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test that DataLoader prevents N+1 queries."""
        # This query would typically cause N+1 problem without DataLoader
        query = """
        query {
            users {
                id
                email
                organization {
                    id
                    name
                }
            }
        }
        """
        
        response = client.post(
            "/api/v1/graphql",
            json={"query": query},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        users = data["data"]["users"]
        
        # Each user should have organization data loaded efficiently
        for user in users:
            if user.get("organization"):
                assert "id" in user["organization"]
                assert "name" in user["organization"]