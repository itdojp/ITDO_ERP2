# Keycloak連携テスト仕様書

**文書番号**: ITDO-ERP-TS-KEYCLOAK-001  
**バージョン**: 1.0  
**作成日**: 2025年7月5日  
**作成者**: Claude Code AI  

---

## 1. テスト概要

### 1.1 テスト目的
Keycloak連携機能が仕様通りに動作し、セキュリティ要件を満たすことを検証する。

### 1.2 テスト範囲
- OAuth2/OpenID Connect認証フロー
- トークン管理機能
- ロールベースアクセス制御
- 既存認証との統合

### 1.3 テスト環境
- Keycloak 23.0（テストコンテナ）
- Python 3.13 + pytest
- モックサーバー（Keycloak API模擬）

---

## 2. 単体テスト仕様

### 2.1 Keycloakクライアントテスト

#### TEST-KC-001: クライアント初期化テスト
```python
def test_keycloak_client_initialization() -> None:
    """Keycloakクライアントが正しく初期化されることを確認"""
    # Given: Keycloak設定
    settings = Settings(
        KEYCLOAK_SERVER_URL="http://localhost:8080",
        KEYCLOAK_REALM="test-realm",
        KEYCLOAK_CLIENT_ID="test-client",
        KEYCLOAK_CLIENT_SECRET="test-secret"
    )
    
    # When: クライアント初期化
    client = KeycloakClient(settings)
    
    # Then: 
    # - クライアントが作成される
    # - 設定が正しく適用される
    assert client.keycloak_openid is not None
    assert client.realm_name == "test-realm"
```

#### TEST-KC-002: 認証URL生成テスト
```python
def test_generate_auth_url() -> None:
    """認証URLが正しく生成されることを確認"""
    # Given: Keycloakクライアント
    client = create_test_keycloak_client()
    
    # When: 認証URL生成
    auth_url = client.get_auth_url(
        redirect_uri="http://localhost:8000/callback",
        state="test-state-123"
    )
    
    # Then:
    # - URLが生成される
    # - 必要なパラメータが含まれる
    assert "http://localhost:8080/auth/realms/test-realm/protocol/openid-connect/auth" in auth_url
    assert "client_id=test-client" in auth_url
    assert "state=test-state-123" in auth_url
    assert "response_type=code" in auth_url
```

#### TEST-KC-003: PKCEチャレンジ生成テスト
```python
def test_pkce_challenge_generation() -> None:
    """PKCEチャレンジが正しく生成されることを確認"""
    # When: PKCEペア生成
    verifier, challenge = generate_pkce_pair()
    
    # Then:
    # - Verifierが43-128文字
    # - ChallengeがBase64URL形式
    # - VerifierからChallengeが導出可能
    assert 43 <= len(verifier) <= 128
    assert is_base64url(challenge)
    assert verify_pkce_pair(verifier, challenge)
```

### 2.2 トークン管理テスト

#### TEST-KC-004: トークン交換テスト
```python
def test_exchange_code_for_token() -> None:
    """認可コードをトークンに交換できることを確認"""
    # Given: モックKeycloakレスポンス
    mock_response = {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "expires_in": 300,
        "token_type": "Bearer"
    }
    
    # When: トークン交換
    with mock_keycloak_response(mock_response):
        tokens = client.exchange_code(
            code="test-auth-code",
            redirect_uri="http://localhost:8000/callback"
        )
    
    # Then: トークンが取得される
    assert tokens["access_token"] == "mock-access-token"
    assert tokens["refresh_token"] == "mock-refresh-token"
```

#### TEST-KC-005: トークン検証テスト
```python
def test_verify_keycloak_token() -> None:
    """Keycloakトークンが正しく検証されることを確認"""
    # Given: 有効なトークン
    valid_token = create_mock_keycloak_token()
    
    # When: トークン検証
    userinfo = verify_keycloak_token(valid_token)
    
    # Then: ユーザー情報が取得される
    assert userinfo["sub"] == "test-user-id"
    assert userinfo["email"] == "test@example.com"
    assert "admin" in userinfo["roles"]
```

#### TEST-KC-006: 無効トークン検証テスト
```python
def test_verify_invalid_token() -> None:
    """無効なトークンが拒否されることを確認"""
    # Given: 無効なトークン
    invalid_token = "invalid-token-string"
    
    # When/Then: 検証時に例外発生
    with pytest.raises(InvalidTokenError):
        verify_keycloak_token(invalid_token)
```

### 2.3 ユーザー情報取得テスト

#### TEST-KC-007: ユーザー情報取得テスト
```python
def test_get_userinfo() -> None:
    """ユーザー情報が正しく取得されることを確認"""
    # Given: 認証済みトークン
    token = "valid-access-token"
    
    # When: ユーザー情報取得
    with mock_keycloak_userinfo():
        userinfo = client.get_userinfo(token)
    
    # Then: 完全な情報が取得される
    assert userinfo["email"] == "test@example.com"
    assert userinfo["name"] == "Test User"
    assert userinfo["roles"] == ["admin", "user"]
    assert userinfo["groups"] == ["management"]
```

---

## 3. 結合テスト仕様

### 3.1 認証フローテスト

#### TEST-API-KC-001: Keycloak認証開始テスト
```python
def test_keycloak_login_redirect() -> None:
    """Keycloak認証URLへのリダイレクトを確認"""
    # When: ログインエンドポイント呼び出し
    response = client.get("/api/v1/auth/keycloak/login")
    
    # Then:
    # - ステータス302
    # - Location headerにKeycloak URL
    # - stateパラメータ存在
    assert response.status_code == 302
    location = response.headers["Location"]
    assert "http://localhost:8080/auth/realms/itdo-erp" in location
    assert "state=" in location
```

#### TEST-API-KC-002: コールバック成功テスト
```python
def test_keycloak_callback_success() -> None:
    """Keycloakコールバックが正しく処理されることを確認"""
    # Given: 有効な認可コード
    auth_code = "valid-auth-code"
    state = "valid-state"
    
    # When: コールバックエンドポイント呼び出し
    with mock_keycloak_token_exchange():
        response = client.post("/api/v1/auth/keycloak/callback", json={
            "code": auth_code,
            "state": state
        })
    
    # Then:
    # - ステータス200
    # - JWTトークン返却
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

#### TEST-API-KC-003: 無効なstateパラメータテスト
```python
def test_invalid_state_parameter() -> None:
    """無効なstateパラメータが拒否されることを確認"""
    # When: 不正なstateでコールバック
    response = client.post("/api/v1/auth/keycloak/callback", json={
        "code": "auth-code",
        "state": "invalid-state"
    })
    
    # Then: エラーレスポンス
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_STATE"
```

### 3.2 ロールベースアクセス制御テスト

#### TEST-API-KC-004: 管理者権限テスト
```python
def test_admin_role_access() -> None:
    """管理者ロールで管理機能にアクセスできることを確認"""
    # Given: 管理者トークン
    admin_token = create_keycloak_token_with_roles(["admin"])
    
    # When: 管理APIアクセス
    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then: アクセス成功
    assert response.status_code == 200
```

#### TEST-API-KC-005: 権限不足テスト
```python
def test_insufficient_permissions() -> None:
    """権限不足でアクセスが拒否されることを確認"""
    # Given: 一般ユーザートークン
    user_token = create_keycloak_token_with_roles(["user"])
    
    # When: 管理APIアクセス試行
    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Then: アクセス拒否
    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"
```

### 3.3 トークンリフレッシュテスト

#### TEST-API-KC-006: トークンリフレッシュ成功テスト
```python
def test_token_refresh_success() -> None:
    """リフレッシュトークンで新しいトークンを取得できることを確認"""
    # Given: 有効なリフレッシュトークン
    refresh_token = "valid-refresh-token"
    
    # When: リフレッシュエンドポイント呼び出し
    with mock_keycloak_token_refresh():
        response = client.post("/api/v1/auth/keycloak/refresh", json={
            "refresh_token": refresh_token
        })
    
    # Then: 新しいトークン取得
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

---

## 4. セキュリティテスト仕様

### 4.1 CSRF対策テスト

#### TEST-SEC-KC-001: State検証テスト
```python
def test_csrf_state_validation() -> None:
    """CSRF対策のstate検証が機能することを確認"""
    # Given: セッションに保存されたstate
    session_state = "secure-random-state"
    
    # When: 異なるstateでコールバック
    response = client.post("/api/v1/auth/keycloak/callback", json={
        "code": "auth-code",
        "state": "different-state"
    })
    
    # Then: リクエスト拒否
    assert response.status_code == 400
    assert "Invalid state" in response.json()["detail"]
```

### 4.2 トークン漏洩対策テスト

#### TEST-SEC-KC-002: HTTPSリダイレクトテスト
```python
def test_https_redirect_enforcement() -> None:
    """本番環境でHTTPSが強制されることを確認"""
    # Given: 本番環境設定
    with production_settings():
        # When: HTTPでアクセス
        response = client.get(
            "http://api.itdo-erp.jp/api/v1/auth/keycloak/login"
        )
        
        # Then: HTTPSへリダイレクト
        assert response.status_code == 301
        assert response.headers["Location"].startswith("https://")
```

---

## 5. パフォーマンステスト仕様

### 5.1 応答時間テスト

#### TEST-PERF-KC-001: 認証開始応答時間
```python
def test_auth_initiation_performance() -> None:
    """認証開始が100ms以内に応答することを確認"""
    start_time = time.time()
    
    response = client.get("/api/v1/auth/keycloak/login")
    
    response_time = (time.time() - start_time) * 1000
    assert response_time < 100
```

#### TEST-PERF-KC-002: トークン検証応答時間
```python
def test_token_validation_performance() -> None:
    """トークン検証が50ms以内に完了することを確認"""
    token = create_test_token()
    
    start_time = time.time()
    verify_keycloak_token(token)
    
    validation_time = (time.time() - start_time) * 1000
    assert validation_time < 50
```

### 5.2 負荷テスト

#### TEST-PERF-KC-003: 並行認証テスト
```python
def test_concurrent_authentications() -> None:
    """100並行認証リクエストが処理できることを確認"""
    # 100スレッドで同時認証
    # 95%以上の成功率を確認
```

---

## 6. 統合テスト仕様

### 6.1 既存認証との共存テスト

#### TEST-INT-KC-001: 認証方式切り替えテスト
```python
def test_auth_method_switching() -> None:
    """既存認証とKeycloak認証が共存することを確認"""
    # Given: 両方の認証が有効
    
    # When/Then: 既存認証でログイン可能
    response = client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "password"
    })
    assert response.status_code == 200
    
    # When/Then: Keycloak認証でもログイン可能
    response = client.get("/api/v1/auth/keycloak/login")
    assert response.status_code == 302
```

### 6.2 セッション管理テスト

#### TEST-INT-KC-002: クロスオリジントークン検証
```python
def test_cross_origin_token_validation() -> None:
    """異なるオリジンからのトークンが検証されることを確認"""
    # Keycloakトークンが内部JWTに変換され
    # 既存のAPIで使用可能なことを確認
```

---

## 7. エラーハンドリングテスト

### 7.1 Keycloak接続エラーテスト

#### TEST-ERR-KC-001: Keycloakダウンテスト
```python
def test_keycloak_unavailable() -> None:
    """Keycloakが利用不可の場合の処理を確認"""
    # Given: Keycloakサーバーダウン
    with mock_keycloak_down():
        # When: 認証試行
        response = client.get("/api/v1/auth/keycloak/login")
        
        # Then: 適切なエラーレスポンス
        assert response.status_code == 503
        assert response.json()["code"] == "KEYCLOAK_UNAVAILABLE"
```

---

## 8. テストデータ

### 8.1 テストレルム設定
```json
{
  "realm": "test-realm",
  "users": [
    {
      "username": "admin@test.com",
      "roles": ["admin", "user"],
      "groups": ["management"]
    },
    {
      "username": "user@test.com", 
      "roles": ["user"],
      "groups": ["sales"]
    }
  ]
}
```

### 8.2 モックトークン
- 有効なアクセストークン
- 期限切れトークン
- 不正な署名のトークン
- 権限不足のトークン

---

## 9. テスト実行計画

### 9.1 実行順序
1. Keycloakクライアント単体テスト
2. トークン管理単体テスト
3. API結合テスト
4. セキュリティテスト
5. パフォーマンステスト
6. 統合テスト

### 9.2 合格基準
- 全テストケース合格
- コードカバレッジ85%以上
- パフォーマンス目標達成
- セキュリティ脆弱性ゼロ