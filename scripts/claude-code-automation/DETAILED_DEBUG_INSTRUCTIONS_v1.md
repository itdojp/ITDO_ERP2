# 🔧 Detailed Debug Instructions v1.0: Backend Test Resolution

## 📅 2025-07-14 10:45 JST - Specific Technical Guidance

### 🎯 Problem Focus: test_get_user_membership_summary

```yaml
症状: backend-testが継続的に失敗
推定原因: SQLAlchemy relationship/query問題
解決期限: 2時間以内
```

## 🔍 Step-by-Step Debug Process

### Step 1: Exact Failure Identification (15 min)
```bash
# 1. 詳細なエラーログ取得
cd backend
uv run pytest tests/integration/api/v1/test_organizations.py::test_get_user_membership_summary -vvs --tb=long > test_error.log 2>&1

# 2. 失敗箇所の特定
grep -A 20 -B 10 "FAILED\|Error\|Exception" test_error.log

# 3. SQLクエリの確認（もしログに含まれる場合）
grep -i "SELECT\|FROM\|JOIN" test_error.log
```

### Step 2: Common SQLAlchemy Issues Check (20 min)
```python
# app/models/user.py の確認ポイント
class User(Base):
    # 1. Relationshipの定義確認
    organization = relationship("Organization", back_populates="users")
    departments = relationship("Department", secondary="user_departments")
    
    # 2. Lazy loading設定
    # lazy='select' vs lazy='joined' vs lazy='subquery'
    
    # 3. 外部キー制約
    organization_id = Column(Integer, ForeignKey("organizations.id"))

# app/api/v1/organizations.py の確認ポイント
def get_user_membership_summary():
    # 1. Query構築方法
    # Bad: db.query(User).filter(User.organization_id == org_id)
    # Good: db.query(User).join(Organization).filter(Organization.id == org_id)
    
    # 2. N+1問題の回避
    # options(joinedload(User.organization))
```

### Step 3: Test Environment Issues (15 min)
```python
# tests/conftest.py の確認
@pytest.fixture
def db():
    # 1. テストDBの初期化確認
    # SQLite vs PostgreSQL の違い
    
    # 2. トランザクション処理
    # rollback() vs commit()
    
    # 3. テストデータの作成順序
    # 外部キー制約を満たす順序で作成

# 特にMulti-tenantの場合
def create_test_data(db):
    # 1. Organization作成
    org = Organization(...)
    db.add(org)
    db.flush()  # IDを取得
    
    # 2. User作成（organization_id設定）
    user = User(organization_id=org.id, ...)
    db.add(user)
    db.commit()
```

## 🛠️ Specific Solutions for Common Problems

### Problem 1: Missing Relationship Definition
```python
# 修正前
class User(Base):
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    # relationshipが定義されていない

# 修正後
class User(Base):
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    organization = relationship("Organization", back_populates="users")
```

### Problem 2: Circular Import Issues
```python
# 修正方法1: TYPE_CHECKINGを使用
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.organization import Organization

class User(Base):
    organization: "Organization" = relationship("Organization", back_populates="users")

# 修正方法2: 文字列で指定
class User(Base):
    organization = relationship("app.models.organization.Organization", back_populates="users")
```

### Problem 3: Query Construction Error
```python
# 修正前（N+1問題あり）
users = db.query(User).filter(User.organization_id == org_id).all()
for user in users:
    print(user.organization.name)  # 各ユーザーで追加クエリ

# 修正後（Eager Loading）
from sqlalchemy.orm import joinedload

users = db.query(User)\
    .options(joinedload(User.organization))\
    .filter(User.organization_id == org_id)\
    .all()
```

### Problem 4: Test Database Compatibility
```python
# SQLite特有の問題対策
if database_url.startswith("sqlite"):
    # Foreign key制約を有効化
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

## 📋 Debug Output Template

### CC01に要求する情報
```yaml
必須情報:
  1. 完全なエラーメッセージ
  2. 失敗しているテストコード（該当部分）
  3. 関連するModel定義
  4. 実行されているSQLクエリ（可能なら）
  5. テストデータの作成方法

フォーマット例:
  ```
  ERROR: test_get_user_membership_summary
  File: tests/integration/api/v1/test_organizations.py:123
  Error: AttributeError: 'User' object has no attribute 'organization'
  
  Test Code:
  def test_get_user_membership_summary(client, db_session, test_user):
      response = client.get(f"/api/v1/organizations/{org_id}/members/summary")
      
  Model Definition:
  class User(Base):
      organization_id = Column(Integer, ForeignKey("organizations.id"))
      # Missing: organization relationship
  ```
```

## 🚀 Quick Fix Checklist

### For CC01 (Primary Debug)
- [ ] エラーログの完全取得
- [ ] Model relationship確認
- [ ] Query構築方法確認
- [ ] Test fixture確認
- [ ] Import循環確認

### For CC03 (Support Debug)
- [ ] CI環境でのログ確認
- [ ] DB接続設定確認
- [ ] 並列テストの影響確認
- [ ] 環境変数の差異確認
- [ ] コンテナ設定確認

## 📊 Success Validation

### ローカル確認
```bash
# 1. 単体テスト実行
uv run pytest tests/integration/api/v1/test_organizations.py::test_get_user_membership_summary -v

# 2. 関連テスト全体
uv run pytest tests/integration/api/v1/test_organizations.py -v

# 3. 統合テスト全体
uv run pytest tests/integration/ -v
```

### CI/CD確認
```yaml
期待結果:
  - backend-test: ✅ PASS
  - Code Quality: ✅ PASS
  - All checks: 30/30 ✅
```

---

**Purpose**: 具体的なデバッグ手順提供
**Target**: CC01（主実装）、CC03（支援）
**Deadline**: 2時間以内での解決
**Key**: 段階的な問題切り分けと具体的な修正例