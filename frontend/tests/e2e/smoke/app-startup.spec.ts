import { test, expect } from '@playwright/test';

test.describe('Application Startup', () => {
  test('application loads successfully', async ({ page }) => {
    // Navigate to the root URL
    await page.goto('/');
    
    // Wait for the application to load
    await page.waitForLoadState('networkidle');
    
    // Check that the page has loaded without errors
    // The app should at least have a title
    const title = await page.title();
    expect(title).toBeTruthy();
    
    // Check that there are no console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Give it a moment to catch any errors
    await page.waitForTimeout(1000);
    expect(errors).toHaveLength(0);
  });

  test('API health check endpoint is accessible', async ({ request }) => {
    // Test that the backend API is running
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
  });
});