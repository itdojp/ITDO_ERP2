"""Integration tests for role permission UI API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from tests.conftest import create_auth_headers
from tests.factories import OrganizationFactory, RoleFactory, UserFactory


@pytest.fixture
def test_organization(db_session: Session) -> Organization:
    """Create test organization."""
    return OrganizationFactory.create(db_session, name="Test Organization")


@pytest.fixture
def test_admin_user(db_session: Session) -> User:
    """Create admin user for testing."""
    return UserFactory.create_with_password(
        db_session, email="admin@test.com", password="password123", is_superuser=True
    )


@pytest.fixture
def admin_token(test_admin_user: User) -> str:
    """Create admin user token for testing."""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": str(test_admin_user.id)})


@pytest.fixture
def test_role(db_session: Session) -> Role:
    """Create test role."""
    import uuid

    return RoleFactory.create(
        db_session, code=f"TEST_ROLE_{uuid.uuid4().hex[:8]}", name="Test Role"
    )


def test_get_permission_definitions(
    client: TestClient, test_admin_user: User, admin_token: str
) -> None:
    """Test getting permission definitions."""
    response = client.get("/api/v1/role-permissions/definitions", headers=create_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()

    # Should have at least 3 categories
    assert len(data) >= 3

    # Check structure
    for category in data:
        assert "name" in category
        assert "groups" in category
        assert len(category["groups"]) > 0


def test_get_permission_ui_structure(
    client: TestClient, test_admin_user: User, admin_token: str
) -> None:
    """Test getting permission UI structure."""
    response = client.get("/api/v1/role-permissions/structure", headers=create_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "categories" in data
    assert "total_permissions" in data
    assert len(data["categories"]) > 0
    assert data["total_permissions"] > 0


def test_get_role_permission_matrix(
    client: TestClient,
    test_admin_user: User,
    test_organization: Organization,
    test_role: Role,
    admin_token: str,
) -> None:
    """Test getting role permission matrix."""
    from tests.conftest import create_auth_headers
    response = client.get(
        f"/api/v1/role-permissions/role/{test_role.id}/matrix",
        params={"organization_id": test_organization.id},
        headers=create_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert data["role_id"] == test_role.id
    assert data["role_name"] == test_role.name
    assert data["organization_id"] == test_organization.id
    assert "permissions" in data
    assert isinstance(data["permissions"], dict)


def test_search_permissions(
    client: TestClient, test_admin_user: User, admin_token: str
) -> None:
    """Test searching permissions."""
    from tests.conftest import create_auth_headers
    response = client.get(
        "/api/v1/role-permissions/search",
        params={"query": "user"},
        headers=create_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()

    # Should find user-related permissions
    assert len(data) > 0

    # Check result structure
    for result in data:
        assert "permission" in result
        assert "category_name" in result
        assert "group_name" in result
        assert "match_score" in result

        # Should contain 'user' in some field
        permission = result["permission"]
        contains_user = (
            "user" in permission["code"].lower()
            or "user" in permission["name"].lower()
            or "user" in permission["description"].lower()
        )
        assert contains_user, f"Permission {permission['code']} should contain 'user'"
