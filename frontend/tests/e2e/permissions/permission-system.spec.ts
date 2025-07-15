import { test, expect } from '../fixtures/auth.fixture';

test.describe('Permission System', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    // Navigate to permissions/roles page
    await page.goto('/admin/permissions');
    await expect(page.locator('h1')).toContainText('Permissions & Roles');
  });

  test('should display role list', async ({ authenticatedPage: page }) => {
    // Verify role list is visible
    await expect(page.locator('[data-testid="role-list"]')).toBeVisible();
    
    // Verify test roles are present
    await expect(page.locator('[data-testid="role-item"]')).toContainText('Administrator');
    await expect(page.locator('[data-testid="role-item"]')).toContainText('User');
  });

  test('should view role permissions', async ({ authenticatedPage: page }) => {
    // Click on Administrator role
    const adminRole = page.locator('[data-testid="role-item"]').filter({ hasText: 'Administrator' });
    await adminRole.click();
    
    // Verify permissions are displayed
    await expect(page.locator('[data-testid="permission-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="permission-item"]')).toContainText('user:read');
    await expect(page.locator('[data-testid="permission-item"]')).toContainText('user:write');
    await expect(page.locator('[data-testid="permission-item"]')).toContainText('user:delete');
  });

  test('should create new role', async ({ authenticatedPage: page }) => {
    // Click create role button
    await page.click('[data-testid="create-role-btn"]');
    
    // Fill role form
    await page.fill('[data-testid="role-name"]', 'Test Manager');
    await page.fill('[data-testid="role-code"]', 'test_manager');
    await page.fill('[data-testid="role-description"]', 'Manager role for testing');
    
    // Select permissions
    await page.check('[data-testid="permission-user:read"]');
    await page.check('[data-testid="permission-user:write"]');
    await page.check('[data-testid="permission-project:read"]');
    
    // Submit form
    await page.click('[data-testid="submit-role"]');
    
    // Verify role was created
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="role-list"]')).toContainText('Test Manager');
  });

  test('should edit role permissions', async ({ authenticatedPage: page }) => {
    // Click edit button for User role
    const userRole = page.locator('[data-testid="role-item"]').filter({ hasText: 'User' });
    await userRole.locator('[data-testid="edit-role"]').click();
    
    // Add new permission
    await page.check('[data-testid="permission-project:read"]');
    
    // Save changes
    await page.click('[data-testid="save-role"]');
    
    // Verify changes were saved
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should assign role to user', async ({ authenticatedPage: page }) => {
    // Navigate to user management
    await page.goto('/admin/users');
    
    // Click on test user
    const testUser = page.locator('[data-testid="user-item"]').filter({ hasText: 'test@example.com' });
    await testUser.click();
    
    // Navigate to roles tab
    await page.click('[data-testid="user-roles-tab"]');
    
    // Assign new role
    await page.click('[data-testid="assign-role-btn"]');
    await page.selectOption('[data-testid="select-role"]', 'admin');
    await page.selectOption('[data-testid="select-organization"]', '1');
    
    // Confirm assignment
    await page.click('[data-testid="confirm-assign"]');
    
    // Verify role was assigned
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-role-list"]')).toContainText('Administrator');
  });

  test('should revoke role from user', async ({ authenticatedPage: page }) => {
    // Navigate to user management
    await page.goto('/admin/users');
    
    // Click on admin user
    const adminUser = page.locator('[data-testid="user-item"]').filter({ hasText: 'admin@example.com' });
    await adminUser.click();
    
    // Navigate to roles tab
    await page.click('[data-testid="user-roles-tab"]');
    
    // Get initial role count
    const initialCount = await page.locator('[data-testid="user-role-item"]').count();
    
    // If there are multiple roles, revoke one
    if (initialCount > 1) {
      await page.click('[data-testid="user-role-item"]:last-child [data-testid="revoke-role"]');
      await page.click('[data-testid="confirm-revoke"]');
      
      // Verify role was revoked
      await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
      const newCount = await page.locator('[data-testid="user-role-item"]').count();
      expect(newCount).toBe(initialCount - 1);
    }
  });

  test('should check permission inheritance', async ({ authenticatedPage: page }) => {
    // Navigate to user management
    await page.goto('/admin/users');
    
    // Click on test user
    const testUser = page.locator('[data-testid="user-item"]').filter({ hasText: 'test@example.com' });
    await testUser.click();
    
    // Navigate to effective permissions tab
    await page.click('[data-testid="effective-permissions-tab"]');
    
    // Verify effective permissions are displayed
    await expect(page.locator('[data-testid="effective-permissions-list"]')).toBeVisible();
    
    // Verify at least user:read permission is present
    await expect(page.locator('[data-testid="permission-item"]')).toContainText('user:read');
  });

  test('should test permission-based access control', async ({ authenticatedPage: page }) => {
    // Test that certain features are only available to admins
    await page.goto('/admin');
    
    // Admin user should see admin menu
    if (await page.locator('[data-testid="admin-menu"]').count() > 0) {
      await expect(page.locator('[data-testid="admin-menu"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-management-link"]')).toBeVisible();
      await expect(page.locator('[data-testid="role-management-link"]')).toBeVisible();
    }
    
    // Navigate to user management (should be accessible to admin)
    await page.goto('/admin/users');
    await expect(page.locator('h1')).toContainText('User Management');
  });

  test('should validate permission scope within organization', async ({ authenticatedPage: page }) => {
    // Navigate to user permissions in current organization
    await page.goto('/admin/users');
    
    // Select user to check organization-scoped permissions
    const testUser = page.locator('[data-testid="user-item"]').filter({ hasText: 'test@example.com' });
    await testUser.click();
    
    // Navigate to organization permissions tab
    await page.click('[data-testid="org-permissions-tab"]');
    
    // Verify organization-specific permissions are shown
    await expect(page.locator('[data-testid="org-permission-list"]')).toBeVisible();
    
    // Check that permissions are scoped to "Test Organization"
    await expect(page.locator('[data-testid="permission-scope"]')).toContainText('Test Organization');
  });

  test('should handle permission conflicts gracefully', async ({ authenticatedPage: page }) => {
    // Try to assign conflicting roles
    await page.goto('/admin/users');
    
    // Click on test user
    const testUser = page.locator('[data-testid="user-item"]').filter({ hasText: 'test@example.com' });
    await testUser.click();
    
    // Navigate to roles tab
    await page.click('[data-testid="user-roles-tab"]');
    
    // Try to assign multiple roles in the same organization
    await page.click('[data-testid="assign-role-btn"]');
    await page.selectOption('[data-testid="select-role"]', 'admin');
    await page.selectOption('[data-testid="select-organization"]', '1');
    await page.click('[data-testid="confirm-assign"]');
    
    // The system should handle this appropriately (either merge permissions or show warning)
    const hasSuccess = await page.locator('[data-testid="success-message"]').count() > 0;
    const hasWarning = await page.locator('[data-testid="warning-message"]').count() > 0;
    
    expect(hasSuccess || hasWarning).toBeTruthy();
  });
});