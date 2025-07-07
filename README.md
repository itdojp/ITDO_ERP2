# ITDO ERP System v2

## Overview

現代的な技術スタックを使用した新世代ERPシステムです。

## Technology Stack

- **Backend**: Python 3.13 + FastAPI
- **Frontend**: React 18 + TypeScript 5
- **Database**: PostgreSQL 15
- **Cache**: Redis
- **Authentication**: Keycloak (OAuth2 / OpenID Connect)
- **Container**: Podman
- **Python Package Manager**: uv
- **Node.js Version Manager**: Volta

## Quick Start

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

## Development Environment

ハイブリッド開発環境を採用：
- **データ層**: 常にコンテナで実行（PostgreSQL, Redis, Keycloak）
- **開発層**: ローカル実行推奨（高速な開発イテレーション）

## CI/CD Pipeline

GitHub Actionsによる包括的な品質保証：

### 🛡️ セキュリティ & 品質チェック
- **Python セキュリティスキャン**: bandit、safety による脆弱性検査
- **Node.js セキュリティ監査**: npm audit による依存関係チェック  
- **コンテナセキュリティ**: Trivy による脆弱性スキャン
- **OWASP ZAP**: 動的セキュリティテスト（本番デプロイ時）

### 🔍 コード品質保証
- **Python型チェック**: mypy strict mode による厳格な型検査
- **TypeScript型チェック**: tsc による型安全性検証
- **ESLint**: TypeScript + React のコード品質チェック
- **型カバレッジ**: 95%以上の型アノテーション率を維持

### 🧪 テスト実行
- **バックエンドテスト**: pytest によるユニット・統合テスト
- **フロントエンドテスト**: Vitest + React Testing Library
- **E2Eテスト**: 本番環境での総合テスト

### 📊 品質メトリクス
- **テストカバレッジ**: 目標 >80%
- **型安全性**: SQLAlchemy 2.0 + 厳格な型チェック
- **セキュリティ**: ゼロ既知脆弱性を維持
- **パフォーマンス**: API応答時間 <200ms

## Documentation

### For Developers
- [Claude Code Team Guide](.claude/TEAM_CLAUDE_GUIDE.md) - **必読**: Claude Code使用時の必須規約
- [Issue Workflow](.claude/ISSUE_WORKFLOW.md) - Issue着手時の手順
- [Development Workflow](.claude/DEVELOPMENT_WORKFLOW.md) - 開発ワークフロー
- [Coding Standards](.claude/CODING_STANDARDS.md) - コーディング規約

### Technical Documentation  
- [Architecture](docs/architecture.md)
- [Development Guide](docs/development-guide.md)
- [API Specification](backend/docs/api-spec.md)

### ⚠️ Important for Claude Code Users
**All team members using Claude Code MUST read and follow [Team Claude Guide](.claude/TEAM_CLAUDE_GUIDE.md) before starting any work.**

## License

Proprietary