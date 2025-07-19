import { test, expect } from '../fixtures/auth.fixture';

test.describe('Department Management', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    // Navigate to departments page
    await page.goto('/departments');
    await expect(page.locator('h1')).toContainText('Departments');
  });

  test('should display department hierarchy', async ({ authenticatedPage: page }) => {
    // Verify department tree is visible
    await expect(page.locator('[data-testid="department-tree"]')).toBeVisible();
    
    // Verify root department exists
    await expect(page.locator('[data-testid="department-node"]')).toContainText('Test Department');
    
    // Verify department information is displayed
    const deptNode = page.locator('[data-testid="department-node"]').first();
    await expect(deptNode).toContainText('TEST_DEPT');
    await expect(deptNode).toContainText('Test Organization');
  });

  test('should expand and collapse department nodes', async ({ authenticatedPage: page }) => {
    // Find expandable department node
    const expandableNode = page.locator('[data-testid="department-node"][data-expandable="true"]').first();
    
    if (await expandableNode.count() > 0) {
      // Click to expand
      await expandableNode.click();
      
      // Verify children are visible
      await expect(page.locator('[data-testid="department-children"]')).toBeVisible();
      
      // Click to collapse
      await expandableNode.click();
      
      // Verify children are hidden
      await expect(page.locator('[data-testid="department-children"]')).toBeHidden();
    }
  });

  test('should create new department', async ({ authenticatedPage: page }) => {
    // Click create department button
    await page.click('[data-testid="create-department-btn"]');
    
    // Fill department form
    await page.fill('[data-testid="dept-name"]', 'New Test Department');
    await page.fill('[data-testid="dept-code"]', 'NEW_DEPT');
    await page.fill('[data-testid="dept-description"]', 'Created during E2E testing');
    
    // Select parent department
    await page.selectOption('[data-testid="parent-department"]', '1'); // Test Department ID
    
    // Submit form
    await page.click('[data-testid="submit-department"]');
    
    // Verify department was created
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="department-tree"]')).toContainText('New Test Department');
  });

  test('should edit department details', async ({ authenticatedPage: page }) => {
    // Click edit button for first department
    await page.click('[data-testid="department-node"]:first-child [data-testid="edit-dept"]');
    
    // Modify department details
    await page.fill('[data-testid="dept-name"]', 'Updated Department Name');
    await page.fill('[data-testid="dept-description"]', 'Updated description');
    
    // Save changes
    await page.click('[data-testid="save-department"]');
    
    // Verify changes were saved
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="department-tree"]')).toContainText('Updated Department Name');
  });

  test('should delete department', async ({ authenticatedPage: page }) => {
    // Create a test department first (to avoid deleting the main one)
    await page.click('[data-testid="create-department-btn"]');
    await page.fill('[data-testid="dept-name"]', 'Department to Delete');
    await page.fill('[data-testid="dept-code"]', 'DEL_DEPT');
    await page.click('[data-testid="submit-department"]');
    
    // Wait for creation
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // Find and delete the created department
    const deleteTarget = page.locator('[data-testid="department-node"]').filter({ hasText: 'Department to Delete' });
    await deleteTarget.locator('[data-testid="delete-dept"]').click();
    
    // Confirm deletion
    await page.click('[data-testid="confirm-delete"]');
    
    // Verify department was deleted
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="department-tree"]')).not.toContainText('Department to Delete');
  });

  test('should move department to different parent', async ({ authenticatedPage: page }) => {
    // Create two departments for moving
    await page.click('[data-testid="create-department-btn"]');
    await page.fill('[data-testid="dept-name"]', 'Source Department');
    await page.fill('[data-testid="dept-code"]', 'SRC_DEPT');
    await page.click('[data-testid="submit-department"]');
    
    await page.click('[data-testid="create-department-btn"]');
    await page.fill('[data-testid="dept-name"]', 'Target Department');
    await page.fill('[data-testid="dept-code"]', 'TGT_DEPT');
    await page.click('[data-testid="submit-department"]');
    
    // Wait for creation
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // Drag source department to target
    const sourceDept = page.locator('[data-testid="department-node"]').filter({ hasText: 'Source Department' });
    const targetDept = page.locator('[data-testid="department-node"]').filter({ hasText: 'Target Department' });
    
    await sourceDept.dragTo(targetDept);
    
    // Verify move was successful
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should view department members', async ({ authenticatedPage: page }) => {
    // Click on department to view details
    await page.click('[data-testid="department-node"]:first-child');
    
    // Navigate to members tab
    await page.click('[data-testid="members-tab"]');
    
    // Verify members list is visible
    await expect(page.locator('[data-testid="member-list"]')).toBeVisible();
    
    // Verify test users are shown
    await expect(page.locator('[data-testid="member-item"]')).toContainText('Test User');
    await expect(page.locator('[data-testid="member-item"]')).toContainText('Admin User');
  });

  test('should add member to department', async ({ authenticatedPage: page }) => {
    // Click on department to view details
    await page.click('[data-testid="department-node"]:first-child');
    
    // Navigate to members tab
    await page.click('[data-testid="members-tab"]');
    
    // Click add member button
    await page.click('[data-testid="add-member-btn"]');
    
    // Select user and role
    await page.selectOption('[data-testid="select-user"]', 'test@example.com');
    await page.selectOption('[data-testid="select-role"]', 'user');
    
    // Add member
    await page.click('[data-testid="confirm-add-member"]');
    
    // Verify member was added
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should search departments', async ({ authenticatedPage: page }) => {
    // Enter search query
    await page.fill('[data-testid="department-search"]', 'Test Department');
    
    // Wait for search results
    await page.waitForTimeout(500);
    
    // Verify filtered results
    const deptNodes = page.locator('[data-testid="department-node"]');
    await expect(deptNodes.first()).toContainText('Test Department');
  });
});