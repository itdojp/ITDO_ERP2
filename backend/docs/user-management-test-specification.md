# ユーザー管理機能テスト仕様書

## 1. テスト概要

### 1.1 目的
ユーザー管理機能の品質を保証し、セキュリティ要件とマルチテナント分離を確認する。

### 1.2 テスト範囲
- ユーザーCRUD操作
- ロール・権限管理
- 認証・認可機能
- セキュリティ制御
- マルチテナント分離

### 1.3 テスト方針
- Test-Driven Development (TDD) アプローチ
- セキュリティファーストテスト
- マルチテナント分離の徹底検証

## 2. 単体テスト (Unit Tests)

### 2.1 モデルレベルテスト

#### TEST-USER-MODEL-001: ユーザー作成
```python
def test_create_user_with_extended_fields():
    """拡張フィールドを含むユーザー作成をテスト"""
    # Given: 拡張ユーザーデータ
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "テストユーザー",
        "phone": "090-1234-5678"
    }
    
    # When: ユーザー作成
    user = User.create(db, **user_data)
    
    # Then: 正しく作成される
    assert user.phone == "090-1234-5678"
    assert user.failed_login_attempts == 0
    assert user.password_changed_at is not None
```

#### TEST-USER-MODEL-002: パスワード履歴
```python
def test_password_history_tracking():
    """パスワード履歴の記録をテスト"""
    # Given: 既存ユーザー
    user = create_test_user()
    
    # When: パスワード変更
    old_hash = user.hashed_password
    user.change_password(db, "NewPassword123!")
    
    # Then: 履歴が記録される
    history = db.query(PasswordHistory).filter_by(user_id=user.id).all()
    assert len(history) == 1
    assert history[0].password_hash == old_hash
```

#### TEST-USER-MODEL-003: アカウントロック
```python
def test_account_lockout():
    """アカウントロック機能をテスト"""
    # Given: ユーザー
    user = create_test_user()
    
    # When: 5回連続でログイン失敗
    for _ in range(5):
        user.record_failed_login()
    
    # Then: アカウントがロックされる
    assert user.is_locked()
    assert user.locked_until > datetime.utcnow()
```

### 2.2 サービスレベルテスト

#### TEST-USER-SERVICE-001: ユーザー作成権限
```python
def test_create_user_permission_system_admin():
    """システム管理者によるユーザー作成をテスト"""
    # Given: システム管理者
    admin = create_test_user(is_superuser=True)
    
    # When: ユーザー作成
    user_data = UserCreateExtended(
        email="new@example.com",
        full_name="新規ユーザー",
        organization_id=1
    )
    user = user_service.create_user(data=user_data, creator=admin, db=db)
    
    # Then: 正常に作成される
    assert user.email == "new@example.com"
    assert user.created_by == admin.id
```

#### TEST-USER-SERVICE-002: 組織管理者権限制限
```python
def test_org_admin_cannot_create_cross_tenant():
    """組織管理者が他組織ユーザーを作成できないことをテスト"""
    # Given: 組織1の管理者
    org1 = create_test_organization()
    org2 = create_test_organization()
    admin1 = create_test_user()
    assign_role(admin1, "ORG_ADMIN", org1)
    
    # When: 組織2のユーザー作成を試行
    with pytest.raises(PermissionDenied):
        user_service.create_user(
            data=UserCreateExtended(
                email="user@org2.com",
                organization_id=org2.id
            ),
            creator=admin1,
            db=db
        )
```

#### TEST-USER-SERVICE-003: ユーザー検索フィルタリング
```python
def test_user_search_multi_tenant_isolation():
    """マルチテナント環境でのユーザー検索分離をテスト"""
    # Given: 2つの組織とユーザー
    org1_user = create_user_in_org("user1@org1.com", org1)
    org2_user = create_user_in_org("user2@org2.com", org2)
    org1_admin = create_org_admin(org1)
    
    # When: 組織1管理者が検索
    result = user_service.search_users(
        searcher=org1_admin,
        search="user",
        db=db
    )
    
    # Then: 自組織ユーザーのみ表示
    user_emails = [u.email for u in result.items]
    assert "user1@org1.com" in user_emails
    assert "user2@org2.com" not in user_emails
```

### 2.3 ロール管理テスト

#### TEST-ROLE-001: ロール割り当て
```python
def test_assign_role_with_department():
    """部門レベルでのロール割り当てをテスト"""
    # Given: ユーザーと部門
    user = create_test_user()
    dept = create_test_department()
    role = create_test_role("DEPT_MANAGER")
    
    # When: 部門管理者ロールを割り当て
    role_service.assign_role(
        user_id=user.id,
        role_id=role.id,
        organization_id=dept.organization_id,
        department_id=dept.id,
        assigned_by=admin.id,
        db=db
    )
    
    # Then: 正しく割り当てられる
    assert user.has_role_in_department("DEPT_MANAGER", dept.id)
```

#### TEST-ROLE-002: 権限継承
```python
def test_permission_inheritance():
    """権限継承のテスト"""
    # Given: 階層構造（親部門→子部門）
    parent_dept = create_test_department(name="親部門")
    child_dept = create_test_department(name="子部門", parent=parent_dept)
    manager = create_test_user()
    
    # When: 親部門の管理者に設定
    assign_department_manager(manager, parent_dept)
    
    # Then: 子部門の権限も継承
    assert manager.has_permission_in_department("dept:read", child_dept.id)
    assert manager.has_permission_in_department("dept:write", child_dept.id)
```

## 3. 統合テスト (Integration Tests)

### 3.1 API テスト

#### TEST-API-USER-001: ユーザー作成API
```python
def test_create_user_api():
    """ユーザー作成APIの統合テスト"""
    # Given: 管理者トークン
    admin_token = get_admin_token()
    
    # When: ユーザー作成API呼び出し
    response = client.post(
        "/api/v1/users",
        json={
            "email": "newuser@example.com",
            "full_name": "新規ユーザー",
            "phone": "090-1234-5678",
            "password": "SecurePass123!",
            "organization_id": 1,
            "role_ids": [2]
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then: 正常に作成される
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["phone"] == "090-1234-5678"
    assert "password" not in data  # パスワードは返さない
```

#### TEST-API-USER-002: ユーザー一覧API（ページネーション）
```python
def test_user_list_pagination():
    """ユーザー一覧のページネーションテスト"""
    # Given: 50人のユーザー
    for i in range(50):
        create_test_user(email=f"user{i}@example.com")
    
    # When: ページ2を取得（20件/ページ）
    response = client.get(
        "/api/v1/users?page=2&limit=20",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then: 正しいページネーション
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["page"] == 2
    assert data["total"] == 50
```

#### TEST-API-USER-003: 権限制御
```python
def test_user_detail_permission_control():
    """ユーザー詳細表示の権限制御テスト"""
    # Given: 異なる組織の2人のユーザー
    org1_user = create_user_in_org("user1@org1.com", org1)
    org2_user = create_user_in_org("user2@org2.com", org2)
    org1_token = get_user_token(org1_user)
    
    # When: 他組織ユーザーの詳細を取得
    response = client.get(
        f"/api/v1/users/{org2_user.id}",
        headers={"Authorization": f"Bearer {org1_token}"}
    )
    
    # Then: アクセス拒否
    assert response.status_code == 403
```

### 3.2 認証・認可テスト

#### TEST-AUTH-001: トークン有効期限
```python
def test_token_expiration():
    """トークン有効期限のテスト"""
    # Given: 短期間トークン
    user = create_test_user()
    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(seconds=1)
    )
    
    # When: 期限切れ後にアクセス
    time.sleep(2)
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then: 認証エラー
    assert response.status_code == 401
```

#### TEST-AUTH-002: ロールベースアクセス制御
```python
def test_rbac_enforcement():
    """RBACの実行テスト"""
    # Given: 一般ユーザー
    user = create_test_user()
    user_token = get_user_token(user)
    
    # When: 管理者専用API呼び出し
    response = client.post(
        "/api/v1/users",
        json={"email": "test@test.com", "full_name": "Test"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Then: 権限不足エラー
    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PERMISSIONS"
```

## 4. セキュリティテスト

### 4.1 データ保護テスト

#### TEST-SEC-001: パスワードハッシュ化
```python
def test_password_hashing_security():
    """パスワードハッシュ化のセキュリティテスト"""
    # Given: パスワード
    password = "MySecurePassword123!"
    
    # When: ユーザー作成
    user = User.create(db, email="test@test.com", password=password)
    
    # Then: パスワードがハッシュ化されている
    assert user.hashed_password != password
    assert user.hashed_password.startswith("$2b$")
    assert verify_password(password, user.hashed_password)
```

#### TEST-SEC-002: SQLインジェクション防止
```python
def test_sql_injection_prevention():
    """SQLインジェクション攻撃の防止テスト"""
    # Given: 悪意のある検索クエリ
    malicious_query = "'; DROP TABLE users; --"
    
    # When: ユーザー検索API呼び出し
    response = client.get(
        f"/api/v1/users?search={malicious_query}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then: 正常に処理される（テーブルは削除されない）
    assert response.status_code == 200
    # ユーザーテーブルが存在することを確認
    users = db.query(User).count()
    assert users >= 0
```

#### TEST-SEC-003: データ漏洩防止
```python
def test_sensitive_data_not_exposed():
    """機密データが漏洩しないことをテスト"""
    # Given: ユーザー
    user = create_test_user()
    user_token = get_user_token(user)
    
    # When: 自分の情報を取得
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Then: 機密情報は含まれない
    data = response.json()
    assert "hashed_password" not in data
    assert "password" not in data
    forbidden_fields = ["hashed_password", "password", "password_history"]
    for field in forbidden_fields:
        assert field not in data
```

### 4.2 マルチテナント分離テスト

#### TEST-TENANT-001: データアクセス分離
```python
def test_cross_tenant_data_isolation():
    """テナント間データアクセス分離テスト"""
    # Given: 2つの組織のユーザー
    org1_admin = create_org_admin("admin1@org1.com", org1)
    org2_user = create_user_in_org("user@org2.com", org2)
    
    # When: 組織1管理者が組織2ユーザーにアクセス
    admin_token = get_user_token(org1_admin)
    response = client.get(
        f"/api/v1/users/{org2_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then: アクセス拒否
    assert response.status_code == 403
```

#### TEST-TENANT-002: ロール割り当て分離
```python
def test_cross_tenant_role_assignment_prevention():
    """テナント間ロール割り当ての防止テスト"""
    # Given: 組織1管理者と組織2ユーザー
    org1_admin = create_org_admin("admin@org1.com", org1)
    org2_user = create_user_in_org("user@org2.com", org2)
    role = create_test_role("MANAGER")
    
    # When: 組織1管理者が組織2ユーザーにロール割り当て
    with pytest.raises(PermissionDenied):
        role_service.assign_role(
            user_id=org2_user.id,
            role_id=role.id,
            organization_id=org2.id,
            assigned_by=org1_admin.id,
            db=db
        )
```

## 5. パフォーマンステスト

### 5.1 応答時間テスト

#### TEST-PERF-001: ユーザー一覧取得
```python
def test_user_list_response_time():
    """ユーザー一覧取得の応答時間テスト"""
    # Given: 1000人のユーザー
    create_bulk_users(1000)
    
    # When: ユーザー一覧取得
    start_time = time.time()
    response = client.get(
        "/api/v1/users?limit=20",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response_time = (time.time() - start_time) * 1000
    
    # Then: 200ms以内で応答
    assert response.status_code == 200
    assert response_time < 200
```

#### TEST-PERF-002: ユーザー検索
```python
def test_user_search_performance():
    """ユーザー検索パフォーマンステスト"""
    # Given: 大量ユーザーデータ
    create_bulk_users(10000)
    
    # When: 検索実行
    start_time = time.time()
    response = client.get(
        "/api/v1/users?search=田中",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response_time = (time.time() - start_time) * 1000
    
    # Then: 500ms以内で応答
    assert response.status_code == 200
    assert response_time < 500
```

### 5.2 負荷テスト

#### TEST-LOAD-001: 同時ログイン
```python
def test_concurrent_login_load():
    """同時ログイン負荷テスト"""
    # Given: 100人のユーザー
    users = create_bulk_users(100)
    
    # When: 同時ログイン
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for user in users:
            future = executor.submit(
                client.post,
                "/api/v1/auth/login",
                json={"email": user.email, "password": "TestPass123!"}
            )
            futures.append(future)
        
        # 全ての結果を収集
        results = [future.result() for future in futures]
    
    # Then: 全て成功
    success_count = sum(1 for r in results if r.status_code == 200)
    assert success_count == 100
```

## 6. エラーハンドリングテスト

### 6.1 バリデーションエラー

#### TEST-ERR-001: 無効なメールアドレス
```python
@pytest.mark.parametrize("email", [
    "invalid-email",
    "@example.com",
    "user@",
    "",
    "a" * 100 + "@example.com"  # 長すぎるメール
])
def test_invalid_email_validation(email):
    """無効なメールアドレスのバリデーションテスト"""
    # When: 無効なメールでユーザー作成
    response = client.post(
        "/api/v1/users",
        json={
            "email": email,
            "full_name": "Test User",
            "password": "ValidPass123!"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then: バリデーションエラー
    assert response.status_code == 422
```

#### TEST-ERR-002: 弱いパスワード
```python
@pytest.mark.parametrize("password", [
    "weak",
    "12345678",
    "password",
    "PASSWORD123",
    "Password!",  # 数字なし
])
def test_weak_password_rejection(password):
    """弱いパスワードの拒否テスト"""
    response = client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": password
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 422
    assert "password" in str(response.json())
```

### 6.2 業務エラー

#### TEST-ERR-003: 重複ユーザー作成
```python
def test_duplicate_user_creation():
    """重複ユーザー作成エラーテスト"""
    # Given: 既存ユーザー
    existing_user = create_test_user("existing@example.com")
    
    # When: 同じメールでユーザー作成
    response = client.post(
        "/api/v1/users",
        json={
            "email": "existing@example.com",
            "full_name": "Duplicate User",
            "password": "ValidPass123!"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Then: 競合エラー
    assert response.status_code == 409
    assert response.json()["code"] == "USER_ALREADY_EXISTS"
```

## 7. 回帰テスト

### 7.1 重要機能の回帰テスト
```python
def test_critical_path_regression():
    """重要機能の回帰テスト"""
    # 1. ユーザー作成
    user = create_test_user("regression@example.com")
    assert user.id is not None
    
    # 2. ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "regression@example.com", "password": "TestPass123!"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 3. 自分の情報取得
    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    
    # 4. 情報更新
    update_response = client.put(
        f"/api/v1/users/{user.id}",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
```

## 8. テスト環境・データ

### 8.1 テストデータ生成
```python
def create_test_user_with_profile(**kwargs):
    """プロファイル付きテストユーザー作成"""
    defaults = {
        "email": f"test{random.randint(1000,9999)}@example.com",
        "full_name": "テストユーザー",
        "phone": "090-1234-5678",
        "password": "TestPassword123!",
        "is_active": True
    }
    defaults.update(kwargs)
    return User.create(db, **defaults)

def create_org_with_users(org_name, user_count=10):
    """組織とユーザーを一括作成"""
    org = create_test_organization(name=org_name)
    users = []
    for i in range(user_count):
        user = create_test_user(email=f"user{i}@{org_name.lower()}.com")
        assign_to_organization(user, org)
        users.append(user)
    return org, users
```

### 8.2 テスト環境設定
```python
@pytest.fixture(scope="function")
def clean_user_data():
    """ユーザーデータクリーンアップ"""
    yield
    # テスト後のクリーンアップ
    db.query(UserRole).delete()
    db.query(PasswordHistory).delete()
    db.query(UserSession).delete()
    db.query(User).delete()
    db.commit()
```

## 9. テスト実行計画

### 9.1 継続的インテグレーション
- 全単体テスト: 2分以内
- 統合テスト: 5分以内
- セキュリティテスト: 3分以内

### 9.2 リリース前テスト
- 全テストスイート実行
- パフォーマンステスト
- セキュリティ監査
- マルチテナント分離検証

### 9.3 成功基準
- テストカバレッジ: 95%以上
- セキュリティテスト: 100%パス
- パフォーマンステスト: 全項目クリア
- マルチテナント分離: 完全分離確認