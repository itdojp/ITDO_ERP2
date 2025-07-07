# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ITDO ERP System v2 - Modern ERP system with hybrid development environment.

**Technology Stack:**
- Backend: Python 3.13 + FastAPI + uv (package manager)
- Frontend: React 18 + TypeScript 5 + Vite + Vitest
- Database: PostgreSQL 15 + Redis 7
- Auth: Keycloak (OAuth2/OpenID Connect)
- Container: Podman (data layer only)

## Architecture

### Backend Structure
- `app/main.py` - FastAPI application entry point
- `app/api/v1/` - API endpoints (versioned)
- `app/core/` - Core utilities (config, database, security)
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic schemas for API
- `app/services/` - Business logic layer
- `tests/` - Test files (unit, integration, security)

### Frontend Structure
- `src/components/` - React components
- `src/pages/` - Page components
- `src/services/` - API client and utilities
- `src/test/` - Test utilities and setup

### Infrastructure
- `infra/compose-data.yaml` - Data layer containers (PostgreSQL, Redis, Keycloak, pgAdmin)
- `scripts/` - Development and deployment scripts
- `Makefile` - Common development commands

## Development Workflow

### Critical Constraints
1. **Test-Driven Development (TDD)**: Always write tests BEFORE implementation
2. **Hybrid Environment**: Data layer in containers, development layer local
3. **uv Tool Usage**: Use `uv` for Python, not pip/activate
4. **Type Safety**: No `any` types, strict type checking required
5. **Issue-Driven Development**: All work starts from GitHub Issues
6. **Issue Assignment Protocol**: MANDATORY issue assignment before starting work

### Issue Assignment Protocol (MANDATORY)
When starting work on any issue, Claude Code MUST follow this protocol:

1. **Issue Assignment Declaration**:
   ```
   🚀 Starting work on this issue
   Assignee: @[username]
   Expected completion: [yyyy-mm-dd]
   Approach: [brief implementation plan]
   ```

2. **Branch Creation**: 
   ```bash
   git checkout -b feature/#[issue-number]-[brief-description]
   ```

3. **Draft PR Creation**:
   ```bash
   gh pr create --draft --title "[WIP] feat: [feature-name] (Closes #[issue-number])" --body "Implementation in progress..."
   ```

This protocol prevents work duplication and ensures team coordination.

### Development Environment Setup
```bash
# 1. Initial setup
make setup-dev

# 2. Start data layer (PostgreSQL, Redis, Keycloak)
make start-data

# 3. Development servers (run in separate terminals)
make dev
```

## Essential Commands

### Development
```bash
# Start development servers
make dev                    # Both backend and frontend
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev

# Data layer management
make start-data            # Start containers
make stop-data            # Stop containers
make status               # Check container status
```

### Testing
```bash
# Run all tests
make test                 # Basic tests (no E2E)
make test-full           # Full test suite including E2E

# Backend specific
cd backend && uv run pytest                    # All tests
cd backend && uv run pytest tests/unit/        # Unit tests only
cd backend && uv run pytest tests/integration/ # Integration tests only
cd backend && uv run pytest -v --cov=app      # With coverage

# Frontend specific
cd frontend && npm test                        # Vitest tests
cd frontend && npm run test:ui                 # Vitest UI
cd frontend && npm run coverage                # Coverage report
```

### Code Quality
```bash
# Lint and format
make lint                 # Both backend and frontend
cd backend && uv run ruff check . && uv run ruff format .
cd frontend && npm run lint

# Type checking
make typecheck           # Both backend and frontend
cd backend && uv run mypy --strict app/
cd frontend && npm run typecheck

# Security scanning
make security-scan       # Full security audit
```

### Package Management
```bash
# Backend (Python with uv)
cd backend && uv add <package>              # Add dependency
cd backend && uv add --dev <package>        # Add dev dependency
cd backend && uv sync                       # Sync dependencies
cd backend && uv run <command>              # Run command in environment

# Frontend (Node.js with npm)
cd frontend && npm install <package>        # Add dependency
cd frontend && npm install --save-dev <package>  # Add dev dependency
cd frontend && npm install                  # Install dependencies
```

## Testing Patterns

### Backend Testing
- Use `pytest` with async support
- Test fixtures in `tests/conftest.py`
- In-memory SQLite for unit tests
- `TestClient` for API testing
- Test categories: unit, integration, security

### Frontend Testing
- Use `vitest` with React Testing Library
- Test setup in `src/test/setup.ts`
- Component tests with `@testing-library/react`
- Coverage reports available

## CI/CD Pipeline

### GitHub Actions Workflows
- **ci.yml**: Main CI/CD pipeline (typecheck, tests, security scans)
- **security-scan.yml**: Comprehensive security scanning
- **typecheck.yml**: Strict type checking with quality gates

### Quality Gates & Checks
✅ **現在安定動作中:**
- Python/Node.js セキュリティスキャン
- TypeScript型チェック  
- フロントエンドテスト（Vitest + React Testing Library）
- コンテナセキュリティスキャン

⚠️ **軽微な問題（開発に影響なし）:**
- Pythonタイプチェック（テストファイルの型アノテーション不足）

### 重要な修正履歴
- **SQLAlchemy 2.0 完全移行**: DeclarativeBase + Mapped型使用
- **GitHub Actions更新**: v3→v4アップデート完了
- **ESLint設定**: TypeScript + React対応完了
- **テスト安定性**: 非同期レンダリング対応完了

## Configuration

### Backend Configuration
- Settings in `app/core/config.py` using Pydantic
- Environment variables in `.env` file
- Database: PostgreSQL with SQLAlchemy 2.0 ORM (Mapped types)
- Authentication: Keycloak integration

### Frontend Configuration
- Vite configuration in `vite.config.ts`
- TypeScript strict mode enabled
- ESLint + Prettier for code formatting (TypeScript/React対応)
- Tailwind CSS for styling

## Quality Standards
- API Response Time: <200ms
- Test Coverage: >80%
- Concurrent Users: 1000+
- Error Handling: Required for all functions
- Type Safety: Strict TypeScript and mypy

## Key Development Notes

### Python Environment
- Always use `uv run` prefix for Python commands
- Never use `pip` or virtual environment activation
- Python 3.13 required

### Container Management
- Use `podman-compose` not `docker-compose`
- Data layer always in containers
- Development layer runs locally for performance

### Database Access
- Development: localhost:5432
- Admin UI: pgAdmin at localhost:8081
- Test: In-memory SQLite

### Service Ports
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Keycloak: http://localhost:8080
- pgAdmin: http://localhost:8081

## Common Issues

### Environment Path
Scripts may need PATH adjustment for uv:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Container Issues
If containers fail to start:
```bash
make stop-data
make start-data
make status
```

### Test Database
Backend tests use in-memory SQLite automatically configured in `tests/conftest.py`