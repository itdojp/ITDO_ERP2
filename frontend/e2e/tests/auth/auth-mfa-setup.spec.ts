import { test, expect } from '@playwright/test';
import { loginAsUser } from '../helpers/auth-helper';

test.describe('Authentication - MFA Setup', () => {
  test.beforeEach(async ({ page }) => {
    // Login as user without MFA
    await loginAsUser(page, 'user@example.com', 'TestPassword123!');
    
    // Navigate to MFA setup
    await page.goto('/settings/security/mfa-setup');
  });

  test('displays MFA setup instructions', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '2段階認証の設定' })).toBeVisible();
    await expect(page.getByText('アカウントのセキュリティを強化します')).toBeVisible();
    
    // Check tabs
    await expect(page.getByRole('tab', { name: '認証アプリ' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '手動設定' })).toBeVisible();
  });

  test('QR code setup flow', async ({ page }) => {
    // Should show QR code
    await expect(page.locator('img[alt="QR Code"]')).toBeVisible();
    
    // Check recommended apps
    await expect(page.getByText('Google Authenticator')).toBeVisible();
    await expect(page.getByText('Microsoft Authenticator')).toBeVisible();
    await expect(page.getByText('Authy')).toBeVisible();
    
    // Proceed to verification
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    
    // Should show verification form
    await expect(page.getByRole('heading', { name: '認証コードを確認' })).toBeVisible();
    await expect(page.getByLabel('デバイス名')).toBeVisible();
    await expect(page.getByLabel('認証コード')).toBeVisible();
  });

  test('manual setup flow', async ({ page }) => {
    // Switch to manual setup
    await page.getByRole('tab', { name: '手動設定' }).click();
    
    // Should show secret key
    const secretKey = page.locator('code');
    await expect(secretKey).toBeVisible();
    await expect(secretKey).toContainText(/[A-Z0-9]{16,}/);
    
    // Copy button
    const copyButton = page.getByRole('button', { name: 'コピー' });
    await copyButton.click();
    await expect(copyButton).toContainText('コピー済み');
    
    // Check setup details
    await expect(page.getByText('設定タイプ: 時間ベース (TOTP)')).toBeVisible();
    await expect(page.getByText('期間: 30秒')).toBeVisible();
    
    // Proceed to verification
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
  });

  test('successful MFA verification', async ({ page }) => {
    // Proceed to verification
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    
    // Enter device name
    await page.getByLabel('デバイス名').fill('My iPhone');
    
    // Enter valid code (in real test, would generate from secret)
    await page.getByLabel('認証コード').fill('123456');
    
    // Submit
    await page.getByRole('button', { name: '確認' }).click();
    
    // Should show backup codes
    await expect(page.getByRole('heading', { name: 'バックアップコード' })).toBeVisible();
    await expect(page.getByText('認証アプリにアクセスできない場合の緊急用コードです')).toBeVisible();
    
    // Should show 8 backup codes
    const backupCodes = page.locator('code');
    await expect(backupCodes).toHaveCount(8);
  });

  test('backup codes download', async ({ page }) => {
    // Complete setup to backup codes
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    await page.getByLabel('認証コード').fill('123456');
    await page.getByRole('button', { name: '確認' }).click();
    
    // Download backup codes
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'バックアップコードをダウンロード' }).click();
    const download = await downloadPromise;
    
    // Check filename
    expect(download.suggestedFilename()).toMatch(/itdo-erp-backup-codes-\d+\.txt/);
    
    // Button should show completion
    await expect(page.getByRole('button', { name: /バックアップコードをダウンロード.*✓/ })).toBeVisible();
  });

  test('requires backup code download before completion', async ({ page }) => {
    // Complete setup to backup codes
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    await page.getByLabel('認証コード').fill('123456');
    await page.getByRole('button', { name: '確認' }).click();
    
    // Try to complete without downloading
    await page.getByRole('button', { name: '設定を完了' }).click();
    
    // Should show error
    await expect(page.getByRole('alert')).toContainText('バックアップコードをダウンロードしてください');
    
    // Download codes
    await page.getByRole('button', { name: 'バックアップコードをダウンロード' }).click();
    
    // Now should be able to complete
    await page.getByRole('button', { name: '設定を完了' }).click();
    await page.waitForURL('/dashboard');
  });

  test('invalid verification code', async ({ page }) => {
    // Proceed to verification
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    
    // Enter invalid code
    await page.getByLabel('認証コード').fill('000000');
    await page.getByRole('button', { name: '確認' }).click();
    
    // Should show error
    await expect(page.getByRole('alert')).toContainText('認証に失敗しました');
  });

  test('code input validation', async ({ page }) => {
    // Proceed to verification
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    
    const codeInput = page.getByLabel('認証コード');
    
    // Should be auto-focused
    await expect(codeInput).toBeFocused();
    
    // Should only accept numbers
    await codeInput.fill('ABC123');
    await expect(codeInput).toHaveValue('123');
    
    // Submit button disabled for invalid length
    await codeInput.fill('123');
    await expect(page.getByRole('button', { name: '確認' })).toBeDisabled();
    
    // Submit button enabled for valid length
    await codeInput.fill('123456');
    await expect(page.getByRole('button', { name: '確認' })).toBeEnabled();
  });

  test('navigation during setup', async ({ page }) => {
    // Go back from verification
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    await page.getByRole('button', { name: '戻る' }).click();
    
    // Should be back at QR code
    await expect(page.locator('img[alt="QR Code"]')).toBeVisible();
  });

  test('setup cancellation warning', async ({ page }) => {
    // Try to navigate away during setup
    await page.getByRole('button', { name: '次へ: コードを確認' }).click();
    
    // Navigate away
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('設定を中断しますか');
      await dialog.dismiss();
    });
    
    await page.goto('/dashboard');
    
    // Should still be on MFA setup
    await expect(page).toHaveURL(/mfa-setup/);
  });
});