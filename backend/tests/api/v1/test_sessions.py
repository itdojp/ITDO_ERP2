"""セッション管理APIのテストモジュール

Phase 3: Validation - 失敗するテストを先に作成
"""
from datetime import datetime, timedelta
from typing import List

import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.user import User


class TestUserSessions:
    """ユーザーセッション管理のテスト"""

    @pytest.mark.asyncio
    async def test_get_my_sessions(
        self, async_client: AsyncClient, user_headers: dict, user_sessions: List[dict]
    ):
        """
        Given: ユーザーとしてログイン済み（複数セッション存在）
        When: 自分のセッション一覧を取得
        Then: アクティブなセッション一覧が返される
        """
        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) > 0
        
        # セッション情報の確認
        session = data["sessions"][0]
        assert "id" in session
        assert "created_at" in session
        assert "last_accessed_at" in session
        assert "expires_at" in session
        assert "ip_address" in session
        assert "user_agent" in session
        assert "is_current" in session
        
        # 現在のセッションが含まれている
        current_sessions = [s for s in data["sessions"] if s["is_current"]]
        assert len(current_sessions) == 1

    @pytest.mark.asyncio
    async def test_terminate_other_session(
        self, async_client: AsyncClient, user_headers: dict, user_sessions: List[dict]
    ):
        """
        Given: 複数のアクティブセッションを持つユーザー
        When: 他のセッションを終了
        Then: 指定したセッションが終了する
        """
        # 最初に全セッションを取得
        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers=user_headers
        )
        sessions = response.json()["sessions"]
        
        # 現在のセッション以外を選択
        other_session = next(s for s in sessions if not s["is_current"])
        
        # セッション終了
        response = await async_client.delete(
            f"/api/v1/users/me/sessions/{other_session['id']}",
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 確認
        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers=user_headers
        )
        remaining_sessions = response.json()["sessions"]
        assert len(remaining_sessions) == len(sessions) - 1
        assert not any(s["id"] == other_session["id"] for s in remaining_sessions)

    @pytest.mark.asyncio
    async def test_cannot_terminate_current_session_via_api(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ログイン済みユーザー
        When: 現在のセッションを終了しようとする
        Then: 400エラーが返される（ログアウトエンドポイントを使用すべき）
        """
        # 現在のセッションIDを取得
        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers=user_headers
        )
        current_session = next(s for s in response.json()["sessions"] if s["is_current"])
        
        # 現在のセッションを終了しようとする
        response = await async_client.delete(
            f"/api/v1/users/me/sessions/{current_session['id']}",
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "current" in data["detail"].lower()


class TestSessionSettings:
    """セッション設定のテスト"""

    @pytest.mark.asyncio
    async def test_get_session_settings(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ユーザーとしてログイン済み
        When: セッション設定を取得
        Then: 現在の設定値が返される
        """
        response = await async_client.get(
            "/api/v1/users/me/sessions/settings",
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_timeout_hours" in data
        assert "idle_timeout_minutes" in data
        assert data["session_timeout_hours"] == 8  # デフォルト値
        assert data["idle_timeout_minutes"] == 30  # デフォルト値

    @pytest.mark.asyncio
    async def test_update_session_timeout(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ユーザーとしてログイン済み
        When: セッションタイムアウトを4時間に変更
        Then: 設定が更新される（次回ログインから適用）
        """
        settings = {
            "session_timeout_hours": 4,
            "idle_timeout_minutes": 30
        }
        
        response = await async_client.put(
            "/api/v1/users/me/sessions/settings",
            json=settings,
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_timeout_hours"] == 4
        assert data["idle_timeout_minutes"] == 30

    @pytest.mark.asyncio
    async def test_session_timeout_validation(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ユーザーとしてログイン済み
        When: 無効なタイムアウト値を設定しようとする
        Then: 400エラーが返される
        """
        # 範囲外の値
        invalid_settings = [
            {"session_timeout_hours": 0, "idle_timeout_minutes": 30},  # 最小値未満
            {"session_timeout_hours": 25, "idle_timeout_minutes": 30}, # 最大値超過
            {"session_timeout_hours": 8, "idle_timeout_minutes": 10},  # アイドル最小値未満
            {"session_timeout_hours": 8, "idle_timeout_minutes": 121}, # アイドル最大値超過
        ]
        
        for settings in invalid_settings:
            response = await async_client.put(
                "/api/v1/users/me/sessions/settings",
                json=settings,
                headers=user_headers
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSessionLimits:
    """セッション数制限のテスト"""

    @pytest.mark.asyncio
    async def test_max_concurrent_sessions(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        Given: ユーザーが3つのアクティブセッションを持っている
        When: 4つ目のセッションでログインする
        Then: 最古のセッションが自動的に終了し、新しいセッションが作成される
        """
        # 3つのセッションを作成
        sessions = []
        for i in range(3):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user.email,
                    "password": "SecurePass123!"
                },
                headers={"User-Agent": f"TestClient{i}"}
            )
            assert response.status_code == status.HTTP_200_OK
            sessions.append(response.json()["access_token"])
        
        # 4つ目のログイン
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "SecurePass123!"
            },
            headers={"User-Agent": "TestClient3"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # 最初のセッションが無効になっていることを確認
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {sessions[0]}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_user_type_session_limits(
        self, async_client: AsyncClient, admin_user: User
    ):
        """
        Given: 管理者ユーザー（セッション数制限が異なる可能性）
        When: セッション制限を確認
        Then: ユーザータイプに応じた制限が適用される
        """
        # 管理者の場合、より多くのセッションが許可される可能性
        sessions = []
        for i in range(5):  # 管理者は5セッションまで許可と仮定
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": admin_user.email,
                    "password": "AdminPass123!"
                },
                headers={"User-Agent": f"AdminClient{i}"}
            )
            assert response.status_code == status.HTTP_200_OK
            sessions.append(response.json()["access_token"])
        
        # すべてのセッションがアクティブ
        for i, token in enumerate(sessions[:5]):
            response = await async_client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == status.HTTP_200_OK


class TestAdminSessionMonitoring:
    """管理者によるセッション監視のテスト"""

    @pytest.mark.asyncio
    async def test_admin_view_all_sessions(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """
        Given: 管理者としてログイン済み
        When: 全アクティブセッションを取得
        Then: すべてのユーザーのセッション情報が表示される
        """
        response = await async_client.get(
            "/api/v1/admin/sessions",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        
        # セッション情報の確認
        if len(data["sessions"]) > 0:
            session = data["sessions"][0]
            assert "id" in session
            assert "user_id" in session
            assert "user_email" in session
            assert "user_name" in session
            assert "created_at" in session
            assert "last_accessed_at" in session
            assert "expires_at" in session
            assert "ip_address" in session

    @pytest.mark.asyncio
    async def test_admin_view_sessions_with_pagination(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """
        Given: 管理者としてログイン済み（多数のセッションが存在）
        When: ページネーション付きでセッション一覧を取得
        Then: 指定されたページのセッションが返される
        """
        response = await async_client.get(
            "/api/v1/admin/sessions?page=1&per_page=50",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sessions"]) <= 50

    @pytest.mark.asyncio
    async def test_admin_terminate_user_session(
        self, async_client: AsyncClient, admin_headers: dict, active_session: dict
    ):
        """
        Given: 管理者としてログイン済み
        When: 特定のユーザーセッションを強制終了
        Then: そのセッションが終了する
        """
        response = await async_client.delete(
            f"/api/v1/admin/sessions/{active_session['id']}",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 終了したセッションでアクセスできない
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {active_session['token']}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_admin_sessions(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: 一般ユーザーとしてログイン済み
        When: 管理者用セッション監視にアクセスしようとする
        Then: 403エラーが返される
        """
        response = await async_client.get(
            "/api/v1/admin/sessions",
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSessionExpiry:
    """セッション有効期限のテスト"""

    @pytest.mark.asyncio
    async def test_session_expiry_time(
        self, async_client: AsyncClient, user_headers: dict, test_user: User
    ):
        """
        Given: セッションタイムアウト8時間のユーザー
        When: 8時間経過後にアクセス
        Then: セッションが期限切れとなる
        """
        # 時間を8時間1分進める
        from unittest.mock import patch
        with patch("app.core.security.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(hours=8, minutes=1)
            
            response = await async_client.get(
                "/api/v1/users/me",
                headers=user_headers
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["code"] == "AUTH002"

    @pytest.mark.asyncio
    async def test_session_refresh_on_activity(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: アクティブなセッション
        When: API呼び出しを行う
        Then: last_accessed_atが更新される
        """
        # 最初のアクセス時刻を記録
        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers=user_headers
        )
        sessions_before = response.json()["sessions"]
        current_session_before = next(s for s in sessions_before if s["is_current"])
        
        # 少し待つ
        import time
        time.sleep(1)
        
        # 別のAPIを呼び出す
        await async_client.get(
            "/api/v1/users/me",
            headers=user_headers
        )
        
        # セッション情報を再取得
        response = await async_client.get(
            "/api/v1/users/me/sessions",
            headers=user_headers
        )
        sessions_after = response.json()["sessions"]
        current_session_after = next(s for s in sessions_after if s["is_current"])
        
        # last_accessed_atが更新されている
        assert current_session_after["last_accessed_at"] > current_session_before["last_accessed_at"]