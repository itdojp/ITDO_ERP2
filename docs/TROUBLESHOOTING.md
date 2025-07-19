# Troubleshooting Guide

## Common Issues and Solutions

### 1. CI/CD Pipeline Failures

#### Backend Test Failures

**Problem**: Backend tests fail with database connection errors
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Solution**:
1. Check PostgreSQL service status in CI
2. Verify database URL configuration
3. Ensure database migrations are run

```bash
# In CI workflow
- name: Wait for PostgreSQL
  run: |
    timeout 60 bash -c 'until nc -z localhost 5432; do sleep 2; done'

- name: Run migrations
  run: |
    cd backend
    uv run alembic upgrade head
```

#### Frontend Test Failures

**Problem**: Frontend tests fail with module not found errors
```
Cannot resolve module '@/components/...'
```

**Solution**:
1. Check Vite configuration for path aliases
2. Verify TypeScript configuration
3. Ensure all dependencies are installed

```typescript
// vite.config.ts
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### E2E Test Failures

**Problem**: E2E tests timeout or fail to connect to services
```
Error: page.goto: net::ERR_CONNECTION_REFUSED
```

**Solution**:
1. Verify services are running and healthy
2. Check port configuration
3. Add proper health checks

```bash
# Health check example
- name: Backend health check
  run: |
    for i in {1..60}; do
      if curl -f http://localhost:8000/health; then
        break
      fi
      sleep 2
    done
```

### 2. Local Development Issues

#### Backend Issues

**Problem**: `uv` command not found
```bash
uv: command not found
```

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Or add to your shell profile
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

**Problem**: Database connection errors locally
```
sqlalchemy.exc.OperationalError: connection to server failed
```

**Solution**:
1. Start data layer services:
   ```bash
   make start-data
   # or
   podman-compose -f infra/compose-data.yaml up -d
   ```

2. Check connection settings in `.env`:
   ```bash
   DATABASE_URL=postgresql://itdo_user:itdo_password@localhost:5432/itdo_erp
   ```

#### Frontend Issues

**Problem**: Node.js version mismatch
```
The engine "node" is incompatible with this module
```

**Solution**:
```bash
# Check Node.js version
node --version

# Install correct version (18 or higher)
nvm install 18
nvm use 18
```

**Problem**: TypeScript compilation errors
```
error TS2307: Cannot find module
```

**Solution**:
1. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Check TypeScript configuration:
   ```bash
   npm run typecheck
   ```

### 3. CORS Configuration Issues

**Problem**: CORS errors in browser console
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution**:
1. Check backend CORS configuration:
   ```python
   # backend/app/core/config.py
   BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
       "http://localhost:3000",
       "http://127.0.0.1:3000"
   ]
   ```

2. Verify environment variables:
   ```bash
   # .env file
   BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

### 4. Docker/Podman Issues

**Problem**: Container fails to start
```
Error: unable to start container: OCI runtime error
```

**Solution**:
1. Check container logs:
   ```bash
   podman logs <container-name>
   ```

2. Verify port availability:
   ```bash
   netstat -tulpn | grep :5432
   ```

3. Clean up containers:
   ```bash
   make stop-data
   podman system prune -f
   make start-data
   ```

### 5. Test Data Issues

**Problem**: E2E tests fail due to missing test data
```
Test user not found
```

**Solution**:
1. Run test data setup:
   ```bash
   cd backend
   uv run python scripts/setup_test_data.py
   ```

2. Check database for test data:
   ```sql
   SELECT * FROM users WHERE email = 'test@example.com';
   ```

### 6. Performance Issues

**Problem**: Slow test execution
```
Tests taking longer than expected
```

**Solution**:
1. Run tests in parallel:
   ```bash
   # Backend
   uv run pytest -n auto

   # Frontend
   npm run test -- --run
   ```

2. Optimize database queries
3. Use test doubles for external services

### 7. Type Checking Issues

**Problem**: mypy type checking failures
```
error: Incompatible types in assignment
```

**Solution**:
1. Add proper type annotations:
   ```python
   def function_name(param: str) -> Dict[str, Any]:
       return {"key": "value"}
   ```

2. Use type ignores sparingly:
   ```python
   result = some_function()  # type: ignore
   ```

3. Check mypy configuration:
   ```ini
   [tool.mypy]
   strict = true
   ```

### 8. Security Scan Issues

**Problem**: Security vulnerabilities detected
```
High severity vulnerability found
```

**Solution**:
1. Update dependencies:
   ```bash
   # Backend
   uv sync --upgrade

   # Frontend
   npm audit fix
   ```

2. Review and fix vulnerabilities:
   ```bash
   # Check security report
   npm audit
   uv run safety check
   ```

### 9. Environment Configuration

**Problem**: Environment variables not loading
```
KeyError: 'SECRET_KEY'
```

**Solution**:
1. Check `.env` file exists and is properly formatted
2. Verify environment loading:
   ```python
   from app.core.config import settings
   print(settings.SECRET_KEY)
   ```

3. Use `.env.example` as template:
   ```bash
   cp .env.example .env
   ```

### 10. Git and Version Control

**Problem**: Merge conflicts in package files
```
CONFLICT (content): Merge conflict in package-lock.json
```

**Solution**:
1. Delete lock file and reinstall:
   ```bash
   rm package-lock.json
   npm install
   git add package-lock.json
   ```

2. For Python dependencies:
   ```bash
   uv sync
   git add uv.lock
   ```

## Debugging Techniques

### 1. Logging and Debug Output

```python
# Backend debugging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

```typescript
// Frontend debugging
console.log('Debug info:', data);
console.table(arrayData);
```

### 2. Database Debugging

```bash
# Connect to development database
PGPASSWORD=itdo_password psql -h localhost -U itdo_user -d itdo_erp

# Check table contents
\dt
SELECT * FROM users LIMIT 5;
```

### 3. Network Debugging

```bash
# Check service connectivity
curl -v http://localhost:8000/health
curl -v http://localhost:3000

# Check open ports
netstat -tulpn | grep :8000
```

### 4. Container Debugging

```bash
# Enter running container
podman exec -it container_name bash

# Check container logs
podman logs container_name --follow
```

## Getting Help

### 1. Documentation Resources

- Project README.md
- API documentation
- Component documentation
- Architecture diagrams

### 2. Team Resources

- Code review feedback
- Team knowledge sharing sessions
- Pair programming sessions
- Architecture discussions

### 3. External Resources

- FastAPI documentation
- React documentation
- Playwright documentation
- PostgreSQL documentation

### 4. Issue Reporting

When reporting issues:

1. **Provide context**: What were you trying to do?
2. **Include error messages**: Full stack traces
3. **Share relevant code**: Minimal reproduction case
4. **Environment details**: OS, versions, configuration
5. **Steps to reproduce**: Clear, numbered steps

---

*Last updated: Phase 2 Sprint 2 Day 3*