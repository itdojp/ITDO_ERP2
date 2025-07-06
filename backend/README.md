# ITDO ERP Backend

FastAPI based backend for ITDO ERP System.

## Technology Stack

- **Python 3.13** - Programming language
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Redis** - Cache/Session storage
- **JWT** - Authentication
- **uv** - Package management

## Setup

```bash
# Install dependencies
uv venv
uv pip sync requirements-dev.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration
```

## Run

```bash
# Start data layer (PostgreSQL, Redis)
podman-compose -f ../infra/compose-data.yaml up -d

# Run migrations (when available)
# uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

## API Documentation

When the server is running, you can access:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

### Available API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout

#### User Management
- `GET /api/v1/users/me` - Get current user
- `POST /api/v1/users` - Create user (extended)
- `GET /api/v1/users` - List users
- `PUT /api/v1/users/{id}` - Update user

#### Project Management
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects (with filters)
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

#### Task Management
- `POST /api/v1/projects/{project_id}/tasks` - Create task
- `GET /api/v1/projects/{project_id}/tasks` - List project tasks
- `GET /api/v1/tasks/{id}` - Get task details
- `PUT /api/v1/tasks/{id}` - Update task
- `PUT /api/v1/tasks/{id}/assign` - Assign task
- `DELETE /api/v1/tasks/{id}` - Delete task

## Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### Using the token
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <your-access-token>"
```

## Testing

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

## Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   │   └── v1/        # API version 1
│   │       ├── auth.py       # Authentication endpoints
│   │       ├── users.py      # User management endpoints
│   │       ├── projects.py   # Project management endpoints
│   │       └── tasks.py      # Task management endpoints
│   ├── core/          # Core utilities
│   ├── models/        # SQLAlchemy models
│   │   ├── user.py           # User model
│   │   ├── project.py        # Project model
│   │   ├── task.py           # Task model
│   │   └── ...
│   ├── schemas/       # Pydantic schemas
│   │   ├── user.py           # User schemas
│   │   ├── project.py        # Project schemas
│   │   ├── task.py           # Task schemas
│   │   └── ...
│   ├── services/      # Business logic
│   │   ├── auth.py           # Authentication service
│   │   ├── user.py           # User service
│   │   ├── project.py        # Project service
│   │   ├── task.py           # Task service
│   │   └── audit.py          # Audit service
│   └── main.py        # Application entry point
├── tests/
│   ├── unit/          # Unit tests
│   │   ├── models/           # Model tests
│   │   └── services/         # Service tests
│   ├── integration/   # Integration tests
│   │   └── api/              # API tests
│   └── security/      # Security tests
├── alembic/           # Database migrations
├── docs/              # Documentation
│   ├── project-management-specification.md
│   └── project-management-test-specification.md
├── pyproject.toml     # Project configuration
└── requirements.txt   # Dependencies
```

## Features

### Implemented Features

#### User Management
- User registration and authentication
- Multi-tenant organization support
- Role-based access control (RBAC)
- Password security (history, complexity, lockout)
- Session management
- Audit logging

#### Project Management
- Project creation and management
- Project status tracking (planning/in_progress/completed/cancelled/on_hold)
- Multi-tenant data isolation
- Date-based project scheduling
- Project soft delete with audit trail

#### Task Management
- Task creation within projects
- Task assignment to users
- Priority management (low/medium/high/urgent)
- Status tracking (not_started/in_progress/completed/on_hold)
- Estimated and actual date tracking
- Task soft delete with audit trail

### Security Features
- JWT-based authentication
- Multi-tenant data isolation
- Role-based access control
- Input validation and sanitization
- Audit logging with integrity checks
- SQL injection protection

## Development Guidelines

1. **TDD (Test-Driven Development)**: Write tests first
2. **Type Safety**: Use type hints, run mypy with --strict
3. **Code Quality**: Use ruff for linting and formatting
4. **Security First**: Validate all inputs, use proper authentication
5. **8-Phase Development**: Follow Issue → PR → Spec → Test → Code → Doc → Review

## Security

- Passwords are hashed using bcrypt
- JWT tokens expire after 24 hours
- All endpoints require authentication except login
- Input validation on all requests
- SQL injection protection via SQLAlchemy ORM