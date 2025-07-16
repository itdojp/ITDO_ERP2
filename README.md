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
- **Code Quality**: 新規エラー 0個/週（必須）

## 📋 プロジェクト規定

**全開発者必読**:
- [PROJECT_STANDARDS.md](PROJECT_STANDARDS.md) - プロジェクト品質規定
- [AGENT_MANDATORY_CHECKLIST.md](AGENT_MANDATORY_CHECKLIST.md) - 必須チェックリスト

### 🚨 Code Quality必須コマンド
```bash
# 作業前後に必ず実行
./scripts/claude-code-quality-check.sh

# コミット前に必ず実行
uv run pre-commit run --all-files
```

## Claude Code Optimization

For efficient Claude Code usage and cost optimization:

1. **Monitoring Script**: Run `./scripts/claude-usage-monitor.sh` for usage analysis
2. **Optimization Guide**: See [Claude Code Optimization Guide](docs/CLAUDE_CODE_OPTIMIZATION_GUIDE.md)
3. **Configuration**: `.claudeignore` and `.gitignore` are optimized for minimal token usage
4. **Best Practices**: 
   - Use `/compact` every 2-4 hours
   - Keep sessions focused and specific
   - Regular cache cleanup for optimal performance

## Documentation

- [Claude Code Usage Guide](docs/claude-code-usage-guide.md) - Claude Code使用方法
- [Claude Code Optimization Guide](docs/CLAUDE_CODE_OPTIMIZATION_GUIDE.md) - 使用量最適化ガイド
- [Development Environment Setup](docs/development-environment-setup.md) - 環境構築手順
- [Architecture](docs/architecture.md)
- [Development Guide](docs/development-guide.md)
- [API Specification](backend/docs/api-spec.md)

## License

Proprietary