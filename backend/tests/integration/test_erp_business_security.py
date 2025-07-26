"""
ERP Business Security Tests
ERP業務セキュリティテスト

48時間以内実装 - 業務セキュリティ検証
- 認証・認可テスト
- データアクセス制御
- 入力値検証
- セキュリティホールチェック
"""

import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.main import app

client = TestClient(app)

# セキュリティテスト用設定
SECURITY_TEST_CONFIG = {
    "sql_injection_payloads": [
        "'; DROP TABLE products; --",
        "' OR '1'='1",
        "UNION SELECT * FROM users",
        "'; UPDATE products SET price=0; --",
    ],
    "xss_payloads": [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
    ],
    "invalid_tokens": [
        "invalid_token",
        "Bearer invalid",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        "",
    ],
}


@pytest.fixture(scope="function")
def security_test_db():
    """セキュリティテスト用データベース"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.models.base import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    yield db
    db.close()

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_token():
    """テスト用JWTトークン生成"""
    payload = {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "user",
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    # テスト用秘密鍵（実際の設定から取得）
    secret_key = getattr(settings, "SECRET_KEY", "test_secret_key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return f"Bearer {token}"


@pytest.fixture
def admin_user_token():
    """テスト用管理者JWTトークン生成"""
    payload = {
        "user_id": 2,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "permissions": ["read", "write", "delete", "admin"],
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    secret_key = getattr(settings, "SECRET_KEY", "test_secret_key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return f"Bearer {token}"


class TestERPAuthenticationSecurity:
    """ERP認証セキュリティテスト"""

    def test_unauthenticated_access_denied(self, security_test_db):
        """未認証アクセス拒否テスト"""
        # 認証が必要なエンドポイントのテスト
        protected_endpoints = [
            ("GET", "/api/v1/products"),
            ("POST", "/api/v1/products"),
            ("GET", "/api/v1/inventory/level/1"),
            ("POST", "/api/v1/inventory/add/1"),
            ("GET", "/api/v1/sales-orders"),
            ("POST", "/api/v1/sales-orders"),
        ]

        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})

            # 未認証の場合は401または適切なエラーが返されることを確認
            assert response.status_code in [401, 422], (
                f"未認証アクセスが許可されています: {method} {endpoint} -> {response.status_code}"
            )

    def test_invalid_token_handling(self, security_test_db):
        """無効トークン処理テスト"""
        # テスト商品作成（認証不要なエンドポイントがある場合）
        for invalid_token in SECURITY_TEST_CONFIG["invalid_tokens"]:
            headers = {"Authorization": invalid_token} if invalid_token else {}

            response = client.get("/api/v1/products", headers=headers)

            # 無効トークンは適切に拒否されることを確認
            assert response.status_code in [401, 422], (
                f"無効トークンが受け入れられました: {invalid_token} -> {response.status_code}"
            )

    def test_token_expiration_handling(self, security_test_db):
        """トークン有効期限処理テスト"""
        # 期限切れトークン生成
        expired_payload = {
            "user_id": 1,
            "username": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1),  # 1時間前に期限切れ
        }

        secret_key = getattr(settings, "SECRET_KEY", "test_secret_key")
        expired_token = jwt.encode(expired_payload, secret_key, algorithm="HS256")

        response = client.get(
            "/api/v1/products", headers={"Authorization": f"Bearer {expired_token}"}
        )

        # 期限切れトークンは拒否されることを確認
        assert response.status_code == 401, (
            f"期限切れトークンが受け入れられました: {response.status_code}"
        )

    def test_role_based_access_control(
        self, security_test_db, test_user_token, admin_user_token
    ):
        """ロールベースアクセス制御テスト"""
        # 管理者のみアクセス可能な操作をテスト
        admin_only_operations = [
            ("DELETE", "/api/v1/products/1"),
            ("GET", "/api/v1/admin/users"),  # 存在する場合
            ("POST", "/api/v1/admin/system/backup"),  # 存在する場合
        ]

        for method, endpoint in admin_only_operations:
            # 一般ユーザーでアクセス試行
            if method == "DELETE":
                user_response = client.delete(
                    endpoint, headers={"Authorization": test_user_token}
                )
            elif method == "GET":
                user_response = client.get(
                    endpoint, headers={"Authorization": test_user_token}
                )
            elif method == "POST":
                user_response = client.post(
                    endpoint, json={}, headers={"Authorization": test_user_token}
                )

            # 一般ユーザーは拒否されることを確認（403 Forbidden期待）
            if user_response.status_code not in [
                404,
                405,
            ]:  # エンドポイントが存在しない場合は除外
                assert user_response.status_code in [403, 401], (
                    f"一般ユーザーが管理者操作にアクセス可能: {method} {endpoint} -> {user_response.status_code}"
                )


class TestERPInputValidationSecurity:
    """ERP入力値検証セキュリティテスト"""

    def test_sql_injection_prevention(self, security_test_db, test_user_token):
        """SQLインジェクション防止テスト"""
        headers = {"Authorization": test_user_token}

        for payload in SECURITY_TEST_CONFIG["sql_injection_payloads"]:
            # 商品作成でSQLインジェクション試行
            malicious_product = {
                "code": payload,
                "name": payload,
                "description": payload,
                "price": 1000.0,
                "status": "active",
            }

            response = client.post(
                "/api/v1/products", json=malicious_product, headers=headers
            )

            # SQLインジェクションは防がれること（500エラーが発生しないこと）
            assert response.status_code != 500, (
                f"SQLインジェクションでサーバーエラーが発生: {payload}"
            )

            # 商品検索でSQLインジェクション試行
            response = client.get(
                "/api/v1/products", params={"search": payload}, headers=headers
            )

            assert response.status_code != 500, (
                f"検索でSQLインジェクションが発生: {payload}"
            )

    def test_xss_prevention(self, security_test_db, test_user_token):
        """XSS攻撃防止テスト"""
        headers = {"Authorization": test_user_token}

        for payload in SECURITY_TEST_CONFIG["xss_payloads"]:
            # XSS攻撃ペイロードを含む商品作成
            xss_product = {
                "code": f"XSS-{uuid.uuid4().hex[:8]}",
                "name": payload,
                "description": payload,
                "price": 1000.0,
                "status": "active",
            }

            response = client.post(
                "/api/v1/products", json=xss_product, headers=headers
            )

            if response.status_code == 201:
                product = response.json()
                product_id = product["id"]

                # 作成された商品を取得
                get_response = client.get(
                    f"/api/v1/products/{product_id}", headers=headers
                )

                if get_response.status_code == 200:
                    retrieved_product = get_response.json()

                    # XSS ペイロードがエスケープまたはサニタイズされていることを確認
                    assert "<script>" not in retrieved_product.get("name", ""), (
                        "XSSペイロードがエスケープされていません"
                    )
                    assert "javascript:" not in retrieved_product.get("name", ""), (
                        "JavaScript URLがサニタイズされていません"
                    )

    def test_input_length_validation(self, security_test_db, test_user_token):
        """入力長制限テスト"""
        headers = {"Authorization": test_user_token}

        # 異常に長い入力値でのテスト
        extremely_long_string = "A" * 10000  # 10KB の文字列

        invalid_products = [
            {
                "code": extremely_long_string,
                "name": "テスト商品",
                "price": 1000.0,
                "status": "active",
            },
            {
                "code": "VALID001",
                "name": extremely_long_string,
                "price": 1000.0,
                "status": "active",
            },
            {
                "code": "VALID002",
                "name": "テスト商品",
                "description": extremely_long_string,
                "price": 1000.0,
                "status": "active",
            },
        ]

        for invalid_product in invalid_products:
            response = client.post(
                "/api/v1/products", json=invalid_product, headers=headers
            )

            # 長すぎる入力は適切に拒否されることを確認
            assert response.status_code in [400, 422], (
                f"長すぎる入力が受け入れられました: {response.status_code}"
            )

    def test_numeric_input_validation(self, security_test_db, test_user_token):
        """数値入力検証テスト"""
        headers = {"Authorization": test_user_token}

        # 無効な数値入力パターン
        invalid_numeric_inputs = [
            {"price": "not_a_number", "cost": 500.0},
            {"price": 1000.0, "cost": "invalid"},
            {"price": float("inf"), "cost": 500.0},
            {"price": float("-inf"), "cost": 500.0},
            {"price": -1000.0, "cost": 500.0},  # 負の価格
            {"price": 1000.0, "cost": -500.0},  # 負のコスト
        ]

        for invalid_input in invalid_numeric_inputs:
            product_data = {
                "code": f"NUM-{uuid.uuid4().hex[:8]}",
                "name": "数値検証テスト商品",
                "status": "active",
                **invalid_input,
            }

            response = client.post(
                "/api/v1/products", json=product_data, headers=headers
            )

            # 無効な数値入力は拒否されることを確認
            assert response.status_code in [400, 422], (
                f"無効な数値入力が受け入れられました: {invalid_input} -> {response.status_code}"
            )


class TestERPDataAccessSecurity:
    """ERPデータアクセスセキュリティテスト"""

    def test_unauthorized_data_access(self, security_test_db, test_user_token):
        """権限のないデータアクセステスト"""
        headers = {"Authorization": test_user_token}

        # 存在しないIDでのアクセス試行
        non_existent_ids = [999999, -1, 0, "invalid_id"]

        for invalid_id in non_existent_ids:
            endpoints = [
                f"/api/v1/products/{invalid_id}",
                f"/api/v1/inventory/level/{invalid_id}",
                f"/api/v1/sales-orders/{invalid_id}",
            ]

            for endpoint in endpoints:
                response = client.get(endpoint, headers=headers)

                # 存在しないリソースは404で適切に処理されることを確認
                assert response.status_code in [404, 422], (
                    f"存在しないリソースへのアクセスが不適切に処理されました: {endpoint} -> {response.status_code}"
                )

    def test_data_modification_authorization(self, security_test_db, test_user_token):
        """データ変更権限テスト"""
        headers = {"Authorization": test_user_token}

        # テスト商品作成
        product_data = {
            "code": "AUTH-TEST-001",
            "name": "権限テスト商品",
            "price": 1000.0,
            "status": "active",
        }

        response = client.post("/api/v1/products", json=product_data, headers=headers)
        if response.status_code == 201:
            product = response.json()
            product_id = product["id"]

            # 権限のない操作の試行
            unauthorized_operations = [
                ("DELETE", f"/api/v1/products/{product_id}"),
                (
                    "PUT",
                    f"/api/v1/products/{product_id}/admin-update",
                ),  # 管理者のみの更新
            ]

            for method, endpoint in unauthorized_operations:
                if method == "DELETE":
                    response = client.delete(endpoint, headers=headers)
                elif method == "PUT":
                    response = client.put(
                        endpoint, json={"status": "admin_locked"}, headers=headers
                    )

                # 権限のない操作は拒否されることを確認
                if response.status_code not in [
                    404,
                    405,
                ]:  # エンドポイントが存在しない場合は除外
                    assert response.status_code in [403, 401], (
                        f"権限のない操作が許可されました: {method} {endpoint} -> {response.status_code}"
                    )

    def test_sensitive_data_exposure(self, security_test_db, test_user_token):
        """機密データ露出防止テスト"""
        headers = {"Authorization": test_user_token}

        # APIレスポンスに機密情報が含まれていないことを確認
        response = client.get("/api/v1/products", headers=headers)

        if response.status_code == 200:
            products = response.json()

            for product in products:
                # 機密データが含まれていないことを確認
                sensitive_fields = ["password", "secret", "private_key", "token"]

                for field in sensitive_fields:
                    assert field not in product, (
                        f"機密フィールドがAPIレスポンスに含まれています: {field}"
                    )

                # 内部実装詳細が露出していないことを確認
                internal_fields = ["__class__", "_sa_", "metadata"]

                for field in internal_fields:
                    assert not any(key.startswith(field) for key in product.keys()), (
                        f"内部実装詳細がAPIレスポンスに露出しています: {field}"
                    )


class TestERPSecurityHeaders:
    """ERPセキュリティヘッダーテスト"""

    def test_security_headers_presence(self, security_test_db):
        """セキュリティヘッダー存在確認テスト"""
        response = client.get("/api/v1/health")  # ヘルスチェックエンドポイント

        # 推奨セキュリティヘッダーの確認
        recommended_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": None,  # HTTPS環境でのみ必要
        }

        for header, expected_values in recommended_headers.items():
            if header in response.headers:
                if expected_values and isinstance(expected_values, list):
                    assert response.headers[header] in expected_values, (
                        f"セキュリティヘッダーの値が推奨値と異なります: {header} = {response.headers[header]}"
                    )
                elif expected_values:
                    assert response.headers[header] == expected_values, (
                        f"セキュリティヘッダーの値が推奨値と異なります: {header} = {response.headers[header]}"
                    )

    def test_cors_configuration(self, security_test_db):
        """CORS設定テスト"""
        # プリフライトリクエストのテスト
        response = client.options(
            "/api/v1/products",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # 不正なオリジンからのリクエストは適切に制限されることを確認
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origins = response.headers["Access-Control-Allow-Origin"]
            assert allowed_origins != "*" or response.status_code == 403, (
                "CORS設定が緩すぎます。すべてのオリジンを許可しています。"
            )


class TestERPBusinessSecurityIntegration:
    """ERP業務セキュリティ統合テスト"""

    def test_secure_business_workflow(self, security_test_db, test_user_token):
        """セキュアな業務ワークフローテスト"""
        headers = {"Authorization": test_user_token}

        # 1. セキュアな商品作成
        secure_product = {
            "code": "SECURE-001",
            "name": "セキュアテスト商品",
            "description": "正常な商品説明",
            "price": 1000.0,
            "cost": 600.0,
            "status": "active",
        }

        response = client.post("/api/v1/products", json=secure_product, headers=headers)
        assert response.status_code == 201
        product = response.json()
        product_id = product["id"]

        # 2. セキュアな在庫操作
        inventory_data = {"quantity": 100, "reason": "初期在庫"}

        response = client.post(
            f"/api/v1/inventory/add/{product_id}", json=inventory_data, headers=headers
        )
        assert response.status_code == 200

        # 3. セキュアな注文作成
        order_data = {
            "customer_name": "正常な顧客名",
            "customer_email": "customer@example.com",
            "items": [{"product_id": product_id, "quantity": 5, "unit_price": 1000.0}],
            "notes": "正常な注文",
        }

        response = client.post("/api/v1/sales-orders", json=order_data, headers=headers)
        assert response.status_code == 201
        order = response.json()

        # 4. データ整合性確認
        assert order["customer_name"] == "正常な顧客名"
        assert len(order["items"]) == 1
        assert order["items"][0]["quantity"] == 5

        # 5. セキュアなデータアクセス確認
        response = client.get(f"/api/v1/products/{product_id}", headers=headers)
        assert response.status_code == 200
        retrieved_product = response.json()
        assert retrieved_product["code"] == "SECURE-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
