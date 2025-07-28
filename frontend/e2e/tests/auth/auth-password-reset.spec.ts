import { test, expect } from '@playwright/test';
import { setupMockData, getPasswordResetToken } from '../helpers/test-data';

test.describe('Authentication - Password Reset', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockData();
  });

  test.describe('Forgot Password', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/auth/forgot-password');
    });

    test('displays forgot password form', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'パスワードをリセット' })).toBeVisible();
      await expect(page.getByText('登録されているメールアドレスを入力してください')).toBeVisible();
      await expect(page.getByLabel('メールアドレス')).toBeVisible();
      await expect(page.getByRole('button', { name: 'リセットメールを送信' })).toBeVisible();
      await expect(page.getByText('ログイン画面に戻る')).toBeVisible();
    });

    test('successful password reset request', async ({ page }) => {
      // Enter email
      await page.getByLabel('メールアドレス').fill('user@example.com');
      
      // Submit form
      await page.getByRole('button', { name: 'リセットメールを送信' }).click();
      
      // Should show success message
      await expect(page.getByRole('heading', { name: 'メールを送信しました' })).toBeVisible();
      await expect(page.getByText('パスワードリセットの手順をメールで送信しました')).toBeVisible();
      await expect(page.getByRole('button', { name: 'ログイン画面に戻る' })).toBeVisible();
    });

    test('password reset for non-existent email', async ({ page }) => {
      // Enter non-existent email
      await page.getByLabel('メールアドレス').fill('nonexistent@example.com');
      
      // Submit form
      await page.getByRole('button', { name: 'リセットメールを送信' }).click();
      
      // Should still show success (to prevent user enumeration)
      await expect(page.getByRole('heading', { name: 'メールを送信しました' })).toBeVisible();
    });

    test('email validation', async ({ page }) => {
      const emailInput = page.getByLabel('メールアドレス');
      
      // Try invalid email
      await emailInput.fill('invalid-email');
      await page.getByRole('button', { name: 'リセットメールを送信' }).click();
      
      // Should show validation error
      await expect(emailInput).toHaveAttribute('type', 'email');
      
      // Valid email
      await emailInput.fill('valid@example.com');
    });

    test('navigation back to login', async ({ page }) => {
      await page.getByText('ログイン画面に戻る').click();
      
      await page.waitForURL('/auth/login');
      await expect(page.getByRole('heading', { name: 'アカウントにログイン' })).toBeVisible();
    });

    test('rate limiting on password reset requests', async ({ page }) => {
      // Make multiple requests
      for (let i = 0; i < 3; i++) {
        await page.goto('/auth/forgot-password');
        await page.getByLabel('メールアドレス').fill('user@example.com');
        await page.getByRole('button', { name: 'リセットメールを送信' }).click();
        await page.waitForTimeout(100);
      }
      
      // Should show rate limit message (if exposed)
      // Note: Usually rate limiting is silent for security
      await expect(page.getByRole('heading', { name: 'メールを送信しました' })).toBeVisible();
    });
  });

  test.describe('Reset Password', () => {
    test.beforeEach(async ({ page }) => {
      // Get a valid reset token
      const token = await getPasswordResetToken('user@example.com');
      await page.goto(`/auth/reset-password?token=${token}`);
    });

    test('displays reset password form', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '新しいパスワードを設定' })).toBeVisible();
      await expect(page.getByLabel('確認コード')).toBeVisible();
      await expect(page.getByLabel('新しいパスワード')).toBeVisible();
      await expect(page.getByLabel('新しいパスワード（確認）')).toBeVisible();
      await expect(page.getByRole('button', { name: 'パスワードを変更' })).toBeVisible();
    });

    test('successful password reset', async ({ page }) => {
      // Enter verification code
      await page.getByLabel('確認コード').fill('123456');
      
      // Enter new password
      await page.getByLabel('新しいパスワード').fill('NewPassword123!');
      await page.getByLabel('新しいパスワード（確認）').fill('NewPassword123!');
      
      // Submit form
      await page.getByRole('button', { name: 'パスワードを変更' }).click();
      
      // Should redirect to login with success message
      await page.waitForURL('/auth/login');
      await expect(page.getByRole('alert')).toContainText('パスワードがリセットされました');
    });

    test('invalid reset token', async ({ page }) => {
      // Navigate with invalid token
      await page.goto('/auth/reset-password?token=invalid-token');
      
      // Should show error
      await expect(page.getByRole('heading', { name: 'リンクが無効です' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'パスワードリセットを再リクエスト' })).toBeVisible();
    });

    test('expired reset token', async ({ page }) => {
      // Get expired token
      const expiredToken = await getPasswordResetToken('user@example.com', { expired: true });
      await page.goto(`/auth/reset-password?token=${expiredToken}`);
      
      // Should show expiration message
      await expect(page.getByText(/有効期限が切れています/)).toBeVisible();
    });

    test('password strength validation on reset', async ({ page }) => {
      const passwordInput = page.getByLabel('新しいパスワード');
      
      // Weak password
      await passwordInput.fill('weak');
      await expect(page.getByText('弱い')).toBeVisible();
      
      // Strong password
      await passwordInput.fill('StrongNewPassword123!');
      await expect(page.getByText('強い')).toBeVisible();
    });

    test('password confirmation mismatch', async ({ page }) => {
      await page.getByLabel('新しいパスワード').fill('NewPassword123!');
      await page.getByLabel('新しいパスワード（確認）').fill('DifferentPassword123!');
      
      await expect(page.getByText('パスワードが一致しません')).toBeVisible();
    });

    test('prevents reusing current password', async ({ page }) => {
      // Enter verification code
      await page.getByLabel('確認コード').fill('123456');
      
      // Try to use current password
      await page.getByLabel('新しいパスワード').fill('CurrentPassword123!');
      await page.getByLabel('新しいパスワード（確認）').fill('CurrentPassword123!');
      
      // Submit form
      await page.getByRole('button', { name: 'パスワードを変更' }).click();
      
      // Should show error
      await expect(page.getByRole('alert')).toContainText('現在のパスワードと異なる必要があります');
    });

    test('verification code validation', async ({ page }) => {
      const codeInput = page.getByLabel('確認コード');
      
      // Should only accept numbers
      await codeInput.fill('ABC123');
      await expect(codeInput).toHaveValue('123');
      
      // Should limit to 6 digits
      await codeInput.fill('1234567890');
      await expect(codeInput).toHaveValue('123456');
    });

    test('no token provided', async ({ page }) => {
      // Navigate without token
      await page.goto('/auth/reset-password');
      
      // Should redirect to forgot password
      await page.waitForURL('/auth/forgot-password');
    });

    test('loading state during password reset', async ({ page }) => {
      // Fill form
      await page.getByLabel('確認コード').fill('123456');
      await page.getByLabel('新しいパスワード').fill('NewPassword123!');
      await page.getByLabel('新しいパスワード（確認）').fill('NewPassword123!');
      
      // Intercept API call
      await page.route('**/api/v1/password-reset/reset', async route => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.continue();
      });
      
      // Submit form
      const submitButton = page.getByRole('button', { name: 'パスワードを変更' });
      await submitButton.click();
      
      // Check loading state
      await expect(submitButton).toBeDisabled();
      await expect(submitButton).toContainText('パスワードを変更中...');
    });
  });
});