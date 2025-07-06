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
  - `auth.py` - Authentication endpoints
  - `users.py` - User management
  - `dashboard.py` - Dashboard statistics
  - `progress.py` - Progress management
- `app/core/` - Core utilities (config, database, security)
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic schemas for API
  - `dashboard.py` - Dashboard response schemas
- `app/services/` - Business logic layer
  - `dashboard.py` - Dashboard statistics service
  - `progress.py` - Progress calculations service
- `tests/` - Test files (unit, integration, security)
  - `test_dashboard_progress/` - Dashboard and progress tests

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
export PATH="/root/.local/bin:$PATH" && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

# Backend specific - ALWAYS include PATH export
export PATH="/root/.local/bin:$PATH" && uv run pytest                    # All tests
export PATH="/root/.local/bin:$PATH" && uv run pytest tests/unit/        # Unit tests only
export PATH="/root/.local/bin:$PATH" && uv run pytest tests/integration/ # Integration tests only
export PATH="/root/.local/bin:$PATH" && uv run pytest -v --cov=app      # With coverage

# Frontend specific
cd frontend && npm test                        # Vitest tests
cd frontend && npm run test:ui                 # Vitest UI
cd frontend && npm run coverage                # Coverage report
```

### Code Quality
```bash
# Lint and format - ALWAYS include PATH export
make lint                 # Both backend and frontend
export PATH="/root/.local/bin:$PATH" && uv run ruff check . && uv run ruff format .
cd frontend && npm run lint

# Type checking - ALWAYS include PATH export
make typecheck           # Both backend and frontend
export PATH="/root/.local/bin:$PATH" && uv run mypy --strict app/
cd frontend && npm run typecheck

# Security scanning
make security-scan       # Full security audit
```

### Package Management
```bash
# Backend (Python with uv) - ALWAYS include PATH export
export PATH="/root/.local/bin:$PATH" && uv add <package>              # Add dependency
export PATH="/root/.local/bin:$PATH" && uv add --dev <package>        # Add dev dependency
export PATH="/root/.local/bin:$PATH" && uv sync                       # Sync dependencies
export PATH="/root/.local/bin:$PATH" && uv run <command>              # Run command in environment

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

## Configuration

### Backend Configuration
- Settings in `app/core/config.py` using Pydantic
- Environment variables in `.env` file
- Database: PostgreSQL with SQLAlchemy ORM
- Authentication: Keycloak integration

### Frontend Configuration
- Vite configuration in `vite.config.ts`
- TypeScript strict mode enabled
- ESLint + Prettier for code formatting
- Tailwind CSS for styling

## Quality Standards
- API Response Time: <200ms
- Test Coverage: >80%
- Concurrent Users: 1000+
- Error Handling: Required for all functions
- Type Safety: Strict TypeScript and mypy

## Key Development Notes

### Python Environment - CRITICAL RULES
1. **MANDATORY PATH Setup**: EVERY uv command MUST start with `export PATH="/root/.local/bin:$PATH" &&`
2. **Always use `uv run` prefix** for Python commands
3. **Never use `pip`** or virtual environment activation
4. **Python 3.13 required**

### uv Command Pattern
```bash
# ALWAYS use this pattern:
export PATH="/root/.local/bin:$PATH" && uv run <command>

# Examples:
export PATH="/root/.local/bin:$PATH" && uv run pytest tests/
export PATH="/root/.local/bin:$PATH" && uv run uvicorn app.main:app --reload
export PATH="/root/.local/bin:$PATH" && uv add fastapi
```

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

## Essential Environment Setup

### Critical: uv PATH Configuration
**MANDATORY**: Before executing ANY Python commands, ALWAYS set PATH for uv:

```bash
export PATH="/root/.local/bin:$PATH"
```

**Root Cause**: uv is installed in `/root/.local/bin/` but not in default PATH.

**Solution**: ALL bash commands MUST include PATH setup:
```bash
# CORRECT - Every uv command must start like this:
export PATH="/root/.local/bin:$PATH" && uv run pytest tests/

# WRONG - Never run uv commands without PATH:
uv run pytest tests/
```

### Automated PATH Setup
Add to shell profile for persistent setup:
```bash
echo 'export PATH="/root/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Common Issues

### Container Issues
If containers fail to start:
```bash
make stop-data
make start-data
make status
```

### Test Database
Backend tests use in-memory SQLite automatically configured in `tests/conftest.py`