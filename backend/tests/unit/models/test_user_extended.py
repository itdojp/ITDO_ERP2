"""
Extended User model unit tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.password_history import PasswordHistory
from app.models.user import User
from tests.factories import create_test_user


class TestUserExtendedModel:
    """Test cases for extended User model functionality."""

    def test_user_with_phone_number(self, db_session: Session) -> None:
        """TEST-USER-MODEL-001: 電話番号を含むユーザー作成をテスト."""
        # Given: 電話番号付きユーザーデータ
        user_data = {
            "email": "phone@example.com",
            "password": "SecurePass123!",
            "full_name": "電話番号テストユーザー",
            "phone": "090-1234-5678",
        }

        # When: ユーザー作成
        user = User.create(
            db_session,
            email=user_data["email"],
            password=user_data["password"],
            full_name=user_data["full_name"],
            phone=user_data["phone"],
        )
        db_session.commit()

        # Then: 正しく作成される
        assert user.phone == "090-1234-5678"
        assert user.password_changed_at is not None
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_password_history_tracking(self, db_session: Session) -> None:
        """TEST-USER-MODEL-002: パスワード履歴の記録をテスト."""
        # Given: 既存ユーザー
        user = create_test_user(db_session, email="history@example.com")
        db_session.commit()
        old_hash = user.hashed_password

        # When: パスワード変更
        user.change_password(db_session, "TestPassword123!", "NewPassword123!")
        db_session.commit()

        # Then: 履歴が記録される
        history = (
            db_session.query(PasswordHistory)
            .filter(PasswordHistory.user_id == user.id)
            .all()
        )
        assert len(history) == 1
        assert history[0].password_hash == old_hash

    def test_password_reuse_prevention(self, db_session: Session) -> None:
        """TEST-USER-MODEL-003: 直近3回のパスワード再利用防止をテスト."""
        # Given: ユーザーとパスワード履歴
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # パスワードを3回変更
        passwords = ["Pass1234!", "Pass5678!", "Pass9012!"]
        for i, new_pass in enumerate(passwords):
            current_pass = "TestPassword123!" if i == 0 else passwords[i - 1]
            user.change_password(db_session, current_pass, new_pass)

        # When/Then: 直近のパスワードは使用不可
        with pytest.raises(BusinessLogicError, match="直近3回"):
            user.change_password(db_session, passwords[-1], passwords[0])

    def test_account_lockout_after_failed_attempts(self, db_session: Session) -> None:
        """TEST-USER-MODEL-004: ログイン失敗によるアカウントロックをテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When: 5回連続でログイン失敗
        for _ in range(5):
            user.record_failed_login(db_session)

        # Then: アカウントがロックされる
        assert user.is_locked()
        assert user.failed_login_attempts == 5
        assert user.locked_until > datetime.now(timezone.utc)
        assert user.locked_until < datetime.now(timezone.utc) + timedelta(minutes=35)

    def test_successful_login_resets_failed_attempts(self, db_session: Session) -> None:
        """TEST-USER-MODEL-005: 成功ログインで失敗回数リセットをテスト."""
        # Given: 失敗回数があるユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        user.failed_login_attempts = 3
        db_session.commit()

        # When: ログイン成功
        user.record_successful_login(db_session)

        # Then: 失敗回数がリセット
        assert user.failed_login_attempts == 0
        assert user.last_login_at is not None

    def test_profile_image_url(self, db_session: Session) -> None:
        """TEST-USER-MODEL-006: プロファイル画像URLの保存をテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When: プロファイル画像URL設定
        user.update(db_session, profile_image_url="https://example.com/avatar.jpg")

        # Then: 正しく保存される
        assert user.profile_image_url == "https://example.com/avatar.jpg"

    def test_password_strength_validation(self, db_session: Session) -> None:
        """TEST-USER-MODEL-007: パスワード強度検証をテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When/Then: 弱いパスワードは拒否
        weak_passwords = [
            "short",  # 短すぎる
            "alllowercase123",  # 大文字なし (2/4)
            "ALLUPPERCASE123",  # 小文字なし (2/4)
            "no123",  # 大文字・特殊文字なし (2/4)
            "NOLOWER123",  # 小文字・特殊文字なし (2/4)
        ]

        for weak_pass in weak_passwords:
            with pytest.raises(BusinessLogicError, match="パスワード"):
                user.change_password(db_session, "TestPassword123!", weak_pass)

    def test_user_session_tracking(self, db_session: Session) -> None:
        """TEST-USER-MODEL-008: ユーザーセッション追跡をテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When: セッション作成
        session = user.create_session(
            db_session,
            session_token="test-session-token",
            refresh_token="test-refresh-token",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        # Then: セッションが記録される
        assert session.user_id == user.id
        assert session.ip_address == "192.168.1.1"
        assert session.expires_at > datetime.now(timezone.utc)
        assert len(user.active_sessions) == 1

    def test_concurrent_session_limit(self, db_session: Session) -> None:
        """TEST-USER-MODEL-009: 同時セッション数制限をテスト."""
        # Given: ユーザーと5つのセッション
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        for i in range(5):
            user.create_session(
                db_session,
                session_token=f"session-{i}",
                refresh_token=f"refresh-{i}",
            )

        # When: 6つ目のセッション作成
        user.create_session(
            db_session, session_token="session-6", refresh_token="refresh-6"
        )

        # Then: 古いセッションが削除され、5つに保たれる
        active_sessions = user.active_sessions
        assert len(active_sessions) == 5
        assert all(s.session_token != "session-0" for s in active_sessions)

    def test_user_organization_assignment(self, db_session: Session) -> None:
        """TEST-USER-MODEL-010: ユーザーの組織割り当てをテスト."""
        # Given: ユーザーと組織
        from tests.factories import create_test_organization, create_test_role

        user = create_test_user(db_session)
        org = create_test_organization(db_session)
        role = create_test_role(db_session, code="USER")
        db_session.add_all([user, org, role])
        db_session.commit()

        # When: 組織に割り当て
        user_role = user.assign_to_organization(
            db_session, organization=org, role=role, assigned_by=user.id
        )

        # Then: 正しく割り当てられる
        assert user_role.user_id == user.id
        assert user_role.organization_id == org.id
        assert user_role.role_id == role.id
        assert user.get_organizations()[0].id == org.id

    def test_user_department_assignment(self, db_session: Session) -> None:
        """TEST-USER-MODEL-011: ユーザーの部門割り当てをテスト."""
        # Given: ユーザー、組織、部門
        from tests.factories import (
            create_test_department,
            create_test_organization,
            create_test_role,
        )

        user = create_test_user(db_session)
        org = create_test_organization(db_session)
        dept = create_test_department(db_session, organization=org)
        role = create_test_role(db_session, code="DEPT_USER")
        db_session.add_all([user, org, dept, role])
        db_session.commit()

        # When: 部門に割り当て
        user_role = user.assign_to_department(
            db_session,
            organization=org,
            department=dept,
            role=role,
            assigned_by=user.id,
        )

        # Then: 正しく割り当てられる
        assert user_role.department_id == dept.id
        assert user.get_departments(org.id)[0].id == dept.id

    def test_user_effective_permissions(self, db_session: Session) -> None:
        """TEST-USER-MODEL-012: ユーザーの実効権限計算をテスト."""
        # Skip this test as it requires complex permission setup
        # This functionality will be tested in integration tests
        pytest.skip("Permission assignment requires full service layer - tested in integration")

    def test_password_expiry_check(self, db_session: Session) -> None:
        """TEST-USER-MODEL-013: パスワード有効期限チェックをテスト."""
        # Given: パスワード変更から90日経過したユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        user.password_changed_at = datetime.now(timezone.utc) - timedelta(days=91)
        db_session.commit()

        # When: パスワード期限チェック
        is_expired = user.is_password_expired()

        # Then: 期限切れと判定
        assert is_expired is True

    def test_user_soft_delete(self, db_session: Session) -> None:
        """TEST-USER-MODEL-014: ユーザーの論理削除をテスト."""
        # Given: アクティブなユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        # When: 論理削除
        user.soft_delete(db_session, deleted_by=1)

        # Then: 非アクティブ化される
        assert user.is_active is False
        assert user.deleted_at is not None
        assert user.deleted_by == 1
        # データは残っている
        assert db_session.query(User).filter(User.id == user_id).first() is not None

    def test_user_activity_log(self, db_session: Session) -> None:
        """TEST-USER-MODEL-015: ユーザー活動ログ記録をテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When: 活動を記録
        user.log_activity(
            db_session,
            action="profile_update",
            details={"field": "full_name", "old": "Old Name", "new": "New Name"},
        )

        # Then: ログが記録される
        from app.models.audit import UserActivityLog

        logs = (
            db_session.query(UserActivityLog)
            .filter(UserActivityLog.user_id == user.id)
            .all()
        )
        assert len(logs) == 1
        assert logs[0].action == "profile_update"
        assert logs[0].details["field"] == "full_name"
