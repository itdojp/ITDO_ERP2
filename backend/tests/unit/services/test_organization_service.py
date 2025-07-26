"""
Organization service unit tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

from unittest.mock import patch

import pytest

from app.core.exceptions import PermissionDenied
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.organization import OrganizationService
from tests.factories import (
    create_test_organization,
    create_test_user,
)
from tests.factories.role import create_test_role, create_test_user_role


class TestOrganizationService:
    """Test cases for OrganizationService."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return OrganizationService()

    def test_create_organization_permission(self, service, db_session) -> None:
        """TEST-SVC-ORG-001: システム管理者のみ組織作成可能なことを確認."""
        # Given: 一般ユーザー
        user = create_test_user(db_session, is_superuser=False)
        db_session.commit()

        # When/Then: 組織作成で権限エラー
        with pytest.raises(PermissionDenied, match="システム管理者権限が必要です"):
            service.create_organization(
                data=OrganizationCreate(
                    code="TEST", name="テスト組織", email="test@example.com"
                ),
                user=user,
                db=db_session,
            )

    def test_create_organization_success(self, service, db_session) -> None:
        """システム管理者による組織作成が成功することを確認."""
        # Given: システム管理者
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: 組織作成
        org = service.create_organization(
            data=OrganizationCreate(
                code="NEWORG",
                name="新組織",
                email="new@example.com",
                fiscal_year_start=4,
            ),
            user=admin,
            db=db_session,
        )

        # Then:
        assert org.id is not None
        assert org.code == "NEWORG"
        assert org.name == "新組織"
        assert org.created_by == admin.id

    def test_organization_filtering(self, service, db_session) -> None:
        """TEST-SVC-ORG-002: ユーザーが所属する組織のみ表示されることを確認."""
        # Given: 複数組織とユーザー
        org1 = create_test_organization(db_session, code="ORG1")
        org2 = create_test_organization(db_session, code="ORG2")
        org3 = create_test_organization(db_session, code="ORG3")

        user = create_test_user(db_session)
        role = create_test_role(db_session, code="USER")

        # ユーザーをorg1とorg2に所属させる
        create_test_user_role(db_session, user=user, role=role, organization=org1)
        create_test_user_role(db_session, user=user, role=role, organization=org2)
        db_session.commit()

        # When: 組織一覧取得
        result = service.get_organizations(user=user, db=db_session)

        # Then: 所属組織のみ
        org_ids = [o.id for o in result.items]
        assert org1.id in org_ids
        assert org2.id in org_ids
        assert org3.id not in org_ids
        assert result.total == 2

    def test_system_admin_sees_all_organizations(self, service, db_session) -> None:
        """システム管理者は全組織を閲覧できることを確認."""
        # Given: 複数組織とシステム管理者
        org1 = create_test_organization(db_session, code="ORG1")
        org2 = create_test_organization(db_session, code="ORG2")
        org3 = create_test_organization(db_session, code="ORG3")

        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: 組織一覧取得
        result = service.get_organizations(user=admin, db=db_session)

        # Then: 全組織が見える
        org_ids = [o.id for o in result.items]
        assert org1.id in org_ids
        assert org2.id in org_ids
        assert org3.id in org_ids
        assert result.total == 3

    def test_update_organization_permission(self, service, db_session) -> None:
        """組織管理者のみ組織情報を更新できることを確認."""
        # Given: 組織と一般ユーザー
        org = create_test_organization(
            db_session,
        )
        user = create_test_user(db_session)
        user_role = create_test_role(db_session, code="USER")
        create_test_user_role(db_session, user=user, role=user_role, organization=org)
        db_session.commit()

        # When/Then: 更新で権限エラー
        with pytest.raises(PermissionDenied):
            service.update_organization(
                org_id=org.id,
                data=OrganizationUpdate(name="更新名"),
                user=user,
                db=db_session,
            )

    def test_update_organization_success(self, service, db_session) -> None:
        """組織管理者による組織更新が成功することを確認."""
        # Given: 組織と組織管理者
        org = create_test_organization(db_session, name="旧名称")
        admin = create_test_user(db_session)
        admin_role = create_test_role(
            db_session, code="ORG_ADMIN", permissions=["org:*"]
        )
        create_test_user_role(db_session, user=admin, role=admin_role, organization=org)
        db_session.commit()

        # When: 組織更新
        updated = service.update_organization(
            org_id=org.id,
            data=OrganizationUpdate(name="新名称", email="new@example.com"),
            user=admin,
            db=db_session,
        )

        # Then:
        assert updated.name == "新名称"
        assert updated.email == "new@example.com"
        assert updated.updated_by == admin.id

    def test_soft_delete_organization(self, service, db_session) -> None:
        """組織の論理削除が動作することを確認."""
        # Given: 組織とシステム管理者
        org = create_test_organization(db_session, is_active=True)
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: 論理削除
        service.delete_organization(org_id=org.id, user=admin, db=db_session)

        # Then: 非アクティブ化
        db_session.refresh(org)
        assert org.is_active is False

    def test_organization_search(self, service, db_session) -> None:
        """組織検索が正しく動作することを確認."""
        # Given: 複数組織
        org1 = create_test_organization(
            db_session, name="株式会社アルファ", code="ALPHA"
        )
        create_test_organization(db_session, name="ベータ商事", code="BETA")
        create_test_organization(db_session, name="ガンマ工業", code="GAMMA")

        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: 検索
        result = service.get_organizations(user=admin, db=db_session, search="アルファ")

        # Then: 該当組織のみ
        assert result.total == 1
        assert result.items[0].id == org1.id

    def test_organization_pagination(self, service, db_session) -> None:
        """組織一覧のページネーションが動作することを確認."""
        # Given: 多数の組織
        for i in range(25):
            create_test_organization(db_session, code=f"ORG{i:03d}")

        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # When: ページ指定
        page1 = service.get_organizations(user=admin, db=db_session, page=1, limit=10)
        page2 = service.get_organizations(user=admin, db=db_session, page=2, limit=10)

        # Then:
        assert len(page1.items) == 10
        assert len(page2.items) == 10
        assert page1.total == 25
        assert page1.items[0].id != page2.items[0].id

    @pytest.mark.skip(reason="AuditLogger not implemented yet")
    def test_organization_audit_log(self, service, db_session) -> None:
        """組織操作が監査ログに記録されることを確認."""
        # Given: システム管理者
        admin = create_test_user(db_session, is_superuser=True)
        db_session.commit()

        # Mock audit logger
        with patch("app.services.organization.AuditLogger.log") as mock_log:
            # When: 組織作成
            org = service.create_organization(
                data=OrganizationCreate(code="AUDIT", name="監査テスト"),
                user=admin,
                db=db_session,
            )

            # Then: 監査ログ呼び出し
            mock_log.assert_called_once_with(
                action="create",
                resource_type="organization",
                resource_id=org.id,
                user=admin,
                changes={"code": "AUDIT", "name": "監査テスト"},
            )
