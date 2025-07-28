import { test, expect } from '@playwright/test';
import { setupMockData, cleanupMockData } from '../helpers/test-data';

test.describe('Authentication - Login', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockData();
    await page.goto('/auth/login');
  });

  test.afterEach(async () => {
    await cleanupMockData();
  });

  test('displays login form with all elements', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/ITDO ERP.*ログイン/);
    
    // Check form elements
    await expect(page.getByRole('heading', { name: 'アカウントにログイン' })).toBeVisible();
    await expect(page.getByLabel('メールアドレス')).toBeVisible();
    await expect(page.getByLabel('パスワード')).toBeVisible();
    await expect(page.getByLabel('ログイン状態を保持')).toBeVisible();
    await expect(page.getByRole('button', { name: 'ログイン' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Googleでログイン/ })).toBeVisible();
    
    // Check links
    await expect(page.getByText('パスワードを忘れた方')).toBeVisible();
    await expect(page.getByText('新規アカウントを作成')).toBeVisible();
  });

  test('successful login without MFA', async ({ page }) => {
    // Fill login form
    await page.getByLabel('メールアドレス').fill('user@example.com');
    await page.getByLabel('パスワード').fill('TestPassword123!');
    
    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Wait for navigation
    await page.waitForURL('/dashboard');
    
    // Verify dashboard is displayed
    await expect(page.getByRole('heading', { name: 'ダッシュボード' })).toBeVisible();
    
    // Verify user info is displayed
    await expect(page.getByText('user@example.com')).toBeVisible();
  });

  test('login with MFA requirement', async ({ page }) => {
    // Fill login form with MFA user
    await page.getByLabel('メールアドレス').fill('mfa-user@example.com');
    await page.getByLabel('パスワード').fill('TestPassword123!');
    
    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Wait for MFA page
    await page.waitForURL('/auth/mfa-verify');
    
    // Verify MFA form is displayed
    await expect(page.getByRole('heading', { name: '2段階認証' })).toBeVisible();
    await expect(page.getByText('mfa-user@example.com')).toBeVisible();
    await expect(page.getByLabel(/認証コード/)).toBeVisible();
  });

  test('login with remember me', async ({ page, context }) => {
    // Fill login form
    await page.getByLabel('メールアドレス').fill('user@example.com');
    await page.getByLabel('パスワード').fill('TestPassword123!');
    await page.getByLabel('ログイン状態を保持').check();
    
    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Wait for navigation
    await page.waitForURL('/dashboard');
    
    // Check that remember me cookie is set
    const cookies = await context.cookies();
    const rememberMeCookie = cookies.find(c => c.name === 'remember_token');
    expect(rememberMeCookie).toBeDefined();
    expect(rememberMeCookie?.expires).toBeGreaterThan(Date.now() / 1000 + 86400); // More than 1 day
  });

  test('login failure with invalid credentials', async ({ page }) => {
    // Fill login form with invalid credentials
    await page.getByLabel('メールアドレス').fill('user@example.com');
    await page.getByLabel('パスワード').fill('WrongPassword');
    
    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Verify error message
    await expect(page.getByRole('alert')).toContainText('ログインに失敗しました');
    
    // Verify still on login page
    await expect(page).toHaveURL('/auth/login');
  });

  test('login with locked account', async ({ page }) => {
    // Fill login form with locked account
    await page.getByLabel('メールアドレス').fill('locked@example.com');
    await page.getByLabel('パスワード').fill('TestPassword123!');
    
    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Verify error message
    await expect(page.getByRole('alert')).toContainText('アカウントがロックされています');
  });

  test('validation errors for empty fields', async ({ page }) => {
    // Click login without filling fields
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Check HTML5 validation
    const emailInput = page.getByLabel('メールアドレス');
    await expect(emailInput).toHaveAttribute('required', '');
    
    const passwordInput = page.getByLabel('パスワード');
    await expect(passwordInput).toHaveAttribute('required', '');
  });

  test('navigation to forgot password', async ({ page }) => {
    await page.getByText('パスワードを忘れた方').click();
    
    await page.waitForURL('/auth/forgot-password');
    await expect(page.getByRole('heading', { name: 'パスワードをリセット' })).toBeVisible();
  });

  test('navigation to registration', async ({ page }) => {
    await page.getByText('新規アカウントを作成').click();
    
    await page.waitForURL('/auth/register');
    await expect(page.getByRole('heading', { name: '新規アカウント作成' })).toBeVisible();
  });

  test('password visibility toggle', async ({ page }) => {
    const passwordInput = page.getByLabel('パスワード');
    
    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Type password
    await passwordInput.fill('TestPassword123!');
    
    // Toggle visibility (if implemented)
    const toggleButton = page.getByRole('button', { name: /パスワードを表示/ });
    if (await toggleButton.isVisible()) {
      await toggleButton.click();
      await expect(passwordInput).toHaveAttribute('type', 'text');
      
      // Toggle back
      await toggleButton.click();
      await expect(passwordInput).toHaveAttribute('type', 'password');
    }
  });

  test('loading state during login', async ({ page }) => {
    // Fill login form
    await page.getByLabel('メールアドレス').fill('user@example.com');
    await page.getByLabel('パスワード').fill('TestPassword123!');
    
    // Intercept API call to delay response
    await page.route('**/api/v1/auth/login', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });
    
    // Submit form
    const loginButton = page.getByRole('button', { name: 'ログイン' });
    await loginButton.click();
    
    // Check loading state
    await expect(loginButton).toBeDisabled();
    await expect(loginButton).toContainText('ログイン中...');
    
    // Wait for completion
    await page.waitForURL('/dashboard');
  });

  test('handles network error gracefully', async ({ page }) => {
    // Fill login form
    await page.getByLabel('メールアドレス').fill('user@example.com');
    await page.getByLabel('パスワード').fill('TestPassword123!');
    
    // Simulate network error
    await page.route('**/api/v1/auth/login', route => route.abort());
    
    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Verify error message
    await expect(page.getByRole('alert')).toContainText(/ネットワークエラー|接続エラー|ログインに失敗しました/);
  });

  test('persists form data on error', async ({ page }) => {
    const email = 'user@example.com';
    
    // Fill login form
    await page.getByLabel('メールアドレス').fill(email);
    await page.getByLabel('パスワード').fill('WrongPassword');
    
    // Submit form
    await page.getByRole('button', { name: 'ログイン' }).click();
    
    // Wait for error
    await expect(page.getByRole('alert')).toBeVisible();
    
    // Verify email is still filled
    await expect(page.getByLabel('メールアドレス')).toHaveValue(email);
    
    // Password should be cleared for security
    await expect(page.getByLabel('パスワード')).toHaveValue('');
  });
});