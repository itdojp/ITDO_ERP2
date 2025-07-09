import { test, expect } from '../fixtures/auth.fixture';

/**
 * Performance Testing Suite
 * Sprint 3 Day 2 - Advanced E2E Testing
 * 
 * Tests for performance metrics, Core Web Vitals, and load times
 */

test.describe('Performance Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Enable performance metrics collection
    await page.coverage.startJSCoverage();
    await page.coverage.startCSSCoverage();
  });

  test.afterEach(async ({ page }) => {
    // Stop coverage collection
    await page.coverage.stopJSCoverage();
    await page.coverage.stopCSSCoverage();
  });

  test('ページ読み込み時間の測定', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    console.log(`Page load time: ${loadTime}ms`);
    
    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('Core Web Vitals測定', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    
    // Measure Core Web Vitals
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        const vitals = {
          FCP: null, // First Contentful Paint
          LCP: null, // Largest Contentful Paint
          CLS: null, // Cumulative Layout Shift
          FID: null, // First Input Delay
          TTFB: null // Time to First Byte
        };

        // Performance Observer for Web Vitals
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            switch (entry.name) {
              case 'first-contentful-paint':
                vitals.FCP = entry.startTime;
                break;
              case 'largest-contentful-paint':
                vitals.LCP = entry.startTime;
                break;
            }
          }
        });

        observer.observe({ type: 'paint', buffered: true });
        observer.observe({ type: 'largest-contentful-paint', buffered: true });

        // Get navigation timing
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
          vitals.TTFB = navigation.responseStart - navigation.requestStart;
        }

        // Return after a short delay to collect metrics
        setTimeout(() => {
          resolve(vitals);
        }, 1000);
      });
    });

    console.log('Core Web Vitals:', webVitals);

    // Assert Web Vitals thresholds
    if (webVitals.FCP) {
      expect(webVitals.FCP).toBeLessThan(1800); // Good FCP < 1.8s
    }
    if (webVitals.LCP) {
      expect(webVitals.LCP).toBeLessThan(2500); // Good LCP < 2.5s
    }
    if (webVitals.TTFB) {
      expect(webVitals.TTFB).toBeLessThan(600); // Good TTFB < 600ms
    }
  });

  test('API応答時間の測定', async ({ page }) => {
    const apiTimes = [];
    
    // Monitor API requests
    page.on('response', response => {
      if (response.url().includes('/api/v1/')) {
        const timing = response.timing();
        apiTimes.push({
          url: response.url(),
          status: response.status(),
          time: timing.responseEnd - timing.requestStart
        });
      }
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Navigate to different pages to trigger API calls
    await page.click('[data-testid="nav-tasks"]');
    await page.waitForLoadState('networkidle');
    
    await page.click('[data-testid="nav-projects"]');
    await page.waitForLoadState('networkidle');

    console.log('API Response Times:', apiTimes);

    // Assert API response times
    apiTimes.forEach(api => {
      expect(api.time).toBeLessThan(2000); // API should respond within 2s
      expect(api.status).toBeLessThan(400); // No client/server errors
    });
  });

  test('大量データ処理の性能測定', async ({ adminPage }) => {
    const startTime = Date.now();
    
    await adminPage.goto('/admin/users');
    
    // Wait for initial load
    await adminPage.waitForSelector('[data-testid="users-table"]');
    
    // Simulate loading large dataset
    await adminPage.selectOption('[data-testid="page-size-select"]', '100');
    await adminPage.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    console.log(`Large dataset load time: ${loadTime}ms`);
    
    // Large dataset should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
    
    // Check table performance
    const tableRows = adminPage.locator('[data-testid="user-row"]');
    const rowCount = await tableRows.count();
    
    console.log(`Loaded ${rowCount} rows`);
    expect(rowCount).toBeGreaterThan(0);
  });

  test('検索機能の性能測定', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    await adminPage.waitForSelector('[data-testid="user-search-input"]');
    
    const searchTimes = [];
    
    // Test different search queries
    const queries = ['admin', 'user', 'manager', 'test'];
    
    for (const query of queries) {
      const startTime = Date.now();
      
      await adminPage.fill('[data-testid="user-search-input"]', query);
      await adminPage.press('[data-testid="user-search-input"]', 'Enter');
      
      // Wait for search results
      await adminPage.waitForLoadState('networkidle');
      
      const searchTime = Date.now() - startTime;
      searchTimes.push({ query, time: searchTime });
      
      // Clear search
      await adminPage.fill('[data-testid="user-search-input"]', '');
      await adminPage.press('[data-testid="user-search-input"]', 'Enter');
      await adminPage.waitForLoadState('networkidle');
    }
    
    console.log('Search performance:', searchTimes);
    
    // Search should complete within 1 second
    searchTimes.forEach(search => {
      expect(search.time).toBeLessThan(1000);
    });
  });

  test('メモリリークの検出', async ({ page }) => {
    // Navigate through multiple pages to check for memory leaks
    const pages = ['/dashboard', '/tasks', '/projects', '/admin/users'];
    
    const initialMemory = await page.evaluate(() => {
      if (performance.memory) {
        return {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize
        };
      }
      return null;
    });
    
    // Navigate through pages multiple times
    for (let i = 0; i < 3; i++) {
      for (const path of pages) {
        await page.goto(path);
        await page.waitForLoadState('networkidle');
        
        // Force garbage collection if possible
        await page.evaluate(() => {
          if (window.gc) {
            window.gc();
          }
        });
      }
    }
    
    const finalMemory = await page.evaluate(() => {
      if (performance.memory) {
        return {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize
        };
      }
      return null;
    });
    
    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.used - initialMemory.used;
      console.log(`Memory usage increase: ${memoryIncrease / 1024 / 1024} MB`);
      
      // Memory increase should be reasonable (< 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    }
  });

  test('ネットワーク条件でのパフォーマンステスト', async ({ page }) => {
    // Simulate slow 3G network
    await page.route('**/*', route => {
      setTimeout(() => route.continue(), 100); // 100ms delay
    });
    
    const startTime = Date.now();
    
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    console.log(`Load time with network delay: ${loadTime}ms`);
    
    // Should handle slow network gracefully (< 10s)
    expect(loadTime).toBeLessThan(10000);
  });

  test('画像最適化の確認', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check for image optimization
    const images = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('img'));
      return imgs.map(img => ({
        src: img.src,
        width: img.naturalWidth,
        height: img.naturalHeight,
        fileSize: img.getAttribute('data-file-size'), // if available
        loading: img.loading
      }));
    });
    
    console.log('Image optimization check:', images);
    
    // Check for lazy loading
    images.forEach(img => {
      if (img.loading) {
        expect(img.loading).toBe('lazy');
      }
    });
  });

  test('JavaScript バンドルサイズの確認', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Get resource sizes
    const resources = await page.evaluate(() => {
      const resources = performance.getEntriesByType('resource');
      return resources
        .filter(resource => resource.name.includes('.js'))
        .map(resource => ({
          name: resource.name,
          size: resource.transferSize,
          type: resource.initiatorType
        }));
    });
    
    console.log('JavaScript bundle sizes:', resources);
    
    // Check bundle sizes
    const totalJSSize = resources.reduce((total, resource) => total + resource.size, 0);
    console.log(`Total JS size: ${totalJSSize / 1024} KB`);
    
    // Total JS should be reasonable (< 2MB)
    expect(totalJSSize).toBeLessThan(2 * 1024 * 1024);
  });

  test('レンダリング性能の測定', async ({ page }) => {
    await page.goto('/admin/users');
    
    // Measure rendering performance
    const renderingMetrics = await page.evaluate(() => {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        console.log('Rendering metrics:', entries);
      });
      
      observer.observe({ type: 'measure', buffered: true });
      observer.observe({ type: 'navigation', buffered: true });
      
      // Get paint timing
      const paintTimings = performance.getEntriesByType('paint');
      return paintTimings.map(entry => ({
        name: entry.name,
        startTime: entry.startTime
      }));
    });
    
    console.log('Paint timings:', renderingMetrics);
    
    // First contentful paint should be fast
    const fcp = renderingMetrics.find(metric => metric.name === 'first-contentful-paint');
    if (fcp) {
      expect(fcp.startTime).toBeLessThan(2000);
    }
  });

  test('同時ユーザー負荷シミュレーション', async ({ page, context }) => {
    // Create multiple pages to simulate concurrent users
    const pages = await Promise.all([
      context.newPage(),
      context.newPage(),
      context.newPage()
    ]);
    
    const startTime = Date.now();
    
    // Simulate multiple users accessing the system
    const promises = pages.map(async (userPage, index) => {
      await userPage.goto('/dashboard');
      await userPage.waitForLoadState('networkidle');
      
      // Simulate user interaction
      await userPage.click('[data-testid="nav-tasks"]');
      await userPage.waitForLoadState('networkidle');
      
      return Date.now() - startTime;
    });
    
    const loadTimes = await Promise.all(promises);
    
    console.log('Concurrent user load times:', loadTimes);
    
    // All users should be served within reasonable time
    loadTimes.forEach(time => {
      expect(time).toBeLessThan(5000);
    });
    
    // Clean up
    await Promise.all(pages.map(p => p.close()));
  });
});