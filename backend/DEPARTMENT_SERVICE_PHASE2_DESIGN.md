# Department Service Phase 2 - 設計仕様書

## 🏗️ **システム設計概要**

### **プロジェクト名**
Department Service Phase 2 - 階層構造拡張とTask Management統合

### **設計原則**
1. **階層型組織構造**: 無制限の深さをサポート
2. **高性能クエリ**: マテリアライズドパスパターンの採用
3. **セキュリティ第一**: 権限継承とアクセス制御
4. **スケーラビリティ**: 大規模組織（10,000+ 部門）対応
5. **統合性**: 既存システムとのシームレス統合

## 🎯 **機能要件**

### **1. 階層構造管理**

#### **1.1 部門階層の表現**
```python
class Department(BaseModel):
    # 既存フィールド
    id: int
    name: str
    parent_id: Optional[int]
    
    # 新規階層フィールド
    path: str              # "1.5.12.45" (マテリアライズドパス)
    depth: int             # 0 (root), 1, 2, 3... (階層の深さ)
    leaf_count: int        # 配下の部門数
    is_leaf: bool          # 末端部門フラグ
```

#### **1.2 階層操作**
- **部門移動**: 循環参照チェック付き
- **部門削除**: カスケード削除または制約チェック
- **部門複製**: 階層構造を保持した複製
- **部門統合**: 複数部門の統合処理

#### **1.3 階層クエリ**
- **祖先取得**: 指定部門の全祖先を取得
- **子孫取得**: 指定部門の全子孫を取得
- **兄弟取得**: 同レベルの部門一覧
- **階層ツリー**: 組織全体のツリー構造

### **2. 権限継承システム**

#### **2.1 権限モデル**
```python
class DepartmentPermission(BaseModel):
    department_id: int
    permission_code: str
    inherited_from: Optional[int]  # 継承元部門ID
    is_explicit: bool             # 明示的権限フラグ
    inheritance_level: int        # 継承階層レベル
```

#### **2.2 継承ルール**
- **デフォルト継承**: 上位部門の権限を自動継承
- **明示的付与**: 特定部門への直接権限付与
- **継承停止**: 指定部門で継承チェーンを停止
- **権限オーバーライド**: 下位部門での権限上書き

#### **2.3 権限チェック**
- **階層権限チェック**: 継承チェーンを辿った権限確認
- **スコープ制限**: 部門範囲内での権限制限
- **役割ベース**: ユーザーの役割に応じた権限適用
- **時間制限**: 時限付き権限の管理

### **3. Task Management統合**

#### **3.1 部門レベルタスク管理**
```python
class DepartmentTask(BaseModel):
    task_id: int
    department_id: int
    assignment_type: str    # "department", "inherited", "shared"
    visibility_scope: str   # "private", "department", "public"
    delegation_level: int   # 委任レベル
```

#### **3.2 タスク権限継承**
- **部門タスク表示**: 部門メンバーが閲覧可能
- **継承タスク管理**: 上位部門からの継承タスク
- **委任タスク**: 下位部門への委任処理
- **協力タスク**: 部門間協力タスク

#### **3.3 タスク組織化**
- **部門タスクボード**: 部門専用のタスクボード
- **階層タスクビュー**: 階層構造でのタスク表示
- **レポート生成**: 部門別タスクレポート
- **進捗追跡**: 部門レベルでの進捗管理

### **4. 部門間連携機能**

#### **4.1 連携協定**
```python
class DepartmentCollaboration(BaseModel):
    department_a_id: int
    department_b_id: int
    collaboration_type: str    # "project", "resource", "information"
    status: str               # "active", "pending", "suspended"
    permissions: List[str]    # 共有権限リスト
    effective_period: DateRange
```

#### **4.2 連携タイプ**
- **プロジェクト連携**: 共同プロジェクトの管理
- **リソース共有**: 人材・設備の共有
- **情報共有**: データとレポートの共有
- **承認ワークフロー**: 部門間承認プロセス

#### **4.3 連携管理**
- **協定締結**: 部門間の協定締結プロセス
- **権限管理**: 連携に伴う権限の管理
- **監査証跡**: 連携活動の記録
- **終了処理**: 連携の終了と後処理

## 🔧 **技術設計**

### **1. データベース設計**

#### **1.1 部門テーブル拡張**
```sql
ALTER TABLE departments ADD COLUMN path VARCHAR(500) NOT NULL DEFAULT '';
ALTER TABLE departments ADD COLUMN depth INTEGER NOT NULL DEFAULT 0;
ALTER TABLE departments ADD COLUMN leaf_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE departments ADD COLUMN is_leaf BOOLEAN NOT NULL DEFAULT true;

-- インデックス作成
CREATE INDEX idx_departments_path ON departments(path);
CREATE INDEX idx_departments_depth ON departments(depth);
CREATE INDEX idx_departments_parent_id ON departments(parent_id);
```

#### **1.2 権限継承テーブル**
```sql
CREATE TABLE department_permissions (
    id SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL,
    permission_code VARCHAR(100) NOT NULL,
    inherited_from INTEGER,
    is_explicit BOOLEAN NOT NULL DEFAULT false,
    inheritance_level INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (inherited_from) REFERENCES departments(id),
    UNIQUE(department_id, permission_code)
);
```

#### **1.3 部門連携テーブル**
```sql
CREATE TABLE department_collaborations (
    id SERIAL PRIMARY KEY,
    department_a_id INTEGER NOT NULL,
    department_b_id INTEGER NOT NULL,
    collaboration_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    permissions JSONB,
    effective_from TIMESTAMP,
    effective_until TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (department_a_id) REFERENCES departments(id),
    FOREIGN KEY (department_b_id) REFERENCES departments(id),
    UNIQUE(department_a_id, department_b_id, collaboration_type)
);
```

### **2. サービス層設計**

#### **2.1 DepartmentHierarchyService**
```python
class DepartmentHierarchyService:
    def move_department(self, dept_id: int, new_parent_id: int) -> bool:
        """部門の移動（循環参照チェック付き）"""
        
    def get_hierarchy_tree(self, root_id: int = None) -> Dict:
        """階層ツリーの取得"""
        
    def get_descendants(self, dept_id: int, max_depth: int = None) -> List[Department]:
        """子孫部門の取得"""
        
    def get_ancestors(self, dept_id: int) -> List[Department]:
        """祖先部門の取得"""
        
    def validate_hierarchy(self, dept_id: int) -> bool:
        """階層構造の整合性チェック"""
```

#### **2.2 DepartmentPermissionService**
```python
class DepartmentPermissionService:
    def check_permission(self, user_id: int, dept_id: int, permission: str) -> bool:
        """権限チェック（継承含む）"""
        
    def get_effective_permissions(self, user_id: int, dept_id: int) -> List[str]:
        """実効権限の取得"""
        
    def grant_permission(self, dept_id: int, permission: str, explicit: bool = True) -> bool:
        """権限の付与"""
        
    def revoke_permission(self, dept_id: int, permission: str) -> bool:
        """権限の取り消し"""
        
    def get_inheritance_chain(self, dept_id: int, permission: str) -> List[int]:
        """継承チェーンの取得"""
```

#### **2.3 DepartmentTaskService**
```python
class DepartmentTaskService:
    def get_department_tasks(self, dept_id: int, include_inherited: bool = True) -> List[Task]:
        """部門タスクの取得"""
        
    def assign_task_to_department(self, task_id: int, dept_id: int) -> bool:
        """タスクの部門割り当て"""
        
    def delegate_task(self, task_id: int, from_dept: int, to_dept: int) -> bool:
        """タスクの委任"""
        
    def get_task_hierarchy(self, task_id: int) -> Dict:
        """タスクの階層情報"""
        
    def generate_department_report(self, dept_id: int, period: DateRange) -> Dict:
        """部門レポートの生成"""
```

### **3. API設計**

#### **3.1 階層管理API**
```python
# 部門階層取得
GET /api/v1/departments/{dept_id}/hierarchy
GET /api/v1/departments/{dept_id}/ancestors
GET /api/v1/departments/{dept_id}/descendants

# 部門操作
POST /api/v1/departments/{dept_id}/move
POST /api/v1/departments/{dept_id}/copy
DELETE /api/v1/departments/{dept_id}/cascade
```

#### **3.2 権限管理API**
```python
# 権限チェック
GET /api/v1/departments/{dept_id}/permissions
POST /api/v1/departments/{dept_id}/permissions/check

# 権限操作
POST /api/v1/departments/{dept_id}/permissions/grant
DELETE /api/v1/departments/{dept_id}/permissions/revoke
GET /api/v1/departments/{dept_id}/permissions/inheritance
```

#### **3.3 タスク統合API**
```python
# 部門タスク管理
GET /api/v1/departments/{dept_id}/tasks
POST /api/v1/departments/{dept_id}/tasks/assign
POST /api/v1/departments/{dept_id}/tasks/delegate

# レポート
GET /api/v1/departments/{dept_id}/reports/tasks
GET /api/v1/departments/{dept_id}/reports/performance
```

## 📊 **パフォーマンス設計**

### **1. クエリ最適化**

#### **1.1 階層クエリの最適化**
```sql
-- 子孫取得（マテリアライズドパス使用）
SELECT * FROM departments 
WHERE path LIKE '1.5.12.%' 
ORDER BY depth, display_order;

-- 祖先取得（パス分割）
WITH RECURSIVE ancestors AS (
    SELECT id, parent_id, path, depth FROM departments WHERE id = ?
    UNION ALL
    SELECT d.id, d.parent_id, d.path, d.depth 
    FROM departments d 
    JOIN ancestors a ON d.id = a.parent_id
)
SELECT * FROM ancestors ORDER BY depth;
```

#### **1.2 権限チェックの最適化**
```python
# 権限キャッシュ戦略
class PermissionCache:
    def __init__(self):
        self.cache = {}
        self.ttl = 300  # 5分
    
    def get_cached_permissions(self, user_id: int, dept_id: int) -> Optional[List[str]]:
        """キャッシュされた権限の取得"""
        
    def cache_permissions(self, user_id: int, dept_id: int, permissions: List[str]):
        """権限のキャッシュ"""
```

### **2. 性能目標**

#### **2.1 応答時間**
- 階層クエリ: < 100ms (1,000部門)
- 権限チェック: < 50ms (キャッシュ有効時)
- タスク取得: < 200ms (部門あたり1,000タスク)

#### **2.2 スループット**
- 同時ユーザー: 1,000+
- 部門操作: 100 ops/sec
- 権限チェック: 10,000 ops/sec

#### **2.3 スケーラビリティ**
- 最大部門数: 10,000+
- 階層深度: 20レベル
- 権限数: 1,000+

## 🔒 **セキュリティ設計**

### **1. 権限モデル**

#### **1.1 階層権限**
- **継承権限**: 上位部門からの自動継承
- **明示権限**: 特定部門への直接付与
- **拒否権限**: 特定権限の明示的拒否

#### **1.2 アクセス制御**
- **部門スコープ**: 部門範囲内でのアクセス制限
- **役割ベース**: ユーザー役割に応じた権限
- **時間制限**: 時限付きアクセス権限

### **2. 監査とログ**

#### **2.1 変更追跡**
- 階層構造の変更履歴
- 権限変更の記録
- 部門間連携の履歴

#### **2.2 セキュリティ監査**
- 不正アクセス検知
- 権限昇格の監視
- 異常な部門操作の検知

## 🧪 **テスト戦略**

### **1. 単体テスト**

#### **1.1 階層操作テスト**
```python
class TestDepartmentHierarchy:
    def test_move_department_success(self):
        """部門移動の成功テスト"""
        
    def test_move_department_circular_reference(self):
        """循環参照の防止テスト"""
        
    def test_get_hierarchy_tree(self):
        """階層ツリー取得テスト"""
```

#### **1.2 権限継承テスト**
```python
class TestPermissionInheritance:
    def test_inherit_parent_permissions(self):
        """親部門権限継承テスト"""
        
    def test_override_inherited_permissions(self):
        """継承権限オーバーライドテスト"""
        
    def test_permission_check_with_inheritance(self):
        """継承を含む権限チェックテスト"""
```

### **2. 統合テスト**

#### **2.1 Task Management統合**
```python
class TestTaskIntegration:
    def test_department_task_assignment(self):
        """部門タスク割り当てテスト"""
        
    def test_task_permission_inheritance(self):
        """タスク権限継承テスト"""
        
    def test_cross_department_collaboration(self):
        """部門間連携テスト"""
```

### **3. パフォーマンステスト**

#### **3.1 階層クエリ性能**
```python
class TestHierarchyPerformance:
    def test_large_hierarchy_query(self):
        """大規模階層クエリテスト"""
        
    def test_deep_hierarchy_performance(self):
        """深い階層での性能テスト"""
        
    def test_concurrent_hierarchy_operations(self):
        """並行階層操作テスト"""
```

## 📅 **実装スケジュール**

### **Phase 2.1: 基盤実装** (Day 1)
- [ ] 階層構造の基盤実装
- [ ] マテリアライズドパスの実装
- [ ] 基本階層操作の実装
- [ ] 単体テストの作成

### **Phase 2.2: 権限システム** (Day 2)
- [ ] 権限継承システムの実装
- [ ] 権限チェック機能の実装
- [ ] キャッシュ機能の実装
- [ ] 権限テストの作成

### **Phase 2.3: Task統合** (Day 3)
- [ ] Task Management統合
- [ ] 部門タスク管理機能
- [ ] レポート機能の実装
- [ ] 統合テストの作成

### **Phase 2.4: 連携機能** (Day 4)
- [ ] 部門間連携機能
- [ ] 承認ワークフロー
- [ ] 監査機能の強化
- [ ] 総合テストの実施

## 🎯 **成功指標**

### **機能指標**
- ✅ 階層操作の成功率 > 99%
- ✅ 権限チェックの正確率 > 99.9%
- ✅ Task統合の完全性 > 99%
- ✅ 連携機能の可用性 > 99%

### **性能指標**
- ✅ 平均応答時間 < 100ms
- ✅ 99パーセンタイル < 500ms
- ✅ エラー率 < 0.1%
- ✅ スループット > 1,000 req/sec

### **品質指標**
- ✅ テストカバレッジ > 90%
- ✅ コード品質スコア > 8.0
- ✅ セキュリティ脆弱性 = 0
- ✅ パフォーマンス回帰 = 0

---

**作成日**: 2024-07-09  
**バージョン**: 2.0  
**ステータス**: 設計完了  
**承認**: 開発チーム