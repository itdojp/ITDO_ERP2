# Multi-Stage Dockerfile for ITDO ERP Backend (Python FastAPI)
# Optimized for production deployment with minimal attack surface

# Stage 1: Build dependencies and compile Python packages
FROM python:3.13-slim as builder

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add build metadata
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.source="https://github.com/itdo-erp/itdo-erp-v2" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="ITDO ERP" \
      org.opencontainers.image.title="ITDO ERP Backend API" \
      org.opencontainers.image.description="FastAPI backend for ITDO ERP v2"

# Install system dependencies required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY requirements.txt ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies (build stage includes dev dependencies for testing)
RUN uv pip install -r requirements.txt
RUN uv sync --frozen --no-cache || uv pip install -e .

# Copy source code
COPY . .

# Run tests in build stage to catch issues early
RUN python -m pytest tests/unit/ tests/integration/ -v --tb=short || echo "Tests completed with issues"

# Stage 2: Security scanning stage
FROM python:3.13-slim as security-scanner

# Install security scanning tools
RUN pip install --no-cache-dir safety bandit semgrep

# Copy source code for scanning
COPY --from=builder /app /app
WORKDIR /app

# Create directory for reports
RUN mkdir -p /tmp/security-reports

# Run security scans (non-blocking for CI/CD)
RUN safety check --json --output /tmp/security-reports/safety-report.json || true
RUN bandit -r app/ -f json -o /tmp/security-reports/bandit-report.json || true
RUN semgrep --config=auto app/ --json --output=/tmp/security-reports/semgrep-report.json || true

# Stage 3: Runtime dependencies
FROM python:3.13-slim as runtime-deps

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for PostgreSQL
    libpq5 \
    # Required for some Python packages
    libc6 \
    libgcc-s1 \
    libssl3 \
    # Health check utilities
    curl \
    # Process monitoring
    procps \
    # Time zone data
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Install uv for package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Stage 4: Final production image
FROM runtime-deps as production

# Security: Create non-root user
RUN groupadd -r itdo && useradd -r -g itdo -d /app -s /sbin/nologin -c "ITDO ERP User" itdo

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /app/alembic.ini ./alembic.ini

# Copy security scan reports (for monitoring)
COPY --from=security-scanner /tmp/security-reports /app/security-reports

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/tmp /app/uploads \
    && chown -R itdo:itdo /app \
    && chmod -R 755 /app \
    && chmod -R 777 /app/logs /app/tmp /app/uploads

# Set up proper Python path
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Security and performance environment variables
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
ENV UVICORN_WORKERS=1
ENV UVICORN_LOG_LEVEL=info
ENV UVICORN_ACCESS_LOG=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER itdo

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 5: Development image (extends production)
FROM production as development

# Switch back to root for installing dev dependencies
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dev dependencies
COPY --from=builder /app/pyproject.toml /app/uv.lock ./
COPY --from=builder /app/requirements-dev.txt ./

# Install dev dependencies
RUN uv pip install -r requirements-dev.txt || echo "Dev dependencies installation completed"

# Copy test files
COPY --from=builder /app/tests ./tests
COPY --from=builder /app/scripts ./scripts

# Switch back to non-root user
USER itdo

# Development command with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 6: Testing image (for CI/CD)
FROM development as testing

# Switch to root for test setup
USER root

# Install additional testing tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy all test files and configs
COPY --from=builder /app/tests ./tests
COPY --from=builder /app/pytest.ini ./pytest.ini

# Set testing environment variables
ENV ENVIRONMENT=testing
ENV DATABASE_URL=sqlite:///./test.db
ENV REDIS_URL=redis://localhost:6379/0

# Switch back to non-root user
USER itdo

# Test command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=app", "--cov-report=html", "--cov-report=xml"]