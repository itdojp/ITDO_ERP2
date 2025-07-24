import { test, expect } from '@playwright/test';
import { StabilityHelper } from '../helpers/stability';

test.describe('Advanced Authentication Tests', () => {
  let stabilityHelper: StabilityHelper;

  test.beforeEach(async ({ page }) => {
    stabilityHelper = new StabilityHelper(page);
    await page.goto('/login');
  });

  test('password strength validation', async ({ page }) => {
    await page.fill('[name="email"]', 'test@example.com');
    
    // Test weak password
    await page.fill('[name="password"]', '123');
    await stabilityHelper.clickWithRetry(page.locator('button[type="submit"]'));
    
    await expect(page.locator('[data-testid="password-strength"]')).toContainText('Weak');
  });

  test('session timeout handling', async ({ page }) => {
    // Login first
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await stabilityHelper.clickWithRetry(page.locator('button[type="submit"]'));
    
    // Simulate session timeout
    await page.evaluate(() => {
      localStorage.removeItem('auth_token');
    });
    
    // Try to access protected route
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });

  test('multi-factor authentication flow', async ({ page }) => {
    await page.fill('[name="email"]', 'mfa-user@example.com');
    await page.fill('[name="password"]', 'password123');
    await stabilityHelper.clickWithRetry(page.locator('button[type="submit"]'));
    
    // Should redirect to MFA page
    await expect(page).toHaveURL('/mfa-verification');
    await expect(page.locator('[data-testid="mfa-code-input"]')).toBeVisible();
  });
});