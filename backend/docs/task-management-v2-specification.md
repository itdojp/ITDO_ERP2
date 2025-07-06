# タスク管理機能仕様書 v2

## 1. 概要

本仕様書は、ITDO ERP System v2における型安全なタスク管理機能の実装仕様を定義します。
PR #19-21で確立された型安全アーキテクチャに基づいて実装を行います。

## 2. 機能要件

### 2.1 タスク管理

#### TASK-001: タスク作成
- **説明**: プロジェクト内に新しいタスクを作成する
- **優先度**: 1（必須）
- **詳細**:
  - タイトル（必須、最大200文字）
  - 説明（任意、Markdown対応）
  - プロジェクトID（必須）
  - ステータス（デフォルト: NOT_STARTED）
  - 優先度（デフォルト: MEDIUM）
  - 期限（任意）
  - 見積時間（任意、時間単位）
  - タグ（任意、複数可）

#### TASK-002: タスク更新
- **説明**: 既存のタスクの情報を更新する
- **優先度**: 1（必須）
- **詳細**:
  - 楽観的ロックによる同時編集制御
  - 変更履歴の自動記録
  - リアルタイム通知（WebSocket）

#### TASK-003: タスク削除
- **説明**: タスクをソフトデリートする
- **優先度**: 1（必須）
- **詳細**:
  - 依存関係がある場合は削除不可
  - 削除履歴の記録
  - 削除権限の確認

#### TASK-004: タスクステータス管理
- **説明**: タスクのステータスを更新する
- **優先度**: 1（必須）
- **ステータスフロー**:
  ```
  NOT_STARTED → IN_PROGRESS → IN_REVIEW → COMPLETED
              ↓              ↓            ↓
              → ON_HOLD ←────┴────────────┘
  ```

#### TASK-005: タスク検索
- **説明**: 高度な検索条件でタスクを検索する
- **優先度**: 1（必須）
- **検索条件**:
  - キーワード検索（タイトル、説明）
  - ステータスフィルタ
  - 優先度フィルタ
  - 担当者フィルタ
  - 期限範囲フィルタ
  - タグフィルタ
  - プロジェクトフィルタ

### 2.2 タスク割り当て

#### TASK-006: ユーザー割り当て
- **説明**: タスクに担当者を割り当てる
- **優先度**: 1（必須）
- **詳細**:
  - 複数ユーザー割り当て可能
  - 役割（メイン担当、レビュアー等）の指定
  - 割り当て通知

#### TASK-007: 割り当て解除
- **説明**: タスクから担当者を解除する
- **優先度**: 1（必須）

#### TASK-008: ワークロード表示
- **説明**: ユーザーのタスク負荷を可視化
- **優先度**: 2（推奨）
- **表示内容**:
  - 担当タスク数
  - 見積時間の合計
  - 期限切れタスク数

### 2.3 タスク依存関係

#### TASK-009: 依存関係設定
- **説明**: タスク間の依存関係を設定する
- **優先度**: 1（必須）
- **依存タイプ**:
  - FS (Finish-to-Start): 完了後開始
  - SS (Start-to-Start): 同時開始
  - FF (Finish-to-Finish): 同時完了
  - SF (Start-to-Finish): 開始後完了

#### TASK-010: 循環依存検出
- **説明**: 依存関係の循環を検出・防止する
- **優先度**: 1（必須）

#### TASK-011: クリティカルパス表示
- **説明**: プロジェクトのクリティカルパスを表示
- **優先度**: 3（オプション）

### 2.4 コメント・履歴

#### TASK-012: コメント投稿
- **説明**: タスクにコメントを投稿する
- **優先度**: 1（必須）
- **機能**:
  - Markdown対応
  - メンション機能（@ユーザー名）
  - 添付ファイル

#### TASK-013: 変更履歴表示
- **説明**: タスクの変更履歴を表示する
- **優先度**: 1（必須）
- **記録項目**:
  - フィールド変更
  - ステータス変更
  - 担当者変更
  - コメント追加

### 2.5 添付ファイル

#### TASK-014: ファイルアップロード
- **説明**: タスクにファイルを添付する
- **優先度**: 2（推奨）
- **制限**:
  - 最大ファイルサイズ: 10MB
  - 許可拡張子: 設定可能
  - ウイルススキャン連携

#### TASK-015: ファイルダウンロード
- **説明**: 添付ファイルをダウンロードする
- **優先度**: 2（推奨）

### 2.6 ビュー機能

#### TASK-016: カンバンボード
- **説明**: カンバン形式でタスクを表示・操作
- **優先度**: 2（推奨）
- **機能**:
  - ドラッグ&ドロップ
  - WIP制限
  - スイムレーン

#### TASK-017: ガントチャート
- **説明**: ガントチャート形式でタスクを表示
- **優先度**: 2（推奨）
- **機能**:
  - 依存関係の可視化
  - 進捗表示
  - マイルストーン

#### TASK-018: カレンダービュー
- **説明**: カレンダー形式でタスクを表示
- **優先度**: 3（オプション）

### 2.7 通知・リマインダー

#### TASK-019: タスク通知
- **説明**: タスクイベントの通知
- **優先度**: 2（推奨）
- **通知タイプ**:
  - 新規割り当て
  - ステータス変更
  - コメント追加
  - 期限接近

#### TASK-020: リマインダー設定
- **説明**: タスクのリマインダーを設定
- **優先度**: 3（オプション）

## 3. データモデル

### 3.1 Task（タスク）

```python
class Task(SoftDeletableModel):
    __tablename__ = "tasks"
    
    # 基本情報
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    parent_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"))
    
    # ステータス・優先度
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus))
    priority: Mapped[TaskPriority] = mapped_column(SQLEnum(TaskPriority))
    
    # 時間管理
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float)
    
    # 進捗管理
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    
    # 楽観的ロック
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # タグ（JSON配列）
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
```

### 3.2 TaskAssignment（タスク割り当て）

```python
class TaskAssignment(BaseModel):
    __tablename__ = "task_assignments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[AssignmentRole] = mapped_column(SQLEnum(AssignmentRole))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    assigned_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
```

### 3.3 TaskDependency（タスク依存関係）

```python
class TaskDependency(BaseModel):
    __tablename__ = "task_dependencies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    predecessor_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    successor_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    dependency_type: Mapped[DependencyType] = mapped_column(SQLEnum(DependencyType))
    lag_time: Mapped[int] = mapped_column(Integer, default=0)  # 日数
```

### 3.4 TaskComment（コメント）

```python
class TaskComment(SoftDeletableModel):
    __tablename__ = "task_comments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task_comments.id"))
    mentioned_users: Mapped[Optional[List[int]]] = mapped_column(JSON)
```

### 3.5 TaskAttachment（添付ファイル）

```python
class TaskAttachment(SoftDeletableModel):
    __tablename__ = "task_attachments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task_comments.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(100))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
```

## 4. API仕様

### 4.1 タスクAPI

#### タスク作成
```
POST /api/v1/tasks
```

**リクエスト:**
```json
{
  "title": "新機能の実装",
  "description": "ユーザー管理機能の追加実装",
  "project_id": 1,
  "priority": "HIGH",
  "due_date": "2024-12-31T23:59:59Z",
  "estimated_hours": 40,
  "assignee_ids": [1, 2],
  "tags": ["backend", "feature"]
}
```

#### タスク一覧取得
```
GET /api/v1/tasks?project_id=1&status=IN_PROGRESS&assignee_id=1
```

#### タスク詳細取得
```
GET /api/v1/tasks/{task_id}
```

#### タスク更新
```
PATCH /api/v1/tasks/{task_id}
```

#### タスク削除
```
DELETE /api/v1/tasks/{task_id}
```

### 4.2 ステータス管理API

#### ステータス更新
```
POST /api/v1/tasks/{task_id}/status
```

### 4.3 割り当てAPI

#### 担当者割り当て
```
POST /api/v1/tasks/{task_id}/assignments
```

#### 担当者解除
```
DELETE /api/v1/tasks/{task_id}/assignments/{user_id}
```

### 4.4 依存関係API

#### 依存関係追加
```
POST /api/v1/tasks/{task_id}/dependencies
```

#### 依存関係削除
```
DELETE /api/v1/tasks/{task_id}/dependencies/{dependency_id}
```

### 4.5 コメントAPI

#### コメント追加
```
POST /api/v1/tasks/{task_id}/comments
```

#### コメント一覧取得
```
GET /api/v1/tasks/{task_id}/comments
```

### 4.6 添付ファイルAPI

#### ファイルアップロード
```
POST /api/v1/tasks/{task_id}/attachments
```

#### ファイルダウンロード
```
GET /api/v1/tasks/{task_id}/attachments/{attachment_id}
```

## 5. WebSocket仕様

### 5.1 接続
```
ws://localhost:8000/ws/tasks/{project_id}
```

### 5.2 イベント

#### タスク更新イベント
```json
{
  "type": "task.updated",
  "task_id": 1,
  "data": { /* タスクデータ */ }
}
```

#### コメント追加イベント
```json
{
  "type": "comment.added",
  "task_id": 1,
  "comment": { /* コメントデータ */ }
}
```

## 6. セキュリティ要件

### 6.1 認証・認可
- JWTトークンによる認証
- プロジェクトベースのアクセス制御
- タスク作成者・担当者の権限管理

### 6.2 データ保護
- SQLインジェクション対策
- XSS対策（HTMLエスケープ）
- ファイルアップロード時のウイルススキャン

### 6.3 監査ログ
- すべての操作の記録
- IPアドレス・ユーザーエージェントの記録

## 7. パフォーマンス要件

### 7.1 レスポンスタイム
- タスク一覧取得: < 200ms
- タスク作成・更新: < 100ms
- 検索: < 500ms

### 7.2 同時接続数
- WebSocket: 1000接続以上

### 7.3 データ量
- 1プロジェクトあたり最大10,000タスク
- 1タスクあたり最大1,000コメント

## 8. 実装優先順位

1. **Phase 1（必須機能）**
   - タスクCRUD（TASK-001〜004）
   - タスク検索（TASK-005）
   - ユーザー割り当て（TASK-006〜007）
   - 依存関係（TASK-009〜010）
   - コメント（TASK-012〜013）

2. **Phase 2（推奨機能）**
   - ワークロード表示（TASK-008）
   - 添付ファイル（TASK-014〜015）
   - カンバンボード（TASK-016）
   - ガントチャート（TASK-017）
   - 通知（TASK-019）

3. **Phase 3（オプション機能）**
   - クリティカルパス（TASK-011）
   - カレンダービュー（TASK-018）
   - リマインダー（TASK-020）