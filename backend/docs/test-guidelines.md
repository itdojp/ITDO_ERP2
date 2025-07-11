# ITDO ERP テストガイドライン

**Claude Code 3作成 - Phase 2 Sprint 1 Day 2**

## 概要

このガイドラインは、ITDO ERPプロジェクトにおけるテスト作成・実行のベストプラクティスをまとめたものです。

## テストインフラ改善内容

### conftest.py の主要改善点

#### 1. データベーステスト環境の最適化

```python
# 単体テスト: SQLite (高速)
if "unit" in os.getenv("PYTEST_CURRENT_TEST", ""):
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    
# 統合テスト: PostgreSQL (本番同等)
else:
    SQLALCHEMY_DATABASE_URL = "postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp"
```

**メリット:**
- 単体テストは高速実行 (SQLite)
- 統合テストは本番環境同等 (PostgreSQL)
- テスト分離による安定性向上

#### 2. テストデータクリーンアップの改善

```python
# PostgreSQL: 外部キー制約を考慮した削除順序
table_order = [
    "user_roles", "role_permissions", "password_history",
    "user_sessions", "user_activity_logs", "audit_logs",
    "project_members", "project_milestones", "projects",
    "users", "roles", "permissions", "departments", "organizations"
]
```

**改善効果:**
- 外部キー制約エラーの解消
- テスト間の完全データ分離
- CI環境での安定性向上

### 3. ファクトリーパターンの活用

```python
# 完全なテストシステム作成
@pytest.fixture
def complete_test_system(db_session: Session) -> Dict[str, Any]:
    role_system = RoleFactory.create_complete_role_system(db_session)
    dept_tree = DepartmentFactory.create_department_tree(db_session, ...)
    users = UserFactory.create_test_users_set(db_session)
    
    return {
        "organization": role_system["organization"],
        "departments": dept_tree,
        "roles": role_system["roles"],
        "permissions": role_system["permissions"],
        "users": users,
    }
```

## テスト作成ベストプラクティス

### 1. 単体テスト (Unit Tests)

**対象:** サービス層、リポジトリ層の個別機能

```python
class TestUserService:
    def test_create_user(self, db_session: Session) -> None:
        # Given
        service = UserService(db_session)
        user_data = UserCreateExtended(...)
        
        # When
        user = service.create_user(user_data, creator, db_session)
        
        # Assert
        assert user.email == user_data.email
```

**ポイント:**
- SQLiteを使用 (高速)
- Given-When-Then パターン
- 単一責任の検証

### 2. 統合テスト (Integration Tests)

**対象:** API層とサービス層の連携

```python
class TestUserAPI:
    def test_create_user_endpoint(self, client: TestClient, admin_token: str) -> None:
        # Given
        headers = create_auth_headers(admin_token)
        user_data = {...}
        
        # When
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        
        # Assert
        assert response.status_code == 201
```

**ポイント:**
- PostgreSQLを使用 (本番同等)
- 認証・認可のテスト
- エンドツーエンド動作確認

### 3. マルチテナントテスト戦略

```python
def test_organization_isolation(self, complete_test_system: Dict[str, Any]) -> None:
    # 組織間データ分離の確認
    org1_user = complete_test_system["users"]["org1_admin"]
    org2_data = complete_test_system["organizations"]["org2"]
    
    # org1のユーザーはorg2のデータにアクセスできない
    with pytest.raises(PermissionDenied):
        service.access_organization_data(org1_user, org2_data.id)
```

## CI/CD 安定化施策

### 1. 環境変数設定

```python
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: Any) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only-32-chars-long")
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")  # テスト高速化
    monkeypatch.setenv("DATABASE_URL", SQLALCHEMY_DATABASE_URL)
```

### 2. Pydantic v2 対応

```python
# v1 (非推奨)
@validator("field_name", pre=True)

# v2 (推奨)
@field_validator("field_name", mode="before")
```

**model_config 使用:**
```python
model_config = {
    "env_file": ".env",
    "case_sensitive": True
}
```

## 権限・セキュリティテスト

### 1. RBAC (Role-Based Access Control) テスト

```python
def test_permission_hierarchy(self, test_role_system: Dict[str, Any]) -> None:
    admin_role = test_role_system["roles"]["admin"]
    user_role = test_role_system["roles"]["user"]
    
    # 管理者は全権限保持
    assert admin_role.has_permission("user.delete")
    # 一般ユーザーは制限権限
    assert not user_role.has_permission("user.delete")
```

### 2. 監査ログテスト

```python
def test_audit_logging(self, db_session: Session, test_admin: User) -> None:
    # Given
    service = UserService(db_session)
    
    # When
    service.delete_user(user_id, test_admin, db_session)
    
    # Then
    audit_logs = db_session.query(AuditLog).filter_by(action="delete").all()
    assert len(audit_logs) == 1
    assert audit_logs[0].user_id == test_admin.id
```

## パフォーマンステスト

### 1. データベースクエリ最適化

```python
def test_user_search_performance(self, db_session: Session) -> None:
    # 大量データでの検索性能確認
    UserFactory.create_batch(db_session, 1000)
    
    start_time = time.time()
    results = service.search_users(params, searcher, db_session)
    execution_time = time.time() - start_time
    
    assert execution_time < 0.2  # 200ms以下
    assert len(results.items) <= 20  # ページネーション確認
```

## エラーハンドリングテスト

### 1. 例外処理パターン

```python
def test_business_logic_error_handling(self, db_session: Session) -> None:
    with pytest.raises(BusinessLogicError) as exc_info:
        service.invalid_operation()
    
    assert "期待されるエラーメッセージ" in str(exc_info.value)
```

### 2. バリデーションエラー

```python
def test_input_validation(self, client: TestClient) -> None:
    invalid_data = {"email": "invalid-email"}
    
    response = client.post("/api/v1/users/", json=invalid_data)
    
    assert response.status_code == 422
    assert "validation error" in response.json()["detail"]
```

## 推奨テスト構成

```
tests/
├── unit/                    # 単体テスト (SQLite)
│   ├── services/
│   ├── repositories/
│   └── models/
├── integration/             # 統合テスト (PostgreSQL)
│   ├── api/
│   └── workflows/
├── security/               # セキュリティテスト
│   ├── auth/
│   └── permissions/
├── conftest.py            # 共通fixtures
└── factories.py           # テストデータ生成
```

## CI改善効果測定

### Before (Day 1前)
- CI失敗率: 高 (Ruffエラー、型チェック警告)
- テスト実行時間: 不安定
- Pydantic非推奨警告: 多数

### After (Day 2)
- CI成功率: 100% (全エラー解消)
- テスト実行時間: 安定 (<2分)
- 警告数: 大幅削減 (Pydantic v2対応)

## 残存課題と対策

### 1. テストカバレッジ向上
- 現在: 43%
- 目標: 80%+
- 対策: 未カバー領域の優先的テスト作成

### 2. E2Eテスト整備
- 現在: 基本的なAPIテストのみ
- 目標: 主要ワークフローの完全カバー
- 対策: Day 3でTaskService連携テスト作成

## Claude Code間連携ポイント

### Code 1 (Organization Service)への要求
- Organization CRUD API完成
- Department連携インターフェース明確化
- 権限チェック統一化

### Code 2 (Task Service)への要求
- 監査ログ実装
- 権限ベースアクセス制御
- Organization境界の尊重

## 次ステップ (Day 3)

1. **TaskService統合テスト作成**
   - Organization-Task連携テスト
   - マルチテナント境界テスト
   - 権限継承テスト

2. **E2Eワークフローテスト**
   - ユーザー作成→権限付与→タスク作成フロー
   - 組織間データ分離確認

3. **パフォーマンステスト拡充**
   - 大量データでの動作確認
   - 同時接続ユーザーテスト

---

**作成者:** Claude Code 3  
**作成日:** Phase 2 Sprint 1 Day 2  
**最終更新:** 2025-07-09