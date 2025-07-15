import { test, expect } from '@playwright/test';

test.describe('User Management CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Navigate to users page
    await page.goto('/users');
    await page.waitForSelector('h1:has-text("User Management")');
  });

  test('display user list with pagination', async ({ page }) => {
    // Check table headers
    await expect(page.locator('th:has-text("Name")')).toBeVisible();
    await expect(page.locator('th:has-text("Email")')).toBeVisible();
    await expect(page.locator('th:has-text("Role")')).toBeVisible();
    await expect(page.locator('th:has-text("Status")')).toBeVisible();
    await expect(page.locator('th:has-text("Actions")')).toBeVisible();

    // Check pagination
    await expect(page.locator('.pagination')).toBeVisible();
    await expect(page.locator('button:has-text("Previous")')).toBeVisible();
    await expect(page.locator('button:has-text("Next")')).toBeVisible();
  });

  test('create new user', async ({ page }) => {
    // Click create button
    await page.click('button:has-text("Add User")');
    
    // Fill form
    await page.fill('input[name="full_name"]', 'Test User');
    await page.fill('input[name="email"]', `testuser${Date.now()}@example.com`);
    await page.fill('input[name="phone"]', '+1234567890');
    await page.selectOption('select[name="role"]', 'user');
    await page.fill('input[name="password"]', 'TestPass123!');
    await page.fill('input[name="confirm_password"]', 'TestPass123!');
    
    // Submit
    await page.click('button[type="submit"]');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('User created successfully');
    
    // Verify user appears in list
    await expect(page.locator('td:has-text("Test User")')).toBeVisible();
  });

  test('edit existing user', async ({ page }) => {
    // Click edit button on first user
    await page.click('button[aria-label="Edit"]:first-of-type');
    
    // Wait for modal
    await page.waitForSelector('.modal-header:has-text("Edit User")');
    
    // Update fields
    await page.fill('input[name="full_name"]', 'Updated User Name');
    await page.fill('input[name="phone"]', '+9876543210');
    
    // Save changes
    await page.click('button:has-text("Save Changes")');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('User updated successfully');
    
    // Verify changes reflected
    await expect(page.locator('td:has-text("Updated User Name")')).toBeVisible();
  });

  test('delete user with confirmation', async ({ page }) => {
    // Get user name for verification
    const userName = await page.locator('tbody tr:last-child td:first-child').textContent();
    
    // Click delete button on last user
    await page.click('tbody tr:last-child button[aria-label="Delete"]');
    
    // Confirm deletion
    await page.waitForSelector('.confirm-dialog');
    await expect(page.locator('.confirm-dialog')).toContainText('Are you sure you want to delete this user?');
    await page.click('button:has-text("Delete")');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('User deleted successfully');
    
    // Verify user removed from list
    await expect(page.locator(`td:has-text("${userName}")`)).not.toBeVisible();
  });

  test('search users by name and email', async ({ page }) => {
    // Search by name
    await page.fill('input[placeholder="Search users..."]', 'John');
    await page.keyboard.press('Enter');
    
    // Verify filtered results
    const nameResults = await page.locator('tbody tr').count();
    expect(nameResults).toBeGreaterThan(0);
    
    // Clear search
    await page.fill('input[placeholder="Search users..."]', '');
    
    // Search by email
    await page.fill('input[placeholder="Search users..."]', '@example.com');
    await page.keyboard.press('Enter');
    
    // Verify filtered results
    const emailResults = await page.locator('tbody tr').count();
    expect(emailResults).toBeGreaterThan(0);
  });

  test('filter users by role', async ({ page }) => {
    // Open filter dropdown
    await page.click('button:has-text("Filter")');
    
    // Select admin role
    await page.check('input[value="admin"]');
    await page.click('button:has-text("Apply Filters")');
    
    // Verify filtered results show only admins
    const rows = await page.locator('tbody tr').all();
    for (const row of rows) {
      await expect(row.locator('td:nth-child(3)')).toContainText('Admin');
    }
  });

  test('bulk actions on multiple users', async ({ page }) => {
    // Select multiple users
    await page.check('tbody tr:nth-child(1) input[type="checkbox"]');
    await page.check('tbody tr:nth-child(2) input[type="checkbox"]');
    await page.check('tbody tr:nth-child(3) input[type="checkbox"]');
    
    // Verify bulk actions appear
    await expect(page.locator('.bulk-actions')).toBeVisible();
    await expect(page.locator('.bulk-actions')).toContainText('3 users selected');
    
    // Perform bulk deactivate
    await page.click('button:has-text("Bulk Actions")');
    await page.click('button:has-text("Deactivate Selected")');
    
    // Confirm action
    await page.click('.confirm-dialog button:has-text("Deactivate")');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('3 users deactivated');
  });

  test('form validation errors', async ({ page }) => {
    // Click create button
    await page.click('button:has-text("Add User")');
    
    // Submit empty form
    await page.click('button[type="submit"]');
    
    // Verify validation errors
    await expect(page.locator('#full_name-error')).toContainText('Name is required');
    await expect(page.locator('#email-error')).toContainText('Email is required');
    await expect(page.locator('#password-error')).toContainText('Password is required');
    
    // Test invalid email
    await page.fill('input[name="email"]', 'invalid-email');
    await page.click('button[type="submit"]');
    await expect(page.locator('#email-error')).toContainText('Invalid email format');
    
    // Test password mismatch
    await page.fill('input[name="password"]', 'Pass123!');
    await page.fill('input[name="confirm_password"]', 'Pass456!');
    await page.click('button[type="submit"]');
    await expect(page.locator('#confirm_password-error')).toContainText('Passwords do not match');
  });
});