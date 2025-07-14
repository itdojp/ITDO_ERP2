"""
User management security tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, PermissionDenied
from app.models.user import PasswordHistory, User
from tests.factories import (
    create_test_department,
    create_test_organization,
    create_test_role,
    create_test_user,
    create_test_user_role,
)


class TestUserSecurityFeatures:
    """Test cases for user security features."""

    def test_password_history_prevents_reuse(self, db_session: Session) -> None:
        """TEST-SEC-USER-001: パスワード履歴による再利用防止をテスト."""
        # Given: ユーザーとパスワード履歴
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # パスワードを数回変更して履歴作成
        passwords = ["OldPass1!", "OldPass2!", "OldPass3!", "CurrentPass!"]
        for i in range(len(passwords) - 1):
            # 履歴に追加
            history = PasswordHistory(
                user_id=user.id, password_hash=user.hashed_password
            )
            db_session.add(history)
            # 新しいパスワードに変更
            user.hashed_password = passwords[i + 1]

        db_session.commit()

        # When/Then: 直近3つのパスワードは使用不可
        from app.core.security import hash_password

        for old_pass in passwords[:3]:
            assert user.is_password_in_history(hash_password(old_pass))

    def test_account_lockout_security(self, db_session: Session) -> None:
        """TEST-SEC-USER-002: アカウントロックアウトのセキュリティをテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When: 5回連続ログイン失敗
        for i in range(5):
            user.record_failed_login(db_session)
            db_session.commit()

            # 5回未満はロックされない
            if i < 4:
                assert not user.is_locked()
            else:
                # 5回目でロック
                assert user.is_locked()

        # Then: ロック期間中はログイン不可
        assert user.locked_until > datetime.now(timezone.utc)
        assert user.locked_until < datetime.now(timezone.utc) + timedelta(minutes=31)

    def test_session_hijacking_prevention(self, db_session: Session) -> None:
        """TEST-SEC-USER-003: セッションハイジャック防止をテスト."""
        # Given: ユーザーとセッション
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # 正規セッション作成
        user.create_session(
            db_session,
            session_token="valid-token",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Windows",
        )

        # When: 異なるIPからの同じトークン使用
        suspicious_session = user.validate_session(
            session_token="valid-token",
            ip_address="10.0.0.1",  # 異なるIP
            user_agent="Mozilla/5.0 Windows",
        )

        # Then: セキュリティ警告またはブロック
        assert suspicious_session.requires_verification
        assert suspicious_session.security_alert == "IP_MISMATCH"

    def test_concurrent_session_limit_security(self, db_session: Session) -> None:
        """TEST-SEC-USER-004: 同時セッション数制限のセキュリティをテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When: 最大数を超えるセッション作成
        sessions = []
        for i in range(6):  # 最大5セッション
            session = user.create_session(
                db_session,
                session_token=f"session-{i}",
                ip_address="192.168.1.100",
            )
            sessions.append(session)

        # Then: 古いセッションが無効化
        db_session.refresh(sessions[0])
        assert sessions[0].is_active is False
        assert len(user.active_sessions) == 5

    def test_privilege_escalation_prevention(self, db_session: Session) -> None:
        """TEST-SEC-USER-005: 権限昇格攻撃の防止をテスト."""
        # Given: 一般ユーザー
        user = create_test_user(db_session)
        org = create_test_organization(db_session)
        user_role = create_test_role(db_session, code="USER", permissions=["read:own"])
        admin_role = create_test_role(db_session, code="ADMIN", permissions=["*"])
        create_test_user_role(db_session, user=user, role=user_role, organization=org)
        db_session.commit()

        # When/Then: 自分に管理者ロールを付与しようとして失敗
        with pytest.raises(PermissionDenied):
            user.assign_role_to_self(admin_role, org)

    def test_data_access_isolation(self, db_session: Session) -> None:
        """TEST-SEC-USER-006: ユーザーデータアクセス分離をテスト."""
        # Given: 2つの組織のユーザー
        org1 = create_test_organization(code="ORG1")
        org2 = create_test_organization(code="ORG2")

        user1 = create_test_user(db_session, email="user1@org1.com")
        user2 = create_test_user(db_session, email="user2@org2.com")

        role = create_test_role(db_session, code="USER")
        create_test_user_role(db_session, user=user1, role=role, organization=org1)
        create_test_user_role(db_session, user=user2, role=role, organization=org2)
        db_session.commit()

        # When: user1がuser2の情報にアクセス
        from app.services.user import UserService

        service = UserService(db_session)

        # Then: アクセス拒否
        with pytest.raises(PermissionDenied):
            service.get_user_detail(user_id=user2.id, viewer=user1, db=db_session)

    def test_sql_injection_in_user_search(self, db_session: Session) -> None:
        """TEST-SEC-USER-007: ユーザー検索でのSQLインジェクション防止をテスト."""
        # Given: ユーザーデータ
        admin = create_test_user(db_session, is_superuser=True)
        target_user = create_test_user(db_session, email="target@example.com")
        db_session.add_all([admin, target_user])
        db_session.commit()

        # When: 悪意のある検索クエリ
        from app.services.user import UserService

        service = UserService(db_session)
        malicious_queries = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "target' UNION SELECT * FROM users --",
        ]

        for query in malicious_queries:
            # SQLインジェクション試行
            from app.schemas.user import UserSearchParams

            params = UserSearchParams(search=query)
            result = service.search_users(params=params, searcher=admin, db=db_session)

            # Then: 正常に処理される（攻撃は無効）
            assert isinstance(result.items, list)
            # テーブルが削除されていない
            assert db_session.query(User).count() >= 2

    def test_password_complexity_enforcement(self, db_session: Session) -> None:
        """TEST-SEC-USER-008: パスワード複雑性の強制をテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When/Then: 様々な弱いパスワードが拒否される
        weak_passwords = [
            "password",  # 辞書攻撃対象
            "12345678",  # 連続数字
            "qwertyui",  # キーボードパターン
            user.email.split("@")[0],  # ユーザー名ベース
            "TestTest",  # 繰り返しパターン
        ]

        from app.core.exceptions import BusinessLogicError

        for weak_pass in weak_passwords:
            with pytest.raises(BusinessLogicError, match="パスワード"):
                user.validate_password_strength(weak_pass)

    def test_sensitive_data_masking(self, db_session: Session) -> None:
        """TEST-SEC-USER-009: 機密データのマスキングをテスト."""
        # Given: ユーザー
        user = create_test_user(
            db_session,
            email="sensitive@example.com",
            full_name="山田太郎",
            phone="090-1234-5678",
        )
        db_session.add(user)
        db_session.commit()

        # When: ログやエクスポートでのデータ表示
        user_dict = user.to_dict_safe()

        # Then: 機密情報がマスクされる
        assert "hashed_password" not in user_dict
        assert user_dict["email"] == "sen******@example.com"
        assert user_dict["phone"] == "090-****-5678"

    def test_brute_force_protection(self, db_session: Session) -> None:
        """TEST-SEC-USER-010: ブルートフォース攻撃防止をテスト."""
        # Given: ユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        # When: 短時間での大量ログイン試行
        start_time = datetime.now(timezone.utc)
        attempt_count = 0

        # 1分間での試行
        while (datetime.now(timezone.utc) - start_time).seconds < 60:
            try:
                # ログイン試行
                user.authenticate(db_session, user.email, "wrong_password")
                attempt_count += 1
            except AuthenticationError as e:
                if "rate_limit" in str(e):
                    break

        # Then: レート制限が発動
        assert attempt_count < 20  # 1分間で20回未満に制限

    def test_token_security_validation(self, db_session: Session) -> None:
        """TEST-SEC-USER-011: トークンセキュリティ検証をテスト."""
        # Given: ユーザーとトークン
        user = create_test_user(db_session)
        db_session.add(user)
        db_session.commit()

        from app.core.security import create_access_token

        # When: 様々な不正トークン
        valid_token = create_access_token({"sub": str(user.id)})

        # トークン改ざん
        tampered_token = valid_token[:-5] + "xxxxx"

        # Then: 不正トークンは拒否
        from app.core.exceptions import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            from app.core.security import verify_token

            verify_token(tampered_token)

    def test_role_permission_boundary(self, db_session: Session) -> None:
        """TEST-SEC-USER-012: ロール権限境界のテストをテスト."""
        # Given: 階層的な組織構造
        org = create_test_organization(db_session)
        parent_dept = create_test_department(db_session, organization_id=org.id, name="親部門")
        child_dept = create_test_department(
            db_session, organization_id=org.id, parent_id=parent_dept.id, name="子部門"
        )

        # 部門管理者
        dept_manager = create_test_user(db_session)
        manager_role = create_test_role(
            code="DEPT_MANAGER", permissions=["dept:*", "user:read"]
        )
        create_test_user_role(
            user=dept_manager,
            role=manager_role,
            organization=org,
            department=child_dept,
        )
        db_session.commit()

        # When: 親部門のユーザーにアクセス
        parent_user = create_test_user(db_session, email="parent@example.com")
        create_test_user_role(
            user=parent_user,
            role=manager_role,
            organization=org,
            department=parent_dept,
        )

        # Then: アクセス拒否（権限境界）
        assert not dept_manager.can_access_user(parent_user)

    def test_audit_trail_integrity(self, db_session: Session) -> None:
        """TEST-SEC-USER-013: 監査証跡の完全性をテスト."""
        # Given: ユーザー操作
        admin = create_test_user(db_session, is_superuser=True)
        user = create_test_user(db_session)
        db_session.add_all([admin, user])
        db_session.commit()

        # When: 重要操作の実行
        from app.services.user import UserService

        service = UserService(db_session)
        service.delete_user(user_id=user.id, deleter=admin, db=db_session)

        # Then: 監査ログが改ざん不可能な形で記録
        from app.models.audit import AuditLog

        logs = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.resource_type == "user",
                AuditLog.resource_id == user.id,
                AuditLog.action == "delete",
            )
            .all()
        )

        assert len(logs) == 1
        assert logs[0].user_id == admin.id
        assert logs[0].checksum is not None  # 改ざん検知用チェックサム

    def test_password_expiry_enforcement(self, db_session: Session) -> None:
        """TEST-SEC-USER-014: パスワード有効期限の強制をテスト."""
        # Given: 期限切れパスワードのユーザー
        user = create_test_user(db_session)
        db_session.add(user)
        user.password_changed_at = datetime.now(timezone.utc) - timedelta(days=91)
        db_session.commit()

        # When: ログイン試行
        from app.services.auth import AuthService

        auth_service = AuthService()

        # Then: パスワード変更が必要
        result = auth_service.authenticate_user(
            db_session, user.email, "TestPassword123!"
        )
        assert result.requires_password_change
        assert result.reason == "PASSWORD_EXPIRED"

    def test_personal_data_encryption(self, db_session: Session) -> None:
        """TEST-SEC-USER-015: 個人情報の暗号化をテスト."""
        # Given: 個人情報を含むユーザー
        user = create_test_user(
            db_session,
            full_name="山田太郎",
            phone="090-1234-5678",
            # 将来的に追加される可能性のある機密情報
            # ssn="123-45-6789",
            # credit_card="1234-5678-9012-3456"
        )
        db_session.add(user)
        db_session.commit()

        # When: データベースに保存
        # 直接SQLで取得（ORMを通さない）
        from sqlalchemy import text
        raw_data = db_session.execute(
            text("SELECT phone FROM users WHERE id = :user_id"),
            {"user_id": user.id}
        ).first()

        # Then: 暗号化されている（平文ではない）
        assert raw_data[0] != "090-1234-5678"  # 暗号化されているはず
        # ORMを通すと復号される
        assert user.phone == "090-1234-5678"
