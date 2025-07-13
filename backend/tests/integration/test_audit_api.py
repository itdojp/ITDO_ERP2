"""Integration tests for audit API."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User
from tests.conftest import create_auth_headers
from tests.factories import AuditLogFactory, OrganizationFactory, UserFactory


@pytest.fixture
def test_organization(db_session: Session) -> Organization:
    """Create test organization."""
    return OrganizationFactory.create(db_session, name="Test Audit Org")


@pytest.fixture
def test_admin_user(db_session: Session) -> User:
    """Create admin user for testing."""
    return UserFactory.create_with_password(
        db_session,
        email="audit_admin@test.com",
        password="password123",
        is_superuser=True,
    )


@pytest.fixture
def admin_token(client: TestClient) -> str:
    """Get admin user token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "audit_admin@test.com", "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.skip(reason="Audit API implementation pending")
def test_get_organization_audit_logs(
    client: TestClient,
    test_admin_user: User,
    test_organization: Organization,
    db_session: Session,
    admin_token: str,
) -> None:
    """Test getting organization audit logs."""
    # Create test audit logs
    for i in range(3):
        AuditLogFactory.create(
            db_session,
            user_id=test_admin_user.id,
            organization_id=test_organization.id,
            action=f"test.action_{i}",
            resource_type="TestResource",
            changes={"field": f"value_{i}"},
        )

    response = client.get(
        f"/api/v1/audit/organizations/{test_organization.id}/logs",
        headers=create_auth_headers(admin_token)
    )

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data

    # Should have 3 logs
    assert data["total"] == 3
    assert len(data["items"]) == 3

    # Check log structure
    log = data["items"][0]
    assert "id" in log
    assert "user_id" in log
    assert "action" in log
    assert "resource_type" in log
    assert "changes" in log
    assert "created_at" in log
    assert "user_email" in log


@pytest.mark.skip(reason="Audit API implementation pending")
def test_search_audit_logs(
    client: TestClient,
    test_admin_user: User,
    test_organization: Organization,
    db_session: Session,
    admin_token: str,
) -> None:
    """Test advanced audit log search."""
    # Create test audit logs with different actions
    AuditLogFactory.create(
        db_session,
        user_id=test_admin_user.id,
        organization_id=test_organization.id,
        action="user.create",
        resource_type="User",
        changes={"email": "test@example.com"},
    )

    AuditLogFactory.create(
        db_session,
        user_id=test_admin_user.id,
        organization_id=test_organization.id,
        action="user.update",
        resource_type="User",
        changes={"status": "active"},
    )

    # Search for user actions
    search_data = {
        "organization_id": test_organization.id,
        "actions": ["user.create", "user.update"],
        "limit": 50,
        "offset": 0,
    }

    response = client.post(
        f"/api/v1/audit/organizations/{test_organization.id}/logs/search",
        json=search_data,
        headers=create_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()

    # Should find both logs
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Check that all returned logs have expected actions
    actions = [log["action"] for log in data["items"]]
    assert "user.create" in actions
    assert "user.update" in actions


@pytest.mark.skip(reason="Audit API implementation pending")
def test_get_audit_statistics(
    client: TestClient,
    test_admin_user: User,
    test_organization: Organization,
    db_session: Session,
    admin_token: str,
) -> None:
    """Test getting audit statistics."""
    # Create test data
    base_time = datetime.now(timezone.utc)

    for i in range(5):
        AuditLogFactory.create(
            db_session,
            user_id=test_admin_user.id,
            organization_id=test_organization.id,
            action="user.create" if i % 2 == 0 else "user.update",
            resource_type="User",
            created_at=base_time - timedelta(hours=i),
        )

    date_from = base_time - timedelta(days=1)
    date_to = base_time + timedelta(hours=1)

    response = client.get(
        f"/api/v1/audit/organizations/{test_organization.id}/logs/statistics",
        params={"date_from": date_from.isoformat(), "date_to": date_to.isoformat()},
        headers=create_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()

    # Check statistics structure
    assert "total_logs" in data
    assert "unique_users" in data
    assert "action_counts" in data
    assert "resource_type_counts" in data

    # Verify statistics
    assert data["total_logs"] == 5
    assert data["unique_users"] == 1
    assert data["action_counts"]["user.create"] == 3
    assert data["action_counts"]["user.update"] == 2
    assert data["resource_type_counts"]["User"] == 5


@pytest.mark.skip(reason="Audit API implementation pending")
def test_export_audit_logs(
    client: TestClient,
    test_admin_user: User,
    test_organization: Organization,
    db_session: Session,
    admin_token: str,
) -> None:
    """Test audit log CSV export."""
    # Create test data
    AuditLogFactory.create(
        db_session,
        user_id=test_admin_user.id,
        organization_id=test_organization.id,
        action="test.export",
        resource_type="TestResource",
        changes={"field": "export_test"},
    )

    response = client.get(
        f"/api/v1/audit/organizations/{test_organization.id}/logs/export",
        headers=create_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]

    # Check CSV content
    csv_content = response.text
    lines = csv_content.strip().split("\n")

    # Should have header + at least one data row
    assert len(lines) >= 2

    # Check header
    header = lines[0]
    expected_columns = ["timestamp", "user_email", "action", "resource_type"]
    for column in expected_columns:
        assert column in header

    # Check data row contains expected action
    data_row = lines[1]
    assert "test.export" in data_row


@pytest.mark.skip(reason="Audit API implementation pending")
def test_get_recent_activity(
    client: TestClient,
    test_admin_user: User,
    test_organization: Organization,
    db_session: Session,
    admin_token: str,
) -> None:
    """Test getting recent audit activity."""
    # Create recent and old audit logs
    now = datetime.now(timezone.utc)

    # Recent log (within last 24 hours)
    AuditLogFactory.create(
        db_session,
        user_id=test_admin_user.id,
        organization_id=test_organization.id,
        action="recent.action",
        created_at=now - timedelta(hours=2),
    )

    # Old log (more than 24 hours ago)
    AuditLogFactory.create(
        db_session,
        user_id=test_admin_user.id,
        organization_id=test_organization.id,
        action="old.action",
        created_at=now - timedelta(hours=26),
    )

    response = client.get(
        f"/api/v1/audit/organizations/{test_organization.id}/logs/recent",
        params={"hours": 24},
        headers=create_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()

    # Should only return recent activity
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["action"] == "recent.action"


@pytest.mark.skip(reason="Audit API implementation pending")
def test_get_available_actions(
    client: TestClient,
    test_admin_user: User,
    test_organization: Organization,
    db_session: Session,
    admin_token: str,
) -> None:
    """Test getting available actions from audit logs."""
    # Create logs with different actions
    actions = ["user.create", "user.update", "role.assign"]
    for action in actions:
        AuditLogFactory.create(
            db_session,
            user_id=test_admin_user.id,
            organization_id=test_organization.id,
            action=action,
            resource_type="User",
        )

    response = client.get(
        f"/api/v1/audit/organizations/{test_organization.id}/logs/actions",
        headers=create_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()

    # Should return list of available actions
    assert isinstance(data, list)
    assert len(data) == 3

    for action in actions:
        assert action in data


@pytest.mark.skip(reason="Audit API implementation pending")
def test_permission_denied_for_wrong_organization(
    client: TestClient, test_admin_user: User, db_session: Session
) -> None:
    """Test permission denied for accessing wrong organization's logs."""
    # Create different organization
    other_org = OrganizationFactory.create(db_session, name="Other Org")

    # Create non-superuser
    UserFactory.create_with_password(
        db_session, email="regular@test.com", password="password123", is_superuser=False
    )

    # Get auth headers for regular user
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    regular_headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/v1/audit/organizations/{other_org.id}/logs", headers=regular_headers
    )

    assert response.status_code == 403
