# プロジェクト管理機能仕様書

## 1. 概要

ITDO ERP System v2における型安全なプロジェクト管理機能の実装仕様書です。この機能は、型安全性を最優先として設計された新しいアーキテクチャ（PR #19, #20, #21）の上に構築されます。

### 1.1 目的
- プロジェクトの作成、管理、追跡を可能にする
- 階層的なプロジェクト構造（親子関係）をサポート
- プロジェクトメンバーの管理と権限制御
- プロジェクトフェーズとマイルストーンの管理

### 1.2 技術要件
- 完全な型安全性（mypy strict mode）
- SoftDeletableModelベースクラスの継承
- BaseRepositoryパターンの使用
- 包括的なエラーハンドリング
- 高いテストカバレッジ（>95%）

## 2. データモデル

### 2.1 Projectモデル

```python
class Project(SoftDeletableModel):
    """プロジェクトモデル"""
    
    # 基本情報
    code: Mapped[str]  # プロジェクトコード（一意）
    name: Mapped[str]  # プロジェクト名
    name_en: Mapped[Optional[str]]  # 英語名
    description: Mapped[Optional[str]]  # 説明
    
    # 組織・部門関連
    organization_id: Mapped[OrganizationId]  # 所属組織
    department_id: Mapped[Optional[DepartmentId]]  # 担当部門
    
    # プロジェクト詳細
    project_type: Mapped[str]  # プロジェクトタイプ
    status: Mapped[str]  # ステータス（planning/in_progress/completed/cancelled/on_hold）
    priority: Mapped[str]  # 優先度（low/medium/high/urgent）
    
    # 日程
    planned_start_date: Mapped[Optional[date]]  # 計画開始日
    planned_end_date: Mapped[Optional[date]]  # 計画終了日
    actual_start_date: Mapped[Optional[date]]  # 実績開始日
    actual_end_date: Mapped[Optional[date]]  # 実績終了日
    
    # 予算・コスト
    budget: Mapped[Optional[Decimal]]  # 予算
    actual_cost: Mapped[Optional[Decimal]]  # 実績コスト
    currency: Mapped[str]  # 通貨（デフォルト: JPY）
    
    # 進捗
    progress_percentage: Mapped[int]  # 進捗率（0-100）
    
    # 階層構造
    parent_id: Mapped[Optional[int]]  # 親プロジェクトID
    
    # 責任者
    project_manager_id: Mapped[Optional[UserId]]  # プロジェクトマネージャー
    
    # メタデータ
    tags: Mapped[List[str]]  # タグ（JSON配列）
    custom_fields: Mapped[Dict[str, Any]]  # カスタムフィールド（JSON）
```

### 2.2 ProjectMemberモデル

```python
class ProjectMember(AuditableModel):
    """プロジェクトメンバーモデル"""
    
    project_id: Mapped[int]  # プロジェクトID
    user_id: Mapped[UserId]  # ユーザーID
    role: Mapped[str]  # プロジェクト内での役割
    allocation_percentage: Mapped[int]  # 割当率（0-100）
    start_date: Mapped[date]  # 参画開始日
    end_date: Mapped[Optional[date]]  # 参画終了日
    is_active: Mapped[bool]  # アクティブフラグ
    notes: Mapped[Optional[str]]  # 備考
```

### 2.3 ProjectPhaseモデル

```python
class ProjectPhase(SoftDeletableModel):
    """プロジェクトフェーズモデル"""
    
    project_id: Mapped[int]  # プロジェクトID
    name: Mapped[str]  # フェーズ名
    description: Mapped[Optional[str]]  # 説明
    phase_order: Mapped[int]  # フェーズ順序
    planned_start_date: Mapped[Optional[date]]  # 計画開始日
    planned_end_date: Mapped[Optional[date]]  # 計画終了日
    actual_start_date: Mapped[Optional[date]]  # 実績開始日
    actual_end_date: Mapped[Optional[date]]  # 実績終了日
    status: Mapped[str]  # ステータス
    deliverables: Mapped[List[str]]  # 成果物リスト（JSON）
```

### 2.4 ProjectMilestoneモデル

```python
class ProjectMilestone(SoftDeletableModel):
    """プロジェクトマイルストーンモデル"""
    
    project_id: Mapped[int]  # プロジェクトID
    phase_id: Mapped[Optional[int]]  # フェーズID
    name: Mapped[str]  # マイルストーン名
    description: Mapped[Optional[str]]  # 説明
    due_date: Mapped[date]  # 期日
    completed_date: Mapped[Optional[date]]  # 完了日
    status: Mapped[str]  # ステータス（pending/completed/missed）
    is_critical: Mapped[bool]  # クリティカルパスフラグ
```

## 3. API仕様

### 3.1 プロジェクトCRUD

#### プロジェクト作成
```
POST /api/v1/projects
Request Body: ProjectCreate
Response: ProjectResponse
```

#### プロジェクト一覧取得
```
GET /api/v1/projects
Query Parameters:
  - organization_id: int (optional)
  - department_id: int (optional)
  - status: str (optional)
  - search: str (optional)
  - skip: int (default: 0)
  - limit: int (default: 100)
Response: PaginatedResponse[ProjectSummary]
```

#### プロジェクト詳細取得
```
GET /api/v1/projects/{project_id}
Response: ProjectResponse
```

#### プロジェクト更新
```
PUT /api/v1/projects/{project_id}
Request Body: ProjectUpdate
Response: ProjectResponse
```

#### プロジェクト削除
```
DELETE /api/v1/projects/{project_id}
Response: SuccessResponse
```

### 3.2 プロジェクトメンバー管理

#### メンバー追加
```
POST /api/v1/projects/{project_id}/members
Request Body: ProjectMemberCreate
Response: ProjectMemberResponse
```

#### メンバー一覧取得
```
GET /api/v1/projects/{project_id}/members
Response: List[ProjectMemberResponse]
```

#### メンバー更新
```
PUT /api/v1/projects/{project_id}/members/{member_id}
Request Body: ProjectMemberUpdate
Response: ProjectMemberResponse
```

#### メンバー削除
```
DELETE /api/v1/projects/{project_id}/members/{member_id}
Response: SuccessResponse
```

### 3.3 プロジェクトフェーズ管理

#### フェーズ作成
```
POST /api/v1/projects/{project_id}/phases
Request Body: ProjectPhaseCreate
Response: ProjectPhaseResponse
```

#### フェーズ一覧取得
```
GET /api/v1/projects/{project_id}/phases
Response: List[ProjectPhaseResponse]
```

### 3.4 マイルストーン管理

#### マイルストーン作成
```
POST /api/v1/projects/{project_id}/milestones
Request Body: ProjectMilestoneCreate
Response: ProjectMilestoneResponse
```

#### マイルストーン一覧取得
```
GET /api/v1/projects/{project_id}/milestones
Response: List[ProjectMilestoneResponse]
```

### 3.5 階層・統計API

#### プロジェクトツリー取得
```
GET /api/v1/projects/tree
Query Parameters:
  - root_id: int (optional)
Response: List[ProjectTree]
```

#### プロジェクト統計取得
```
GET /api/v1/projects/{project_id}/statistics
Response: ProjectStatistics
```

## 4. ビジネスロジック

### 4.1 プロジェクトステータス管理
- `planning`: 計画中
- `in_progress`: 進行中
- `completed`: 完了
- `cancelled`: キャンセル
- `on_hold`: 保留

### 4.2 権限管理
- プロジェクト作成: 組織管理者またはプロジェクト管理権限
- プロジェクト更新: プロジェクトマネージャーまたは上位権限
- メンバー管理: プロジェクトマネージャー権限
- 閲覧: プロジェクトメンバーまたは組織メンバー

### 4.3 バリデーションルール
- プロジェクトコードは組織内で一意
- 計画終了日は計画開始日より後
- 親プロジェクトの期間内に子プロジェクトが収まる
- 予算は0以上
- 進捗率は0-100の範囲

### 4.4 自動計算
- 子プロジェクトの進捗から親プロジェクトの進捗を自動計算
- フェーズの完了状況からプロジェクト進捗を更新
- 実績コストの自動集計

## 5. セキュリティ要件

### 5.1 アクセス制御
- プロジェクトメンバーのみがプロジェクト詳細を閲覧可能
- 組織外のユーザーはアクセス不可
- 部門制限がある場合は部門メンバーのみアクセス可能

### 5.2 監査ログ
- すべての作成・更新・削除操作を記録
- プロジェクトメンバーの追加・削除を記録
- ステータス変更を記録

### 5.3 データ保護
- ソフトデリート実装により誤削除を防止
- 重要な変更には承認フローを実装可能
- 定期的なバックアップ

## 6. パフォーマンス要件

### 6.1 レスポンスタイム
- 一覧取得: <200ms
- 詳細取得: <100ms
- 作成・更新: <300ms

### 6.2 スケーラビリティ
- 10,000プロジェクトまで対応
- プロジェクトあたり1,000メンバーまで対応
- 階層は最大10レベルまで

### 6.3 最適化
- プロジェクト一覧はページネーション必須
- 頻繁にアクセスされるデータはキャッシュ
- インデックスの適切な設定

## 7. テスト要件

### 7.1 単体テスト
- モデルのバリデーションテスト
- リポジトリのCRUDテスト
- サービス層のビジネスロジックテスト

### 7.2 統合テスト
- API エンドポイントテスト
- 権限チェックテスト
- データベーストランザクションテスト

### 7.3 パフォーマンステスト
- 大量データでのレスポンステスト
- 同時アクセステスト
- メモリ使用量テスト

## 8. 将来の拡張性

### 8.1 追加予定機能
- ガントチャート表示用API
- プロジェクトテンプレート機能
- リソース管理機能
- プロジェクト間の依存関係管理

### 8.2 統合予定
- タスク管理機能との連携
- ダッシュボードでの表示
- 通知機能との連携
- レポート生成機能