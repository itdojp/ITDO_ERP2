# Department Service API仕様書

## 概要

Department Service APIは、組織内の部門管理を行うための包括的なRESTful APIです。階層構造、権限管理、タスク統合、部門間コラボレーションなどの機能を提供します。

## 基本情報

- **ベースURL**: `http://localhost:8000/api/v1/departments`
- **認証**: Bearer Token (JWT)
- **Content-Type**: `application/json`

## API エンドポイント

### 1. 部門一覧取得
```
GET /departments
```

#### パラメータ
- `skip`: int = 0 (オフセット)
- `limit`: int = 100 (取得件数)
- `organization_id`: int (組織IDでフィルタ)
- `search`: str (検索クエリ)
- `active_only`: bool = true (アクティブな部門のみ)
- `department_type`: str (部門タイプでフィルタ)

#### レスポンス
```json
{
  "items": [
    {
      "id": 1,
      "code": "IT",
      "name": "IT部門",
      "name_en": "IT Department",
      "organization_id": 1,
      "parent_id": null,
      "is_active": true,
      "department_type": "operational",
      "user_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### 2. 部門詳細取得
```
GET /departments/{department_id}
```

#### レスポンス
```json
{
  "id": 1,
  "code": "IT",
  "name": "IT部門",
  "name_en": "IT Department",
  "description": "情報技術部門",
  "organization_id": 1,
  "parent_id": null,
  "manager_id": 10,
  "is_active": true,
  "department_type": "operational",
  "contact_email": "it@company.com",
  "contact_phone": "03-1234-5678",
  "location": "東京本社 3F",
  "budget": 1000000.0,
  "cost_center": "CC-IT-001",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": 1,
  "updated_by": 1
}
```

### 3. 部門作成
```
POST /departments
```

#### リクエストボディ
```json
{
  "code": "HR",
  "name": "人事部",
  "name_en": "Human Resources",
  "description": "人事管理部門",
  "organization_id": 1,
  "parent_id": null,
  "manager_id": 20,
  "department_type": "support",
  "contact_email": "hr@company.com",
  "contact_phone": "03-1234-5679",
  "location": "東京本社 2F",
  "budget": 500000.0,
  "cost_center": "CC-HR-001"
}
```

### 4. 部門更新
```
PUT /departments/{department_id}
```

#### リクエストボディ
```json
{
  "name": "人事部（更新）",
  "description": "人事管理部門（更新）",
  "manager_id": 25,
  "budget": 600000.0
}
```

### 5. 部門削除
```
DELETE /departments/{department_id}
```

#### レスポンス
```json
{
  "success": true,
  "message": "Department deleted successfully",
  "id": 1
}
```

## 階層管理エンドポイント

### 6. 部門階層ツリー取得
```
GET /departments/organization/{organization_id}/tree
```

#### レスポンス
```json
[
  {
    "id": 1,
    "code": "ROOT",
    "name": "本社",
    "name_en": "Headquarters",
    "is_active": true,
    "level": 0,
    "parent_id": null,
    "manager_id": 1,
    "manager_name": "CEO",
    "user_count": 100,
    "children": [
      {
        "id": 2,
        "code": "IT",
        "name": "IT部門",
        "name_en": "IT Department",
        "is_active": true,
        "level": 1,
        "parent_id": 1,
        "manager_id": 10,
        "manager_name": "CTO",
        "user_count": 15,
        "children": []
      }
    ]
  }
]
```

### 7. 部門サブツリー取得
```
GET /departments/{department_id}/tree
```

#### パラメータ
- `max_depth`: int (最大階層深度)

### 8. 直下の子部門取得
```
GET /departments/{department_id}/children
```

#### パラメータ
- `active_only`: bool = true (アクティブな部門のみ)

### 9. 部門移動
```
POST /departments/{department_id}/move
```

#### リクエストボディ
```json
{
  "new_parent_id": 5
}
```

### 10. 部門権限取得
```
GET /departments/{department_id}/permissions
```

#### パラメータ
- `user_id`: int (特定ユーザーの権限)
- `include_inherited`: bool = true (継承権限を含む)

#### レスポンス
```json
{
  "direct_permissions": ["departments.view", "departments.edit"],
  "inherited_permissions": ["organization.view"],
  "effective_permissions": ["departments.view", "departments.edit", "organization.view"],
  "inheritance_chain": [
    {"id": 1, "name": "IT部門", "depth": 0},
    {"id": 2, "name": "本社", "depth": 1}
  ]
}
```

## タスク統合エンドポイント

### 11. 部門タスク一覧取得
```
GET /departments/{department_id}/tasks
```

#### パラメータ
- `include_inherited`: bool = true (継承タスクを含む)
- `include_delegated`: bool = true (委譲タスクを含む)
- `status`: List[str] (ステータスフィルタ)
- `priority`: List[str] (優先度フィルタ)

#### レスポンス
```json
[
  {
    "id": 1,
    "title": "システム開発",
    "description": "新システムの開発",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2024-12-31T23:59:59Z",
    "project_id": 1,
    "assignee_id": 10,
    "reporter_id": 5,
    "assignment_info": {
      "assignment_type": "department",
      "visibility_scope": "department",
      "assigned_at": "2024-01-01T00:00:00Z",
      "delegated_from": null
    }
  }
]
```

### 12. タスク部門割り当て
```
POST /departments/{department_id}/tasks/{task_id}
```

#### リクエストボディ
```json
{
  "assignment_type": "department",
  "visibility_scope": "department",
  "notes": "部門へのタスク割り当て"
}
```

### 13. タスク委譲
```
POST /departments/{department_id}/tasks/{task_id}/delegate
```

#### リクエストボディ
```json
{
  "to_department_id": 5,
  "notes": "専門的な対応のため委譲"
}
```

### 14. タスク割り当て解除
```
DELETE /departments/{department_id}/tasks/{task_id}
```

### 15. 部門タスク統計
```
GET /departments/{department_id}/task-statistics
```

#### レスポンス
```json
{
  "total_tasks": 25,
  "by_status": {
    "pending": 5,
    "in_progress": 10,
    "completed": 8,
    "cancelled": 2
  },
  "by_priority": {
    "high": 8,
    "medium": 12,
    "low": 5
  },
  "overdue_tasks": 3,
  "completion_rate": 0.32,
  "average_completion_time": 7.5
}
```

## 追加機能エンドポイント

### 16. 部門並び順更新
```
PUT /departments/reorder
```

#### リクエストボディ
```json
{
  "department_ids": [1, 3, 2, 4]
}
```

### 17. 部門ユーザー一覧
```
GET /departments/{department_id}/users
```

#### パラメータ
- `include_sub_departments`: bool = false (サブ部門ユーザーを含む)

## エラーレスポンス

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters",
  "code": "INVALID_REQUEST"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required",
  "code": "UNAUTHORIZED"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions",
  "code": "PERMISSION_DENIED"
}
```

### 404 Not Found
```json
{
  "detail": "Department not found",
  "code": "NOT_FOUND"
}
```

### 409 Conflict
```json
{
  "detail": "Department code already exists",
  "code": "DUPLICATE_CODE"
}
```

## 業務ロジック

### 階層管理
- 最大階層深度: 10レベル
- 循環参照の検出と防止
- 親部門削除時の子部門の昇格オプション

### 権限継承
- 上位階層からの権限継承
- 継承の中断設定
- 効果的権限の計算

### タスク統合
- 部門レベルでのタスク管理
- 継承タスクの自動配布
- 部門間でのタスク委譲

### コラボレーション
- 部門間協力協定
- タスク共有とリソース共有
- 協力履歴の管理

## 使用例

### 1. 新しい部門の作成
```bash
curl -X POST http://localhost:8000/api/v1/departments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "MARKETING",
    "name": "マーケティング部",
    "name_en": "Marketing Department",
    "organization_id": 1,
    "department_type": "operational"
  }'
```

### 2. 部門階層の取得
```bash
curl -X GET http://localhost:8000/api/v1/departments/organization/1/tree \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. タスクの部門割り当て
```bash
curl -X POST http://localhost:8000/api/v1/departments/1/tasks/5 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_type": "department",
    "visibility_scope": "organization",
    "notes": "重要プロジェクトのため組織全体で可視化"
  }'
```

### 4. 部門統計の取得
```bash
curl -X GET http://localhost:8000/api/v1/departments/1/task-statistics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 注意事項

1. **認証**: すべてのエンドポイントは認証が必要です
2. **権限**: 操作に応じた適切な権限が必要です
3. **組織隔離**: 部門は組織レベルで隔離されています
4. **ソフト削除**: 削除は論理削除で実行されます
5. **監査ログ**: すべての変更は監査ログに記録されます

## セキュリティ考慮事項

- 組織間でのデータ隔離
- 階層権限による細かいアクセス制御
- 機密情報の適切な保護
- 操作履歴の完全な記録

## パフォーマンス最適化

- 階層クエリの最適化
- 大量データに対する効率的な検索
- キャッシュを活用した高速レスポンス
- 適切なインデックス設計

---

**更新日**: 2024年12月
**バージョン**: 2.0.0
**作成者**: Department Service Team