# タスク管理機能テスト仕様書

**Document Number**: ITDO-ERP-TEST-004  
**Version**: 1.0  
**Date**: 2025年7月6日  
**Author**: Claude Code AI  
**Reviewer**: ootakazuhiko

---

## 1. テスト概要

### 1.1 目的
タスク管理機能の品質保証のため、包括的なテストを実施します。

### 1.2 テスト範囲
- ユニットテスト: TaskServiceのビジネスロジック
- 統合テスト: API エンドポイントの動作確認
- セキュリティテスト: 認証・認可・データ分離

### 1.3 テスト環境
- Backend: Python 3.13 + FastAPI + pytest
- Database: In-memory SQLite (テスト用)
- 認証: モックJWT

---

## 2. テストケース一覧

### 2.1 ユニットテスト

#### TaskService テスト

| ID | テストケース | 説明 | 期待結果 |
|----|------------|------|---------|
| TASK-U-001 | test_create_task_success | 正常なタスク作成 | タスクが作成される |
| TASK-U-002 | test_create_task_invalid_project | 無効なプロジェクトID | ValidationError |
| TASK-U-003 | test_create_task_no_permission | 権限なしでタスク作成 | PermissionDenied |
| TASK-U-004 | test_get_task_success | タスク詳細取得成功 | タスク情報返却 |
| TASK-U-005 | test_get_task_not_found | 存在しないタスク取得 | TaskNotFound |
| TASK-U-006 | test_update_task_success | タスク更新成功 | 更新された情報返却 |
| TASK-U-007 | test_update_task_no_permission | 権限なしで更新 | PermissionDenied |
| TASK-U-008 | test_delete_task_success | タスク削除成功 | 論理削除される |
| TASK-U-009 | test_delete_task_with_dependencies | 依存関係があるタスク削除 | DependencyError |
| TASK-U-010 | test_list_tasks_with_filters | フィルタ付き一覧取得 | 条件に合うタスクのみ |
| TASK-U-011 | test_list_tasks_pagination | ページネーション動作 | 指定ページのデータ |
| TASK-U-012 | test_list_tasks_sorting | ソート機能 | 指定順序で返却 |

#### ステータス管理テスト

| ID | テストケース | 説明 | 期待結果 |
|----|------------|------|---------|
| TASK-U-013 | test_update_status_valid_transition | 有効なステータス遷移 | ステータス更新成功 |
| TASK-U-014 | test_update_status_invalid_transition | 無効なステータス遷移 | InvalidTransition |
| TASK-U-015 | test_get_status_history | ステータス履歴取得 | 履歴リスト返却 |

#### 担当者管理テスト

| ID | テストケース | 説明 | 期待結果 |
|----|------------|------|---------|
| TASK-U-016 | test_assign_user_success | 担当者割り当て成功 | 割り当て完了 |
| TASK-U-017 | test_assign_invalid_user | 無効なユーザー割り当て | UserNotFound |
| TASK-U-018 | test_assign_user_different_org | 他組織ユーザー割り当て | PermissionDenied |
| TASK-U-019 | test_unassign_user_success | 担当者解除成功 | 解除完了 |
| TASK-U-020 | test_bulk_assign_users | 複数担当者一括割り当て | 全員割り当て完了 |

#### 期限・優先度管理テスト

| ID | テストケース | 説明 | 期待結果 |
|----|------------|------|---------|
| TASK-U-021 | test_set_due_date_success | 期限設定成功 | 期限が設定される |
| TASK-U-022 | test_set_past_due_date | 過去の期限設定 | ValidationError |
| TASK-U-023 | test_get_overdue_tasks | 期限超過タスク取得 | 期限超過リスト |
| TASK-U-024 | test_set_priority_success | 優先度設定成功 | 優先度更新 |

#### 依存関係管理テスト

| ID | テストケース | 説明 | 期待結果 |
|----|------------|------|---------|
| TASK-U-025 | test_add_dependency_success | 依存関係追加成功 | 依存関係作成 |
| TASK-U-026 | test_add_circular_dependency | 循環依存の検出 | CircularDependency |
| TASK-U-027 | test_get_dependencies | 依存関係取得 | 依存関係リスト |
| TASK-U-028 | test_remove_dependency | 依存関係削除 | 削除成功 |

### 2.2 統合テスト

#### API エンドポイントテスト

| ID | テストケース | 説明 | 期待結果 |
|----|------------|------|---------|
| TASK-I-001 | test_create_task_api | POST /api/v1/tasks | 201 Created |
| TASK-I-002 | test_list_tasks_api | GET /api/v1/tasks | 200 OK |
| TASK-I-003 | test_get_task_detail_api | GET /api/v1/tasks/{id} | 200 OK |
| TASK-I-004 | test_update_task_api | PATCH /api/v1/tasks/{id} | 200 OK |
| TASK-I-005 | test_delete_task_api | DELETE /api/v1/tasks/{id} | 204 No Content |
| TASK-I-006 | test_update_status_api | POST /api/v1/tasks/{id}/status | 200 OK |
| TASK-I-007 | test_bulk_update_api | POST /api/v1/tasks/bulk/status | 200 OK |
| TASK-I-008 | test_search_tasks_api | GET /api/v1/tasks?q=keyword | 200 OK |

### 2.3 セキュリティテスト

| ID | テストケース | 説明 | 期待結果 |
|----|------------|------|---------|
| TASK-S-001 | test_unauthorized_access | 認証なしでアクセス | 401 Unauthorized |
| TASK-S-002 | test_cross_org_access | 他組織のタスクアクセス | 403 Forbidden |
| TASK-S-003 | test_sql_injection | SQLインジェクション防止 | 400 Bad Request |
| TASK-S-004 | test_xss_prevention | XSS攻撃防止 | サニタイズされる |
| TASK-S-005 | test_rate_limiting | レート制限 | 429 Too Many Requests |
| TASK-S-006 | test_input_validation | 入力値検証 | 422 Unprocessable |

---

## 3. テストデータ

### 3.1 基本テストデータ
```python
# テスト組織
test_org = {
    "id": 1,
    "name": "テスト組織"
}

# テストユーザー
test_users = [
    {"id": 1, "name": "管理者", "role": "admin", "org_id": 1},
    {"id": 2, "name": "一般ユーザー", "role": "member", "org_id": 1},
    {"id": 3, "name": "他組織ユーザー", "role": "member", "org_id": 2}
]

# テストプロジェクト
test_project = {
    "id": 1,
    "name": "テストプロジェクト",
    "organization_id": 1
}

# テストタスク
test_tasks = [
    {
        "id": 1,
        "title": "タスク1",
        "status": "not_started",
        "priority": "medium",
        "project_id": 1
    },
    {
        "id": 2,
        "title": "タスク2",
        "status": "in_progress",
        "priority": "high",
        "project_id": 1,
        "assignee_ids": [2]
    }
]
```

### 3.2 エッジケーステストデータ
```python
# 長いタイトル
long_title = "A" * 200  # 最大長

# 長い説明
long_description = "B" * 5000  # 最大長

# 特殊文字を含むデータ
special_chars_data = {
    "title": "'; DROP TABLE tasks; --",
    "description": "<script>alert('XSS')</script>"
}

# 大量データ
bulk_task_ids = list(range(1, 101))  # 100件
```

---

## 4. テスト実行計画

### 4.1 テストフェーズ
1. **Phase 1**: ユニットテスト実装（TASK-U-001〜028）
2. **Phase 2**: 統合テスト実装（TASK-I-001〜008）
3. **Phase 3**: セキュリティテスト実装（TASK-S-001〜006）

### 4.2 テストカバレッジ目標
- ライン: 80%以上
- ブランチ: 70%以上
- 関数: 90%以上

### 4.3 パフォーマンステスト基準
- タスク作成: 100ms以内
- タスク一覧（100件）: 200ms以内
- タスク検索: 500ms以内

---

## 5. テスト自動化

### 5.1 CI/CDパイプライン
```yaml
test:
  script:
    - export PATH="/root/.local/bin:$PATH"
    - uv run pytest tests/unit/
    - uv run pytest tests/integration/
    - uv run pytest tests/security/
    - uv run pytest --cov=app --cov-report=html
```

### 5.2 テストコマンド
```bash
# 全テスト実行
export PATH="/root/.local/bin:$PATH" && uv run pytest tests/test_task_management/

# カバレッジ付き実行
export PATH="/root/.local/bin:$PATH" && uv run pytest tests/test_task_management/ --cov=app.services.task --cov=app.api.v1.tasks

# 特定のテストのみ
export PATH="/root/.local/bin:$PATH" && uv run pytest tests/test_task_management/unit/test_task_service.py -v
```

---

## 6. テスト成功基準

### 6.1 機能テスト
- 全テストケースがPASS
- カバレッジ80%以上
- 重大なバグゼロ

### 6.2 非機能テスト
- パフォーマンス基準を満たす
- セキュリティ脆弱性なし
- エラーハンドリング適切

### 6.3 回帰テスト
- 既存機能への影響なし
- APIの後方互換性維持

---

## 7. リスクと対策

### 7.1 識別されたリスク
1. **データベース依存**: テスト用DBの準備が必要
   - 対策: In-memory SQLite使用
   
2. **外部サービス依存**: 通知機能のテスト
   - 対策: モックサービス使用
   
3. **並行処理**: 同時アクセステスト
   - 対策: マルチスレッドテスト実装

### 7.2 テスト制限事項
- WebSocket通知機能は別途テスト
- 実際のメール送信はモック化
- 大規模データ（10,000件以上）は別途性能テスト

---

## 8. 品質メトリクス

### 8.1 測定項目
- テストケース実行率: 100%
- バグ検出率
- テスト実行時間
- カバレッジ率

### 8.2 品質目標
- 重大度高のバグ: 0件
- 重大度中のバグ: 3件以下
- テスト実行時間: 5分以内

---

## 9. 承認

**作成者**: Claude Code AI  
**日付**: 2025年7月6日  
**バージョン**: 1.0  

**レビュー・承認**:  
承認者: _________________  
日付: _________________