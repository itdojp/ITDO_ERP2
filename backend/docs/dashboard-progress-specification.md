# 進捗管理・ダッシュボード機能仕様書

**文書番号**: ITDO-ERP-DASH-001  
**バージョン**: 1.0  
**作成日**: 2025年7月6日  
**作成者**: Claude Code AI  
**承認者**: ootakazuhiko

---

## 1. 概要

### 1.1 目的
ITDOERPシステムにおける進捗管理とダッシュボード機能の実装仕様を定義する。

### 1.2 適用範囲
- 基本的な進捗管理機能（PROJ-005）
- KPI表示機能（DASH-001）
- リアルタイム更新機能
- パフォーマンス最適化

### 1.3 前提条件
- Phase 3-A（プロジェクト管理機能）が完了済み
- プロジェクト・タスクデータが利用可能
- マルチテナント基盤が利用可能
- RBAC基盤が利用可能

---

## 2. 機能要件

### 2.1 進捗管理機能（PROJ-005）

#### 2.1.1 プロジェクト進捗計算
- **機能ID**: PROJ-005-01
- **概要**: プロジェクトの進捗率を計算
- **計算方法**:
  - タスク完了率ベース: 完了タスク数 / 全タスク数 × 100
  - 工数ベース: 完了工数 / 全工数 × 100
  - 期間ベース: 経過日数 / 予定日数 × 100

#### 2.1.2 期日遅れ検出
- **機能ID**: PROJ-005-02
- **概要**: 期日を過ぎたプロジェクト・タスクの検出
- **アラート条件**:
  - 終了予定日を過ぎたプロジェクト
  - 終了予定日を過ぎたタスク
  - 終了予定日まで3日以内のプロジェクト・タスク

#### 2.1.3 進捗レポート生成
- **機能ID**: PROJ-005-03
- **概要**: 進捗状況のレポート生成
- **出力形式**: JSON, CSV
- **レポート内容**:
  - プロジェクト概要
  - 進捗状況
  - 期日遅れ情報
  - タスク完了状況

### 2.2 ダッシュボード機能（DASH-001）

#### 2.2.1 プロジェクト統計表示
- **機能ID**: DASH-001-01
- **概要**: プロジェクト全体の統計情報表示
- **表示項目**:
  - 総プロジェクト数
  - ステータス別プロジェクト数
  - 今月完了プロジェクト数
  - 期日遅れプロジェクト数

#### 2.2.2 タスク統計表示
- **機能ID**: DASH-001-02
- **概要**: タスク全体の統計情報表示
- **表示項目**:
  - 総タスク数
  - ステータス別タスク数
  - 優先度別タスク数
  - 今日期限のタスク数

#### 2.2.3 進捗グラフ表示
- **機能ID**: DASH-001-03
- **概要**: 進捗状況のグラフィカル表示
- **グラフ種別**:
  - 円グラフ: ステータス別分布
  - 棒グラフ: 期間別完了数
  - 線グラフ: 進捗率推移
  - ガントチャート: プロジェクトスケジュール

#### 2.2.4 期日アラート表示
- **機能ID**: DASH-001-04
- **概要**: 期日に関するアラート表示
- **アラート種別**:
  - 期日超過（赤）
  - 期日間近（黄）
  - 正常（緑）

### 2.3 リアルタイム更新機能

#### 2.3.1 WebSocket通信
- **機能ID**: REAL-001
- **概要**: リアルタイムデータ更新
- **更新イベント**:
  - プロジェクト作成・更新・削除
  - タスク作成・更新・削除・ステータス変更
  - 進捗率変更

#### 2.3.2 通知機能
- **機能ID**: REAL-002
- **概要**: 重要な変更の通知
- **通知条件**:
  - 期日超過発生
  - プロジェクト完了
  - タスク割り当て

---

## 3. データモデル

### 3.1 ダッシュボード統計（dashboard_stats）

```sql
-- ビューとして実装（実テーブルではない）
CREATE VIEW dashboard_stats AS
SELECT 
    organization_id,
    COUNT(*) as total_projects,
    COUNT(CASE WHEN status = 'planning' THEN 1 END) as planning_projects,
    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_projects,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_projects,
    COUNT(CASE WHEN end_date < CURRENT_DATE AND status != 'completed' THEN 1 END) as overdue_projects,
    updated_at
FROM projects 
WHERE deleted_at IS NULL
GROUP BY organization_id;
```

### 3.2 進捗計算（project_progress）

```sql
-- ビューとして実装
CREATE VIEW project_progress AS
SELECT 
    p.id as project_id,
    p.organization_id,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    CASE 
        WHEN COUNT(t.id) = 0 THEN 0
        ELSE ROUND(COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / COUNT(t.id), 2)
    END as completion_percentage,
    CASE 
        WHEN p.end_date < CURRENT_DATE AND p.status != 'completed' THEN true
        ELSE false
    END as is_overdue
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id AND t.deleted_at IS NULL
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.organization_id;
```

---

## 4. API仕様

### 4.1 ダッシュボードAPI

#### 4.1.1 ダッシュボード統計取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/dashboard/stats`
- **クエリパラメータ**:
  - `organization_id`: 組織ID（管理者のみ）
- **レスポンス**: 200 OK
```json
{
  "project_stats": {
    "total": 25,
    "planning": 5,
    "in_progress": 15,
    "completed": 5,
    "overdue": 3
  },
  "task_stats": {
    "total": 150,
    "not_started": 30,
    "in_progress": 80,
    "completed": 35,
    "on_hold": 5,
    "overdue": 12
  },
  "recent_activity": [
    {
      "type": "project_completed",
      "project_name": "プロジェクトA",
      "timestamp": "2025-07-06T10:00:00Z"
    }
  ]
}
```

#### 4.1.2 進捗データ取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/dashboard/progress`
- **クエリパラメータ**:
  - `period`: 期間（week/month/quarter）
  - `organization_id`: 組織ID（管理者のみ）
- **レスポンス**: 200 OK
```json
{
  "period": "month",
  "progress_data": [
    {
      "date": "2025-07-01",
      "completed_projects": 2,
      "completed_tasks": 15,
      "total_progress": 65.5
    }
  ],
  "project_progress": [
    {
      "project_id": 1,
      "project_name": "プロジェクトA",
      "completion_percentage": 75.0,
      "total_tasks": 20,
      "completed_tasks": 15,
      "is_overdue": false
    }
  ]
}
```

#### 4.1.3 期日アラート取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/dashboard/alerts`
- **レスポンス**: 200 OK
```json
{
  "overdue_projects": [
    {
      "project_id": 5,
      "project_name": "遅延プロジェクト",
      "end_date": "2025-07-01",
      "days_overdue": 5
    }
  ],
  "overdue_tasks": [
    {
      "task_id": 25,
      "task_title": "遅延タスク",
      "project_name": "プロジェクトB",
      "end_date": "2025-07-03",
      "days_overdue": 3
    }
  ],
  "upcoming_deadlines": [
    {
      "type": "project",
      "id": 3,
      "name": "期限間近プロジェクト",
      "end_date": "2025-07-08",
      "days_remaining": 2
    }
  ]
}
```

### 4.2 進捗管理API

#### 4.2.1 プロジェクト進捗取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/projects/{project_id}/progress`
- **レスポンス**: 200 OK
```json
{
  "project_id": 1,
  "completion_percentage": 75.0,
  "total_tasks": 20,
  "completed_tasks": 15,
  "task_breakdown": {
    "not_started": 2,
    "in_progress": 3,
    "completed": 15,
    "on_hold": 0
  },
  "timeline": {
    "start_date": "2025-06-01",
    "end_date": "2025-08-31",
    "days_elapsed": 35,
    "days_remaining": 56,
    "is_on_track": true
  }
}
```

#### 4.2.2 進捗レポート生成
- **メソッド**: GET
- **エンドポイント**: `/api/v1/projects/{project_id}/report`
- **クエリパラメータ**:
  - `format`: csv | json（デフォルト: json）
- **レスポンス**: 200 OK（JSONまたはCSVファイル）

### 4.3 WebSocket API

#### 4.3.1 リアルタイム更新
- **エンドポイント**: `/ws/dashboard`
- **認証**: JWTトークン
- **メッセージ形式**:
```json
{
  "type": "progress_update",
  "data": {
    "project_id": 1,
    "completion_percentage": 80.0,
    "updated_at": "2025-07-06T10:30:00Z"
  }
}
```

---

## 5. セキュリティ要件

### 5.1 認証・認可
- すべてのAPIエンドポイントで認証が必要
- WebSocket接続でJWT認証
- 組織別データアクセス制御（マルチテナント）

### 5.2 権限制御
- **ダッシュボード参照**: 組織メンバー以上
- **進捗データ参照**: プロジェクトメンバー以上
- **レポート生成**: プロジェクトメンバー以上
- **組織横断データ**: システム管理者のみ

### 5.3 データ保護
- センシティブな統計データの適切な権限制御
- ログイン状況の追跡
- 監査ログ記録

---

## 6. 非機能要件

### 6.1 パフォーマンス
- ダッシュボード読み込み時間: 500ms以下
- 統計計算処理時間: 200ms以下
- WebSocket通信遅延: 100ms以下
- 大量データ処理: ページネーション必須

### 6.2 可用性
- サービス稼働率: 99.9%以上
- WebSocket接続安定性: 99%以上

### 6.3 拡張性
- 組織数: 1000組織まで対応
- プロジェクト数: 10000プロジェクトまで対応
- 同時WebSocket接続: 1000接続まで対応

---

## 7. 技術仕様

### 7.1 バックエンド
- **フレームワーク**: FastAPI
- **WebSocket**: FastAPI WebSocket
- **データベース**: PostgreSQL（ビュー活用）
- **キャッシュ**: Redis（統計データキャッシュ）

### 7.2 フロントエンド
- **フレームワーク**: React 18
- **チャートライブラリ**: Chart.js または Recharts
- **WebSocket**: native WebSocket API
- **状態管理**: React Query + Zustand

### 7.3 リアルタイム通信
- **プロトコル**: WebSocket
- **認証**: JWT Bearer Token
- **フォーマット**: JSON

---

## 8. 実装スケジュール

### フェーズ3-B（1日）
1. **仕様書作成**（完了）
2. **テスト仕様作成**（2時間）
3. **テストコード実装**（3時間）
4. **実装**（3時間）

---

## 9. 改訂履歴

| バージョン | 改訂日 | 改訂内容 | 改訂者 |
|------------|--------|----------|--------|
| 1.0 | 2025/07/06 | 初版作成 | Claude Code AI |

---

**承認**

プロジェクトオーナー: ootakazuhiko _________________ 日付: 2025/07/06  
Claude Code AI: _________________ 日付: 2025/07/06