import { test, expect } from '@playwright/test';

test.describe('Application Startup', () => {
  // Configure test timeouts based on environment
  test.beforeEach(async ({ page }) => {
    if (process.env.CI) {
      test.setTimeout(120000); // 2 minutes for CI
      await page.setDefaultTimeout(45000);
      await page.setDefaultNavigationTimeout(45000);
    } else {
      test.setTimeout(60000); // 1 minute for local
      await page.setDefaultTimeout(30000);
      await page.setDefaultNavigationTimeout(30000);
    }
  });

  test('application loads successfully with retries', async ({ page }) => {
    const maxAttempts = process.env.CI ? 5 : 3;
    const waitTime = process.env.CI ? 3000 : 2000;
    let lastError: Error | null = null;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        console.log(`Attempt ${attempt}/${maxAttempts}: Loading application...`);
        
        await page.goto('/', { 
          waitUntil: 'domcontentloaded',
          timeout: process.env.CI ? 45000 : 30000
        });
        
        // Wait for page to stabilize
        await page.waitForTimeout(waitTime);
        
        // Verify page loaded
        const title = await page.title();
        const bodyContent = await page.textContent('body');
        
        if (title && bodyContent && bodyContent.length > 5) {
          console.log(`Success! Page title: "${title}", content length: ${bodyContent.length}`);
          expect(title).toBeTruthy();
          expect(bodyContent.length).toBeGreaterThan(5);
          return; // Success, exit test
        }
        
        throw new Error(`Page not fully loaded: title="${title}", content=${bodyContent?.length || 0} chars`);
        
      } catch (error) {
        lastError = error as Error;
        console.log(`Attempt ${attempt} failed: ${error.message}`);
        
        if (attempt < maxAttempts) {
          console.log(`Waiting ${waitTime * attempt}ms before retry...`);
          await page.waitForTimeout(waitTime * attempt); // Exponential backoff
        }
      }
    }
    
    // If we get here, all attempts failed
    console.error('All attempts failed. Last error:', lastError?.message);
    throw lastError || new Error('Application failed to load after all attempts');
  });

  test('backend health check endpoint responds', async ({ request }) => {
    const maxAttempts = process.env.CI ? 10 : 5;
    const timeout = process.env.CI ? 20000 : 15000;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        console.log(`Health check attempt ${attempt}/${maxAttempts}...`);
        
        const response = await request.get('http://localhost:8000/health', { 
          timeout: timeout 
        });
        
        if (response.ok()) {
          const data = await response.json();
          console.log('Backend health check passed:', data);
          expect(data).toHaveProperty('status', 'healthy');
          return; // Success
        }
        
        throw new Error(`Health check failed: ${response.status()} ${response.statusText()}`);
        
      } catch (error) {
        console.log(`Health check attempt ${attempt} failed: ${error.message}`);
        
        if (attempt < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        } else {
          throw error;
        }
      }
    }
  });

  test('basic page structure validation', async ({ page }) => {
    await page.goto('/', { 
      waitUntil: 'domcontentloaded',
      timeout: process.env.CI ? 45000 : 30000
    });
    
    // Wait for page stabilization
    await page.waitForTimeout(process.env.CI ? 3000 : 2000);
    
    // Check basic structure exists
    const bodyExists = await page.locator('body').count();
    expect(bodyExists).toBe(1);
    
    // Check for any content in body
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    expect(bodyText.trim().length).toBeGreaterThan(0);
    
    console.log(`Page structure validated. Body content: ${bodyText.length} characters`);
  });

  test('no critical JavaScript errors', async ({ page }) => {
    const jsErrors: string[] = [];
    const pageErrors: string[] = [];
    
    // Capture JavaScript errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const errorText = msg.text();
        // Filter out non-critical development errors
        if (!errorText.includes('favicon') && 
            !errorText.includes('404') &&
            !errorText.includes('net::ERR_CONNECTION_REFUSED') &&
            !errorText.includes('sourcemap')) {
          jsErrors.push(errorText);
        }
      }
    });
    
    // Capture page errors
    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });
    
    await page.goto('/', { 
      waitUntil: 'domcontentloaded',
      timeout: process.env.CI ? 45000 : 30000
    });
    
    // Wait for any async errors to surface
    await page.waitForTimeout(process.env.CI ? 5000 : 3000);
    
    // Report errors but only fail on critical ones
    if (jsErrors.length > 0) {
      console.warn('JavaScript console errors detected:', jsErrors);
    }
    
    if (pageErrors.length > 0) {
      console.warn('Page errors detected:', pageErrors);
    }
    
    // Only fail on critical errors that would break functionality
    const criticalErrors = [...jsErrors, ...pageErrors].filter(error =>
      error.includes('ReferenceError') ||
      error.includes('TypeError: Cannot read') ||
      error.includes('SyntaxError') ||
      error.includes('is not defined')
    );
    
    expect(criticalErrors).toHaveLength(0);
  });
});