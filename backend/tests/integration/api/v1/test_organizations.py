"""
Organization API integration tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.main import app
from tests.factories import (
    create_test_organization,
    create_test_role,
    create_test_user,
    create_test_user_role,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def get_auth_header(user) -> dict:
    """Get authorization header for user."""
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestOrganizationAPI:
    """Test cases for Organization API endpoints."""

    def test_create_organization_api(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-ORG-001: 組織作成APIが正しく動作することを確認."""
        # Given: システム管理者トークン
        admin = create_test_user(is_superuser=True)
        db_session.commit()
        headers = get_auth_header(admin)

        # When: API呼び出し
        response = client.post(
            "/api/v1/organizations",
            json={
                "code": "NEWORG",
                "name": "新組織",
                "email": "new@example.com",
                "fiscal_year_start": 4,
            },
            headers=headers,
        )

        # Then:
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "NEWORG"
        assert data["name"] == "新組織"
        assert data["id"] is not None
        assert data["is_active"] is True

    def test_create_organization_unauthorized(
        self, client: TestClient, db_session: Session
    ) -> None:
        """認証なしで組織作成が拒否されることを確認."""
        # When: 認証なしでAPI呼び出し
        response = client.post(
            "/api/v1/organizations", json={"code": "UNAUTH", "name": "無認証組織"}
        )

        # Then:
        assert response.status_code == 403  # No auth header

    def test_create_organization_forbidden(
        self, client: TestClient, db_session: Session
    ) -> None:
        """一般ユーザーによる組織作成が拒否されることを確認."""
        # Given: 一般ユーザー
        user = create_test_user(is_superuser=False)
        db_session.commit()
        headers = get_auth_header(user)

        # When: API呼び出し
        response = client.post(
            "/api/v1/organizations",
            json={"code": "FORBIDDEN", "name": "権限なし組織"},
            headers=headers,
        )

        # Then:
        assert response.status_code == 403
        assert "システム管理者権限が必要です" in response.json()["detail"]

    def test_list_organizations_api(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-ORG-002: 組織一覧APIがフィルタリングされることを確認."""
        # Given: 複数組織と制限ユーザー
        org1 = create_test_organization(code="ORG1", name="組織1")
        create_test_organization(code="ORG2", name="組織2")
        create_test_organization(code="ORG3", name="組織3")

        user = create_test_user()
        role = create_test_role(code="ORG_ADMIN")
        create_test_user_role(user=user, role=role, organization=org1)
        db_session.commit()

        headers = get_auth_header(user)

        # When: API呼び出し
        response = client.get("/api/v1/organizations", headers=headers)

        # Then: 所属組織のみ
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == org1.id

    def test_get_organization_detail(
        self, client: TestClient, db_session: Session
    ) -> None:
        """組織詳細取得APIが正しく動作することを確認."""
        # Given: 組織とアクセス権を持つユーザー
        org = create_test_organization(
            code="DETAIL", name="詳細テスト組織", email="detail@example.com"
        )
        user = create_test_user()
        role = create_test_role()
        create_test_user_role(user=user, role=role, organization=org)
        db_session.commit()

        headers = get_auth_header(user)

        # When: API呼び出し
        response = client.get(f"/api/v1/organizations/{org.id}", headers=headers)

        # Then:
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == org.id
        assert data["code"] == "DETAIL"
        assert data["name"] == "詳細テスト組織"

    def test_get_organization_forbidden(
        self, client: TestClient, db_session: Session
    ) -> None:
        """アクセス権のない組織の詳細取得が拒否されることを確認."""
        # Given: 組織とアクセス権のないユーザー
        org = create_test_organization()
        user = create_test_user()
        db_session.commit()

        headers = get_auth_header(user)

        # When: API呼び出し
        response = client.get(f"/api/v1/organizations/{org.id}", headers=headers)

        # Then:
        assert response.status_code == 403

    def test_update_organization_api(
        self, client: TestClient, db_session: Session
    ) -> None:
        """組織更新APIが正しく動作することを確認."""
        # Given: 組織と組織管理者
        org = create_test_organization(name="旧名称", email="old@example.com")
        admin = create_test_user()
        admin_role = create_test_role(code="ORG_ADMIN", permissions=["org:*"])
        create_test_user_role(user=admin, role=admin_role, organization=org)
        db_session.commit()

        headers = get_auth_header(admin)

        # When: API呼び出し
        response = client.put(
            f"/api/v1/organizations/{org.id}",
            json={"name": "新名称", "email": "new@example.com"},
            headers=headers,
        )

        # Then:
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["email"] == "new@example.com"

    def test_delete_organization_api(
        self, client: TestClient, db_session: Session
    ) -> None:
        """組織削除（論理削除）APIが正しく動作することを確認."""
        # Given: 組織とシステム管理者
        org = create_test_organization(is_active=True)
        admin = create_test_user(is_superuser=True)
        db_session.commit()

        headers = get_auth_header(admin)

        # When: API呼び出し
        response = client.delete(f"/api/v1/organizations/{org.id}", headers=headers)

        # Then:
        assert response.status_code == 204

        # 論理削除確認
        db_session.refresh(org)
        assert org.is_active is False

    def test_organization_search_api(
        self, client: TestClient, db_session: Session
    ) -> None:
        """組織検索APIが正しく動作することを確認."""
        # Given: 複数組織
        create_test_organization(name="アルファ商事", code="ALPHA")
        create_test_organization(name="ベータ工業", code="BETA")
        create_test_organization(name="アルファシステム", code="ALPHASYS")

        admin = create_test_user(is_superuser=True)
        db_session.commit()

        headers = get_auth_header(admin)

        # When: 検索API呼び出し
        response = client.get(
            "/api/v1/organizations", params={"search": "アルファ"}, headers=headers
        )

        # Then:
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        org_names = [item["name"] for item in data["items"]]
        assert "アルファ商事" in org_names
        assert "アルファシステム" in org_names
        assert "ベータ工業" not in org_names

    def test_organization_pagination_api(
        self, client: TestClient, db_session: Session
    ) -> None:
        """組織一覧のページネーションAPIが正しく動作することを確認."""
        # Given: 多数の組織
        for i in range(15):
            create_test_organization(code=f"PAGE{i:03d}")

        admin = create_test_user(is_superuser=True)
        db_session.commit()

        headers = get_auth_header(admin)

        # When: ページ1
        response1 = client.get(
            "/api/v1/organizations", params={"page": 1, "limit": 10}, headers=headers
        )

        # When: ページ2
        response2 = client.get(
            "/api/v1/organizations", params={"page": 2, "limit": 10}, headers=headers
        )

        # Then:
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert len(data1["items"]) == 10
        assert len(data2["items"]) == 5
        assert data1["total"] == 15
        assert data1["page"] == 1
        assert data2["page"] == 2

    def test_organization_validation_errors(
        self, client: TestClient, db_session: Session
    ) -> None:
        """組織作成時のバリデーションエラーが正しく返されることを確認."""
        # Given: システム管理者
        admin = create_test_user(is_superuser=True)
        db_session.commit()
        headers = get_auth_header(admin)

        # When: 不正なデータで作成
        response = client.post(
            "/api/v1/organizations",
            json={
                "code": "",  # 空のコード
                "name": "",  # 空の名前
                "email": "invalid-email",  # 不正なメール
                "fiscal_year_start": 13,  # 範囲外
            },
            headers=headers,
        )

        # Then:
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(e["loc"] == ["body", "code"] for e in errors)
        assert any(e["loc"] == ["body", "name"] for e in errors)
        assert any(e["loc"] == ["body", "email"] for e in errors)
        assert any(e["loc"] == ["body", "fiscal_year_start"] for e in errors)
