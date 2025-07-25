# 🤖 Claude Code クイックリファレンス

## 🚀 コード作成前のチェックリスト

### Python
```bash
# 1. 既存のエラーを確認
cd backend && uv run ruff check . | head -20

# 2. インポートする予定のモジュールを確認
grep -r "from app.models" app/ | grep -v __pycache__
```

### TypeScript
```bash
# 1. 既存のコンポーネント構造を確認
ls -la frontend/src/components/

# 2. 型定義を確認
grep -r "interface.*Props" frontend/src/
```

## 📝 コード作成時の必須パターン

### Python - 行長制限の対処法
```python
# ❌ 長すぎる行
result = await some_very_long_function_name_that_exceeds_88_chars(parameter1, parameter2, parameter3)

# ✅ 改行を使用
result = await some_very_long_function_name_that_exceeds_88_chars(
    parameter1,
    parameter2,
    parameter3
)

# ❌ 長い文字列
error_message = "This is a very long error message that exceeds the 88 character limit and will cause E501"

# ✅ 複数行文字列または分割
error_message = (
    "This is a very long error message that exceeds "
    "the 88 character limit and will cause E501"
)
```

### Python - インポート整理
```python
# ✅ 正しいインポート順序
# 1. 標準ライブラリ
from __future__ import annotations
import os
from typing import Any, Optional

# 2. サードパーティ
from fastapi import Depends
from sqlalchemy import select

# 3. ローカル
from app.core.config import settings
from app.models.user import User
```

### TypeScript - any型の回避
```typescript
// ❌ any型の使用
const data: any = await fetchData();

// ✅ 適切な型定義
interface ApiResponse {
  id: string;
  data: unknown; // 本当に不明な場合
}
const data: ApiResponse = await fetchData();

// ✅ ジェネリクスの活用
async function fetchData<T>(): Promise<T> {
  const response = await fetch('/api/data');
  return response.json() as T;
}
```

## 🔧 コード作成後の必須コマンド

### 各ファイル保存後
```bash
# Python
cd backend && uv run ruff check <filename> --fix
cd backend && uv run ruff format <filename>

# TypeScript
cd frontend && npm run lint:fix
```

### コミット前
```bash
# 全体チェック（必須）
uv run pre-commit run --all-files

# 問題があった場合
cd backend && uv run ruff check . --fix --unsafe-fixes
cd backend && uv run ruff format .
```

## 🎯 よくあるエラーと対処法

### E501: Line too long
```python
# 関数呼び出しは括弧の後で改行
result = function_name(
    long_parameter_1,
    long_parameter_2,
)

# リストや辞書も同様
config = {
    "very_long_key_name": "value",
    "another_long_key": "another_value",
}
```

### F401: Unused import
```python
# 使用しないインポートは即削除
# Type checkingのみで使用する場合
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User  # 実行時にはインポートされない
```

### F821: Undefined name
```python
# 必ず定義してから使用
# グローバル変数の場合は明示的に
global_var: Optional[str] = None

def use_var() -> str:
    if global_var is None:
        raise ValueError("Not initialized")
    return global_var
```

## 🚨 Claude Codeエージェント専用ルール

1. **新規ファイル作成時**
   - 必ず `/templates/claude-code-*.py` or `.tsx` をベースに使用
   - テンプレートをコピーして修正する形で開始

2. **既存ファイル編集時**
   - 編集前に `ruff check <file>` で現状確認
   - 編集後に `ruff format <file>` で整形

3. **テスト作成時**
   - テストファイルも同じ品質基準を適用
   - `pytest -xvs <test_file>` で即座に実行確認

4. **PR作成前**
   - 必ず `uv run pre-commit run --all-files` を実行
   - エラーがある場合は修正してから再実行

## 💡 生産性向上のヒント

### エラーの事前回避
```bash
# Pythonファイル作成時の初期設定
echo '"""Module docstring."""' > new_file.py
echo 'from __future__ import annotations' >> new_file.py
echo '' >> new_file.py

# 作業開始時の環境確認
cd backend && uv run ruff --version
cd frontend && npm run lint -- --version
```

### バッチ処理
```bash
# 複数ファイルの一括修正
cd backend
find app -name "*.py" -type f | xargs uv run ruff check --fix
find app -name "*.py" -type f | xargs uv run ruff format
```

---

このリファレンスを参照しながらコードを作成することで、
Code Qualityエラーを最小限に抑え、効率的な開発が可能です。