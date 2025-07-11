# E2E Testing Guide

## Overview

This project uses Playwright for End-to-End (E2E) testing to ensure the application works correctly from a user's perspective.

## Test Structure

```
frontend/tests/e2e/
├── smoke/              # Basic application functionality tests
├── performance/        # Performance and load testing
├── accessibility/      # Accessibility compliance tests
├── auth/              # Authentication flow tests
├── users/             # User management tests
├── organizations/     # Organization management tests
├── departments/       # Department management tests
├── tasks/             # Task management tests
├── permissions/       # Permission system tests
├── integration/       # Cross-component integration tests
├── api/               # API integration tests
├── fixtures/          # Test fixtures and helpers
└── pages/             # Page Object Model classes
```

## Running E2E Tests

### Prerequisites

1. Ensure both backend and frontend services are running:
   ```bash
   # Terminal 1: Start backend
   cd backend
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Start frontend
   cd frontend
   npm run dev
   ```

2. Install Playwright browsers:
   ```bash
   cd frontend
   npm run e2e:install
   ```

### Running Tests

```bash
# Run all E2E tests
npm run e2e

# Run in headed mode (see browser)
npm run e2e:headed

# Run specific test file
npx playwright test tests/e2e/smoke/

# Run with UI mode
npm run e2e:ui

# Generate test report
npm run e2e:report
```

### CI/CD Execution

E2E tests run automatically in CI/CD pipelines:

- **Smoke Tests**: Run on every PR to ensure basic functionality
- **Full Test Suite**: Run on main branch and releases
- **Performance Tests**: Run nightly and on releases

## Test Categories

### 1. Smoke Tests (`/smoke/`)
- Basic application startup
- API health checks
- Critical path verification
- **Purpose**: Ensure the application is functional

### 2. Performance Tests (`/performance/`)
- Page load time measurement
- API response time testing
- Memory leak detection
- Concurrent user simulation
- **Purpose**: Ensure the application performs well under load

### 3. Accessibility Tests (`/accessibility/`)
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation
- WCAG compliance checks
- **Purpose**: Ensure the application is accessible to all users

### 4. Integration Tests (`/integration/`)
- Cross-component workflows
- End-to-end user journeys
- Data flow validation
- **Purpose**: Ensure components work together correctly

## Writing E2E Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

test.describe('Feature Description', () => {
  test.beforeEach(async ({ page }) => {
    // Setup code
  });

  test('should perform specific action', async ({ page }) => {
    // Arrange
    const loginPage = new LoginPage(page);
    
    // Act
    await loginPage.goto();
    await loginPage.login('user@example.com', 'password');
    
    // Assert
    await expect(page).toHaveURL('/dashboard');
  });
});
```

### Page Object Model

Use Page Object Model for maintainable tests:

```typescript
// pages/login.page.ts
import { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  private emailInput = 'input[name="email"]';
  private passwordInput = 'input[name="password"]';
  private submitButton = 'button[type="submit"]';

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.fill(this.emailInput, email);
    await this.page.fill(this.passwordInput, password);
    await this.page.click(this.submitButton);
  }
}
```

### Best Practices

1. **Use data-testid attributes** for stable selectors:
   ```html
   <button data-testid="submit-button">Submit</button>
   ```

2. **Wait for elements** instead of using fixed timeouts:
   ```typescript
   await page.waitForSelector('[data-testid="submit-button"]');
   ```

3. **Use meaningful test descriptions**:
   ```typescript
   test('should display error message when login fails with invalid credentials', async ({ page }) => {
     // Test implementation
   });
   ```

4. **Clean up test data** after each test:
   ```typescript
   test.afterEach(async ({ page }) => {
     // Cleanup code
   });
   ```

## Test Data Management

### Fixtures

Use fixtures for reusable test setup:

```typescript
// fixtures/auth.fixture.ts
import { test as base } from '@playwright/test';

export const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    // Login logic
    await use(page);
    // Cleanup logic
  },
});
```

### Test Data

- Use factories for generating test data
- Clean up data after tests
- Use unique identifiers to avoid conflicts

## Configuration

### Playwright Configuration

Key settings in `playwright.config.ts`:

```typescript
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
});
```

### Environment Variables

- `CI=true`: Enables CI-specific settings
- `PLAYWRIGHT_BASE_URL`: Frontend URL
- `VITE_API_URL`: Backend API URL

## Debugging Tests

### Local Debugging

1. **Run in headed mode**:
   ```bash
   npm run e2e:headed
   ```

2. **Use debug mode**:
   ```bash
   npm run e2e:debug
   ```

3. **Add breakpoints** in test code:
   ```typescript
   await page.pause(); // Pauses execution
   ```

### CI Debugging

1. **Check test artifacts**:
   - Screenshots on failure
   - Video recordings
   - HTML reports

2. **Enable verbose logging**:
   ```typescript
   console.log('Debug info:', await page.textContent('selector'));
   ```

## Troubleshooting

### Common Issues

1. **Test timeouts**:
   - Increase timeout values
   - Use proper wait conditions
   - Check network connectivity

2. **Element not found**:
   - Verify selectors
   - Wait for dynamic content
   - Check for timing issues

3. **Flaky tests**:
   - Add proper waits
   - Use retry mechanisms
   - Isolate test data

### Solutions

1. **Network issues**:
   ```typescript
   await page.waitForLoadState('networkidle');
   ```

2. **Dynamic content**:
   ```typescript
   await page.waitForSelector('[data-testid="dynamic-content"]');
   ```

3. **Race conditions**:
   ```typescript
   await expect(page.locator('selector')).toBeVisible();
   ```

## Monitoring and Reporting

### Test Reports

- HTML reports with screenshots
- JUnit XML for CI integration
- JSON reports for processing

### Metrics

- Test execution time
- Pass/fail rates
- Performance benchmarks
- Coverage metrics

## Continuous Improvement

### Regular Maintenance

1. **Review test results** weekly
2. **Update selectors** when UI changes
3. **Optimize slow tests**
4. **Add tests for new features**

### Best Practices Evolution

1. **Share patterns** across team
2. **Document lessons learned**
3. **Refactor common code**
4. **Update this guide** regularly

## Support

For questions or issues:

1. Check this documentation
2. Review existing test examples
3. Consult team knowledge base
4. Ask in team chat channels

---

*Last updated: Phase 2 Sprint 2 Day 3*