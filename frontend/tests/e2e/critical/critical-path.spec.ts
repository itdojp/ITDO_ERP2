import { test, expect } from '@playwright/test';

// Critical path tests - must pass for deployment
test.describe('Critical Path Tests', () => {
  test('application startup', async ({ page }) => {
    // Navigate to the root URL
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    
    // Check that the page has loaded
    const title = await page.title();
    expect(title).toBeTruthy();
    
    // Check for basic page structure
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
    expect(body.length).toBeGreaterThan(10);
  });

  test('backend API health', async ({ request }) => {
    // Test that the backend API is accessible
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
  });

  test('frontend-backend connectivity', async ({ page }) => {
    // Test that frontend can communicate with backend
    await page.goto('/');
    
    // Check if the app can make API calls
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        return res.ok;
      } catch (error) {
        return false;
      }
    });
    
    expect(response).toBe(true);
  });
});