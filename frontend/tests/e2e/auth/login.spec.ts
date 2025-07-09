import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

test.describe('Login Flow', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('successful login with valid credentials', async ({ page }) => {
    // Arrange
    const validEmail = 'test@example.com';
    const validPassword = 'password123';

    // Act
    await loginPage.login(validEmail, validPassword);

    // Assert
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('failed login with invalid credentials', async ({ page }) => {
    // Arrange
    const invalidEmail = 'wrong@example.com';
    const invalidPassword = 'wrongpassword';

    // Act
    await loginPage.login(invalidEmail, invalidPassword);

    // Assert
    await loginPage.waitForError();
    const errorText = await loginPage.getErrorText();
    expect(errorText).toContain('Invalid credentials');
    await expect(page).toHaveURL('/login');
  });

  test('login form validation', async ({ page }) => {
    // Test empty form submission
    await loginPage.submit();
    
    // Assert
    await expect(page.locator('#email-error')).toBeVisible();
    await expect(page.locator('#password-error')).toBeVisible();
  });

  test('remember me functionality', async ({ page }) => {
    // Arrange
    const email = 'test@example.com';
    const password = 'password123';

    // Act
    await loginPage.fillEmail(email);
    await loginPage.fillPassword(password);
    await page.check('input[name="rememberMe"]');
    await loginPage.submit();

    // Assert
    await expect(page).toHaveURL('/dashboard');
    
    // Check cookie persistence
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find(c => c.name === 'session');
    expect(sessionCookie?.expires).toBeGreaterThan(Date.now() / 1000 + 86400); // > 1 day
  });

  test('redirect to requested page after login', async ({ page }) => {
    // Navigate to protected page
    await page.goto('/settings');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login?redirect=/settings');
    
    // Login
    await loginPage.login('test@example.com', 'password123');
    
    // Should redirect back to settings
    await expect(page).toHaveURL('/settings');
  });
});