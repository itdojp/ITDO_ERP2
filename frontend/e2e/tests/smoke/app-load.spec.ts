import { test, expect } from '@playwright/test';

test.describe('Application Loading', () => {
  test('アプリケーションが正常に起動する', async ({ page }) => {
    // Navigate to home page
    await page.goto('/');
    
    // Check page title contains ITDO ERP
    await expect(page).toHaveTitle(/ITDO ERP/);
    
    // Check that the page loads without errors
    const bodyElement = page.locator('body');
    await expect(bodyElement).toBeVisible();
    
    // Check for console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait a bit to catch any delayed errors
    await page.waitForTimeout(1000);
    
    // Verify no console errors
    expect(consoleErrors).toHaveLength(0);
  });

  test('ナビゲーションが表示される', async ({ page }) => {
    await page.goto('/');
    
    // Check for navigation elements
    const navigation = page.locator('[data-testid="main-navigation"]');
    await expect(navigation).toBeVisible({ timeout: 10000 });
  });

  test('ログインページにリダイレクトされる（未認証の場合）', async ({ page }) => {
    // Try to access a protected route
    await page.goto('/dashboard');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
    
    // Login form should be visible
    const loginForm = page.locator('[data-testid="login-form"]');
    await expect(loginForm).toBeVisible();
  });

  test('404ページが正しく表示される', async ({ page }) => {
    // Navigate to non-existent page
    await page.goto('/non-existent-page');
    
    // Check for 404 content
    const notFoundText = page.locator('text=/404|Not Found|ページが見つかりません/i');
    await expect(notFoundText).toBeVisible();
  });

  test('APIエンドポイントが応答する', async ({ page, request }) => {
    // Check backend health endpoint
    const response = await request.get('http://localhost:8000/api/v1/health');
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
  });

  test('静的アセットが正しくロードされる', async ({ page }) => {
    await page.goto('/');
    
    // Check for CSS loading
    const cssResponse = await page.waitForResponse(response => 
      response.url().includes('.css') && response.status() === 200
    );
    expect(cssResponse).toBeTruthy();
    
    // Check for JavaScript loading
    const jsResponse = await page.waitForResponse(response => 
      response.url().includes('.js') && response.status() === 200
    );
    expect(jsResponse).toBeTruthy();
  });
});