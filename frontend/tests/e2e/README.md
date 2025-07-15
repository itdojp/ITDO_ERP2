# E2E Testing with Playwright

## Overview

This directory contains end-to-end tests using Playwright for the ITDO ERP system.

## Structure

```
tests/e2e/
├── auth/              # Authentication flow tests
├── users/             # User management tests
├── organizations/     # Organization management tests
├── fixtures/          # Test fixtures and helpers
├── pages/             # Page object models
└── README.md          # This file
```

## Running Tests

### Local Execution

```bash
# Run all tests
npm run test:e2e

# Run tests with UI (headed mode)
npm run test:e2e:headed

# Run specific test file
npm run test:e2e auth/login.spec.ts

# Run tests for specific browser
npm run test:e2e -- --project=chromium
npm run test:e2e -- --project=firefox
npm run test:e2e -- --project=webkit

# Run tests in debug mode
npm run test:e2e -- --debug

# Run tests with specific tags
npm run test:e2e -- --grep @smoke
npm run test:e2e -- --grep @critical
```

### Debugging

```bash
# Debug mode with Playwright Inspector
npx playwright test --debug

# View trace after test failure
npx playwright show-trace trace.zip

# Generate and view HTML report
npm run test:e2e -- --reporter=html
npx playwright show-report
```

## Test Categories

### Authentication Tests (`auth/`)
- **login.spec.ts**: Login flow testing (5 test cases)
- **logout.spec.ts**: Logout flow testing (4 test cases)
- **session.spec.ts**: Session management testing (5 test cases)

### User Management Tests (`users/`)
- **user-crud.spec.ts**: User CRUD operations (8 test cases)
  - Display user list with pagination
  - Create new user
  - Edit existing user
  - Delete user with confirmation
  - Search users by name and email
  - Filter users by role
  - Bulk actions on multiple users
  - Form validation errors

### Organization Management Tests (`organizations/`)
- **org-management.spec.ts**: Organization hierarchy and permissions (8 test cases)
  - Display organization hierarchy
  - Create new organization
  - Create department under organization
  - Edit organization details
  - Manage organization permissions
  - Move department to different organization
  - Delete organization with confirmation
  - Search and filter organizations

## Writing Tests

### Best Practices

1. **Page Object Model Pattern**
   ```typescript
   // pages/user.page.ts
   export class UserPage {
     constructor(private page: Page) {}
     
     async createUser(userData: UserData) {
       // Implementation
     }
   }
   ```

2. **Test Independence**
   - Each test should be able to run independently
   - Use `beforeEach` for common setup
   - Clean up test data in `afterEach`

3. **Use Fixtures**
   ```typescript
   import { test } from '../fixtures/auth.fixture';
   
   test('authenticated test', async ({ authenticatedPage }) => {
     // Test with pre-authenticated page
   });
   ```

4. **Explicit Waits**
   ```typescript
   // Good
   await page.waitForSelector('.user-list');
   
   // Avoid
   await page.waitForTimeout(5000);
   ```

5. **Meaningful Assertions**
   ```typescript
   await expect(page.locator('.toast')).toContainText('User created successfully');
   ```

### Test Data Management

- Use unique identifiers for test data (e.g., timestamps)
- Clean up created test data after tests
- Use test-specific email addresses: `test${Date.now()}@example.com`

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Daily scheduled runs at 2 AM UTC

### GitHub Actions Workflow

The E2E tests are integrated into the CI/CD pipeline with:
- Multi-browser testing (Chromium, Firefox, WebKit)
- Parallel execution for faster feedback
- Automatic retry on failures (2 retries in CI)
- Screenshot capture on failures
- Test report generation

### Artifacts

The following artifacts are uploaded after each test run:
- HTML test reports
- Screenshots on failure
- Video recordings on failure
- Trace files for debugging

## Environment Variables

```bash
# Base URL for the application
BASE_URL=http://localhost:3000

# API URL for backend
API_URL=http://localhost:8000

# Test user credentials
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=password123
TEST_ADMIN_EMAIL=admin@example.com
TEST_ADMIN_PASSWORD=admin123
```

## Troubleshooting

### Common Issues

1. **Browser not installed**
   ```bash
   npx playwright install
   ```

2. **Port already in use**
   - Check if dev server is running on port 3000
   - Kill the process: `lsof -ti:3000 | xargs kill -9`

3. **Flaky tests**
   - Increase timeout in playwright.config.ts
   - Add explicit waits for elements
   - Check for race conditions

### Getting Help

- Playwright Documentation: https://playwright.dev
- Project Issues: https://github.com/itdojp/ITDO_ERP2/issues