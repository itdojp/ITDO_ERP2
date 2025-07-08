"""
User service unit tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, PermissionDeniedError
from app.schemas.user import UserUpdate
from app.schemas.user_extended import UserCreateExtended, UserSearchParams
from app.services.user import UserService
from tests.factories import (
    create_test_department,
    create_test_organization,
    create_test_role,
    create_test_user,
    create_test_user_role,
)


class TestUserService:
    """Test cases for UserService."""

    @pytest.fixture
    def service(self, db_session: Session) -> UserService:
        """Create service instance."""
        return UserService(db_session)

    def test_create_user_system_admin(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-001: システム管理者によるユーザー作成をテスト."""
        # Given: システム管理者と組織
        admin = create_test_user(db_session, is_superuser=True)
        org = create_test_organization(
            db_session,
        )
        role = create_test_role(db_session, code="USER")
        db_session.add_all([admin, org, role])
        db_session.commit()

        # When: ユーザー作成
        user_data = UserCreateExtended(
            email="newuser@example.com",
            full_name="新規ユーザー",
            phone="090-1234-5678",
            password="SecurePass123!",
            organization_id=org.id,
            role_ids=[role.id],
        )
        user = service.create_user(data=user_data, creator=admin, db=db_session)

        # Then: 正常に作成される
        assert user.email == "newuser@example.com"
        assert user.phone == "090-1234-5678"
        assert user.created_by == admin.id
        assert len(user.user_roles) == 1
        assert user.user_roles[0].organization_id == org.id

    def test_org_admin_create_user_in_org(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-002: 組織管理者による自組織ユーザー作成をテスト."""
        # Given: 組織管理者
        org = create_test_organization(
            db_session,
        )
        admin = create_test_user(
            db_session,
        )
        admin_role = create_test_role(db_session, code="ORG_ADMIN")
        user_role = create_test_role(db_session, code="USER")
        create_test_user_role(db_session, user=admin, role=admin_role, organization=org)
        db_session.add_all([org, admin, admin_role, user_role])
        db_session.commit()

        # When: 自組織のユーザー作成
        user_data = UserCreateExtended(
            email="orguser@example.com",
            full_name="組織ユーザー",
            password="OrgPass123!",
            organization_id=org.id,
            role_ids=[user_role.id],
        )
        user = service.create_user(data=user_data, creator=admin, db=db_session)

        # Then: 正常に作成される
        assert user.email == "orguser@example.com"
        assert user.get_organizations()[0].id == org.id

    def test_org_admin_cannot_create_cross_tenant(
        self, service, db_session: Session
    ) -> None:
        """TEST-USER-SERVICE-003: 組織管理者が他組織ユーザーを作成できない
        ことをテスト."""
        # Given: 組織1の管理者と組織2
        org1 = create_test_organization(db_session, code="ORG1")
        org2 = create_test_organization(db_session, code="ORG2")
        admin = create_test_user(
            db_session,
        )
        admin_role = create_test_role(db_session, code="ORG_ADMIN")
        create_test_user_role(
            db_session, user=admin, role=admin_role, organization=org1
        )
        db_session.commit()

        # When/Then: 組織2のユーザー作成で権限エラー
        with pytest.raises(PermissionDeniedError, match="権限がありません"):
            service.create_user(
                data=UserCreateExtended(
                    email="crossorg@example.com",
                    full_name="他組織ユーザー",
                    password="CrossOrg123!",
                    organization_id=org2.id,
                ),
                creator=admin,
                db=db_session,
            )

    def test_search_users_multi_tenant_isolation(
        self, service, db_session: Session
    ) -> None:
        """TEST-USER-SERVICE-004: マルチテナント環境でのユーザー検索分離をテスト."""
        # Given: 2つの組織とユーザー
        org1 = create_test_organization(db_session, code="ORG1")
        org2 = create_test_organization(db_session, code="ORG2")
        role = create_test_role(db_session, code="USER")

        # 各組織にユーザー作成
        user1 = create_test_user(db_session, email="user1@org1.com")
        user2 = create_test_user(db_session, email="user2@org2.com")
        create_test_user_role(db_session, user=user1, role=role, organization=org1)
        create_test_user_role(db_session, user=user2, role=role, organization=org2)

        # 組織1の管理者
        admin1 = create_test_user(db_session, email="admin@org1.com")
        admin_role = create_test_role(db_session, code="ORG_ADMIN")
        create_test_user_role(
            db_session, user=admin1, role=admin_role, organization=org1
        )
        db_session.commit()

        # When: 組織1管理者が検索
        search_params = UserSearchParams(search="user")
        result = service.search_users(
            params=search_params, searcher=admin1, db=db_session
        )

        # Then: 自組織ユーザーのみ表示
        user_emails = [u.email for u in result.items]
        assert "user1@org1.com" in user_emails
        assert "user2@org2.com" not in user_emails

    def test_update_user_self(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-005: ユーザーが自分の情報を更新できることをテスト."""
        # Given: ユーザー
        user = create_test_user(db_session, full_name="旧名前", phone="090-0000-0000")
        db_session.add(user)
        db_session.commit()

        # When: 自分の情報更新
        update_data = UserUpdate(full_name="新名前", phone="090-1111-1111")
        updated = service.update_user(
            user_id=user.id, data=update_data, updater=user, db=db_session
        )

        # Then: 正常に更新される
        assert updated.full_name == "新名前"
        assert updated.phone == "090-1111-1111"

    def test_update_user_permission_denied(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-006: 権限のないユーザー更新が拒否されることをテスト."""
        # Given: 2人のユーザー（関係なし）
        user1 = create_test_user(db_session, email="user1@example.com")
        user2 = create_test_user(db_session, email="user2@example.com")
        db_session.add_all([user1, user2])
        db_session.commit()

        # When/Then: user1がuser2を更新しようとして失敗
        with pytest.raises(PermissionDeniedError):
            service.update_user(
                user_id=user2.id,
                data=UserUpdate(full_name="不正な更新"),
                updater=user1,
                db=db_session,
            )

    def test_change_password_self(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-007: ユーザーが自分のパスワードを変更できることをテスト."""
        # Given: ユーザー
        user = create_test_user(
            db_session,
        )
        db_session.add(user)
        db_session.commit()
        old_hash = user.hashed_password

        # When: パスワード変更
        service.change_password(
            user_id=user.id,
            current_password="TestPassword123!",
            new_password="NewSecurePass123!",
            changer=user,
            db=db_session,
        )

        # Then: パスワードが変更される
        db_session.refresh(user)
        assert user.hashed_password != old_hash
        assert user.password_changed_at > user.created_at

    def test_change_password_wrong_current(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-008: 現在のパスワードが間違っている場合をテスト."""
        # Given: ユーザー
        user = create_test_user(
            db_session,
        )
        db_session.add(user)
        db_session.commit()

        # When/Then: 間違った現在のパスワードでエラー
        with pytest.raises(BusinessLogicError, match="現在のパスワード"):
            service.change_password(
                user_id=user.id,
                current_password="WrongPassword123!",
                new_password="NewPass123!",
                changer=user,
                db=db_session,
            )

    def test_admin_reset_password(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-009: 管理者によるパスワードリセットをテスト."""
        # Given: ユーザーと組織管理者
        org = create_test_organization(
            db_session,
        )
        user = create_test_user(
            db_session,
        )
        admin = create_test_user(
            db_session,
        )
        role = create_test_role(db_session, code="USER")
        admin_role = create_test_role(db_session, code="ORG_ADMIN")
        create_test_user_role(db_session, user=user, role=role, organization=org)
        create_test_user_role(db_session, user=admin, role=admin_role, organization=org)
        db_session.commit()

        # When: 管理者がパスワードリセット
        temp_password = service.reset_password(
            user_id=user.id, resetter=admin, db=db_session
        )

        # Then: 一時パスワードが生成される
        assert len(temp_password) >= 12
        assert user.password_must_change is True

    def test_assign_role_to_user(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-010: ユーザーへのロール割り当てをテスト."""
        # Given: ユーザー、組織、ロール
        org = create_test_organization(
            db_session,
        )
        user = create_test_user(
            db_session,
        )
        admin = create_test_user(
            db_session,
        )
        new_role = create_test_role(db_session, code="MANAGER")
        admin_role = create_test_role(db_session, code="ORG_ADMIN")
        create_test_user_role(db_session, user=admin, role=admin_role, organization=org)
        db_session.commit()

        # When: ロール割り当て
        user_role = service.assign_role(
            user_id=user.id,
            role_id=new_role.id,
            organization_id=org.id,
            assigner=admin,
            db=db_session,
        )

        # Then: 正しく割り当てられる
        assert user_role.user_id == user.id
        assert user_role.role_id == new_role.id
        assert user_role.assigned_by == admin.id

    def test_assign_role_with_expiry(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-011: 期限付きロール割り当てをテスト."""
        # Given: セットアップ
        org = create_test_organization(
            db_session,
        )
        user = create_test_user(
            db_session,
        )
        admin = create_test_user(db_session, is_superuser=True)
        role = create_test_role(db_session, code="TEMP_MANAGER")
        db_session.add_all([org, user, admin, role])
        db_session.commit()

        # When: 期限付きロール割り当て
        expires_at = datetime.utcnow() + timedelta(days=30)
        user_role = service.assign_role(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=expires_at,
            assigner=admin,
            db=db_session,
        )

        # Then: 期限が設定される
        assert user_role.expires_at is not None
        assert user_role.expires_at.date() == expires_at.date()

    def test_remove_role_from_user(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-012: ユーザーからのロール削除をテスト."""
        # Given: ロールを持つユーザー
        org = create_test_organization(
            db_session,
        )
        user = create_test_user(
            db_session,
        )
        admin = create_test_user(db_session, is_superuser=True)
        role = create_test_role(db_session, code="REMOVE_ME")
        create_test_user_role(db_session, user=user, role=role, organization=org)
        db_session.commit()

        # When: ロール削除
        service.remove_role(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            remover=admin,
            db=db_session,
        )

        # Then: ロールが削除される
        remaining_roles = user.get_roles_in_organization(org.id)
        assert len(remaining_roles) == 0

    def test_soft_delete_user(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-013: ユーザーの論理削除をテスト."""
        # Given: ユーザーとシステム管理者
        user = create_test_user(db_session, is_active=True)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.add_all([user, admin])
        db_session.commit()

        # When: 論理削除
        service.delete_user(user_id=user.id, deleter=admin, db=db_session)

        # Then: 非アクティブ化される
        db_session.refresh(user)
        assert user.is_active is False
        assert user.deleted_at is not None
        assert user.deleted_by == admin.id

    def test_cannot_delete_self(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-014: 自分自身を削除できないことをテスト."""
        # Given: システム管理者
        admin = create_test_user(db_session, is_superuser=True)
        db_session.add(admin)
        db_session.commit()

        # When/Then: 自分を削除しようとして失敗
        with pytest.raises(BusinessLogicError, match="自分自身"):
            service.delete_user(user_id=admin.id, deleter=admin, db=db_session)

    def test_cannot_delete_last_admin(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-015: 最後のシステム管理者を削除できないことをテスト."""
        # Given: 唯一のシステム管理者
        admin = create_test_user(db_session, is_superuser=True)
        db_session.add(admin)
        db_session.commit()

        # When/Then: 削除しようとして失敗
        other_admin = create_test_user(db_session, is_superuser=True)
        db_session.add(other_admin)
        db_session.commit()

        with pytest.raises(BusinessLogicError, match="最後のシステム管理者"):
            # 実際には他の管理者を全て削除してから実行
            service.delete_user(user_id=admin.id, deleter=other_admin, db=db_session)

    def test_get_user_permissions(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-016: ユーザーの実効権限取得をテスト."""
        # Given: 複数ロールを持つユーザー
        org = create_test_organization(
            db_session,
        )
        user = create_test_user(
            db_session,
        )
        role1 = create_test_role(db_session, code="READER", permissions=["read:*"])
        role2 = create_test_role(
            db_session, code="WRITER", permissions=["write:own", "delete:own"]
        )
        create_test_user_role(db_session, user=user, role=role1, organization=org)
        create_test_user_role(db_session, user=user, role=role2, organization=org)
        db_session.commit()

        # When: 実効権限取得
        permissions = service.get_user_permissions(
            user_id=user.id, organization_id=org.id, db=db_session
        )

        # Then: 全権限が統合される
        assert "read:*" in permissions
        assert "write:own" in permissions
        assert "delete:own" in permissions

    def test_user_activity_logging(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-017: ユーザー操作の監査ログ記録をテスト."""
        # Given: システム管理者
        admin = create_test_user(db_session, is_superuser=True)
        db_session.add(admin)
        db_session.commit()

        # Mock audit logger
        with patch("app.services.user.AuditLogger.log") as mock_log:
            # When: ユーザー作成
            user = service.create_user(
                data=UserCreateExtended(
                    email="audit@example.com",
                    full_name="監査テストユーザー",
                    password="AuditPass123!",
                    organization_id=1,
                ),
                creator=admin,
                db=db_session,
            )

            # Then: 監査ログが記録される
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["action"] == "create"
            assert call_args[1]["resource_type"] == "user"
            assert call_args[1]["resource_id"] == user.id
            assert call_args[1]["user"] == admin

    def test_search_users_with_filters(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-018: 複数フィルタでのユーザー検索をテスト."""
        # Given: 様々な条件のユーザー
        org = create_test_organization(
            db_session,
        )
        dept = create_test_department(db_session, organization=org)
        role1 = create_test_role(db_session, code="MANAGER")
        role2 = create_test_role(db_session, code="USER")

        # アクティブなマネージャー
        active_manager = create_test_user(
            db_session, email="active.manager@example.com", full_name="田中太郎"
        )
        create_test_user_role(
            db_session,
            user=active_manager,
            role=role1,
            organization=org,
            department=dept,
        )

        # 非アクティブなユーザー
        inactive_user = create_test_user(
            db_session,
            email="inactive@example.com",
            full_name="山田花子",
            is_active=False,
        )
        create_test_user_role(
            db_session, user=inactive_user, role=role2, organization=org
        )

        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: フィルタ付き検索
        params = UserSearchParams(
            search="田中",
            organization_id=org.id,
            department_id=dept.id,
            role_id=role1.id,
            is_active=True,
        )
        result = service.search_users(params=params, searcher=admin, db=db_session)

        # Then: 条件に合うユーザーのみ
        assert len(result.items) == 1
        assert result.items[0].email == "active.manager@example.com"

    def test_bulk_user_import(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-019: 一括ユーザーインポートをテスト."""
        # Given: インポートデータ
        org = create_test_organization(
            db_session,
        )
        role = create_test_role(db_session, code="USER")
        admin = create_test_user(db_session, is_superuser=True)
        db_session.add_all([org, role, admin])
        db_session.commit()

        import_data = [
            {
                "email": "import1@example.com",
                "full_name": "インポート1",
                "phone": "090-1111-1111",
            },
            {
                "email": "import2@example.com",
                "full_name": "インポート2",
                "phone": "090-2222-2222",
            },
        ]

        # When: 一括インポート
        results = service.bulk_import_users(
            data=import_data,
            organization_id=org.id,
            role_id=role.id,
            importer=admin,
            db=db_session,
        )

        # Then: 全員正常にインポート
        assert results.success_count == 2
        assert results.error_count == 0
        assert len(results.created_users) == 2

    def test_export_user_list(self, service, db_session: Session) -> None:
        """TEST-USER-SERVICE-020: ユーザーリストのエクスポートをテスト."""
        # Given: 複数のユーザー
        org = create_test_organization(
            db_session,
        )
        admin = create_test_user(db_session, is_superuser=True)
        for i in range(5):
            user = create_test_user(db_session, email=f"export{i}@example.com")
            role = create_test_role(db_session, code=f"ROLE{i}")
            create_test_user_role(db_session, user=user, role=role, organization=org)
        db_session.commit()

        # When: エクスポート
        export_data = service.export_users(
            organization_id=org.id, format="csv", exporter=admin, db=db_session
        )

        # Then: CSVデータが生成される
        assert export_data.content_type == "text/csv"
        assert len(export_data.rows) == 5
        assert "email" in export_data.headers
        assert "full_name" in export_data.headers
