# ユーザー管理機能仕様書

## 1. 概要

### 1.1 目的
マルチテナント ERP システムにおけるユーザー管理機能を提供し、組織・部門・ロールベースのアクセス制御を実現する。

### 1.2 スコープ
- ユーザーのライフサイクル管理（作成・更新・削除）
- ロール・権限管理
- マルチテナント環境でのデータ分離
- セキュリティ制御

## 2. 機能要件

### 2.1 ユーザー管理機能

#### 2.1.1 ユーザー作成
- **権限**: システム管理者、組織管理者のみ
- **入力項目**:
  - メールアドレス（必須、一意）
  - フルネーム（必須）
  - パスワード（必須、強度チェック）
  - 電話番号（任意）
  - 所属組織（必須）
  - 所属部門（任意）
  - 初期ロール（必須）
  - アクティブフラグ（デフォルト: true）

#### 2.1.2 ユーザー一覧・検索
- **権限**: 組織管理者は自組織ユーザーのみ、システム管理者は全ユーザー
- **検索条件**:
  - 名前（部分一致）
  - メールアドレス（部分一致）
  - 所属組織
  - 所属部門
  - ロール
  - アクティブ状態
- **ページネーション**: 対応（デフォルト 20件/ページ）

#### 2.1.3 ユーザー詳細表示
- **権限**: 自分自身、または管理権限を持つユーザー
- **表示項目**: 基本情報、所属情報、ロール情報、最終ログイン日時

#### 2.1.4 ユーザー更新
- **権限**: 
  - 基本情報: 自分自身、または管理権限を持つユーザー
  - ロール変更: 組織管理者以上
  - 組織・部門変更: システム管理者のみ
- **更新可能項目**: フルネーム、電話番号、パスワード

#### 2.1.5 ユーザー削除（論理削除）
- **権限**: システム管理者のみ
- **制約**: 
  - 自分自身は削除不可
  - システム管理者は最低1人必要

### 2.2 ロール・権限管理

#### 2.2.1 ロール割り当て
- **権限**: 組織管理者以上
- **割り当て可能ロール**:
  - 組織管理者: 自組織内の全ロール
  - システム管理者: 全ロール
- **制約**:
  - 一人のユーザーに複数ロール可能
  - 組織・部門レベルでの制限
  - 期限付き割り当て可能

#### 2.2.2 権限継承
- **階層構造**: システム > 組織 > 部門
- **継承ルール**:
  - 上位レベルの権限は下位に継承
  - 明示的な拒否設定で継承を無効化可能
  - 部門管理者は子部門の権限も継承

### 2.3 パスワード管理

#### 2.3.1 パスワード変更
- **権限**: 自分自身、または管理権限を持つユーザー
- **要件**: 
  - 現在のパスワード確認（自分の場合）
  - 新パスワードの強度チェック
  - パスワード履歴チェック（直近3回は使用不可）

#### 2.3.2 パスワードリセット
- **権限**: 組織管理者以上
- **フロー**:
  1. 管理者が一時パスワードを生成
  2. ユーザーに安全な方法で通知
  3. 初回ログイン時にパスワード変更を強制

## 3. 非機能要件

### 3.1 セキュリティ要件

#### 3.1.1 認証・認可
- JWT ベースの認証
- ロールベースアクセス制御（RBAC）
- セッション管理（リフレッシュトークン対応）

#### 3.1.2 データ保護
- パスワードハッシュ化（bcrypt）
- 個人情報の暗号化
- 監査ログの記録

#### 3.1.3 マルチテナント分離
- 組織レベルでのデータ完全分離
- Cross-tenant アクセスの防止
- Row Level Security（RLS）の実装

### 3.2 パフォーマンス要件
- ユーザー一覧表示: 200ms 以内
- ユーザー検索: 500ms 以内
- 同時ユーザー数: 1000人対応

### 3.3 可用性要件
- 稼働率: 99.9%
- バックアップ: 日次
- 復旧時間: 4時間以内

## 4. データモデル

### 4.1 ユーザー拡張情報
```sql
-- User モデルの拡張
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN profile_image_url VARCHAR(500);
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
```

### 4.2 パスワード履歴
```sql
CREATE TABLE password_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.3 ユーザーセッション
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) NOT NULL,
    refresh_token VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 5. API エンドポイント

### 5.1 ユーザー管理 API

#### POST /api/v1/users
```json
{
  "email": "user@example.com",
  "full_name": "田中太郎",
  "phone": "090-1234-5678",
  "password": "SecurePass123!",
  "organization_id": 1,
  "department_id": 2,
  "role_ids": [2, 3],
  "is_active": true
}
```

#### GET /api/v1/users
```
Query Parameters:
- page: int (default: 1)
- limit: int (default: 20)
- search: string
- organization_id: int
- department_id: int
- role_id: int
- is_active: boolean
```

#### GET /api/v1/users/{user_id}
ユーザー詳細情報を取得

#### PUT /api/v1/users/{user_id}
```json
{
  "full_name": "田中次郎",
  "phone": "090-5678-1234"
}
```

#### DELETE /api/v1/users/{user_id}
論理削除（is_active = false）

### 5.2 ロール管理 API

#### POST /api/v1/users/{user_id}/roles
```json
{
  "role_id": 2,
  "organization_id": 1,
  "department_id": 2,
  "expires_at": "2024-12-31T23:59:59Z"
}
```

#### DELETE /api/v1/users/{user_id}/roles/{role_id}
ロール割り当て解除

#### GET /api/v1/users/{user_id}/permissions
ユーザーの実効権限一覧

### 5.3 パスワード管理 API

#### PUT /api/v1/users/{user_id}/password
```json
{
  "current_password": "current_pass",
  "new_password": "new_secure_pass"
}
```

#### POST /api/v1/users/{user_id}/password/reset
管理者によるパスワードリセット

## 6. セキュリティ制御

### 6.1 アクセス制御マトリックス

| 操作 | システム管理者 | 組織管理者 | 部門管理者 | 一般ユーザー |
|------|----------------|------------|------------|--------------|
| ユーザー作成 | ○ | ○（自組織内） | × | × |
| ユーザー一覧 | ○（全組織） | ○（自組織） | ○（自部門） | ×（自分のみ） |
| ユーザー詳細 | ○ | ○（自組織） | ○（自部門） | ○（自分のみ） |
| ユーザー更新 | ○ | ○（自組織） | ○（自部門） | ○（自分のみ） |
| ユーザー削除 | ○ | × | × | × |
| ロール割り当て | ○ | ○（自組織内） | × | × |

### 6.2 監査ログ
全ての操作について以下の情報を記録：
- 操作者
- 操作対象
- 操作内容
- 実行日時
- IPアドレス
- 結果（成功/失敗）

### 6.3 セキュリティ制約
- パスワード強度: 8文字以上、大小英数字・記号を3種類以上
- ログイン試行制限: 5回失敗で30分ロック
- セッション有効期限: 24時間（アクセストークン）、7日間（リフレッシュトークン）
- 同時セッション制限: 5セッション/ユーザー

## 7. エラーハンドリング

### 7.1 エラーコード定義
- USER001: ユーザーが既に存在します
- USER002: ユーザーが見つかりません
- USER003: 権限が不足しています
- USER004: パスワードが無効です
- USER005: アカウントがロックされています
- USER006: 無効なロール割り当てです

### 7.2 エラーレスポンス形式
```json
{
  "detail": "エラーメッセージ",
  "code": "USER001",
  "timestamp": "2024-01-01T00:00:00Z",
  "field": "email"
}
```

## 8. テスト要件

### 8.1 単体テスト
- モデルレベルの検証
- サービスロジックの検証
- 権限制御の検証

### 8.2 統合テスト
- API エンドポイントの検証
- 認証・認可の検証
- データ整合性の検証

### 8.3 セキュリティテスト
- 権限昇格攻撃の防止
- SQLインジェクションの防止
- XSSの防止
- マルチテナント分離の検証

## 9. 実装スケジュール

### Phase 1: 基盤実装（1日目）
- User モデル拡張
- 基本 CRUD API
- 認証・認可機能

### Phase 2: 高度機能（2日目）
- ロール管理機能
- パスワード管理機能
- 検索・フィルタリング

### Phase 3: セキュリティ強化（3日目）
- 監査ログ
- セキュリティ制約
- パフォーマンス最適化