import { test, expect } from '@playwright/test';

test.describe('Application Startup', () => {
  test('application loads successfully', async ({ page }) => {
    const errors: string[] = [];
    
    // Monitor console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Navigate to the root URL with robust error handling
    let pageLoaded = false;
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        await page.goto('/', { 
          waitUntil: 'domcontentloaded', 
          timeout: 20000 
        });
        pageLoaded = true;
        break;
      } catch (error) {
        console.log(`Navigation attempt ${attempt}/3 failed: ${error.message}`);
        if (attempt === 3) throw error;
        await page.waitForTimeout(2000);
      }
    }
    
    expect(pageLoaded).toBe(true);
    
    // Check that the page has loaded without errors
    const title = await page.title();
    expect(title).toBeTruthy();
    console.log(`Page title: ${title}`);
    
    // Check for basic page structure
    const bodyContent = await page.textContent('body');
    expect(bodyContent).toBeTruthy();
    expect(bodyContent.length).toBeGreaterThan(10);
    
    // Check for significant errors only
    const significantErrors = errors.filter(error => 
      !error.includes('404') && 
      !error.includes('favicon') &&
      !error.includes('sourcemap') &&
      !error.includes('net::ERR_INTERNET_DISCONNECTED') &&
      !error.includes('Loading CSS chunk')
    );
    
    if (significantErrors.length > 0) {
      console.error(`Console errors (${significantErrors.length}):`, significantErrors);
    }
    expect(significantErrors).toHaveLength(0);
  });

  test('API health check endpoint is accessible', async ({ request }) => {
    // Simple health check with timeout
    const response = await request.get('http://localhost:8000/health', { timeout: 15000 });
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    
    console.log('Backend health check passed:', data);
  });

  test('API ping endpoint works', async ({ request }) => {
    const response = await request.get('http://localhost:8000/ping', { timeout: 15000 });
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('message', 'pong');
    
    console.log('Backend ping test passed:', data);
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