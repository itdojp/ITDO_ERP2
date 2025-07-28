import { test, expect } from '@playwright/test';
import { setupMockData, cleanupMockData } from '../helpers/test-data';

test.describe('Authentication - Complete Flow', () => {
  test.beforeAll(async () => {
    await setupMockData();
  });

  test.afterAll(async () => {
    await cleanupMockData();
  });

  test('complete authentication lifecycle', async ({ page, context }) => {
    // Step 1: Register new user
    await test.step('Register new user', async () => {
      await page.goto('/auth/register');
      
      await page.getByLabel('お名前').fill('新規 ユーザー');
      await page.getByLabel('メールアドレス').fill('newuser@example.com');
      await page.getByLabel('パスワード', { exact: true }).fill('SecurePassword123!');
      await page.getByLabel('パスワード（確認）').fill('SecurePassword123!');
      
      await page.getByRole('button', { name: 'アカウントを作成' }).click();
      
      await page.waitForURL('/auth/login');
      await expect(page.getByRole('alert')).toContainText('アカウントが作成されました');
    });

    // Step 2: Login
    await test.step('Login with new account', async () => {
      await page.getByLabel('メールアドレス').fill('newuser@example.com');
      await page.getByLabel('パスワード').fill('SecurePassword123!');
      await page.getByLabel('ログイン状態を保持').check();
      
      await page.getByRole('button', { name: 'ログイン' }).click();
      
      await page.waitForURL('/dashboard');
      await expect(page.getByText('newuser@example.com')).toBeVisible();
    });

    // Step 3: Setup MFA
    await test.step('Setup MFA', async () => {
      await page.goto('/settings/security/mfa-setup');
      
      // Proceed with setup
      await page.getByRole('button', { name: '次へ: コードを確認' }).click();
      
      // Enter device name and code
      await page.getByLabel('デバイス名').fill('My Test Device');
      await page.getByLabel('認証コード').fill('123456');
      await page.getByRole('button', { name: '確認' }).click();
      
      // Download backup codes
      await page.getByRole('button', { name: 'バックアップコードをダウンロード' }).click();
      await page.getByRole('button', { name: '設定を完了' }).click();
      
      await page.waitForURL('/dashboard');
    });

    // Step 4: Logout
    await test.step('Logout', async () => {
      const userMenu = page.getByRole('button', { name: /newuser@example\.com|ユーザーメニュー/ });
      await userMenu.click();
      await page.getByRole('menuitem', { name: 'ログアウト' }).click();
      
      await page.waitForURL('/auth/login');
    });

    // Step 5: Login with MFA
    await test.step('Login with MFA', async () => {
      await page.getByLabel('メールアドレス').fill('newuser@example.com');
      await page.getByLabel('パスワード').fill('SecurePassword123!');
      await page.getByRole('button', { name: 'ログイン' }).click();
      
      // Should require MFA
      await page.waitForURL('/auth/mfa-verify');
      await page.getByLabel(/認証コード/).fill('123456');
      await page.getByRole('button', { name: '確認' }).click();
      
      await page.waitForURL('/dashboard');
    });

    // Step 6: Check session management
    await test.step('Check sessions', async () => {
      await page.goto('/settings/security');
      await page.getByRole('tab', { name: 'セッション管理' }).click();
      
      // Should show current session
      await expect(page.getByText('現在のセッション')).toBeVisible();
      await expect(page.getByText('信頼済み')).toBeVisible(); // Trusted device
    });

    // Step 7: Change password
    await test.step('Change password', async () => {
      await page.goto('/settings/change-password');
      
      await page.getByLabel('現在のパスワード').fill('SecurePassword123!');
      await page.getByLabel('新しいパスワード').fill('NewSecurePassword456!');
      await page.getByLabel('新しいパスワード（確認）').fill('NewSecurePassword456!');
      
      await page.getByRole('button', { name: 'パスワードを変更' }).click();
      
      // Should log out after password change
      await page.waitForURL('/auth/login');
      await expect(page.getByRole('alert')).toContainText('パスワードが変更されました');
    });

    // Step 8: Login with new password
    await test.step('Login with new password', async () => {
      await page.getByLabel('メールアドレス').fill('newuser@example.com');
      await page.getByLabel('パスワード').fill('NewSecurePassword456!');
      await page.getByRole('button', { name: 'ログイン' }).click();
      
      // MFA
      await page.waitForURL('/auth/mfa-verify');
      await page.getByLabel(/認証コード/).fill('123456');
      await page.getByRole('button', { name: '確認' }).click();
      
      await page.waitForURL('/dashboard');
    });

    // Step 9: Test remember me persistence
    await test.step('Test remember me persistence', async () => {
      // Close and reopen browser context
      const cookies = await context.cookies();
      const rememberCookie = cookies.find(c => c.name === 'remember_token');
      expect(rememberCookie).toBeDefined();
      
      // Create new page in same context
      const newPage = await context.newPage();
      await newPage.goto('/dashboard');
      
      // Should still be logged in
      await expect(newPage.getByText('newuser@example.com')).toBeVisible();
      await newPage.close();
    });

    // Step 10: Disable MFA
    await test.step('Disable MFA', async () => {
      await page.goto('/settings/security');
      await page.getByRole('tab', { name: '2段階認証' }).click();
      
      await page.getByRole('button', { name: '2段階認証を無効化' }).click();
      await page.getByPlaceholder('パスワード').fill('NewSecurePassword456!');
      await page.getByRole('button', { name: '無効化' }).last().click();
      
      await page.waitForTimeout(1000);
      await expect(page.getByText('2段階認証が無効になっています')).toBeVisible();
    });
  });

  test('password reset flow', async ({ page }) => {
    const testEmail = 'reset-test@example.com';
    
    // Step 1: Create account
    await test.step('Create test account', async () => {
      await page.goto('/auth/register');
      
      await page.getByLabel('お名前').fill('Reset Test User');
      await page.getByLabel('メールアドレス').fill(testEmail);
      await page.getByLabel('パスワード', { exact: true }).fill('OldPassword123!');
      await page.getByLabel('パスワード（確認）').fill('OldPassword123!');
      
      await page.getByRole('button', { name: 'アカウントを作成' }).click();
      await page.waitForURL('/auth/login');
    });

    // Step 2: Request password reset
    await test.step('Request password reset', async () => {
      await page.getByText('パスワードを忘れた方').click();
      await page.waitForURL('/auth/forgot-password');
      
      await page.getByLabel('メールアドレス').fill(testEmail);
      await page.getByRole('button', { name: 'リセットメールを送信' }).click();
      
      await expect(page.getByRole('heading', { name: 'メールを送信しました' })).toBeVisible();
    });

    // Step 3: Reset password (simulate clicking email link)
    await test.step('Reset password with token', async () => {
      // In real test, would get token from email or API
      const resetToken = 'test-reset-token-12345';
      await page.goto(`/auth/reset-password?token=${resetToken}`);
      
      await page.getByLabel('確認コード').fill('123456');
      await page.getByLabel('新しいパスワード').fill('NewPassword789!');
      await page.getByLabel('新しいパスワード（確認）').fill('NewPassword789!');
      
      await page.getByRole('button', { name: 'パスワードを変更' }).click();
      
      await page.waitForURL('/auth/login');
      await expect(page.getByRole('alert')).toContainText('パスワードがリセットされました');
    });

    // Step 4: Login with new password
    await test.step('Login with new password', async () => {
      await page.getByLabel('メールアドレス').fill(testEmail);
      await page.getByLabel('パスワード').fill('NewPassword789!');
      await page.getByRole('button', { name: 'ログイン' }).click();
      
      await page.waitForURL('/dashboard');
      await expect(page.getByText(testEmail)).toBeVisible();
    });
  });

  test('concurrent session handling', async ({ browser }) => {
    const email = 'concurrent@example.com';
    const password = 'TestPassword123!';
    
    // Create test user
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();
    
    await page1.goto('/auth/register');
    await page1.getByLabel('お名前').fill('Concurrent User');
    await page1.getByLabel('メールアドレス').fill(email);
    await page1.getByLabel('パスワード', { exact: true }).fill(password);
    await page1.getByLabel('パスワード（確認）').fill(password);
    await page1.getByRole('button', { name: 'アカウントを作成' }).click();
    await page1.waitForURL('/auth/login');
    
    // Login in first browser
    await page1.getByLabel('メールアドレス').fill(email);
    await page1.getByLabel('パスワード').fill(password);
    await page1.getByRole('button', { name: 'ログイン' }).click();
    await page1.waitForURL('/dashboard');
    
    // Login in second browser
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();
    
    await page2.goto('/auth/login');
    await page2.getByLabel('メールアドレス').fill(email);
    await page2.getByLabel('パスワード').fill(password);
    await page2.getByRole('button', { name: 'ログイン' }).click();
    await page2.waitForURL('/dashboard');
    
    // Check sessions in first browser
    await page1.goto('/settings/security');
    await page1.getByRole('tab', { name: 'セッション管理' }).click();
    
    // Should see 2 active sessions
    const sessions = page1.locator('tr').filter({ hasText: /Chrome|Firefox|Safari/ });
    await expect(sessions).toHaveCount(2);
    
    // Revoke session from second browser
    await page1.locator('tr')
      .filter({ hasNot: page1.getByText('現在のセッション') })
      .first()
      .getByRole('button', { name: '無効化' })
      .click();
    await page1.getByRole('button', { name: '無効化' }).last().click();
    
    // Second browser should be logged out
    await page2.reload();
    await expect(page2).toHaveURL('/auth/login');
    
    // Cleanup
    await context1.close();
    await context2.close();
  });
});