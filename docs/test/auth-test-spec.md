# 認証機能テスト仕様書

**文書番号**: ITDO-ERP-TS-AUTH-001  
**バージョン**: 1.0  
**作成日**: 2025年7月5日  
**作成者**: Claude Code AI  

---

## 1. テスト概要

### 1.1 テスト目的
認証基盤機能（AUTH-001, AUTH-004, USER-001）が要件通りに動作することを検証する。

### 1.2 テスト範囲
- ユーザー認証機能
- JWTトークン管理
- ユーザー登録機能
- セキュリティ要件の充足

### 1.3 テスト環境
- Python 3.13 + pytest
- FastAPI TestClient
- PostgreSQL 15（テストDB）
- Redis 7（テスト用）

---

## 2. 単体テスト仕様

### 2.1 セキュリティユーティリティテスト

#### TEST-SEC-001: パスワードハッシュ化テスト
```python
def test_password_hashing():
    """パスワードが正しくハッシュ化されることを確認"""
    # Given: プレーンテキストパスワード
    password = "SecurePassword123!"
    
    # When: ハッシュ化
    hashed = hash_password(password)
    
    # Then: 
    # - ハッシュが生成される
    # - 元のパスワードと異なる
    # - bcryptフォーマットである
```

#### TEST-SEC-002: パスワード検証テスト
```python
def test_password_verification():
    """正しいパスワードが検証されることを確認"""
    # Given: パスワードとそのハッシュ
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    # When: 検証
    result = verify_password(password, hashed)
    
    # Then: Trueが返される
```

#### TEST-SEC-003: 不正パスワード検証テスト
```python
def test_invalid_password_verification():
    """不正なパスワードが拒否されることを確認"""
    # Given: パスワードと異なるパスワードのハッシュ
    password = "SecurePassword123!"
    wrong_password = "WrongPassword123!"
    hashed = hash_password(password)
    
    # When: 検証
    result = verify_password(wrong_password, hashed)
    
    # Then: Falseが返される
```

### 2.2 JWT管理テスト

#### TEST-JWT-001: アクセストークン生成テスト
```python
def test_create_access_token():
    """アクセストークンが正しく生成されることを確認"""
    # Given: ユーザーデータ
    data = {"sub": "123", "email": "test@example.com"}
    
    # When: トークン生成
    token = create_access_token(data)
    
    # Then:
    # - トークンが生成される
    # - デコード可能である
    # - ペイロードが正しい
    # - 有効期限が設定されている
```

#### TEST-JWT-002: トークン検証テスト
```python
def test_verify_token():
    """有効なトークンが検証されることを確認"""
    # Given: 有効なトークン
    token = create_access_token({"sub": "123"})
    
    # When: 検証
    payload = verify_token(token)
    
    # Then: ペイロードが返される
```

#### TEST-JWT-003: 期限切れトークンテスト
```python
def test_expired_token():
    """期限切れトークンが拒否されることを確認"""
    # Given: 期限切れトークン（-1時間）
    token = create_access_token(
        {"sub": "123"}, 
        expires_delta=timedelta(hours=-1)
    )
    
    # When/Then: 検証時に例外発生
    with pytest.raises(ExpiredTokenError):
        verify_token(token)
```

### 2.3 ユーザーモデルテスト

#### TEST-USER-001: ユーザー作成テスト
```python
def test_create_user():
    """ユーザーが正しく作成されることを確認"""
    # Given: ユーザー情報
    user_data = {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
    
    # When: ユーザー作成
    user = User.create(**user_data)
    
    # Then:
    # - ユーザーが作成される
    # - パスワードがハッシュ化されている
    # - デフォルト値が設定されている
```

#### TEST-USER-002: メールアドレス重複テスト
```python
def test_duplicate_email():
    """重複メールアドレスが拒否されることを確認"""
    # Given: 既存ユーザー
    User.create(email="test@example.com", ...)
    
    # When/Then: 同じメールで作成時に例外
    with pytest.raises(IntegrityError):
        User.create(email="test@example.com", ...)
```

---

## 3. 結合テスト仕様

### 3.1 認証APIテスト

#### TEST-API-001: ログイン成功テスト
```python
def test_login_success():
    """正しい認証情報でログインできることを確認"""
    # Given: 登録済みユーザー
    create_test_user("test@example.com", "Password123!")
    
    # When: ログインAPI呼び出し
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Password123!"
    })
    
    # Then:
    # - ステータス200
    # - access_tokenが含まれる
    # - token_typeが"bearer"
    # - expires_inが86400（24時間）
```

#### TEST-API-002: ログイン失敗テスト（不正パスワード）
```python
def test_login_invalid_password():
    """不正なパスワードでログインが拒否されることを確認"""
    # Given: 登録済みユーザー
    create_test_user("test@example.com", "Password123!")
    
    # When: 不正なパスワードでログイン
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPassword!"
    })
    
    # Then:
    # - ステータス401
    # - エラーコード"AUTH001"
```

#### TEST-API-003: ログイン失敗テスト（存在しないユーザー）
```python
def test_login_nonexistent_user():
    """存在しないユーザーでログインが拒否されることを確認"""
    # When: 未登録メールでログイン
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "Password123!"
    })
    
    # Then:
    # - ステータス401
    # - エラーコード"AUTH001"
```

### 3.2 ユーザー管理APIテスト

#### TEST-API-004: ユーザー作成成功テスト
```python
def test_create_user_success():
    """管理者権限でユーザーが作成できることを確認"""
    # Given: 管理者トークン
    admin_token = get_admin_token()
    
    # When: ユーザー作成API呼び出し
    response = client.post(
        "/api/v1/users",
        json={
            "email": "newuser@example.com",
            "password": "Password123!",
            "full_name": "New User"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then:
    # - ステータス201
    # - ユーザー情報が返される
    # - パスワードは含まれない
```

#### TEST-API-005: ユーザー作成権限エラーテスト
```python
def test_create_user_forbidden():
    """一般ユーザーがユーザー作成できないことを確認"""
    # Given: 一般ユーザートークン
    user_token = get_user_token()
    
    # When: ユーザー作成試行
    response = client.post(
        "/api/v1/users",
        json={...},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Then:
    # - ステータス403
    # - エラーコード"AUTH004"
```

#### TEST-API-006: 現在のユーザー情報取得テスト
```python
def test_get_current_user():
    """ログイン中のユーザー情報が取得できることを確認"""
    # Given: ユーザートークン
    user_token = get_user_token()
    
    # When: /users/me 呼び出し
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Then:
    # - ステータス200
    # - 正しいユーザー情報
```

---

## 4. セキュリティテスト仕様

### 4.1 入力検証テスト

#### TEST-VAL-001: メールアドレス形式検証
```python
@pytest.mark.parametrize("email", [
    "invalid-email",
    "@example.com",
    "user@",
    "user@.com",
    "",
])
def test_invalid_email_format(email):
    """不正なメール形式が拒否されることを確認"""
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert response.status_code == 422
```

#### TEST-VAL-002: パスワード強度検証
```python
@pytest.mark.parametrize("password", [
    "short",           # 短すぎる
    "alllowercase",    # 小文字のみ
    "ALLUPPERCASE",    # 大文字のみ
    "12345678",        # 数字のみ
    "NoNumbers!",      # 数字なし
])
def test_weak_password(password):
    """弱いパスワードが拒否されることを確認"""
    response = client.post("/api/v1/users", json={
        "email": "test@example.com",
        "password": password,
        "full_name": "Test User"
    })
    assert response.status_code == 422
```

### 4.2 SQLインジェクション対策テスト

#### TEST-SEC-004: SQLインジェクション試行
```python
def test_sql_injection_attempt():
    """SQLインジェクションが防止されることを確認"""
    # When: SQLインジェクション試行
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com' OR '1'='1",
        "password": "' OR '1'='1"
    })
    
    # Then: 通常の認証失敗として処理
    assert response.status_code == 401
```

---

## 5. パフォーマンステスト仕様

### 5.1 応答時間テスト

#### TEST-PERF-001: ログインAPI応答時間
```python
def test_login_response_time():
    """ログインAPIが200ms以内に応答することを確認"""
    start_time = time.time()
    
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Password123!"
    })
    
    response_time = (time.time() - start_time) * 1000
    assert response_time < 200
```

### 5.2 負荷テスト

#### TEST-PERF-002: 並行ログインテスト
```python
def test_concurrent_logins():
    """100並行ログインが処理できることを確認"""
    # 100スレッドで同時ログイン
    # 全て成功することを確認
```

---

## 6. エラーハンドリングテスト

### 6.1 エラーレスポンス形式テスト

#### TEST-ERR-001: エラーレスポンス形式
```python
def test_error_response_format():
    """エラーレスポンスが仕様通りの形式であることを確認"""
    response = client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrong"
    })
    
    error = response.json()
    assert "detail" in error
    assert "code" in error
    assert "timestamp" in error
```

---

## 7. テストデータ

### 7.1 テストユーザー
| メールアドレス | パスワード | 役割 |
|----------------|------------|------|
| admin@test.com | Admin123! | 管理者 |
| user1@test.com | User123! | 一般ユーザー |
| user2@test.com | User123! | 一般ユーザー |
| inactive@test.com | Inactive123! | 非アクティブ |

### 7.2 テストシナリオデータ
- 正常系: 各APIの成功パターン
- 異常系: 認証失敗、権限不足、バリデーションエラー
- 境界値: 最大長、最小長、特殊文字

---

## 8. テスト実行計画

### 8.1 実行順序
1. 単体テスト（セキュリティ、JWT、モデル）
2. 結合テスト（API）
3. セキュリティテスト
4. パフォーマンステスト
5. エラーハンドリングテスト

### 8.2 合格基準
- 全テストケース合格
- コードカバレッジ80%以上
- パフォーマンス目標達成
- セキュリティ脆弱性ゼロ