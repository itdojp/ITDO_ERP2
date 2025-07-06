# Task Management v2 - API Reference

## 概要

型安全なタスク管理機能のAPI仕様書です。すべてのエンドポイントは `/api/v1/tasks` プレフィックスを持ちます。

## 認証

すべてのエンドポイントは Bearer token認証が必要です。

```http
Authorization: Bearer <your-jwt-token>
```

## エラーレスポンス

標準的なHTTPステータスコードとエラー形式を使用します。

```json
{
  "detail": "Error message description"
}
```

## エンドポイント一覧

### タスク管理

#### 1. タスク作成

**POST** `/api/v1/tasks`

新しいタスクを作成します。

**Request Body:**
```json
{
  "title": "タスクタイトル",
  "description": "タスクの説明（Markdown対応）",
  "project_id": 1,
  "parent_task_id": null,
  "priority": "HIGH",
  "due_date": "2024-12-31T23:59:59Z",
  "start_date": "2024-07-01T09:00:00Z",
  "estimated_hours": 40.0,
  "tags": ["backend", "feature"],
  "assignee_ids": [1, 2]
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "title": "タスクタイトル",
  "description": "タスクの説明",
  "project_id": 1,
  "parent_task_id": null,
  "status": "NOT_STARTED",
  "priority": "HIGH",
  "due_date": "2024-12-31T23:59:59Z",
  "start_date": "2024-07-01T09:00:00Z",
  "estimated_hours": 40.0,
  "actual_hours": null,
  "progress_percentage": 0,
  "tags": ["backend", "feature"],
  "version": 1,
  "organization_id": 1,
  "created_at": "2024-07-07T06:00:00Z",
  "updated_at": "2024-07-07T06:00:00Z",
  "created_by": 1,
  "updated_by": 1,
  "is_deleted": false
}
```

**Error Responses:**
- `400 Bad Request`: 無効なリクエストデータ
- `403 Forbidden`: プロジェクトへのアクセス権限なし
- `404 Not Found`: プロジェクトが見つからない

#### 2. タスク一覧取得

**GET** `/api/v1/tasks`

タスクを検索・フィルタリングして取得します。

**Query Parameters:**
- `search` (string): タイトル・説明での検索
- `status` (string): ステータスフィルタ (`NOT_STARTED`, `IN_PROGRESS`, `IN_REVIEW`, `ON_HOLD`, `COMPLETED`)
- `priority` (string): 優先度フィルタ (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
- `assignee_id` (integer): 担当者IDフィルタ
- `project_id` (integer): プロジェクトIDフィルタ
- `due_date_from` (string): 期限範囲（開始）
- `due_date_to` (string): 期限範囲（終了）
- `tags` (array): タグフィルタ
- `is_overdue` (boolean): 期限切れフィルタ
- `page` (integer): ページ番号（default: 1）
- `limit` (integer): 1ページあたりの件数（default: 20, max: 100）
- `sort_by` (string): ソートフィールド（default: created_at）
- `sort_order` (string): ソート順（asc/desc, default: desc）

**Example Request:**
```http
GET /api/v1/tasks?search=実装&status=IN_PROGRESS&page=1&limit=20&sort_by=due_date&sort_order=asc
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 123,
      "title": "機能実装",
      // ... other task fields
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "has_next": true,
  "has_prev": false
}
```

#### 3. タスク詳細取得

**GET** `/api/v1/tasks/{task_id}`

指定したタスクの詳細を取得します。

**Response (200 OK):**
```json
{
  "id": 123,
  "title": "タスクタイトル",
  // ... all task fields
}
```

**Error Responses:**
- `404 Not Found`: タスクが見つからない
- `403 Forbidden`: アクセス権限なし

#### 4. タスク更新

**PATCH** `/api/v1/tasks/{task_id}`

タスクの情報を更新します（楽観的ロック対応）。

**Request Body:**
```json
{
  "title": "更新されたタイトル",
  "description": "更新された説明",
  "priority": "HIGH",
  "due_date": "2024-12-31T23:59:59Z",
  "estimated_hours": 50.0,
  "actual_hours": 30.0,
  "progress_percentage": 75,
  "tags": ["backend", "feature", "urgent"],
  "version": 1
}
```

**Response (200 OK):**
```json
{
  "id": 123,
  "title": "更新されたタイトル",
  "version": 2,
  // ... other updated fields
}
```

**Error Responses:**
- `404 Not Found`: タスクが見つからない
- `403 Forbidden`: 更新権限なし
- `409 Conflict`: 楽観的ロック競合（他のユーザーが同時更新）

#### 5. タスク削除

**DELETE** `/api/v1/tasks/{task_id}`

タスクをソフトデリートします。

**Response (204 No Content)**

**Error Responses:**
- `404 Not Found`: タスクが見つからない
- `403 Forbidden`: 削除権限なし
- `400 Bad Request`: 依存関係が存在するため削除不可

### ステータス管理

#### 6. ステータス更新

**POST** `/api/v1/tasks/{task_id}/status`

タスクのステータスを更新します。

**Request Body:**
```json
{
  "status": "IN_PROGRESS",
  "comment": "作業を開始しました",
  "version": 1
}
```

**Response (200 OK):**
```json
{
  "id": 123,
  "status": "IN_PROGRESS",
  "version": 2,
  // ... other task fields
}
```

**Error Responses:**
- `400 Bad Request`: 無効なステータス遷移
- `409 Conflict`: 楽観的ロック競合

### 割り当て管理

#### 7. ユーザー割り当て

**POST** `/api/v1/tasks/{task_id}/assignments`

タスクにユーザーを割り当てます。

**Request Body:**
```json
{
  "user_id": 2,
  "role": "ASSIGNEE"
}
```

**Response (201 Created)**

**Error Responses:**
- `400 Bad Request`: 既に割り当て済み
- `404 Not Found`: ユーザーまたはタスクが見つからない

#### 8. 割り当て解除

**DELETE** `/api/v1/tasks/{task_id}/assignments/{user_id}`

タスクからユーザーの割り当てを解除します。

**Response (204 No Content)**

### 依存関係管理

#### 9. 依存関係追加

**POST** `/api/v1/tasks/{task_id}/dependencies`

タスクに依存関係を追加します。

**Request Body:**
```json
{
  "predecessor_id": 1,
  "dependency_type": "FS",
  "lag_time": 2
}
```

**Response (201 Created)**

**Error Responses:**
- `400 Bad Request`: 循環依存が発生、または同一プロジェクト外

#### 10. 依存関係削除

**DELETE** `/api/v1/dependencies/{dependency_id}`

依存関係を削除します。

**Response (204 No Content)**

#### 11. 依存関係ツリー取得

**GET** `/api/v1/tasks/{task_id}/dependencies`

タスクの依存関係ツリーを取得します。

**Response (200 OK):**
```json
{
  "task": {
    "id": 123,
    "title": "メインタスク"
  },
  "predecessors": [
    {
      "task": {
        "id": 122,
        "title": "先行タスク"
      },
      "dependency_type": "FS",
      "lag_time": 0,
      "predecessors": []
    }
  ],
  "successors": [
    {
      "task": {
        "id": 124,
        "title": "後続タスク"
      },
      "dependency_type": "FS",
      "lag_time": 1,
      "successors": []
    }
  ]
}
```

### コメント管理

#### 12. コメント追加

**POST** `/api/v1/tasks/{task_id}/comments`

タスクにコメントを追加します。

**Request Body:**
```json
{
  "content": "コメント内容（Markdown対応）",
  "parent_comment_id": null,
  "mentioned_users": [2, 3]
}
```

**Response (201 Created)**

#### 13. コメント一覧取得

**GET** `/api/v1/tasks/{task_id}/comments`

タスクのコメント一覧を取得します。

**Response (200 OK):**
```json
{
  "task_id": 123,
  "comments": []
}
```

### ファイル管理

#### 14. ファイルアップロード

**POST** `/api/v1/tasks/{task_id}/attachments`

タスクにファイルを添付します。

**Request (multipart/form-data):**
- `file`: アップロードファイル（最大10MB）

**Response (201 Created):**
```json
{
  "message": "File upload not yet implemented",
  "task_id": 123,
  "filename": "document.pdf"
}
```

**Error Responses:**
- `413 Payload Too Large`: ファイルサイズ超過（10MB以上）

#### 15. ファイルダウンロード

**GET** `/api/v1/tasks/{task_id}/attachments/{attachment_id}`

添付ファイルをダウンロードします。

**Response (200 OK):**
```json
{
  "message": "File download not yet implemented",
  "task_id": 123,
  "attachment_id": 456
}
```

### 一括操作

#### 16. 一括更新

**PATCH** `/api/v1/tasks/bulk`

複数のタスクを一括更新します。

**Request Body:**
```json
{
  "task_ids": [123, 124, 125],
  "status": "IN_PROGRESS",
  "priority": "HIGH",
  "assignee_id": 2,
  "due_date": "2024-12-31T23:59:59Z"
}
```

**Response (200 OK):**
```json
{
  "success_count": 2,
  "error_count": 1,
  "errors": [
    {
      "task_id": 125,
      "error": "Invalid status transition from COMPLETED to IN_PROGRESS"
    }
  ]
}
```

### 分析・レポート

#### 17. ユーザーワークロード

**GET** `/api/v1/tasks/analytics/workload/{user_id}`

ユーザーのワークロード分析を取得します。

**Response (200 OK):**
```json
{
  "user_id": 2,
  "assigned_tasks_count": 15,
  "estimated_hours_total": 120.5,
  "overdue_tasks_count": 3,
  "completed_tasks_count": 8,
  "in_progress_tasks_count": 5
}
```

#### 18. 組織統計

**GET** `/api/v1/tasks/analytics/organization`

組織のタスク統計を取得します。

**Response (200 OK):**
```json
{
  "total_tasks": 500,
  "by_status": {
    "NOT_STARTED": 100,
    "IN_PROGRESS": 200,
    "IN_REVIEW": 50,
    "ON_HOLD": 25,
    "COMPLETED": 125
  },
  "by_priority": {
    "LOW": 100,
    "MEDIUM": 250,
    "HIGH": 125,
    "URGENT": 25
  },
  "overdue_count": 45,
  "completion_rate": 25.0,
  "average_completion_time_days": 12.5
}
```

#### 19. クリティカルパス

**GET** `/api/v1/tasks/projects/{project_id}/critical-path`

プロジェクトのクリティカルパスを取得します。

**Response (200 OK):**
```json
[
  {
    "id": 123,
    "title": "要件定義",
    "estimated_hours": 40.0
    // ... other task fields
  },
  {
    "id": 124,
    "title": "設計",
    "estimated_hours": 80.0
    // ... other task fields
  }
]
```

#### 20. ユーザータスク

**GET** `/api/v1/tasks/users/{user_id}/tasks`

ユーザーに割り当てられたタスク一覧を取得します。

**Query Parameters:**
- `status` (string): ステータスフィルタ
- `limit` (integer): 最大取得件数（default: 50, max: 100）

**Response (200 OK):**
```json
[
  {
    "id": 123,
    "title": "担当タスク1",
    // ... other task fields
  }
]
```

## データ型定義

### TaskStatus
- `NOT_STARTED`: 未開始
- `IN_PROGRESS`: 進行中
- `IN_REVIEW`: レビュー中
- `ON_HOLD`: 保留
- `COMPLETED`: 完了

### TaskPriority
- `LOW`: 低
- `MEDIUM`: 中
- `HIGH`: 高
- `URGENT`: 緊急

### DependencyType
- `FS`: Finish-to-Start（完了後開始）
- `SS`: Start-to-Start（同時開始）
- `FF`: Finish-to-Finish（同時完了）
- `SF`: Start-to-Finish（開始後完了）

### AssignmentRole
- `ASSIGNEE`: 担当者
- `REVIEWER`: レビュアー
- `OBSERVER`: 監視者

## レスポンス時間目標

- タスク一覧取得: < 200ms
- タスク作成・更新: < 100ms
- 検索: < 500ms
- 一括更新: < 1s（100件）

## セキュリティ考慮事項

1. **認証**: 全エンドポイントでJWT Bearer token必須
2. **認可**: 組織・プロジェクトレベルアクセス制御
3. **入力検証**: Pydanticによる型安全なバリデーション
4. **SQLインジェクション**: SQLAlchemy ORMによる防御
5. **ファイルセキュリティ**: アップロード時のサイズ・タイプ制限

---

**API Version**: v2.0.0  
**Last Updated**: 2024-07-07