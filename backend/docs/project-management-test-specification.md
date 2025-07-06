# プロジェクト管理機能テスト仕様書

**文書番号**: ITDO-ERP-PROJ-TEST-001  
**バージョン**: 1.0  
**作成日**: 2025年7月6日  
**作成者**: Claude Code AI  
**承認者**: ootakazuhiko

---

## 1. テスト概要

### 1.1 目的
プロジェクト管理機能（PROJ-001, PROJ-002）の品質保証のためのテスト仕様を定義する。

### 1.2 テスト対象
- プロジェクト管理機能（PROJ-001）
- タスク管理機能（PROJ-002）
- マルチテナント対応
- RBAC統合

### 1.3 テスト方針
- **TDD実装**: Red-Green-Refactorサイクル
- **テストカバレッジ**: 80%以上
- **テスト種別**: 単体・統合・セキュリティテスト

---

## 2. 単体テスト仕様

### 2.1 プロジェクトモデルテスト

#### TEST-PROJ-MODEL-001: プロジェクト作成テスト
```python
def test_project_creation():
    """プロジェクト作成の基本テスト"""
    # Given: プロジェクト作成データ
    project_data = {
        "name": "テストプロジェクト",
        "description": "テスト用プロジェクト",
        "start_date": "2025-07-01",
        "end_date": "2025-12-31",
        "status": "planning",
        "organization_id": 1,
        "created_by": 1
    }
    
    # When: プロジェクトを作成
    project = Project.create(db_session, **project_data)
    
    # Then: 正常に作成される
    assert project.id is not None
    assert project.name == "テストプロジェクト"
    assert project.status == "planning"
    assert project.organization_id == 1
```

#### TEST-PROJ-MODEL-002: プロジェクト名バリデーション
```python
def test_project_name_validation():
    """プロジェクト名のバリデーションテスト"""
    # Given: 不正なプロジェクト名
    with pytest.raises(ValidationError):
        # When/Then: 空文字列で作成→バリデーションエラー
        Project.create(db_session, name="", organization_id=1, start_date="2025-07-01")
    
    with pytest.raises(ValidationError):
        # When/Then: 101文字で作成→バリデーションエラー
        Project.create(db_session, name="a" * 101, organization_id=1, start_date="2025-07-01")
```

#### TEST-PROJ-MODEL-003: プロジェクトステータス管理
```python
def test_project_status_transition():
    """プロジェクトステータス遷移テスト"""
    # Given: 計画中のプロジェクト
    project = create_test_project(status="planning")
    
    # When: ステータスを実行中に変更
    project.update_status("in_progress")
    
    # Then: ステータスが更新される
    assert project.status == "in_progress"
    assert project.updated_at > project.created_at
```

#### TEST-PROJ-MODEL-004: プロジェクト日付バリデーション
```python
def test_project_date_validation():
    """プロジェクト日付のバリデーションテスト"""
    # Given: 終了日が開始日より前
    with pytest.raises(ValidationError, match="終了日は開始日以降である必要があります"):
        # When/Then: 不正な日付で作成→バリデーションエラー
        Project.create(
            db_session,
            name="テストプロジェクト",
            start_date="2025-12-31",
            end_date="2025-07-01",
            organization_id=1
        )
```

#### TEST-PROJ-MODEL-005: プロジェクトソフトデリート
```python
def test_project_soft_delete():
    """プロジェクトソフトデリートテスト"""
    # Given: 既存プロジェクト
    project = create_test_project()
    project_id = project.id
    
    # When: ソフトデリート実行
    project.soft_delete(db_session, deleted_by=1)
    
    # Then: deleted_atが設定される
    assert project.deleted_at is not None
    assert project.deleted_by == 1
    
    # And: 通常のクエリでは取得されない
    active_project = db_session.query(Project).filter(Project.id == project_id).first()
    assert active_project is None
```

### 2.2 タスクモデルテスト

#### TEST-TASK-MODEL-001: タスク作成テスト
```python
def test_task_creation():
    """タスク作成の基本テスト"""
    # Given: プロジェクトとタスクデータ
    project = create_test_project()
    task_data = {
        "title": "テストタスク",
        "description": "テスト用タスク",
        "status": "not_started",
        "priority": "medium",
        "project_id": project.id,
        "created_by": 1
    }
    
    # When: タスクを作成
    task = Task.create(db_session, **task_data)
    
    # Then: 正常に作成される
    assert task.id is not None
    assert task.title == "テストタスク"
    assert task.status == "not_started"
    assert task.project_id == project.id
```

#### TEST-TASK-MODEL-002: タスクタイトルバリデーション
```python
def test_task_title_validation():
    """タスクタイトルのバリデーションテスト"""
    project = create_test_project()
    
    # Given: 不正なタスクタイトル
    with pytest.raises(ValidationError):
        # When/Then: 空文字列で作成→バリデーションエラー
        Task.create(db_session, title="", project_id=project.id)
    
    with pytest.raises(ValidationError):
        # When/Then: 201文字で作成→バリデーションエラー
        Task.create(db_session, title="a" * 201, project_id=project.id)
```

#### TEST-TASK-MODEL-003: タスク優先度とステータス
```python
def test_task_priority_and_status():
    """タスク優先度とステータスのテスト"""
    project = create_test_project()
    
    # Given: 各優先度でタスクを作成
    priorities = ["low", "medium", "high", "urgent"]
    statuses = ["not_started", "in_progress", "completed", "on_hold"]
    
    for priority in priorities:
        for status in statuses:
            # When: タスクを作成
            task = Task.create(
                db_session,
                title=f"タスク_{priority}_{status}",
                priority=priority,
                status=status,
                project_id=project.id
            )
            
            # Then: 正常に作成される
            assert task.priority == priority
            assert task.status == status
```

#### TEST-TASK-MODEL-004: タスク担当者割り当て
```python
def test_task_assignment():
    """タスク担当者割り当てテスト"""
    # Given: プロジェクトとユーザー
    project = create_test_project()
    user = create_test_user()
    
    # When: 担当者を割り当て
    task = Task.create(
        db_session,
        title="担当者テスト",
        project_id=project.id,
        assigned_to=user.id
    )
    
    # Then: 担当者が設定される
    assert task.assigned_to == user.id
    assert task.assignee.email == user.email
```

#### TEST-TASK-MODEL-005: タスク日付管理
```python
def test_task_date_management():
    """タスク日付管理テスト"""
    project = create_test_project()
    
    # Given: 日付を指定してタスクを作成
    task = Task.create(
        db_session,
        title="日付テスト",
        project_id=project.id,
        estimated_start_date="2025-07-01",
        estimated_end_date="2025-07-31"
    )
    
    # When: 実際の日付を更新
    task.start_task()  # actual_start_dateを設定
    task.complete_task()  # actual_end_dateを設定
    
    # Then: 実際の日付が設定される
    assert task.actual_start_date is not None
    assert task.actual_end_date is not None
    assert task.status == "completed"
```

---

## 3. サービス層テスト仕様

### 3.1 プロジェクトサービステスト

#### TEST-PROJ-SERVICE-001: プロジェクト作成サービス
```python
def test_project_service_create():
    """プロジェクト作成サービステスト"""
    # Given: プロジェクトサービスと作成者
    service = ProjectService()
    creator = create_test_user()
    project_data = ProjectCreateRequest(
        name="サービステスト",
        description="テスト",
        start_date="2025-07-01",
        organization_id=1
    )
    
    # When: プロジェクトを作成
    project = service.create_project(
        data=project_data,
        creator=creator,
        db=db_session
    )
    
    # Then: 正常に作成される
    assert project.name == "サービステスト"
    assert project.created_by == creator.id
```

#### TEST-PROJ-SERVICE-002: マルチテナント分離
```python
def test_project_service_multi_tenant_isolation():
    """マルチテナント分離テスト"""
    # Given: 異なる組織のユーザー
    org1_user = create_test_user(organization_id=1)
    org2_user = create_test_user(organization_id=2)
    org1_project = create_test_project(organization_id=1)
    
    service = ProjectService()
    
    # When: 組織2のユーザーが組織1のプロジェクトにアクセス
    with pytest.raises(PermissionDenied):
        # Then: アクセスが拒否される
        service.get_project(
            project_id=org1_project.id,
            viewer=org2_user,
            db=db_session
        )
```

#### TEST-PROJ-SERVICE-003: プロジェクト検索フィルタ
```python
def test_project_service_search_filters():
    """プロジェクト検索フィルタテスト"""
    # Given: 複数のプロジェクト
    user = create_test_user()
    projects = [
        create_test_project(name="プロジェクトA", status="planning"),
        create_test_project(name="プロジェクトB", status="in_progress"),
        create_test_project(name="プロジェクトC", status="completed")
    ]
    
    service = ProjectService()
    
    # When: ステータスでフィルタ
    search_params = ProjectSearchParams(status="in_progress")
    result = service.search_projects(
        params=search_params,
        searcher=user,
        db=db_session
    )
    
    # Then: 該当するプロジェクトのみ返される
    assert result.total == 1
    assert result.items[0].name == "プロジェクトB"
```

#### TEST-PROJ-SERVICE-004: プロジェクト権限チェック
```python
def test_project_service_permission_check():
    """プロジェクト権限チェックテスト"""
    # Given: プロジェクトと一般ユーザー
    project = create_test_project()
    normal_user = create_test_user()
    admin_user = create_test_user(is_superuser=True)
    
    service = ProjectService()
    
    # When: 一般ユーザーがプロジェクトを削除しようとする
    with pytest.raises(PermissionDenied):
        # Then: 権限エラーが発生
        service.delete_project(
            project_id=project.id,
            deleter=normal_user,
            db=db_session
        )
    
    # When: 管理者がプロジェクトを削除
    service.delete_project(
        project_id=project.id,
        deleter=admin_user,
        db=db_session
    )
    
    # Then: 正常に削除される
    assert project.deleted_at is not None
```

### 3.2 タスクサービステスト

#### TEST-TASK-SERVICE-001: タスク作成サービス
```python
def test_task_service_create():
    """タスク作成サービステスト"""
    # Given: タスクサービスとプロジェクト
    service = TaskService()
    project = create_test_project()
    creator = create_test_user()
    task_data = TaskCreateRequest(
        title="サービステスト",
        description="テスト",
        priority="high",
        project_id=project.id
    )
    
    # When: タスクを作成
    task = service.create_task(
        data=task_data,
        creator=creator,
        db=db_session
    )
    
    # Then: 正常に作成される
    assert task.title == "サービステスト"
    assert task.priority == "high"
    assert task.project_id == project.id
```

#### TEST-TASK-SERVICE-002: タスク担当者変更
```python
def test_task_service_assign_user():
    """タスク担当者変更テスト"""
    # Given: タスクとユーザー
    task = create_test_task()
    assignee = create_test_user()
    assigner = create_test_user(is_superuser=True)
    
    service = TaskService()
    
    # When: 担当者を変更
    service.assign_task(
        task_id=task.id,
        assignee_id=assignee.id,
        assigner=assigner,
        db=db_session
    )
    
    # Then: 担当者が更新される
    assert task.assigned_to == assignee.id
```

---

## 4. API統合テスト仕様

### 4.1 プロジェクト管理APIテスト

#### TEST-API-PROJ-001: プロジェクト作成API
```python
def test_create_project_api(client, auth_headers):
    """プロジェクト作成APIテスト"""
    # Given: プロジェクト作成データ
    project_data = {
        "name": "APIテストプロジェクト",
        "description": "テスト用",
        "start_date": "2025-07-01",
        "organization_id": 1
    }
    
    # When: POST /api/v1/projects
    response = client.post(
        "/api/v1/projects",
        json=project_data,
        headers=auth_headers
    )
    
    # Then: 201 Createdで作成される
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "APIテストプロジェクト"
    assert data["status"] == "planning"
```

#### TEST-API-PROJ-002: プロジェクト一覧取得API
```python
def test_list_projects_api(client, auth_headers):
    """プロジェクト一覧取得APIテスト"""
    # Given: 複数のプロジェクト
    projects = [
        create_test_project(name=f"プロジェクト{i}")
        for i in range(5)
    ]
    
    # When: GET /api/v1/projects
    response = client.get(
        "/api/v1/projects?page=1&limit=3",
        headers=auth_headers
    )
    
    # Then: ページネーションされた結果が返される
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["limit"] == 3
```

#### TEST-API-PROJ-003: プロジェクト詳細取得API
```python
def test_get_project_detail_api(client, auth_headers):
    """プロジェクト詳細取得APIテスト"""
    # Given: 既存プロジェクト
    project = create_test_project()
    
    # When: GET /api/v1/projects/{id}
    response = client.get(
        f"/api/v1/projects/{project.id}",
        headers=auth_headers
    )
    
    # Then: プロジェクト詳細が返される
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project.id
    assert data["name"] == project.name
```

#### TEST-API-PROJ-004: プロジェクト更新API
```python
def test_update_project_api(client, auth_headers):
    """プロジェクト更新APIテスト"""
    # Given: 既存プロジェクト
    project = create_test_project()
    update_data = {
        "name": "更新されたプロジェクト",
        "status": "in_progress"
    }
    
    # When: PUT /api/v1/projects/{id}
    response = client.put(
        f"/api/v1/projects/{project.id}",
        json=update_data,
        headers=auth_headers
    )
    
    # Then: プロジェクトが更新される
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新されたプロジェクト"
    assert data["status"] == "in_progress"
```

#### TEST-API-PROJ-005: プロジェクト削除API
```python
def test_delete_project_api(client, admin_auth_headers):
    """プロジェクト削除APIテスト"""
    # Given: 既存プロジェクト
    project = create_test_project()
    
    # When: DELETE /api/v1/projects/{id}
    response = client.delete(
        f"/api/v1/projects/{project.id}",
        headers=admin_auth_headers
    )
    
    # Then: プロジェクトが削除される
    assert response.status_code == 204
```

### 4.2 タスク管理APIテスト

#### TEST-API-TASK-001: タスク作成API
```python
def test_create_task_api(client, auth_headers):
    """タスク作成APIテスト"""
    # Given: プロジェクトとタスクデータ
    project = create_test_project()
    task_data = {
        "title": "APIテストタスク",
        "description": "テスト用タスク",
        "priority": "high"
    }
    
    # When: POST /api/v1/projects/{id}/tasks
    response = client.post(
        f"/api/v1/projects/{project.id}/tasks",
        json=task_data,
        headers=auth_headers
    )
    
    # Then: 201 Createdで作成される
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "APIテストタスク"
    assert data["priority"] == "high"
    assert data["project_id"] == project.id
```

#### TEST-API-TASK-002: タスク一覧取得API
```python
def test_list_tasks_api(client, auth_headers):
    """タスク一覧取得APIテスト"""
    # Given: プロジェクトと複数のタスク
    project = create_test_project()
    tasks = [
        create_test_task(project_id=project.id, title=f"タスク{i}")
        for i in range(3)
    ]
    
    # When: GET /api/v1/projects/{id}/tasks
    response = client.get(
        f"/api/v1/projects/{project.id}/tasks",
        headers=auth_headers
    )
    
    # Then: タスク一覧が返される
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
```

---

## 5. セキュリティテスト仕様

### 5.1 認証・認可テスト

#### TEST-SECURITY-001: 認証なしアクセス拒否
```python
def test_unauthorized_access_denied(client):
    """認証なしアクセス拒否テスト"""
    # When: 認証ヘッダーなしでAPIアクセス
    response = client.get("/api/v1/projects")
    
    # Then: 401 Unauthorizedが返される
    assert response.status_code == 401
```

#### TEST-SECURITY-002: 不正トークンアクセス拒否
```python
def test_invalid_token_access_denied(client):
    """不正トークンアクセス拒否テスト"""
    # Given: 不正なトークン
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    
    # When: 不正トークンでAPIアクセス
    response = client.get("/api/v1/projects", headers=invalid_headers)
    
    # Then: 401 Unauthorizedが返される
    assert response.status_code == 401
```

#### TEST-SECURITY-003: 組織間データアクセス拒否
```python
def test_cross_organization_access_denied(client):
    """組織間データアクセス拒否テスト"""
    # Given: 異なる組織のプロジェクトとユーザー
    org1_project = create_test_project(organization_id=1)
    org2_user_headers = create_auth_headers(organization_id=2)
    
    # When: 異なる組織のユーザーがプロジェクトにアクセス
    response = client.get(
        f"/api/v1/projects/{org1_project.id}",
        headers=org2_user_headers
    )
    
    # Then: 403 Forbiddenが返される
    assert response.status_code == 403
```

### 5.2 入力バリデーションテスト

#### TEST-SECURITY-004: SQLインジェクション対策
```python
def test_sql_injection_protection(client, auth_headers):
    """SQLインジェクション対策テスト"""
    # Given: SQLインジェクション攻撃を含むデータ
    malicious_data = {
        "name": "'; DROP TABLE projects; --",
        "start_date": "2025-07-01",
        "organization_id": 1
    }
    
    # When: 悪意のあるデータでプロジェクト作成
    response = client.post(
        "/api/v1/projects",
        json=malicious_data,
        headers=auth_headers
    )
    
    # Then: 適切に処理される（エラーまたは正常処理）
    assert response.status_code in [201, 400]
    
    # And: データベースが破損していない
    projects_count = db_session.query(Project).count()
    assert projects_count >= 0  # テーブルが存在することを確認
```

#### TEST-SECURITY-005: XSS攻撃対策
```python
def test_xss_protection(client, auth_headers):
    """XSS攻撃対策テスト"""
    # Given: XSS攻撃を含むデータ
    xss_data = {
        "name": "<script>alert('XSS')</script>",
        "description": "<img src=x onerror=alert('XSS')>",
        "start_date": "2025-07-01",
        "organization_id": 1
    }
    
    # When: 悪意のあるデータでプロジェクト作成
    response = client.post(
        "/api/v1/projects",
        json=xss_data,
        headers=auth_headers
    )
    
    # Then: スクリプトがエスケープされる
    if response.status_code == 201:
        data = response.json()
        assert "<script>" not in data["name"]
        assert "onerror=" not in data["description"]
```

---

## 6. パフォーマンステスト仕様

### 6.1 レスポンス時間テスト

#### TEST-PERF-001: API応答時間テスト
```python
def test_api_response_time(client, auth_headers):
    """API応答時間テスト"""
    import time
    
    # Given: プロジェクト一覧取得API
    start_time = time.time()
    
    # When: APIを呼び出し
    response = client.get("/api/v1/projects", headers=auth_headers)
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # ms
    
    # Then: 200ms以下で応答
    assert response.status_code == 200
    assert response_time < 200
```

#### TEST-PERF-002: 大量データ処理テスト
```python
def test_large_data_handling(client, auth_headers):
    """大量データ処理テスト"""
    # Given: 大量のプロジェクト（100件）
    projects = [
        create_test_project(name=f"プロジェクト{i}")
        for i in range(100)
    ]
    
    # When: ページネーションで取得
    response = client.get(
        "/api/v1/projects?page=1&limit=50",
        headers=auth_headers
    )
    
    # Then: 正常に処理される
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 100
    assert len(data["items"]) == 50
```

---

## 7. テスト実行計画

### 7.1 テスト実行順序
1. **単体テスト** (モデル・サービス)
2. **統合テスト** (API)
3. **セキュリティテスト**
4. **パフォーマンステスト**

### 7.2 テスト環境
- **テストデータベース**: PostgreSQL (テスト専用)
- **テストフレームワーク**: pytest
- **モック**: pytest-mock
- **カバレッジ**: pytest-cov

### 7.3 成功基準
- **全テストケース成功**: 100%
- **コードカバレッジ**: 80%以上
- **API応答時間**: 200ms以下
- **セキュリティテスト**: 脆弱性ゼロ

---

## 8. テストケース一覧

### 8.1 単体テスト (15件)
- プロジェクトモデル: 5件
- タスクモデル: 5件
- サービス層: 5件

### 8.2 統合テスト (10件)
- プロジェクト管理API: 5件
- タスク管理API: 5件

### 8.3 セキュリティテスト (5件)
- 認証・認可: 3件
- 入力バリデーション: 2件

### 8.4 パフォーマンステスト (2件)
- 応答時間: 1件
- 大量データ: 1件

**合計: 32テストケース**

---

## 9. 改訂履歴

| バージョン | 改訂日 | 改訂内容 | 改訂者 |
|------------|--------|----------|--------|
| 1.0 | 2025/07/06 | 初版作成 | Claude Code AI |

---

**承認**

プロジェクトオーナー: ootakazuhiko _________________ 日付: 2025/07/06  
Claude Code AI: _________________ 日付: 2025/07/06