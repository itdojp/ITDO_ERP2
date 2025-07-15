"""
Extended User API integration tests.

Following TDD approach - Red phase: Writing tests before implementation.

NOTE: Many tests are currently skipped because create_test_user_role is not yet
implemented.
"""

import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from tests.factories import (
    DepartmentFactory,
    OrganizationFactory,
    RoleFactory,
    UserFactory,
)


@pytest.mark.skip(
    reason="Extended user tests require create_test_user_role implementation"
)
class TestUserManagementAPI:
    """Test cases for extended user management API endpoints."""

    def test_create_user_with_organization(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-001: 組織付きユーザー作成APIをテスト."""
        # Given: システム管理者と組織
        admin = UserFactory.create_admin(db_session)
        org = OrganizationFactory.create(db_session)
        role = RoleFactory.create_with_organization(db_session, org, code="USER")
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: ユーザー作成API呼び出し
        response = client.post(
            "/api/v1/users",
            json={
                "email": "newuser@example.com",
                "full_name": "新規ユーザー",
                "phone": "090-1234-5678",
                "password": "SecurePass123!",
                "organization_id": org.id,
                "role_ids": [role.id],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 正常に作成される
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["phone"] == "090-1234-5678"
        assert "password" not in data
        assert "organizations" in data
        assert len(data["organizations"]) == 1
        assert data["organizations"][0]["id"] == org.id

    def test_create_user_with_department(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-002: 部門付きユーザー作成APIをテスト."""
        # Given: セットアップ
<<<<<<< HEAD
=======

        admin = UserFactory.create(db_session, is_superuser=True)
        org = OrganizationFactory.create(db_session)
        dept = DepartmentFactory.create(db_session, organization=org)
        role = RoleFactory.create(db_session, code="DEPT_USER")

>>>>>>> main
        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        dept = DepartmentFactory.create(organization=org)
        role = RoleFactory.create(code="DEPT_USER")
<<<<<<< HEAD
=======

>>>>>>> main
        db_session.add_all([admin, org, dept, role])
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: 部門付きユーザー作成
        response = client.post(
            "/api/v1/users",
            json={
                "email": "deptuser@example.com",
                "full_name": "部門ユーザー",
                "password": "DeptPass123!",
                "organization_id": org.id,
                "department_id": dept.id,
                "role_ids": [role.id],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 部門に所属
        assert response.status_code == 201
        data = response.json()
        assert "departments" in data
        assert len(data["departments"]) == 1
        assert data["departments"][0]["id"] == dept.id

    @pytest.mark.skip(reason="create_test_user_role not implemented yet")
    def test_user_list_with_pagination(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-003: ユーザー一覧のページネーションAPIをテスト."""
        # Given: 50人のユーザー
<<<<<<< HEAD
        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")
        db_session.add_all([admin, org, role])

        for i in range(50):
            UserFactory.create(email=f"user{i:03d}@example.com")
            # TODO: Implement create_test_user_role functionality
            # create_test_user_role(user=user, role=role, organization=org)
=======

        admin = UserFactory.create(db_session, is_superuser=True)
        org = OrganizationFactory.create(db_session)
        role = RoleFactory.create(db_session, code="USER")
        db_session.add_all([admin, org, role])

        for i in range(50):
            UserFactory.create(db_session, email=f"user{i:03d}@example.com")
            # create_test_user_role functionality is available
            # create_test_user_role can be used if needed

        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")
        db_session.add_all([admin, org, role])

        for i in range(50):
            UserFactory.create(email=f"user{i:03d}@example.com")
            # TODO: Implement create_test_user_role functionality
            # create_test_user_role(user=user, role=role, organization=org)

>>>>>>> main
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: ページ2を取得
        response = client.get(
            "/api/v1/users?page=2&limit=20",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 正しいページネーション
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 20
        assert data["page"] == 2
        assert data["limit"] == 20
        assert data["total"] == 51  # 50 + admin

    def test_user_search_filters(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-004: ユーザー検索フィルタAPIをテスト."""
        # Given: 様々な条件のユーザー
<<<<<<< HEAD
        admin = UserFactory.create(is_superuser=True)
        org1 = OrganizationFactory.create(code="ORG1")
        OrganizationFactory.create(code="ORG2")
        dept = DepartmentFactory.create(organization=org1)
        role_manager = RoleFactory.create(code="MANAGER")
        RoleFactory.create(code="USER")

        # 検索対象ユーザー
        UserFactory.create(
=======

        admin = UserFactory.create(db_session, is_superuser=True)
        org1 = OrganizationFactory.create(db_session, code="ORG1")
        OrganizationFactory.create(db_session, code="ORG2")
        dept = DepartmentFactory.create(db_session, organization=org1)
        role_manager = RoleFactory.create(db_session, code="MANAGER")
        RoleFactory.create(db_session, db_session, code="USER")

        # 検索対象ユーザー
        UserFactory.create(
            db_session, email="tanaka@org1.com", full_name="田中太郎", is_active=True

        admin = UserFactory.create(is_superuser=True)
        org1 = OrganizationFactory.create(code="ORG1")
        OrganizationFactory.create(code="ORG2")
        dept = DepartmentFactory.create(organization=org1)
        role_manager = RoleFactory.create(code="MANAGER")
        RoleFactory.create(code="USER")

        # 検索対象ユーザー
        UserFactory.create(
>>>>>>> main
            email="tanaka@org1.com", full_name="田中太郎", is_active=True

        )
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(
        #     user=target_user, role=role_manager, organization=org1, department=dept
        # )

        # 検索対象外ユーザー
<<<<<<< HEAD
        UserFactory.create(email="yamada@org2.com", full_name="山田花子")
=======

        UserFactory.create(db_session, email="yamada@org2.com", full_name="山田花子")

        UserFactory.create(email="yamada@org2.com", full_name="山田花子")

>>>>>>> main
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(user=other_user, role=role_user, organization=org2)

        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: フィルタ付き検索
        response = client.get(
            f"/api/v1/users?search=田中&organization_id={org1.id}"
            f"&department_id={dept.id}&role_id={role_manager.id}&is_active=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 条件に合うユーザーのみ
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["email"] == "tanaka@org1.com"

    def test_user_detail_with_roles(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-005: ユーザー詳細（ロール情報付き）APIをテスト."""
        # Given: 複数ロールを持つユーザー
<<<<<<< HEAD
=======

        user = UserFactory.create(db_session)
        org = OrganizationFactory.create(db_session)
        DepartmentFactory.create(db_session, db_session, organization=org)
        RoleFactory.create(db_session, db_session, code="MANAGER", name="マネージャー")
        RoleFactory.create(db_session, db_session, code="ANALYST", name="アナリスト")

>>>>>>> main
        user = UserFactory.create()
        org = OrganizationFactory.create()
        DepartmentFactory.create(organization=org)
        RoleFactory.create(code="MANAGER", name="マネージャー")
        RoleFactory.create(code="ANALYST", name="アナリスト")
<<<<<<< HEAD
=======

>>>>>>> main
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(user=user, role=role1, organization=org)
        # create_test_user_role(
        #     user=user, role=role2, organization=org, department=dept
        # )
        db_session.commit()
        user_token = create_access_token({"sub": str(user.id)})

        # When: ユーザー詳細取得
        response = client.get(
            f"/api/v1/users/{user.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: ロール情報を含む
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) == 2
        role_names = [r["role"]["name"] for r in data["roles"]]
        assert "マネージャー" in role_names
        assert "アナリスト" in role_names

    def test_update_user_profile(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-006: ユーザープロファイル更新APIをテスト."""
        # Given: ユーザー
<<<<<<< HEAD
        user = UserFactory.create(full_name="旧名前", phone="090-0000-0000")
=======

        user = UserFactory.create(db_session, full_name="旧名前", phone="090-0000-0000")

        user = UserFactory.create(full_name="旧名前", phone="090-0000-0000")

>>>>>>> main
        db_session.add(user)
        db_session.commit()
        user_token = create_access_token({"sub": str(user.id)})

        # When: プロファイル更新
        response = client.put(
            f"/api/v1/users/{user.id}",
            json={
                "full_name": "新名前",
                "phone": "090-1111-1111",
                "profile_image_url": "https://example.com/avatar.jpg",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: 正常に更新
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "新名前"
        assert data["phone"] == "090-1111-1111"
        assert data["profile_image_url"] == "https://example.com/avatar.jpg"

    def test_change_password_api(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-007: パスワード変更APIをテスト."""
        # Given: ユーザー
<<<<<<< HEAD
        user = UserFactory.create()
=======

        user = UserFactory.create(db_session)

        user = UserFactory.create()

>>>>>>> main
        db_session.add(user)
        db_session.commit()
        user_token = create_access_token({"sub": str(user.id)})

        # When: パスワード変更
        response = client.put(
            f"/api/v1/users/{user.id}/password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "NewSecurePass123!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: 成功
        assert response.status_code == 200
        assert response.json()["message"] == "パスワードが変更されました"

    def test_change_password_wrong_current(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-008: 間違った現在パスワードでの変更失敗をテスト."""
        # Given: ユーザー
<<<<<<< HEAD
        user = UserFactory.create()
=======

        user = UserFactory.create(db_session)

        user = UserFactory.create()

>>>>>>> main
        db_session.add(user)
        db_session.commit()
        user_token = create_access_token({"sub": str(user.id)})

        # When: 間違った現在パスワード
        response = client.put(
            f"/api/v1/users/{user.id}/password",
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewPass123!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: エラー
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_PASSWORD"

    def test_admin_reset_password(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-009: 管理者によるパスワードリセットAPIをテスト."""
        # Given: ユーザーと管理者
<<<<<<< HEAD
=======

        OrganizationFactory.create(db_session)
        user = UserFactory.create(db_session)
        admin = UserFactory.create()
        RoleFactory.create(db_session, code="USER")
        RoleFactory.create(db_session, code="ORG_ADMIN", permissions=["user:*"])

>>>>>>> main
        OrganizationFactory.create()
        user = UserFactory.create()
        admin = UserFactory.create()
        RoleFactory.create(code="USER")
        RoleFactory.create(code="ORG_ADMIN", permissions=["user:*"])
<<<<<<< HEAD
=======

>>>>>>> main
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(user=user, role=user_role, organization=org)
        # create_test_user_role(user=admin, role=admin_role, organization=org)
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: パスワードリセット
        response = client.post(
            f"/api/v1/users/{user.id}/password/reset",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 一時パスワード生成
        assert response.status_code == 200
        data = response.json()
        assert "temporary_password" in data
        assert len(data["temporary_password"]) >= 12

    def test_assign_role_to_user(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-010: ユーザーへのロール割り当てAPIをテスト."""
        # Given: セットアップ
        org = OrganizationFactory.create()
<<<<<<< HEAD
=======

        user = UserFactory.create(db_session)
        admin = UserFactory.create()
        new_role = RoleFactory.create(code="MANAGER", name="マネージャー")
        RoleFactory.create(db_session, code="ORG_ADMIN", permissions=["role:*"])

>>>>>>> main
        user = UserFactory.create()
        admin = UserFactory.create()
        new_role = RoleFactory.create(code="MANAGER", name="マネージャー")
        RoleFactory.create(code="ORG_ADMIN", permissions=["role:*"])
<<<<<<< HEAD
=======

>>>>>>> main
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(user=admin, role=admin_role, organization=org)
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: ロール割り当て
        response = client.post(
            f"/api/v1/users/{user.id}/roles",
            json={
                "role_id": new_role.id,
                "organization_id": org.id,
                "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 成功
        assert response.status_code == 201
        data = response.json()
        assert data["role"]["name"] == "マネージャー"
        assert data["expires_at"] is not None

    def test_remove_role_from_user(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-011: ユーザーからのロール削除APIをテスト."""
        # Given: ロールを持つユーザー
        org = OrganizationFactory.create()
<<<<<<< HEAD
        user = UserFactory.create()
=======

        user = UserFactory.create(db_session)

        user = UserFactory.create()

>>>>>>> main
        admin = UserFactory.create(is_superuser=True)
        role = RoleFactory.create(code="REMOVE_ME")
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(user=user, role=role, organization=org)
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: ロール削除
        response = client.delete(
            f"/api/v1/users/{user.id}/roles/{role.id}?organization_id={org.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 成功
        assert response.status_code == 204

    def test_get_user_permissions(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-012: ユーザー権限一覧取得APIをテスト."""
        # Given: 複数ロールのユーザー
        org = OrganizationFactory.create()
<<<<<<< HEAD
        user = UserFactory.create()
        RoleFactory.create(code="READER", permissions=["read:users", "read:reports"])
        RoleFactory.create(code="WRITER", permissions=["write:reports", "delete:own"])
=======

        user = UserFactory.create(db_session)
        RoleFactory.create(
            db_session, code="READER", permissions=["read:users", "read:reports"]
        )
        RoleFactory.create(
            db_session, code="WRITER", permissions=["write:reports", "delete:own"]
        )

        user = UserFactory.create()
        RoleFactory.create(code="READER", permissions=["read:users", "read:reports"])
        RoleFactory.create(code="WRITER", permissions=["write:reports", "delete:own"])

>>>>>>> main
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(user=user, role=role1, organization=org)
        # create_test_user_role(user=user, role=role2, organization=org)
        db_session.commit()
        user_token = create_access_token({"sub": str(user.id)})

        # When: 権限一覧取得
        response = client.get(
            f"/api/v1/users/{user.id}/permissions?organization_id={org.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: 統合された権限
        assert response.status_code == 200
        permissions = response.json()["permissions"]
        assert "read:users" in permissions
        assert "read:reports" in permissions
        assert "write:reports" in permissions
        assert "delete:own" in permissions

    def test_soft_delete_user(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-013: ユーザー論理削除APIをテスト."""
        # Given: ユーザーとシステム管理者
        user = UserFactory.create(is_active=True)
        admin = UserFactory.create(is_superuser=True)
        db_session.add_all([user, admin])
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: 論理削除
        response = client.delete(
            f"/api/v1/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 成功
        assert response.status_code == 204
        # 確認
        db_session.refresh(user)
        assert user.is_active is False

    def test_cannot_delete_self(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-014: 自分自身を削除できないことをテスト."""
        # Given: システム管理者
        admin = UserFactory.create(is_superuser=True)
        db_session.add(admin)
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: 自分を削除
        response = client.delete(
            f"/api/v1/users/{admin.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: エラー
        assert response.status_code == 400
        assert response.json()["code"] == "CANNOT_DELETE_SELF"

    def test_user_list_response_time(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-015: ユーザー一覧の応答時間をテスト."""
        # Given: 1000人のユーザー
<<<<<<< HEAD
        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")
=======

        admin = UserFactory.create(db_session, is_superuser=True)
        org = OrganizationFactory.create(db_session)
        role = RoleFactory.create(db_session, code="USER")

        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")

>>>>>>> main
        db_session.add_all([admin, org, role])

        # バルクインサートで高速化
        users = []
        for i in range(1000):
            user = UserFactory.create(
                email=f"perf{i:04d}@example.com", full_name=f"パフォーマンス{i}"
            )
            users.append(user)
        db_session.add_all(users)
        db_session.commit()

        admin_token = create_access_token({"sub": str(admin.id)})

        # When: 一覧取得
        start_time = time.time()
        response = client.get(
            "/api/v1/users?limit=20",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response_time = (time.time() - start_time) * 1000

        # Then: 200ms以内
        assert response.status_code == 200
        assert response_time < 200

    def test_cross_tenant_access_denied(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-016: テナント間アクセス拒否をテスト."""
        # Given: 異なる組織のユーザー
        OrganizationFactory.create(code="ORG1")
        OrganizationFactory.create(code="ORG2")
        user1 = UserFactory.create(email="user1@org1.com")
        user2 = UserFactory.create(email="user2@org2.com")
<<<<<<< HEAD
        RoleFactory.create(code="USER")
=======

        RoleFactory.create(db_session, code="USER")

        RoleFactory.create(code="USER")

>>>>>>> main
        # TODO: Implement create_test_user_role functionality
        # create_test_user_role(user=user1, role=role, organization=org1)
        # create_test_user_role(user=user2, role=role, organization=org2)
        db_session.commit()

        user1_token = create_access_token({"sub": str(user1.id)})

        # When: 他組織ユーザーにアクセス
        response = client.get(
            f"/api/v1/users/{user2.id}",
            headers={"Authorization": f"Bearer {user1_token}"},
        )

        # Then: アクセス拒否
        assert response.status_code == 403
        assert response.json()["code"] == "ACCESS_DENIED"

    def test_bulk_user_import(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-017: 一括ユーザーインポートAPIをテスト."""
        # Given: セットアップ
<<<<<<< HEAD
        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")
=======

        admin = UserFactory.create(db_session, is_superuser=True)
        org = OrganizationFactory.create(db_session)
        role = RoleFactory.create(db_session, code="USER")

        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")

>>>>>>> main
        db_session.add_all([admin, org, role])
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: 一括インポート
        response = client.post(
            "/api/v1/users/import",
            json={
                "organization_id": org.id,
                "role_id": role.id,
                "users": [
                    {
                        "email": "import1@example.com",
                        "full_name": "インポート太郎",
                        "phone": "090-1111-1111",
                    },
                    {
                        "email": "import2@example.com",
                        "full_name": "インポート花子",
                        "phone": "090-2222-2222",
                    },
                ],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: 成功
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 2
        assert data["error_count"] == 0
        assert len(data["created_users"]) == 2

    def test_export_users_csv(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-018: ユーザーリストCSVエクスポートAPIをテスト."""
        # Given: 複数ユーザー
<<<<<<< HEAD
        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")
=======

        admin = UserFactory.create(db_session, is_superuser=True)
        org = OrganizationFactory.create(db_session)
        role = RoleFactory.create(db_session, code="USER")

        admin = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        role = RoleFactory.create(code="USER")

>>>>>>> main
        db_session.add_all([admin, org, role])

        for i in range(5):
            UserFactory.create(
                email=f"export{i}@example.com", full_name=f"エクスポート{i}"
            )
<<<<<<< HEAD
            # TODO: Implement create_test_user_role functionality
            # create_test_user_role(user=user, role=role, organization=org)
=======

            # create_test_user_role functionality is available
            # create_test_user_role can be used if needed

            # TODO: Implement create_test_user_role functionality
            # create_test_user_role(user=user, role=role, organization=org)

>>>>>>> main
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: CSVエクスポート
        response = client.get(
            f"/api/v1/users/export?organization_id={org.id}&format=csv",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Then: CSVレスポンス
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

    def test_user_activity_log(self, client: TestClient, db_session: Session) -> None:
        """TEST-API-USER-019: ユーザー活動ログ取得APIをテスト."""
        # Given: ユーザー
<<<<<<< HEAD
        user = UserFactory.create()
=======

        user = UserFactory.create(db_session)

        user = UserFactory.create()

>>>>>>> main
        db_session.add(user)
        db_session.commit()
        user_token = create_access_token({"sub": str(user.id)})

        # 何か活動（プロファイル更新）
        client.put(
            f"/api/v1/users/{user.id}",
            json={"full_name": "更新後の名前"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # When: 活動ログ取得
        response = client.get(
            f"/api/v1/users/{user.id}/activities",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # Then: ログが返される
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert data["items"][0]["action"] == "profile_update"

    def test_password_validation_errors(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-020: パスワードバリデーションエラーをテスト."""
        # Given: 管理者
        admin = UserFactory.create(is_superuser=True)
        db_session.add(admin)
        db_session.commit()
        admin_token = create_access_token({"sub": str(admin.id)})

        # When: 弱いパスワードでユーザー作成
        weak_passwords = [
            "short",  # 短すぎる
            "alllowercase123",  # 大文字なし
            "NoNumbers!",  # 数字なし
        ]

        for weak_pass in weak_passwords:
            response = client.post(
                "/api/v1/users",
                json={
                    "email": f"weak{weak_pass}@example.com",
                    "full_name": "弱いパスワード",
                    "password": weak_pass,
                    "organization_id": 1,
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            # Then: バリデーションエラー
            assert response.status_code == 422
            errors = response.json()["detail"]
            assert any(e["loc"] == ["body", "password"] for e in errors)
