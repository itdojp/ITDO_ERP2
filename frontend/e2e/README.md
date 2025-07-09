# E2E Testing Documentation

## Overview
This directory contains End-to-End (E2E) tests for the ITDO ERP frontend application using Playwright.

## Structure
```
e2e/
├── fixtures/        # Test fixtures and helpers
│   └── auth.fixture.ts  # Authentication helpers
├── pages/          # Page Object Models
│   ├── base.page.ts     # Base page class
│   └── login.page.ts    # Login page object
├── tests/          # Test specifications
│   ├── auth/           # Authentication tests
│   │   └── login.spec.ts
│   ├── smoke/          # Smoke tests
│   │   └── app-load.spec.ts
│   └── integration/    # Integration tests
├── playwright.config.ts # Playwright configuration
├── tsconfig.json       # TypeScript configuration
└── .gitignore         # Git ignore rules
```

## Running Tests

### Prerequisites
1. Ensure the backend is running with data services:
   ```bash
   make start-data  # Start PostgreSQL, Redis, Keycloak
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   npx playwright install
   ```

### Test Commands
```bash
# Run all E2E tests
npm run e2e

# Run tests with UI mode (interactive)
npm run e2e:ui

# Run tests in debug mode
npm run e2e:debug

# Run tests in headed mode (see browser)
npm run e2e:headed

# Show test report
npm run e2e:report
```

### Running Specific Tests
```bash
# Run only smoke tests
npx playwright test smoke/

# Run only auth tests
npx playwright test auth/

# Run a specific test file
npx playwright test auth/login.spec.ts

# Run tests matching a pattern
npx playwright test -g "ログイン"
```

## Test Users
The following test users are available in `fixtures/auth.fixture.ts`:

- **Admin**: `admin@e2e.test` / `AdminPass123!`
- **Manager**: `manager@e2e.test` / `ManagerPass123!`
- **User**: `user@e2e.test` / `UserPass123!`

## Writing Tests

### Using Page Objects
```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

test('example test', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.gotoLoginPage();
  await loginPage.login('user@example.com', 'password');
  // ... assertions
});
```

### Using Authentication Fixtures
```typescript
import { test, expect } from '../fixtures/auth.fixture';

test('authenticated test', async ({ authenticatedPage }) => {
  // Page is already logged in as regular user
  await authenticatedPage.goto('/dashboard');
  // ... test code
});

test('admin test', async ({ adminPage }) => {
  // Page is already logged in as admin
  await adminPage.goto('/admin/users');
  // ... test code
});
```

## Best Practices

1. **Use data-testid attributes**: Always use `data-testid` for element selection
   ```typescript
   await page.click('[data-testid="submit-button"]');
   ```

2. **Page Object Model**: Create page objects for reusable interactions
   ```typescript
   export class DashboardPage extends BasePage {
     async clickUserMenu() {
       await this.click('[data-testid="user-menu"]');
     }
   }
   ```

3. **Wait for elements**: Always wait for elements before interacting
   ```typescript
   await page.waitForSelector('[data-testid="loading"]', { state: 'hidden' });
   ```

4. **Use fixtures**: Leverage fixtures for common setup
   ```typescript
   test('needs auth', async ({ authenticatedPage }) => {
     // Already logged in
   });
   ```

5. **Meaningful test names**: Use Japanese for clarity
   ```typescript
   test('ユーザー一覧が表示される', async ({ page }) => {
     // Test implementation
   });
   ```

## CI Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests
- Manual workflow dispatch

Test artifacts (reports, screenshots) are saved for failed tests.

## Troubleshooting

### Tests failing locally
1. Ensure all services are running: `make status`
2. Check browser installation: `npx playwright install`
3. Clear test data: `make reset-db`

### Timeout issues
Increase timeout in specific tests:
```typescript
test('slow test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // Test code
});
```

### Debug mode
Run with `--debug` flag or use `page.pause()`:
```typescript
test('debug me', async ({ page }) => {
  await page.goto('/');
  await page.pause(); // Opens inspector
});
```