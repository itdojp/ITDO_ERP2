# 技術的制約とガイドライン

## システム要件

### パフォーマンス要件
- **API応答時間**: 200ms以内（95パーセンタイル）
- **同時接続数**: 1000ユーザー対応
- **データベース**: 接続プール最大20接続
- **メモリ使用量**: Backend 512MB以内、Frontend bundle 2MB以内

### 可用性要件
- **稼働率**: 99.9%以上
- **データバックアップ**: 日次自動バックアップ
- **障害復旧**: RTO 4時間、RPO 1時間

## 技術スタック制約

### Python/Backend
```python
# 必須バージョン
Python >= 3.11
FastAPI >= 0.104.1
SQLAlchemy >= 2.0.23
pydantic >= 2.5.0

# 禁止事項
- Django（FastAPIを使用）
- Flask（FastAPIを使用）
- pip/virtualenv（uvを使用）
- asyncpg直接使用（SQLAlchemy ORM経由）
```

### Node.js/Frontend
```json
{
  "engines": {
    "node": ">=18.18.2",
    "npm": ">=9.8.1"
  },
  "required": [
    "React >= 18.2.0",
    "TypeScript >= 5.2.2",
    "Vite >= 4.5.0"
  ],
  "prohibited": [
    "create-react-app",
    "webpack直接設定",
    "JavaScript（TypeScript必須）"
  ]
}
```

### データベース
```sql
-- 必須設定
PostgreSQL >= 15
Redis >= 7

-- 制約事項
- ORMを経由しない生SQL禁止（セキュリティ理由）
- NOSQLデータベース使用禁止（データ整合性要件）
- インメモリDB（本番環境）使用禁止
```

## アーキテクチャ制約

### レイヤー分離
```
┌─────────────────┐
│   Presentation  │ ← React Components
├─────────────────┤
│    Service      │ ← Business Logic
├─────────────────┤
│   Repository    │ ← Data Access
├─────────────────┤
│    Database     │ ← PostgreSQL
└─────────────────┘
```

### 依存関係ルール
```python
# ✅ 許可された依存関係
Presentation → Service → Repository → Database
Service → External APIs

# ❌ 禁止された依存関係
Repository → Service  # 逆依存禁止
Database → Repository # 逆依存禁止
Presentation → Repository # レイヤー飛び越し禁止
```

## セキュリティ制約

### 認証・認可
```python
# 必須実装
- OAuth2 / OpenID Connect（Keycloak使用）
- JWT Token（有効期限30分）
- Refresh Token（有効期限7日）
- Role-Based Access Control (RBAC)

# 禁止事項
- 独自認証システム
- Session-based認証
- 平文パスワード保存
- 管理者権限のハードコーディング
```

### データ保護
```python
# 必須実装
from cryptography.fernet import Fernet
import bcrypt

# パスワードハッシュ化（必須）
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# 機密データ暗号化（必須）
cipher = Fernet(encryption_key)
encrypted_data = cipher.encrypt(sensitive_data.encode())

# 禁止事項
- 機密データの平文保存
- ログへの機密情報出力
- フロントエンドでの機密データ保持
```

### 入力値検証
```python
# 必須実装（Pydantic使用）
from pydantic import BaseModel, EmailStr, Field, validator

class UserInput(BaseModel):
    email: EmailStr  # メール形式検証
    name: str = Field(..., min_length=1, max_length=100)  # 長さ制限
    age: int = Field(..., ge=0, le=150)  # 範囲制限
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

# 禁止事項
- 入力値検証なしのAPI
- HTMLエスケープなしの出力
- SQLクエリへの直接入力値埋め込み
```

## コード品質制約

### 型安全性
```python
# Python - mypy strict モード必須
[tool.mypy]
strict = true
disallow_any_expr = true
disallow_any_decorated = true
disallow_any_explicit = true
disallow_any_generics = true

# TypeScript - strict モード必須
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true
  }
}
```

### テスト要件
```python
# 必須テストカバレッジ
- 単体テスト: 80%以上
- 統合テスト: 主要API全て
- E2Eテスト: クリティカルパス全て

# 必須テストパターン
@pytest.mark.asyncio
async def test_function():
    # Arrange - テストデータ準備
    # Act - 実行
    # Assert - 検証
    pass

# 禁止事項
- テストなしのコード実装
- モックなしの外部依存テスト
- 副作用があるテスト
```

### エラーハンドリング
```python
# 必須実装パターン
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def api_function():
    try:
        # ビジネスロジック
        result = await business_logic()
        return result
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail="Invalid input")
    except BusinessLogicError as e:
        logger.error(f"Business logic error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# 禁止事項
- 例外の無視（pass文）
- 汎用Exception catchのみ
- エラーメッセージに機密情報含有
```

## インフラストラクチャ制約

### コンテナ要件
```yaml
# 必須設定
version: '3.8'
services:
  app:
    image: python:3.11-slim  # 軽量イメージ使用
    resources:
      limits:
        memory: 512M  # メモリ制限
        cpus: '0.5'   # CPU制限
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

# 禁止事項
- :latest タグの使用
- root ユーザーでの実行
- シークレットの環境変数露出
```

### 環境設定
```bash
# 必須環境変数
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
SECRET_KEY=random-secret-key
LOG_LEVEL=INFO

# 禁止事項
export SECRET_KEY=hardcoded-secret  # ハードコーディング禁止
export DEBUG=true  # 本番環境でのデバッグモード禁止
```

## 開発プロセス制約

### Git ワークフロー
```bash
# 必須ブランチ戦略
main     ← 本番環境
develop  ← 統合環境
feature/* ← 機能開発

# 必須プロセス
1. Issue作成
2. feature ブランチ作成
3. Draft PR作成
4. テスト実装
5. 機能実装
6. レビュー
7. マージ

# 禁止事項
- main ブランチへの直接push
- テストなしのPR
- レビューなしのマージ
```

### CI/CD要件
```yaml
# 必須チェック項目
- name: Type Check
  run: |
    mypy --strict backend/
    tsc --noEmit --project frontend/

- name: Lint Check
  run: |
    black --check backend/
    eslint frontend/src/

- name: Test
  run: |
    pytest backend/tests/
    npm test -- --coverage

- name: Security Scan
  run: |
    bandit -r backend/
    npm audit

# 失敗時の動作
- テスト失敗時: デプロイ停止
- セキュリティ脆弱性発見時: デプロイ停止
- カバレッジ不足時: 警告表示
```

## 監視・ログ要件

### ログ設定
```python
# 必須ログ項目
import structlog

logger = structlog.get_logger()

# API アクセスログ
logger.info(
    "api_access",
    method=request.method,
    path=request.url.path,
    user_id=current_user.id,
    response_time=response_time,
    status_code=response.status_code
)

# エラーログ
logger.error(
    "api_error",
    error_type=type(exception).__name__,
    error_message=str(exception),
    user_id=getattr(current_user, 'id', None),
    stack_trace=traceback.format_exc()
)
```

### メトリクス収集
```python
# 必須メトリクス
- API応答時間
- エラー率
- データベース接続数
- メモリ使用量
- CPU使用率

# 禁止ログ項目
- パスワード
- JWT Token
- 個人情報（PII）
- クレジットカード情報
```

## 制約違反時の対応

### 自動チェック
```bash
# pre-commit フック設定
repos:
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: mypy --strict
        language: system
        types: [python]
        
      - id: typescript
        name: typescript
        entry: tsc --noEmit
        language: system
        types: [typescript]
```

### 手動レビュー
- [ ] アーキテクチャ違反がないか
- [ ] セキュリティ要件を満たしているか
- [ ] パフォーマンス要件を満たしているか
- [ ] コード品質基準を満たしているか

### 制約違反時の対応
1. **即座の修正**: セキュリティ関連
2. **次回リリースで修正**: パフォーマンス関連
3. **技術負債として管理**: レガシーコード関連

これらの制約は品質、セキュリティ、保守性を確保するための最低限の要件です。違反がある場合は、実装前に必ず修正してください。