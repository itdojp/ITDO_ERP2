# Task Management v2 - Implementation Guide

## 概要

Issue #24で実装された型安全なタスク管理機能の実装ガイドです。
この機能は8-phase開発ワークフローに従って実装され、TDD（テスト駆動開発）アプローチを採用しています。

## アーキテクチャ

### 技術スタック
- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic v2
- **Database**: PostgreSQL 15 with JSON support
- **Authentication**: JWT + role-based access control
- **Real-time**: WebSocket (設計済み、実装は将来フェーズ)
- **Testing**: pytest + Factory Boy
- **Type Safety**: 完全な型安全性（no `any` types）

### レイヤー構造
```
┌─────────────────┐
│   API Layer     │  FastAPI routes, HTTP handling
├─────────────────┤
│ Service Layer   │  Business logic, permissions
├─────────────────┤
│Repository Layer │  Data access, queries
├─────────────────┤
│  Model Layer    │  SQLAlchemy models, relationships
└─────────────────┘
```

## データモデル

### 主要エンティティ

#### Task（タスク）
```python
class Task(SoftDeletableModel):
    # 基本情報
    title: str                    # タスクタイトル（最大200文字）
    description: Optional[str]    # 説明（Markdown対応）
    project_id: int              # プロジェクトID
    parent_task_id: Optional[int] # 親タスクID（階層構造）
    
    # ステータス・優先度
    status: TaskStatus           # NOT_STARTED, IN_PROGRESS, IN_REVIEW, ON_HOLD, COMPLETED
    priority: TaskPriority       # LOW, MEDIUM, HIGH, URGENT
    
    # 時間管理
    due_date: Optional[datetime] # 期限
    start_date: Optional[datetime] # 開始日
    estimated_hours: Optional[float] # 見積時間
    actual_hours: Optional[float]    # 実際の時間
    
    # 進捗管理
    progress_percentage: int     # 進捗率（0-100）
    version: int                # 楽観的ロック用バージョン
    tags: Optional[List[str]]   # タグ（JSON配列）
```

#### TaskAssignment（割り当て）
```python
class TaskAssignment(BaseModel):
    task_id: int                 # タスクID
    user_id: int                # ユーザーID
    role: AssignmentRole        # ASSIGNEE, REVIEWER, OBSERVER
    assigned_at: datetime       # 割り当て日時
    assigned_by: int            # 割り当て者
```

#### TaskDependency（依存関係）
```python
class TaskDependency(BaseModel):
    predecessor_id: int          # 先行タスクID
    successor_id: int           # 後続タスクID
    dependency_type: DependencyType # FS, SS, FF, SF
    lag_time: int               # ラグタイム（日数）
```

### 関係性
- Task → Project（多対一）
- Task → Task（親子関係、多対一）
- Task → TaskAssignment（一対多）
- Task → TaskDependency（多対多、自己参照）
- Task → TaskComment（一対多）
- Task → TaskAttachment（一対多）

## セットアップ手順

### 1. データベースマイグレーション
```bash
# マイグレーション実行
alembic upgrade head

# 新しいテーブルが作成される：
# - projects
# - tasks
# - task_assignments
# - task_dependencies
# - task_comments
# - task_attachments
```

### 2. 環境設定
```bash
# 必要な環境変数
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. 依存関係
```bash
# 必要なPythonパッケージ（既存環境に含まれる）
fastapi>=0.104.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0
```

## API使用例

### 1. タスク作成
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新機能の実装",
    "description": "ユーザー管理機能の追加実装",
    "project_id": 1,
    "priority": "HIGH",
    "due_date": "2024-12-31T23:59:59Z",
    "estimated_hours": 40,
    "assignee_ids": [1, 2],
    "tags": ["backend", "feature"]
  }'
```

### 2. タスク検索
```bash
curl -X GET "http://localhost:8000/api/v1/tasks?search=実装&status=IN_PROGRESS&page=1&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. ステータス更新
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/1/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "IN_PROGRESS",
    "comment": "作業を開始しました",
    "version": 1
  }'
```

### 4. 依存関係追加
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/2/dependencies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "predecessor_id": 1,
    "dependency_type": "FS",
    "lag_time": 0
  }'
```

## ビジネスロジック

### 1. 権限制御
- **組織レベル分離**: ユーザーは自身の組織のタスクのみアクセス可能
- **プロジェクトレベル制御**: プロジェクトメンバーのみタスクにアクセス可能
- **操作権限**: 作成・更新・削除権限は役割ベース

### 2. ステータス遷移
```
NOT_STARTED → IN_PROGRESS → IN_REVIEW → COMPLETED
             ↓              ↓            ↓
             → ON_HOLD ←────┴────────────┘
```

### 3. 依存関係管理
- **循環依存検出**: 依存関係追加時に循環参照をチェック
- **依存タイプ**:
  - FS (Finish-to-Start): 完了後開始
  - SS (Start-to-Start): 同時開始
  - FF (Finish-to-Finish): 同時完了
  - SF (Start-to-Finish): 開始後完了

### 4. 楽観的ロック
- **同時編集制御**: versionフィールドによる楽観的ロック
- **競合検出**: 更新時にバージョン不一致で409 Conflictを返却

## パフォーマンス最適化

### 1. データベース最適化
- **インデックス**: 検索頻度の高いフィールドにインデックス設定
- **外部キー**: 適切な外部キー制約でデータ整合性確保
- **JSON型**: タグ情報にPostgreSQLのJSON型を活用

### 2. クエリ最適化
- **Eager Loading**: 関連データの事前読み込み
- **ページネーション**: 大量データの効率的な取得
- **フィルタリング**: データベースレベルでの条件絞り込み

### 3. キャッシュ戦略（将来実装）
- **Redis**: セッション管理、一時データ
- **アプリケーションレベル**: 頻繁にアクセスされるデータ

## セキュリティ

### 1. 認証・認可
- **JWT Token**: Bearer token認証
- **Role-based Access**: 役割ベースアクセス制御
- **Multi-tenant**: 組織レベルデータ分離

### 2. 入力検証
- **Pydantic**: スキーマレベルバリデーション
- **SQLインジェクション**: SQLAlchemy ORMによる防御
- **XSS**: HTMLエスケープ処理

### 3. ファイルセキュリティ（設計済み）
- **ウイルススキャン**: アップロードファイルのスキャン
- **容量制限**: 10MB制限
- **拡張子制御**: 許可拡張子の設定

## モニタリング

### 1. ログ出力
- **操作ログ**: 全CRUD操作の記録
- **エラーログ**: 例外発生時の詳細記録
- **アクセスログ**: APIアクセスの記録

### 2. メトリクス（将来実装）
- **レスポンス時間**: API応答時間測定
- **使用量統計**: 機能使用頻度
- **エラー率**: エラー発生率監視

## トラブルシューティング

### 1. よくある問題

#### 権限エラー (403 Forbidden)
```
原因: ユーザーが組織またはプロジェクトにアクセス権限がない
対策: ユーザーの組織・役割設定を確認
```

#### 楽観的ロックエラー (409 Conflict)
```
原因: 他のユーザーが同じタスクを同時に更新
対策: 最新のversionを取得して再試行
```

#### 循環依存エラー (400 Bad Request)
```
原因: 依存関係の追加が循環参照を引き起こす
対策: 依存関係の構造を見直し
```

### 2. デバッグ手順
1. ログファイルの確認
2. データベースの制約確認
3. 権限設定の検証
4. APIリクエストの検証

## 将来の拡張

### 1. Real-time機能
- **WebSocket**: タスク更新のリアルタイム通知
- **コラボレーション**: 同時編集の可視化

### 2. 高度な機能
- **ガントチャート**: プロジェクト進捗の可視化
- **カンバンボード**: タスクのドラッグ&ドロップ操作
- **カレンダービュー**: 期限ベースの表示

### 3. インテグレーション
- **外部ツール**: GitHub, Slack等との連携
- **通知システム**: メール、プッシュ通知
- **レポート機能**: 進捗レポートの自動生成

## 品質保証

### 1. テスト戦略
- **単体テスト**: 38ケース実装済み
- **統合テスト**: 21ケース実装済み
- **パフォーマンステスト**: 6ケース実装済み
- **セキュリティテスト**: 6ケース実装済み

### 2. 品質基準
- **カバレッジ**: 85%以上
- **レスポンス時間**: < 200ms（一覧取得）
- **同時接続**: 1000ユーザー対応

---

**実装者**: Claude Code  
**実装日**: 2024-07-07  
**バージョン**: v2.0.0