# ITDO ERP API設計書

**文書番号**: ITDO-ERP-API-001  
**バージョン**: 1.0  
**作成日**: 2025年7月5日  
**作成者**: システム設計チーム  
**承認者**: ootakazuhiko  

---

## 1. はじめに

### 1.1 目的
本書は、ITDO ERPシステムのWeb APIの設計を詳細に定義し、APIの構造、エンドポイント、データフォーマット、セキュリティ、およびベストプラクティスを明確にすることを目的とする。

### 1.2 API設計原則
- **RESTful**: REST原則に準拠した設計
- **一貫性**: 統一されたURLパターンとレスポンス形式
- **バージョニング**: 後方互換性を考慮したバージョン管理
- **セキュリティ**: JWT認証とRBACによるアクセス制御
- **国際化**: 多言語対応とタイムゾーン考慮

### 1.3 対象読者
- フロントエンド開発者
- バックエンド開発者
- 外部システム連携担当者
- APIテスト担当者

---

## 2. API基本仕様

### 2.1 基本情報

| 項目 | 内容 |
|------|------|
| プロトコル | HTTPS |
| データ形式 | JSON |
| 文字コード | UTF-8 |
| 日時形式 | ISO 8601 (例: 2025-01-04T10:30:00+09:00) |
| APIバージョン | v1 |
| ベースURL | https://api.itdo-erp.com/api/v1 |

### 2.2 HTTPメソッド

| メソッド | 用途 | 冪等性 |
|----------|------|--------|
| GET | リソースの取得 | Yes |
| POST | リソースの作成 | No |
| PUT | リソースの完全更新 | Yes |
| PATCH | リソースの部分更新 | Yes |
| DELETE | リソースの削除 | Yes |

### 2.3 ステータスコード

| コード | 意味 | 使用場面 |
|--------|------|----------|
| 200 | OK | 正常な取得、更新、削除 |
| 201 | Created | リソースの作成成功 |
| 204 | No Content | 削除成功（レスポンスボディなし） |
| 400 | Bad Request | リクエストパラメータエラー |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | 権限不足 |
| 404 | Not Found | リソースが存在しない |
| 409 | Conflict | リソースの競合（重複など） |
| 422 | Unprocessable Entity | バリデーションエラー |
| 429 | Too Many Requests | レート制限超過 |
| 500 | Internal Server Error | サーバーエラー |

---

## 3. 認証・認可

### 3.1 認証フロー

```
1. ログイン
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

2. レスポンス
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
  "token_type": "Bearer",
  "expires_in": 3600
}

3. APIリクエスト
GET /api/v1/projects
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 3.2 権限レベル

| レベル | 説明 | スコープ |
|--------|------|----------|
| SystemAdmin | システム管理者 | 全機能 |
| CompanyAdmin | 企業管理者 | 自社の全機能 |
| DepartmentManager | 部門管理者 | 部門内の機能 |
| User | 一般ユーザー | 割り当てられた機能 |

---

## 4. 共通仕様

### 4.1 リクエストヘッダー

| ヘッダー名 | 必須 | 説明 | 例 |
|------------|------|------|-----|
| Authorization | Yes | 認証トークン | Bearer {token} |
| Accept | Yes | レスポンス形式 | application/json |
| Content-Type | Yes* | リクエストボディ形式 | application/json |
| Accept-Language | No | 言語指定 | ja-JP |
| X-Request-ID | No | リクエスト追跡ID | uuid-v4 |

*POSTやPUTリクエスト時のみ必須

### 4.2 レスポンス形式

#### 4.2.1 成功レスポンス
```json
{
  "success": true,
  "data": {
    // リソースデータ
  },
  "meta": {
    "timestamp": "2025-01-04T10:30:00+09:00",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 4.2.2 エラーレスポンス
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が正しくありません",
    "details": [
      {
        "field": "email",
        "message": "有効なメールアドレスを入力してください"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-01-04T10:30:00+09:00",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 4.3 ページネーション

#### 4.3.1 リクエストパラメータ
| パラメータ | 説明 | デフォルト | 最大値 |
|------------|------|------------|--------|
| page | ページ番号 | 1 | - |
| limit | 1ページあたりの件数 | 20 | 100 |
| sort | ソート項目 | created_at | - |
| order | ソート順序 (asc/desc) | desc | - |

#### 4.3.2 レスポンス形式
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "links": {
    "self": "/api/v1/projects?page=1&limit=20",
    "first": "/api/v1/projects?page=1&limit=20",
    "last": "/api/v1/projects?page=8&limit=20",
    "next": "/api/v1/projects?page=2&limit=20",
    "prev": null
  }
}
```

### 4.4 フィルタリング

```
GET /api/v1/projects?status=active&created_after=2025-01-01&manager_id=uuid
```

---

## 5. APIエンドポイント仕様

### 5.1 認証API

#### 5.1.1 ログイン
```yaml
POST /api/v1/auth/login
Description: ユーザーログイン
Request:
  Content-Type: application/json
  Body:
    email: string (required)
    password: string (required)
    remember_me: boolean (optional)
Response:
  200:
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: integer
    user:
      id: uuid
      email: string
      name: string
      roles: array
```

#### 5.1.2 トークンリフレッシュ
```yaml
POST /api/v1/auth/refresh
Description: アクセストークンの更新
Request:
  Content-Type: application/json
  Body:
    refresh_token: string (required)
Response:
  200:
    access_token: string
    token_type: string
    expires_in: integer
```

### 5.2 ユーザー管理API

#### 5.2.1 ユーザー一覧取得
```yaml
GET /api/v1/users
Description: ユーザー一覧の取得
Parameters:
  - department_id: uuid (optional)
  - is_active: boolean (optional)
  - search: string (optional)
  - page: integer (optional)
  - limit: integer (optional)
Response:
  200:
    data:
      - id: uuid
        employee_code: string
        email: string
        full_name: string
        department:
          id: uuid
          name: string
        position: string
        is_active: boolean
```

#### 5.2.2 ユーザー詳細取得
```yaml
GET /api/v1/users/{user_id}
Description: ユーザー詳細情報の取得
Response:
  200:
    data:
      id: uuid
      employee_code: string
      email: string
      full_name: string
      full_name_kana: string
      department:
        id: uuid
        name: string
      position: string
      phone: string
      mobile: string
      hire_date: date
      is_active: boolean
      roles:
        - id: uuid
          name: string
          permissions: array
```

#### 5.2.3 ユーザー作成
```yaml
POST /api/v1/users
Description: 新規ユーザーの作成
Request:
  Content-Type: application/json
  Body:
    employee_code: string (required)
    email: string (required)
    password: string (required)
    full_name: string (required)
    full_name_kana: string (optional)
    department_id: uuid (required)
    position: string (optional)
    phone: string (optional)
    mobile: string (optional)
    hire_date: date (optional)
    role_ids: array[uuid] (required)
Response:
  201:
    data: {user object}
    location: /api/v1/users/{user_id}
```

### 5.3 プロジェクト管理API

#### 5.3.1 プロジェクト一覧取得
```yaml
GET /api/v1/projects
Description: プロジェクト一覧の取得
Parameters:
  - status: string (optional) [planning, active, completed, suspended]
  - manager_id: uuid (optional)
  - customer_id: uuid (optional)
  - start_date_from: date (optional)
  - start_date_to: date (optional)
  - include_archived: boolean (optional, default: false)
Response:
  200:
    data:
      - id: uuid
        project_code: string
        name: string
        customer:
          id: uuid
          name: string
        manager:
          id: uuid
          name: string
        status: string
        planned_start_date: date
        planned_end_date: date
        progress_percentage: number
        budget_amount: number
```

#### 5.3.2 プロジェクト作成
```yaml
POST /api/v1/projects
Description: 新規プロジェクトの作成
Request:
  Content-Type: application/json
  Body:
    project_code: string (required)
    name: string (required)
    description: string (optional)
    customer_id: uuid (optional)
    project_type: string (required)
    manager_id: uuid (required)
    planned_start_date: date (required)
    planned_end_date: date (required)
    budget_amount: number (optional)
    member_ids: array[uuid] (optional)
Response:
  201:
    data: {project object}
    location: /api/v1/projects/{project_id}
```

### 5.4 タスク管理API

#### 5.4.1 タスク一覧取得
```yaml
GET /api/v1/projects/{project_id}/tasks
Description: プロジェクト内のタスク一覧取得
Parameters:
  - status: string (optional) [todo, in_progress, completed]
  - assignee_id: uuid (optional)
  - parent_task_id: uuid (optional)
Response:
  200:
    data:
      - id: uuid
        task_code: string
        name: string
        assignee:
          id: uuid
          name: string
        status: string
        priority: integer
        planned_start_date: date
        planned_end_date: date
        progress_percentage: number
        subtasks: array
```

### 5.5 経費管理API

#### 5.5.1 経費申請作成
```yaml
POST /api/v1/expenses
Description: 経費申請の作成
Request:
  Content-Type: application/json
  Body:
    expense_date: date (required)
    expense_category_id: uuid (required)
    amount: number (required)
    tax_amount: number (optional)
    project_id: uuid (optional)
    description: string (required)
    receipt_file: string (optional, base64)
Response:
  201:
    data:
      id: uuid
      expense_number: string
      status: string
      created_at: datetime
```

### 5.6 レポートAPI

#### 5.6.1 プロジェクトサマリー
```yaml
GET /api/v1/reports/project-summary
Description: プロジェクトサマリーレポートの取得
Parameters:
  - project_ids: array[uuid] (optional)
  - date_from: date (required)
  - date_to: date (required)
  - group_by: string (optional) [project, customer, department]
Response:
  200:
    data:
      summary:
        total_projects: integer
        active_projects: integer
        total_budget: number
        total_spent: number
        total_hours: number
      details:
        - project_id: uuid
          project_name: string
          budget: number
          spent: number
          hours: number
          progress: number
```

---

## 6. エラーコード一覧

### 6.1 共通エラーコード

| コード | HTTPステータス | 説明 |
|--------|----------------|------|
| UNAUTHORIZED | 401 | 認証が必要です |
| FORBIDDEN | 403 | アクセス権限がありません |
| NOT_FOUND | 404 | リソースが見つかりません |
| VALIDATION_ERROR | 422 | 入力値エラー |
| RATE_LIMIT_EXCEEDED | 429 | レート制限超過 |
| INTERNAL_ERROR | 500 | サーバー内部エラー |

### 6.2 業務エラーコード

| コード | HTTPステータス | 説明 |
|--------|----------------|------|
| DUPLICATE_EMAIL | 409 | メールアドレスが既に使用されています |
| INVALID_DATE_RANGE | 400 | 日付範囲が不正です |
| BUDGET_EXCEEDED | 400 | 予算を超過しています |
| TASK_DEPENDENCY_ERROR | 400 | タスクの依存関係エラー |
| WORKFLOW_STATE_ERROR | 400 | ワークフロー状態エラー |

---

## 7. API利用制限

### 7.1 レート制限

| 認証状態 | 制限 | 単位 |
|----------|------|------|
| 未認証 | 60 | リクエスト/時間 |
| 認証済み | 1000 | リクエスト/時間 |
| 管理者 | 5000 | リクエスト/時間 |

### 7.2 レート制限ヘッダー

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

---

## 8. セキュリティ

### 8.1 通信の暗号化
- 全ての通信はHTTPS（TLS 1.3）で暗号化
- HTTP Strict Transport Security (HSTS) の有効化

### 8.2 認証トークン
- JWT (JSON Web Token) を使用
- アクセストークン有効期限: 1時間
- リフレッシュトークン有効期限: 30日

### 8.3 CORS設定
```
Access-Control-Allow-Origin: https://app.itdo-erp.com
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, Accept, X-Request-ID
Access-Control-Max-Age: 86400
```

### 8.4 入力検証
- 全ての入力値はサーバー側で検証
- SQLインジェクション対策
- XSS対策（HTMLエスケープ）

---

## 9. API開発ガイドライン

### 9.1 URL設計
- 小文字とハイフン使用（snake_caseは避ける）
- 複数形を使用（/users, /projects）
- 階層は浅く保つ（3階層まで）

### 9.2 バージョニング
- URLパスにバージョンを含める（/api/v1/）
- 後方互換性を維持
- 非推奨APIは6ヶ月間維持

### 9.3 エラーハンドリング
- 一貫したエラーレスポンス形式
- 詳細なエラー情報の提供
- ログへの適切な記録

### 9.4 パフォーマンス
- N+1問題の回避
- 適切なインデックスの使用
- レスポンスの最小化（必要なフィールドのみ）

---

## 10. API仕様書の自動生成

### 10.1 OpenAPI仕様
```yaml
openapi: 3.0.3
info:
  title: ITDO ERP API
  version: 1.0.0
  description: ITDO ERP System REST API
servers:
  - url: https://api.itdo-erp.com/api/v1
    description: Production server
  - url: https://staging-api.itdo-erp.com/api/v1
    description: Staging server
```

### 10.2 自動生成ツール
- FastAPIの自動ドキュメント生成機能
- Swagger UI: /docs
- ReDoc: /redoc

---

## 11. サンプルコード

### 11.1 cURL
```bash
# ログイン
curl -X POST https://api.itdo-erp.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# プロジェクト一覧取得
curl -X GET https://api.itdo-erp.com/api/v1/projects \
  -H "Authorization: Bearer {access_token}"
```

### 11.2 JavaScript (Fetch API)
```javascript
// ログイン
const login = async () => {
  const response = await fetch('https://api.itdo-erp.com/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: 'user@example.com',
      password: 'password123'
    })
  });
  
  const data = await response.json();
  return data;
};

// APIリクエスト
const getProjects = async (token) => {
  const response = await fetch('https://api.itdo-erp.com/api/v1/projects', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  return data;
};
```

### 11.3 Python
```python
import requests

# ログイン
def login(email, password):
    url = "https://api.itdo-erp.com/api/v1/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    response = requests.post(url, json=payload)
    return response.json()

# プロジェクト一覧取得
def get_projects(token):
    url = "https://api.itdo-erp.com/api/v1/projects"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()
```

---

## 12. 改訂履歴

| バージョン | 改訂日 | 改訂内容 | 改訂者 |
|------------|--------|----------|--------|
| 1.0 | 2025/07/05 | 初版作成 | システム設計チーム |

---

**承認**

API設計リード: _________________ 日付: _______  
フロントエンドリード: _________________ 日付: _______  
セキュリティリード: _________________ 日付: _______