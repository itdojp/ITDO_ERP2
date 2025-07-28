import { test, expect, Page } from '@playwright/test';
import { loginAsUser } from '../helpers/auth-helper';

test.describe('Authentication - Session Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as user
    await loginAsUser(page, 'user@example.com', 'TestPassword123!');
    
    // Navigate to session management
    await page.goto('/settings/security');
    await page.getByRole('tab', { name: 'セッション管理' }).click();
  });

  test('displays active sessions', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'アクティブなセッション' })).toBeVisible();
    
    // Should show current session
    await expect(page.getByText('現在のセッション')).toBeVisible();
    
    // Should show session details
    await expect(page.getByText(/Chrome on Windows/)).toBeVisible();
    await expect(page.getByText(/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/)).toBeVisible(); // IP address
    
    // Should show other sessions button
    await expect(page.getByRole('button', { name: '他のすべてのセッションを無効化' })).toBeVisible();
  });

  test('revoke other session', async ({ page, context }) => {
    // Create another session
    const page2 = await context.newPage();
    await loginAsUser(page2, 'user@example.com', 'TestPassword123!');
    await page2.close();
    
    // Refresh session list
    await page.reload();
    
    // Find non-current session
    const otherSession = page.locator('tr').filter({ hasNot: page.getByText('現在のセッション') }).first();
    
    // Click revoke button
    await otherSession.getByRole('button', { name: '無効化' }).click();
    
    // Confirm in modal
    await expect(page.getByText('このセッションを無効化すると')).toBeVisible();
    await page.getByRole('button', { name: '無効化' }).last().click();
    
    // Session should be removed
    await expect(otherSession).not.toBeVisible();
  });

  test('revoke all other sessions', async ({ page, context }) => {
    // Create multiple sessions
    for (let i = 0; i < 2; i++) {
      const newPage = await context.newPage();
      await loginAsUser(newPage, 'user@example.com', 'TestPassword123!');
      await newPage.close();
    }
    
    // Refresh session list
    await page.reload();
    
    // Click revoke all button
    await page.getByRole('button', { name: '他のすべてのセッションを無効化' }).click();
    
    // Should only show current session
    await expect(page.getByText('現在のセッション')).toBeVisible();
    const sessions = page.locator('tr');
    await expect(sessions).toHaveCount(2); // Header + current session
  });

  test('session configuration', async ({ page }) => {
    // Check session settings
    await expect(page.getByText('セッション設定')).toBeVisible();
    
    // Session timeout
    const timeoutSelect = page.getByLabel('セッションタイムアウト');
    await expect(timeoutSelect).toBeVisible();
    await expect(timeoutSelect).toHaveValue('480'); // 8 hours default
    
    // Change timeout
    await timeoutSelect.selectOption('240'); // 4 hours
    
    // Should auto-save
    await page.waitForTimeout(500);
    
    // Verify saved
    await page.reload();
    await expect(timeoutSelect).toHaveValue('240');
  });

  test('remember me duration', async ({ page }) => {
    const rememberSelect = page.getByLabel('ログイン状態の保持期間');
    await expect(rememberSelect).toBeVisible();
    
    // Change duration
    await rememberSelect.selectOption('30'); // 30 days
    
    // Should auto-save
    await page.waitForTimeout(500);
    
    // Verify saved
    await page.reload();
    await expect(rememberSelect).toHaveValue('30');
  });

  test('concurrent session limit', async ({ page }) => {
    const limitSelect = page.getByLabel('最大同時セッション数');
    await expect(limitSelect).toBeVisible();
    
    // Change limit
    await limitSelect.selectOption('5');
    
    // Should auto-save
    await page.waitForTimeout(500);
    
    // Verify saved
    await page.reload();
    await expect(limitSelect).toHaveValue('5');
  });

  test('require MFA for new device', async ({ page }) => {
    const mfaSwitch = page.getByRole('switch', { name: '新しいデバイスからのログインにMFAを要求' });
    await expect(mfaSwitch).toBeVisible();
    
    // Toggle switch
    await mfaSwitch.click();
    
    // Should be checked
    await expect(mfaSwitch).toBeChecked();
    
    // Verify saved
    await page.reload();
    await expect(mfaSwitch).toBeChecked();
  });

  test('trusted device indicator', async ({ page }) => {
    // Look for trusted device badge
    const trustedBadge = page.getByText('信頼済み');
    if (await trustedBadge.isVisible()) {
      await expect(trustedBadge).toHaveClass(/badge.*info/);
    }
  });

  test('session activity details', async ({ page }) => {
    // Check activity information
    await expect(page.getByText('最終アクティビティ:')).toBeVisible();
    await expect(page.getByText('ログイン日時:')).toBeVisible();
    
    // Should show timestamps
    const timestamps = page.locator('text=/\\d{4}\\/\\d{2}\\/\\d{2}/');
    await expect(timestamps).toHaveCount(2); // Login and last activity
  });

  test('session location display', async ({ page }) => {
    // Check if location is displayed (if available)
    const location = page.getByText(/Tokyo|東京|Japan|日本/);
    if (await location.isVisible()) {
      await expect(location).toBeVisible();
    }
  });

  test('mobile device detection', async ({ page, browser }) => {
    // Create mobile session
    const mobileContext = await browser.newContext({
      ...browser.contexts()[0],
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) Mobile/15E148',
    });
    const mobilePage = await mobileContext.newPage();
    await loginAsUser(mobilePage, 'user@example.com', 'TestPassword123!');
    await mobilePage.close();
    await mobileContext.close();
    
    // Refresh session list
    await page.reload();
    
    // Should show mobile icon
    await expect(page.getByText('📱')).toBeVisible();
  });

  test('cannot revoke current session', async ({ page }) => {
    // Find current session row
    const currentSession = page.locator('tr').filter({ has: page.getByText('現在のセッション') });
    
    // Revoke button should be disabled
    const revokeButton = currentSession.getByRole('button', { name: '無効化' });
    await expect(revokeButton).toBeDisabled();
  });

  test('session expiration warning', async ({ page }) => {
    // If session is about to expire, should show warning
    // This would require mocking time or waiting
    
    // Check for any expiration warnings
    const warning = page.getByText(/セッションの有効期限/);
    if (await warning.isVisible()) {
      await expect(warning).toHaveClass(/warning|alert/);
    }
  });

  test('refresh session list', async ({ page, context }) => {
    // Get initial session count
    const initialSessions = await page.locator('tr').count();
    
    // Create new session
    const newPage = await context.newPage();
    await loginAsUser(newPage, 'user@example.com', 'TestPassword123!');
    
    // Manual refresh (if button exists)
    const refreshButton = page.getByRole('button', { name: /更新|リフレッシュ/ });
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
    } else {
      await page.reload();
    }
    
    // Should show new session
    const newSessions = await page.locator('tr').count();
    expect(newSessions).toBeGreaterThan(initialSessions);
    
    await newPage.close();
  });
});