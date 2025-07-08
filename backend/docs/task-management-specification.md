# タスク管理機能仕様書

**Document Number**: ITDO-ERP-SPEC-004  
**Version**: 1.0  
**Date**: 2025年7月6日  
**Author**: Claude Code AI  
**Reviewer**: ootakazuhiko

---

## 1. 概要

### 1.1 目的
ITDO ERPシステムにおけるプロジェクト管理機能の中核となるタスク管理機能を実装します。本機能により、プロジェクト内のタスクの作成、管理、追跡が可能になります。

### 1.2 スコープ
- タスクのCRUD操作（作成・読取・更新・削除）
- タスクステータス管理
- タスク担当者管理
- タスク期限管理
- タスク優先度管理
- タスク間の依存関係管理

### 1.3 用語定義
- **タスク（Task）**: プロジェクト内の作業単位
- **ステータス（Status）**: タスクの進行状態（未着手、進行中、完了、保留）
- **担当者（Assignee）**: タスクを実行する責任者
- **優先度（Priority）**: タスクの重要度（高、中、低）

---

## 2. 機能要件

### 2.1 タスク管理

#### 2.1.1 タスク作成（TASK-001）
**説明**: 新規タスクを作成する  
**入力**:
- タイトル（必須、最大200文字）
- 説明（任意、最大5000文字）
- プロジェクトID（必須）
- 担当者ID（任意）
- 期限（任意）
- 優先度（必須、デフォルト: 中）
- 親タスクID（任意）
- タグ（任意、複数可）

**処理**:
1. 入力値の検証
2. プロジェクトへのアクセス権限確認
3. タスクエンティティの作成
4. データベースへの保存
5. 担当者への通知（設定されている場合）

**出力**: 作成されたタスクの詳細情報

#### 2.1.2 タスク一覧取得（TASK-002）
**説明**: タスク一覧を取得する  
**入力**:
- プロジェクトID（任意）
- ステータス（任意）
- 担当者ID（任意）
- 期限範囲（任意）
- 優先度（任意）
- 検索キーワード（任意）
- ソート条件（任意）
- ページネーション（任意）

**処理**:
1. アクセス権限の確認
2. フィルタ条件の適用
3. 検索処理
4. ソート処理
5. ページネーション処理

**出力**: タスク一覧（ページネーション情報付き）

#### 2.1.3 タスク詳細取得（TASK-003）
**説明**: 特定のタスクの詳細情報を取得する  
**入力**: タスクID  
**処理**:
1. タスクの存在確認
2. アクセス権限の確認
3. 関連情報の取得（担当者、プロジェクト、サブタスクなど）

**出力**: タスクの詳細情報

#### 2.1.4 タスク更新（TASK-004）
**説明**: タスク情報を更新する  
**入力**:
- タスクID（必須）
- 更新内容（部分更新可能）

**処理**:
1. タスクの存在確認
2. 更新権限の確認
3. 変更履歴の記録
4. 更新処理
5. 関係者への通知

**出力**: 更新後のタスク情報

#### 2.1.5 タスク削除（TASK-005）
**説明**: タスクを削除する  
**入力**: タスクID  
**処理**:
1. タスクの存在確認
2. 削除権限の確認
3. 依存関係の確認
4. 論理削除の実行
5. 監査ログの記録

**出力**: 削除成功/失敗の結果

### 2.2 ステータス管理

#### 2.2.1 ステータス更新（TASK-006）
**説明**: タスクのステータスを更新する  
**入力**:
- タスクID
- 新しいステータス
- コメント（任意）

**処理**:
1. ステータス遷移の妥当性確認
2. 更新処理
3. ステータス変更履歴の記録
4. 関係者への通知

**出力**: 更新後のステータス情報

#### 2.2.2 ステータス履歴取得（TASK-007）
**説明**: タスクのステータス変更履歴を取得する  
**入力**: タスクID  
**処理**: 変更履歴の取得  
**出力**: ステータス変更履歴一覧

### 2.3 担当者管理

#### 2.3.1 担当者割り当て（TASK-008）
**説明**: タスクに担当者を割り当てる  
**入力**:
- タスクID
- 担当者ID（複数可）
- 役割（任意）

**処理**:
1. 担当者の妥当性確認
2. 割り当て処理
3. 担当者への通知

**出力**: 割り当て結果

#### 2.3.2 担当者解除（TASK-009）
**説明**: タスクから担当者を解除する  
**入力**:
- タスクID
- 担当者ID

**処理**:
1. 解除権限の確認
2. 解除処理
3. 通知

**出力**: 解除結果

### 2.4 期限管理

#### 2.4.1 期限設定（TASK-010）
**説明**: タスクの期限を設定する  
**入力**:
- タスクID
- 期限日時
- リマインダー設定（任意）

**処理**:
1. 期限の妥当性確認
2. 設定処理
3. リマインダーのスケジューリング

**出力**: 設定結果

#### 2.4.2 期限超過タスク取得（TASK-011）
**説明**: 期限を超過したタスクを取得する  
**入力**:
- プロジェクトID（任意）
- 期間（任意）

**処理**: 期限超過タスクの検索  
**出力**: 期限超過タスク一覧

### 2.5 優先度管理

#### 2.5.1 優先度設定（TASK-012）
**説明**: タスクの優先度を設定する  
**入力**:
- タスクID
- 優先度（高、中、低）

**処理**:
1. 設定権限の確認
2. 優先度更新

**出力**: 更新結果

### 2.6 依存関係管理

#### 2.6.1 依存関係設定（TASK-013）
**説明**: タスク間の依存関係を設定する  
**入力**:
- タスクID
- 依存先タスクID
- 依存タイプ（ブロッキング、関連）

**処理**:
1. 循環依存のチェック
2. 依存関係の設定

**出力**: 設定結果

#### 2.6.2 依存関係取得（TASK-014）
**説明**: タスクの依存関係を取得する  
**入力**: タスクID  
**処理**: 依存関係の取得  
**出力**: 依存関係情報

### 2.7 検索・フィルタ

#### 2.7.1 タスク検索（TASK-015）
**説明**: キーワードでタスクを検索する  
**入力**:
- 検索キーワード
- 検索対象（タイトル、説明、タグ）

**処理**: 全文検索  
**出力**: 検索結果

#### 2.7.2 高度なフィルタリング（TASK-016）
**説明**: 複数条件でタスクをフィルタリングする  
**入力**: 複数のフィルタ条件  
**処理**: 条件に基づくフィルタリング  
**出力**: フィルタ結果

### 2.8 バルク操作

#### 2.8.1 一括ステータス更新（TASK-017）
**説明**: 複数タスクのステータスを一括更新する  
**入力**:
- タスクIDリスト
- 新しいステータス

**処理**: バッチ更新処理  
**出力**: 更新結果

#### 2.8.2 一括削除（TASK-018）
**説明**: 複数タスクを一括削除する  
**入力**: タスクIDリスト  
**処理**: バッチ削除処理  
**出力**: 削除結果

### 2.9 通知管理

#### 2.9.1 タスク通知設定（TASK-019）
**説明**: タスクの通知設定を管理する  
**入力**:
- タスクID
- 通知タイプ
- 通知先

**処理**: 通知設定の保存  
**出力**: 設定結果

#### 2.9.2 リマインダー送信（TASK-020）
**説明**: タスクのリマインダーを送信する  
**処理**: スケジュールされたリマインダーの送信  
**出力**: 送信結果

---

## 3. 非機能要件

### 3.1 パフォーマンス要件
- タスク一覧取得: 1000件以下で200ms以内
- タスク作成・更新: 100ms以内
- 検索処理: 500ms以内

### 3.2 セキュリティ要件
- 組織間のデータ分離
- ロールベースアクセス制御
- 監査ログの記録
- 入力値の検証とサニタイゼーション

### 3.3 スケーラビリティ要件
- 組織あたり10,000タスクまで対応
- 同時接続ユーザー1,000人対応

---

## 4. データモデル

### 4.1 Taskテーブル
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    parent_task_id INTEGER REFERENCES tasks(id),
    status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    due_date TIMESTAMP,
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    organization_id INTEGER NOT NULL REFERENCES organizations(id)
);
```

### 4.2 TaskAssignmentテーブル
```sql
CREATE TABLE task_assignments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role VARCHAR(50),
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER NOT NULL REFERENCES users(id)
);
```

### 4.3 TaskDependencyテーブル
```sql
CREATE TABLE task_dependencies (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    depends_on_task_id INTEGER NOT NULL REFERENCES tasks(id),
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'blocking',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 TaskHistoryテーブル
```sql
CREATE TABLE task_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. API仕様

### 5.1 エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /api/v1/tasks | タスク作成 |
| GET | /api/v1/tasks | タスク一覧取得 |
| GET | /api/v1/tasks/{id} | タスク詳細取得 |
| PATCH | /api/v1/tasks/{id} | タスク更新 |
| DELETE | /api/v1/tasks/{id} | タスク削除 |
| POST | /api/v1/tasks/{id}/status | ステータス更新 |
| GET | /api/v1/tasks/{id}/history | 変更履歴取得 |
| POST | /api/v1/tasks/{id}/assign | 担当者割り当て |
| DELETE | /api/v1/tasks/{id}/assign/{user_id} | 担当者解除 |
| POST | /api/v1/tasks/{id}/dependencies | 依存関係設定 |
| GET | /api/v1/tasks/{id}/dependencies | 依存関係取得 |
| POST | /api/v1/tasks/bulk/status | 一括ステータス更新 |
| DELETE | /api/v1/tasks/bulk | 一括削除 |

### 5.2 リクエスト/レスポンス例

#### タスク作成
**Request:**
```json
POST /api/v1/tasks
{
    "title": "API設計書作成",
    "description": "タスク管理機能のAPI設計書を作成する",
    "project_id": 1,
    "assignee_ids": [2, 3],
    "due_date": "2025-07-15T17:00:00Z",
    "priority": "high",
    "tags": ["設計", "API"]
}
```

**Response:**
```json
{
    "id": 123,
    "title": "API設計書作成",
    "description": "タスク管理機能のAPI設計書を作成する",
    "project": {
        "id": 1,
        "name": "ERPシステム開発"
    },
    "assignees": [
        {"id": 2, "name": "山田太郎"},
        {"id": 3, "name": "鈴木花子"}
    ],
    "status": "not_started",
    "priority": "high",
    "due_date": "2025-07-15T17:00:00Z",
    "tags": ["設計", "API"],
    "created_at": "2025-07-06T10:00:00Z",
    "created_by": {
        "id": 1,
        "name": "管理者"
    }
}
```

---

## 6. エラー処理

### 6.1 エラーコード
- 400: 不正なリクエスト
- 401: 認証エラー
- 403: アクセス権限なし
- 404: リソースが見つからない
- 409: 競合（例：循環依存）
- 422: バリデーションエラー

### 6.2 エラーレスポンス例
```json
{
    "error": {
        "code": "TASK_NOT_FOUND",
        "message": "指定されたタスクが見つかりません",
        "details": {
            "task_id": 123
        }
    }
}
```

---

## 7. 実装優先順位

1. **Phase 1**: 基本CRUD操作（TASK-001～005）
2. **Phase 2**: ステータス・担当者管理（TASK-006～009）
3. **Phase 3**: 期限・優先度管理（TASK-010～012）
4. **Phase 4**: 依存関係・検索機能（TASK-013～016）
5. **Phase 5**: バルク操作・通知機能（TASK-017～020）

---

## 8. 承認

**作成者**: Claude Code AI  
**日付**: 2025年7月6日  
**バージョン**: 1.0  

**レビュー・承認**:  
承認者: _________________  
日付: _________________