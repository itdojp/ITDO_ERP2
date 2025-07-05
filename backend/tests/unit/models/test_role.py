"""
Role and UserRole model unit tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.department import Department
from app.models.organization import Organization
from app.models.role import Role, UserRole
from app.models.user import User
from tests.factories import (
    DepartmentFactory,
    OrganizationFactory,
    RoleFactory,
    UserFactory,
    UserRoleFactory,
)


class TestRoleModel:
    """Test cases for Role model."""

    def test_system_roles_exist(self, db_session) -> None:
        """TEST-ROLE-001: システムロールが存在することを確認."""
        # Given: システムロールの初期化
        Role.init_system_roles(db_session)

        # When: システムロール取得
        roles = db_session.query(Role).filter_by(is_system=True).all()

        # Then:
        role_codes = [r.code for r in roles]
        assert "SYSTEM_ADMIN" in role_codes
        assert "ORG_ADMIN" in role_codes
        assert "DEPT_MANAGER" in role_codes
        assert "USER" in role_codes

        # システム管理者ロールの権限確認
        admin_role = next(r for r in roles if r.code == "SYSTEM_ADMIN")
        assert "*" in admin_role.permissions

    def test_create_custom_role(self, db_session) -> None:
        """カスタムロールが作成できることを確認."""
        # When: カスタムロール作成
        role = Role(
            code="CUSTOM_VIEWER",
            name="カスタム閲覧者",
            description="特定機能の閲覧のみ",
            permissions=["read:projects", "read:tasks"],
            is_system=False,
        )
        db_session.add(role)
        db_session.commit()

        # Then:
        assert role.id is not None
        assert role.code == "CUSTOM_VIEWER"
        assert len(role.permissions) == 2
        assert role.is_system is False
        assert role.is_active is True

    def test_duplicate_role_code(self, db_session) -> None:
        """重複するロールコードが拒否されることを確認."""
        # Given: 既存ロール
        role1 = RoleFactory(code="VIEWER")
        db_session.commit()

        # When/Then: 同じコードで作成
        role2 = Role(code="VIEWER", name="別の閲覧者")
        db_session.add(role2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_role_permission_check(self, db_session) -> None:
        """ロールの権限チェックが正しく動作することを確認."""
        # Given: 権限を持つロール
        role = Role(
            code="EDITOR",
            name="編集者",
            permissions=["read:*", "write:projects", "write:tasks"],
        )

        # When/Then: 権限チェック
        assert role.has_permission("read:projects")
        assert role.has_permission("read:anything")  # ワイルドカード
        assert role.has_permission("write:projects")
        assert not role.has_permission("delete:projects")
        assert not role.has_permission("write:users")

    def test_system_role_cannot_be_deleted(self, db_session) -> None:
        """システムロールが削除できないことを確認."""
        # Given: システムロール
        Role.init_system_roles(db_session)
        admin_role = db_session.query(Role).filter_by(code="SYSTEM_ADMIN").first()

        # When/Then: 削除試行
        with pytest.raises(ValueError, match="システムロールは削除できません"):
            admin_role.delete()

    def test_role_soft_delete(self, db_session) -> None:
        """カスタムロールの論理削除が動作することを確認."""
        # Given: カスタムロール
        role = RoleFactory(is_system=False, is_active=True)
        db_session.commit()

        # When: 論理削除
        role.is_active = False
        db_session.commit()

        # Then:
        assert role.is_active is False
        # データは残っている
        assert db_session.query(Role).filter_by(id=role.id).first() is not None


class TestUserRoleModel:
    """Test cases for UserRole model."""

    def test_assign_role_to_user(self, db_session) -> None:
        """TEST-ROLE-002: ユーザーにロールを付与できることを確認."""
        # Given: ユーザーと組織
        user = UserFactory()
        org = OrganizationFactory()
        role = RoleFactory(code="ORG_ADMIN")
        db_session.commit()

        # When: ロール付与
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            assigned_by=user.id,
        )
        db_session.add(user_role)
        db_session.commit()

        # Then:
        assert user_role.id is not None
        assert user_role.user_id == user.id
        assert user_role.role_id == role.id
        assert user_role.organization_id == org.id
        assert isinstance(user_role.assigned_at, datetime)

    def test_prevent_duplicate_role_assignment(self, db_session) -> None:
        """TEST-ROLE-003: 同じロールの重複付与が防止されることを確認."""
        # Given: ロール付与済み
        user = UserFactory()
        org = OrganizationFactory()
        role = RoleFactory()
        user_role1 = UserRoleFactory(user=user, role=role, organization=org)
        db_session.commit()

        # When/Then: 同じロール付与で例外
        user_role2 = UserRole(user_id=user.id, role_id=role.id, organization_id=org.id)
        db_session.add(user_role2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_department_level_role_assignment(self, db_session) -> None:
        """部門レベルでのロール付与が動作することを確認."""
        # Given: ユーザー、組織、部門
        user = UserFactory()
        org = OrganizationFactory()
        dept = DepartmentFactory(organization=org)
        role = RoleFactory(code="DEPT_MANAGER")
        db_session.commit()

        # When: 部門レベルでロール付与
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            department_id=dept.id,
        )
        db_session.add(user_role)
        db_session.commit()

        # Then:
        assert user_role.department_id == dept.id
        assert user_role.department.id == dept.id

    def test_role_expiration(self, db_session) -> None:
        """ロールの有効期限が機能することを確認."""
        # Given: 期限付きロール
        user = UserFactory()
        org = OrganizationFactory()
        role = RoleFactory()

        # 期限切れロール
        expired_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )

        # 有効なロール
        valid_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=org.id,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )

        # Then:
        assert expired_role.is_expired() is True
        assert valid_role.is_expired() is False

    def test_user_role_cascade_delete(self, db_session) -> None:
        """ユーザー削除時にロール付与も削除されることを確認."""
        # Given: ユーザーとロール付与
        user = UserFactory()
        user_role = UserRoleFactory(user=user)
        db_session.commit()
        user_role_id = user_role.id

        # When: ユーザー削除
        db_session.delete(user)
        db_session.commit()

        # Then: ロール付与も削除される
        assert db_session.query(UserRole).filter_by(id=user_role_id).first() is None

    def test_get_user_permissions(self, db_session) -> None:
        """ユーザーの権限が正しく取得できることを確認."""
        # Given: 複数ロールを持つユーザー
        user = UserFactory()
        org = OrganizationFactory()

        # 組織管理者ロール
        org_admin_role = RoleFactory(code="ORG_ADMIN", permissions=["org:*", "read:*"])
        # プロジェクト管理者ロール
        proj_admin_role = RoleFactory(
            code="PROJ_ADMIN", permissions=["project:*", "task:*"]
        )

        UserRoleFactory(user=user, role=org_admin_role, organization=org)
        UserRoleFactory(user=user, role=proj_admin_role, organization=org)
        db_session.commit()

        # When: ユーザーの権限取得
        permissions = user.get_permissions(organization_id=org.id)

        # Then: 両方のロールの権限を持つ
        assert "org:write" in permissions  # org:* から展開
        assert "read:users" in permissions  # read:* から展開
        assert "project:create" in permissions
        assert "task:delete" in permissions

    def test_user_has_role_in_organization(self, db_session) -> None:
        """ユーザーが特定組織でロールを持つか確認できることを確認."""
        # Given: 2つの組織でロールを持つユーザー
        user = UserFactory()
        org1 = OrganizationFactory(code="ORG1")
        org2 = OrganizationFactory(code="ORG2")
        admin_role = RoleFactory(code="ORG_ADMIN")

        UserRoleFactory(user=user, role=admin_role, organization=org1)
        db_session.commit()

        # Then:
        assert user.has_role("ORG_ADMIN", organization_id=org1.id) is True
        assert user.has_role("ORG_ADMIN", organization_id=org2.id) is False
