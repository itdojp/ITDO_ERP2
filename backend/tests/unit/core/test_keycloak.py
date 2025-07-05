"""
Keycloak client unit tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Tuple
import hashlib
import base64
import secrets

from app.core.keycloak import (
    KeycloakClient,
    generate_pkce_pair,
    verify_pkce_pair,
    is_base64url,
    InvalidTokenError,
    AuthenticationError,
)
from tests.utils.settings import create_test_settings


class TestKeycloakClient:
    """Test cases for KeycloakClient class."""

    def test_keycloak_client_initialization(self) -> None:
        """TEST-KC-001: Keycloakクライアントが正しく初期化されることを確認."""
        # Given: Keycloak設定
        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )

        # When: クライアント初期化
        client = KeycloakClient(settings)

        # Then: クライアントが作成され、設定が正しく適用される
        assert client.keycloak_openid is not None
        assert client.realm_name == "test-realm"
        assert client.client_id == "test-client"
        assert client.server_url == "http://localhost:8080"

    def test_generate_auth_url(self) -> None:
        """TEST-KC-002: 認証URLが正しく生成されることを確認."""
        # Given: Keycloakクライアント
        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When: 認証URL生成
        auth_url = client.get_auth_url(
            redirect_uri="http://localhost:8000/callback",
            state="test-state-123",
        )

        # Then: URLが生成され、必要なパラメータが含まれる
        assert "http://localhost:8080/auth/realms/test-realm/protocol/openid-connect/auth" in auth_url
        assert "client_id=test-client" in auth_url
        assert "state=test-state-123" in auth_url
        assert "response_type=code" in auth_url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback" in auth_url

    def test_generate_auth_url_with_pkce(self) -> None:
        """認証URLにPKCEパラメータが含まれることを確認."""
        # Given: Keycloakクライアント
        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When: PKCE付き認証URL生成
        auth_url, verifier = client.get_auth_url_with_pkce(
            redirect_uri="http://localhost:8000/callback",
            state="test-state-123",
        )

        # Then: PKCEパラメータが含まれる
        assert "code_challenge=" in auth_url
        assert "code_challenge_method=S256" in auth_url
        assert len(verifier) >= 43
        assert len(verifier) <= 128

    @patch("app.core.keycloak.KeycloakOpenID")
    def test_exchange_code_for_token(self, mock_keycloak_class: Mock) -> None:
        """TEST-KC-004: 認可コードをトークンに交換できることを確認."""
        # Given: モックKeycloakレスポンス
        mock_keycloak = Mock()
        mock_keycloak.token.return_value = {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
        mock_keycloak_class.return_value = mock_keycloak

        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When: トークン交換
        tokens = client.exchange_code(
            code="test-auth-code",
            redirect_uri="http://localhost:8000/callback",
        )

        # Then: トークンが取得される
        assert tokens["access_token"] == "mock-access-token"
        assert tokens["refresh_token"] == "mock-refresh-token"
        assert tokens["expires_in"] == 300
        assert tokens["token_type"] == "Bearer"

        # 正しいパラメータで呼ばれたことを確認
        mock_keycloak.token.assert_called_once_with(
            code="test-auth-code",
            redirect_uri="http://localhost:8000/callback",
            grant_type="authorization_code",
        )

    @patch("app.core.keycloak.KeycloakOpenID")
    def test_verify_keycloak_token(self, mock_keycloak_class: Mock) -> None:
        """TEST-KC-005: Keycloakトークンが正しく検証されることを確認."""
        # Given: 有効なトークン
        mock_keycloak = Mock()
        mock_keycloak.introspect.return_value = {
            "active": True,
            "sub": "test-user-id",
            "email": "test@example.com",
        }
        mock_keycloak.userinfo.return_value = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "name": "Test User",
            "realm_access": {"roles": ["admin", "user"]},
        }
        mock_keycloak_class.return_value = mock_keycloak

        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When: トークン検証
        userinfo = client.verify_token("valid-token")

        # Then: ユーザー情報が取得される
        assert userinfo["sub"] == "test-user-id"
        assert userinfo["email"] == "test@example.com"
        assert "admin" in userinfo["realm_access"]["roles"]

    @patch("app.core.keycloak.KeycloakOpenID")
    def test_verify_invalid_token(self, mock_keycloak_class: Mock) -> None:
        """TEST-KC-006: 無効なトークンが拒否されることを確認."""
        # Given: 無効なトークン
        mock_keycloak = Mock()
        mock_keycloak.introspect.return_value = {"active": False}
        mock_keycloak_class.return_value = mock_keycloak

        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When/Then: 検証時に例外発生
        with pytest.raises(InvalidTokenError) as exc_info:
            client.verify_token("invalid-token")

        assert "Token is not active" in str(exc_info.value)

    @patch("app.core.keycloak.KeycloakOpenID")
    def test_get_userinfo(self, mock_keycloak_class: Mock) -> None:
        """TEST-KC-007: ユーザー情報が正しく取得されることを確認."""
        # Given: 認証済みトークン
        mock_keycloak = Mock()
        mock_keycloak.userinfo.return_value = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "name": "Test User",
            "realm_access": {"roles": ["admin", "user"]},
            "groups": ["management"],
        }
        mock_keycloak_class.return_value = mock_keycloak

        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When: ユーザー情報取得
        userinfo = client.get_userinfo("valid-access-token")

        # Then: 完全な情報が取得される
        assert userinfo["email"] == "test@example.com"
        assert userinfo["name"] == "Test User"
        assert userinfo["realm_access"]["roles"] == ["admin", "user"]
        assert userinfo["groups"] == ["management"]

    @patch("app.core.keycloak.KeycloakOpenID")
    def test_refresh_token(self, mock_keycloak_class: Mock) -> None:
        """リフレッシュトークンで新しいトークンを取得できることを確認."""
        # Given: 有効なリフレッシュトークン
        mock_keycloak = Mock()
        mock_keycloak.refresh_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
        mock_keycloak_class.return_value = mock_keycloak

        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When: トークンリフレッシュ
        new_tokens = client.refresh_token("valid-refresh-token")

        # Then: 新しいトークンが取得される
        assert new_tokens["access_token"] == "new-access-token"
        assert new_tokens["refresh_token"] == "new-refresh-token"

    @patch("app.core.keycloak.KeycloakOpenID")
    def test_logout(self, mock_keycloak_class: Mock) -> None:
        """ログアウトが正しく実行されることを確認."""
        # Given: 有効なリフレッシュトークン
        mock_keycloak = Mock()
        mock_keycloak.logout.return_value = None
        mock_keycloak_class.return_value = mock_keycloak

        settings = create_test_settings(
            KEYCLOAK_SERVER_URL="http://localhost:8080",
            KEYCLOAK_REALM="test-realm",
            KEYCLOAK_CLIENT_ID="test-client",
            KEYCLOAK_CLIENT_SECRET="test-secret",
        )
        client = KeycloakClient(settings)

        # When: ログアウト
        client.logout("valid-refresh-token")

        # Then: ログアウトが呼ばれる
        mock_keycloak.logout.assert_called_once_with("valid-refresh-token")


class TestPKCEFunctions:
    """Test cases for PKCE-related functions."""

    def test_pkce_challenge_generation(self) -> None:
        """TEST-KC-003: PKCEチャレンジが正しく生成されることを確認."""
        # When: PKCEペア生成
        verifier, challenge = generate_pkce_pair()

        # Then: Verifierが43-128文字、ChallengeがBase64URL形式
        assert 43 <= len(verifier) <= 128
        assert is_base64url(challenge)
        
        # Verifierは有効な文字のみ含む
        valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        assert all(c in valid_chars for c in verifier)

    def test_pkce_verification(self) -> None:
        """PKCEペアが正しく検証されることを確認."""
        # Given: PKCEペア
        verifier, challenge = generate_pkce_pair()

        # When/Then: VerifierからChallengeが導出可能
        assert verify_pkce_pair(verifier, challenge) is True

    def test_pkce_verification_invalid(self) -> None:
        """不正なPKCEペアが拒否されることを確認."""
        # Given: 異なるverifierとchallenge
        verifier1, _ = generate_pkce_pair()
        _, challenge2 = generate_pkce_pair()

        # When/Then: 検証失敗
        assert verify_pkce_pair(verifier1, challenge2) is False

    def test_is_base64url(self) -> None:
        """Base64URL形式の検証が正しく動作することを確認."""
        # Valid base64url strings
        assert is_base64url("abc123-_") is True
        assert is_base64url("") is True
        
        # Invalid strings (contains invalid characters)
        assert is_base64url("abc+123") is False  # + is not valid in base64url
        assert is_base64url("abc/123") is False  # / is not valid in base64url
        assert is_base64url("abc=") is False     # = padding is not valid in base64url
        assert is_base64url("abc 123") is False  # space is not valid


class TestKeycloakExceptions:
    """Test cases for Keycloak exceptions."""

    def test_invalid_token_error(self) -> None:
        """InvalidTokenErrorが正しく動作することを確認."""
        error = InvalidTokenError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_authentication_error(self) -> None:
        """AuthenticationErrorが正しく動作することを確認."""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert isinstance(error, Exception)