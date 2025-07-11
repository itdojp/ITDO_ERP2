import { test, expect } from '@playwright/test';

test.describe('Concurrent Users Testing', () => {
  test('multiple simultaneous API calls', async ({ request }) => {
    const concurrentRequests = 5; // Reduced for CI stability
    const promises: Promise<{ status: number; data: { status: string }; duration: number }>[] = [];

    // Create multiple simultaneous requests
    for (let i = 0; i < concurrentRequests; i++) {
      promises.push(
        request.get('http://localhost:8000/health').then(async (response) => ({
          status: response.status(),
          data: await response.json() as { status: string },
          duration: Date.now(),
        }))
      );
    }

    const startTime = Date.now();
    const results = await Promise.all(promises);
    const totalTime = Date.now() - startTime;

    console.log(`${concurrentRequests} concurrent requests completed in ${totalTime}ms`);

    // All requests should succeed
    results.forEach((result) => {
      expect(result.status).toBe(200);
      expect(result.data.status).toBe('healthy');
    });

    // Total time should be reasonable
    expect(totalTime).toBeLessThan(10000); // Under 10 seconds for CI
  });

  test('session management under load', async ({ browser }) => {
    const contexts = [];
    const pages = [];
    const userCount = 3; // Reduced for CI stability

    try {
      // Create multiple browser contexts (simulating different users)
      for (let i = 0; i < userCount; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        contexts.push(context);
        pages.push(page);
      }

      // Navigate all pages simultaneously with timeouts
      const navigationPromises = pages.map((page, index) => 
        page.goto('/', { 
          waitUntil: 'networkidle',
          timeout: 30000
        }).then(() => ({
          pageIndex: index,
          title: page.title(),
          url: page.url(),
        })).catch(error => ({
          pageIndex: index,
          error: error.message,
          title: null,
          url: null,
        }))
      );

      const results = await Promise.all(navigationPromises);

      // Count successful loads
      const successfulLoads = results.filter(result => result.title && !result.error);
      const failedLoads = results.filter(result => result.error);

      console.log(`Successfully loaded ${successfulLoads.length}/${userCount} concurrent user sessions`);
      
      if (failedLoads.length > 0) {
        console.log('Failed loads:', failedLoads);
      }

      // At least 80% should succeed
      expect(successfulLoads.length).toBeGreaterThanOrEqual(Math.ceil(userCount * 0.8));

    } finally {
      // Clean up contexts
      await Promise.all(contexts.map(context => context.close()));
    }
  });

  test('database connection pool test', async ({ request }) => {
    // Test database connection pool by making many DB-hitting requests
    const requests = [];
    
    for (let i = 0; i < 20; i++) {
      requests.push(
        request.get('http://localhost:8000/health').then(async (response) => ({
          attempt: i + 1,
          success: response.ok(),
          status: response.status(),
        }))
      );
    }

    const results = await Promise.all(requests);
    
    // All requests should succeed
    const successfulRequests = results.filter(r => r.success);
    expect(successfulRequests.length).toBe(20);

    console.log(`Database connection pool handled ${successfulRequests.length}/20 requests successfully`);
  });

  test('memory leak detection with repeated operations', async ({ page }) => {
    await page.goto('/');

    // Take initial memory measurement
    const initialMemory = await page.evaluate(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Perform repeated operations
    for (let i = 0; i < 10; i++) {
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      // Force garbage collection if available
      await page.evaluate(() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if ((window as any).gc) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (window as any).gc();
        }
      });
    }

    // Take final memory measurement
    const finalMemory = await page.evaluate(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    console.log(`Memory: Initial ${initialMemory} bytes, Final ${finalMemory} bytes`);

    // Memory shouldn't grow excessively (allow for some variance)
    if (initialMemory > 0 && finalMemory > 0) {
      const memoryGrowth = finalMemory - initialMemory;
      const maxAllowedGrowth = initialMemory * 0.5; // 50% growth tolerance
      
      expect(memoryGrowth).toBeLessThan(maxAllowedGrowth);
    }
  });
});