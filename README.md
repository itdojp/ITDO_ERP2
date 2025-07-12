# ITDO ERP System v2

[🇯🇵 日本語](#japanese) | [🇬🇧 English](#english)

---

## <a name="japanese"></a>🇯🇵 日本語

### 概要

現代的な技術スタックを使用した新世代ERPシステムです。

### 技術スタック

- **バックエンド**: Python 3.13 + FastAPI
- **フロントエンド**: React 18 + TypeScript 5
- **データベース**: PostgreSQL 15
- **キャッシュ**: Redis
- **認証**: Keycloak (OAuth2 / OpenID Connect)
- **コンテナ**: Podman
- **Pythonパッケージ管理**: uv
- **Node.jsバージョン管理**: Volta

### クイックスタート

```bash
# 1. プロジェクト初期化
./scripts/init-project.sh

# 2. データ層起動
podman-compose -f infra/compose-data.yaml up -d

# 3. 開発サーバー起動（ローカル）
# Backend
cd backend && uv run uvicorn app.main:app --reload

# Frontend (別ターミナル)
cd frontend && npm run dev
```

### 開発環境

ハイブリッド開発環境を採用：
- **データ層**: 常にコンテナで実行（PostgreSQL, Redis, Keycloak）
- **開発層**: ローカル実行推奨（高速な開発イテレーション）

### CI/CDパイプライン

GitHub Actionsによる包括的な品質保証：

#### 🛡️ セキュリティ & 品質チェック
- **Python セキュリティスキャン**: bandit、safety による脆弱性検査
- **Node.js セキュリティ監査**: npm audit による依存関係チェック  
- **コンテナセキュリティ**: Trivy による脆弱性スキャン
- **OWASP ZAP**: 動的セキュリティテスト（本番デプロイ時）

#### 🔍 コード品質保証
- **Python型チェック**: mypy strict mode による厳格な型検査
- **TypeScript型チェック**: tsc による型安全性検証
- **ESLint**: TypeScript + React のコード品質チェック
- **型カバレッジ**: 95%以上の型アノテーション率を維持

#### 🧪 テスト実行
- **バックエンドテスト**: pytest によるユニット・統合テスト
- **フロントエンドテスト**: Vitest + React Testing Library
- **E2Eテスト**: 本番環境での総合テスト

#### 📊 品質メトリクス
- **テストカバレッジ**: 目標 >80%
- **型安全性**: SQLAlchemy 2.0 + 厳格な型チェック
- **セキュリティ**: ゼロ既知脆弱性を維持
- **パフォーマンス**: API応答時間 <200ms

### ドキュメント

- [Claude Code使用ガイド](docs/claude-code-usage-guide.md) - Claude Code使用方法
- [開発環境セットアップ](docs/development-environment-setup.md) - 環境構築手順
- [アーキテクチャ](docs/architecture.md)
- [開発ガイド](docs/development-guide.md)
- [API仕様](backend/docs/api-spec.md)

### ライセンス

Proprietary

---

## <a name="english"></a>🇬🇧 English

### Overview

A next-generation ERP system built with modern technology stack.

### Technology Stack

- **Backend**: Python 3.13 + FastAPI
- **Frontend**: React 18 + TypeScript 5
- **Database**: PostgreSQL 15
- **Cache**: Redis
- **Authentication**: Keycloak (OAuth2 / OpenID Connect)
- **Container**: Podman
- **Python Package Manager**: uv
- **Node.js Version Manager**: Volta

### Quick Start

```bash
# 1. Initialize project
./scripts/init-project.sh

# 2. Start data layer
podman-compose -f infra/compose-data.yaml up -d

# 3. Start development servers (local)
# Backend
cd backend && uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```

### Development Environment

Hybrid development environment:
- **Data Layer**: Always runs in containers (PostgreSQL, Redis, Keycloak)
- **Development Layer**: Local execution recommended (fast development iteration)

### CI/CD Pipeline

Comprehensive quality assurance with GitHub Actions:

#### 🛡️ Security & Quality Checks
- **Python Security Scan**: Vulnerability detection with bandit and safety
- **Node.js Security Audit**: Dependency checking with npm audit
- **Container Security**: Vulnerability scanning with Trivy
- **OWASP ZAP**: Dynamic security testing (production deployment)

#### 🔍 Code Quality Assurance
- **Python Type Checking**: Strict type checking with mypy strict mode
- **TypeScript Type Checking**: Type safety verification with tsc
- **ESLint**: Code quality checking for TypeScript + React
- **Type Coverage**: Maintaining >95% type annotation rate

#### 🧪 Test Execution
- **Backend Tests**: Unit and integration tests with pytest
- **Frontend Tests**: Vitest + React Testing Library
- **E2E Tests**: Comprehensive testing in production environment

#### 📊 Quality Metrics
- **Test Coverage**: Target >80%
- **Type Safety**: SQLAlchemy 2.0 + strict type checking
- **Security**: Maintaining zero known vulnerabilities
- **Performance**: API response time <200ms

### Documentation

- [Claude Code Usage Guide](docs/claude-code-usage-guide.md) - How to use Claude Code
- [Development Environment Setup](docs/development-environment-setup.md) - Environment setup instructions
- [Architecture](docs/architecture.md)
- [Development Guide](docs/development-guide.md)
- [API Specification](backend/docs/api-spec.md)

### License

Proprietary