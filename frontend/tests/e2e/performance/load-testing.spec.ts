import { test, expect } from '@playwright/test';

test.describe('Performance Testing', () => {
  test('page load time measurement', async ({ page }) => {
    const startTime = Date.now();
    
    // Navigate to homepage
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);
    
    // Assert load time is reasonable (under 3 seconds)
    expect(loadTime).toBeLessThan(3000);
  });

  test('API response time measurement', async ({ request }) => {
    const endpoints = [
      '/health',
      '/api/v1/ping',
    ];

    for (const endpoint of endpoints) {
      const startTime = Date.now();
      
      const response = await request.get(`http://localhost:8000${endpoint}`);
      
      const responseTime = Date.now() - startTime;
      console.log(`${endpoint} response time: ${responseTime}ms`);
      
      expect(response.ok()).toBeTruthy();
      // API responses should be under 200ms
      expect(responseTime).toBeLessThan(200);
    }
  });

  test('large data processing test', async ({ page }) => {
    // Navigate to a data-heavy page (when implemented)
    await page.goto('/');
    
    // Measure memory usage
    const metrics = await page.evaluate(() => {
      return {
        usedJSHeapSize: (performance as any).memory?.usedJSHeapSize || 0,
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