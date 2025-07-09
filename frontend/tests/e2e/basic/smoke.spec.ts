import { test, expect } from '@playwright/test';

test.describe('Basic Smoke Tests', () => {
  test('application loads successfully', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Check that the page loads
    await expect(page).toHaveTitle(/ITDO/);
    
    // Verify page has content
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
  });

  test('backend health check endpoint is accessible', async ({ request }) => {
    // Test backend connectivity
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
  });

  test('frontend serves without errors', async ({ page }) => {
    // Monitor console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignore common development warnings
        if (!text.includes('favicon') && 
            !text.includes('404') &&
            !text.includes('Failed to load resource')) {
          consoleErrors.push(text);
        }
      }
    });
    
    // Navigate to the application
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Check for critical errors
    expect(consoleErrors).toHaveLength(0);
  });
});