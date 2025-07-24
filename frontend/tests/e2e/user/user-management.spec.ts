import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

test.describe('User Management Flow', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    await loginPage.goto();
    await loginPage.login('admin@example.com', 'admin123');
  });

  test('admin can create new user', async ({ page }) => {
    await page.click('[data-testid="users-menu"]');
    await page.click('[data-testid="create-user-button"]');
    
    await page.fill('[name="email"]', 'newuser@example.com');
    await page.fill('[name="fullName"]', 'New User');
    await page.fill('[name="password"]', 'NewUser123!');
    
    await page.click('[data-testid="submit-user"]');
    
    await expect(page.locator('[data-testid="success-message"]')).toContainText('User created successfully');
  });

  test('user list displays correctly', async ({ page }) => {
    await page.click('[data-testid="users-menu"]');
    
    await expect(page.locator('[data-testid="users-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-row"]').first()).toBeVisible();
  });

  test('user search functionality works', async ({ page }) => {
    await page.click('[data-testid="users-menu"]');
    
    await page.fill('[data-testid="user-search"]', 'admin');
    await page.press('[data-testid="user-search"]', 'Enter');
    
    await expect(page.locator('[data-testid="user-row"]')).toContainText('admin');
  });

  test('user details modal opens', async ({ page }) => {
    await page.click('[data-testid="users-menu"]');
    await page.click('[data-testid="user-row"]', { position: { x: 50, y: 10 } });
    
    await expect(page.locator('[data-testid="user-details-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-email"]')).toBeVisible();
  });
});