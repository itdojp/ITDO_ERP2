# マージコンフリクト直接解決支援 - 2025-07-16 15:50

## 🚨 緊急解決支援: permission.py統合版作成

### 📋 最高難度ファイルの直接解決

CC03への分析を待つ間、最も困難な`backend/app/services/permission.py`の競合を直接解決します。

```python
# backend/app/services/permission.py - 統合版
"""
Permission Service
権限管理サービスの統合実装
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.repositories.base import BaseRepository


class PermissionService:
    """権限管理サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.permission_repo = BaseRepository(Permission, db)
    
    async def create_permission(
        self, 
        permission_data: PermissionCreate
    ) -> Permission:
        """権限を作成"""
        permission = Permission(**permission_data.model_dump())
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def get_permission_by_id(self, permission_id: int) -> Optional[Permission]:
        """IDで権限を取得"""
        return await self.permission_repo.get_by_id(permission_id)
    
    async def get_permissions_by_role(self, role_id: int) -> List[Permission]:
        """ロールIDで権限一覧を取得"""
        query = select(Permission).join(
            Role.permissions
        ).where(Role.id == role_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_permissions(self, user_id: int) -> List[Permission]:
        """ユーザーが持つ全権限を取得"""
        query = select(Permission).join(
            Role.permissions
        ).join(
            User.roles
        ).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def check_user_permission(
        self, 
        user_id: int, 
        permission_name: str
    ) -> bool:
        """ユーザーが特定の権限を持つかチェック"""
        query = select(Permission).join(
            Role.permissions
        ).join(
            User.roles
        ).where(
            and_(
                User.id == user_id,
                Permission.name == permission_name
            )
        )
        result = await self.db.execute(query)
        permission = result.scalar_one_or_none()
        return permission is not None
    
    async def update_permission(
        self, 
        permission_id: int, 
        permission_data: PermissionUpdate
    ) -> Optional[Permission]:
        """権限を更新"""
        permission = await self.get_permission_by_id(permission_id)
        if not permission:
            return None
        
        for field, value in permission_data.model_dump(exclude_unset=True).items():
            setattr(permission, field, value)
        
        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def delete_permission(self, permission_id: int) -> bool:
        """権限を削除"""
        permission = await self.get_permission_by_id(permission_id)
        if not permission:
            return False
        
        await self.db.delete(permission)
        await self.db.commit()
        return True
    
    async def get_all_permissions(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Permission]:
        """全権限を取得"""
        return await self.permission_repo.get_multi(skip=skip, limit=limit)
```

---

## 🔧 router.py競合解決ガイド

### 現在の競合内容分析
```python
# backend/app/api/v1/router.py - 競合解決ガイド

"""
競合箇所の分析:
1. APIルーター登録の重複
2. インポート文の競合
3. 新機能エンドポイントの統合

解決方針:
- 両ブランチの機能を統合
- 重複の排除
- アルファベット順の整理
"""

# 統合版のインポート文（アルファベット順）
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.audit import router as audit_router
from app.api.v1.departments import router as departments_router
from app.api.v1.multi_tenant import router as multi_tenant_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.permission_inheritance import router as permission_inheritance_router
from app.api.v1.role_permission_ui import router as role_permission_ui_router
from app.api.v1.roles import router as roles_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.user_preferences import router as user_preferences_router
from app.api.v1.user_privacy import router as user_privacy_router
from app.api.v1.user_profile import router as user_profile_router
from app.api.v1.users import router as users_router
from app.api.v1.users_extended import router as users_extended_router

api_router = APIRouter()

# ルーター登録（機能別にグループ化）
# 認証・ユーザー管理
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(users_extended_router, prefix="/users", tags=["users-extended"])
api_router.include_router(user_preferences_router, prefix="/users", tags=["user-preferences"])
api_router.include_router(user_privacy_router, prefix="/users", tags=["user-privacy"])
api_router.include_router(user_profile_router, prefix="/users", tags=["user-profile"])

# 組織・部門管理
api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
api_router.include_router(departments_router, prefix="/departments", tags=["departments"])
api_router.include_router(multi_tenant_router, prefix="/tenants", tags=["multi-tenant"])

# 権限・ロール管理
api_router.include_router(roles_router, prefix="/roles", tags=["roles"])
api_router.include_router(permission_inheritance_router, prefix="/permissions", tags=["permissions"])
api_router.include_router(role_permission_ui_router, prefix="/role-permissions", tags=["role-permissions"])

# タスク・プロジェクト管理
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])

# 監査・ログ
api_router.include_router(audit_router, prefix="/audit", tags=["audit"])
```

---

## 🛠️ 段階的競合解決手順書

### Step 1: 高難度ファイル（CC03実行推奨）
```bash
# 1. permission.py - 上記統合版を使用
git add backend/app/services/permission.py

# 2. router.py - 上記ガイドに従って手動統合
# 競合マーカーを除去し、統合版に置換
git add backend/app/api/v1/router.py
```

### Step 2: 中難度ファイル（CC01・CC03協調）
```bash
# 3. user.py - ユーザーモデルの統合
# インポート文を統合し、フィールド定義を両方含める
git add backend/app/models/user.py

# 4. organization.py系 - 機能統合
# 両ブランチの機能を統合実装
git add backend/app/services/organization.py
git add backend/app/repositories/organization.py

# 5. conftest.py - テスト設定統合
# 両方のテスト設定を統合
git add backend/tests/conftest.py
```

### Step 3: 低難度ファイル（CC01実行可能）
```bash
# 6-11. Factory系ファイル - 機械的統合
# インポートとファクトリ定義の統合
git add backend/tests/factories/department.py
git add backend/tests/factories/organization.py
git add backend/tests/factories/user.py
git add backend/app/models/user_session.py
git add backend/tests/unit/test_models_user.py
```

### Step 4: 最終確認・テスト
```bash
# 構文チェック
cd backend && uv run python -m py_compile app/services/permission.py
cd backend && uv run python -m py_compile app/api/v1/router.py

# 型チェック
cd backend && uv run mypy app/services/permission.py
cd backend && uv run mypy app/api/v1/router.py

# インポートテスト
cd backend && python -c "from app.services.permission import PermissionService; print('OK')"
cd backend && python -c "from app.api.v1.router import api_router; print('OK')"

# 最終コミット
git commit -m "resolve: Fix merge conflicts in 11 files

- Integrate permission.py from both branches
- Merge router.py with all endpoints
- Unify model and service implementations
- Consolidate test configurations

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## ⚡ CC03への具体的指示

### マージコンフリクト解決専門ミッション
```yaml
CC03の専門的役割:
  1. 残り9ファイルの詳細分析
  2. 段階的解決戦略の立案
  3. CC01への具体的指導
  4. 品質確認・検証

期待される成果:
  - 6時間以内: 全ファイル分析完了
  - 12時間以内: 解決戦略提供
  - 24時間以内: 完全解決達成
  - CC03リーダーシップ確立

技術的権限:
  - 解決方針の最終決定権
  - CC01への技術指導権
  - 品質基準の設定権
  - 緊急判断権
```

### 協調作業フロー
```yaml
CC03 → CC01の指導フロー:
  1. CC03: ファイル分析・解決戦略立案
  2. CC01: CC03指示に基づく実装
  3. CC03: 各段階での品質確認
  4. CC01: 問題発生時はCC03に相談
  5. CC03: 最終検証・完了確認

期待される協調成果:
  - 効率的な問題解決
  - 高品質な統合実装
  - 技術的学習・成長
  - 将来の協調モデル確立
```

---

## 🚀 緊急時代替案

### Plan B: ブランチリセット戦略
```bash
# 現在の変更を一時保存
git stash push -m "auth-edge-case-tests changes"

# mainブランチに戻る
git checkout main
git pull origin main

# 新ブランチで再開
git checkout -b feature/merge-conflict-resolution
git stash pop

# 段階的に機能を追加
# 競合を完全回避した実装
```

### Plan C: 外部専門支援
```yaml
条件: 24時間以内に解決困難な場合
対応: Git・マージ専門家の緊急招聘
期待: 6時間以内の完全解決
効果: CC01・CC03の学習機会
```

---

## 📊 解決完了の成功指標

### 技術的成功
```yaml
24時間以内:
  ✅ 11ファイル全競合解決
  ✅ CI/CD成功確認
  ✅ 全機能動作確認
  ✅ Phase 6実装準備完了

品質確認:
  ✅ 構文エラーなし
  ✅ 型チェック通過
  ✅ インポート循環なし
  ✅ テスト実行成功
```

### チーム成功
```yaml
CC03成果:
  ✅ 技術リーダーシップ発揮
  ✅ 複雑問題の解決実現
  ✅ CC01との効果的協調
  ✅ 将来の予防策提案

CC01成果:
  ✅ 協調作業での成功
  ✅ 技術的学習・成長
  ✅ 品質維持の実現
  ✅ 持続可能な作業ペース
```

---

**作成日**: 2025-07-16 15:50
**目的**: マージコンフリクト緊急解決支援
**戦略**: 直接解決支援 + CC03専門指導
**目標**: 24時間以内の完全解決