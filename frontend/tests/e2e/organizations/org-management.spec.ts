import { test, expect } from '@playwright/test';

test.describe('Organization Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Navigate to organizations page
    await page.goto('/organizations');
    await page.waitForSelector('h1:has-text("Organization Management")');
  });

  test('display organization hierarchy', async ({ page }) => {
    // Check tree view is visible
    await expect(page.locator('.org-tree-view')).toBeVisible();
    
    // Check root organization
    await expect(page.locator('.org-node-root')).toBeVisible();
    await expect(page.locator('.org-node-root')).toContainText('ITDO Corporation');
    
    // Expand root node
    await page.click('.org-node-root button[aria-label="Expand"]');
    
    // Check child departments visible
    await expect(page.locator('.org-node-child')).toBeVisible();
    await expect(page.locator('.org-node-child').first()).toBeVisible();
  });

  test('create new organization', async ({ page }) => {
    // Click create button
    await page.click('button:has-text("Create Organization")');
    
    // Fill organization form
    await page.fill('input[name="name"]', 'New Test Organization');
    await page.fill('input[name="code"]', 'TEST-ORG-001');
    await page.fill('textarea[name="description"]', 'Test organization for E2E testing');
    await page.selectOption('select[name="industry"]', 'technology');
    await page.fill('input[name="website"]', 'https://testorg.example.com');
    
    // Add address
    await page.fill('input[name="address.street"]', '123 Test Street');
    await page.fill('input[name="address.city"]', 'Test City');
    await page.fill('input[name="address.state"]', 'Test State');
    await page.fill('input[name="address.postal_code"]', '12345');
    await page.fill('input[name="address.country"]', 'Test Country');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('Organization created successfully');
    
    // Verify organization appears in tree
    await expect(page.locator('.org-node:has-text("New Test Organization")')).toBeVisible();
  });

  test('create department under organization', async ({ page }) => {
    // Select parent organization
    await page.click('.org-node:has-text("ITDO Corporation")');
    
    // Click add department button
    await page.click('button:has-text("Add Department")');
    
    // Fill department form
    await page.fill('input[name="name"]', 'Test Department');
    await page.fill('input[name="code"]', 'TEST-DEPT-001');
    await page.fill('textarea[name="description"]', 'Test department for E2E testing');
    await page.selectOption('select[name="type"]', 'engineering');
    
    // Set manager
    await page.click('input[name="manager_search"]');
    await page.fill('input[name="manager_search"]', 'John');
    await page.click('.search-result:has-text("John Doe")');
    
    // Submit
    await page.click('button[type="submit"]');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('Department created successfully');
    
    // Verify department appears under parent
    await page.click('.org-node:has-text("ITDO Corporation") button[aria-label="Expand"]');
    await expect(page.locator('.org-node-child:has-text("Test Department")')).toBeVisible();
  });

  test('edit organization details', async ({ page }) => {
    // Click on organization node
    await page.click('.org-node:has-text("ITDO Corporation")');
    
    // Click edit button
    await page.click('button:has-text("Edit Organization")');
    
    // Update fields
    await page.fill('input[name="name"]', 'ITDO Corporation Updated');
    await page.fill('textarea[name="description"]', 'Updated description for testing');
    await page.fill('input[name="website"]', 'https://updated.itdo.com');
    
    // Save changes
    await page.click('button:has-text("Save Changes")');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('Organization updated successfully');
    
    // Verify changes reflected
    await expect(page.locator('.org-node:has-text("ITDO Corporation Updated")')).toBeVisible();
  });

  test('manage organization permissions', async ({ page }) => {
    // Select organization
    await page.click('.org-node:has-text("ITDO Corporation")');
    
    // Click permissions tab
    await page.click('button[role="tab"]:has-text("Permissions")');
    
    // Add user to organization
    await page.click('button:has-text("Add User")');
    await page.fill('input[placeholder="Search users..."]', 'jane');
    await page.click('.search-result:has-text("Jane Smith")');
    
    // Set role
    await page.selectOption('select[name="role"]', 'org_manager');
    
    // Set permissions
    await page.check('input[value="view_reports"]');
    await page.check('input[value="manage_users"]');
    await page.check('input[value="manage_departments"]');
    
    // Save permissions
    await page.click('button:has-text("Grant Permissions")');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('Permissions updated successfully');
    
    // Verify user appears in permissions list
    await expect(page.locator('.permission-row:has-text("Jane Smith")')).toBeVisible();
    await expect(page.locator('.permission-row:has-text("Organization Manager")')).toBeVisible();
  });

  test('move department to different organization', async ({ page }) => {
    // Expand organizations
    await page.click('.org-node:has-text("ITDO Corporation") button[aria-label="Expand"]');
    
    // Select department to move
    await page.click('.org-node-child:has-text("Engineering")');
    
    // Click move button
    await page.click('button:has-text("Move Department")');
    
    // Select new parent
    await page.waitForSelector('.modal-header:has-text("Move Department")');
    await page.click('.org-select-item:has-text("Sales Division")');
    
    // Confirm move
    await page.click('button:has-text("Move")');
    
    // Confirm in dialog
    await page.click('.confirm-dialog button:has-text("Confirm Move")');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('Department moved successfully');
    
    // Verify department appears under new parent
    await page.click('.org-node:has-text("Sales Division") button[aria-label="Expand"]');
    await expect(page.locator('.org-node:has-text("Sales Division") .org-node-child:has-text("Engineering")')).toBeVisible();
  });

  test('delete organization with confirmation', async ({ page }) => {
    // Create test organization first
    await page.click('button:has-text("Create Organization")');
    await page.fill('input[name="name"]', 'Organization to Delete');
    await page.fill('input[name="code"]', 'DEL-ORG-001');
    await page.click('button[type="submit"]');
    await page.waitForSelector('.toast-success');
    
    // Select the organization
    await page.click('.org-node:has-text("Organization to Delete")');
    
    // Click delete button
    await page.click('button:has-text("Delete Organization")');
    
    // Verify warning about child entities
    await expect(page.locator('.warning-message')).toContainText('This organization has no child departments or users');
    
    // Type organization name to confirm
    await page.fill('input[placeholder="Type organization name to confirm"]', 'Organization to Delete');
    
    // Confirm deletion
    await page.click('button:has-text("Delete Permanently")');
    
    // Verify success
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.toast-success')).toContainText('Organization deleted successfully');
    
    // Verify organization removed from tree
    await expect(page.locator('.org-node:has-text("Organization to Delete")')).not.toBeVisible();
  });

  test('search and filter organizations', async ({ page }) => {
    // Search by name
    await page.fill('input[placeholder="Search organizations..."]', 'Engineering');
    await page.keyboard.press('Enter');
    
    // Verify filtered results
    await expect(page.locator('.org-node')).toContainText('Engineering');
    await expect(page.locator('.search-results-count')).toContainText('1 result');
    
    // Clear search
    await page.click('button[aria-label="Clear search"]');
    
    // Filter by industry
    await page.click('button:has-text("Filters")');
    await page.selectOption('select[name="industry_filter"]', 'technology');
    await page.click('button:has-text("Apply Filters")');
    
    // Verify filtered organizations
    const orgNodes = await page.locator('.org-node').all();
    expect(orgNodes.length).toBeGreaterThan(0);
  });
});