"""
Extended User API integration tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

import time
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from tests.factories import (
    create_test_department,
    create_test_organization,
    create_test_role,
    create_test_user,
    create_test_user_role,
)


class TestUserManagementAPI:
    """Test cases for extended user management API endpoints."""

    def test_create_user_with_organization(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-001: 組織付きユーザー作成APIをテスト."""
        # Given: システム管理者と組織
        admin = create_test_user(is_superuser=True)
        org = create_test_organization()
        role = create_test_role(code="USER")
        db_session.add_all([admin, org, role])
        db_session.commit()
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
        admin = create_test_user(is_superuser=True)
        org = create_test_organization()
        dept = create_test_department(organization=org)
        role = create_test_role(code="DEPT_USER")
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

    def test_user_list_with_pagination(
        self, client: TestClient, db_session: Session
    ) -> None:
        """TEST-API-USER-003: ユーザー一覧のページネーションAPIをテスト."""
        # Given: 50人のユーザー
        admin = create_test_user(is_superuser=True)
        org = create_test_organization()
        role = create_test_role(code="USER")
        db_session.add_all([admin, org, role])

        for i in range(50):
            user = create_test_user(email=f"user{i:03d}@example.com")
            create_test_user_role(user=user, role=role, organization=org)
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
        admin = create_test_user(is_superuser=True)
        org1 = create_test_organization(code="ORG1")
        org2 = create_test_organization(code="ORG2")
        dept = create_test_department(organization=org1)
        role_manager = create_test_role(code="MANAGER")
        role_user = create_test_role(code="USER")

        # 検索対象ユーザー
        target_user = create_test_user(
            email="tanaka@org1.com", full_name="田中太郎", is_active=True
        )
        create_test_user_role(
            user=target_user, role=role_manager, organization=org1, department=dept
        )

        # 検索対象外ユーザー
        other_user = create_test_user(email="yamada@org2.com", full_name="山田花子")
        create_test_user_role(user=other_user, role=role_user, organization=org2)

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
        user = create_test_user()
        org = create_test_organization()
        dept = create_test_department(organization=org)
        role1 = create_test_role(code="MANAGER", name="マネージャー")
        role2 = create_test_role(code="ANALYST", name="アナリスト")
        create_test_user_role(user=user, role=role1, organization=org)
        create_test_user_role(user=user, role=role2, organization=org, department=dept)
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
        user = create_test_user(full_name="旧名前", phone="090-0000-0000")
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
        user = create_test_user()
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
        user = create_test_user()
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
        org = create_test_organization()
        user = create_test_user()
        admin = create_test_user()
        user_role = create_test_role(code="USER")
        admin_role = create_test_role(code="ORG_ADMIN", permissions=["user:*"])
        create_test_user_role(user=user, role=user_role, organization=org)
        create_test_user_role(user=admin, role=admin_role, organization=org)
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
        org = create_test_organization()
        user = create_test_user()
        admin = create_test_user()
        new_role = create_test_role(code="MANAGER", name="マネージャー")
        admin_role = create_test_role(code="ORG_ADMIN", permissions=["role:*"])
        create_test_user_role(user=admin, role=admin_role, organization=org)
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
        org = create_test_organization()
        user = create_test_user()
        admin = create_test_user(is_superuser=True)
        role = create_test_role(code="REMOVE_ME")
        create_test_user_role(user=user, role=role, organization=org)
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
        org = create_test_organization()
        user = create_test_user()
        role1 = create_test_role(
            code="READER", permissions=["read:users", "read:reports"]
        )
        role2 = create_test_role(
            code="WRITER", permissions=["write:reports", "delete:own"]
        )
        create_test_user_role(user=user, role=role1, organization=org)
        create_test_user_role(user=user, role=role2, organization=org)
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
        user = create_test_user(is_active=True)
        admin = create_test_user(is_superuser=True)
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
        admin = create_test_user(is_superuser=True)
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
        admin = create_test_user(is_superuser=True)
        org = create_test_organization()
        role = create_test_role(code="USER")
        db_session.add_all([admin, org, role])

        # バルクインサートで高速化
        users = []
        for i in range(1000):
            user = create_test_user(
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
        org1 = create_test_organization(code="ORG1")
        org2 = create_test_organization(code="ORG2")
        user1 = create_test_user(email="user1@org1.com")
        user2 = create_test_user(email="user2@org2.com")
        role = create_test_role(code="USER")
        create_test_user_role(user=user1, role=role, organization=org1)
        create_test_user_role(user=user2, role=role, organization=org2)
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
        admin = create_test_user(is_superuser=True)
        org = create_test_organization()
        role = create_test_role(code="USER")
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
        admin = create_test_user(is_superuser=True)
        org = create_test_organization()
        role = create_test_role(code="USER")
        db_session.add_all([admin, org, role])

        for i in range(5):
            user = create_test_user(
                email=f"export{i}@example.com", full_name=f"エクスポート{i}"
            )
            create_test_user_role(user=user, role=role, organization=org)
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
        user = create_test_user()
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
        admin = create_test_user(is_superuser=True)
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
