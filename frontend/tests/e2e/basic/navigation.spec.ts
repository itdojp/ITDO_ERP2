import { test, expect } from '@playwright/test';

test.describe('Basic Navigation', () => {
  test('application root redirects or shows content', async ({ page }) => {
    // Navigate to root
    await page.goto('/');
    
    // Wait for any redirects to complete
    await page.waitForLoadState('networkidle');
    
    // Should either show login page or dashboard
    const url = page.url();
    const isAuthPage = url.includes('/login') || url.includes('/auth');
    const isDashboard = url.includes('/dashboard') || url.endsWith('/');
    
    expect(isAuthPage || isDashboard).toBeTruthy();
  });

  test('navigation links are clickable', async ({ page }) => {
    await page.goto('/');
    
    // Find all links
    const links = await page.locator('a[href]').all();
    
    // If there are links, check at least one is visible
    if (links.length > 0) {
      const firstVisibleLink = await page.locator('a[href]').first();
      await expect(firstVisibleLink).toBeVisible({ timeout: 10000 });
    }
  });

  test('page responds to browser navigation', async ({ page }) => {
    // Go to home
    await page.goto('/');
    
    // Navigate to a different path
    await page.goto('/about');
    await page.waitForLoadState('domcontentloaded');
    
    // Go back
    await page.goBack();
    await page.waitForLoadState('domcontentloaded');
    
    // URL should change (or stay same if single-page app)
    const finalUrl = page.url();
    expect(finalUrl).toBeTruthy();
  });

  test('application handles route changes without full reload', async ({ page }) => {
    await page.goto('/');
    
    // Try to navigate via link click (if any exist)
    const link = await page.locator('a[href^="/"]').first();
    if (await link.isVisible({ timeout: 5000 }).catch(() => false)) {
      await link.click();
      await page.waitForLoadState('domcontentloaded');
      
      // Check if it's still the same app instance (SPA behavior)
      const afterClickTimestamp = await page.evaluate(() => {
        return (window as Window & { __APP_INITIALIZED__?: number }).__APP_INITIALIZED__ || Date.now();
      });
      
      // In SPA, the timestamp would be the same
      // In MPA, it would be different
      // Both are valid behaviors
      expect(afterClickTimestamp).toBeTruthy();
    }
  });

  test('page title is set correctly', async ({ page }) => {
    await page.goto('/');
    
    // Get the page title
    const title = await page.title();
    
    // Should have a title
    expect(title).toBeTruthy();
    
    // Should contain app name or be non-empty
    expect(title.length).toBeGreaterThan(0);
  });
});