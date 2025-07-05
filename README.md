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

## Documentation

- [Claude Code Usage Guide](docs/claude-code-usage-guide.md) - Claude Code使用方法
- [Development Environment Setup](docs/development-environment-setup.md) - 環境構築手順
- [Architecture](docs/architecture.md)
- [Development Guide](docs/development-guide.md)
- [API Specification](backend/docs/api-spec.md)

## License

Proprietary