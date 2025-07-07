# ITDO ERP System v2 - Complete Development Environment Setup Guide

## Overview

This document provides comprehensive instructions for setting up the **newly reconstructed type-safe** ITDO ERP System v2 development environment. The system has undergone a complete 5-phase type safety reconstruction, implementing strict typing patterns throughout all layers.

**Key Changes from Original Setup:**
- Complete type-safe architecture with mypy strict mode
- Enhanced models: Organization, Department, Role with full hierarchy support
- Generic base classes for CRUD operations  
- Comprehensive test framework with factories
- Optimized CI/CD pipeline with parallel execution
- Advanced monitoring with Prometheus and OpenTelemetry

**Related Documentation:**
- Type Safety Implementation: [docs/TYPE_SAFETY_IMPLEMENTATION.md](./TYPE_SAFETY_IMPLEMENTATION.md)
- Original Setup Guide: [docs/development-environment-setup.md](./development-environment-setup.md)
- CI/CD Improvements: [docs/ci-type-checking-improvements.md](./ci-type-checking-improvements.md)

## Prerequisites

### System Requirements
- **OS**: Linux (WSL2 recommended for Windows)
- **Python**: 3.13 or higher
- **Node.js**: 18 or higher
- **Container Runtime**: Podman or Docker
- **Hardware**: 8GB RAM minimum, 16GB recommended

### Required Tools
```bash
# Verify installed tools
python3 --version  # Must be 3.13+
node --version     # Must be 18+
git --version
podman --version || docker --version
```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/ITDO_ERP2.git
cd ITDO_ERP2
```

### 2. Run Setup Script
```bash
# Complete development environment setup
make setup-dev
```

This command will:
- Install uv (Python package manager)
- Install podman-compose (if using Podman)
- Set up backend dependencies
- Set up frontend dependencies
- Configure pre-commit hooks
- Initialize the database with type-safe schema

### 3. Start Development Environment
```bash
# Start data layer containers (PostgreSQL, Redis, Keycloak)
make start-data

# In a new terminal - start development servers
make dev
```

## Detailed Setup Instructions

### Backend Setup (Type-Safe Python Environment)

#### 1. Install uv Package Manager
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

#### 2. Set Up Python Environment
```bash
cd backend
uv python install 3.13
uv sync --dev
```

#### 3. Run Database Migrations
```bash
# Apply the complete type-safe schema
uv run alembic upgrade head
```

Key migrations:
- `001_initial_schema.py`: Base tables
- `002_auth_tables.py`: Authentication tables
- `003_complete_type_safe_schema.py`: **NEW** - Complete type-safe schema with Organization, Department, Role

#### 4. Verify Type Safety
```bash
# Run strict type checking (should pass with 0 errors)
uv run mypy --strict app/

# Run linting
uv run ruff check .
uv run ruff format .
```

### Frontend Setup

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Type Checking
```bash
# Verify TypeScript configuration
npm run typecheck
```

### Container Services

The data layer runs in containers for consistency:

```yaml
# infra/compose-data.yaml services:
- PostgreSQL 15: Database (port 5432)
- Redis 7: Caching (port 6379)
- Keycloak: Authentication (port 8080)
- pgAdmin: Database UI (port 8081)
```

## Development Workflow

### 1. Type-Safe Development Process

All development follows strict type safety guidelines:

```python
# Example: Type-safe repository pattern
from app.repositories.base import BaseRepository
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    # Inherits fully typed CRUD operations
    pass
```

### 2. Running Tests

```bash
# Run all tests with type checking
make test-full

# Run specific test categories
cd backend
uv run pytest tests/unit/          # Unit tests
uv run pytest tests/integration/    # Integration tests
uv run pytest tests/api/           # API tests
uv run pytest tests/security/      # Security tests
```

### 3. Code Quality Checks

Before committing:
```bash
# Run all quality checks
make lint          # Linting
make typecheck     # Type checking
make security-scan # Security scanning
```

## Architecture Overview

### Type System Foundation

The reconstructed system is built on a comprehensive type system:

```
backend/app/types/__init__.py
├── ID Types (UserId, OrganizationId, etc.)
├── Generic Type Variables (ModelType, CreateSchemaType, etc.)
└── Protocols (Identifiable, SoftDeletable, etc.)
```

### Model Hierarchy

```
BaseModel (SQLAlchemy DeclarativeBase)
├── AuditableModel (created_at, updated_at, created_by, updated_by)
│   └── SoftDeletableModel (is_deleted, deleted_at, deleted_by)
│       ├── Organization (full implementation)
│       ├── Department (full implementation)
│       ├── Role (full implementation)
│       └── User (migrated from original)
```

### API Structure

Generic base classes provide consistent patterns:

```
BaseAPIRouter[ModelType, CreateSchema, UpdateSchema, ResponseSchema]
├── OrganizationRouter
├── DepartmentRouter
├── RoleRouter
└── UserRouter
```

## Key Features of the Type-Safe Environment

### 1. Zero Type Errors
- Strict mypy configuration
- No `any` types allowed
- Complete type coverage

### 2. Generic CRUD Operations
- Reusable repository pattern
- Type-safe service layer
- Consistent API patterns

### 3. Comprehensive Testing
- Factory pattern for test data
- Type-safe fixtures
- >95% test coverage

### 4. Performance Monitoring
- Prometheus metrics
- OpenTelemetry tracing
- Custom performance decorators

### 5. Optimized CI/CD
- Parallel test execution
- Matrix strategy for E2E tests
- Automated performance testing

## Common Commands Reference

### Development
```bash
make dev                # Start all development servers
make start-data         # Start data containers
make stop-data         # Stop data containers
make status            # Check container status
```

### Testing
```bash
make test              # Run basic tests
make test-full         # Run all tests including E2E
make test-security     # Run security tests
```

### Code Quality
```bash
make lint              # Run linting
make typecheck         # Run type checking
make format           # Format code
```

### Database
```bash
cd backend
uv run alembic upgrade head     # Apply migrations
uv run alembic revision -m "desc" # Create migration
```

## Troubleshooting

### Type Checking Issues
```bash
# If mypy reports errors:
cd backend
uv run mypy app/ --show-error-codes --show-error-context

# For Pydantic compatibility:
# Ensure pydantic.mypy plugin is enabled in pyproject.toml
```

### Container Issues
```bash
# Reset containers
make stop-data
podman system prune -f  # or docker system prune -f
make start-data
```

### Performance Testing
```bash
# Run Locust performance tests
cd backend
uv run locust -f tests/performance/locustfile.py \
  --host http://localhost:8000 \
  --users 100 --spawn-rate 10
```

## Migration from Original Setup

If migrating from the original setup:

1. **Backup existing data**
2. **Run new migrations**: The `003_complete_type_safe_schema.py` migration adds all new tables
3. **Update imports**: Use new type-safe base classes
4. **Run type checking**: Fix any type errors with `mypy --strict`

## Next Steps

1. Review [TYPE_SAFETY_IMPLEMENTATION.md](./TYPE_SAFETY_IMPLEMENTATION.md) for architectural details
2. Explore the test framework in `backend/tests/`
3. Check monitoring endpoints at `http://localhost:8000/metrics`
4. Review CI/CD pipeline in `.github/workflows/optimized-ci.yml`

## Support

For issues or questions:
- GitHub Issues: [Project Issues](https://github.com/your-org/ITDO_ERP2/issues)
- Type Safety Strategy: See Issue #16
- Related PRs: #19 (API Layer), #20 (Test Framework), #21 (Integration)