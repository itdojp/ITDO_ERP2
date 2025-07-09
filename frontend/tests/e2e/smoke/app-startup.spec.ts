import { test, expect } from '@playwright/test';

test.describe('Application Startup', () => {
  test('application loads successfully', async ({ page }) => {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    // Monitor console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });

    // Navigate to the root URL
    await page.goto('/');
    
    // Wait for the application to load
    await page.waitForLoadState('networkidle');
    
    // Check that the page has loaded without errors
    const title = await page.title();
    expect(title).toBeTruthy();
    console.log(`Page title: ${title}`);
    
    // Check for basic page structure
    const bodyContent = await page.textContent('body');
    expect(bodyContent).toBeTruthy();
    expect(bodyContent.length).toBeGreaterThan(0);
    
    // Give it a moment to catch any errors
    await page.waitForTimeout(2000);
    
    // Log warnings but don't fail on them
    if (warnings.length > 0) {
      console.log(`Console warnings (${warnings.length}):`, warnings.slice(0, 5));
    }
    
    // Fail on console errors
    if (errors.length > 0) {
      console.error(`Console errors (${errors.length}):`, errors);
    }
    expect(errors).toHaveLength(0);
  });

  test('API health check endpoint is accessible', async ({ request }) => {
    // Test that the backend API is running
    const response = await request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    
    console.log('Backend health check passed:', data);
  });

  test('API ping endpoint works', async ({ request }) => {
    const response = await request.get('http://localhost:8000/ping');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('message', 'pong');
    
    console.log('Backend ping test passed:', data);
  });

  test('CORS headers are properly configured', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    const headers = response.headers();
    
    // Check for CORS headers
    expect(headers['access-control-allow-origin']).toBeTruthy();
    console.log('CORS Origin header:', headers['access-control-allow-origin']);
  });

  test('frontend serves static assets', async ({ page }) => {
    await page.goto('/');
    
    // Check if any CSS is loaded
    const stylesheets = await page.evaluate(() => {
      return Array.from(document.styleSheets).length;
    });
    
    console.log(`Stylesheets loaded: ${stylesheets}`);
    expect(stylesheets).toBeGreaterThan(0);
  });
});