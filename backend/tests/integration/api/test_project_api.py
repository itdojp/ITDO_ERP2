"""Project API integration tests."""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from tests.factories import create_test_organization, create_test_user, create_test_project, create_test_role, create_test_user_role


class TestProjectAPI:
    """Project API test class."""

    def test_create_project_api(self, client: TestClient, auth_headers: dict, db_session) -> None:
        """TEST-API-PROJ-001: プロジェクト作成APIテスト."""
        # Given: プロジェクト作成データ
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        project_data = {
            "name": "APIテストプロジェクト",
            "description": "テスト用プロジェクト",
            "start_date": "2025-07-01",
            "end_date": "2025-12-31",
            "organization_id": organization.id
        }
        
        # When: POST /api/v1/projects
        response = client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers
        )
        
        # Then: 201 Createdで作成される
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "APIテストプロジェクト"
        assert data["description"] == "テスト用プロジェクト"
        assert data["status"] == "planning"
        assert data["start_date"] == "2025-07-01"
        assert data["end_date"] == "2025-12-31"
        assert data["organization_id"] == organization.id

    def test_list_projects_api(self, client: TestClient, auth_headers: dict, db_session) -> None:
        """TEST-API-PROJ-002: プロジェクト一覧取得APIテスト."""
        # Given: 複数のプロジェクト
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        projects = [
            create_test_project(
                name=f"プロジェクト{i}",
                organization_id=organization.id,
                created_by=user.id
            )
            for i in range(5)
        ]
        db_session.add_all(projects)
        db_session.commit()
        
        # When: GET /api/v1/projects
        response = client.get(
            "/api/v1/projects?page=1&limit=3",
            headers=auth_headers
        )
        
        # Then: ページネーションされた結果が返される
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["limit"] == 3

    def test_get_project_detail_api(self, client: TestClient, auth_headers: dict, db_session) -> None:
        """TEST-API-PROJ-003: プロジェクト詳細取得APIテスト."""
        # Given: 既存プロジェクト
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        project = create_test_project(
            name="詳細テスト",
            description="詳細取得テスト",
            organization_id=organization.id,
            created_by=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # When: GET /api/v1/projects/{id}
        response = client.get(
            f"/api/v1/projects/{project.id}",
            headers=auth_headers
        )
        
        # Then: プロジェクト詳細が返される
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "詳細テスト"
        assert data["description"] == "詳細取得テスト"

    def test_update_project_api(self, client: TestClient, auth_headers: dict, db_session) -> None:
        """TEST-API-PROJ-004: プロジェクト更新APIテスト."""
        # Given: 既存プロジェクト
        organization = create_test_organization()
        user = create_test_user()
        admin_role = create_test_role(code="PROJECT_ADMIN")
        create_test_user_role(user=user, role=admin_role, organization=organization)
        
        db_session.add_all([organization, user, admin_role])
        db_session.commit()
        
        project = create_test_project(
            name="更新前",
            organization_id=organization.id,
            created_by=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        update_data = {
            "name": "更新されたプロジェクト",
            "description": "更新された説明",
            "status": "in_progress"
        }
        
        # When: PUT /api/v1/projects/{id}
        response = client.put(
            f"/api/v1/projects/{project.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Then: プロジェクトが更新される
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新されたプロジェクト"
        assert data["description"] == "更新された説明"
        assert data["status"] == "in_progress"

    def test_delete_project_api(self, client: TestClient, admin_auth_headers: dict, db_session) -> None:
        """TEST-API-PROJ-005: プロジェクト削除APIテスト."""
        # Given: 既存プロジェクト
        organization = create_test_organization()
        admin = create_test_user(is_superuser=True)
        
        db_session.add_all([organization, admin])
        db_session.commit()
        
        project = create_test_project(
            name="削除テスト",
            organization_id=organization.id,
            created_by=admin.id
        )
        db_session.add(project)
        db_session.commit()
        
        # When: DELETE /api/v1/projects/{id}
        response = client.delete(
            f"/api/v1/projects/{project.id}",
            headers=admin_auth_headers
        )
        
        # Then: プロジェクトが削除される
        assert response.status_code == 204

    def test_unauthorized_access_denied(self, client: TestClient) -> None:
        """TEST-SECURITY-001: 認証なしアクセス拒否テスト."""
        # When: 認証ヘッダーなしでAPIアクセス
        response = client.get("/api/v1/projects")
        
        # Then: 401 Unauthorizedが返される
        assert response.status_code == 401

    def test_invalid_token_access_denied(self, client: TestClient) -> None:
        """TEST-SECURITY-002: 不正トークンアクセス拒否テスト."""
        # Given: 不正なトークン
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        # When: 不正トークンでAPIアクセス
        response = client.get("/api/v1/projects", headers=invalid_headers)
        
        # Then: 401 Unauthorizedが返される
        assert response.status_code == 401

    def test_cross_organization_access_denied(self, client: TestClient, db_session) -> None:
        """TEST-SECURITY-003: 組織間データアクセス拒否テスト."""
        # Given: 異なる組織のプロジェクトとユーザー
        org1 = create_test_organization(code="ORG1")
        org2 = create_test_organization(code="ORG2")
        
        org1_user = create_test_user(email="user1@org1.com")
        org2_user = create_test_user(email="user2@org2.com")
        
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=org1_user, role=member_role, organization=org1)
        create_test_user_role(user=org2_user, role=member_role, organization=org2)
        
        db_session.add_all([org1, org2, org1_user, org2_user, member_role])
        db_session.commit()
        
        org1_project = create_test_project(
            name="組織1プロジェクト",
            organization_id=org1.id,
            created_by=org1_user.id
        )
        db_session.add(org1_project)
        db_session.commit()
        
        # 組織2ユーザーの認証ヘッダー
        org2_auth_headers = {"Authorization": f"Bearer {create_auth_token(org2_user)}"}
        
        # When: 異なる組織のユーザーがプロジェクトにアクセス
        response = client.get(
            f"/api/v1/projects/{org1_project.id}",
            headers=org2_auth_headers
        )
        
        # Then: 403 Forbiddenが返される
        assert response.status_code == 403

    def test_project_validation_error(self, client: TestClient, auth_headers: dict, db_session) -> None:
        """プロジェクトバリデーションエラーテスト."""
        # Given: 不正なプロジェクトデータ
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        invalid_data = {
            "name": "",  # 空文字列
            "start_date": "2025-12-31",
            "end_date": "2025-07-01",  # 開始日より前
            "organization_id": organization.id
        }
        
        # When: 不正データでプロジェクト作成
        response = client.post(
            "/api/v1/projects",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Then: 400 Bad Requestが返される
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_project_not_found(self, client: TestClient, auth_headers: dict) -> None:
        """存在しないプロジェクトアクセステスト."""
        # When: 存在しないプロジェクトにアクセス
        response = client.get(
            "/api/v1/projects/999",
            headers=auth_headers
        )
        
        # Then: 404 Not Foundが返される
        assert response.status_code == 404

    def test_project_search_filters(self, client: TestClient, auth_headers: dict, db_session) -> None:
        """プロジェクト検索フィルタテスト."""
        # Given: 複数のプロジェクト
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        projects = [
            create_test_project(
                name="プロジェクトA",
                status="planning",
                organization_id=organization.id,
                created_by=user.id
            ),
            create_test_project(
                name="プロジェクトB",
                status="in_progress",
                organization_id=organization.id,
                created_by=user.id
            ),
            create_test_project(
                name="プロジェクトC",
                status="completed",
                organization_id=organization.id,
                created_by=user.id
            )
        ]
        db_session.add_all(projects)
        db_session.commit()
        
        # When: ステータスでフィルタ
        response = client.get(
            "/api/v1/projects?status=in_progress",
            headers=auth_headers
        )
        
        # Then: 該当するプロジェクトのみ返される
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "プロジェクトB"
        assert data["items"][0]["status"] == "in_progress"


def create_auth_token(user) -> str:
    """認証トークンを作成するヘルパー関数."""
    # 実際の実装では、JWT生成ロジックを使用
    return f"test_token_{user.id}"