"""
Multi-tenant security tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied
from app.services.department import DepartmentService
from app.services.organization import OrganizationService
from tests.factories import (
    create_test_department,
    create_test_organization,
    create_test_role,
    create_test_user,
    create_test_user_role,
)


class TestMultiTenantSecurity:
    """Test cases for multi-tenant data isolation."""

    def test_organization_data_isolation(self, db_session: Session) -> None:
        """TEST-MT-001: 異なる組織のデータが分離されることを確認."""
        # Given: 2つの組織とユーザー
        org1 = create_test_organization(code="ORG1", name="組織1")
        org2 = create_test_organization(code="ORG2", name="組織2")

        # 各組織にユーザーを作成
        user1 = create_test_user(email="user1@org1.com")
        user2 = create_test_user(email="user2@org2.com")

        role = create_test_role(code="ORG_USER")

        # ユーザーを組織に所属させる
        create_test_user_role(user=user1, role=role, organization=org1)
        create_test_user_role(user=user2, role=role, organization=org2)

        # 各組織に部門作成
        dept1 = create_test_department(
            organization=org1, code="DEPT1", name="組織1の部門"
        )
        dept2 = create_test_department(
            organization=org2, code="DEPT2", name="組織2の部門"
        )
        db_session.commit()

        # When: 各ユーザーで部門取得
        dept_service = DepartmentService()
        depts_user1 = dept_service.get_departments(user=user1, db=db_session)
        depts_user2 = dept_service.get_departments(user=user2, db=db_session)

        # Then: 自組織のデータのみ
        assert len(depts_user1.items) == 1
        assert depts_user1.items[0].id == dept1.id
        assert depts_user1.items[0].name == "組織1の部門"

        assert len(depts_user2.items) == 1
        assert depts_user2.items[0].id == dept2.id
        assert depts_user2.items[0].name == "組織2の部門"

    def test_cross_organization_permission_denied(self, db_session: Session) -> None:
        """TEST-MT-002: 他組織のリソースにアクセスできないことを確認."""
        # Given: 組織1の管理者
        org1 = create_test_organization(code="ORG1")
        org2 = create_test_organization(code="ORG2")

        admin1 = create_test_user(email="admin@org1.com")
        admin_role = create_test_role(code="ORG_ADMIN", permissions=["org:*", "dept:*"])
        create_test_user_role(user=admin1, role=admin_role, organization=org1)
        db_session.commit()

        # When: 組織2のデータ更新試行
        org_service = OrganizationService()

        with pytest.raises(PermissionDenied):
            org_service.update_organization(
                org_id=org2.id, data={"name": "不正な更新"}, user=admin1, db=db_session
            )

    def test_department_access_isolation(self, db_session: Session) -> None:
        """部門レベルでのアクセス制御が機能することを確認."""
        # Given: 組織内の2つの部門
        org = create_test_organization()
        dept1 = create_test_department(organization=org, code="SALES", name="営業部")
        dept2 = create_test_department(organization=org, code="HR", name="人事部")

        # 部門管理者を作成
        dept_manager = create_test_user(email="manager@sales.com")
        manager_role = create_test_role(code="DEPT_MANAGER", permissions=["dept:*"])

        # 営業部のみの管理者として設定
        create_test_user_role(
            user=dept_manager, role=manager_role, organization=org, department=dept1
        )
        db_session.commit()

        # When/Then: 営業部は更新可能
        dept_service = DepartmentService()
        updated = dept_service.update_department(
            dept_id=dept1.id,
            data={"name": "営業部更新"},
            user=dept_manager,
            db=db_session,
        )
        assert updated.name == "営業部更新"

        # When/Then: 人事部は更新不可
        with pytest.raises(PermissionDenied):
            dept_service.update_department(
                dept_id=dept2.id,
                data={"name": "人事部更新"},
                user=dept_manager,
                db=db_session,
            )

    def test_sql_injection_prevention(self, db_session: Session) -> None:
        """SQLインジェクションが防止されることを確認."""
        # Given: システム管理者
        admin = create_test_user(is_superuser=True)
        db_session.commit()

        # When: 悪意のある検索文字列
        org_service = OrganizationService()
        result = org_service.get_organizations(
            user=admin, db=db_session, search="'; DROP TABLE organizations; --"
        )

        # Then: 正常に処理される（エラーなし）
        assert result is not None

        # テーブルが削除されていない
        from app.models.organization import Organization

        assert db_session.query(Organization).count() >= 0

    def test_data_leak_prevention(self, db_session: Session) -> None:
        """データ漏洩が防止されることを確認."""
        # Given: 機密情報を含む組織
        org1 = create_test_organization(
            code="SECRET", name="機密組織", email="secret@example.com"
        )
        org2 = create_test_organization(code="PUBLIC", name="公開組織")

        # ユーザーは組織2のみアクセス可能
        user = create_test_user()
        role = create_test_role()
        create_test_user_role(user=user, role=role, organization=org2)
        db_session.commit()

        # When: 全組織取得試行
        org_service = OrganizationService()
        result = org_service.get_organizations(user=user, db=db_session)

        # Then: 機密組織は含まれない
        org_codes = [o.code for o in result.items]
        assert "SECRET" not in org_codes
        assert "PUBLIC" in org_codes

    def test_role_hierarchy_isolation(self, db_session: Session) -> None:
        """ロール階層でのアクセス制御が機能することを確認."""
        # Given: 組織と部門階層
        org = create_test_organization()
        parent_dept = create_test_department(
            organization=org, code="PARENT", name="親部門", level=1
        )
        child_dept = create_test_department(
            organization=org, parent=parent_dept, code="CHILD", name="子部門", level=2
        )

        # 親部門の管理者
        parent_manager = create_test_user()
        manager_role = create_test_role(
            code="DEPT_MANAGER", permissions=["dept:*", "dept.children:*"]
        )
        create_test_user_role(
            user=parent_manager,
            role=manager_role,
            organization=org,
            department=parent_dept,
        )
        db_session.commit()

        # When: 子部門へのアクセス
        dept_service = DepartmentService()

        # Then: 親部門管理者は子部門も管理可能
        child_data = dept_service.get_department(
            dept_id=child_dept.id, user=parent_manager, db=db_session
        )
        assert child_data.id == child_dept.id

    def test_audit_log_isolation(self, db_session: Session) -> None:
        """監査ログも組織ごとに分離されることを確認."""
        # Given: 2つの組織での操作
        org1 = create_test_organization(code="ORG1")
        org2 = create_test_organization(code="ORG2")

        admin1 = create_test_user(email="admin1@example.com")
        admin2 = create_test_user(email="admin2@example.com")

        role = create_test_role(code="ORG_ADMIN", permissions=["org:*"])
        create_test_user_role(user=admin1, role=role, organization=org1)
        create_test_user_role(user=admin2, role=role, organization=org2)
        db_session.commit()

        # 各組織で部門作成（監査ログ生成）
        dept_service = DepartmentService()
        dept1 = dept_service.create_department(
            data={"code": "DEPT1", "name": "部門1"},
            organization_id=org1.id,
            user=admin1,
            db=db_session,
        )
        dept2 = dept_service.create_department(
            data={"code": "DEPT2", "name": "部門2"},
            organization_id=org2.id,
            user=admin2,
            db=db_session,
        )

        # When: 監査ログ取得
        from app.services.audit import AuditService

        audit_service = AuditService()

        logs1 = audit_service.get_audit_logs(
            user=admin1, db=db_session, organization_id=org1.id
        )
        logs2 = audit_service.get_audit_logs(
            user=admin2, db=db_session, organization_id=org2.id
        )

        # Then: 自組織のログのみ
        assert all(log.organization_id == org1.id for log in logs1.items)
        assert all(log.organization_id == org2.id for log in logs2.items)
