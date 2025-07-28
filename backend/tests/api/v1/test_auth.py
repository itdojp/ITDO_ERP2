"""認証APIのテストモジュール

Phase 3: Validation - 失敗するテストを先に作成
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User


class TestLogin:
    """ログインエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        Given: 有効なメールアドレスとパスワードを持つユーザーが存在する
        When: 正しい認証情報でログインする
        Then: アクセストークンとリフレッシュトークンが返される
        """
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @pytest.mark.asyncio
    async def test_login_with_invalid_password(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        Given: 登録済みユーザーが存在する
        When: 誤ったパスワードでログインを試みる
        Then: 401エラーが返される
        """
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["detail"] == "Invalid authentication credentials"
        assert data["code"] == "AUTH001"

    @pytest.mark.asyncio
    async def test_login_with_nonexistent_email(
        self, async_client: AsyncClient
    ):
        """
        Given: 存在しないメールアドレス
        When: ログインを試みる
        Then: 401エラーが返される（セキュリティのため存在しないことは明示しない）
        """
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["detail"] == "Invalid authentication credentials"

    @pytest.mark.asyncio
    async def test_account_lockout_after_failed_attempts(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        Given: ユーザーが存在する
        When: 5回連続でログインに失敗する
        Then: アカウントが30分間ロックされる
        """
        # 5回失敗
        for _ in range(5):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "WrongPassword"
                }
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 6回目の試行（正しいパスワードでも失敗）
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == status.HTTP_423_LOCKED
        data = response.json()
        assert "locked" in data["detail"].lower()
        assert data["code"] == "AUTH004"


class TestGoogleSSO:
    """Google OAuth認証のテスト"""

    @pytest.mark.asyncio
    async def test_google_login_with_valid_token(
        self, async_client: AsyncClient
    ):
        """
        Given: 有効なGoogle IDトークン
        When: Googleログインを実行する
        Then: アクセストークンが返される
        """
        with patch("app.services.auth.verify_google_token") as mock_verify:
            mock_verify.return_value = {
                "email": "user@example.com",
                "email_verified": True,
                "name": "Test User",
                "sub": "google-user-id-123"
            }
            
            response = await async_client.post(
                "/api/v1/auth/login/google",
                json={"id_token": "valid-google-token"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_google_login_with_invalid_token(
        self, async_client: AsyncClient
    ):
        """
        Given: 無効なGoogle IDトークン
        When: Googleログインを試みる
        Then: 401エラーが返される
        """
        with patch("app.services.auth.verify_google_token") as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            
            response = await async_client.post(
                "/api/v1/auth/login/google",
                json={"id_token": "invalid-google-token"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMFA:
    """多要素認証のテスト"""

    @pytest.mark.asyncio
    async def test_mfa_required_for_external_access(
        self, async_client: AsyncClient, test_user_with_mfa: User
    ):
        """
        Given: MFAが設定されたユーザーが社外からアクセス
        When: メール/パスワードでログイン
        Then: MFA要求のレスポンスが返される
        """
        # 社外IPアドレスをシミュレート
        headers = {"X-Forwarded-For": "203.0.113.10"}
        
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "mfa@example.com",
                "password": "SecurePass123!"
            },
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["mfa_required"] is True
        assert "mfa_token" in data  # MFA検証用の一時トークン
        assert "access_token" not in data  # まだアクセストークンは発行されない

    @pytest.mark.asyncio
    async def test_mfa_verification_with_valid_code(
        self, async_client: AsyncClient, mfa_token: str
    ):
        """
        Given: MFA一時トークンを持つユーザー
        When: 正しい6桁のTOTPコードを送信
        Then: アクセストークンが発行される
        """
        with patch("app.services.auth.verify_totp") as mock_verify:
            mock_verify.return_value = True
            
            response = await async_client.post(
                "/api/v1/auth/mfa/verify",
                json={"code": "123456"},
                headers={"Authorization": f"Bearer {mfa_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_mfa_verification_with_invalid_code(
        self, async_client: AsyncClient, mfa_token: str
    ):
        """
        Given: MFA一時トークンを持つユーザー
        When: 誤った6桁のコードを送信
        Then: 401エラーが返される
        """
        with patch("app.services.auth.verify_totp") as mock_verify:
            mock_verify.return_value = False
            
            response = await async_client.post(
                "/api/v1/auth/mfa/verify",
                json={"code": "000000"},
                headers={"Authorization": f"Bearer {mfa_token}"}
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert data["code"] == "AUTH003"

    @pytest.mark.asyncio
    async def test_mfa_setup_generates_qr_code(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """
        Given: 認証済みユーザー
        When: MFA設定を開始
        Then: QRコードとバックアップコードが生成される
        """
        response = await async_client.post(
            "/api/v1/auth/mfa/setup",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "qr_code" in data
        assert "secret" in data
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 10


class TestTokenRefresh:
    """トークンリフレッシュのテスト"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, async_client: AsyncClient, valid_refresh_token: str
    ):
        """
        Given: 有効なリフレッシュトークン
        When: トークンリフレッシュを要求
        Then: 新しいアクセストークンが発行される
        """
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": valid_refresh_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != valid_refresh_token  # 新しいトークン

    @pytest.mark.asyncio
    async def test_refresh_token_expired(
        self, async_client: AsyncClient, expired_refresh_token: str
    ):
        """
        Given: 期限切れのリフレッシュトークン
        When: トークンリフレッシュを要求
        Then: 401エラーが返される
        """
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_refresh_token}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["code"] == "AUTH002"


class TestPasswordReset:
    """パスワードリセットのテスト"""

    @pytest.mark.asyncio
    async def test_password_reset_request(
        self, async_client: AsyncClient, test_user: User
    ):
        """
        Given: 登録済みユーザー
        When: パスワードリセットを要求
        Then: 204レスポンスが返される（メール送信）
        """
        with patch("app.services.email.send_password_reset_email") as mock_send:
            mock_send.return_value = None
            
            response = await async_client.post(
                "/api/v1/auth/password/reset",
                json={"email": "test@example.com"}
            )
            
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_password_reset_with_nonexistent_email(
        self, async_client: AsyncClient
    ):
        """
        Given: 存在しないメールアドレス
        When: パスワードリセットを要求
        Then: 204レスポンスが返される（セキュリティのため同じレスポンス）
        """
        response = await async_client.post(
            "/api/v1/auth/password/reset",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_password_reset_confirm_success(
        self, async_client: AsyncClient, password_reset_token: str
    ):
        """
        Given: 有効なパスワードリセットトークン
        When: 新しいパスワードを設定
        Then: パスワードが更新される
        """
        response = await async_client.post(
            "/api/v1/auth/password/reset/confirm",
            json={
                "token": password_reset_token,
                "new_password": "NewSecurePass456!"
            }
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 新しいパスワードでログイン可能
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "NewSecurePass456!"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_password_reset_with_weak_password(
        self, async_client: AsyncClient, password_reset_token: str
    ):
        """
        Given: 有効なパスワードリセットトークン
        When: 弱いパスワードを設定しようとする
        Then: 400エラーが返される
        """
        response = await async_client.post(
            "/api/v1/auth/password/reset/confirm",
            json={
                "token": password_reset_token,
                "new_password": "weak"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "password" in data["detail"].lower()


class TestLogout:
    """ログアウトのテスト"""

    @pytest.mark.asyncio
    async def test_logout_success(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """
        Given: ログイン済みユーザー
        When: ログアウトする
        Then: セッションが終了する
        """
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 同じトークンでアクセスできない
        test_response = await async_client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        assert test_response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSessionTimeout:
    """セッションタイムアウトのテスト"""

    @pytest.mark.asyncio
    async def test_idle_timeout(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """
        Given: ログイン済みユーザー（アイドルタイムアウト30分）
        When: 30分間操作を行わない
        Then: セッションがタイムアウトする
        """
        # 時間を30分進める
        with patch("app.core.security.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(minutes=31)
            
            response = await async_client.get(
                "/api/v1/users/me",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert "timeout" in data["detail"].lower()