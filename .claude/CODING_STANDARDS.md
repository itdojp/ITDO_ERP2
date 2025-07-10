# コーディング規約

## 基本原則

1. **安全第一**: テストなしでコードを書かない
2. **型安全**: 型定義を必須とし、any型は原則禁止
3. **一貫性**: 既存のパターンに従う
4. **可読性**: 明確で理解しやすいコードを書く
5. **保守性**: 将来の変更に対応しやすい設計

## Python（Backend）規約

### 基本設定
```python
# 必須インポート
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
```

### 命名規則
- **関数・変数**: snake_case
- **クラス**: PascalCase
- **定数**: UPPER_SNAKE_CASE
- **プライベート**: _leading_underscore

### 型定義
```python
# ✅ 良い例
def get_user(user_id: int) -> Optional[User]:
    pass

def process_data(items: List[Dict[str, Any]]) -> Dict[str, int]:
    pass

# ❌ 悪い例
def get_user(user_id):  # 型定義なし
    pass

def process_data(items: Any) -> Any:  # any型使用
    pass
```

### エラーハンドリング
```python
# ✅ 良い例
from fastapi import HTTPException

@router.get("/users/{user_id}")
async def get_user(user_id: int) -> UserResponse:
    try:
        user = await user_service.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.from_orm(user)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### テスト

#### 基本的なテスト構造
```python
# テストファイル: test_{module_name}.py
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, db_session: Session) -> None:
        """Test user creation."""
        # Given: テストデータ
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        # When: ユーザー作成
        user = User.create(
            db_session,
            email=user_data["email"],
            password=user_data["password"],
            full_name=user_data["full_name"]
        )
        
        # Then: 正しく作成される
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
```

#### 型アノテーションのルール

##### 必須の型アノテーション
```python
# ✅ 良い例 - 最小限の型アノテーション
def test_user_creation(self, db_session: Session) -> None:
    """Test user creation functionality."""
    pass

def test_api_endpoint(self, client: TestClient, admin_token: str) -> None:
    """Test API endpoint."""
    pass

@pytest.fixture
def sample_user(self) -> User:
    """Create sample user for testing."""
    return User(email="test@example.com")
```

##### 型アノテーションのガイドライン
- **関数の引数**: 必須（Session, TestClient, str等）
- **戻り値**: None を明示的に指定
- **fixture**: 戻り値の型を必ず指定
- **複雑な型**: Any を使用して簡潔に

#### 統合テスト
```python
@pytest.mark.asyncio
async def test_get_user_success(client: TestClient, user_token: str) -> None:
    # Arrange
    user_id = 1
    
    # Act
    response = client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == user_id

@pytest.mark.asyncio
async def test_get_user_not_found(client: TestClient, admin_token: str) -> None:
    # Arrange
    user_id = 999
    
    # Act
    response = client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### SQLAlchemy モデル定義

#### バージョンの統一
- **新規プロジェクト**: SQLAlchemy 2.0スタイル（Mapped型）を使用
- **既存プロジェクト**: 段階的に2.0スタイルへ移行
- **混在する場合**: 明確にコメントで示す

#### SQLAlchemy 2.0スタイル（推奨）
```python
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
```

#### SQLAlchemy 1.xスタイル（レガシー）
```python
from sqlalchemy import Column, Integer, String, Boolean

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
```

#### バージョン混在時の対処
```python
# SQLAlchemy 1.xモデルの属性アクセス時
role_id = int(role.id)  # type: ignore[arg-type]
role_name = str(role.name)  # type: ignore[arg-type]
```

### ORM↔スキーマ変換

#### 明示的な変換（推奨）
ORMオブジェクトからPydanticスキーマへの変換は明示的に行う：

```python
# ✅ 良い例 - 明示的な変換
from app.schemas.user import UserResponse

def get_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name
    )

# ❌ 悪い例 - 暗黙的な変換に依存
def get_user_response(user: User) -> UserResponse:
    return UserResponse.from_orm(user)  # 型チェックで警告
```

#### 複雑なネストされた変換
```python
# ✅ 良い例 - ネストされたオブジェクトも明示的に変換
role_info = UserRoleInfo(
    role=RoleBasic(
        id=ur.role.id,
        code=ur.role.code,
        name=ur.role.name
    ),
    organization=OrganizationBasic(
        id=ur.organization.id,
        code=ur.organization.code,
        name=ur.organization.name
    )
)
```

#### Pydanticのfrom_attributes使用時の注意
```python
class UserResponse(BaseModel):
    # from_attributes=Trueは実行時には動作するが、
    # 型チェックでは認識されない場合がある
    class Config:
        from_attributes = True
```

### 型チェック（mypy）設定

#### 基本方針
- **新規プロジェクト**: `strict = true`を推奨
- **既存プロジェクト**: 段階的に厳格度を上げる
- **テストファイル**: 型エラーを無視する設定を許可

#### pyproject.toml設定例
```toml
[tool.mypy]
python_version = "3.13"
strict = true

# テストファイルの型エラーを無視
[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true
```

### type: ignoreコメントの使用規則

#### 使用可能なケース（優先順位順）

1. **外部ライブラリの型定義不備**
   ```python
   # FastAPIの既知の型定義問題
   app.add_exception_handler(ValidationError, handler)  # type: ignore[arg-type]
   ```

2. **SQLAlchemyバージョン混在**
   ```python
   # SQLAlchemy 1.x Column型への対処
   user_id = int(user.id)  # type: ignore[arg-type]
   ```

3. **段階的な型安全性向上の過程**
   ```python
   # TODO: モデルをSQLAlchemy 2.0スタイルに移行後削除
   org_name = str(org.name)  # type: ignore[arg-type]
   ```

#### 必須ルール
- 具体的なエラーコードを指定（例: [arg-type]）
- 理由をコメントで説明
- 可能な限りTODOコメントで将来の削除計画を示す

### 型チェックエラーの管理戦略

#### エラー分類ファイルの作成
大規模な型エラーが発生した場合は`.mypy-ignore.md`を作成：

```markdown
# Mypy Type Checking Error Classification

## 🔴 高優先度（早急に修正必要）
- 実行時エラーの可能性があるもの
- None型の属性アクセス
- 不正な戻り値型

## 🟡 中優先度（将来的に修正推奨）
- 型安全性は損なわれるが動作するもの
- ORM↔スキーマ変換の型不一致

## 🟢 低優先度（安全に無視可能）
- テスト関数の型アノテーション
- 外部ライブラリの型定義問題
```

#### 修正の追跡
- 修正したエラーは取り消し線で記録
- 新たに追加したtype: ignoreコメントは別途記録

### プロジェクト初期設定の推奨事項

#### 新規プロジェクトの型チェック設定

##### 推奨されるpyproject.toml設定
```toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true

# プロジェクト初期は段階的に厳格化
[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true

# SQLAlchemy プラグイン（2.0使用時）
plugins = ["sqlalchemy.ext.mypy.plugin"]
```

##### 既存プロジェクトへの導入
1. まず`mypy --no-error-summary`で現状把握
2. `.mypy-ignore.md`でエラー分類
3. 高優先度から順次修正
4. CI/CDでは`continue-on-error: true`から開始

### CI/CDパイプラインでの型チェック

#### 段階的な型安全性向上
1. **Phase 1**: 高優先度エラーのみをビルド失敗条件とする
2. **Phase 2**: 中優先度エラーを警告として扱う
3. **Phase 3**: エラー数の推移を追跡し、段階的に削減

#### 設定例
```yaml
# .github/workflows/ci.yml
- name: Type Check
  run: |
    uv run mypy . --strict
  continue-on-error: true  # 一時的にエラーを許容
```

## TypeScript（Frontend）規約

### 基本設定
```typescript
// 必須設定
"strict": true,
"noUnusedLocals": true,
"noUnusedParameters": true,
"noImplicitReturns": true
```

### 命名規則
- **関数・変数**: camelCase
- **コンポーネント・型**: PascalCase
- **定数**: UPPER_SNAKE_CASE
- **プライベート**: _leadingUnderscore

### 型定義
```typescript
// ✅ 良い例
interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
}

interface ApiResponse<T> {
  data: T;
  message: string;
  status: 'success' | 'error';
}

// ❌ 悪い例
interface User {
  id: any;  // any型使用
  name: string;
  email?: string;  // 不必要なoptional
}
```

### React コンポーネント
```typescript
// ✅ 良い例
interface UserCardProps {
  user: User;
  onEdit: (user: User) => void;
  isLoading?: boolean;
}

export function UserCard({ user, onEdit, isLoading = false }: UserCardProps) {
  const handleEditClick = useCallback(() => {
    onEdit(user);
  }, [user, onEdit]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      <button onClick={handleEditClick}>Edit</button>
    </div>
  );
}
```

### API呼び出し
```typescript
// ✅ 良い例
import { apiClient } from '@/services/api';

interface GetUsersParams {
  page?: number;
  limit?: number;
  search?: string;
}

export async function getUsers(params: GetUsersParams = {}): Promise<User[]> {
  try {
    const response = await apiClient.get<ApiResponse<User[]>>('/users', {
      params,
    });
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch users:', error);
    throw new Error('Failed to fetch users');
  }
}
```

### テスト
```typescript
// テストファイル: {ComponentName}.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UserCard } from './UserCard';

const mockUser: User = {
  id: 1,
  name: 'John Doe',
  email: 'john@example.com',
  createdAt: new Date('2023-01-01'),
};

describe('UserCard', () => {
  it('renders user information correctly', () => {
    // Arrange
    const onEdit = jest.fn();
    
    // Act
    render(<UserCard user={mockUser} onEdit={onEdit} />);
    
    // Assert
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    // Arrange
    const onEdit = jest.fn();
    render(<UserCard user={mockUser} onEdit={onEdit} />);
    
    // Act
    fireEvent.click(screen.getByText('Edit'));
    
    // Assert
    expect(onEdit).toHaveBeenCalledWith(mockUser);
  });
});
```

## データベース（SQL）規約

### 命名規則
- **テーブル**: snake_case（複数形）
- **カラム**: snake_case
- **インデックス**: idx_{table}_{column}
- **外部キー**: fk_{table}_{referenced_table}

### テーブル設計
```sql
-- ✅ 良い例
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

## API設計規約

### RESTful API
```
GET    /api/v1/users           # ユーザー一覧取得
GET    /api/v1/users/{id}      # ユーザー詳細取得
POST   /api/v1/users           # ユーザー作成
PUT    /api/v1/users/{id}      # ユーザー更新
DELETE /api/v1/users/{id}      # ユーザー削除
```

### レスポンス形式
```json
{
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "message": "Success",
  "status": "success"
}
```

### エラーレスポンス
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["Invalid email format"]
    }
  },
  "status": "error"
}
```

## Git規約

### ブランチ命名
- **機能**: feature/#123-add-user-management
- **バグ修正**: bugfix/#456-fix-login-error
- **ホットフィックス**: hotfix/#789-critical-security-fix

### コミットメッセージ
```
feat: add user authentication system

- Implement JWT-based authentication
- Add login/logout endpoints
- Create user session management
- Add password hashing with bcrypt

Closes #123
```

### PR命名
```
[WIP] feat: User Management System (Closes #123)
```

## セキュリティ規約

### 認証・認可
```python
# ✅ 良い例
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> User:
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await get_user_by_id(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 入力値検証
```python
# ✅ 良い例
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "password": "securepassword123"
            }
        }
```

## パフォーマンス規約

### データベースクエリ
```python
# ✅ 良い例 - N+1問題を回避
users = session.query(User).options(
    joinedload(User.profile),
    joinedload(User.roles)
).all()

# ❌ 悪い例 - N+1問題
users = session.query(User).all()
for user in users:
    print(user.profile.bio)  # 各ユーザーごとにクエリ実行
```

### フロントエンド最適化
```typescript
// ✅ 良い例 - メモ化とコード分割
import { memo, lazy, Suspense } from 'react';

const UserList = lazy(() => import('./UserList'));

export const UserManagement = memo(() => {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <UserList />
    </Suspense>
  );
});
```

## 品質チェック

### 自動チェック項目
- [ ] 型チェック（mypy --strict / tsc --noEmit）
- [ ] テストコードの型チェック（最小限のアノテーション必須）
- [ ] リント（black, isort, eslint）
- [ ] テスト（pytest / vitest）
- [ ] セキュリティスキャン
- [ ] パフォーマンステスト

### 手動チェック項目
- [ ] コードレビュー
- [ ] 設計レビュー
- [ ] セキュリティレビュー
- [ ] ドキュメント更新