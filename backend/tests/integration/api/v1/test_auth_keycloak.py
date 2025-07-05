"""
Keycloak authentication API integration tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

import pytest
import time
from unittest.mock import patch, Mock
from typing import Dict, Any, Generator
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.keycloak import KeycloakClient
from app.core.config import get_settings
from tests.utils.keycloak import (
    mock_keycloak_token_exchange,
    mock_keycloak_token_refresh,
    mock_keycloak_userinfo,
    create_keycloak_token_with_roles,
)


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_keycloak_client() -> Generator[Mock, None, None]:
    """Create mock Keycloak client."""
    with patch("app.api.v1.auth_keycloak.get_keycloak_client") as mock:
        yield mock.return_value


class TestKeycloakAuthenticationAPI:
    """Test cases for Keycloak authentication endpoints."""

    def test_keycloak_login_redirect(self, client: TestClient) -> None:
        """TEST-API-KC-001: Keycloak認証URLへのリダイレクトを確認."""
        # When: ログインエンドポイント呼び出し
        response = client.get("/api/v1/auth/keycloak/login")

        # Then: ステータス302、Location headerにKeycloak URL、stateパラメータ存在
        assert response.status_code == 302
        location = response.headers["Location"]
        assert "http://localhost:8080/auth/realms/itdo-erp" in location
        assert "state=" in location
        assert "client_id=" in location
        assert "response_type=code" in location
        assert "redirect_uri=" in location

    def test_keycloak_login_with_redirect_uri(self, client: TestClient) -> None:
        """カスタムリダイレクトURIでの認証開始を確認."""
        # When: カスタムリダイレクトURI付きでログイン
        response = client.get(
            "/api/v1/auth/keycloak/login",
            params={"redirect_uri": "http://localhost:3000/dashboard"},
        )

        # Then: リダイレクトURIがセッションに保存される
        assert response.status_code == 302
        # Note: セッション確認は実装時に追加

    def test_keycloak_callback_success(
        self, client: TestClient, mock_keycloak_client: Mock
    ) -> None:
        """TEST-API-KC-002: Keycloakコールバックが正しく処理されることを確認."""
        # Given: 有効な認可コード
        mock_keycloak_client.exchange_code.return_value = {
            "access_token": "keycloak-access-token",
            "refresh_token": "keycloak-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
        mock_keycloak_client.get_userinfo.return_value = {
            "sub": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "realm_access": {"roles": ["user"]},
        }

        # When: コールバックエンドポイント呼び出し
        response = client.post(
            "/api/v1/auth/keycloak/callback",
            json={"code": "valid-auth-code", "state": "valid-state"},
        )

        # Then: ステータス200、JWTトークン返却
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "refresh_token" in data

    def test_invalid_state_parameter(self, client: TestClient) -> None:
        """TEST-API-KC-003: 無効なstateパラメータが拒否されることを確認."""
        # When: 不正なstateでコールバック
        response = client.post(
            "/api/v1/auth/keycloak/callback",
            json={"code": "auth-code", "state": "invalid-state"},
        )

        # Then: エラーレスポンス
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_STATE"
        assert "Invalid state parameter" in response.json()["detail"]

    def test_keycloak_callback_missing_code(self, client: TestClient) -> None:
        """認可コードなしのコールバックが拒否されることを確認."""
        # When: codeパラメータなしでコールバック
        response = client.post(
            "/api/v1/auth/keycloak/callback", json={"state": "valid-state"}
        )

        # Then: バリデーションエラー
        assert response.status_code == 422

    def test_keycloak_token_exchange_failure(
        self, client: TestClient, mock_keycloak_client: Mock
    ) -> None:
        """Keycloakトークン交換失敗時のエラー処理を確認."""
        # Given: トークン交換エラー
        mock_keycloak_client.exchange_code.side_effect = Exception(
            "Token exchange failed"
        )

        # When: コールバック処理
        response = client.post(
            "/api/v1/auth/keycloak/callback",
            json={"code": "auth-code", "state": "valid-state"},
        )

        # Then: 認証エラー
        assert response.status_code == 401
        assert response.json()["code"] == "AUTH_FAILED"

    def test_keycloak_userinfo_endpoint(self, client: TestClient) -> None:
        """Keycloakユーザー情報エンドポイントの動作を確認."""
        # Given: 有効なトークン
        token = create_keycloak_token_with_roles(["user"])

        # When: ユーザー情報取得
        with mock_keycloak_userinfo():
            response = client.get(
                "/api/v1/auth/keycloak/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )

        # Then: ユーザー情報返却
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data
        assert "roles" in data

    def test_keycloak_refresh_token(
        self, client: TestClient, mock_keycloak_client: Mock
    ) -> None:
        """TEST-API-KC-006: リフレッシュトークンで新しいトークンを取得できることを確認."""
        # Given: 有効なリフレッシュトークン
        mock_keycloak_client.refresh_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }

        # When: リフレッシュエンドポイント呼び出し
        response = client.post(
            "/api/v1/auth/keycloak/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

        # Then: 新しいトークン取得
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-access-token"
        assert data["refresh_token"] == "new-refresh-token"

    def test_keycloak_logout(
        self, client: TestClient, mock_keycloak_client: Mock
    ) -> None:
        """Keycloakログアウトが正しく処理されることを確認."""
        # Given: 有効なトークン
        token = create_keycloak_token_with_roles(["user"])

        # When: ログアウトエンドポイント呼び出し
        response = client.post(
            "/api/v1/auth/keycloak/logout",
            json={"refresh_token": "valid-refresh-token"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Then: ログアウト成功
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"


class TestKeycloakRoleBasedAccess:
    """Test cases for role-based access control."""

    def test_admin_role_access(self, client: TestClient) -> None:
        """TEST-API-KC-004: 管理者ロールで管理機能にアクセスできることを確認."""
        # Given: 管理者トークン
        admin_token = create_keycloak_token_with_roles(["admin"])

        # When: 管理APIアクセス
        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Then: アクセス成功
        assert response.status_code == 200

    def test_insufficient_permissions(self, client: TestClient) -> None:
        """TEST-API-KC-005: 権限不足でアクセスが拒否されることを確認."""
        # Given: 一般ユーザートークン
        user_token = create_keycloak_token_with_roles(["user"])

        # When: 管理APIアクセス試行
        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {user_token}"}
        )

        # Then: アクセス拒否
        assert response.status_code == 403
        assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_multiple_roles_access(self, client: TestClient) -> None:
        """複数ロールを持つユーザーのアクセス権限を確認."""
        # Given: 複数ロールを持つトークン
        multi_role_token = create_keycloak_token_with_roles(["user", "manager"])

        # When: マネージャーAPIアクセス
        response = client.get(
            "/api/v1/manager/reports",
            headers={"Authorization": f"Bearer {multi_role_token}"},
        )

        # Then: アクセス成功
        assert response.status_code == 200


class TestKeycloakSecurity:
    """Test cases for Keycloak security features."""

    def test_csrf_state_validation(self, client: TestClient) -> None:
        """TEST-SEC-KC-001: CSRF対策のstate検証が機能することを確認."""
        # Given: セッションに保存されたstate（実装時にモック化）
        # When: 異なるstateでコールバック
        response = client.post(
            "/api/v1/auth/keycloak/callback",
            json={"code": "auth-code", "state": "different-state"},
        )

        # Then: リクエスト拒否
        assert response.status_code == 400
        assert "Invalid state" in response.json()["detail"]

    def test_https_redirect_enforcement(self, client: TestClient) -> None:
        """TEST-SEC-KC-002: 本番環境でHTTPSが強制されることを確認."""
        # Given: 本番環境設定
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.ENVIRONMENT = "production"
            mock_settings.return_value.KEYCLOAK_SERVER_URL = "https://keycloak.itdo-erp.jp"

            # When: HTTPでアクセス
            response = client.get(
                "/api/v1/auth/keycloak/login",
                headers={"X-Forwarded-Proto": "http"},
            )

            # Then: HTTPSへリダイレクト
            assert response.status_code in [301, 307]

    def test_token_validation_security(self, client: TestClient) -> None:
        """改ざんされたトークンが拒否されることを確認."""
        # Given: 改ざんされたトークン
        tampered_token = "tampered.jwt.token"

        # When: API呼び出し
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {tampered_token}"}
        )

        # Then: 認証エラー
        assert response.status_code == 401


class TestKeycloakPerformance:
    """Test cases for Keycloak performance requirements."""

    def test_auth_initiation_performance(self, client: TestClient) -> None:
        """TEST-PERF-KC-001: 認証開始が100ms以内に応答することを確認."""
        start_time = time.time()

        response = client.get("/api/v1/auth/keycloak/login")

        response_time = (time.time() - start_time) * 1000
        assert response_time < 100
        assert response.status_code == 302

    def test_token_validation_performance(
        self, client: TestClient, mock_keycloak_client: Mock
    ) -> None:
        """TEST-PERF-KC-002: トークン検証が50ms以内に完了することを確認."""
        # Given: キャッシュされたトークン検証
        mock_keycloak_client.verify_token.return_value = {
            "sub": "user-123",
            "email": "test@example.com",
        }
        token = create_keycloak_token_with_roles(["user"])

        start_time = time.time()

        # When: トークン検証を含むAPI呼び出し
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )

        validation_time = (time.time() - start_time) * 1000
        assert validation_time < 50
        assert response.status_code == 200


class TestKeycloakErrorHandling:
    """Test cases for Keycloak error handling."""

    def test_keycloak_unavailable(
        self, client: TestClient, mock_keycloak_client: Mock
    ) -> None:
        """TEST-ERR-KC-001: Keycloakが利用不可の場合の処理を確認."""
        # Given: Keycloakサーバーダウン
        mock_keycloak_client.get_auth_url.side_effect = Exception(
            "Connection refused"
        )

        # When: 認証試行
        response = client.get("/api/v1/auth/keycloak/login")

        # Then: 適切なエラーレスポンス
        assert response.status_code == 503
        assert response.json()["code"] == "KEYCLOAK_UNAVAILABLE"
        assert "Keycloak service is temporarily unavailable" in response.json()["detail"]

    def test_error_response_format(self, client: TestClient) -> None:
        """エラーレスポンスが統一形式であることを確認."""
        # When: 無効なリクエスト
        response = client.post("/api/v1/auth/keycloak/callback", json={})

        # Then: 統一エラー形式
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error
        # エラー形式の詳細は実装時に調整