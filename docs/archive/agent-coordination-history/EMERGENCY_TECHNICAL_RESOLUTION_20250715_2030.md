# 緊急技術問題解決指示 - 2025-07-15 20:30

## 🚨 現在の緊急状況

### エージェント状況
- **CC01**: PR #98完了後、応答なし（1時間経過）
- **CC02**: 緊急活性化プロトコルへの応答なし
- **CC03**: 復活プロトコルへの応答なし

### 技術的緊急事態
- **PR #124**: 12ファイルのマージ競合、多数のテスト失敗
- **Backend test**: SQLAlchemyマッパーエラー
- **TypeScript**: 型チェック失敗

## 🔧 PR #124 緊急修正手順

### 1. マージ競合の解決（最優先）

```bash
cd /mnt/c/work/ITDO_ERP2
git checkout feature/auth-edge-cases
git pull origin main

# 競合ファイルの確認
git status | grep "both modified"

# 各競合ファイルの解決
# backend/app/models/role.py が主要な問題
```

### 2. Backend Model修正

#### Role modelの修正
```python
# backend/app/models/role.py
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, String, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.permission import Permission
    from app.models.user import User

# Roleモデルに必要なリレーション追加
class Role(Base):
    __tablename__ = "roles"
    
    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String, nullable=False)
    organization_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # 必須リレーション
    organization: Mapped["Organization"] = relationship("Organization", back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary="role_permissions")
    users: Mapped[List["User"]] = relationship("User", secondary="user_roles", back_populates="roles")
```

### 3. Import修正

```bash
# 全ファイルのimport修正
find backend -name "*.py" -exec grep -l "from typing import" {} \; | while read file; do
    # Optional, List, Dict, Any のimportを確認・追加
    echo "Checking imports in $file"
done

# 具体的な修正例
# backend/app/api/v1/endpoints/auth.py
# from typing import Optional を追加
```

### 4. Test Database Isolation修正

```bash
# backend/tests/conftest.py の確認
cd backend
cat tests/conftest.py

# テスト用データベース設定の修正
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
```

## 🤖 エージェント復活手順

### CC01 復活確認
```bash
echo "🔄 CC01 Health Check - $(date)"
echo "Previous achievement: PR #98 (97% success rate)"
echo "Current task: PR #124 technical resolution"
echo "Status: Awaiting response"
```

### CC02 簡易起動
```bash
echo "🔄 CC02 Simple Activation - $(date)"
echo "Task: Backend model fixes for PR #124"
echo "Focus: SQLAlchemy relationships"
echo "Duration: 30 minutes"
```

### CC03 技術サポート要請
```bash
echo "🔄 CC03 Technical Support - $(date)"
echo "Task: CI/CD pipeline fixes"
echo "Focus: Test failures resolution"
echo "Priority: Critical"
```

## 📊 修正優先順位

### 1. 即座修正（15分以内）
1. **Import statements**: `Optional`, `List`, `Dict`の追加
2. **Role model**: `organization`リレーションの追加
3. **Merge conflicts**: 12ファイルの競合解決

### 2. テスト修正（30分以内）
1. **Backend tests**: SQLAlchemy関連エラー修正
2. **TypeScript checks**: 型定義の修正
3. **Test isolation**: データベース分離の実装

### 3. CI/CD安定化（45分以内）
1. **GitHub Actions**: ワークフロー修正
2. **Test reliability**: 不安定なテストの修正
3. **Build optimization**: ビルド時間短縮

## 🎯 成功基準

### 技術的成功
- ✅ マージ競合: 0件
- ✅ Backend test: Pass
- ✅ TypeScript check: Pass
- ✅ CI/CD: 30/30 checks passing

### エージェント成功
- ✅ CC01: 応答復活
- ✅ CC02: Backend修正参加
- ✅ CC03: Infrastructure支援

## 🚀 実行指示

### Option A: 人間開発者実行
```bash
# 緊急性を考慮し、人間開発者が直接修正
cd /mnt/c/work/ITDO_ERP2
git checkout feature/auth-edge-cases
# 上記の修正を適用
git add -A
git commit -m "fix: Resolve merge conflicts and test failures for PR #124"
git push
```

### Option B: エージェント復活待機
```bash
# エージェントへの簡潔な指示
echo "PR #124: Import修正とRole model修正のみ実行"
echo "30分以内に完了"
echo "詳細な説明は不要"
```

## 📋 次のステップ

1. **20:45まで**: Import修正完了
2. **21:00まで**: マージ競合解決
3. **21:15まで**: CI/CD全チェック通過
4. **21:30まで**: PR #124マージ準備完了

---
**緊急対応開始**: 2025-07-15 20:30
**目標完了時刻**: 2025-07-15 21:30
**次回評価**: 2025-07-15 21:00