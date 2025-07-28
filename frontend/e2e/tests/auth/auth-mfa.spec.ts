import { test, expect } from '@playwright/test';
import { setupMockData, generateTOTPCode } from '../helpers/test-data';

test.describe('Authentication - MFA Verification', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockData();
    
    // Login with MFA user
    await page.goto('/auth/login');
    await page.getByLabel('メールアドレス').fill('mfa-user@example.com');
    await page.getByLabel('パスワード').fill('TestPassword123!');
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Should redirect to MFA page
    await page.waitForURL('/auth/mfa-verify');
  });

  test('displays MFA verification form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '2段階認証' })).toBeVisible();
    await expect(page.getByText('mfa-user@example.com')).toBeVisible();
    await expect(page.getByLabel(/認証コード/)).toBeVisible();
    await expect(page.getByRole('button', { name: '確認' })).toBeVisible();
    
    // Check additional options
    await expect(page.getByText('バックアップコードを使用')).toBeVisible();
    await expect(page.getByText('コードが届かない場合')).toBeVisible();
    await expect(page.getByText('ログイン画面に戻る')).toBeVisible();
  });

  test('successful MFA verification with TOTP', async ({ page }) => {
    // Generate valid TOTP code (in real test, this would use the actual secret)
    const totpCode = await generateTOTPCode('mfa-user@example.com');
    
    // Enter TOTP code
    await page.getByLabel(/認証コード/).fill(totpCode);
    
    // Submit
    await page.getByRole('button', { name: '確認' }).click();
    
    // Should redirect to dashboard
    await page.waitForURL('/dashboard');
    await expect(page.getByRole('heading', { name: 'ダッシュボード' })).toBeVisible();
  });

  test('MFA verification with backup code', async ({ page }) => {
    // Switch to backup code mode
    await page.getByText('バックアップコードを使用').click();
    
    // Verify UI changed
    await expect(page.getByLabel(/バックアップコード/)).toBeVisible();
    await expect(page.getByText('バックアップコードは8文字の英数字です')).toBeVisible();
    
    // Enter backup code
    await page.getByLabel(/バックアップコード/).fill('ABCD1234');
    
    // Submit
    await page.getByRole('button', { name: '確認' }).click();
    
    // Should redirect to dashboard
    await page.waitForURL('/dashboard');
  });

  test('invalid TOTP code', async ({ page }) => {
    // Enter invalid code
    await page.getByLabel(/認証コード/).fill('000000');
    
    // Submit
    await page.getByRole('button', { name: '確認' }).click();
    
    // Should show error
    await expect(page.getByRole('alert')).toContainText('認証に失敗しました');
    
    // Should remain on MFA page
    await expect(page).toHaveURL('/auth/mfa-verify');
  });

  test('TOTP code input validation', async ({ page }) => {
    const codeInput = page.getByLabel(/認証コード/);
    
    // Should only accept numbers
    await codeInput.fill('ABC123');
    await expect(codeInput).toHaveValue('123');
    
    // Should limit to 6 digits
    await codeInput.fill('1234567890');
    await expect(codeInput).toHaveValue('123456');
    
    // Submit button should be disabled for invalid length
    await codeInput.fill('123');
    await expect(page.getByRole('button', { name: '確認' })).toBeDisabled();
    
    // Submit button should be enabled for valid length
    await codeInput.fill('123456');
    await expect(page.getByRole('button', { name: '確認' })).toBeEnabled();
  });

  test('backup code input validation', async ({ page }) => {
    // Switch to backup code mode
    await page.getByText('バックアップコードを使用').click();
    
    const codeInput = page.getByLabel(/バックアップコード/);
    
    // Should accept alphanumeric
    await codeInput.fill('ABCD1234');
    await expect(codeInput).toHaveValue('ABCD1234');
    
    // Submit button should be disabled for invalid length
    await codeInput.fill('ABC');
    await expect(page.getByRole('button', { name: '確認' })).toBeDisabled();
    
    // Submit button should be enabled for valid length
    await codeInput.fill('ABCD1234');
    await expect(page.getByRole('button', { name: '確認' })).toBeEnabled();
  });

  test('resend code functionality', async ({ page }) => {
    // Click resend
    await page.getByText('コードが届かない場合').click();
    
    // Should show notification
    await expect(page.getByRole('alert')).toContainText('新しいコードを送信しました');
  });

  test('return to login', async ({ page }) => {
    // Click return to login
    await page.getByText('ログイン画面に戻る').click();
    
    // Should redirect to login
    await page.waitForURL('/auth/login');
    await expect(page.getByRole('heading', { name: 'アカウントにログイン' })).toBeVisible();
  });

  test('MFA session timeout', async ({ page }) => {
    // Wait for session to expire (simulate by intercepting API)
    await page.route('**/api/v1/auth/mfa/verify', route => 
      route.fulfill({
        status: 401,
        json: { detail: 'MFAトークンの有効期限が切れました' }
      })
    );
    
    // Try to verify
    await page.getByLabel(/認証コード/).fill('123456');
    await page.getByRole('button', { name: '確認' }).click();
    
    // Should show error and redirect to login
    await expect(page.getByRole('alert')).toContainText('有効期限が切れました');
    await page.waitForURL('/auth/login');
  });

  test('rate limiting on MFA attempts', async ({ page }) => {
    // Try multiple invalid attempts
    for (let i = 0; i < 5; i++) {
      await page.getByLabel(/認証コード/).fill('000000');
      await page.getByRole('button', { name: '確認' }).click();
      await page.waitForTimeout(100);
    }
    
    // Should show rate limit error
    await expect(page.getByRole('alert')).toContainText(/試行回数の上限|しばらくしてから/);
  });

  test('MFA code auto-focus and formatting', async ({ page }) => {
    const codeInput = page.getByLabel(/認証コード/);
    
    // Should be auto-focused
    await expect(codeInput).toBeFocused();
    
    // Should show formatted placeholder
    await expect(codeInput).toHaveAttribute('placeholder', '000000');
    
    // Should have proper input mode for mobile
    await expect(codeInput).toHaveAttribute('inputmode', 'numeric');
  });
});