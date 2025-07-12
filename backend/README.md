# ITDO ERP Backend

[🇬🇧 English](#english) | [🇯🇵 日本語](#japanese)

---

## English

FastAPI based backend for ITDO ERP System.

### Technology Stack

- **Python 3.13** - Programming language
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Redis** - Cache/Session storage
- **JWT** - Authentication
- **uv** - Package management

### Setup

#### Quick Setup
```bash
# Automated setup (recommended)
./setup-env.sh
```

#### Manual Setup
```bash
# Ensure uv is available in PATH
source ~/.local/bin/env
# or
export PATH="$HOME/.local/bin:$PATH"

# Verify uv is working
uv --version

# Install dependencies
uv venv
uv pip sync requirements-dev.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Run

```bash
# Start data layer (PostgreSQL, Redis)
podman-compose -f ../infra/compose-data.yaml up -d

# Run migrations (when available)
# uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

### API Documentation

When the server is running, you can access:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

### Authentication

The API uses JWT (JSON Web Tokens) for authentication.

#### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

#### Using the token
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your-access-token>"
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_security.py -v

# Run with type checking
uv run mypy --strict app/
```

### Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   │   └── v1/        # API version 1
│   ├── core/          # Core utilities
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # Application entry point
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── security/      # Security tests
├── alembic/           # Database migrations
├── pyproject.toml     # Project configuration
└── requirements.txt   # Dependencies
```

### Development Guidelines

1. **TDD (Test-Driven Development)**: Write tests first
2. **Type Safety**: Use type hints, run mypy with --strict
3. **Code Quality**: Use ruff for linting and formatting
4. **Security First**: Validate all inputs, use proper authentication

### Contributing

We welcome contributions! Please follow the development guidelines and ensure all tests pass before submitting a pull request.

### Security

- Passwords are hashed using bcrypt
- JWT tokens expire after 24 hours
- All endpoints require authentication except login
- Input validation on all requests
- SQL injection protection via SQLAlchemy ORM

---

## Japanese

ITDO ERPシステム用のFastAPIベースのバックエンドです。

### 技術スタック

- **Python 3.13** - プログラミング言語
- **FastAPI** - Webフレームワーク
- **SQLAlchemy** - ORM
- **PostgreSQL** - データベース
- **Redis** - キャッシュ/セッションストレージ
- **JWT** - 認証
- **uv** - パッケージ管理

### セットアップ

#### クイックセットアップ
```bash
# 自動セットアップ（推奨）
./setup-env.sh
```

#### 手動セットアップ
```bash
# uvがPATHで利用可能であることを確認
source ~/.local/bin/env
# または
export PATH="$HOME/.local/bin:$PATH"

# uvが動作することを確認
uv --version

# 依存関係をインストール
uv venv
uv pip sync requirements-dev.txt

# 環境変数をセットアップ
cp .env.example .env
# 設定に合わせて .env を編集
```

### 実行

```bash
# データレイヤー（PostgreSQL、Redis）を開始
podman-compose -f ../infra/compose-data.yaml up -d

# マイグレーションを実行（利用可能な場合）
# uv run alembic upgrade head

# 開発サーバーを開始
uv run uvicorn app.main:app --reload
```

### APIドキュメント

サーバーが動作している場合、以下にアクセスできます：
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

### 認証

APIは認証にJWT（JSON Web Tokens）を使用します。

#### ログイン
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

#### トークンの使用
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your-access-token>"
```

### テスト

```bash
# すべてのテストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=app --cov-report=html

# 特定のテストファイルを実行
uv run pytest tests/unit/test_security.py -v

# 型チェック付きで実行
uv run mypy --strict app/
```

### プロジェクト構造

```
backend/
├── app/
│   ├── api/           # APIエンドポイント
│   │   └── v1/        # APIバージョン1
│   ├── core/          # コアユーティリティ
│   ├── models/        # SQLAlchemyモデル
│   ├── schemas/       # Pydanticスキーマ
│   ├── services/      # ビジネスロジック
│   └── main.py        # アプリケーションエントリーポイント
├── tests/
│   ├── unit/          # ユニットテスト
│   ├── integration/   # 統合テスト
│   └── security/      # セキュリティテスト
├── alembic/           # データベースマイグレーション
├── pyproject.toml     # プロジェクト設定
└── requirements.txt   # 依存関係
```

### 開発ガイドライン

1. **TDD（テスト駆動開発）**: テストを最初に書く
2. **型安全性**: 型ヒントを使用し、mypyを--strictで実行
3. **コード品質**: リントとフォーマットにruffを使用
4. **セキュリティファースト**: すべての入力を検証し、適切な認証を使用

### 貢献

貢献を歓迎します！プルリクエストを提出する前に、開発ガイドラインに従い、すべてのテストが通ることを確認してください。

### セキュリティ

- パスワードはbcryptを使用してハッシュ化
- JWTトークンは24時間で期限切れ
- ログイン以外のすべてのエンドポイントで認証が必要
- すべてのリクエストで入力検証
- SQLAlchemy ORMによるSQLインジェクション保護