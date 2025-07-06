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
# IMPORTANT: Always set PATH for uv
export PATH="/root/.local/bin:$PATH"

# Install dependencies
uv venv
uv sync

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration
```

## Run

```bash
# IMPORTANT: Always set PATH for uv
export PATH="/root/.local/bin:$PATH"

# Start data layer (PostgreSQL, Redis)
make start-data
# or: podman-compose -f ../infra/compose-data.yaml up -d

# Run migrations (when available)
# uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

When the server is running, you can access:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

### Available Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

#### User Management
- `GET /api/v1/users/me` - Get current user info
- `PATCH /api/v1/users/me` - Update current user

#### Dashboard (NEW)
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/progress` - Get progress data
- `GET /api/v1/dashboard/alerts` - Get alerts and notifications

#### Progress Management (NEW)
- `GET /api/v1/projects/{project_id}/progress` - Get project progress details
- `GET /api/v1/projects/{project_id}/report` - Generate progress report (JSON/CSV)

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
# IMPORTANT: Always set PATH for uv
export PATH="/root/.local/bin:$PATH"

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_security.py -v

# Run dashboard/progress tests
uv run pytest tests/test_dashboard_progress/ -v

# Run with type checking
uv run mypy --strict app/
```

## Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   │   └── v1/        # API version 1
│   │       ├── auth.py      # Authentication endpoints
│   │       ├── users.py     # User management
│   │       ├── dashboard.py # Dashboard statistics (NEW)
│   │       └── progress.py  # Progress management (NEW)
│   ├── core/          # Core utilities
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   │   ├── dashboard.py     # Dashboard schemas (NEW)
│   │   └── ...
│   ├── services/      # Business logic
│   │   ├── dashboard.py     # Dashboard service (NEW)
│   │   ├── progress.py      # Progress service (NEW)
│   │   └── ...
│   └── main.py        # Application entry point
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   ├── security/      # Security tests
│   └── test_dashboard_progress/  # Dashboard/Progress tests (NEW)
│       ├── unit/
│       ├── integration/
│       └── security/
├── docs/              # Documentation
│   ├── dashboard-progress-specification.md
│   └── dashboard-progress-test-specification.md
├── alembic/           # Database migrations
├── pyproject.toml     # Project configuration
└── requirements.txt   # Dependencies
```

## Development Guidelines

1. **TDD (Test-Driven Development)**: Write tests first
2. **Type Safety**: Use type hints, run mypy with --strict
3. **Code Quality**: Use ruff for linting and formatting
4. **Security First**: Validate all inputs, use proper authentication

## Security

- Passwords are hashed using bcrypt
- JWT tokens expire after 24 hours
- All endpoints require authentication except login
- Input validation on all requests
- SQL injection protection via SQLAlchemy ORM