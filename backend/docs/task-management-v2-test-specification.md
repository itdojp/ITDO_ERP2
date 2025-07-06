# タスク管理機能テスト仕様書 v2

## 1. 概要

本テスト仕様書は、型安全なタスク管理機能の品質を保証するためのテスト計画を定義します。
TDD（テスト駆動開発）のアプローチに従い、実装前にすべてのテストケースを定義します。

## 2. テスト戦略

### 2.1 テストレベル
- **単体テスト**: リポジトリ、サービス、モデルの個別機能
- **統合テスト**: API エンドポイントの動作確認
- **パフォーマンステスト**: 負荷テスト、応答時間測定
- **セキュリティテスト**: 認証・認可、入力検証

### 2.2 テストカバレッジ目標
- 単体テスト: 90%以上
- 統合テスト: 80%以上
- 全体: 85%以上

## 3. テストケース

### 3.1 単体テスト

#### 3.1.1 Task モデルテスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| UT-TASK-001 | タスク作成（必須フィールドのみ） | タスクが作成される |
| UT-TASK-002 | タスク作成（全フィールド） | すべてのフィールドが正しく設定される |
| UT-TASK-003 | タイトル文字数制限（200文字） | 検証エラー |
| UT-TASK-004 | 不正なステータス値 | 検証エラー |
| UT-TASK-005 | 不正な優先度値 | 検証エラー |
| UT-TASK-006 | 進捗率範囲（0-100） | 検証エラー |
| UT-TASK-007 | ソフトデリート実行 | deleted_atが設定される |
| UT-TASK-008 | 楽観的ロック更新 | versionがインクリメントされる |

#### 3.1.2 TaskAssignment モデルテスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| UT-ASSIGN-001 | 担当者割り当て作成 | 割り当てが作成される |
| UT-ASSIGN-002 | 重複割り当て防止 | 検証エラー |
| UT-ASSIGN-003 | 不正な役割値 | 検証エラー |
| UT-ASSIGN-004 | 存在しないユーザーID | 外部キー制約エラー |

#### 3.1.3 TaskDependency モデルテスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| UT-DEP-001 | 依存関係作成（FS型） | 依存関係が作成される |
| UT-DEP-002 | 自己参照防止 | 検証エラー |
| UT-DEP-003 | 不正な依存タイプ | 検証エラー |
| UT-DEP-004 | ラグタイム設定 | 正しく設定される |

#### 3.1.4 TaskRepository テスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| UT-REPO-001 | タスク検索（キーワード） | 該当タスクが返される |
| UT-REPO-002 | タスク検索（ステータス） | フィルタが適用される |
| UT-REPO-003 | タスク検索（複数条件） | AND条件で検索される |
| UT-REPO-004 | ページネーション | 正しくページングされる |
| UT-REPO-005 | ソート（期限昇順） | 期限順にソートされる |
| UT-REPO-006 | 担当タスク取得 | ユーザーのタスクのみ返される |
| UT-REPO-007 | 期限切れタスク取得 | 期限切れのみ返される |
| UT-REPO-008 | 循環依存検出 | Trueが返される |
| UT-REPO-009 | 依存関係ツリー取得 | 正しい階層構造が返される |
| UT-REPO-010 | 楽観的ロックチェック | バージョン不一致でエラー |

#### 3.1.5 TaskService テスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| UT-SVC-001 | タスク作成（権限あり） | タスクが作成される |
| UT-SVC-002 | タスク作成（権限なし） | PermissionDeniedエラー |
| UT-SVC-003 | ステータス更新（有効な遷移） | ステータスが更新される |
| UT-SVC-004 | ステータス更新（無効な遷移） | InvalidTransitionエラー |
| UT-SVC-005 | 担当者割り当て（通知付き） | 割り当てと通知が作成される |
| UT-SVC-006 | 複数担当者一括割り当て | すべて割り当てられる |
| UT-SVC-007 | 依存関係追加（循環なし） | 依存関係が作成される |
| UT-SVC-008 | 依存関係追加（循環あり） | CircularDependencyエラー |
| UT-SVC-009 | タスク削除（依存なし） | ソフトデリートされる |
| UT-SVC-010 | タスク削除（依存あり） | DependencyExistsエラー |
| UT-SVC-011 | ワークロード計算 | 正しい負荷が計算される |
| UT-SVC-012 | クリティカルパス計算 | 正しいパスが返される |

### 3.2 統合テスト

#### 3.2.1 タスクAPI テスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| IT-API-001 | POST /tasks - 正常系 | 201 Created |
| IT-API-002 | POST /tasks - 検証エラー | 422 Unprocessable Entity |
| IT-API-003 | POST /tasks - 認証なし | 401 Unauthorized |
| IT-API-004 | GET /tasks - フィルタなし | 200 OK、全タスク |
| IT-API-005 | GET /tasks - フィルタあり | 200 OK、フィルタ適用 |
| IT-API-006 | GET /tasks/{id} - 存在する | 200 OK |
| IT-API-007 | GET /tasks/{id} - 存在しない | 404 Not Found |
| IT-API-008 | PATCH /tasks/{id} - 正常系 | 200 OK |
| IT-API-009 | PATCH /tasks/{id} - 楽観的ロック | 409 Conflict |
| IT-API-010 | DELETE /tasks/{id} - 正常系 | 204 No Content |

#### 3.2.2 割り当てAPI テスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| IT-ASSIGN-001 | POST /tasks/{id}/assignments | 201 Created |
| IT-ASSIGN-002 | DELETE /tasks/{id}/assignments/{user_id} | 204 No Content |
| IT-ASSIGN-003 | GET /users/{id}/tasks | 200 OK、担当タスク一覧 |

#### 3.2.3 依存関係API テスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| IT-DEP-001 | POST /tasks/{id}/dependencies | 201 Created |
| IT-DEP-002 | POST /tasks/{id}/dependencies - 循環 | 400 Bad Request |
| IT-DEP-003 | GET /tasks/{id}/dependencies | 200 OK、依存関係一覧 |
| IT-DEP-004 | DELETE /dependencies/{id} | 204 No Content |

#### 3.2.4 WebSocket テスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| IT-WS-001 | WebSocket接続 | 接続成功 |
| IT-WS-002 | タスク更新イベント受信 | イベントが配信される |
| IT-WS-003 | 権限外プロジェクト | 接続拒否 |
| IT-WS-004 | 同時接続数上限 | 適切にハンドリング |

### 3.3 パフォーマンステスト

| ID | テストケース | 目標値 | 条件 |
|----|------------|-------|-----|
| PT-001 | タスク一覧取得 | < 200ms | 1000件 |
| PT-002 | タスク検索 | < 500ms | 10000件中検索 |
| PT-003 | タスク作成 | < 100ms | 単一作成 |
| PT-004 | 一括更新 | < 1s | 100件更新 |
| PT-005 | 同時編集 | エラーなし | 10ユーザー同時 |
| PT-006 | WebSocket同時接続 | 1000接続 | メモリ使用量監視 |

### 3.4 セキュリティテスト

| ID | テストケース | 期待結果 |
|----|------------|---------|
| ST-001 | SQLインジェクション | 攻撃が無効化される |
| ST-002 | XSS攻撃 | HTMLがエスケープされる |
| ST-003 | 権限昇格試行 | 403 Forbidden |
| ST-004 | 他組織データアクセス | 404 Not Found |
| ST-005 | ファイルアップロード（ウイルス） | アップロード拒否 |
| ST-006 | ファイルアップロード（大容量） | 413 Payload Too Large |

## 4. テストデータ

### 4.1 基本テストデータ

```python
# プロジェクト
test_project = {
    "id": 1,
    "name": "テストプロジェクト",
    "organization_id": 1
}

# ユーザー
test_users = [
    {"id": 1, "email": "manager@example.com", "role": "PROJECT_MANAGER"},
    {"id": 2, "email": "member1@example.com", "role": "DEVELOPER"},
    {"id": 3, "email": "member2@example.com", "role": "DEVELOPER"}
]

# タスク
test_tasks = [
    {
        "id": 1,
        "title": "要件定義",
        "status": "COMPLETED",
        "priority": "HIGH"
    },
    {
        "id": 2,
        "title": "設計",
        "status": "IN_PROGRESS",
        "priority": "HIGH"
    },
    {
        "id": 3,
        "title": "実装",
        "status": "NOT_STARTED",
        "priority": "MEDIUM"
    }
]
```

### 4.2 エッジケースデータ

```python
# 最大文字数
max_title = "あ" * 200

# 特殊文字
special_chars = "'; DROP TABLE tasks; --"

# 日付境界値
edge_dates = [
    "2024-01-01T00:00:00Z",  # 年始
    "2024-12-31T23:59:59Z",  # 年末
    "2024-02-29T00:00:00Z"   # うるう年
]
```

## 5. テスト環境

### 5.1 テストデータベース
- PostgreSQL 15（インメモリ）
- テスト実行ごとにクリーンアップ

### 5.2 モック/スタブ
- 通知サービス: モック
- ファイルストレージ: ローカルモック
- ウイルススキャン: スタブ

### 5.3 テストツール
- pytest: テストフレームワーク
- pytest-asyncio: 非同期テスト
- factory-boy: テストデータ生成
- pytest-cov: カバレッジ測定
- locust: パフォーマンステスト

## 6. テスト実行計画

### 6.1 開発フェーズ
1. TDD Red: すべてのテストを失敗状態で実装
2. TDD Green: 機能実装してテストをパス
3. リファクタリング: コード品質向上

### 6.2 CI/CD統合
- プルリクエスト時: 単体テスト + 統合テスト
- マージ時: 全テスト実行
- デプロイ前: パフォーマンステスト

### 6.3 テスト実行コマンド

```bash
# 単体テストのみ
pytest tests/unit/test_task_management_v2/ -v

# 統合テストのみ
pytest tests/integration/test_task_management_v2/ -v

# カバレッジ付き全テスト
pytest tests/test_task_management_v2/ --cov=app --cov-report=html

# パフォーマンステスト
locust -f tests/performance/test_task_performance.py
```

## 7. 品質基準

### 7.1 合格基準
- すべての必須テストケースがパス
- カバレッジ目標達成
- パフォーマンス目標達成
- セキュリティテスト合格

### 7.2 不具合管理
- Critical: 即時修正
- High: リリース前修正
- Medium: 次スプリント対応
- Low: バックログ追加

## 8. リスクと対策

| リスク | 影響度 | 対策 |
|-------|-------|-----|
| WebSocket負荷 | 高 | ロードバランサー導入 |
| 大量データ | 中 | ページネーション強制 |
| 同時編集競合 | 中 | 楽観的ロック実装 |
| 依存関係複雑化 | 低 | 階層制限導入 |