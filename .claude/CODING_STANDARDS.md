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
```python
# テストファイル: test_{module_name}.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_user_success(client: AsyncClient):
    # Arrange
    user_id = 1
    
    # Act
    response = await client.get(f"/api/v1/users/{user_id}")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == user_id

@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    # Arrange
    user_id = 999
    
    # Act
    response = await client.get(f"/api/v1/users/{user_id}")
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
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
- [ ] リント（black, isort, eslint）
- [ ] テスト（pytest / vitest）
- [ ] セキュリティスキャン
- [ ] パフォーマンステスト

### 手動チェック項目
- [ ] コードレビュー
- [ ] 設計レビュー
- [ ] セキュリティレビュー
- [ ] ドキュメント更新