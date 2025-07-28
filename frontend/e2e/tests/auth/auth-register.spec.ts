import { test, expect } from '@playwright/test';
import { setupMockData, cleanupMockData } from '../helpers/test-data';

test.describe('Authentication - Registration', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockData();
    await page.goto('/auth/register');
  });

  test.afterEach(async () => {
    await cleanupMockData();
  });

  test('displays registration form with all fields', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '新規アカウント作成' })).toBeVisible();
    await expect(page.getByLabel('お名前')).toBeVisible();
    await expect(page.getByLabel('メールアドレス')).toBeVisible();
    await expect(page.getByLabel('パスワード', { exact: true })).toBeVisible();
    await expect(page.getByLabel('パスワード（確認）')).toBeVisible();
    await expect(page.getByRole('button', { name: 'アカウントを作成' })).toBeVisible();
    
    // Check links
    await expect(page.getByText('ログイン')).toBeVisible();
    await expect(page.getByText('利用規約')).toBeVisible();
    await expect(page.getByText('プライバシーポリシー')).toBeVisible();
  });

  test('successful registration', async ({ page }) => {
    // Fill registration form
    await page.getByLabel('お名前').fill('山田 太郎');
    await page.getByLabel('メールアドレス').fill('new-user@example.com');
    await page.getByLabel('パスワード', { exact: true }).fill('StrongPassword123!');
    await page.getByLabel('パスワード（確認）').fill('StrongPassword123!');
    
    // Submit form
    await page.getByRole('button', { name: 'アカウントを作成' }).click();
    
    // Should redirect to login with success message
    await page.waitForURL('/auth/login');
    await expect(page.getByRole('alert')).toContainText('アカウントが作成されました');
  });

  test('password strength indicator', async ({ page }) => {
    const passwordInput = page.getByLabel('パスワード', { exact: true });
    
    // Weak password
    await passwordInput.fill('weak');
    await expect(page.getByText('弱い')).toBeVisible();
    await expect(page.locator('.bg-red-500')).toBeVisible();
    
    // Show requirements
    await expect(page.getByText('8文字以上必要です')).toBeVisible();
    await expect(page.getByText('大文字を含めてください')).toBeVisible();
    await expect(page.getByText('数字を含めてください')).toBeVisible();
    await expect(page.getByText('特殊文字を含めてください')).toBeVisible();
    
    // Medium password
    await passwordInput.fill('Medium123');
    await expect(page.getByText('普通')).toBeVisible();
    await expect(page.locator('.bg-yellow-500')).toBeVisible();
    
    // Strong password
    await passwordInput.fill('StrongPassword123!');
    await expect(page.getByText('強い')).toBeVisible();
    await expect(page.locator('.bg-green-500')).toBeVisible();
  });

  test('password confirmation validation', async ({ page }) => {
    // Enter passwords
    await page.getByLabel('パスワード', { exact: true }).fill('Password123!');
    await page.getByLabel('パスワード（確認）').fill('DifferentPassword123!');
    
    // Should show mismatch error
    await expect(page.getByText('パスワードが一致しません')).toBeVisible();
    
    // Fix password
    await page.getByLabel('パスワード（確認）').fill('Password123!');
    
    // Error should disappear
    await expect(page.getByText('パスワードが一致しません')).not.toBeVisible();
  });

  test('email validation', async ({ page }) => {
    const emailInput = page.getByLabel('メールアドレス');
    
    // Invalid email
    await emailInput.fill('invalid-email');
    await page.getByLabel('お名前').click(); // Blur
    
    // HTML5 validation
    await page.getByRole('button', { name: 'アカウントを作成' }).click();
    await expect(emailInput).toHaveAttribute('type', 'email');
    
    // Valid email
    await emailInput.fill('valid@example.com');
  });

  test('duplicate email registration', async ({ page }) => {
    // Fill form with existing email
    await page.getByLabel('お名前').fill('山田 太郎');
    await page.getByLabel('メールアドレス').fill('existing@example.com');
    await page.getByLabel('パスワード', { exact: true }).fill('StrongPassword123!');
    await page.getByLabel('パスワード（確認）').fill('StrongPassword123!');
    
    // Submit form
    await page.getByRole('button', { name: 'アカウントを作成' }).click();
    
    // Should show error
    await expect(page.getByRole('alert')).toContainText('このメールアドレスは既に登録されています');
  });

  test('weak password rejection', async ({ page }) => {
    // Fill form with weak password
    await page.getByLabel('お名前').fill('山田 太郎');
    await page.getByLabel('メールアドレス').fill('new-user@example.com');
    await page.getByLabel('パスワード', { exact: true }).fill('weak');
    await page.getByLabel('パスワード（確認）').fill('weak');
    
    // Submit form
    await page.getByRole('button', { name: 'アカウントを作成' }).click();
    
    // Should show error
    await expect(page.getByRole('alert')).toContainText('パスワードが弱すぎます');
  });

  test('required field validation', async ({ page }) => {
    // Try to submit empty form
    await page.getByRole('button', { name: 'アカウントを作成' }).click();
    
    // Check required attributes
    await expect(page.getByLabel('お名前')).toHaveAttribute('required', '');
    await expect(page.getByLabel('メールアドレス')).toHaveAttribute('required', '');
    await expect(page.getByLabel('パスワード', { exact: true })).toHaveAttribute('required', '');
    await expect(page.getByLabel('パスワード（確認）')).toHaveAttribute('required', '');
  });

  test('navigation to login', async ({ page }) => {
    await page.getByText('ログイン').first().click();
    
    await page.waitForURL('/auth/login');
    await expect(page.getByRole('heading', { name: 'アカウントにログイン' })).toBeVisible();
  });

  test('terms and privacy links', async ({ page }) => {
    // Check terms link
    const termsLink = page.getByText('利用規約');
    await expect(termsLink).toHaveAttribute('href', '/terms');
    
    // Check privacy link
    const privacyLink = page.getByText('プライバシーポリシー');
    await expect(privacyLink).toHaveAttribute('href', '/privacy');
  });

  test('loading state during registration', async ({ page }) => {
    // Fill form
    await page.getByLabel('お名前').fill('山田 太郎');
    await page.getByLabel('メールアドレス').fill('new-user@example.com');
    await page.getByLabel('パスワード', { exact: true }).fill('StrongPassword123!');
    await page.getByLabel('パスワード（確認）').fill('StrongPassword123!');
    
    // Intercept API call to delay response
    await page.route('**/api/v1/users/register', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });
    
    // Submit form
    const submitButton = page.getByRole('button', { name: 'アカウントを作成' });
    await submitButton.click();
    
    // Check loading state
    await expect(submitButton).toBeDisabled();
    await expect(submitButton).toContainText('アカウント作成中...');
  });

  test('handles special characters in name', async ({ page }) => {
    // Fill form with special characters in name
    await page.getByLabel('お名前').fill('山田 太郎-ロバート');
    await page.getByLabel('メールアドレス').fill('special-name@example.com');
    await page.getByLabel('パスワード', { exact: true }).fill('StrongPassword123!');
    await page.getByLabel('パスワード（確認）').fill('StrongPassword123!');
    
    // Submit form
    await page.getByRole('button', { name: 'アカウントを作成' }).click();
    
    // Should succeed
    await page.waitForURL('/auth/login');
  });

  test('password visibility toggle', async ({ page }) => {
    const passwordInput = page.getByLabel('パスワード', { exact: true });
    const confirmInput = page.getByLabel('パスワード（確認）');
    
    // Type passwords
    await passwordInput.fill('TestPassword123!');
    await confirmInput.fill('TestPassword123!');
    
    // Initially should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await expect(confirmInput).toHaveAttribute('type', 'password');
    
    // Toggle visibility if available
    const toggleButtons = page.getByRole('button', { name: /パスワードを表示/ });
    if (await toggleButtons.first().isVisible()) {
      await toggleButtons.first().click();
      await expect(passwordInput).toHaveAttribute('type', 'text');
    }
  });
});