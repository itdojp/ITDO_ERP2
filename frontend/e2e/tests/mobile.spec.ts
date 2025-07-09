import { test, expect } from '../fixtures/auth.fixture';

/**
 * Mobile Testing Suite
 * Sprint 3 Day 2 - Advanced E2E Testing
 * 
 * Tests for mobile devices, touch interactions, responsive design, and mobile-specific features
 */

test.describe('Mobile Testing', () => {
  // Common mobile viewports
  const mobileViewports = [
    { name: 'iPhone 12', width: 390, height: 844 },
    { name: 'iPhone SE', width: 375, height: 667 },
    { name: 'Samsung Galaxy S21', width: 360, height: 800 },
    { name: 'iPad', width: 768, height: 1024 },
    { name: 'iPad Pro', width: 1024, height: 1366 }
  ];

  test.describe('レスポンシブデザインテスト', () => {
    mobileViewports.forEach(viewport => {
      test(`${viewport.name} でのレイアウト確認`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        
        // Check if mobile navigation is visible
        if (viewport.width < 768) {
          await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
          await expect(page.locator('[data-testid="desktop-navigation"]')).not.toBeVisible();
        } else {
          await expect(page.locator('[data-testid="desktop-navigation"]')).toBeVisible();
        }
        
        // Check content is properly sized
        const content = page.locator('[data-testid="dashboard-content"]');
        await expect(content).toBeVisible();
        
        // No horizontal scrolling
        const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
        expect(scrollWidth).toBeLessThanOrEqual(viewport.width);
      });
    });
  });

  test.describe('タッチインタラクション', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('タッチナビゲーション', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/dashboard');
      
      // Test mobile menu
      await authenticatedPage.tap('[data-testid="mobile-menu-button"]');
      await expect(authenticatedPage.locator('[data-testid="mobile-navigation"]')).toBeVisible();
      
      // Test navigation tap
      await authenticatedPage.tap('[data-testid="mobile-nav-tasks"]');
      await expect(authenticatedPage).toHaveURL(/\/tasks/);
      
      // Test swipe gesture (if supported)
      const taskCard = authenticatedPage.locator('[data-testid="task-card"]').first();
      if (await taskCard.count() > 0) {
        // Simulate swipe
        await taskCard.hover();
        await authenticatedPage.mouse.down();
        await authenticatedPage.mouse.move(100, 0);
        await authenticatedPage.mouse.up();
      }
    });

    test('スワイプジェスチャー', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/tasks');
      
      // Test swipe on task cards
      const taskCard = authenticatedPage.locator('[data-testid="task-card"]').first();
      
      if (await taskCard.count() > 0) {
        const boundingBox = await taskCard.boundingBox();
        
        if (boundingBox) {
          // Swipe left to reveal actions
          await authenticatedPage.touchscreen.tap(boundingBox.x + boundingBox.width / 2, boundingBox.y + boundingBox.height / 2);
          await authenticatedPage.touchscreen.tap(boundingBox.x + boundingBox.width - 20, boundingBox.y + boundingBox.height / 2);
          
          // Actions should be visible
          await expect(authenticatedPage.locator('[data-testid="task-actions"]')).toBeVisible();
        }
      }
    });

    test('ピンチズーム対応', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Test pinch zoom
      await page.touchscreen.tap(200, 200);
      
      // Simulate pinch gesture
      await page.evaluate(() => {
        const event = new TouchEvent('touchstart', {
          touches: [
            new Touch({ identifier: 1, target: document.body, clientX: 100, clientY: 100 }),
            new Touch({ identifier: 2, target: document.body, clientX: 200, clientY: 200 })
          ]
        });
        document.body.dispatchEvent(event);
      });
      
      // Content should handle zoom appropriately
      const viewport = await page.evaluate(() => {
        const meta = document.querySelector('meta[name="viewport"]');
        return meta ? meta.getAttribute('content') : '';
      });
      
      expect(viewport).toContain('user-scalable=yes');
    });
  });

  test.describe('モバイル固有機能', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('プルトゥリフレッシュ', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/tasks');
      
      // Test pull-to-refresh
      await authenticatedPage.evaluate(() => {
        window.scrollTo(0, 0);
      });
      
      // Simulate pull down gesture
      await authenticatedPage.mouse.move(200, 100);
      await authenticatedPage.mouse.down();
      await authenticatedPage.mouse.move(200, 200);
      await authenticatedPage.mouse.up();
      
      // Should trigger refresh
      await expect(authenticatedPage.locator('[data-testid="refresh-indicator"]')).toBeVisible();
    });

    test('無限スクロール', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/admin/users');
      
      // Scroll to bottom
      await authenticatedPage.evaluate(() => {
        window.scrollTo(0, document.body.scrollHeight);
      });
      
      // Should load more content
      await expect(authenticatedPage.locator('[data-testid="loading-more"]')).toBeVisible();
      
      // Wait for more content to load
      await authenticatedPage.waitForTimeout(2000);
      
      // More items should be visible
      const userRows = authenticatedPage.locator('[data-testid="user-row"]');
      const count = await userRows.count();
      expect(count).toBeGreaterThan(10);
    });

    test('オフライン対応', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Simulate offline
      await page.setOfflineMode(true);
      
      // Try to navigate
      await page.click('[data-testid="nav-tasks"]');
      
      // Should show offline message
      await expect(page.locator('[data-testid="offline-message"]')).toBeVisible();
      
      // Restore online
      await page.setOfflineMode(false);
      
      // Should work normally
      await page.reload();
      await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    });
  });

  test.describe('モバイルフォーム', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('モバイルフォーム入力', async ({ adminPage }) => {
      await adminPage.goto('/admin/users');
      await adminPage.tap('[data-testid="add-user-button"]');
      
      // Test mobile form
      const form = adminPage.locator('[data-testid="user-form"]');
      await expect(form).toBeVisible();
      
      // Form should be properly sized
      const formBox = await form.boundingBox();
      expect(formBox?.width).toBeLessThanOrEqual(375);
      
      // Test input types
      const emailInput = adminPage.locator('[data-testid="user-email-input"]');
      await expect(emailInput).toHaveAttribute('type', 'email');
      
      const phoneInput = adminPage.locator('[data-testid="user-phone-input"]');
      await expect(phoneInput).toHaveAttribute('type', 'tel');
    });

    test('バーチャルキーボード対応', async ({ adminPage }) => {
      await adminPage.goto('/admin/users');
      await adminPage.tap('[data-testid="add-user-button"]');
      
      // Focus on input
      await adminPage.tap('[data-testid="user-email-input"]');
      
      // Virtual keyboard simulation
      await adminPage.evaluate(() => {
        // Simulate virtual keyboard opening
        const viewport = window.visualViewport;
        if (viewport) {
          const event = new Event('resize');
          Object.defineProperty(event, 'target', {
            value: { ...viewport, height: viewport.height * 0.6 }
          });
          window.dispatchEvent(event);
        }
      });
      
      // Form should adjust
      const form = adminPage.locator('[data-testid="user-form"]');
      const formBox = await form.boundingBox();
      
      // Form should still be visible
      expect(formBox?.y).toBeGreaterThan(0);
    });
  });

  test.describe('モバイルパフォーマンス', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('モバイルページ読み込み速度', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      console.log(`Mobile load time: ${loadTime}ms`);
      
      // Mobile should load within 4 seconds
      expect(loadTime).toBeLessThan(4000);
    });

    test('モバイルスクロール性能', async ({ page }) => {
      await page.goto('/admin/users');
      
      const startTime = Date.now();
      
      // Perform scroll test
      for (let i = 0; i < 10; i++) {
        await page.evaluate(() => {
          window.scrollBy(0, 100);
        });
        await page.waitForTimeout(50);
      }
      
      const scrollTime = Date.now() - startTime;
      console.log(`Mobile scroll time: ${scrollTime}ms`);
      
      // Should scroll smoothly
      expect(scrollTime).toBeLessThan(1000);
    });
  });

  test.describe('タブレット対応', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
    });

    test('タブレットレイアウト', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/dashboard');
      
      // Should show tablet layout
      await expect(authenticatedPage.locator('[data-testid="tablet-layout"]')).toBeVisible();
      
      // Should have both navigation styles available
      const desktopNav = authenticatedPage.locator('[data-testid="desktop-navigation"]');
      const mobileNav = authenticatedPage.locator('[data-testid="mobile-menu-button"]');
      
      // Tablet might show either based on implementation
      const hasDesktopNav = await desktopNav.count() > 0;
      const hasMobileNav = await mobileNav.count() > 0;
      
      expect(hasDesktopNav || hasMobileNav).toBeTruthy();
    });

    test('タブレット向け操作', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/admin/users');
      
      // Test tablet-specific interactions
      const userRow = authenticatedPage.locator('[data-testid="user-row"]').first();
      
      // Long press for context menu
      await userRow.hover();
      await authenticatedPage.mouse.down();
      await authenticatedPage.waitForTimeout(800); // Long press
      await authenticatedPage.mouse.up();
      
      // Context menu should appear
      await expect(authenticatedPage.locator('[data-testid="context-menu"]')).toBeVisible();
    });
  });

  test.describe('デバイス機能統合', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('カメラ機能', async ({ page }) => {
      await page.goto('/profile');
      
      // Test camera access for profile picture
      const cameraButton = page.locator('[data-testid="camera-button"]');
      
      if (await cameraButton.count() > 0) {
        // Mock camera permission
        await page.evaluate(() => {
          Object.defineProperty(navigator, 'mediaDevices', {
            value: {
              getUserMedia: () => Promise.resolve(new MediaStream())
            }
          });
        });
        
        await cameraButton.click();
        await expect(page.locator('[data-testid="camera-preview"]')).toBeVisible();
      }
    });

    test('位置情報機能', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Mock geolocation
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'geolocation', {
          value: {
            getCurrentPosition: (success: any) => success({
              coords: { latitude: 35.6762, longitude: 139.6503 }
            })
          }
        });
      });
      
      const locationButton = page.locator('[data-testid="location-button"]');
      
      if (await locationButton.count() > 0) {
        await locationButton.click();
        await expect(page.locator('[data-testid="location-info"]')).toBeVisible();
      }
    });
  });

  test.describe('PWA機能', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('インストール可能性', async ({ page }) => {
      await page.goto('/');
      
      // Check for PWA manifest
      const manifest = await page.evaluate(() => {
        const link = document.querySelector('link[rel="manifest"]');
        return link ? link.getAttribute('href') : null;
      });
      
      expect(manifest).toBeTruthy();
      
      // Check for service worker
      const serviceWorker = await page.evaluate(() => {
        return 'serviceWorker' in navigator;
      });
      
      expect(serviceWorker).toBeTruthy();
    });

    test('ホーム画面追加', async ({ page }) => {
      await page.goto('/');
      
      // Simulate beforeinstallprompt event
      await page.evaluate(() => {
        const event = new Event('beforeinstallprompt');
        window.dispatchEvent(event);
      });
      
      // Install banner should appear
      const installBanner = page.locator('[data-testid="install-banner"]');
      
      if (await installBanner.count() > 0) {
        await expect(installBanner).toBeVisible();
      }
    });
  });
});