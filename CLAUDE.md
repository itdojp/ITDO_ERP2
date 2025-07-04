# Claude Code Project Configuration

## Required Reading Files

Before starting any development work, Claude Code must read and understand the following files:

1. `.claude/PROJECT_CONTEXT.md` - Project context and business domain knowledge
2. `.claude/DEVELOPMENT_WORKFLOW.md` - Detailed development workflow and process
3. `.claude/CODING_STANDARDS.md` - Coding standards and quality requirements
4. `.claude/TECHNICAL_CONSTRAINTS.md` - Technical constraints and limitations

## Project Overview

ITDO ERP System v2 - Modern ERP system with hybrid development environment.

**Technology Stack:**
- Backend: Python 3.11 + FastAPI + uv
- Frontend: React 18 + TypeScript 5 + Vite  
- Database: PostgreSQL 15 + Redis 7
- Auth: Keycloak (OAuth2/OpenID Connect)
- Container: Podman (Hybrid configuration)

## Critical Development Rules

### MANDATORY CONSTRAINTS
1. **Test-Driven Development (TDD)**: Write tests BEFORE implementation (REQUIRED)
2. **Issue-Driven Development**: All work starts from GitHub Issues
3. **Type Safety**: No `any` types allowed, strict type checking required
4. **Hybrid Environment**: Data layer in containers, development layer local (recommended)
5. **uv Tool Usage**: Python environment management (NO pip/activate)

### DEVELOPMENT PROCESS (8 Phases)
1. Issue Confirmation → 2. Draft PR Creation → 3. Specification Creation → 
4. Test Specification → 5. Test Code Implementation → 6. Implementation → 
7. Documentation Update → 8. Review Preparation

### QUALITY STANDARDS
- API Response Time: <200ms
- Test Coverage: >80%  
- Concurrent Users: 1000+
- Error Handling: Required for all functions

## Essential Commands

```bash
# Data Layer (Always containers)
podman-compose -f infra/compose-data.yaml up -d

# Development (Local recommended)
cd backend && uv run uvicorn app.main:app --reload
cd frontend && npm run dev

# Testing
cd backend && uv run pytest
cd frontend && npm test

# Type Checking
cd backend && uv run mypy --strict .
cd frontend && npm run typecheck
```

## Development Prompt Template

When starting development work, use this exact prompt:

```
Read the following configuration files first:
- .claude/PROJECT_CONTEXT.md
- .claude/DEVELOPMENT_WORKFLOW.md  
- .claude/CODING_STANDARDS.md
- .claude/TECHNICAL_CONSTRAINTS.md

Then implement Issue #[number] following the 8-phase development workflow:
- Use hybrid development environment
- Follow TDD strictly (tests before implementation)
- Ensure all constraints and standards are met
```