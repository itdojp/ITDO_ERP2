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

    // Navigate to the root URL with extended timeout
    await page.goto('/', { 
      waitUntil: 'networkidle', 
      timeout: 30000 
    });
    
    // Wait for the application to load completely
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    
    // Check that the page has loaded without errors
    const title = await page.title();
    expect(title).toBeTruthy();
    console.log(`Page title: ${title}`);
    
    // Check for basic page structure with retry
    let bodyContent = '';
    for (let i = 0; i < 5; i++) {
      try {
        bodyContent = await page.textContent('body', { timeout: 5000 });
        if (bodyContent && bodyContent.length > 0) break;
      } catch (e) {
        console.log(`Attempt ${i + 1}: Waiting for body content...`);
        await page.waitForTimeout(1000);
      }
    }
    
    expect(bodyContent).toBeTruthy();
    expect(bodyContent.length).toBeGreaterThan(0);
    
    // Give it a moment to catch any errors
    await page.waitForTimeout(3000);
    
    // Log warnings but don't fail on them
    if (warnings.length > 0) {
      console.log(`Console warnings (${warnings.length}):`, warnings.slice(0, 5));
    }
    
    // Fail on console errors (but ignore common development warnings)
    const significantErrors = errors.filter(error => 
      !error.includes('404') && 
      !error.includes('favicon') &&
      !error.includes('sourcemap')
    );
    
    if (significantErrors.length > 0) {
      console.error(`Console errors (${significantErrors.length}):`, significantErrors);
    }
    expect(significantErrors).toHaveLength(0);
  });

  test('API health check endpoint is accessible', async ({ request }) => {
    // Test that the backend API is running with retry logic
    let response;
    let attempts = 0;
    const maxAttempts = 5;
    
    while (attempts < maxAttempts) {
      try {
        response = await request.get('http://localhost:8000/health', { timeout: 10000 });
        if (response.ok()) break;
      } catch (error) {
        attempts++;
        if (attempts === maxAttempts) throw error;
        console.log(`Health check attempt ${attempts} failed, retrying...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    
    console.log('Backend health check passed:', data);
  });

  test('API ping endpoint works', async ({ request }) => {
    const response = await request.get('http://localhost:8000/ping', { timeout: 10000 });
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('message', 'pong');
    
    console.log('Backend ping test passed:', data);
  });

  test('CORS headers are properly configured', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health', { timeout: 10000 });
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