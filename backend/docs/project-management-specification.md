# プロジェクト管理機能仕様書

**文書番号**: ITDO-ERP-PROJ-001  
**バージョン**: 1.0  
**作成日**: 2025年7月6日  
**作成者**: Claude Code AI  
**承認者**: ootakazuhiko

---

## 1. 概要

### 1.1 目的
ITDOERPシステムにおけるプロジェクト管理基本機能の実装仕様を定義する。

### 1.2 適用範囲
- プロジェクト作成・管理機能（PROJ-001）
- シンプルなタスク管理機能（PROJ-002）
- マルチテナント対応
- RBAC統合

### 1.3 前提条件
- Phase 2-B（ユーザー管理機能）が完了済み
- マルチテナント基盤が利用可能
- RBAC基盤が利用可能

---

## 2. 機能要件

### 2.1 プロジェクト管理機能（PROJ-001）

#### 2.1.1 プロジェクト作成
- **機能ID**: PROJ-001-01
- **概要**: 新規プロジェクトの作成
- **入力項目**:
  - プロジェクト名（必須、最大100文字）
  - プロジェクト説明（任意、最大1000文字）
  - 開始日（必須）
  - 終了日（任意）
  - ステータス（計画中/実行中/完了/中断）
  - 組織ID（必須、マルチテナント）
- **出力**: 作成されたプロジェクト情報

#### 2.1.2 プロジェクト一覧取得
- **機能ID**: PROJ-001-02
- **概要**: プロジェクト一覧の取得（ページネーション対応）
- **フィルタ条件**:
  - 組織ID（マルチテナント）
  - ステータス
  - 作成者
  - 日付範囲
- **ソート条件**: 作成日時、更新日時、名前

#### 2.1.3 プロジェクト詳細取得
- **機能ID**: PROJ-001-03
- **概要**: 指定されたプロジェクトの詳細情報取得
- **権限チェック**: プロジェクトへのアクセス権限確認

#### 2.1.4 プロジェクト更新
- **機能ID**: PROJ-001-04
- **概要**: プロジェクト情報の更新
- **権限チェック**: プロジェクト編集権限確認

#### 2.1.5 プロジェクト削除
- **機能ID**: PROJ-001-05
- **概要**: プロジェクトの削除（ソフトデリート）
- **権限チェック**: プロジェクト削除権限確認

### 2.2 タスク管理機能（PROJ-002）

#### 2.2.1 タスク作成
- **機能ID**: PROJ-002-01
- **概要**: プロジェクト内でのタスク作成
- **入力項目**:
  - タスク名（必須、最大200文字）
  - タスク説明（任意、最大2000文字）
  - 担当者ID（任意）
  - 優先度（低/中/高/緊急）
  - ステータス（未着手/進行中/完了/保留）
  - 予定開始日（任意）
  - 予定終了日（任意）
  - プロジェクトID（必須）

#### 2.2.2 タスク一覧取得
- **機能ID**: PROJ-002-02
- **概要**: プロジェクト内のタスク一覧取得
- **フィルタ条件**:
  - プロジェクトID
  - 担当者ID
  - ステータス
  - 優先度

#### 2.2.3 タスク詳細取得・更新・削除
- **機能ID**: PROJ-002-03, PROJ-002-04, PROJ-002-05
- **概要**: タスクの基本CRUD操作

---

## 3. データモデル

### 3.1 プロジェクトモデル（projects）

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'planning',
    start_date DATE NOT NULL,
    end_date DATE,
    organization_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    updated_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by INTEGER,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    FOREIGN KEY (deleted_by) REFERENCES users(id)
);
```

### 3.2 タスクモデル（tasks）

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    project_id INTEGER NOT NULL,
    assigned_to INTEGER,
    estimated_start_date DATE,
    estimated_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    created_by INTEGER NOT NULL,
    updated_by INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by INTEGER,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    FOREIGN KEY (deleted_by) REFERENCES users(id)
);
```

---

## 4. API仕様

### 4.1 プロジェクト管理API

#### 4.1.1 プロジェクト作成
- **メソッド**: POST
- **エンドポイント**: `/api/v1/projects`
- **リクエスト**:
```json
{
  "name": "新規プロジェクト",
  "description": "プロジェクトの説明",
  "start_date": "2025-07-01",
  "end_date": "2025-12-31",
  "status": "planning",
  "organization_id": 1
}
```
- **レスポンス**: 201 Created
```json
{
  "id": 1,
  "name": "新規プロジェクト",
  "description": "プロジェクトの説明",
  "status": "planning",
  "start_date": "2025-07-01",
  "end_date": "2025-12-31",
  "organization_id": 1,
  "created_by": 1,
  "created_at": "2025-07-06T10:00:00Z",
  "updated_at": "2025-07-06T10:00:00Z"
}
```

#### 4.1.2 プロジェクト一覧取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/projects`
- **クエリパラメータ**:
  - `page`: ページ番号（デフォルト: 1）
  - `limit`: 1ページあたりの件数（デフォルト: 20、最大: 100）
  - `status`: ステータスフィルタ
  - `organization_id`: 組織IDフィルタ（管理者のみ）

#### 4.1.3 プロジェクト詳細取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/projects/{project_id}`

#### 4.1.4 プロジェクト更新
- **メソッド**: PUT
- **エンドポイント**: `/api/v1/projects/{project_id}`

#### 4.1.5 プロジェクト削除
- **メソッド**: DELETE
- **エンドポイント**: `/api/v1/projects/{project_id}`

### 4.2 タスク管理API

#### 4.2.1 タスク作成
- **メソッド**: POST
- **エンドポイント**: `/api/v1/projects/{project_id}/tasks`

#### 4.2.2 タスク一覧取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/projects/{project_id}/tasks`

#### 4.2.3 タスク詳細取得
- **メソッド**: GET
- **エンドポイント**: `/api/v1/tasks/{task_id}`

#### 4.2.4 タスク更新
- **メソッド**: PUT
- **エンドポイント**: `/api/v1/tasks/{task_id}`

#### 4.2.5 タスク削除
- **メソッド**: DELETE
- **エンドポイント**: `/api/v1/tasks/{task_id}`

---

## 5. セキュリティ要件

### 5.1 認証・認可
- すべてのAPIエンドポイントで認証が必要
- JWTトークンによる認証
- 組織別データアクセス制御（マルチテナント）

### 5.2 権限制御
- **プロジェクト作成**: 組織メンバー以上
- **プロジェクト参照**: プロジェクトメンバー以上
- **プロジェクト編集**: プロジェクト管理者以上
- **プロジェクト削除**: プロジェクト管理者またはシステム管理者

### 5.3 データバリデーション
- 入力値の型チェック
- 文字数制限チェック
- 必須項目チェック
- 日付の妥当性チェック

---

## 6. 非機能要件

### 6.1 パフォーマンス
- API応答時間: 200ms以下
- 大量データ処理: ページネーション必須

### 6.2 可用性
- サービス稼働率: 99.9%以上

### 6.3 拡張性
- プロジェクトテンプレート機能への拡張を考慮
- カスタムフィールド追加への対応

---

## 7. テスト要件

### 7.1 テストカバレッジ
- 単体テスト: 80%以上
- 統合テスト: 主要シナリオカバー

### 7.2 テスト種別
1. **単体テスト**
   - モデルバリデーション
   - ビジネスロジック
   - API レスポンス

2. **統合テスト**
   - API エンドツーエンド
   - データベース連携
   - 認証・認可

3. **セキュリティテスト**
   - SQL インジェクション
   - XSS 攻撃
   - 権限チェック

---

## 8. 実装スケジュール

### フェーズ3-A（1日）
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