import { test, expect } from '@playwright/test';

test.describe('Logout Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('successful logout from dashboard', async ({ page }) => {
    // Act
    await page.click('button[aria-label="User menu"]');
    await page.click('text=Logout');

    // Assert
    await expect(page).toHaveURL('/login');
    await expect(page.locator('.logout-success')).toBeVisible();
    await expect(page.locator('.logout-success')).toContainText('You have been logged out');
  });

  test('logout clears session', async ({ page, context }) => {
    // Check session exists
    let cookies = await context.cookies();
    expect(cookies.find(c => c.name === 'session')).toBeDefined();

    // Logout
    await page.click('button[aria-label="User menu"]');
    await page.click('text=Logout');

    // Check session cleared
    cookies = await context.cookies();
    expect(cookies.find(c => c.name === 'session')).toBeUndefined();
  });

  test('accessing protected route after logout redirects to login', async ({ page }) => {
    // Logout
    await page.click('button[aria-label="User menu"]');
    await page.click('text=Logout');
    await page.waitForURL('/login');

    // Try to access protected route
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL('/login?redirect=/dashboard');
  });

  test('logout from different pages', async ({ page }) => {
    const protectedPages = ['/dashboard', '/users', '/settings', '/projects'];

    for (const route of protectedPages) {
      // Navigate to page
      await page.goto(route);
      
      // Logout
      await page.click('button[aria-label="User menu"]');
      await page.click('text=Logout');

      // Assert redirect to login
      await expect(page).toHaveURL('/login');
      
      // Re-login for next iteration
      if (route !== protectedPages[protectedPages.length - 1]) {
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');
        await page.waitForURL('/dashboard');
      }
    }
  });
});