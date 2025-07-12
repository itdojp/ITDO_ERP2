# 組織管理機能テスト仕様書

**文書番号**: ITDO-ERP-TS-ORG-001  
**バージョン**: 1.0  
**作成日**: 2025年7月5日  
**作成者**: Claude Code AI  

---

## 1. テスト概要

### 1.1 テスト目的
組織管理機能（ORG-001, ORG-002, PERM-001, PERM-002）が要件通りに動作し、マルチテナントのデータ分離が確実に行われることを検証する。

### 1.2 テスト範囲
- 組織管理CRUD機能
- 部門階層管理機能
- ロール管理・付与機能
- マルチテナントデータ分離
- 権限制御・監査ログ

### 1.3 テスト環境
- Python 3.13 + pytest
- PostgreSQL 15（テストDB）
- FastAPI TestClient
- Factory Boy（テストデータ生成）

---

## 2. 単体テスト仕様

### 2.1 組織モデルテスト

#### TEST-ORG-001: 組織作成テスト
```python
def test_create_organization() -> None:
    """組織が正しく作成されることを確認"""
    # Given: 組織データ
    org_data = {
        "code": "ITDO",
        "name": "株式会社ITDO",
        "email": "info@itdo.jp",
        "fiscal_year_start": 4
    }
    
    # When: 組織作成
    org = Organization.create(**org_data)
    
    # Then:
    assert org.id is not None
    assert org.code == "ITDO"
    assert org.is_active is True
    assert org.created_at is not None
```

#### TEST-ORG-002: 組織コード重複テスト
```python
def test_duplicate_organization_code() -> None:
    """重複する組織コードが拒否されることを確認"""
    # Given: 既存組織
    Organization.create(code="ITDO", name="既存組織")
    
    # When/Then: 同じコードで作成時に例外
    with pytest.raises(IntegrityError):
        Organization.create(code="ITDO", name="新組織")
```

#### TEST-ORG-003: 組織更新テスト
```python
def test_update_organization() -> None:
    """組織情報が更新できることを確認"""
    # Given: 既存組織
    org = Organization.create(code="ITDO", name="旧名称")
    
    # When: 更新
    org.update(name="新名称", email="new@itdo.jp")
    
    # Then:
    assert org.name == "新名称"
    assert org.email == "new@itdo.jp"
    assert org.updated_at > org.created_at
```

### 2.2 部門モデルテスト

#### TEST-DEPT-001: 部門作成テスト
```python
def test_create_department() -> None:
    """部門が正しく作成されることを確認"""
    # Given: 組織
    org = create_test_organization()
    
    # When: 部門作成
    dept = Department.create(
        organization_id=org.id,
        code="SALES",
        name="営業部",
        level=1
    )
    
    # Then:
    assert dept.id is not None
    assert dept.level == 1
    assert dept.parent_id is None
    assert dept.path == str(dept.id)
```

#### TEST-DEPT-002: 子部門作成テスト
```python
def test_create_child_department() -> None:
    """子部門が正しく作成されることを確認"""
    # Given: 親部門
    parent = create_test_department(level=1)
    
    # When: 子部門作成
    child = Department.create(
        organization_id=parent.organization_id,
        parent_id=parent.id,
        code="SALES_TOKYO",
        name="東京営業所",
        level=2
    )
    
    # Then:
    assert child.parent_id == parent.id
    assert child.level == 2
    assert child.path == f"{parent.id}/{child.id}"
```

#### TEST-DEPT-003: 階層制限テスト
```python
def test_department_level_limit() -> None:
    """3階層目の部門作成が拒否されることを確認"""
    # Given: 2階層の部門
    parent = create_test_department(level=1)
    child = create_test_department(parent_id=parent.id, level=2)
    
    # When/Then: 3階層目作成で例外
    with pytest.raises(ValueError, match="部門階層は2階層まで"):
        Department.create(
            organization_id=parent.organization_id,
            parent_id=child.id,
            code="INVALID",
            name="無効な部門",
            level=3
        )
```

### 2.3 ロール管理テスト

#### TEST-ROLE-001: システムロール存在確認テスト
```python
def test_system_roles_exist() -> None:
    """システムロールが存在することを確認"""
    # When: システムロール取得
    roles = Role.get_system_roles()
    
    # Then:
    role_codes = [r.code for r in roles]
    assert "SYSTEM_ADMIN" in role_codes
    assert "ORG_ADMIN" in role_codes
    assert "DEPT_MANAGER" in role_codes
    assert "USER" in role_codes
```

#### TEST-ROLE-002: ユーザーロール付与テスト
```python
def test_assign_role_to_user() -> None:
    """ユーザーにロールを付与できることを確認"""
    # Given: ユーザーと組織
    user = create_test_user()
    org = create_test_organization()
    role = Role.get_by_code("ORG_ADMIN")
    
    # When: ロール付与
    user_role = UserRole.assign(
        user_id=user.id,
        role_id=role.id,
        organization_id=org.id
    )
    
    # Then:
    assert user_role.id is not None
    assert user_role.user_id == user.id
    assert user_role.organization_id == org.id
```

#### TEST-ROLE-003: 重複ロール付与防止テスト
```python
def test_prevent_duplicate_role_assignment() -> None:
    """同じロールの重複付与が防止されることを確認"""
    # Given: ロール付与済み
    user_role = create_test_user_role()
    
    # When/Then: 同じロール付与で例外
    with pytest.raises(IntegrityError):
        UserRole.assign(
            user_id=user_role.user_id,
            role_id=user_role.role_id,
            organization_id=user_role.organization_id
        )
```

---

## 3. サービス層テスト

### 3.1 組織サービステスト

#### TEST-SVC-ORG-001: 組織作成権限テスト
```python
def test_create_organization_permission() -> None:
    """システム管理者のみ組織作成可能なことを確認"""
    # Given: 一般ユーザー
    user = create_test_user(is_system_admin=False)
    
    # When/Then: 組織作成で権限エラー
    with pytest.raises(PermissionDenied):
        org_service.create_organization(
            data=OrganizationCreate(code="TEST", name="テスト"),
            user=user
        )
```

#### TEST-SVC-ORG-002: 組織フィルタリングテスト
```python
def test_organization_filtering() -> None:
    """ユーザーが所属する組織のみ表示されることを確認"""
    # Given: 複数組織とユーザー
    org1 = create_test_organization(code="ORG1")
    org2 = create_test_organization(code="ORG2")
    org3 = create_test_organization(code="ORG3")
    
    user = create_test_user()
    assign_user_to_organization(user, org1)
    assign_user_to_organization(user, org2)
    
    # When: 組織一覧取得
    orgs = org_service.get_organizations(user=user)
    
    # Then: 所属組織のみ
    org_ids = [o.id for o in orgs]
    assert org1.id in org_ids
    assert org2.id in org_ids
    assert org3.id not in org_ids
```

### 3.2 部門サービステスト

#### TEST-SVC-DEPT-001: 部門階層取得テスト
```python
def test_get_department_tree() -> None:
    """部門階層が正しく取得できることを確認"""
    # Given: 階層構造
    org = create_test_organization()
    sales = create_test_department(org.id, "SALES", "営業部")
    tokyo = create_test_department(org.id, "TOKYO", "東京", parent=sales)
    osaka = create_test_department(org.id, "OSAKA", "大阪", parent=sales)
    
    # When: 階層取得
    tree = dept_service.get_department_tree(org.id)
    
    # Then:
    assert len(tree) == 1
    assert tree[0]["code"] == "SALES"
    assert len(tree[0]["children"]) == 2
```

### 3.3 権限サービステスト

#### TEST-SVC-PERM-001: 権限チェックテスト
```python
def test_permission_check() -> None:
    """権限チェックが正しく動作することを確認"""
    # Given: ユーザーとロール
    user = create_test_user()
    org = create_test_organization()
    assign_role(user, "DEPT_MANAGER", org)
    
    # When/Then:
    assert perm_service.has_permission(user, "dept:write", org)
    assert perm_service.has_permission(user, "dept:read", org)
    assert not perm_service.has_permission(user, "org:delete", org)
```

---

## 4. API統合テスト

### 4.1 組織管理APIテスト

#### TEST-API-ORG-001: 組織作成APIテスト
```python
def test_create_organization_api() -> None:
    """組織作成APIが正しく動作することを確認"""
    # Given: システム管理者トークン
    token = get_system_admin_token()
    
    # When: API呼び出し
    response = client.post(
        "/api/v1/organizations",
        json={
            "code": "NEWORG",
            "name": "新組織",
            "email": "new@example.com"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then:
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "NEWORG"
    assert data["id"] is not None
```

#### TEST-API-ORG-002: 組織一覧取得APIテスト
```python
def test_list_organizations_api() -> None:
    """組織一覧APIがフィルタリングされることを確認"""
    # Given: 複数組織と制限ユーザー
    setup_multi_tenant_data()
    token = get_org_admin_token(org_id=1)
    
    # When: API呼び出し
    response = client.get(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then: 所属組織のみ
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == 1
```

### 4.2 部門管理APIテスト

#### TEST-API-DEPT-001: 部門作成APIテスト
```python
def test_create_department_api() -> None:
    """部門作成APIが正しく動作することを確認"""
    # Given: 組織管理者
    org = create_test_organization()
    token = get_org_admin_token(org.id)
    
    # When: API呼び出し
    response = client.post(
        "/api/v1/departments",
        json={
            "organization_id": org.id,
            "code": "HR",
            "name": "人事部"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then:
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "HR"
    assert data["level"] == 1
```

### 4.3 ロール管理APIテスト

#### TEST-API-ROLE-001: ロール付与APIテスト
```python
def test_assign_role_api() -> None:
    """ロール付与APIが正しく動作することを確認"""
    # Given: システム管理者とターゲットユーザー
    user = create_test_user()
    org = create_test_organization()
    token = get_system_admin_token()
    
    # When: API呼び出し
    response = client.post(
        f"/api/v1/users/{user.id}/roles",
        json={
            "role_id": 2,  # ORG_ADMIN
            "organization_id": org.id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then:
    assert response.status_code == 201
    
    # ロール確認
    roles = get_user_roles(user.id)
    assert any(r.role_id == 2 for r in roles)
```

---

## 5. マルチテナントテスト

### 5.1 データ分離テスト

#### TEST-MT-001: 組織間データ分離テスト
```python
def test_organization_data_isolation() -> None:
    """異なる組織のデータが分離されることを確認"""
    # Given: 2つの組織とユーザー
    org1 = create_test_organization("ORG1")
    org2 = create_test_organization("ORG2")
    
    user1 = create_user_in_organization(org1)
    user2 = create_user_in_organization(org2)
    
    # 各組織に部門作成
    dept1 = create_department(org1, "DEPT1")
    dept2 = create_department(org2, "DEPT2")
    
    # When: 各ユーザーで部門取得
    depts_user1 = dept_service.get_departments(user1)
    depts_user2 = dept_service.get_departments(user2)
    
    # Then: 自組織のデータのみ
    assert len(depts_user1) == 1
    assert depts_user1[0].id == dept1.id
    
    assert len(depts_user2) == 1
    assert depts_user2[0].id == dept2.id
```

### 5.2 権限分離テスト

#### TEST-MT-002: 組織間権限分離テスト
```python
def test_cross_organization_permission_denied() -> None:
    """他組織のリソースにアクセスできないことを確認"""
    # Given: 組織1の管理者
    org1 = create_test_organization("ORG1")
    org2 = create_test_organization("ORG2")
    admin1 = create_org_admin(org1)
    
    # When: 組織2のデータ更新試行
    with pytest.raises(PermissionDenied):
        org_service.update_organization(
            org_id=org2.id,
            data={"name": "不正な更新"},
            user=admin1
        )
```

---

## 6. セキュリティテスト

### 6.1 SQL インジェクション対策テスト

#### TEST-SEC-001: 組織検索SQLインジェクションテスト
```python
def test_organization_search_sql_injection() -> None:
    """SQLインジェクションが防止されることを確認"""
    # When: 悪意のある検索文字列
    response = client.get(
        "/api/v1/organizations",
        params={"search": "'; DROP TABLE organizations; --"},
        headers=get_auth_header()
    )
    
    # Then: 正常に処理される（エラーなし）
    assert response.status_code == 200
    
    # テーブルが削除されていない
    assert Organization.query.count() > 0
```

### 6.2 権限昇格防止テスト

#### TEST-SEC-002: 権限昇格防止テスト
```python
def test_prevent_privilege_escalation() -> None:
    """一般ユーザーが自身に管理者権限を付与できないことを確認"""
    # Given: 一般ユーザー
    user = create_test_user()
    token = get_user_token(user)
    
    # When: 自身に管理者ロール付与試行
    response = client.post(
        f"/api/v1/users/{user.id}/roles",
        json={"role_id": 1},  # SYSTEM_ADMIN
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then: 権限エラー
    assert response.status_code == 403
```

---

## 7. パフォーマンステスト

### 7.1 大量データテスト

#### TEST-PERF-001: 大量組織でのクエリ性能
```python
def test_large_organization_query_performance() -> None:
    """1000組織でのクエリが高速であることを確認"""
    # Given: 1000組織
    for i in range(1000):
        create_test_organization(f"ORG{i:04d}")
    
    # When: 組織一覧取得
    start_time = time.time()
    orgs = org_service.get_organizations(page=1, limit=20)
    elapsed = time.time() - start_time
    
    # Then: 200ms以内
    assert elapsed < 0.2
    assert len(orgs.items) == 20
```

### 7.2 階層データ性能テスト

#### TEST-PERF-002: 深い階層での性能
```python
def test_department_tree_performance() -> None:
    """100部門の階層取得が高速であることを確認"""
    # Given: 100部門の階層構造
    org = create_test_organization()
    create_department_tree(org, depth=2, width=10)  # 100部門
    
    # When: 階層取得
    start_time = time.time()
    tree = dept_service.get_department_tree(org.id)
    elapsed = time.time() - start_time
    
    # Then: 100ms以内
    assert elapsed < 0.1
```

---

## 8. 監査ログテスト

### 8.1 操作記録テスト

#### TEST-AUDIT-001: 組織作成監査ログテスト
```python
def test_organization_creation_audit_log() -> None:
    """組織作成が監査ログに記録されることを確認"""
    # Given: 監査ログカウント
    before_count = AuditLog.query.count()
    
    # When: 組織作成
    org = org_service.create_organization(
        data={"code": "AUDIT", "name": "監査テスト"},
        user=get_test_admin()
    )
    
    # Then: ログ記録
    after_count = AuditLog.query.count()
    assert after_count == before_count + 1
    
    log = AuditLog.query.order_by(AuditLog.id.desc()).first()
    assert log.action == "create"
    assert log.resource_type == "organization"
    assert log.resource_id == org.id
```

---

## 9. エラーハンドリングテスト

### 9.1 バリデーションエラーテスト

#### TEST-ERR-001: 必須フィールド欠落テスト
```python
def test_organization_required_fields() -> None:
    """必須フィールド欠落時のエラーを確認"""
    # When: コードなしで作成
    response = client.post(
        "/api/v1/organizations",
        json={"name": "名前のみ"},
        headers=get_admin_header()
    )
    
    # Then: バリデーションエラー
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"] == ["body", "code"] for e in errors)
```

---

## 10. テスト実行計画

### 10.1 実行順序
1. モデル単体テスト
2. サービス層テスト
3. API統合テスト
4. マルチテナントテスト
5. セキュリティテスト
6. パフォーマンステスト

### 10.2 合格基準
- 全テストケース合格
- コードカバレッジ85%以上
- パフォーマンス目標達成
- セキュリティ脆弱性ゼロ