import { test, expect } from '@playwright/test';

test.describe('Performance Testing', () => {
  test('page load time measurement', async ({ page }) => {
    // Use Performance API for more accurate timing
    const startTime = Date.now();
    
    // Navigate to homepage with performance monitoring
    await page.goto('/', { 
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    const loadTime = Date.now() - startTime;
    
    // Get performance metrics from browser
    const performanceMetrics = await page.evaluate(() => {
      if (performance.timing) {
        const timing = performance.timing;
        return {
          domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
          loadComplete: timing.loadEventEnd - timing.navigationStart,
          firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
          firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
        };
      }
      return null;
    });
    
    console.log(`Page load time: ${loadTime}ms`);
    console.log('Performance metrics:', performanceMetrics);
    
    // Assert load time is reasonable (under 5 seconds for CI)
    expect(loadTime).toBeLessThan(5000);
    
    // If performance metrics are available, check them
    if (performanceMetrics) {
      expect(performanceMetrics.domContentLoaded).toBeLessThan(3000);
      expect(performanceMetrics.firstContentfulPaint).toBeLessThan(2000);
    }
  });

  test('API response time measurement', async ({ request }) => {
    const endpoints = [
      '/health',
      '/ping',
    ];

    for (const endpoint of endpoints) {
      const startTime = Date.now();
      
      const response = await request.get(`http://localhost:8000${endpoint}`);
      
      const responseTime = Date.now() - startTime;
      console.log(`${endpoint} response time: ${responseTime}ms`);
      
      expect(response.ok()).toBeTruthy();
      // API responses should be under 1000ms for CI stability
      expect(responseTime).toBeLessThan(1000);
    }
  });

  test('large data processing test', async ({ page }) => {
    // Navigate to a data-heavy page (when implemented)
    await page.goto('/');
    
    // Measure memory usage
    const metrics = await page.evaluate(() => {
      return {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        usedJSHeapSize: (performance as any).memory?.usedJSHeapSize || 0,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        totalJSHeapSize: (performance as any).memory?.totalJSHeapSize || 0,
      };
    });

    console.log('Memory metrics:', metrics);
    
    // Ensure memory usage is reasonable (under 50MB)
    if (metrics.usedJSHeapSize > 0) {
      expect(metrics.usedJSHeapSize).toBeLessThan(50 * 1024 * 1024);
    }
  });

  test('network request optimization', async ({ page }) => {
    const requests: Array<{ url: string; duration: number; size: number }> = [];
    
    // Monitor network requests
    page.on('response', async (response) => {
      const request = response.request();
      const timing = response.timing();
      
      requests.push({
        url: request.url(),
        duration: timing.responseEnd,
        size: (await response.body()).length,
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Analyze requests
    const totalRequests = requests.length;
    const totalSize = requests.reduce((sum, req) => sum + req.size, 0);
    const avgDuration = requests.reduce((sum, req) => sum + req.duration, 0) / totalRequests;

    console.log(`Total requests: ${totalRequests}`);
    console.log(`Total size: ${totalSize} bytes`);
    console.log(`Average duration: ${avgDuration}ms`);

    // Performance assertions
    expect(totalRequests).toBeLessThan(50); // Not too many requests
    expect(totalSize).toBeLessThan(5 * 1024 * 1024); // Under 5MB total
    expect(avgDuration).toBeLessThan(500); // Average response under 500ms
  });
});