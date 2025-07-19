import { test, expect } from '@playwright/test';

test.describe('Session Management', () => {
  test('session persists across page navigation', async ({ page, context }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // Get session cookie
    const cookies = await context.cookies();
    const sessionCookie = cookies.find(c => c.name === 'session');
    expect(sessionCookie).toBeDefined();

    // Navigate to different pages
    const pages = ['/users', '/projects', '/settings'];
    for (const route of pages) {
      await page.goto(route);
      await expect(page).toHaveURL(route);
      // Should not redirect to login
      await expect(page.locator('button[aria-label="User menu"]')).toBeVisible();
    }
  });

  test('session timeout redirects to login', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // Simulate session timeout by clearing cookies
    await page.context().clearCookies();

    // Try to navigate
    await page.goto('/users');

    // Should redirect to login
    await expect(page).toHaveURL('/login?redirect=/users');
    await expect(page.locator('.session-expired')).toBeVisible();
    await expect(page.locator('.session-expired')).toContainText('Session expired');
  });

  test('concurrent session handling', async ({ browser }) => {
    // Create two contexts (simulate two browser tabs)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    // Login in first context
    await page1.goto('/login');
    await page1.fill('input[name="email"]', 'test@example.com');
    await page1.fill('input[name="password"]', 'password123');
    await page1.click('button[type="submit"]');
    await page1.waitForURL('/dashboard');

    // Login in second context
    await page2.goto('/login');
    await page2.fill('input[name="email"]', 'test@example.com');
    await page2.fill('input[name="password"]', 'password123');
    await page2.click('button[type="submit"]');
    await page2.waitForURL('/dashboard');

    // Both should have active sessions
    await expect(page1.locator('h1')).toContainText('Dashboard');
    await expect(page2.locator('h1')).toContainText('Dashboard');

    // Cleanup
    await context1.close();
    await context2.close();
  });

  test('refresh token functionality', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // Wait for initial token
    await page.waitForTimeout(1000);

    // Make API call that triggers token refresh
    await page.evaluate(() => {
      return fetch('/api/users/me', {
        headers: { 'Authorization': 'Bearer expired-token' }
      });
    });

    // Should still be logged in
    await page.reload();
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('button[aria-label="User menu"]')).toBeVisible();
  });

  test('remember me session persistence', async ({ page, context }) => {
    // Login with remember me
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.check('input[name="rememberMe"]');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // Get cookies
    const cookies = await context.cookies();
    const sessionCookie = cookies.find(c => c.name === 'session');
    const rememberToken = cookies.find(c => c.name === 'remember_token');

    // Verify long-lived cookies
    expect(sessionCookie).toBeDefined();
    expect(rememberToken).toBeDefined();
    expect(rememberToken?.expires).toBeGreaterThan(Date.now() / 1000 + 7 * 86400); // > 7 days
  });
});