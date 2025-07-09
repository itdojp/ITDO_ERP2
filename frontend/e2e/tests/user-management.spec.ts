import { test, expect } from '../fixtures/auth.fixture';

test.describe('User Management', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure we start with a fresh session
    await page.context().clearCookies();
  });

  test('ユーザー一覧ページが表示される', async ({ adminPage }) => {
    // Navigate to user management page
    await adminPage.goto('/admin/users');
    
    // Check page title and main elements
    await expect(adminPage).toHaveTitle(/ユーザー管理|User Management/);
    await expect(adminPage.locator('[data-testid="users-table"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="add-user-button"]')).toBeVisible();
  });

  test('新しいユーザーを作成できる', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Click add user button
    await adminPage.click('[data-testid="add-user-button"]');
    
    // Check user creation form
    await expect(adminPage.locator('[data-testid="user-form"]')).toBeVisible();
    
    // Fill user details
    const timestamp = Date.now();
    const testEmail = `testuser${timestamp}@e2e.test`;
    
    await adminPage.fill('[data-testid="user-email-input"]', testEmail);
    await adminPage.fill('[data-testid="user-name-input"]', `Test User ${timestamp}`);
    await adminPage.fill('[data-testid="user-phone-input"]', '+81-90-1234-5678');
    
    // Select organization
    await adminPage.selectOption('[data-testid="user-organization-select"]', '1');
    
    // Submit form
    await adminPage.click('[data-testid="save-user-button"]');
    
    // Check success message
    await expect(adminPage.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="success-message"]')).toContainText(/ユーザーが作成されました|User created successfully/);
    
    // Verify user appears in list
    await adminPage.goto('/admin/users');
    await expect(adminPage.locator(`text=${testEmail}`)).toBeVisible();
  });

  test('ユーザー情報を編集できる', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Find first user and click edit
    const firstUserRow = adminPage.locator('[data-testid="user-row"]').first();
    await firstUserRow.locator('[data-testid="edit-user-button"]').click();
    
    // Check edit form
    await expect(adminPage.locator('[data-testid="user-form"]')).toBeVisible();
    
    // Update user name
    const updatedName = `Updated User ${Date.now()}`;
    await adminPage.fill('[data-testid="user-name-input"]', updatedName);
    
    // Save changes
    await adminPage.click('[data-testid="save-user-button"]');
    
    // Check success message
    await expect(adminPage.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('ユーザーを無効化できる', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Find first active user
    const activeUserRow = adminPage.locator('[data-testid="user-row"][data-status="active"]').first();
    await activeUserRow.locator('[data-testid="disable-user-button"]').click();
    
    // Confirm disable action
    await adminPage.click('[data-testid="confirm-disable-button"]');
    
    // Check success message
    await expect(adminPage.locator('[data-testid="success-message"]')).toBeVisible();
    
    // Verify user status changed
    await expect(activeUserRow.locator('[data-testid="user-status"]')).toContainText(/無効|Inactive/);
  });

  test('ユーザー検索機能が動作する', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Use search functionality
    await adminPage.fill('[data-testid="user-search-input"]', 'admin');
    await adminPage.click('[data-testid="search-button"]');
    
    // Check filtered results
    const userRows = adminPage.locator('[data-testid="user-row"]');
    const rowCount = await userRows.count();
    
    // Should have at least one result (admin user)
    expect(rowCount).toBeGreaterThan(0);
    
    // All visible rows should contain 'admin'
    for (let i = 0; i < rowCount; i++) {
      const rowText = await userRows.nth(i).textContent();
      expect(rowText?.toLowerCase()).toContain('admin');
    }
  });

  test('ユーザー詳細ページが表示される', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Click on first user
    const firstUserRow = adminPage.locator('[data-testid="user-row"]').first();
    await firstUserRow.locator('[data-testid="view-user-button"]').click();
    
    // Check user detail page
    await expect(adminPage.locator('[data-testid="user-detail"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="user-email"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="user-organization"]')).toBeVisible();
    await expect(adminPage.locator('[data-testid="user-roles"]')).toBeVisible();
  });

  test('ユーザーにロールを割り当てできる', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Find first user and access role management
    const firstUserRow = adminPage.locator('[data-testid="user-row"]').first();
    await firstUserRow.locator('[data-testid="manage-roles-button"]').click();
    
    // Check role management modal/page
    await expect(adminPage.locator('[data-testid="role-management"]')).toBeVisible();
    
    // Assign a role
    await adminPage.check('[data-testid="role-manager-checkbox"]');
    await adminPage.click('[data-testid="save-roles-button"]');
    
    // Check success message
    await expect(adminPage.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('非管理者ユーザーはユーザー管理にアクセスできない', async ({ userPage }) => {
    // Try to access user management as regular user
    await userPage.goto('/admin/users');
    
    // Should be redirected or show access denied
    await expect(userPage.locator('[data-testid="access-denied"]')).toBeVisible();
  });

  test('ユーザー一覧のページネーションが機能する', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Check if pagination exists (only if there are enough users)
    const pagination = adminPage.locator('[data-testid="pagination"]');
    
    if (await pagination.isVisible()) {
      // Click next page
      await adminPage.click('[data-testid="next-page-button"]');
      
      // Verify page changed
      await expect(adminPage.locator('[data-testid="page-indicator"]')).toContainText('2');
      
      // Click previous page
      await adminPage.click('[data-testid="prev-page-button"]');
      
      // Verify back to page 1
      await expect(adminPage.locator('[data-testid="page-indicator"]')).toContainText('1');
    }
  });

  test('ユーザー削除機能が動作する', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    
    // Create a test user first to delete
    await adminPage.click('[data-testid="add-user-button"]');
    
    const testEmail = `deletetest${Date.now()}@e2e.test`;
    await adminPage.fill('[data-testid="user-email-input"]', testEmail);
    await adminPage.fill('[data-testid="user-name-input"]', 'Delete Test User');
    await adminPage.selectOption('[data-testid="user-organization-select"]', '1');
    await adminPage.click('[data-testid="save-user-button"]');
    
    // Wait for success and go back to list
    await expect(adminPage.locator('[data-testid="success-message"]')).toBeVisible();
    await adminPage.goto('/admin/users');
    
    // Find and delete the test user
    const testUserRow = adminPage.locator(`[data-testid="user-row"]:has-text("${testEmail}")`);
    await testUserRow.locator('[data-testid="delete-user-button"]').click();
    
    // Confirm deletion
    await adminPage.click('[data-testid="confirm-delete-button"]');
    
    // Check success message
    await expect(adminPage.locator('[data-testid="success-message"]')).toBeVisible();
    
    // Verify user is removed from list
    await expect(adminPage.locator(`text=${testEmail}`)).not.toBeVisible();
  });
});