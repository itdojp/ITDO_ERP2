# ITDO ERP System v2 - System Architecture Documentation

## 📋 Overview

ITDO ERP System v2 is a modern, cloud-native Enterprise Resource Planning system built with scalability, security, and maintainability in mind. This document provides a comprehensive overview of the system architecture, design decisions, and implementation patterns.

## 📊 System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  React 18 + TypeScript 5 + Vite + Tailwind CSS + Vitest      │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTP/HTTPS
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI + Python 3.13 + Pydantic + SQLAlchemy 2.0 + uv      │
└─────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Modules                          │
├─────────────────────────────────────────────────────────────────┤
│  Financial  │  Project  │  Resource  │  Inventory  │   Sales   │
│ Management  │ Management│ Management │ Management  │ Management │
└─────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL 15  │    Redis 7     │   Keycloak    │   pgAdmin   │
│  (Primary DB)   │   (Caching)    │  (Auth/IAM)   │  (DB Admin) │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Backend Stack
- **Runtime**: Python 3.13
- **Framework**: FastAPI (async/await support)
- **Package Manager**: uv (ultra-fast Python package installer)
- **Database ORM**: SQLAlchemy 2.0 with Mapped types
- **Schema Validation**: Pydantic v2
- **Authentication**: Keycloak (OAuth2/OpenID Connect)
- **Caching**: Redis 7
- **Testing**: pytest + pytest-asyncio

#### Frontend Stack  
- **Framework**: React 18 with Hooks and Concurrent Features
- **Language**: TypeScript 5 (strict mode)
- **Build Tool**: Vite (fast HMR)
- **Styling**: Tailwind CSS + CSS Modules
- **Testing**: Vitest + React Testing Library
- **State Management**: Context API + Custom Hooks

#### Infrastructure Stack
- **Database**: PostgreSQL 15 (containerized)
- **Cache**: Redis 7 (containerized)
- **Auth Provider**: Keycloak (containerized)
- **Container Runtime**: Podman (data layer only)
- **CI/CD**: GitHub Actions
- **Monitoring**: OpenTelemetry ready

## 🏗️ Design Patterns & Principles

### Clean Architecture Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Routers + Pydantic Schemas + HTTP Exception Handlers  │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Business Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  Services + Use Cases + Domain Logic + Business Rules          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Access Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  SQLAlchemy Models + Repositories + Database Abstractions      │
└─────────────────────────────────────────────────────────────────┘
```

### Core Design Principles

1. **Separation of Concerns**: Clear boundaries between layers
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Single Responsibility**: Each class/function has one reason to change
4. **Domain-Driven Design**: Business logic encapsulated in domain services
5. **API-First Design**: OpenAPI-driven development with automatic documentation

## 📂 Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   └── v1/                    # API version 1 endpoints
│   │       ├── __init__.py
│   │       ├── router.py          # Main API router
│   │       ├── auth.py            # Authentication endpoints
│   │       ├── health.py          # Health check endpoints
│   │       ├── users.py           # User management
│   │       ├── organizations.py   # Organization management
│   │       ├── departments.py     # Department management
│   │       ├── projects.py        # Project management
│   │       ├── tasks.py           # Task management
│   │       ├── resources.py       # Resource management
│   │       ├── financial.py       # Financial management
│   │       └── inventory.py       # Inventory management
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Application configuration
│   │   ├── database.py           # Database connection/session
│   │   ├── security.py           # Security utilities
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── middleware.py         # Custom middleware
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py              # Base model class
│   │   ├── user.py              # User model
│   │   ├── organization.py      # Organization model
│   │   ├── department.py        # Department model
│   │   ├── project.py           # Project model
│   │   ├── task.py              # Task model
│   │   ├── resource.py          # Resource model
│   │   ├── financial.py         # Financial models
│   │   └── inventory.py         # Inventory models
│   ├── schemas/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py             # User schemas
│   │   ├── organization.py     # Organization schemas
│   │   ├── department.py       # Department schemas
│   │   ├── project.py          # Project schemas
│   │   ├── task.py             # Task schemas
│   │   ├── resource.py         # Resource schemas
│   │   ├── financial.py        # Financial schemas
│   │   └── inventory.py        # Inventory schemas
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── user.py            # User business logic
│   │   ├── organization.py    # Organization business logic
│   │   ├── department.py      # Department business logic
│   │   ├── project.py         # Project business logic
│   │   ├── task.py            # Task business logic
│   │   ├── resource.py        # Resource business logic
│   │   ├── financial.py       # Financial business logic
│   │   └── inventory.py       # Inventory business logic
│   └── utils/                 # Utility modules
│       ├── __init__.py
│       ├── cache.py          # Caching utilities
│       ├── security.py       # Security utilities
│       └── validators.py     # Custom validators
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   ├── performance/         # Performance tests
│   └── conftest.py         # Test configuration
├── docs/                   # Documentation
├── scripts/               # Utility scripts
├── alembic/              # Database migrations
├── requirements.txt      # Python dependencies (legacy)
├── pyproject.toml       # Modern Python project configuration
└── Makefile            # Development commands
```

### Frontend Structure
```
frontend/
├── src/
│   ├── main.tsx              # Application entry point
│   ├── App.tsx               # Root component
│   ├── components/           # Reusable UI components
│   │   ├── common/          # Common components
│   │   ├── forms/           # Form components
│   │   ├── layout/          # Layout components
│   │   └── ui/              # Basic UI components
│   ├── pages/               # Page components
│   │   ├── auth/           # Authentication pages
│   │   ├── dashboard/      # Dashboard pages
│   │   ├── projects/       # Project management pages
│   │   ├── tasks/          # Task management pages
│   │   ├── resources/      # Resource management pages
│   │   ├── financial/      # Financial management pages
│   │   └── inventory/      # Inventory management pages
│   ├── services/           # API client and utilities
│   │   ├── api/           # API client
│   │   ├── auth/          # Authentication service
│   │   └── utils/         # Utility functions
│   ├── hooks/             # Custom React hooks
│   ├── contexts/          # React contexts
│   ├── types/             # TypeScript type definitions
│   ├── test/              # Test utilities and setup
│   └── assets/            # Static assets
├── public/                # Public assets
├── tests/                 # Frontend tests
├── package.json          # Node.js dependencies
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
└── tailwind.config.js    # Tailwind CSS configuration
```

## 🔒 Security Architecture

### Authentication & Authorization

1. **Identity Provider**: Keycloak (OAuth2/OpenID Connect)
   - Centralized user management
   - Role-based access control (RBAC)
   - Multi-factor authentication support
   - Single sign-on (SSO) capability

2. **API Security**:
   - JWT token-based authentication
   - Token refresh mechanism
   - Role and permission validation
   - Rate limiting and throttling

3. **Data Protection**:
   - Encryption at rest (database level)
   - Encryption in transit (TLS/HTTPS)
   - Sensitive data masking in logs
   - GDPR compliance features

### Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  HTTPS + CSP + CORS + JWT Token Management                     │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Rate Limiting + Input Validation + Authentication + RBAC      │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  Permission Checks + Business Rules + Audit Logging            │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Access Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  SQL Injection Protection + ORM + Database Security            │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Data Architecture

### Database Design

#### Core Entities
- **Organizations**: Multi-tenant support
- **Users**: User management with RBAC
- **Departments**: Hierarchical organization structure
- **Projects**: Project lifecycle management
- **Tasks**: Task management with dependencies
- **Resources**: Human and material resource tracking
- **Financial**: Comprehensive financial management
- **Inventory**: Stock and warehouse management

#### Relationships
```
Organization (1) ←→ (N) Department
Organization (1) ←→ (N) User
Organization (1) ←→ (N) Project
Department   (1) ←→ (N) User
Project      (1) ←→ (N) Task
User         (1) ←→ (N) Task (assignee)
Project      (1) ←→ (N) Resource Allocation
```

### Caching Strategy

1. **Application Cache** (Redis):
   - Session storage
   - API response caching
   - Database query result caching
   - Real-time data caching

2. **Database Cache**:
   - Query plan caching
   - Index optimization
   - Connection pooling

## 🚀 Performance Architecture

### Optimization Strategies

1. **Backend Optimization**:
   - Async/await for I/O operations
   - Database query optimization
   - Connection pooling
   - Response caching
   - Background task processing

2. **Frontend Optimization**:
   - Code splitting and lazy loading
   - Tree shaking and bundle optimization
   - Image optimization
   - Service workers for caching

3. **Database Optimization**:
   - Proper indexing strategy
   - Query optimization
   - Database partitioning
   - Read replicas for scaling

### Monitoring & Observability

1. **Application Monitoring**:
   - Performance metrics collection
   - Error tracking and logging
   - API response time monitoring
   - Resource utilization tracking

2. **Business Metrics**:
   - User activity tracking
   - Feature usage analytics
   - Business KPI monitoring
   - Real-time dashboard updates

## 🔄 Integration Architecture

### Module Integration

1. **Financial Integration**:
   - Cross-module financial tracking
   - Real-time cost calculation
   - Revenue recognition
   - Budget monitoring

2. **Project-Resource Integration**:
   - Resource allocation tracking
   - Capacity planning
   - Cost attribution
   - Utilization reporting

3. **Inventory-Sales Integration**:
   - Stock level monitoring
   - Automated reordering
   - Sales impact on inventory
   - Financial impact tracking

### External Integration Points

1. **Authentication**: Keycloak SSO
2. **Database**: PostgreSQL with connection pooling
3. **Caching**: Redis for session and data caching
4. **Monitoring**: OpenTelemetry-ready instrumentation
5. **CI/CD**: GitHub Actions integration

## 📈 Scalability Architecture

### Horizontal Scaling
- Stateless application design
- Load balancer ready
- Database read replicas
- Microservice-ready modular design

### Vertical Scaling
- Efficient resource utilization
- Memory optimization
- CPU-efficient algorithms
- I/O optimization

## 🛠️ Development Architecture

### Development Workflow
1. **Issue-Driven Development**: All work starts from GitHub Issues
2. **Feature Branching**: `feature/issue-{number}-description`
3. **Test-Driven Development**: Write tests before implementation
4. **Code Review**: Pull request review process
5. **Continuous Integration**: Automated testing and quality checks

### Quality Assurance
1. **Code Quality**: ESLint, Prettier, Ruff, mypy
2. **Testing**: Unit, integration, E2E, performance tests
3. **Security**: SAST, dependency scanning, security audits
4. **Performance**: Load testing, performance monitoring

## 📚 API Architecture

### RESTful API Design
- Resource-based URLs
- HTTP method semantics
- Status code standards
- Pagination support
- Filtering and sorting

### API Versioning
- URL-based versioning (`/api/v1/`)
- Backward compatibility
- Deprecation strategy
- Migration guides

### API Documentation
- OpenAPI 3.0 specification
- Interactive API documentation
- Code examples
- Authentication guides

## 🔮 Future Architecture Considerations

### Planned Enhancements
1. **Microservices Migration**: Gradual decomposition into microservices
2. **Event-Driven Architecture**: Implement event sourcing for audit trails
3. **Cloud Native**: Kubernetes deployment with auto-scaling
4. **AI/ML Integration**: Predictive analytics and intelligent automation
5. **Real-time Features**: WebSocket support for real-time updates

### Technology Evolution
- GraphQL API layer for complex queries
- Serverless functions for specific workflows
- Container orchestration with Kubernetes
- Message queues for async processing
- Advanced monitoring with distributed tracing

---

## 📝 Document Information

- **Version**: 1.0
- **Last Updated**: 2025-01-26
- **Maintained By**: ITDO ERP Development Team
- **Review Cycle**: Quarterly

---

*This document is part of the ITDO ERP System v2 technical documentation suite.*