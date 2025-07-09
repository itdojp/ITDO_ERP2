import { test, expect } from '../fixtures/auth.fixture';

/**
 * Visual Regression Testing Suite
 * Sprint 3 Day 2 - Advanced E2E Testing
 * 
 * Tests for visual consistency across different pages and components
 */

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set consistent viewport for screenshot comparison
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('ログインページの視覚的確認', async ({ page }) => {
    await page.goto('/login');
    
    // Wait for all elements to load
    await page.waitForSelector('[data-testid="login-form"]');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot for comparison
    await expect(page).toHaveScreenshot('login-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('ダッシュボードページの視覚的確認', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // Wait for dashboard content to load
    await authenticatedPage.waitForSelector('[data-testid="dashboard-content"]');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Hide dynamic content (dates, timestamps)
    await authenticatedPage.addStyleTag({
      content: `
        .timestamp, .date, .time { visibility: hidden !important; }
        .chart-animation { animation: none !important; }
      `
    });
    
    await expect(authenticatedPage).toHaveScreenshot('dashboard-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('ユーザー管理ページの視覚的確認', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Wait for user table to load
    await adminPage.waitForSelector('[data-testid="users-table"]');
    await adminPage.waitForLoadState('networkidle');
    
    // Hide dynamic content (user IDs, timestamps)
    await adminPage.addStyleTag({
      content: `
        .user-id, .created-at, .last-login { visibility: hidden !important; }
        .loading-spinner { display: none !important; }
      `
    });
    
    await expect(adminPage).toHaveScreenshot('user-management-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('タスク一覧ページの視覚的確認', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/tasks');
    
    // Wait for tasks content to load
    await authenticatedPage.waitForSelector('[data-testid="tasks-content"]');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Hide dynamic content
    await authenticatedPage.addStyleTag({
      content: `
        .task-id, .due-date, .created-at { visibility: hidden !important; }
        .progress-animation { animation: none !important; }
      `
    });
    
    await expect(authenticatedPage).toHaveScreenshot('tasks-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('モバイルビューでの視覚的確認', async ({ authenticatedPage }) => {
    // Set mobile viewport
    await authenticatedPage.setViewportSize({ width: 375, height: 667 });
    
    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForSelector('[data-testid="dashboard-content"]');
    
    // Check mobile navigation
    await authenticatedPage.click('[data-testid="mobile-menu-button"]');
    await authenticatedPage.waitForSelector('[data-testid="mobile-navigation"]');
    
    await expect(authenticatedPage).toHaveScreenshot('mobile-dashboard.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('ダークモードでの視覚的確認', async ({ authenticatedPage }) => {
    // Enable dark mode
    await authenticatedPage.emulateMedia({ colorScheme: 'dark' });
    
    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForSelector('[data-testid="dashboard-content"]');
    await authenticatedPage.waitForLoadState('networkidle');
    
    await expect(authenticatedPage).toHaveScreenshot('dark-mode-dashboard.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('フォームバリデーションの視覚的確認', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Click add user button
    await adminPage.click('[data-testid="add-user-button"]');
    await adminPage.waitForSelector('[data-testid="user-form"]');
    
    // Submit empty form to trigger validation
    await adminPage.click('[data-testid="save-user-button"]');
    
    // Wait for validation messages
    await adminPage.waitForSelector('[data-testid="email-error"]');
    
    await expect(adminPage).toHaveScreenshot('form-validation-errors.png', {
      animations: 'disabled'
    });
  });

  test('モーダルダイアログの視覚的確認', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Find first user and click delete
    const firstUserRow = adminPage.locator('[data-testid="user-row"]').first();
    await firstUserRow.locator('[data-testid="delete-user-button"]').click();
    
    // Wait for confirmation modal
    await adminPage.waitForSelector('[data-testid="delete-confirmation-modal"]');
    
    await expect(adminPage).toHaveScreenshot('delete-confirmation-modal.png', {
      animations: 'disabled'
    });
  });

  test('データテーブルの視覚的確認', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Wait for table to load
    await adminPage.waitForSelector('[data-testid="users-table"]');
    await adminPage.waitForLoadState('networkidle');
    
    // Focus on just the table area
    const table = adminPage.locator('[data-testid="users-table"]');
    
    await expect(table).toHaveScreenshot('users-table.png', {
      animations: 'disabled'
    });
  });

  test('ページネーションの視覚的確認', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Wait for pagination to appear
    await adminPage.waitForSelector('[data-testid="pagination"]');
    
    // Focus on pagination component
    const pagination = adminPage.locator('[data-testid="pagination"]');
    
    await expect(pagination).toHaveScreenshot('pagination-component.png', {
      animations: 'disabled'
    });
  });

  test('エラーページの視覚的確認', async ({ page }) => {
    // Navigate to non-existent page
    await page.goto('/non-existent-page');
    
    // Wait for 404 page
    await page.waitForSelector('text=/404|Not Found/i');
    
    await expect(page).toHaveScreenshot('404-error-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('レスポンシブデザインの視覚的確認', async ({ authenticatedPage }) => {
    const viewports = [
      { width: 1920, height: 1080, name: 'desktop-large' },
      { width: 1280, height: 720, name: 'desktop-medium' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 375, height: 667, name: 'mobile' }
    ];

    for (const viewport of viewports) {
      await authenticatedPage.setViewportSize({ 
        width: viewport.width, 
        height: viewport.height 
      });
      
      await authenticatedPage.goto('/dashboard');
      await authenticatedPage.waitForSelector('[data-testid="dashboard-content"]');
      
      await expect(authenticatedPage).toHaveScreenshot(`dashboard-${viewport.name}.png`, {
        fullPage: true,
        animations: 'disabled'
      });
    }
  });

  test('ローディング状態の視覚的確認', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/admin/users');
    
    // Intercept API call to simulate slow loading
    await authenticatedPage.route('**/api/v1/admin/users', route => {
      setTimeout(() => route.continue(), 2000);
    });
    
    // Reload page and capture loading state
    await authenticatedPage.reload();
    
    // Wait for loading indicator
    await authenticatedPage.waitForSelector('[data-testid="loading"]');
    
    await expect(authenticatedPage).toHaveScreenshot('loading-state.png', {
      animations: 'disabled'
    });
  });
});