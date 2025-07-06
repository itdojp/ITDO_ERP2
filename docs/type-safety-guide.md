# 型安全性ガイド

## 概要

ITDO ERP System v2では、型安全性を最優先として開発を行います。このガイドでは、型安全なコードを書くための指針と実践方法を説明します。

## 基本原則

### 1. 厳格な型チェック（Strict Mode）

すべてのコードはmypyの厳格モードでチェックされます：

```toml
# backend/pyproject.toml
[tool.mypy]
strict = true
disallow_any_explicit = true
disallow_any_generics = true
```

### 2. Any型の禁止

`Any`型の使用は原則禁止です。型が不明な場合は以下を使用してください：

```python
# ❌ Bad
def process_data(data: Any) -> Any:
    return data

# ✅ Good
from typing import Union, Dict, List, Optional

def process_data(data: Union[Dict[str, str], List[str]]) -> Optional[str]:
    if isinstance(data, dict):
        return data.get("key")
    elif isinstance(data, list):
        return data[0] if data else None
    return None
```

### 3. 型アノテーションの必須化

すべての関数、メソッド、変数に型アノテーションが必要です：

```python
# ❌ Bad
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total

# ✅ Good
from typing import List
from decimal import Decimal
from app.models.item import Item

def calculate_total(items: List[Item]) -> Decimal:
    total: Decimal = Decimal("0")
    for item in items:
        total += item.price
    return total
```

## 実装パターン

### 1. ベースクラスの使用

共通の型定義は`app/types/__init__.py`から使用します：

```python
from app.types import (
    ModelType,
    CreateSchemaType,
    UpdateSchemaType,
    ServiceResult
)
```

### 2. リポジトリパターン

データアクセスは型安全なリポジトリパターンを使用：

```python
from app.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    pass
```

### 3. APIルーター

APIエンドポイントは基底クラスを使用：

```python
from app.api.base import BaseAPIRouter
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse

user_router = BaseAPIRouter(
    prefix="/users",
    tags=["users"],
    model=User,
    repository=UserRepository,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    response_schema=UserResponse
).get_router()
```

## 型チェックツール

### 1. 開発時のチェック

```bash
# backend ディレクトリで実行
./scripts/typecheck.sh

# 詳細レポート生成
./scripts/typecheck.sh --report
```

### 2. VS Codeタスク

- `Ctrl+Shift+P` → `Tasks: Run Task` → `Full Type Check`
- または個別に：
  - `Python: Type Check`
  - `TypeScript: Type Check`

### 3. Pre-commitフック

コミット時に自動的に型チェックが実行されます。

### 4. CI/CDパイプライン

プルリクエスト時に自動的に型チェックが実行され、結果がコメントされます。

## 型チェックエラーの対処法

### 1. Union型の使用

```python
from typing import Union

def parse_value(value: Union[str, int]) -> str:
    if isinstance(value, int):
        return str(value)
    return value
```

### 2. TypeGuardの使用

```python
from typing import TypeGuard, List, Dict, Any

def is_string_list(items: List[Any]) -> TypeGuard[List[str]]:
    return all(isinstance(item, str) for item in items)

def process_strings(items: List[Any]) -> None:
    if is_string_list(items):
        # ここでitemsはList[str]として扱われる
        for item in items:
            print(item.upper())
```

### 3. Protocolの使用

```python
from typing import Protocol

class Auditable(Protocol):
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]

def audit_log(entity: Auditable) -> None:
    print(f"Created at: {entity.created_at}")
```

## 型無視コメントの使用

型無視コメントは最小限に留め、必ず理由を記載してください：

```python
# ❌ Bad
result = some_function()  # type: ignore

# ✅ Good
# FastAPIのStarlette型定義の不整合により一時的に無視
app.add_exception_handler(RequestValidationError, handler)  # type: ignore[arg-type]
```

## 品質基準

### 必須要件
- mypyエラー: 0件
- `Any`型の使用: 0件（やむを得ない場合を除く）

### 推奨基準
- `type: ignore`コメント: 20件以下
- 型カバレッジ: 95%以上

## トラブルシューティング

### よくあるエラーと解決方法

1. **"Incompatible return value type"**
   ```python
   # 問題: 戻り値の型が一致しない
   def get_user(id: int) -> User:
       user = db.query(User).filter(User.id == id).first()
       return user  # userはOptional[User]
   
   # 解決: 適切な型チェック
   def get_user(id: int) -> Optional[User]:
       return db.query(User).filter(User.id == id).first()
   ```

2. **"Item 'None' has no attribute"**
   ```python
   # 問題: Noneチェックがない
   user = get_user(id)
   print(user.name)  # userがNoneの可能性
   
   # 解決: Noneチェックを追加
   user = get_user(id)
   if user:
       print(user.name)
   ```

3. **"Missing type annotation"**
   ```python
   # 問題: 型アノテーションがない
   def process(data):
       return data
   
   # 解決: 型アノテーションを追加
   def process(data: str) -> str:
       return data
   ```

## 参考資料

- [mypy documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)