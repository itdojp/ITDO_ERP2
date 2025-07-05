# API 仕様書

## Organization Management API

### 基本情報
- **Base URL**: `/api/v1/organizations`
- **認証**: Bearer Token (JWT)
- **Content-Type**: `application/json`

### エンドポイント一覧

#### 1. 組織作成
```http
POST /api/v1/organizations
```

**権限**: システム管理者のみ

**リクエスト**:
```json
{
  "code": "ORG001",
  "name": "株式会社サンプル",
  "name_kana": "カブシキガイシャサンプル",
  "postal_code": "100-0001",
  "address": "東京都千代田区丸の内1-1-1",
  "phone": "03-1234-5678",
  "email": "info@sample.com",
  "website": "https://sample.com",
  "fiscal_year_start": 4
}
```

**レスポンス** (201 Created):
```json
{
  "id": 1,
  "code": "ORG001",
  "name": "株式会社サンプル",
  "name_kana": "カブシキガイシャサンプル",
  "postal_code": "100-0001",
  "address": "東京都千代田区丸の内1-1-1",
  "phone": "03-1234-5678",
  "email": "info@sample.com",
  "website": "https://sample.com",
  "fiscal_year_start": 4,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": 1,
  "updated_by": null
}
```

#### 2. 組織一覧取得
```http
GET /api/v1/organizations
```

**権限**: 所属組織のみ表示（システム管理者は全組織）

**クエリパラメータ**:
- `page` (int, optional): ページ番号 (default: 1)
- `limit` (int, optional): 1ページあたりの件数 (default: 10)
- `search` (string, optional): 検索キーワード（組織名・コードで検索）

**レスポンス** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "code": "ORG001",
      "name": "株式会社サンプル",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

#### 3. 組織詳細取得
```http
GET /api/v1/organizations/{org_id}
```

**権限**: 組織メンバーまたはシステム管理者

**レスポンス** (200 OK):
```json
{
  "id": 1,
  "code": "ORG001",
  "name": "株式会社サンプル",
  "name_kana": "カブシキガイシャサンプル",
  "postal_code": "100-0001",
  "address": "東京都千代田区丸の内1-1-1",
  "phone": "03-1234-5678",
  "email": "info@sample.com",
  "website": "https://sample.com",
  "fiscal_year_start": 4,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": 1,
  "updated_by": null
}
```

#### 4. 組織更新
```http
PUT /api/v1/organizations/{org_id}
```

**権限**: 組織管理者またはシステム管理者

**リクエスト**:
```json
{
  "name": "株式会社サンプル（更新）",
  "email": "new-info@sample.com"
}
```

**レスポンス** (200 OK):
```json
{
  "id": 1,
  "code": "ORG001",
  "name": "株式会社サンプル（更新）",
  "email": "new-info@sample.com",
  "updated_at": "2024-01-02T00:00:00Z",
  "updated_by": 2
}
```

#### 5. 組織削除（論理削除）
```http
DELETE /api/v1/organizations/{org_id}
```

**権限**: システム管理者のみ

**レスポンス** (204 No Content)

### エラーレスポンス

#### 認証エラー (401 Unauthorized)
```json
{
  "detail": "認証が必要です"
}
```

#### 権限エラー (403 Forbidden)
```json
{
  "detail": "システム管理者権限が必要です"
}
```

#### 組織が見つからない (404 Not Found)
```json
{
  "detail": "組織が見つかりません"
}
```

#### バリデーションエラー (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "loc": ["body", "code"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### セキュリティ考慮事項

1. **マルチテナント分離**: 組織データは厳密に分離され、他組織のデータにアクセス不可
2. **Role-Based Access Control**: ロールに基づく細かな権限制御
3. **監査ログ**: 全ての操作が監査ログに記録
4. **入力値検証**: SQLインジェクション等の攻撃を防止

### 使用例

#### 組織作成とメンバー追加の例
```bash
# 1. 組織作成（システム管理者）
curl -X POST /api/v1/organizations \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "NEWORG",
    "name": "新組織"
  }'

# 2. ユーザーを組織に追加（別途 User-Role API使用）
curl -X POST /api/v1/user-roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role_id": 2,
    "organization_id": 1
  }'
```