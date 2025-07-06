# ダッシュボード機能仕様書

## 1. 概要

ITDO ERP System v2における型安全なダッシュボード機能の実装仕様書です。この機能は、組織・プロジェクト・タスクの統合ビューを提供し、ユーザーが重要な情報を一目で把握できるようにします。

### 1.1 目的
- 組織全体およびユーザー個人の重要指標を統合表示
- プロジェクトとタスクの進捗状況をリアルタイムで監視
- 期限切れアイテムや注意が必要な項目のアラート表示
- パフォーマンス指標とトレンドの可視化

### 1.2 技術要件
- 完全な型安全性（mypy strict mode）
- 高速なデータ集計とキャッシュ機能
- リアルタイム更新対応
- 多様なフィルタリングオプション

## 2. ダッシュボード構成

### 2.1 メインダッシュボード
組織の全体概要を表示するメインビュー

#### 2.1.1 組織統計ウィジェット
```python
class OrganizationStats(BaseModel):
    """組織全体統計"""
    total_projects: int = Field(..., description="総プロジェクト数")
    active_projects: int = Field(..., description="アクティブプロジェクト数")
    completed_projects: int = Field(..., description="完了プロジェクト数")
    overdue_projects: int = Field(..., description="期限切れプロジェクト数")
    total_tasks: int = Field(..., description="総タスク数")
    pending_tasks: int = Field(..., description="未完了タスク数")
    overdue_tasks: int = Field(..., description="期限切れタスク数")
    total_users: int = Field(..., description="総ユーザー数")
    active_users: int = Field(..., description="アクティブユーザー数")
```

#### 2.1.2 プロジェクト進捗サマリー
```python
class ProjectProgressSummary(BaseModel):
    """プロジェクト進捗サマリー"""
    id: int
    code: str
    name: str
    status: str
    progress_percentage: int
    planned_end_date: Optional[date]
    is_overdue: bool
    days_remaining: Optional[int]
    member_count: int
    budget_usage_percentage: Optional[float]
```

#### 2.1.3 最近のアクティビティ
```python
class RecentActivity(BaseModel):
    """最近のアクティビティ"""
    id: int
    activity_type: str = Field(..., description="アクティビティタイプ")
    description: str = Field(..., description="説明")
    entity_type: str = Field(..., description="対象エンティティタイプ")
    entity_id: int = Field(..., description="対象エンティティID")
    entity_name: str = Field(..., description="対象エンティティ名")
    user_id: UserId = Field(..., description="実行ユーザーID")
    user_name: str = Field(..., description="実行ユーザー名")
    timestamp: datetime = Field(..., description="実行時刻")
```

### 2.2 個人ダッシュボード
ユーザー個人のタスクとプロジェクトビュー

#### 2.2.1 個人統計
```python
class PersonalStats(BaseModel):
    """個人統計"""
    my_projects: int = Field(..., description="参画プロジェクト数")
    my_active_projects: int = Field(..., description="アクティブプロジェクト数")
    my_tasks: int = Field(..., description="自分のタスク数")
    my_pending_tasks: int = Field(..., description="未完了タスク数")
    my_overdue_tasks: int = Field(..., description="期限切れタスク数")
    tasks_due_today: int = Field(..., description="今日期限のタスク数")
    tasks_due_this_week: int = Field(..., description="今週期限のタスク数")
```

#### 2.2.2 今日の予定
```python
class TodaySchedule(BaseModel):
    """今日の予定"""
    due_tasks: List[TaskSummary] = Field(default_factory=list, description="期限のタスク")
    project_milestones: List[MilestoneSummary] = Field(default_factory=list, description="マイルストーン")
    meetings: List[MeetingSummary] = Field(default_factory=list, description="会議予定")
```

### 2.3 プロジェクトダッシュボード
特定プロジェクトの詳細ビュー

#### 2.3.1 プロジェクト詳細統計
```python
class ProjectDashboardStats(BaseModel):
    """プロジェクトダッシュボード統計"""
    project_info: ProjectInfo
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    total_phases: int
    completed_phases: int
    total_milestones: int
    completed_milestones: int
    overdue_milestones: int
    team_members: int
    budget_status: BudgetStatus
    timeline_status: TimelineStatus
```

## 3. データモデル

### 3.1 ダッシュボード設定
```python
class DashboardConfig(AuditableModel):
    """ダッシュボード設定"""
    
    __tablename__ = "dashboard_configs"
    
    user_id: Mapped[UserId] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        comment="ユーザーID"
    )
    
    # レイアウト設定
    layout: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="ダッシュボードレイアウト設定"
    )
    
    # ウィジェット設定
    widgets: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="ウィジェット設定"
    )
    
    # フィルタ設定
    default_filters: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="デフォルトフィルタ設定"
    )
    
    # 表示設定
    display_preferences: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="表示設定"
    )
```

### 3.2 ダッシュボードキャッシュ
```python
class DashboardCache(BaseModel):
    """ダッシュボードキャッシュモデル"""
    
    __tablename__ = "dashboard_cache"
    
    cache_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        primary_key=True,
        comment="キャッシュキー"
    )
    
    cache_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="キャッシュタイプ"
    )
    
    user_id: Mapped[Optional[UserId]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        comment="ユーザーID（個人キャッシュの場合）"
    )
    
    organization_id: Mapped[Optional[OrganizationId]] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=True,
        comment="組織ID（組織キャッシュの場合）"
    )
    
    data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="キャッシュデータ"
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="有効期限"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="作成日時"
    )
```

## 4. API仕様

### 4.1 メインダッシュボード
```
GET /api/v1/dashboard/main
Query Parameters:
  - organization_id: int (optional)
  - refresh: bool (default: false) - キャッシュを無視して最新データを取得
Response: MainDashboardData
```

### 4.2 個人ダッシュボード
```
GET /api/v1/dashboard/personal
Query Parameters:
  - date_range: str (optional) - today, week, month
  - refresh: bool (default: false)
Response: PersonalDashboardData
```

### 4.3 プロジェクトダッシュボード
```
GET /api/v1/dashboard/project/{project_id}
Query Parameters:
  - include_details: bool (default: false)
  - refresh: bool (default: false)
Response: ProjectDashboardData
```

### 4.4 統計API
```
GET /api/v1/dashboard/stats/organization
Response: OrganizationStats

GET /api/v1/dashboard/stats/personal
Response: PersonalStats

GET /api/v1/dashboard/stats/trends
Query Parameters:
  - period: str (week, month, quarter)
  - metric: str (projects, tasks, budget)
Response: TrendData
```

### 4.5 アクティビティ
```
GET /api/v1/dashboard/activities/recent
Query Parameters:
  - limit: int (default: 20)
  - activity_type: str (optional)
Response: List[RecentActivity]
```

### 4.6 設定管理
```
GET /api/v1/dashboard/config
Response: DashboardConfig

PUT /api/v1/dashboard/config
Request Body: DashboardConfigUpdate
Response: DashboardConfig
```

## 5. ビジネスロジック

### 5.1 データ集計ルール
- **プロジェクト統計**: アクティブ、完了、期限切れの分類
- **タスク統計**: ステータス別、期限別の集計
- **予算統計**: 使用率、残額、超過金額の計算
- **進捗統計**: 加重平均による全体進捗の算出

### 5.2 キャッシュ戦略
- **組織統計**: 1時間キャッシュ
- **個人統計**: 15分キャッシュ
- **プロジェクト統計**: 30分キャッシュ
- **アクティビティ**: 5分キャッシュ

### 5.3 リアルタイム更新
- プロジェクト・タスクの状態変更時にキャッシュを無効化
- WebSocket接続によるリアルタイム通知
- 重要な変更（期限切れ、完了など）の即座な反映

## 6. パフォーマンス要件

### 6.1 レスポンス時間
- ダッシュボード表示: <500ms (キャッシュヒット時: <100ms)
- 統計データ取得: <300ms
- フィルタ適用: <200ms

### 6.2 データ量対応
- 10,000プロジェクト、100,000タスクまで対応
- 同時接続1,000ユーザーまで対応
- 履歴データは1年分まで高速アクセス

### 6.3 最適化
- インデックス最適化による高速クエリ
- バックグラウンドでの統計データ事前計算
- 階層的キャッシュ構造による効率的なデータ管理

## 7. セキュリティ要件

### 7.1 アクセス制御
- ユーザーは自分の組織のデータのみ閲覧可能
- プロジェクトメンバーのみプロジェクトダッシュボード閲覧可能
- 管理者は組織全体のダッシュボード閲覧可能

### 7.2 データ保護
- 個人情報を含む統計の匿名化
- 機密プロジェクトの除外オプション
- 権限に応じた表示項目の制御

## 8. 将来の拡張性

### 8.1 追加予定機能
- カスタムウィジェット作成機能
- ダッシュボードのエクスポート機能
- アラート・通知機能
- 詳細レポート生成

### 8.2 統合予定
- カレンダー機能との連携
- 通知システムとの連携
- 外部ツール（Slack、Teams）との連携
- モバイルアプリ対応