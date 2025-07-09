import { test as base, Page } from '@playwright/test';

/**
 * Test user types for E2E testing
 */
export interface TestUser {
  email: string;
  password: string;
  role: 'admin' | 'manager' | 'user';
  organizationId?: number;
}

/**
 * Authentication fixtures for E2E tests
 */
export interface AuthFixtures {
  authenticatedPage: Page;
  adminPage: Page;
  managerPage: Page;
  userPage: Page;
}

/**
 * Test users for different roles
 */
export const TEST_USERS: Record<string, TestUser> = {
  admin: {
    email: 'admin@e2e.test',
    password: 'AdminPass123!',
    role: 'admin'
  },
  manager: {
    email: 'manager@e2e.test',
    password: 'ManagerPass123!',
    role: 'manager',
    organizationId: 1
  },
  user: {
    email: 'user@e2e.test',
    password: 'UserPass123!',
    role: 'user',
    organizationId: 1
  }
};

/**
 * Helper function to perform login
 */
async function login(page: Page, user: TestUser): Promise<void> {
  await page.goto('/login');
  
  // Fill login form
  await page.fill('[data-testid="email-input"]', user.email);
  await page.fill('[data-testid="password-input"]', user.password);
  
  // Submit form
  await page.click('[data-testid="login-button"]');
  
  // Wait for redirect to dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
  
  // Verify login success
  await page.waitForSelector('[data-testid="user-menu"]', { state: 'visible' });
}

/**
 * Extended test with authentication fixtures
 */
export const test = base.extend<AuthFixtures>({
  // Generic authenticated page (uses regular user by default)
  authenticatedPage: async ({ page }, use) => {
    await login(page, TEST_USERS.user);
    await use(page);
    // Optional: Logout after test
    // await logout(page);
  },

  // Admin authenticated page
  adminPage: async ({ page }, use) => {
    await login(page, TEST_USERS.admin);
    await use(page);
  },

  // Manager authenticated page
  managerPage: async ({ page }, use) => {
    await login(page, TEST_USERS.manager);
    await use(page);
  },

  // Regular user authenticated page
  userPage: async ({ page }, use) => {
    await login(page, TEST_USERS.user);
    await use(page);
  }
});

export { expect } from '@playwright/test';

/**
 * Helper to save authentication state
 */
export async function saveAuthState(page: Page, path: string): Promise<void> {
  await page.context().storageState({ path });
}

/**
 * Helper to logout
 */
export async function logout(page: Page): Promise<void> {
  await page.click('[data-testid="user-menu"]');
  await page.click('[data-testid="logout-button"]');
  await page.waitForURL('**/login');
}