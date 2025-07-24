# PR #157 Department Model コンフリクト解決支援 - 2025-07-16 16:35

## 🔧 CC03への具体的解決手順

### 📋 コンフリクトの詳細分析手順

```bash
# 1. PR #157の状態確認
gh pr view 157

# 2. ブランチをチェックアウト
git fetch origin
git checkout -b pr-157-fix origin/pr-157

# 3. mainブランチとの差分確認
git fetch origin main
git diff origin/main...HEAD -- backend/app/models/department.py

# 4. コンフリクト詳細確認
git merge origin/main
# または
git rebase origin/main
```

### 🎯 Department Model統合戦略

```python
# backend/app/models/department.py - 統合版案

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User

class Department(BaseModel):
    """部門モデル - 階層構造対応版"""
    
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_department_org_code"),
    )
    
    # 基本フィールド
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # 階層構造フィールド（一時的にコメントアウトまたは条件付き実装）
    # PR #96との競合を避けるため、段階的に実装
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # 階層パス（後続実装用にプレースホルダー）
    # path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # depth: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    # 組織との関連
    organization_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # リレーションシップ
    organization: Mapped["Organization"] = relationship(
        back_populates="departments"
    )
    
    # 階層構造のリレーションシップ
    parent: Mapped[Optional["Department"]] = relationship(
        remote_side="Department.id",
        backref="children"
    )
    
    # ユーザーとの関連
    users: Mapped[List["User"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    @property
    def full_path(self) -> str:
        """部門の完全パスを返す（階層構造対応）"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
```

### 🛠️ 段階的解決アプローチ

#### Step 1: 最小限の統合（推奨）
```python
# 両PRで共通する基本機能のみ統合
# path, depthフィールドは一時的に除外
# parent_id による階層構造は維持
```

#### Step 2: マイグレーション調整
```python
# backend/alembic/versions/XXX_department_hierarchy.py
def upgrade():
    # 基本的な階層構造のみ追加
    op.add_column('departments', 
        sa.Column('parent_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_department_parent',
        'departments', 'departments',
        ['parent_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    op.drop_constraint('fk_department_parent', 'departments')
    op.drop_column('departments', 'parent_id')
```

#### Step 3: テスト確認
```bash
# モデルテスト実行
cd backend && uv run pytest tests/unit/models/test_department.py -v

# 統合テスト実行
cd backend && uv run pytest tests/integration/api/v1/test_departments.py -v

# 型チェック
cd backend && uv run mypy app/models/department.py --strict
```

### 📊 PR #96 との調整戦略

```yaml
競合回避策:
  1. 共通機能の統合:
     - 基本的なCRUD機能
     - organization_id関連
     - 基本的なバリデーション
  
  2. 段階的実装:
     Phase 1: 基本階層構造（parent_id）
     Phase 2: パス管理（path, depth）
     Phase 3: 高度な階層機能
  
  3. インターフェース統一:
     - API レスポンス形式の統一
     - スキーマ定義の調整
     - エラーハンドリング統一
```

### 🚀 CC03への実行指示

```yaml
優先順位:
  1. コンフリクトファイルの特定
  2. 両ブランチの意図理解
  3. 最小限統合版の作成
  4. テスト実行・確認
  5. PR更新・レビュー依頼

期待時間: 2-3時間

成功基準:
  - コンフリクト解消
  - 全テスト合格
  - CI/CD グリーン
  - 両機能の共存
```

### 💡 トラブルシューティング

```bash
# マージコンフリクトが複雑な場合
git checkout --ours backend/app/models/department.py  # 現在のブランチ優先
git checkout --theirs backend/app/models/department.py # mainブランチ優先

# 手動マージ後の確認
git add backend/app/models/department.py
git status
git diff --cached

# コミット前の最終確認
cd backend && uv run python -m py_compile app/models/department.py
```

---

## 🔍 PR #96 CI実行問題の調査手順（CC02用）

### 診断コマンド
```bash
# PRの詳細情報取得
gh pr view 96 --json state,mergeable,checks

# ワークフローの状態確認
gh run list --workflow=ci.yml --limit=10

# 手動でのCI実行試行
gh workflow run ci.yml --ref feature/organization-management

# ローカルでのテスト実行
git checkout feature/organization-management
cd backend && uv run pytest -v
cd frontend && npm test
```

### 代替CI戦略
```yaml
Option 1: PR再作成
  - 現在のPRをクローズ
  - 小規模PRに分割
  - 段階的マージ

Option 2: 手動検証
  - ローカルで全テスト実行
  - 結果をPRコメントに記載
  - レビュアーによる確認

Option 3: Force Push
  - ブランチをrebase
  - force pushで更新
  - CI再トリガー試行
```

---

**緊急度**: 高（PR #157）、中（PR #96）
**推奨対応者**: CC03（PR #157）、CC02（PR #96）
**期待完了時間**: 6時間以内