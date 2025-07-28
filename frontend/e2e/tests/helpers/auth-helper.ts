import { Page } from '@playwright/test';

export async function loginAsUser(
  page: Page,
  email: string,
  password: string,
  options?: {
    rememberMe?: boolean;
    expectMFA?: boolean;
  }
) {
  await page.goto('/auth/login');
  
  // Fill login form
  await page.getByLabel('メールアドレス').fill(email);
  await page.getByLabel('パスワード').fill(password);
  
  if (options?.rememberMe) {
    await page.getByLabel('ログイン状態を保持').check();
  }
  
  // Submit form
  await page.getByRole('button', { name: 'ログイン' }).click();
  
  if (options?.expectMFA) {
    // Wait for MFA page
    await page.waitForURL('/auth/mfa-verify');
    
    // Enter MFA code
    await page.getByLabel(/認証コード/).fill('123456');
    await page.getByRole('button', { name: '確認' }).click();
  }
  
  // Wait for dashboard
  await page.waitForURL('/dashboard');
}

export async function logout(page: Page) {
  // Click user menu
  const userMenu = page.getByRole('button', { name: /user@example\.com|ユーザーメニュー/ });
  await userMenu.click();
  
  // Click logout
  await page.getByRole('menuitem', { name: 'ログアウト' }).click();
  
  // Wait for login page
  await page.waitForURL('/auth/login');
}

export async function isAuthenticated(page: Page): Promise<boolean> {
  // Check if we can access a protected route
  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
  
  // If redirected to login, not authenticated
  return !page.url().includes('/auth/login');
}

export async function getCurrentUser(page: Page) {
  if (!await isAuthenticated(page)) {
    return null;
  }
  
  // Get user info from page
  const userEmail = await page.locator('[data-testid="user-email"]').textContent();
  const userName = await page.locator('[data-testid="user-name"]').textContent();
  
  return {
    email: userEmail,
    name: userName,
  };
}

export async function setupMFA(page: Page, deviceName = 'Test Device') {
  // Navigate to MFA setup
  await page.goto('/settings/security/mfa-setup');
  
  // Click next
  await page.getByRole('button', { name: '次へ: コードを確認' }).click();
  
  // Enter device name
  await page.getByLabel('デバイス名').fill(deviceName);
  
  // Enter verification code
  await page.getByLabel('認証コード').fill('123456');
  
  // Submit
  await page.getByRole('button', { name: '確認' }).click();
  
  // Download backup codes
  await page.getByRole('button', { name: 'バックアップコードをダウンロード' }).click();
  
  // Complete setup
  await page.getByRole('button', { name: '設定を完了' }).click();
  
  // Wait for redirect
  await page.waitForURL('/dashboard');
}

export async function disableMFA(page: Page, password: string) {
  // Navigate to security settings
  await page.goto('/settings/security');
  await page.getByRole('tab', { name: '2段階認証' }).click();
  
  // Click disable
  await page.getByRole('button', { name: '2段階認証を無効化' }).click();
  
  // Enter password in modal
  await page.getByPlaceholder('パスワード').fill(password);
  
  // Confirm
  await page.getByRole('button', { name: '無効化' }).last().click();
  
  // Wait for completion
  await page.waitForTimeout(1000);
}

export async function changePassword(
  page: Page,
  currentPassword: string,
  newPassword: string
) {
  // Navigate to change password
  await page.goto('/settings/change-password');
  
  // Fill form
  await page.getByLabel('現在のパスワード').fill(currentPassword);
  await page.getByLabel('新しいパスワード').fill(newPassword);
  await page.getByLabel('新しいパスワード（確認）').fill(newPassword);
  
  // Submit
  await page.getByRole('button', { name: 'パスワードを変更' }).click();
  
  // Wait for success
  await page.waitForSelector('[role="alert"]');
}

export async function requestPasswordReset(page: Page, email: string) {
  // Navigate to forgot password
  await page.goto('/auth/forgot-password');
  
  // Enter email
  await page.getByLabel('メールアドレス').fill(email);
  
  // Submit
  await page.getByRole('button', { name: 'リセットメールを送信' }).click();
  
  // Wait for success message
  await page.waitForSelector('text=メールを送信しました');
}

export async function completePasswordReset(
  page: Page,
  token: string,
  newPassword: string,
  verificationCode?: string
) {
  // Navigate to reset page
  await page.goto(`/auth/reset-password?token=${token}`);
  
  // Enter verification code if provided
  if (verificationCode) {
    await page.getByLabel('確認コード').fill(verificationCode);
  }
  
  // Enter new password
  await page.getByLabel('新しいパスワード').fill(newPassword);
  await page.getByLabel('新しいパスワード（確認）').fill(newPassword);
  
  // Submit
  await page.getByRole('button', { name: 'パスワードを変更' }).click();
  
  // Wait for redirect to login
  await page.waitForURL('/auth/login');
}